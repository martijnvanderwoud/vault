#!/usr/bin/python3
"""Run-notities van de autonome agents lezen en schrijven, volgens gebieden/agents/agent-runs.md.

Gedeeld door de runners (zoals dependabot_runner.py), het dashboard en de watcher.
Plan: gebieden/vault/agents-dashboard-plan.md.
"""
import json
import os
import subprocess
import tempfile
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent
AGENTS = VAULT / 'gebieden/agents'
ENV = VAULT / '.env'
LIJSTEN = ('aandacht',)
STATUSSEN = ('running', 'paused', 'done', 'failed', 'resolved')
# Buiten de vault: anders wijzigt er elke paar seconden een bestand in Obsidian en in git.
WATCHER = Path.home() / '.agent-watcher'
HEARTBEAT = WATCHER / 'heartbeat'
HEARTBEAT_MAX = timedelta(minutes=3)
YOUTRACK_API = 'https://crimsoncricket.myjetbrains.com/youtrack/api'


def yaml_waarde(value):
    if value is None or value == '':
        return ' ""'
    if isinstance(value, bool):
        return ' true' if value else ' false'
    if isinstance(value, list):
        return ' []' if not value else ''.join('\n  - ' + json.dumps(v, ensure_ascii=False) for v in value)
    if isinstance(value, (int, float)):
        return ' %s' % value
    return ' ' + json.dumps(str(value), ensure_ascii=False)


def atomair_schrijven(path, inhoud):
    """Een tijdelijk bestand in dezelfde map en dan `rename`. Zo leest een ander proces (runner,
    watcher, Obsidian) nooit een half geschreven bestand. De punt ervoor verbergt het voor Obsidian."""
    path = Path(path)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name + '.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(inhoud)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def notitie_schrijven(path, fm, tekst, volgorde=()):
    """Schrijft de notitie atomair. Eerst de velden uit `volgorde`, dan de rest in de volgorde van
    `fm`: een gelezen notitie houdt zo zijn volgorde."""
    sleutels = [k for k in volgorde if k in fm] + [k for k in fm if k not in volgorde]
    regels = ['---'] + ['%s:%s' % (k, yaml_waarde(fm[k])) for k in sleutels] + ['---', '']
    atomair_schrijven(path, '\n'.join(regels) + tekst.rstrip() + '\n')


def yaml_lezen(value):
    """Een waarde uit de frontmatter. De runner schrijft JSON, maar Obsidian schrijft de hele frontmatter
    opnieuw als ik daar een property wijzig (`status`): dan staan strings zonder quotes."""
    try:
        return json.loads(value)
    except ValueError:
        pass
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def notitie_lezen(path, lijsten=LIJSTEN):
    """Frontmatter en tekst van een run-notitie, van `notitie_schrijven` of daarna door Obsidian bewerkt.
    Een leeg veld is een lege lijst als het in `lijsten` staat, anders een lege string."""
    inhoud = Path(path).read_text(encoding='utf-8')
    if not inhoud.startswith('---\n'):
        return {}, inhoud
    kop, _, tekst = inhoud[4:].partition('\n---\n')
    fm, key, blok = {}, None, None
    for line in kop.splitlines():
        if blok is not None and (line.startswith('  ') or not line.strip()):
            blok.append(line[2:])
            continue
        if blok is not None:  # einde van een blok-string (`|-` of `>-`) van Obsidian
            fm[key] = ('\n' if fm[key].startswith('|') else ' ').join(blok).strip('\n')
            blok = None
        if line.lstrip().startswith('- ') and key:
            fm[key].append(yaml_lezen(line.lstrip()[2:].strip()))
            continue
        key, _, value = line.partition(':')
        key, value = key.strip(), value.strip()
        if value[:1] in ('|', '>'):
            fm[key], blok = value, []
        elif value[:1] == '[' and value[-1:] == ']':  # inline lijst, zoals `lijsten: [prs]`
            fm[key] = [yaml_lezen(v.strip()) for v in value[1:-1].split(',') if v.strip()]
        else:
            fm[key] = [] if value in ('', '[]') else yaml_lezen(value)
    if blok is not None:
        fm[key] = ('\n' if fm[key].startswith('|') else ' ').join(blok).strip('\n')
    for key, value in fm.items():
        if value == [] and key not in lijsten:
            fm[key] = ''
    return fm, tekst.lstrip('\n')


def agents(map=AGENTS):
    """De agents uit gebieden/agents/<agent>.md met een veld `runs`: {naam: frontmatter}, met `runs`
    als Path. Andere notities in die map, zoals agent-runs.md, tellen niet mee."""
    result = {}
    for path in sorted(Path(map).glob('*.md')):
        fm, _ = notitie_lezen(path)
        if fm.get('runs'):
            result[path.stem] = dict(fm, runs=VAULT / fm['runs'], lijsten=LIJSTEN + tuple(fm.get('lijsten') or ()))
    return result


