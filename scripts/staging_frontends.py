#!/usr/bin/python3
"""Frontends voor een staging-uitrol releasen naar de private npm-repo.

Leest de frontends uit data/staging-repos.json. De releaseversie is de versie in package.json op
develop (npm kent geen -SNAPSHOT). Een frontend die in een andere frontend zit (veld "in"), gaat
eerst: portal-ui-common vóór portal-employee-ui en portal-worker-ui.

Er is geen stoppunt: na het plan (clones in ~/staging-runs/<repo>, alleen lezen) start elke
frontend in een eigen thread en wacht alleen op de frontends die hij nodig heeft:
1. "Prepare release": pas als de frontend waarvan hij afhangt gepubliceerd is, die versie in
   package.json en package-lock.json zetten (branch feature/prepare-release-X.Y.Z, PR naar develop,
   squash-merge na groene checks).
2. "Release X.Y.Z": PR develop → master met een merge-commit, alleen als develop nog op de stand
   uit het plan staat. Daarna wachten op master.yml en op precies die versie in de npm-repo.
3. "Update for next development version" (branch feature/next-version-X.Y.Z, minor-versie omhoog), zodra
   de frontend zelf en zijn afnemers gepubliceerd zijn. De develop-build van portal-ui-common zet
   de lock files van employee en worker terug op develop; dat mag pas na hun release.
De stand staat in ~/staging-runs/frontends.json. staging_release_branches.py start deze keten
zelf (klasse Keten) en laat iam en portal wachten op hun frontends.
Het script pusht alleen feature/prepare-release-* en feature/next-version-* van frontends uit de
config, nooit met --force. (PR's naar develop moeten van feature/*, hotfix/* of dependabot/* komen:
dat eist de org-brede workflow "GitFlow Pull Request Validator".)
Stond een frontend al in de npm-repo en staat develop nog op die versie, dan volgt alleen nog de
volgende versie.
Gebruik: staging_frontends.py [--plan] [--repos A,B] [--uit BESTAND]. Met --plan alleen het plan.
"""
import datetime
import json
import os
import re
import subprocess
import sys
import threading
import time

DATA = os.path.expanduser('~/vault/data/staging-repos.json')
RUNS = os.path.expanduser('~/staging-runs')
STATE = os.path.join(RUNS, 'frontends.json')
START, EIND = '<!-- frontends:start -->', '<!-- frontends:eind -->'
PR_BODY = 'Opened by `staging_frontends.py` for a staging release.\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)'


class Afwijking(Exception):
    """Deze frontend kan niet verder; de melding komt in de samenvatting."""


def run(cwd, *args):
    return subprocess.run(list(args), cwd=cwd, check=True, capture_output=True, text=True).stdout


def git(cwd, *args):
    return run(cwd, 'git', *args)


def gh(*args):
    return run(None, 'gh', *args)


def clone(org, repo):
    pad = os.path.join(RUNS, repo)
    if not os.path.isdir(os.path.join(pad, '.git')):
        os.makedirs(RUNS, exist_ok=True)
        run(None, 'git', 'clone', '-q', 'git@github.com:%s/%s.git' % (org, repo), pad)
    git(pad, 'config', 'core.autocrlf', 'false')
    git(pad, 'fetch', '-q', '--prune', 'origin')
    git(pad, 'checkout', '-q', '--detach', 'origin/develop')
    git(pad, 'reset', '-q', '--hard')
    git(pad, 'clean', '-qfdx')
    return pad


def package(pad):
    return json.load(open(os.path.join(pad, 'package.json')))


def pompkracht_deps(pkg):
    return {naam: spec for soort in ('dependencies', 'devDependencies', 'peerDependencies')
            for naam, spec in pkg.get(soort, {}).items() if naam.startswith('@pompkracht/')}


