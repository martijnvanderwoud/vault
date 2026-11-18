#!/usr/bin/python3
"""Runner van Ward, de bewaker van system health: draait de checks op de hosts van Pompkracht.

De hosts komen uit ~/.ssh/config (de `Host`-regels zonder wildcard), de verwachte waarden uit
data/ward/baseline.json. Die referentie pas ik bewust met de hand aan, nooit automatisch. Behalve
de checks uit scripts/ward/checks/ vergelijkt de runner de hostlijst met de referentie: een host die
erbij komt of uit de config verdwijnt, is een `warn` van de check `hosts`.
Plan: gebieden/werk/ward-plan.md.

    ward_runner.py [--dry-run] [--referentie PAD] [--uitkomsten PAD] [--model MODEL]

Toont per check en host de uitkomst (`ok`, `warn` of `alarm`) met details. Exitcode 0 als alles
`ok` is, 1 bij een `warn`, 2 bij een `alarm`. Is er iets niet `ok`, dan start een gewone run een
headless sessie met Ward (`claude -p`), die de bevinding nagaat, een notitie in inbox/ schrijft en
mij mailt. Nu nog bij elke `warn` of `alarm`; dat het alleen bij een verandering gebeurt, komt in
stap 4. Mislukt de sessie, dan volgt een macOS-melding. Log in ~/.ward/logs/.
`--dry-run` toont alleen de uitkomsten. `--referentie` neemt een andere referentie, om `warn` te
testen. `--uitkomsten` leest de uitkomsten uit een JSON-bestand ({check: {host: [uitkomst,
details]}}) in plaats van de checks te draaien: een test, die Ward als test meekrijgt.
"""
import argparse
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from string import Template

# Met `python3 -I` (zoals onder launchd) staat de map van het script niet in sys.path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import agentruns  # noqa: E402
import ssh  # noqa: E402
from checks import CHECKS, UITKOMSTEN  # noqa: E402

VAULT = Path(__file__).resolve().parent.parent.parent
REFERENTIE = VAULT / 'data/ward/baseline.json'
HEADLESS = Path(__file__).resolve().parent / 'headless'
MAIL_HOOK = Path(__file__).resolve().parent / 'mail_hook.py'
INBOX = VAULT / 'inbox'

HOME = Path.home()
WARD = HOME / '.ward'  # werkmap van de sessie, buiten de vault: geen projectinstellingen of hooks
LOGS = WARD / 'logs'
# PATH zonder mijn shellprofiel, zoals onder launchd: ~/.local/bin voor claude.
BASIS_PATH = [str(HOME / '.local/bin'), '/opt/homebrew/bin', '/usr/bin', '/bin', '/usr/sbin', '/sbin']
DEFAULT_MODEL = 'claude-opus-5-5'
TIMEOUT = 20  # minuten
SEND = 'mcp__claude_ai_Gmail__send_message'


def hosts_check(hosts, verwacht):
    """{host: (uitkomst, details)} voor de hostlijst tegenover de hosts uit de referentie."""
    result = {}
    for host in hosts:
        result[host] = ('ok', 'in de referentie') if host in verwacht else (
            'warn', 'nieuwe host, niet in de referentie')
    for host in verwacht:
        if host not in hosts:
            result[host] = ('warn', 'ontbreekt in %s' % ssh.SSH_CONFIG)
    return result


def draaien(referentie):
    """{check: {host: (uitkomst, details)}} voor alle checks."""
    hosts = ssh.hosts()
    uitkomsten = {'hosts': hosts_check(hosts, referentie['hosts'])}
    for check in CHECKS:
        uitkomsten[check.NAAM] = check.check(hosts, referentie[check.NAAM])
    return uitkomsten


def ergste(uitkomsten):
    return max((u for per_host in uitkomsten.values() for u, _ in per_host.values()),
               key=UITKOMSTEN.index, default='ok')


def aantallen(per_host):
    return {u: sum(1 for v, _ in per_host.values() if v == u) for u in UITKOMSTEN}


