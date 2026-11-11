#!/usr/bin/python3
"""Runner van de autonome Dependabot-routine (Debbie). Nu: repo's selecteren en clones klaarzetten.

Gebruik: dependabot_runner.py --dry-run [--repo NAAM ...]
Toont per project uit de skill welke repo's nu een run zouden krijgen, zonder iets te wijzigen.
Een repo komt in aanmerking als er open PR's zijn van de auteurs uit de frontmatter `authors`
(standaard app/dependabot) en alle checks klaar zijn. Een repo met een lopende, gepauzeerde of
mislukte run, of een run die deze ISO-week al klaar is met dezelfde PR's, slaat hij over.

Gebruik: dependabot_runner.py --prepare --repo NAAM [--repo NAAM ...]
Zet de clone in ~/dependabot-runs/NAAM klaar (clonen of fetchen, moet schoon zijn) en toont de
tools die een run daar krijgt. Werkt ook zonder mijn shellprofiel, zoals onder launchd.
Plan: gebieden/werk/dependabot-routine-autonoom-plan.md.
"""
import argparse
import json
import os
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
    """Uit ~/vault/.env, voor ${YOUTRACK_TOKEN} in mcp.json. Wordt nooit getoond."""
    for line in reversed((VAULT / '.env').read_text().splitlines()):
        if line.startswith('YOUTRACK_TOKEN='):
            return line.split('=', 1)[1].strip()
    raise Stop('YOUTRACK_TOKEN ontbreekt in ' + str(VAULT / '.env'))


def omgeving(clone):
    """De omgeving voor `claude` in deze clone. Gaat niet uit van mijn shellprofiel."""
    env = basis_env()
    node = node_bin(clone)
    if node:
        env['PATH'] = node + ':' + env['PATH']
    env['CLAUDE_ENV_FILE'] = str(RUNNER / 'env.sh')
    env['YOUTRACK_TOKEN'] = youtrack_token()
    return env


def claude_args(project, clone):
    """De vaste flags voor een run, behalve prompt, sessie, model en output (stap 7)."""
    settings = json.loads((RUNNER / 'settings.json').read_text())
    # Mijn globale CLAUDE.md noemt bijvoorbeeld youtrack_edit_comment.py, en dat mag de run niet.
    settings['claudeMdExcludes'] = [str(HOME / '.claude/CLAUDE.md')]
    return ['--add-dir', str(VAULT), '--add-dir', str(CLONES / '.scratch' / project['name']),
            '--setting-sources', 'project,local', '--settings', json.dumps(settings),
            '--strict-mcp-config', '--mcp-config', str(RUNNER / 'mcp.json'),
            '--permission-mode', 'dontAsk', '--permission-prompts', 'none']


def tools_tonen(clone, env):
    """Draait de tools zoals een Bash-commando van de run ze ziet: met env.sh in de clone."""
    script = ('. "$CLAUDE_ENV_FILE"; for t in git gh claude java mvn gradle node npm; do printf "%-7s" $t; '
              'command -v $t || echo ontbreekt; done; java -version 2>&1 | head -1; mvn -v 2>/dev/null | head -1; '
              'node -v 2>/dev/null; claude --version; gh auth status 2>&1 | grep -E "Logged in|Token scopes"; '
              'claude auth status 2>&1 | grep -i -E "logged|login|method" | head -2; '
              'git ls-remote --heads origin >/dev/null && echo "git via HTTPS: ok"')
    return run(['/bin/zsh', '-f', '-c', script], cwd=clone, env=env)


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
    parser.add_argument('--prepare', action='store_true', help='clone klaarzetten en de tools tonen')
    parser.add_argument('--repo', action='append', default=[], help='alleen dit project (herhaalbaar)')
    args = parser.parse_args()
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
    if not args.dry_run:
        raise SystemExit('Runs starten kan nog niet (stap 7 van het plan). Gebruik --dry-run of --prepare.')
    breedte = max(len(p.stem) for p in PROJECTEN.glob('*.md'))
    for project, prs, besluit, reden in selecteer(args.repo):
        nummers = ' '.join('#%d' % pr['number'] for pr in prs)
        regel = '%-*s  %-9s  %s' % (breedte, project['name'], besluit, nummers)
        print((regel + ('  — ' + reden if reden and besluit != 'niets' else '')).rstrip())


if __name__ == '__main__':
    sys.exit(main())
