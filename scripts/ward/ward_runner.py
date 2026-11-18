#!/usr/bin/python3
"""Runner van Ward, de bewaker van system health: draait de checks op de hosts van Pompkracht.

De hosts komen uit ~/.ssh/config (de `Host`-regels zonder wildcard), de verwachte waarden uit
data/ward/baseline.json. Die referentie pas ik bewust met de hand aan, nooit automatisch. Behalve
de checks uit scripts/ward/checks/ vergelijkt de runner de hostlijst met de referentie: een host die
erbij komt of uit de config verdwijnt, is een `warn` van de check `hosts`.
Plan: gebieden/werk/ward-plan.md.

    ward_runner.py [--dry-run] [--referentie PAD] [--uitkomsten PAD] [--status PAD] [--model MODEL]

Toont per check en host de uitkomst (`ok`, `warn` of `alarm`) met details, en wat er veranderd is
sinds de vorige run (de status in ~/.ward/status.json). Exitcode 0 als alles `ok` is, 1 bij een
`warn`, 2 bij een `alarm`. Alleen een verandering levert iets op, een bekend probleem niet elke dag
opnieuw. Wordt een host slechter of anders niet `ok`, dan start een headless sessie met Ward
(`claude -p`), die de bevinding nagaat, een notitie in inbox/ schrijft en mij mailt. Is er alleen
herstel naar `ok`, dan schrijft de runner zelf een korte notitie en volgt een macOS-melding, zonder
model en zonder mail (mailen kan alleen via de claude.ai-koppeling, dus via een sessie). Mislukt de
sessie, dan volgt een macOS-melding en blijft de oude status staan, zodat de volgende run het
opnieuw probeert. De status, met de tijd van de laatste geslaagde run, schrijft alleen een geslaagde
run. Een tweede runner stopt meteen (lock). launchd start de runner elke dag om 9:00
(scripts/ward/nl.crimsoncricket.ward.plist). Log in ~/.ward/logs/.
`--dry-run` toont alleen de uitkomsten en veranderingen, zonder lock, sessie of status. `--referentie`
neemt een andere referentie, om `warn` te testen. `--uitkomsten` leest de uitkomsten uit een
JSON-bestand ({check: {host: [uitkomst, details]}}) in plaats van de checks te draaien: een test, die
Ward als test meekrijgt. Bij een test geldt de status alleen met `--status`; zonder vergelijkt de
runner met niets en schrijft hij niets.
"""
import argparse
import fcntl
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
STATUS = WARD / 'status.json'
LOCK = WARD / 'runner.lock'
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


def kern(uitkomst, details):
    """Wat telt als verandering. Bij `ok` alleen de uitkomst; bij onbereikbaar niet de foutmelding
    van ssh, die van dag tot dag kan verschillen."""
    if uitkomst == 'ok':
        return uitkomst, ''
    return uitkomst, 'onbereikbaar' if details.startswith('onbereikbaar') else details


def veranderingen(vorige, uitkomsten):
    """{check: {host: [vorige, nu]}} voor elke host waarvan de kern veranderd is. Een host die er
    vorige keer niet was, telt als vorige `ok`; een host die nu ontbreekt, als nu `ok`."""
    result = {}
    for naam in set(vorige) | set(uitkomsten):
        oud, nieuw = vorige.get(naam, {}), uitkomsten.get(naam, {})
        for host in list(nieuw) + [h for h in oud if h not in nieuw]:
            was, is_ = tuple(oud.get(host, ('ok', ''))), tuple(nieuw.get(host, ('ok', '')))
            if kern(*was) != kern(*is_):
                result.setdefault(naam, {})[host] = [list(was), list(is_)]
    return result


def status_lezen(path):
    """De uitkomsten van de laatste geslaagde run, of {} als er nog geen is."""
    try:
        return json.loads(path.read_text())['uitkomsten']
    except (OSError, ValueError, KeyError):
        return {}


def status_schrijven(path, uitkomsten, moment):
    path.parent.mkdir(parents=True, exist_ok=True)
    agentruns.atomair_schrijven(path, json.dumps(
        {'laatste_run': moment.isoformat(), 'uitkomsten': uitkomsten}, indent=2, ensure_ascii=False) + '\n')


def lock_nemen():
    """Exclusieve lock voor dit runner-proces, of None als er al een draait."""
    WARD.mkdir(exist_ok=True)
    f = open(LOCK, 'a+')
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        f.close()
        return None
    return f


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


