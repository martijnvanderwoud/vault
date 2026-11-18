#!/usr/bin/python3
"""Runner van de autonome Dependabot-routine (Debbie): repo's selecteren, runs starten en vastleggen.

Gebruik: dependabot_runner.py [--repo NAAM ...] [--model MODEL] [--timeout MINUTEN]
Zonder --repo alleen de projecten met `autonoom: true` in de frontmatter. Werkt eerst de run-notities bij (zie `opruimen`) en start dan per repo die in aanmerking komt een
run, één tegelijk. Per run een notitie in gebieden/werk/dependabot-runs/<jaar>-w<week>-<repo>.md
en een log in ~/dependabot-runs/.logs/. Een macOS-melding als de watcher van het agents-dashboard
niet draait. Een tweede runner-proces stopt meteen (lock). Een `paused`- of `failed`-run blokkeert de
repo. Na een hervatting zet de runner hem op `done` zodra er een verslag van Debbie in het issue staat.
Anders geef ik hem met de hand vrij met `status: resolved`, of zet ik het issue op Done.
De watcher (scripts/agent_watcher.py) doet wat voor alle agents geldt: de melding bij `paused` en
`failed`, `issue_state` bijhouden, en een afgebroken run op `failed` zetten.
Overzicht: gebieden/agents/dashboard.md.

Gebruik: dependabot_runner.py --dry-run [--repo NAAM ...]
Toont per project uit de skill welke repo's nu een run zouden krijgen, zonder iets te wijzigen.
Een repo komt in aanmerking als er open PR's zijn van de auteurs uit de frontmatter `authors`
(standaard app/dependabot) en alle checks klaar zijn. Een repo met een lopende, gepauzeerde of
mislukte run, of een run die deze ISO-week al klaar is met dezelfde PR's, slaat hij over.

Gebruik: dependabot_runner.py --prepare --repo NAAM [--repo NAAM ...]
Zet de clone in ~/dependabot-runs/NAAM klaar (clonen of fetchen, moet schoon zijn) en toont de
tools die een run daar krijgt. Werkt ook zonder mijn shellprofiel, zoals onder launchd.
Run-notities volgens gebieden/agents/agent-runs.md, via scripts/agentruns.py.
Plan: gebieden/werk/dependabot-routine-autonoom-plan.md.
"""
import argparse
import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agentruns  # noqa: E402

VAULT = Path(__file__).resolve().parent.parent
PROJECTEN = VAULT / '.claude/skills/dependabot-routine/projecten'
RUNS = VAULT / 'gebieden/werk/dependabot-runs'
DEFAULT_AUTHORS = ['app/dependabot']
# Zo lang na het openen van een PR zonder checks wachten we nog tot de checks verschijnen.
GEEN_CHECKS_WACHTTIJD = timedelta(minutes=30)
PENDING_STATES = {'PENDING', 'EXPECTED'}

HOME = Path.home()
CLONES = HOME / 'dependabot-runs'
RUNNER = VAULT / 'scripts/dependabot-runner'
NVM_SH = '/opt/homebrew/opt/nvm/nvm.sh'
# PATH zonder mijn shellprofiel: Homebrew (gh, git) en ~/.local/bin (claude). Node komt erbij uit
# .nvmrc, SDKMAN per commando via env.sh.
BASIS_PATH = ['/opt/homebrew/bin', str(HOME / '.local/bin'), '/usr/bin', '/bin', '/usr/sbin', '/sbin']
# Git via HTTPS met gh als credential helper: gh is ingelogd via de keychain, een SSH-agent is er
# onder launchd niet altijd.
GH_CREDENTIAL_HELPER = '!gh auth git-credential'

LOGS = CLONES / '.logs'
LOCK = CLONES / '.runner.lock'
DEFAULT_MODEL = 'claude-opus-5-5'
DEFAULT_TIMEOUT = 120  # minuten; stap 8 van de skill wacht op de build van de base branch
VERSLAG_KOP = 'Debbie (Dependabot routine) report'
# De volgorde in de run-notities. `onderwerp` is bij Debbie de naam van het project (de repo).
VELDEN = ['description', 'agent', 'status', 'onderwerp', 'issue', 'step', 'reason', 'session_id', 'started',
          'ended', 'resume', 'aandacht', 'prs', 'model', 'pid', 'kosten', 'beurten', 'geweigerd', 'log', 'issue_state']