def gepubliceerd(pad, naam, versie):
    """Staat precies deze versie in de npm-repo? Niet op dist-tags vertrouwen: die staan soms verkeerd."""
    r = subprocess.run(['npm', 'view', '%s@%s' % (naam, versie), 'version', '--prefer-online'],
                       cwd=pad, capture_output=True, text=True)
    return r.returncode == 0 and r.stdout.strip() == versie


def volgorde(frontends):
    """Frontends gesorteerd zodat elke frontend na de frontends komt die erin zitten."""
    namen = {e['repo'] for e in frontends}
    deps = {e['repo']: [] for e in frontends}
    for e in frontends:
        for afnemer in e.get('in', '').split():
            if afnemer in namen:
                deps[afnemer].append(e['repo'])
    klaar = []
    while len(klaar) < len(deps):
        # Frontends waar andere op wachten eerst, zodat hun build al loopt.
        vrij = sorted((r for r in deps if r not in klaar and all(d in klaar for d in deps[r])),
                      key=lambda r: (not any(r in d for d in deps.values()), r))
        if not vrij:
            raise SystemExit('Kring in de "in"-velden van de frontends')
        klaar += vrij
    return klaar, deps


def plannen(org, repo, deps, plan):
    pad = clone(org, repo)
    pkg = package(pad)
    versie = pkg['version']
    if not re.fullmatch(r'\d+\.\d+\.\d+', versie):
        raise Afwijking('versie `%s` in package.json is geen X.Y.Z' % versie)
    m = {'versie': versie, 'pakket': pkg['name'], 'develop': git(pad, 'rev-parse', 'origin/develop').strip(),
         'commits': int(git(pad, 'rev-list', '--count', 'origin/master..origin/develop'))}
    if gepubliceerd(pad, pkg['name'], versie):
        m['gepubliceerd'] = 'al eerder'
        return m
    if not m['commits']:
        raise Afwijking('develop loopt niet voor op master, maar %s staat niet in de npm-repo' % versie)
    pinnen = {}
    for naam, spec in pompkracht_deps(pkg).items():
        if '-' not in spec:
            continue
        dep = naam.split('/', 1)[1]
        if dep not in deps[repo]:
            raise Afwijking('`%s` staat op develop-build `%s` en wordt niet door dit script gereleased' % (naam, spec))
        if 'versie' not in plan.get(dep, {}):
            raise Afwijking('`%s` hangt af van %s, en die staat niet (goed) in het plan' % (repo, dep))
        pinnen[naam] = plan[dep]['versie']
    m['pinnen'] = pinnen
    open_prs = json.loads(gh('pr', 'list', '-R', '%s/%s' % (org, repo), '--base', 'master', '--head', 'develop',
                             '--json', 'number'))
    if open_prs:
        raise Afwijking('er staat al een PR develop → master open: #%d' % open_prs[0]['number'])
    for prefix in ('feature/prepare-release-', 'feature/next-version-'):
        if git(pad, 'ls-remote', '--heads', 'origin', prefix + '*').strip():
            raise Afwijking('er staat al een %s*-branch op de remote' % prefix)
    return m


def diff(pad, branch):
    """Bestanden en (weg, erbij)-regels van de diff origin/develop..branch."""
    bestanden = set(git(pad, 'diff', '--name-only', 'origin/develop', branch).split())
    weg, erbij = [], []
    for regel in git(pad, 'diff', '--unified=0', 'origin/develop', branch).split('\n'):
        if regel.startswith('-') and not regel.startswith('---'):
            weg.append(regel[1:])
        elif regel.startswith('+') and not regel.startswith('+++'):
            erbij.append(regel[1:])
    return bestanden, weg, erbij


def pushen(pad, branch):
    if git(pad, 'ls-remote', '--heads', 'origin', branch).strip():
        raise Afwijking('branch %s staat al op de remote' % branch)
    ref = 'refs/heads/' + branch
    git(pad, 'push', '-q', 'origin', '%s:%s' % (ref, ref))


def pr_maken(org, repo, base, head, titel):
    url = gh('pr', 'create', '-R', '%s/%s' % (org, repo), '--base', base, '--head', head,
             '--title', titel, '--body', PR_BODY).strip().split('\n')[-1]
    return int(url.rstrip('/').rsplit('/', 1)[1])


