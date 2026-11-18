#!/usr/bin/python3
"""Run-notities van de autonome agents lezen en schrijven, volgens gebieden/agents/agent-runs.md.

Gedeeld door de runners (zoals dependabot_runner.py), en later het dashboard en de watcher.
Plan: gebieden/vault/agents-dashboard-plan.md.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent
AGENTS = VAULT / 'gebieden/agents'
LIJSTEN = ('aandacht',)
STATUSSEN = ('running', 'paused', 'done', 'failed', 'resolved')


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