LIJSTEN = ('aandacht', 'prs')


class Stop(Exception):
    """Reden om in deze repo niets te doen. Opruimen doet de runner nooit zelf."""


def frontmatter(path):
    """Leest simpele YAML-frontmatter: `key: waarde`, `key: [a, b]` en blok-lijsten met `- `."""
    lines = path.read_text(encoding='utf-8').splitlines()
    if not lines or lines[0].strip() != '---':
        return {}
    data, key = {}, None
    for line in lines[1:]:
        if line.strip() == '---':
            break
        if line.startswith((' ', '-')) and line.strip().startswith('- ') and key:
            data[key].append(line.strip()[2:].strip().strip('"\''))
            continue
        key, _, value = line.partition(':')
        key, value = key.strip(), value.strip()
        if value.startswith('[') and value.endswith(']'):
            data[key] = [v.strip().strip('"\'') for v in value[1:-1].split(',') if v.strip()]
        elif value == '':
            data[key] = []
        else:
            data[key] = value.strip('"\'')
    return data


def projecten():
    result = []
    for path in sorted(PROJECTEN.glob('*.md')):
        fm = frontmatter(path)
        if 'repo' not in fm:
            raise SystemExit('frontmatter `repo` ontbreekt in ' + str(path))
        result.append({'name': path.stem, 'repo': fm['repo'], 'authors': fm.get('authors') or DEFAULT_AUTHORS,
                       'autonoom': fm.get('autonoom') == 'true'})
    return result


def open_prs(repo, authors):
    prs = []
    for author in authors:
        out = subprocess.run(
            ['gh', 'pr', 'list', '--repo', repo, '--author', author, '--state', 'open', '--limit', '50',
             '--json', 'number,headRefOid,createdAt,statusCheckRollup'],
            check=True, capture_output=True, text=True, env=basis_env()).stdout
        prs += json.loads(out)
    return sorted(prs, key=lambda pr: pr['number'])


def checks_klaar(pr, nu):
    """Alle checks van de PR zijn afgerond. Zonder checks: pas na de wachttijd."""
    checks = pr['statusCheckRollup'] or []
    if not checks:
        geopend = datetime.fromisoformat(pr['createdAt'].replace('Z', '+00:00'))
        return nu - geopend >= GEEN_CHECKS_WACHTTIJD
    for check in checks:
        if check.get('__typename') == 'StatusContext':
            if check.get('state') in PENDING_STATES:
                return False
        elif check.get('status') != 'COMPLETED':
            return False
    return True


def vingerafdruk(prs):
    """Nummer en commit van elke PR. Een rebase door Dependabot telt als een andere PR."""
    return ['#%d@%s' % (pr['number'], pr['headRefOid'][:7]) for pr in prs]


def laatste_run(name):
    """De run-notitie van dit project met de laatste `started`, of None."""
    laatste = agentruns.laatste_per_onderwerp(notities(), LIJSTEN).get(name)
    return laatste[1] if laatste else None


def iso_week(moment):
    return moment.isocalendar()[:2]


def beoordeel(project, prs, run, nu):
    """Geeft (besluit, reden): besluit is `run`, `wacht`, `overslaan` of `niets`."""
    if not prs:
        return 'niets', "geen open PR's"
    # Na `resolved` (met de hand vrijgegeven) of zonder vorige run mag het gewoon.
    if run and run.get('status') == 'running':
        return 'overslaan', 'run loopt al (%s)' % run.get('session_id', '?')
    if run and run.get('status') in ('paused', 'failed'):
        return 'overslaan', 'vorige run is %s, wacht op mij (%s)' % (
            run['status'], run.get('issue') or (run.get('reason') or '?').splitlines()[0])
    bezig = [pr['number'] for pr in prs if not checks_klaar(pr, nu)]
    if bezig:
        return 'wacht', 'checks lopen nog: ' + ' '.join('#%d' % n for n in bezig)
    if run and run.get('status') == 'done' and run.get('started'):
        gestart = datetime.fromisoformat(run['started'].replace('Z', '+00:00'))
        if iso_week(gestart.astimezone()) == iso_week(nu.astimezone()) and \
                sorted(run.get('prs') or []) == sorted(vingerafdruk(prs)):
            return 'overslaan', "deze week al gedaan met dezelfde PR's (%s)" % run.get('issue', '?')
    return 'run', ''