def tonen(uitkomsten):
    breedte = max(len(h) for per_host in uitkomsten.values() for h in per_host)
    for naam, per_host in uitkomsten.items():
        print('%s: %s' % (naam, ', '.join('%d %s' % (n, u) for u, n in aantallen(per_host).items() if n)))
        for host, (uitkomst, details) in per_host.items():
            print('  %-5s  %-*s  %s' % (uitkomst, breedte, host, details))


# --- Ward headless --------------------------------------------------------------------------

def nu_lokaal():
    return datetime.now().astimezone().replace(microsecond=0)


def tilde(path):
    """Het pad met ~ voor de thuismap, zoals in de allowlist."""
    return str(path).replace(str(HOME), '~', 1)


def nieuwe_notitie(datum):
    stem, n = 'ward-%s' % datum, 1
    while (INBOX / (stem + '.md')).exists() or (LOGS / (stem + '.jsonl')).exists():
        n += 1
        stem = 'ward-%s-%d' % (datum, n)
    return INBOX / (stem + '.md'), stem


def prompt(uitkomsten, notitie, moment, test):
    niet_ok = {naam: {h: list(v) for h, v in per_host.items() if v[0] != 'ok'}
               for naam, per_host in uitkomsten.items()}
    datum = moment.date().isoformat()
    return Template((HEADLESS / 'prompt.md').read_text()).substitute(
        moment=moment.isoformat(), datum=datum, notitie=tilde(notitie), ergste=ergste(uitkomsten),
        uitkomsten=json.dumps({k: v for k, v in niet_ok.items() if v}, indent=2, ensure_ascii=False),
        aantallen='; '.join('%s: %s' % (naam, ', '.join('%d %s' % (n, u) for u, n in aantallen(ph).items() if n))
                            for naam, ph in uitkomsten.items()),
        test=('**Dit is een test met nagemaakte uitkomsten.** Ga ze toch na, zet `TEST` in de titel van '
              'de notitie, en verwacht dat de echte hosts iets anders laten zien.\n') if test else '',
        onderwerp='Ward TEST:' if test else 'Ward:')


def claude_args(notitie):
    """De vaste flags: allowlist, mailhook, en alleen schrijven op het pad van de notitie."""
    settings = json.loads((HEADLESS / 'settings.json').read_text())
    settings['permissions']['allow'].append('Edit(%s)' % tilde(notitie))
    # Mijn globale CLAUDE.md noemt tools en scripts die Ward niet mag.
    settings['claudeMdExcludes'] = [str(HOME / '.claude/CLAUDE.md')]
    settings['hooks'] = {'PreToolUse': [{'matcher': 'mcp__claude_ai_Gmail__.*', 'hooks': [
        {'type': 'command', 'command': '/usr/bin/python3 -I "%s"' % MAIL_HOOK}]}]}
    # Geen --strict-mcp-config: dat zet de claude.ai-koppelingen uit, en de mail gaat via Gmail daar.
    return ['--add-dir', str(INBOX), '--setting-sources', 'project,local', '--settings', json.dumps(settings),
            '--permission-mode', 'dontAsk', '--permission-prompts', 'none']


def omgeving():
    env = {'HOME': str(HOME), 'USER': HOME.name, 'LOGNAME': HOME.name, 'LANG': 'en_US.UTF-8',
           'PATH': ':'.join(BASIS_PATH)}
    # launchd geeft SSH_AUTH_SOCK mee (stap 1); nagaan.py heeft hem nodig voor de sleutels.
    if os.environ.get('SSH_AUTH_SOCK'):
        env['SSH_AUTH_SOCK'] = os.environ['SSH_AUTH_SOCK']
    return env