def checks_afwachten(org, repo, nr, max_minuten=30):
    """Wacht tot de checks van de PR klaar zijn; geen checks na twee minuten is ook goed."""
    begin = time.time()
    while time.time() < begin + max_minuten * 60:
        time.sleep(20)
        r = subprocess.run(['gh', 'pr', 'checks', str(nr), '-R', '%s/%s' % (org, repo), '--json', 'name,bucket'],
                           capture_output=True, text=True)
        try:
            checks = json.loads(r.stdout)
        except ValueError:
            checks = []
        if not checks:
            if time.time() > begin + 120:
                return
            continue
        fout = [c['name'] for c in checks if c['bucket'] in ('fail', 'cancel')]
        if fout:
            raise Afwijking('checks van PR #%d faalden: %s' % (nr, ', '.join(fout)))
        if all(c['bucket'] in ('pass', 'skipping') for c in checks):
            return
    raise Afwijking('checks van PR #%d na %d minuten nog niet klaar' % (nr, max_minuten))


def mergen(org, repo, nr, *opties):
    gh('pr', 'merge', str(nr), '-R', '%s/%s' % (org, repo), *opties)
    pr = json.loads(gh('pr', 'view', str(nr), '-R', '%s/%s' % (org, repo), '--json', 'state,mergeCommit'))
    if pr['state'] != 'MERGED':
        raise Afwijking('PR #%d is niet gemerged (%s)' % (nr, pr['state']))
    return pr['mergeCommit']['oid']


def develop_controleren(pad, m):
    git(pad, 'fetch', '-q', '--prune', 'origin')
    if git(pad, 'rev-parse', 'origin/develop').strip() != m['develop']:
        raise Afwijking('origin/develop is veranderd sinds het plan; maak opnieuw een plan')


def prepare_release(org, repo, m):
    """Develop-builds van andere frontends vervangen door hun releaseversie."""
    pad = os.path.join(RUNS, repo)
    develop_controleren(pad, m)
    branch = 'feature/prepare-release-' + m['versie']
    git(pad, 'checkout', '-q', '-B', branch, 'origin/develop')
    oud = pompkracht_deps(package(pad))
    run(pad, 'npm', 'install', '--package-lock-only', '--ignore-scripts', '--prefer-online',
        *['%s@%s' % (naam, versie) for naam, versie in sorted(m['pinnen'].items())])
    lock = json.load(open(os.path.join(pad, 'package-lock.json')))
    for naam, versie in m['pinnen'].items():
        if lock['packages'].get('node_modules/' + naam, {}).get('version') != versie:
            raise Afwijking('`%s` staat na npm install niet op %s in package-lock.json' % (naam, versie))
    git(pad, 'add', 'package.json', 'package-lock.json')
    git(pad, 'commit', '-q', '-m', 'Prepare release ' + m['versie'])
    bestanden, weg, erbij = diff(pad, branch)
    if not bestanden <= {'package.json', 'package-lock.json'}:
        raise Afwijking('diff raakt onverwachte bestanden: %s' % ', '.join(sorted(bestanden)))
    nieuw = pompkracht_deps(package(pad))
    gewijzigd = {n for n in set(oud) | set(nieuw) if oud.get(n) != nieuw.get(n)}
    if gewijzigd != set(m['pinnen']) or any(nieuw[n] != '^' + v for n, v in m['pinnen'].items()):
        raise Afwijking('package.json verandert anders dan verwacht: %s' % ', '.join(sorted(gewijzigd)))
    m['lock_regels'] = len(weg) + len(erbij)
    pushen(pad, branch)
    nr = pr_maken(org, repo, 'develop', branch, 'Prepare release ' + m['versie'])
    m['prepare_pr'] = nr
    checks_afwachten(org, repo, nr)
    m['develop'] = mergen(org, repo, nr, '--squash', '--delete-branch')