def basis_env():
    return {'HOME': str(HOME), 'USER': HOME.name, 'LOGNAME': HOME.name, 'LANG': 'en_US.UTF-8',
            'PATH': ':'.join(BASIS_PATH)}


def run(args, cwd=None, env=None):
    p = subprocess.run(args, cwd=cwd, env=env or basis_env(), stdin=subprocess.DEVNULL,
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise Stop('%s mislukt: %s' % (' '.join(args[:3]), (p.stderr or p.stdout).strip()[-500:]))
    return p.stdout


def clone_klaarzetten(project):
    """Clonet de repo of haalt hem bij, met HTTPS en gh. Een vuile clone is een Stop."""
    clone = CLONES / project['name']
    url = 'https://github.com/%s.git' % project['repo']
    if not clone.exists():
        run(['git', 'clone', '--quiet', '-c', 'credential.helper=',
             '-c', 'credential.https://github.com.helper=' + GH_CREDENTIAL_HELPER, url, str(clone)])
    # Ook voor clones van vóór de runner, die nog via SSH gingen. Een lege helper wist wat de
    # globale of systeemconfig instelt, zoals osxkeychain.
    run(['git', 'remote', 'set-url', 'origin', url], cwd=clone)
    run(['git', 'config', '--replace-all', 'credential.helper', ''], cwd=clone)
    run(['git', 'config', '--replace-all', 'credential.https://github.com.helper', GH_CREDENTIAL_HELPER], cwd=clone)
    run(['git', 'fetch', '--prune', '--quiet', 'origin'], cwd=clone)
    vuil = run(['git', 'status', '--porcelain'], cwd=clone).strip()
    if vuil:
        raise Stop('clone %s is niet schoon:\n%s' % (clone, vuil))
    (CLONES / '.scratch' / project['name']).mkdir(parents=True, exist_ok=True)
    return clone


def node_bin(clone):
    """De bin-map van de Node-versie uit .nvmrc, zo nodig eerst geïnstalleerd. None zonder .nvmrc."""
    if not (clone / '.nvmrc').exists():
        return None
    env = dict(basis_env(), NVM_DIR=str(HOME / '.nvm'))
    # Zoals load-nvmrc in mijn .zshrc: alleen installeren als er lokaal geen passende versie is.
    out = run(['/bin/bash', '-c', '. "%s" && { nvm which >/dev/null 2>&1 || nvm install >/dev/null; } && nvm which'
               % NVM_SH], cwd=clone, env=env)
    return str(Path(out.strip().splitlines()[-1]).parent)


def youtrack_token():
    """Voor ${YOUTRACK_TOKEN} in mcp.json."""
    token = agentruns.env_waarde('YOUTRACK_TOKEN')
    if not token:
        raise Stop('YOUTRACK_TOKEN ontbreekt in ' + str(VAULT / '.env'))
    return token


def omgeving(clone):
    """De omgeving voor `claude` in deze clone. Gaat niet uit van mijn shellprofiel."""
    env = basis_env()
    node = node_bin(clone)
    if node:
        env['PATH'] = node + ':' + env['PATH']
    env['CLAUDE_ENV_FILE'] = str(RUNNER / 'env.sh')
    env['YOUTRACK_TOKEN'] = youtrack_token()
    # Voor ${NPM_TOKEN} in de .npmrc van de npm-repo's (Nexus van Pompkracht). Zet mijn .zshrc ook.
    if (clone / '.npmrc').exists() and 'NPM_TOKEN' in (clone / '.npmrc').read_text():
        token = agentruns.env_waarde('NPM_TOKEN')
        if not token:
            raise Stop('NPM_TOKEN ontbreekt in %s, en .npmrc vraagt erom' % (VAULT / '.env'))
        env['NPM_TOKEN'] = token
    return env


def claude_args(project, clone):
    """De vaste flags voor een run, behalve prompt, sessie, model en output (zie `run_starten`)."""
    settings = json.loads((RUNNER / 'settings.json').read_text())
    # Mijn globale CLAUDE.md noemt bijvoorbeeld youtrack_edit_comment.py, en dat mag de run niet.
    settings['claudeMdExcludes'] = [str(HOME / '.claude/CLAUDE.md')]
    return ['--add-dir', str(VAULT), '--add-dir', str(CLONES / '.scratch' / project['name']),
            '--setting-sources', 'project,local', '--settings', json.dumps(settings),
            '--strict-mcp-config', '--mcp-config', str(RUNNER / 'mcp.json'),
            '--permission-mode', 'dontAsk', '--permission-prompts', 'none']


def tools_tonen(clone, env):
    """Draait de tools zoals een Bash-commando van de run ze ziet: met env.sh in de clone."""
    script = ('. "$CLAUDE_ENV_FILE"; for t in git gh claude java mvn gradle sbt node npm; do printf "%-7s" $t; '
              'command -v $t || echo ontbreekt; done; java -version 2>&1 | head -1; mvn -v 2>/dev/null | head -1; '
              'node -v 2>/dev/null; claude --version; gh auth status 2>&1 | grep -E "Logged in|Token scopes"; '
              'claude auth status 2>&1 | grep -i -E "logged|login|method" | head -2; '
              'git ls-remote --heads origin >/dev/null && echo "git via HTTPS: ok"')
    return run(['/bin/zsh', '-f', '-c', script], cwd=clone, env=env)


# --- Run-notities ---------------------------------------------------------------------------

def notitie_schrijven(path, fm, tekst):
    agentruns.notitie_schrijven(path, fm, tekst, VELDEN)


def notitie_lezen(path):
    return agentruns.notitie_lezen(path, LIJSTEN)


def notities():
    """De run-notities: alleen die met `agent: debbie`. Andere notities in de map schrijft de runner
    zo nooit opnieuw."""
    return agentruns.notities(RUNS, 'debbie')


def nieuwe_notitie(name, moment):
    jaar, week = iso_week(moment)
    stem, n = '%d-w%02d-%s' % (jaar, week, name), 1
    while (RUNS / (stem + '.md')).exists() or (LOGS / (stem + '.jsonl')).exists():
        n += 1
        stem = '%d-w%02d-%s-%d' % (jaar, week, name, n)
    return RUNS / (stem + '.md'), stem


def index_bijwerken():
    subprocess.run([sys.executable, str(VAULT / 'scripts/build_index.py')], check=False, capture_output=True)


def watcher_controleren():
    """Meldt het als de watcher van het dashboard geen heartbeat meer schrijft. Het dashboard toont dat
    zelf pas als het opnieuw gemaakt wordt, en dat doet juist de watcher. Zonder watcher komen er ook
    geen meldingen bij `paused` en `failed` en worden afgebroken runs niet `failed`."""
    stil = agentruns.watcher_stil(nu_lokaal())
    if stil is None:
        return
    sinds = 'nog nooit gedraaid' if stil == 'nooit' else 'stil sinds %s' % stil.strftime('%d-%m %H:%M')
    print('agent-watcher %s' % sinds)
    agentruns.melden('Agent-watcher draait niet', '%s, het agents-dashboard ververst niet' % sinds.capitalize())


def resume_regel(name, sessie):
    return 'cd ~/dependabot-runs/%s && claude --resume %s' % (name, sessie)


def nu_lokaal():
    return datetime.now().astimezone().replace(microsecond=0)


def verslag_na(issue, sinds):
    """Staat er in het issue een verslag van Debbie dat na `sinds` geplaatst is? None bij een fout."""
    try:
        comments = agentruns.youtrack_get('/issues/%s/comments?fields=text,created&$top=200' % issue)
    except Exception as e:  # netwerk of YouTrack: volgende keer opnieuw
        print('  YouTrack %s niet te lezen: %s' % (issue, e))
        return None
    grens = datetime.fromisoformat(sinds).timestamp() * 1000
    return any((c.get('text') or '').lstrip().startswith(VERSLAG_KOP) and c.get('created', 0) > grens
               for c in comments)


def opruimen(dry_run):
    """Zet een gepauzeerde of mislukte run op `done` als er na het einde een verslag van Debbie in het
    issue staat (hervat). Geeft regels. Een afgebroken run op `failed` zetten, `issue_state` bijhouden
    en melden doet de watcher (scripts/agent_watcher.py), voor alle agents."""
    regels = []
    for path in notities():
        fm, _ = notitie_lezen(path)
        status = fm.get('status')
        if status not in ('paused', 'failed') or not fm.get('issue') or not fm.get('ended') or \
                agentruns.afgehandeld(fm) or not verslag_na(fm['issue'], fm['ended']):
            continue
        regels.append('%s: %s -> done' % (path.stem, status))
        if dry_run:
            continue
        # Opnieuw lezen: de watcher kan de notitie intussen geschreven hebben (YouTrack duurt even).
        fm, tekst = notitie_lezen(path)
        if fm.get('status') != status:
            continue
        stap = ' bij stap %s' % fm['step'] if fm.get('step') else ''
        tekst += '\n\nOp `done` gezet op %s: na de %s%s (%s) staat er een verslag in %s.\n' % (
            nu_lokaal().isoformat(), status, stap, fm.get('reason') or '?', fm['issue'])
        for key in ('step', 'reason', 'resume'):
            fm.pop(key, None)
        fm['status'] = 'done'
        fm['description'] = agentruns.beschrijving(fm)
        notitie_schrijven(path, fm, tekst)
    if not dry_run and regels:
        index_bijwerken()
    return regels


# --- Run starten ----------------------------------------------------------------------------

class Afgebroken(Exception):
    """De runner kreeg SIGTERM, bijvoorbeeld van launchd."""


def sigterm(signum, frame):
    raise Afgebroken('runner kreeg SIGTERM')


def log_uitlezen(log):
    """Het result-event en de tekst van het model uit de stream-json-log."""
    result, teksten = None, []
    for regel in log.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            event = json.loads(regel)
        except ValueError:
            continue  # stderr staat ook in de log
        if event.get('type') == 'result':
            result = event
        elif event.get('type') == 'assistant':
            teksten += [b.get('text', '') for b in event.get('message', {}).get('content', [])
                        if b.get('type') == 'text']
    return result, teksten


def statusregels(tekst):
    """(status, velden, aandacht) uit de laatste RUN_STATUS-regel en de RUN_ATTENTION-regels ervoor."""
    regels = tekst.splitlines()
    for i in range(len(regels) - 1, -1, -1):
        m = re.match(r'\s*RUN_STATUS:\s*(\w+)(.*)', regels[i])
        if m:
            velden = {k: (a if a else b) for k, a, b in re.findall(r'(\w+)=(?:"([^"]*)"|(\S+))', m.group(2))}
            aandacht = [r.split(':', 1)[1].strip() for r in regels[:i] if r.strip().startswith('RUN_ATTENTION:')]
            return m.group(1), velden, aandacht
    return None, {}, []


def run_starten(project, prs, model, timeout):
    """Eén run in de clone van dit project. Geeft de eindstatus."""
    RUNS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    gestart = nu_lokaal()
    path, stem = nieuwe_notitie(project['name'], gestart)
    log = LOGS / (stem + '.jsonl')
    fm = {'agent': 'debbie', 'status': 'running', 'onderwerp': project['name'], 'issue': '', 'started': gestart.isoformat(),
          'aandacht': [], 'prs': vingerafdruk(prs), 'model': model}
    tekst = '# Debbie-run %s\n\nPR\'s bij de start: %s.\n' % (project['name'], ' '.join(fm['prs']))

    def afsluiten(status, **velden):
        fm.update(velden, status=status, ended=nu_lokaal().isoformat())
        fm.pop('pid', None)
        if status in ('paused', 'failed') and fm.get('session_id'):
            fm['resume'] = resume_regel(project['name'], fm['session_id'])
        else:
            fm.pop('resume', None)
        fm['description'] = agentruns.beschrijving(fm)
        notitie_schrijven(path, fm, tekst)
        index_bijwerken()
        return status

    try:
        clone = clone_klaarzetten(project)
        env = omgeving(clone)
    except Stop as stop:
        tekst += '\nGeen run gestart: de clone was niet klaar te zetten.\n'
        return afsluiten('paused', reason=str(stop))

    sessie = str(uuid.uuid4())
    jaar, week = iso_week(gestart)
    # debbie-<repo>-w<week>, met het volgnummer uit de bestandsnaam bij een tweede run in een week
    naam = 'debbie-%s-w%02d%s' % (project['name'], week, stem[len('%d-w%02d-%s' % (jaar, week, project['name'])):])
    args = (['claude', '-p', '/dependabot-routine autonoom session=' + sessie, '--session-id', sessie, '-n', naam,
             '--model', model, '--output-format', 'stream-json', '--verbose'] + claude_args(project, clone))
    with open(log, 'w') as uit:
        proc = subprocess.Popen(args, cwd=clone, env=env, stdin=subprocess.DEVNULL, stdout=uit,
                                stderr=subprocess.STDOUT, start_new_session=True)
    # `resume` al bij de start: zet de watcher een afgebroken run op `failed`, dan staat het commando er al.
    fm.update(session_id=sessie, pid=proc.pid, resume=resume_regel(project['name'], sessie),
              log=str(log).replace(str(HOME), '~', 1))
    fm['description'] = agentruns.beschrijving(fm)
    notitie_schrijven(path, fm, tekst)
    index_bijwerken()
    print('  gestart: sessie %s, log %s' % (sessie, fm['log']))

    try:
        returncode = proc.wait(timeout=timeout * 60)
    except (subprocess.TimeoutExpired, Afgebroken, KeyboardInterrupt) as e:
        stoppen(proc)
        reden = 'run duurde langer dan %d minuten' % timeout if isinstance(e, subprocess.TimeoutExpired) else \
            'runner afgebroken (%s)' % (e or type(e).__name__)
        afsluiten('failed', reason=reden)
        if isinstance(e, subprocess.TimeoutExpired):
            return 'failed'
        raise

    result, teksten = log_uitlezen(log)
    status, velden, aandacht = statusregels((result or {}).get('result') or '')
    if not status:  # de regels staan normaal in het laatste bericht, maar zoek ze anders verderop
        status, velden, aandacht = statusregels('\n'.join(teksten))
    if result:
        fm['kosten'] = round(result.get('total_cost_usd') or 0, 2)
        fm['beurten'] = result.get('num_turns')
        geweigerd = result.get('permission_denials') or []
        fm['geweigerd'] = len(geweigerd)
        if geweigerd:
            tekst += '\nGeweigerde tools:\n\n' + ''.join(
                '- `%s`: `%s`\n' % (d.get('tool_name'), json.dumps(d.get('tool_input'), ensure_ascii=False)[:300])
                for d in geweigerd)
    issue = velden.get('issue', '')
    fm['issue'] = '' if issue == 'none' else issue
    fm['aandacht'] = aandacht
    if returncode != 0 or (result or {}).get('is_error') or status not in ('done', 'paused'):
        reden = 'exitcode %d' % returncode if returncode else \
            'run gaf een fout' if (result or {}).get('is_error') else 'geen RUN_STATUS-regel'
        return afsluiten('failed', reason=reden)
    if status == 'paused':
        return afsluiten('paused', step=velden.get('step', ''), reason=velden.get('reason', ''))
    return afsluiten('done')


def stoppen(proc):
    """Stopt claude en alles wat hij startte (eigen procesgroep)."""
    for sig, wacht in ((signal.SIGTERM, 15), (signal.SIGKILL, 5)):
        try:
            os.killpg(proc.pid, sig)
            proc.wait(timeout=wacht)
            return
        except ProcessLookupError:
            return
        except subprocess.TimeoutExpired:
            continue


def lock_nemen():
    """Exclusieve lock voor dit runner-proces, of None als er al een draait."""
    CLONES.mkdir(exist_ok=True)
    f = open(LOCK, 'a+')
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        f.close()
        return None
    f.truncate(0)
    f.write(str(os.getpid()))
    f.flush()
    return f


def selecteer(namen):
    """Met namen precies die projecten, anders alleen die met `autonoom: true` (de allowlist)."""
    nu = datetime.now(timezone.utc)
    lijst = [p for p in projecten() if p['name'] in namen or not namen and p['autonoom']]
    onbekend = set(namen) - {p['name'] for p in lijst}
    if onbekend:
        raise SystemExit('onbekend project: ' + ', '.join(sorted(onbekend)))
    with ThreadPoolExecutor(max_workers=8) as pool:
        alle_prs = list(pool.map(lambda p: open_prs(p['repo'], p['authors']), lijst))
    result = []
    for project, prs in zip(lijst, alle_prs):
        besluit, reden = beoordeel(project, prs, laatste_run(project['name']), nu)
        result.append((project, prs, besluit, reden))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--dry-run', action='store_true', help='alleen tonen welke repo\'s een run krijgen')
    parser.add_argument('--prepare', action='store_true', help='clone klaarzetten en de tools tonen')
    parser.add_argument('--repo', action='append', default=[], help='alleen dit project, ook zonder autonoom: true (herhaalbaar)')
    parser.add_argument('--model', default=DEFAULT_MODEL, help='model voor claude --model (standaard %(default)s)')
    parser.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT, help='minuten per run (standaard %(default)s)')
    args = parser.parse_args()
    # Onder launchd gaat stdout naar runner.log, en zonder dit staat een regel er pas na de run.
    sys.stdout.reconfigure(line_buffering=True)
    if args.prepare:
        if not args.repo:
            raise SystemExit('--prepare vraagt om --repo')
        alle = {p['name']: p for p in projecten()}
        for naam in args.repo:
            if naam not in alle:
                raise SystemExit('onbekend project: ' + naam)
            print('== ' + naam)
            try:
                clone = clone_klaarzetten(alle[naam])
                print(tools_tonen(clone, omgeving(clone)), end='')
            except Stop as stop:
                print('STOP: %s' % stop)
        return
    if args.dry_run:
        for regel in opruimen(dry_run=True):
            print('zou bijwerken: ' + regel)
        for project, prs, besluit, reden in selecteer(args.repo):
            print(regel_tonen(project, prs, besluit, reden))
        uit = [p['name'] for p in projecten() if not p['autonoom']]
        if not args.repo and uit:
            print('niet autonoom: ' + ', '.join(uit))
        return
    # Zo is in runner.log te zien of launchd elk half uur start.
    print('-- %s' % nu_lokaal().isoformat())
    lock = lock_nemen()
    if not lock:
        print('er draait al een runner (%s)' % LOCK)
        return
    signal.signal(signal.SIGTERM, sigterm)
    for regel in opruimen(dry_run=False):
        print('bijgewerkt: ' + regel)
    # Pas na opruimen (YouTrack, een paar seconden): na het inloggen starten runner en watcher
    # tegelijk, en dan heeft de watcher zijn eerste heartbeat nog niet geschreven.
    watcher_controleren()
    for project, prs, besluit, reden in selecteer(args.repo):
        print(regel_tonen(project, prs, besluit, reden))
        if besluit == 'run':
            try:
                print('  -> %s' % run_starten(project, prs, args.model, args.timeout))
            except (Afgebroken, KeyboardInterrupt) as e:
                print('  -> failed, %s' % (e or 'onderbroken'))
                return 1


def regel_tonen(project, prs, besluit, reden):
    breedte = max(len(p.stem) for p in PROJECTEN.glob('*.md'))
    nummers = ' '.join('#%d' % pr['number'] for pr in prs)
    regel = '%-*s  %-9s  %s' % (breedte, project['name'], besluit, nummers)
    return (regel + ('  — ' + reden if reden and besluit != 'niets' else '')).rstrip()


if __name__ == '__main__':
    sys.exit(main())