def log_uitlezen(log):
    """(result, mails): het result-event en per send_message of hij lukte. De claude.ai-koppelingen
    staan niet in het init-event; Ward laadt send_message uitgesteld, via ToolSearch."""
    result, aanroepen, mails = None, set(), []
    for regel in log.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            event = json.loads(regel)
        except ValueError:
            continue  # stderr staat ook in de log
        if event.get('type') == 'result':
            result = event
        for blok in (event.get('message') or {}).get('content') or []:
            if not isinstance(blok, dict):
                continue
            if blok.get('type') == 'tool_use' and blok.get('name') == SEND:
                aanroepen.add(blok.get('id'))
            elif blok.get('type') == 'tool_result' and blok.get('tool_use_id') in aanroepen:
                mails.append(not blok.get('is_error'))
    return result, mails


def ward_starten(uitkomsten, model, test):
    """Eén sessie met Ward. Geeft (gelukt, reden)."""
    LOGS.mkdir(parents=True, exist_ok=True)
    moment = nu_lokaal()
    notitie, stem = nieuwe_notitie(moment.date().isoformat())
    log = LOGS / (stem + '.jsonl')
    sessie = str(uuid.uuid4())
    args = (['claude', '-p', prompt(uitkomsten, notitie, moment, test), '--session-id', sessie,
             '-n', stem, '--model', model, '--output-format', 'stream-json', '--verbose'] + claude_args(notitie))
    print('Ward gestart: sessie %s, log %s' % (sessie, tilde(log)))
    with open(log, 'w') as uit:
        try:
            returncode = subprocess.run(args, cwd=WARD, env=omgeving(), stdin=subprocess.DEVNULL, stdout=uit,
                                        stderr=subprocess.STDOUT, timeout=TIMEOUT * 60).returncode
        except subprocess.TimeoutExpired:
            return False, 'sessie duurde langer dan %d minuten' % TIMEOUT
    subprocess.run([sys.executable, str(VAULT / 'scripts/build_index.py')], check=False, capture_output=True)

    result, mails = log_uitlezen(log)
    if result:
        print('kosten $%.2f, %s beurten, %d geweigerd' % (result.get('total_cost_usd') or 0, result.get('num_turns'),
                                                         len(result.get('permission_denials') or [])))
    tekst = (result or {}).get('result') or ''
    if returncode != 0:
        return False, 'exitcode %d' % returncode
    if (result or {}).get('is_error'):
        return False, 'sessie gaf een fout'
    if not notitie.exists():
        return False, 'geen notitie in %s' % tilde(notitie)
    if not any(mails):
        return False, 'geen mail verstuurd'
    if 'WARD_STATUS: done' not in tekst:
        return False, 'geen WARD_STATUS: done'
    return True, tilde(notitie)


def main():
    parser = argparse.ArgumentParser(description='Runner van Ward: checks op de hosts van Pompkracht.')
    parser.add_argument('--dry-run', action='store_true', help='alleen de uitkomsten tonen')
    parser.add_argument('--referentie', type=Path, default=REFERENTIE, help='andere baseline.json')
    parser.add_argument('--uitkomsten', type=Path, help='nagemaakte uitkomsten uit JSON, om Ward te testen')
    parser.add_argument('--model', default=DEFAULT_MODEL, help='model voor Ward (standaard %(default)s)')
    args = parser.parse_args()
    sys.stdout.reconfigure(line_buffering=True)

    if args.uitkomsten:
        uitkomsten = {naam: {h: tuple(v) for h, v in per_host.items()}
                      for naam, per_host in json.loads(args.uitkomsten.read_text()).items()}
    else:
        uitkomsten = draaien(json.loads(args.referentie.read_text()))
    tonen(uitkomsten)
    slechtste = ergste(uitkomsten)
    if not args.dry_run and slechtste != 'ok':
        gelukt, reden = ward_starten(uitkomsten, args.model, test=bool(args.uitkomsten))
        print('Ward: %s' % ('klaar, %s' % reden if gelukt else 'mislukt, %s' % reden))
        if not gelukt:
            agentruns.melden('Ward-run mislukt', 'Bij een %s: %s' % (slechtste, reden))
    sys.exit(UITKOMSTEN.index(slechtste))


if __name__ == '__main__':
    main()