def release(org, repo, m):
    pad = os.path.join(RUNS, repo)
    develop_controleren(pad, m)
    git(pad, 'checkout', '-q', '--detach', 'origin/develop')
    pkg = package(pad)
    if pkg['version'] != m['versie']:
        raise Afwijking('versie op develop is %s, verwacht %s' % (pkg['version'], m['versie']))
    rest = ['%s %s' % (n, s) for n, s in pompkracht_deps(pkg).items() if '-' in s]
    if rest:
        raise Afwijking('nog develop-builds op develop: %s' % ', '.join(rest))
    titel = 'Release ' + m['versie']
    nr = pr_maken(org, repo, 'master', 'develop', titel)
    m['release_pr'] = nr
    head = json.loads(gh('pr', 'view', str(nr), '-R', '%s/%s' % (org, repo), '--json', 'headRefOid'))['headRefOid']
    if head != m['develop']:
        raise Afwijking('PR #%d wijst naar %s, niet naar develop uit het plan' % (nr, head[:8]))
    checks_afwachten(org, repo, nr)
    m['release'] = mergen(org, repo, nr, '--merge', '--subject', titel, '--body', '')


def publicatie_afwachten(org, repo, m, max_minuten=30):
    pad = os.path.join(RUNS, repo)
    einde = time.time() + max_minuten * 60
    while time.time() < einde:
        time.sleep(30)
        runs = json.loads(gh('run', 'list', '-R', '%s/%s' % (org, repo), '--commit', m['release'],
                             '--workflow', 'master.yml', '--limit', '1', '--json', 'status,conclusion,url'))
        if not runs or runs[0]['status'] != 'completed':
            continue
        m['run'] = runs[0]['url']
        if runs[0]['conclusion'] != 'success':
            raise Afwijking('master-build %s' % runs[0]['conclusion'])
        for _ in range(10):
            if gepubliceerd(pad, m['pakket'], m['versie']):
                m['gepubliceerd'] = datetime.datetime.now().isoformat(timespec='seconds')
                return
            time.sleep(15)
        raise Afwijking('master-build geslaagd, maar %s staat niet in de npm-repo' % m['versie'])
    raise Afwijking('master-build na %d minuten nog niet klaar' % max_minuten)


def volgende_versie(org, repo, m):
    pad = os.path.join(RUNS, repo)
    git(pad, 'fetch', '-q', '--prune', 'origin')
    git(pad, 'checkout', '-q', '--detach', 'origin/develop')
    huidig = package(pad)['version']
    if huidig != m['versie']:
        raise Afwijking('versie op develop is al %s' % huidig)
    major, minor, _ = (int(n) for n in huidig.split('.'))
    nieuw = '%d.%d.0' % (major, minor + 1)
    branch = 'feature/next-version-' + nieuw
    git(pad, 'checkout', '-q', '-B', branch, 'origin/develop')
    run(pad, 'npm', 'version', nieuw, '--no-git-tag-version', '--ignore-scripts')
    git(pad, 'add', 'package.json', 'package-lock.json')
    git(pad, 'commit', '-q', '-m', 'Update for next development version')
    bestanden, weg, erbij = diff(pad, branch)
    if not bestanden <= {'package.json', 'package-lock.json'}:
        raise Afwijking('diff raakt onverwachte bestanden: %s' % ', '.join(sorted(bestanden)))
    if (any(r.strip().rstrip(',') != '"version": "%s"' % huidig for r in weg)
            or any(r.strip().rstrip(',') != '"version": "%s"' % nieuw for r in erbij)):
        raise Afwijking('diff bevat andere regels dan de versie')
    pushen(pad, branch)
    nr = pr_maken(org, repo, 'develop', branch, 'Update for next development version')
    m['volgende_pr'] = nr
    checks_afwachten(org, repo, nr)
    mergen(org, repo, nr, '--squash', '--delete-branch')
    m['volgende'] = nieuw


