#!/usr/bin/python3
"""Runner van de autonome Dependabot-routine (Debbie). Nu alleen de selectie van repo's.

Gebruik: dependabot_runner.py --dry-run [--repo NAAM ...]
Toont per project uit de skill welke repo's nu een run zouden krijgen, zonder iets te wijzigen.
Een repo komt in aanmerking als er open PR's zijn van de auteurs uit de frontmatter `authors`
(standaard app/dependabot) en alle checks klaar zijn. Een repo met een lopende, gepauzeerde of
mislukte run, of een run die deze ISO-week al klaar is met dezelfde PR's, slaat hij over.
Plan: gebieden/werk/dependabot-routine-autonoom-plan.md.
"""
import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent
PROJECTEN = VAULT / '.claude/skills/dependabot-routine/projecten'
RUNS = VAULT / 'gebieden/werk/dependabot-runs'
DEFAULT_AUTHORS = ['app/dependabot']
# Zo lang na het openen van een PR zonder checks wachten we nog tot de checks verschijnen.
GEEN_CHECKS_WACHTTIJD = timedelta(minutes=30)
PENDING_STATES = {'PENDING', 'EXPECTED'}


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
        result.append({'name': path.stem, 'repo': fm['repo'], 'authors': fm.get('authors') or DEFAULT_AUTHORS})
    return result


def open_prs(repo, authors):
    prs = []
    for author in authors:
        out = subprocess.run(
            ['gh', 'pr', 'list', '--repo', repo, '--author', author, '--state', 'open', '--limit', '50',
             '--json', 'number,headRefOid,createdAt,statusCheckRollup'],
            check=True, capture_output=True, text=True).stdout
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
    if not RUNS.is_dir():
        return None
    runs = [fm for fm in (frontmatter(p) for p in RUNS.glob('*.md') if p.name != 'index.md')
            if fm.get('repo') in (name,) or str(fm.get('repo', '')).endswith('/' + name)]
    return max(runs, key=lambda fm: fm.get('started', ''), default=None)


def iso_week(moment):
    return moment.isocalendar()[:2]


def beoordeel(project, prs, run, nu):
    """Geeft (besluit, reden): besluit is `run`, `wacht`, `overslaan` of `niets`."""
    if not prs:
        return 'niets', "geen open PR's"
    if run and run.get('status') == 'running':
        return 'overslaan', 'run loopt al (%s)' % run.get('session_id', '?')
    if run and run.get('status') in ('paused', 'failed'):
        return 'overslaan', 'vorige run is %s, wacht op mij (%s)' % (run['status'], run.get('issue', '?'))
    bezig = [pr['number'] for pr in prs if not checks_klaar(pr, nu)]
    if bezig:
        return 'wacht', 'checks lopen nog: ' + ' '.join('#%d' % n for n in bezig)
    if run and run.get('status') == 'done' and run.get('started'):
        gestart = datetime.fromisoformat(run['started'].replace('Z', '+00:00'))
        if iso_week(gestart.astimezone()) == iso_week(nu.astimezone()) and \
                sorted(run.get('prs') or []) == sorted(vingerafdruk(prs)):
            return 'overslaan', "deze week al gedaan met dezelfde PR's (%s)" % run.get('issue', '?')
    return 'run', ''


def selecteer(namen):
    nu = datetime.now(timezone.utc)
    lijst = [p for p in projecten() if not namen or p['name'] in namen]
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
    parser.add_argument('--repo', action='append', default=[], help='alleen dit project (herhaalbaar)')
    args = parser.parse_args()
    if not args.dry_run:
        raise SystemExit('Runs starten kan nog niet (stap 7 van het plan). Gebruik --dry-run.')
    breedte = max(len(p.stem) for p in PROJECTEN.glob('*.md'))
    for project, prs, besluit, reden in selecteer(args.repo):
        nummers = ' '.join('#%d' % pr['number'] for pr in prs)
        regel = '%-*s  %-9s  %s' % (breedte, project['name'], besluit, nummers)
        print((regel + ('  — ' + reden if reden and besluit != 'niets' else '')).rstrip())


if __name__ == '__main__':
    sys.exit(main())