def notities(runs, agent):
    """De run-notities van deze agent in map `runs`: alleen die met `agent: <agent>`. Andere notities
    in de map, zoals een eigen dashboard, worden zo nooit opnieuw geschreven."""
    runs = Path(runs)
    if not runs.is_dir():
        return []
    return [p for p in sorted(runs.glob('*.md')) if notitie_lezen(p)[0].get('agent') == agent]


def laatste_per_onderwerp(paden, lijsten=LIJSTEN):
    """{onderwerp: (path, fm, tekst)} met per onderwerp de run met de laatste `started`."""
    laatste = {}
    for path in paden:
        fm, tekst = notitie_lezen(path, lijsten)
        vorige = laatste.get(fm.get('onderwerp'))
        if vorige is None or fm.get('started', '') >= vorige[1].get('started', ''):
            laatste[fm.get('onderwerp')] = (path, fm, tekst)
    return laatste


def proces_leeft(pid, naam='claude'):
    """Leeft het proces nog, en heet het `naam`? Een hergebruikt pid telt niet."""
    try:
        os.kill(int(pid), 0)
    except (ProcessLookupError, ValueError, TypeError):
        return False
    except PermissionError:
        pass
    comm = subprocess.run(['ps', '-o', 'comm=', '-p', str(pid)], capture_output=True, text=True).stdout
    return os.path.basename(comm.strip()) == naam


def afgehandeld(fm):
    """Het issue staat op Done, of ik heb de run vrijgegeven (`resolved`)."""
    return fm.get('issue_state') == 'Done' or fm.get('status') == 'resolved'


def wacht_op_mij(fm):
    status = fm.get('status')
    return (status != 'running' and not afgehandeld(fm)
            and (status in ('paused', 'failed') or bool(fm.get('aandacht'))))


def beschrijving(fm):
    """De `description` van een run-notitie, zoals `Debbie-run cata, gestart 2026-11-18 12:25: paused bij
    stap 4 (CATA-123)`. Runner en watcher schrijven hem opnieuw als de status verandert."""
    status = fm['status'] + (' bij stap %s' % fm['step'] if fm.get('step') else '')
    issue = ' (%s)' % fm['issue'] if fm.get('issue') else ''
    return '%s-run %s, gestart %s: %s%s' % (str(fm['agent']).capitalize(), fm['onderwerp'],
                                           fm['started'][:16].replace('T', ' '), status, issue)


def melden(titel, tekst):
    """macOS-melding. Een comment op mijn eigen issue geeft waarschijnlijk geen notificatie."""
    subprocess.run(['osascript', '-e', 'on run argv', '-e',
                    'display notification (item 2 of argv) with title (item 1 of argv)', '-e', 'end run',
                    titel, tekst], check=False, capture_output=True)


def env_waarde(naam):
    """Uit ~/vault/.env, of None. Wordt nooit getoond."""
    for line in reversed(ENV.read_text().splitlines()):
        if line.startswith(naam + '='):
            return line.split('=', 1)[1].strip().strip('"\'')
    return None


def youtrack_get(pad):
    """JSON van de REST-API van YouTrack. Gooit een fout bij netwerk, YouTrack of een ontbrekend token."""
    token = env_waarde('YOUTRACK_TOKEN')
    if not token:
        raise LookupError('YOUTRACK_TOKEN ontbreekt in ' + str(ENV))
    headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/json'}
    return json.load(urllib.request.urlopen(urllib.request.Request(YOUTRACK_API + pad, headers=headers), timeout=30))


def issue_state(issue):
    """De State van het issue in YouTrack. Gooit een fout als dat niet lukt."""
    velden = youtrack_get('/issues/%s?fields=customFields(name,value(name))' % issue)
    return next(((f.get('value') or {}).get('name') for f in velden.get('customFields', [])
                 if f.get('name') == 'State'), None)


def heartbeat_schrijven(nu):
    WATCHER.mkdir(exist_ok=True)
    atomair_schrijven(HEARTBEAT, nu.isoformat(timespec='seconds') + '\n')


def watcher_stil(nu):
    """None als de watcher leeft, anders sinds wanneer niet (een datetime) of 'nooit'."""
    try:
        laatste = datetime.fromisoformat(HEARTBEAT.read_text(encoding='utf-8').strip())
    except (OSError, ValueError):
        return 'nooit'
    return None if nu - laatste <= HEARTBEAT_MAX else laatste