def status(m):
    if 'fout' in m:
        return 'gepubliceerd, volgende versie mislukt' if 'gepubliceerd' in m else 'fout'
    if 'volgende' in m:
        return 'gepubliceerd, develop op %s' % m['volgende']
    if m.get('gepubliceerd') == 'al eerder':
        return 'stond al in de npm-repo'
    if 'gepubliceerd' in m:
        return 'gepubliceerd'
    if 'release' in m:
        return 'gemerged naar master, build loopt'
    return 'gepland'


def samenvatting(datum, resultaten, uitgevoerd):
    intro = ('Uitgevoerd op %s.' % datum if uitgevoerd else
             'Alleen gepland op %s (`--plan`), nog niets gepusht of gemerged.' % datum)
    regels = [START, '## Frontends', '', intro, '']
    afwijkingen = [(r, m) for r, m in resultaten.items() if 'fout' in m]
    if afwijkingen:
        regels += ['### Afwijkingen', '']
        regels += ['- **%s**: %s%s' % (r, m['fout'], ', [run](%s)' % m['run'] if 'run' in m else '')
                   for r, m in afwijkingen] + ['']
    regels += ['| Frontend | Versie | Commits | Eerst pinnen | PR\'s | Status |',
               '| --- | --- | --- | --- | --- | --- |']
    for r, m in resultaten.items():
        if 'versie' not in m:
            continue
        prs = ', '.join('#%d' % m[k] for k in ('prepare_pr', 'release_pr', 'volgende_pr') if k in m) or '-'
        pinnen = '<br>'.join('`%s` %s' % (n.split('/', 1)[1], v) for n, v in m.get('pinnen', {}).items()) or '-'
        regels.append('| `%s` | %s | %d | %s | %s | %s |' % (
            r, m['versie'], m['commits'], pinnen, prs, status(m)))
    return '\n'.join(regels + ['', EIND])


def schrijf_sectie(pad, sectie):
    """Vervangt de sectie, of zet hem boven de release branches en de eerste kop."""
    tekst = open(pad).read() if os.path.exists(pad) else ''
    if START in tekst and EIND in tekst:
        tekst = tekst[:tekst.index(START)] + sectie + tekst[tekst.index(EIND) + len(EIND):]
    else:
        m = re.search(r'^(<!-- release-branches:start -->|## )', tekst, re.M)
        tekst = (tekst[:m.start()] + sectie + '\n\n' + tekst[m.start():]) if m else tekst.rstrip('\n') + '\n\n' + sectie + '\n'
    open(pad, 'w').write(tekst)


def uitvoer(uit, sectie):
    if uit:
        schrijf_sectie(uit, sectie)
        print('Samenvatting geschreven in %s' % uit, file=sys.stderr)
    else:
        print(sectie)


def fout(m, e):
    if isinstance(e, subprocess.CalledProcessError):
        m['fout'] = '`%s` faalde: %s' % (' '.join(e.cmd[:3]), (e.stderr or e.stdout or '').strip()[-300:])
    else:
        m['fout'] = str(e)