def herstel_noteren(veranderd, moment):
    """Alleen herstel naar `ok`: een korte notitie in inbox/, zonder model. Geeft het pad."""
    notitie, _ = nieuwe_notitie(moment.date().isoformat())
    hosts = ['- `%s` (%s): was %s, %s' % (host, naam, was[0], was[1])
             for naam, per_host in veranderd.items() for host, (was, _) in per_host.items()]
    agentruns.notitie_schrijven(notitie, {
        'description': 'Ward %s - herstel: %d host(s) weer ok' % (moment.date().isoformat(), len(hosts)),
        'tags': ['ward']}, '# Ward %s: weer ok\n\nDe runner (%s) ziet deze hosts weer `ok`:\n\n%s\n\n'
        'Er is geen sessie met Ward gestart en geen mail gestuurd.\n' % (
            moment.date().isoformat(), moment.isoformat(), '\n'.join(hosts)))
    subprocess.run([sys.executable, str(VAULT / 'scripts/build_index.py')], check=False, capture_output=True)
    return notitie


def prompt(uitkomsten, veranderd, notitie, moment, test):
    niet_ok = {naam: {h: list(v) for h, v in per_host.items() if v[0] != 'ok'}
               for naam, per_host in uitkomsten.items()}
    datum = moment.date().isoformat()
    return Template((HEADLESS / 'prompt.md').read_text()).substitute(
        moment=moment.isoformat(), datum=datum, notitie=tilde(notitie), ergste=ergste(uitkomsten),
        uitkomsten=json.dumps({k: v for k, v in niet_ok.items() if v}, indent=2, ensure_ascii=False),
        veranderd=json.dumps(veranderd, indent=2, ensure_ascii=False),
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


def ward_starten(uitkomsten, veranderd, model, test):
    """Eén sessie met Ward. Geeft (gelukt, reden)."""
    LOGS.mkdir(parents=True, exist_ok=True)
    moment = nu_lokaal()
    notitie, stem = nieuwe_notitie(moment.date().isoformat())
    log = LOGS / (stem + '.jsonl')
    sessie = str(uuid.uuid4())
    args = (['claude', '-p', prompt(uitkomsten, veranderd, notitie, moment, test), '--session-id', sessie,
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
    parser.add_argument('--status', type=Path, help='ander status.json (standaard %s, bij een test geen)' % tilde(STATUS))
    parser.add_argument('--model', default=DEFAULT_MODEL, help='model voor Ward (standaard %(default)s)')
    args = parser.parse_args()
    sys.stdout.reconfigure(line_buffering=True)
    test = bool(args.uitkomsten)
    status = args.status or (None if test or args.referentie != REFERENTIE else STATUS)

    lock = None if args.dry_run else lock_nemen()
    if not args.dry_run and lock is None:
        print('%s: er draait al een runner, gestopt' % nu_lokaal().isoformat())
        sys.exit(0)
    moment = nu_lokaal()
    print('--- %s' % moment.isoformat())
    if args.uitkomsten:
        uitkomsten = {naam: {h: tuple(v) for h, v in per_host.items()}
                      for naam, per_host in json.loads(args.uitkomsten.read_text()).items()}
    else:
        uitkomsten = draaien(json.loads(args.referentie.read_text()))
    tonen(uitkomsten)
    slechtste = ergste(uitkomsten)
    # Zonder status (een test) telt alles wat niet ok is als verandering.
    veranderd = veranderingen(status_lezen(status) if status else {}, uitkomsten)
    slechter = any(nu[0] != 'ok' for per_host in veranderd.values() for _, nu in per_host.values())
    print('veranderd: %s' % ('; '.join('%s %s: %s -> %s' % (naam, host, was[0], nu[0])
                                       for naam, ph in veranderd.items() for host, (was, nu) in ph.items())
                             or 'niets'))
    if args.dry_run:
        sys.exit(UITKOMSTEN.index(slechtste))

    gelukt = True
    if slechter:
        gelukt, reden = ward_starten(uitkomsten, veranderd, args.model, test)
        print('Ward: %s' % ('klaar, %s' % reden if gelukt else 'mislukt, %s' % reden))
        if not gelukt:
            agentruns.melden('Ward-run mislukt', 'Bij een %s: %s' % (slechtste, reden))
    elif veranderd:
        notitie = herstel_noteren(veranderd, moment)
        print('herstel: %s' % tilde(notitie))
        agentruns.melden('Ward: weer ok', '%d host(s) hersteld, zie %s' % (
            sum(len(ph) for ph in veranderd.values()), notitie.name))
    if gelukt and status:
        status_schrijven(status, {naam: {h: list(v) for h, v in ph.items()} for naam, ph in uitkomsten.items()},
                         moment)
    sys.exit(UITKOMSTEN.index(slechtste))


if __name__ == '__main__':
    main()