class Keten:
    """De frontendketen: elke frontend in een eigen thread, die alleen wacht op wat hij nodig heeft."""

    def __init__(self, cfg, alleen=None):
        self.org = cfg['org']
        frontends = [e for e in cfg['repos'] if e['rol'] == 'frontend']
        self.orde, self.deps = volgorde(frontends)
        if alleen:
            nodig = set()
            while alleen - nodig:
                nodig |= alleen
                alleen = alleen | {d for r in alleen for d in self.deps.get(r, [])}
            self.orde = [r for r in self.orde if r in nodig]
        self.afnemers = {r: [a for a in self.orde if r in self.deps[a]] for r in self.orde}
        self.repos, self.snapshot = {}, {}
        self.klaar = {r: threading.Event() for r in self.orde}
        self.lock = threading.Lock()
        self.threads = []
        self.datum = datetime.date.today().isoformat()

    def plannen(self):
        for repo in self.orde:
            print('%s: plan' % repo, file=sys.stderr)
            try:
                self.repos[repo] = plannen(self.org, repo, self.deps, self.repos)
            except (Afwijking, subprocess.CalledProcessError) as e:
                self.repos[repo] = {}
                fout(self.repos[repo], e)
            self.bewaar(repo)

    def bewaar(self, repo):
        """Alleen de thread van repo verandert self.repos[repo]; hij maakt zelf de kopie."""
        kopie = json.loads(json.dumps(self.repos[repo]))
        with self.lock:
            self.snapshot[repo] = kopie
            json.dump({'datum': self.datum, 'repos': self.snapshot}, open(STATE, 'w'), indent=2)

    def starten(self):
        for repo in self.orde:
            t = threading.Thread(target=self.afwerken, args=(repo,), daemon=True)
            t.start()
            self.threads.append(t)

    def gepubliceerd(self, repo):
        """Wacht tot de frontend gepubliceerd is of faalde; True als hij in de npm-repo staat."""
        self.klaar[repo].wait()
        return 'gepubliceerd' in self.repos[repo]

    def afwachten(self):
        for t in self.threads:
            t.join()

    def afwerken(self, repo):
        m = self.repos[repo]
        try:
            if 'fout' not in m and 'gepubliceerd' not in m:
                mislukt = [d for d in self.deps[repo] if not self.gepubliceerd(d)]
                if mislukt:
                    raise Afwijking('%s is niet gepubliceerd' % ', '.join(mislukt))
                if m['pinnen']:
                    print('%s: prepare release %s' % (repo, m['versie']), file=sys.stderr)
                    prepare_release(self.org, repo, m)
                    self.bewaar(repo)
                print('%s: release %s' % (repo, m['versie']), file=sys.stderr)
                release(self.org, repo, m)
                self.bewaar(repo)
                print('%s: wacht op publicatie' % repo, file=sys.stderr)
                publicatie_afwachten(self.org, repo, m)
                print('%s: %s gepubliceerd' % (repo, m['versie']), file=sys.stderr)
        except Exception as e:
            fout(m, e)
        finally:
            self.bewaar(repo)
            self.klaar[repo].set()
        if 'fout' in m or 'gepubliceerd' not in m:
            return
        # De develop-build van deze frontend zet de lock files van zijn afnemers terug op @develop:
        # pas als die gepubliceerd zijn.
        try:
            mislukt = [a for a in self.afnemers[repo] if not self.gepubliceerd(a)]
            if mislukt:
                raise Afwijking('volgende versie niet gemaakt: %s is niet gepubliceerd' % ', '.join(mislukt))
            print('%s: volgende versie' % repo, file=sys.stderr)
            volgende_versie(self.org, repo, m)
        except Exception as e:
            fout(m, e)
        self.bewaar(repo)

    def uitvoer(self, uit, uitgevoerd=True):
        """Met de markers van dit script, ook als het releasescript de keten heeft gestart."""
        uitvoer(uit, self.samenvatting(uitgevoerd))

    def samenvatting(self, uitgevoerd=True):
        return samenvatting(self.datum, {r: self.repos[r] for r in self.orde if r in self.repos}, uitgevoerd)


def main():
    args = sys.argv[1:]
    uit = args[args.index('--uit') + 1] if '--uit' in args else None
    alleen = set(args[args.index('--repos') + 1].split(',')) if '--repos' in args else None
    cfg = json.load(open(DATA))
    keten = Keten(cfg, alleen)
    if alleen and alleen - set(keten.orde):
        raise SystemExit('Onbekende frontend: %s' % ', '.join(sorted(alleen - set(keten.orde))))
    controleer_token()
    keten.plannen()
    if '--plan' not in args:
        keten.starten()
        keten.afwachten()
    keten.uitvoer(uit, '--plan' not in args)


def controleer_token():
    if not os.environ.get('NPM_TOKEN'):
        raise SystemExit('NPM_TOKEN ontbreekt; zonder token kan npm de private repo niet lezen')


if __name__ == '__main__':
    main()
