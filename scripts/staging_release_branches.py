#!/usr/bin/python3
"""Release branches voor een staging-uitrol klaarzetten, in eigen clones.

Leest de image-repo's uit data/staging-repos.json en maakt per repo in ~/staging-runs/<repo>
een branch release/X.Y.Z vanaf origin/develop, met één commit "Prepare release X.Y.Z": de
versie zonder -SNAPSHOT (bij npm blijft package.json zoals hij is), het base image gepind op
de nieuwste tag met digest van Docker Hub, en bij iam en portal de frontendversies in het
pre-release-profiel (uit package.json op master van de frontend). Daarna controleert het per repo
of de diff alleen die regels raakt, en legt het de stand vast in ~/staging-runs/state.json. Van
de image-repo's wordt niets gepusht: dat is het stoppunt.
Tegelijk start het de frontendketen uit staging_frontends.py, parallel en zonder stoppunt. Die
released de frontends naar de npm-repo en pusht en merget daarvoor zelf, alleen bij frontends
uit de config: feature/prepare-release-* en feature/next-version-*, en PR's naar develop en
master. De repo's
zonder frontends worden meteen klaargezet, iam en portal pas als hun eigen frontends
gepubliceerd zijn.
Met --push worden de klaargezette branches uit de state gepusht, alleen als de branch en
origin/develop nog precies zo zijn als bij het klaarzetten. Daarna volgt het script de
pre-release-runs en zet het de RC-tags in de state.
Direct na het pushen zet --push de YouTrack-tag "release candidate" op de hoofdissues van wat er
in de release zit: de commits in master...release/X.Y.Z van elke image-repo met een open release
branch, en in de release-merge van elke frontend die vandaag gepubliceerd is. Vanaf dan gaat
nieuw werk op develop niet meer mee, dus begint de Dependabot-routine een nieuwe parent. --tag
doet alleen die stap (idempotent; met --droog zonder te taggen). De hoofdissues komen in de state, voor staging_infra_pr.py.
Gebruik: staging_release_branches.py [--push | --tag [--droog]] [--repos A,B] [--uit BESTAND]. Zonder --uit
gaat de samenvatting naar stdout; met --uit komt hij als sectie in die notitie.
"""
import base64
import datetime
import fnmatch
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DATA = os.path.expanduser('~/vault/data/staging-repos.json')
RUNS = os.path.expanduser('~/staging-runs')
STATE = os.path.join(RUNS, 'state.json')
FRONTENDS = os.path.join(RUNS, 'frontends.json')
START, EIND = '<!-- release-branches:start -->', '<!-- release-branches:eind -->'
TAG = 'release candidate'


class Afwijking(Exception):
    """Deze repo kan niet klaargezet worden; de melding komt in de samenvatting."""


def git(cwd, *args):
    return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def nieuwste_image(soort, cache={}):
    """Nieuwste tag die bij het patroon past, met de digest van de multi-arch index."""
    if soort['hub'] + soort['tag'] in cache:
        return cache[soort['hub'] + soort['tag']]
    patroon, gevonden = re.compile(soort['tag']), []
    url = 'https://hub.docker.com/v2/repositories/%s/tags?page_size=100&ordering=last_updated' % soort['hub']
    for _ in range(10):
        data = json.load(urllib.request.urlopen(url))
        gevonden += [(t['name'], t['digest']) for t in data['results']
                     if patroon.fullmatch(t['name']) and t.get('digest')]
        url = data.get('next')
        if not url:
            break
    if not gevonden:
        raise SystemExit('Geen tag gevonden voor %s met patroon %s' % (soort['hub'], soort['tag']))
    tag, digest = max(gevonden, key=lambda t: [int(n) for n in re.findall(r'\d+', t[0])])
    cache[soort['hub'] + soort['tag']] = soort['nieuw'].format(tag=tag, digest=digest)
    return cache[soort['hub'] + soort['tag']]


def clone(org, repo):
    pad = os.path.join(RUNS, repo)
    if not os.path.isdir(os.path.join(pad, '.git')):
        os.makedirs(RUNS, exist_ok=True)
        subprocess.run(['git', 'clone', '-q', 'git@github.com:%s/%s.git' % (org, repo), pad],
                       check=True, capture_output=True, text=True)
    git(pad, 'config', 'core.autocrlf', 'false')
    git(pad, 'fetch', '-q', '--prune', '--prune-tags', '--tags', 'origin')
    git(pad, 'checkout', '-q', '--detach', 'origin/develop')
    git(pad, 'reset', '-q', '--hard')
    git(pad, 'clean', '-qfdx')
    return pad


def vervang_eenmaal(pad, bestand, patroon, vervanging):
    """Vervangt op de enige regel die bij patroon past; geeft (oude regel, nieuwe regel)."""
    tekst = open(os.path.join(pad, bestand), newline='').read()
    regels = tekst.split('\n')
    treffers = [i for i, r in enumerate(regels) if re.search(patroon, r.rstrip('\r'))]
    if len(treffers) != 1:
        raise Afwijking('`%s` past %d keer in `%s`, verwacht 1' % (patroon, len(treffers), bestand))
    i = treffers[0]
    oud = regels[i]
    regels[i] = re.sub(patroon, vervanging, oud.rstrip('\r'), count=1) + ('\r' if oud.endswith('\r') else '')
    if regels[i] != oud:
        open(os.path.join(pad, bestand), 'w', newline='').write('\n'.join(regels))
    return oud.rstrip('\r'), regels[i].rstrip('\r')


def gewijzigde_regels(pad, branch):
    """Bestanden en (weg, erbij)-regels van de diff origin/develop..branch."""
    bestanden = set(git(pad, 'diff', '--name-only', 'origin/develop', branch).split())
    weg, erbij = [], []
    for regel in git(pad, 'diff', '--unified=0', 'origin/develop', branch).split('\n'):
        if regel.startswith('-') and not regel.startswith('---'):
            weg.append(regel[1:])
        elif regel.startswith('+') and not regel.startswith('+++'):
            erbij.append(regel[1:])
    return bestanden, sorted(weg), sorted(erbij)


def snapshots(pad, globs):
    gevonden = []
    for bestand in git(pad, 'ls-files').split('\n'):
        if any(fnmatch.fnmatch(bestand, g) for g in globs):
            for nr, regel in enumerate(open(os.path.join(pad, bestand), errors='replace'), 1):
                if '-SNAPSHOT' in regel:
                    gevonden.append('%s:%d' % (bestand, nr))
    return gevonden


def klaarzetten(cfg, entry):
    org, repo = cfg['org'], entry['repo']
    pad = clone(org, repo)
    open_branches = [r.split('refs/heads/')[1] for r in
                     git(pad, 'ls-remote', '--heads', 'origin', 'release/*').split('\n') if r]
    if open_branches:
        raise Afwijking('er staat al een release branch op de remote: %s' % ', '.join(open_branches))
    nieuw = int(git(pad, 'rev-list', '--count', 'origin/master..origin/develop'))
    if not nieuw:
        raise Afwijking('develop loopt niet voor op master, er is niets uit te rollen')

    soort = cfg['versies'][entry['versie']]
    wijzigingen = []
    if entry['versie'] == 'npm':
        versie = json.load(open(os.path.join(pad, soort['bestand'])))['version']
        if not re.fullmatch(r'\d+\.\d+\.\d+', versie):
            raise Afwijking('versie `%s` in package.json is geen X.Y.Z' % versie)
    else:
        oud, _ = vervang_eenmaal(pad, soort['bestand'], soort['regel'], r'\g<0>')
        versie = re.search(soort['regel'], oud).group('v')
        wijzigingen.append(vervang_eenmaal(pad, soort['bestand'], soort['regel'],
                                           lambda m: m.group(0).replace('-SNAPSHOT', '')))
        rest = snapshots(pad, soort['snapshot'])
        if rest:
            raise Afwijking('nog -SNAPSHOT na het aanpassen van de versie: %s' % ', '.join(rest))
    if git(pad, 'tag', '-l', versie).strip():
        raise Afwijking('tag %s bestaat al' % versie)

    image = nieuwste_image(cfg['images'][entry['image']['soort']])
    oud_image, nieuw_image = vervang_eenmaal(pad, entry['image']['bestand'],
                                             cfg['images'][entry['image']['soort']]['huidig'],
                                             lambda m: image)
    if oud_image != nieuw_image:
        wijzigingen.append((oud_image, nieuw_image))

    frontends = []
    for prop, frontend in sorted(entry.get('frontends', {}).items()):
        nieuw_f = frontend_versie(org, frontend)
        oud_f, nieuw_regel = vervang_eenmaal(pad, soort['bestand'],
                                             r'(?<=<%s>)\d+\.\d+\.\d+(?=</%s>)' % (re.escape(prop), re.escape(prop)),
                                             lambda m: nieuw_f)
        if oud_f != nieuw_regel:
            wijzigingen.append((oud_f, nieuw_regel))
        frontends.append((frontend, re.search(r'\d+\.\d+\.\d+', oud_f).group(0), nieuw_f))
    if not wijzigingen:
        raise Afwijking('niets te wijzigen: versie en base image zijn al goed')

    branch = 'release/' + versie
    git(pad, 'checkout', '-q', '-B', branch)
    git(pad, 'add', soort['bestand'], entry['image']['bestand'])
    git(pad, 'commit', '-q', '-m', 'Prepare release ' + versie)

    bestanden, weg, erbij = gewijzigde_regels(pad, branch)
    verwacht = {soort['bestand'], entry['image']['bestand']}
    if not bestanden <= verwacht:
        raise Afwijking('diff raakt onverwachte bestanden: %s' % ', '.join(sorted(bestanden - verwacht)))
    if weg != sorted(w[0] for w in wijzigingen) or erbij != sorted(w[1] for w in wijzigingen):
        raise Afwijking('diff bevat andere regels dan de versie, het base image en de frontends')
    return {'versie': versie, 'branch': branch, 'sha': git(pad, 'rev-parse', 'HEAD').strip(),
            'develop': git(pad, 'rev-parse', 'origin/develop').strip(), 'commits': nieuw,
            'image_oud': base_ref(oud_image, cfg['images'][entry['image']['soort']]['huidig']),
            'image_nieuw': image, 'versie_gewijzigd': entry['versie'] != 'npm', 'frontends': frontends}


def frontend_versie(org, frontend):
    """De gereleasede versie van een frontend: package.json op master, na een geslaagde master-build.

    Staat de frontend in het plan van staging_frontends.py maar is hij nog niet gepubliceerd, dan
    eerst die keten afmaken: anders komt de vorige versie in de release branch.
    """
    if os.path.exists(FRONTENDS):
        m = json.load(open(FRONTENDS))['repos'].get(frontend, {})
        if m and 'gepubliceerd' not in m:
            raise Afwijking('frontend %s is nog niet gepubliceerd (zie %s)' % (frontend, FRONTENDS))
    pkg = json.loads(base64.b64decode(gh_json('api', 'repos/%s/%s/contents/package.json?ref=master' % (org, frontend))['content']))
    runs = gh_json('run', 'list', '-R', '%s/%s' % (org, frontend), '--branch', 'master', '--workflow', 'master.yml',
                   '--limit', '1', '--json', 'status,conclusion')
    if not runs or runs[0]['conclusion'] != 'success':
        raise Afwijking('laatste master-build van %s is niet geslaagd' % frontend)
    return pkg['version']


def pushen(org, repo, m):
    """Pusht de klaargezette branch, alleen als er sinds het klaarzetten niets veranderd is."""
    pad = os.path.join(RUNS, repo)
    git(pad, 'fetch', '-q', '--prune', 'origin')
    if git(pad, 'rev-parse', 'refs/heads/' + m['branch']).strip() != m['sha']:
        raise Afwijking('lokale %s is veranderd sinds het klaarzetten' % m['branch'])
    if git(pad, 'rev-parse', 'origin/develop').strip() != m['develop']:
        raise Afwijking('origin/develop is veranderd sinds het klaarzetten; zet opnieuw klaar')
    if git(pad, 'ls-remote', '--heads', 'origin', 'release/*').strip():
        raise Afwijking('er staat intussen al een release branch op de remote')
    ref = 'refs/heads/' + m['branch']
    git(pad, 'push', '-q', 'origin', '%s:%s' % (ref, ref))


def gh_json(*args):
    return json.loads(subprocess.run(['gh', *args], check=True, capture_output=True, text=True).stdout)


def volgen(org, gepusht, state, max_minuten=40):
    """Wacht tot de pre-release-runs klaar zijn en haalt per repo de RC-tag op."""
    open_ = set(gepusht)
    einde = time.time() + max_minuten * 60
    while open_ and time.time() < einde:
        time.sleep(30)
        for repo in sorted(open_):
            m = state[repo]
            try:
                runs = gh_json('run', 'list', '-R', '%s/%s' % (org, repo), '--branch', m['branch'],
                               '--limit', '1', '--json', 'databaseId,status,conclusion,url')
            except (subprocess.CalledProcessError, ValueError):
                continue
            if not runs or runs[0]['status'] != 'completed':
                continue
            open_.discard(repo)
            m['run'] = runs[0]['url']
            if runs[0]['conclusion'] != 'success':
                m['fout'] = 'pre-release-run %s' % runs[0]['conclusion']
                continue
            pad = os.path.join(RUNS, repo)
            git(pad, 'fetch', '-q', '--tags', 'origin')
            tags = [t for t in git(pad, 'tag', '-l', m['versie'] + '-rc.*', '--points-at', m['sha']).split() if t]
            if tags:
                m['rc'] = max(tags, key=lambda t: int(t.rsplit('.', 1)[1]))
            else:
                m['fout'] = 'run geslaagd, maar geen RC-tag op %s' % m['sha'][:8]
            print('%s: %s' % (repo, m.get('rc') or m['fout']), file=sys.stderr)
    for repo in open_:
        state[repo]['fout'] = 'run na %d minuten nog niet klaar' % max_minuten


def laad_script(naam):
    """Laadt een script uit deze map als module: met python3 -I staat de map niet op sys.path."""
    spec = importlib.util.spec_from_file_location(
        naam, os.path.join(os.path.dirname(os.path.abspath(__file__)), naam + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def open_release_branch(org, repo):
    """De enige release/*-branch op de remote, of None. Meer dan één is een fout."""
    out = subprocess.run(['git', 'ls-remote', '--heads', 'git@github.com:%s/%s.git' % (org, repo), 'release/*'],
                         check=True, capture_output=True, text=True).stdout
    branches = [r.split('refs/heads/')[1] for r in out.split('\n') if r]
    if len(branches) > 1:
        raise Afwijking('meer dan één release branch op de remote: %s' % ', '.join(branches))
    return branches[0] if branches else None


def release_inhoud(cfg):
    """Per repo (base, head) van wat er in deze release zit, plus meldingen voor wat ontbreekt.

    Image-repo's: master...release/X.Y.Z. Frontends die vandaag gepubliceerd zijn (frontends.json):
    de merge-commit van de PR "Release X.Y.Z" naar master, ten opzichte van zijn eerste parent.
    """
    org, inhoud, meldingen = cfg['org'], {}, []
    for entry in cfg['repos']:
        if entry['rol'] != 'image':
            continue
        try:
            branch = open_release_branch(org, entry['repo'])
        except Afwijking as e:
            meldingen.append('%s: %s' % (entry['repo'], e))
            continue
        if branch:
            inhoud[entry['repo']] = ('master', branch)
    frontends = json.load(open(FRONTENDS)) if os.path.exists(FRONTENDS) else {}
    vandaag = datetime.date.today().isoformat()
    for repo, m in frontends.get('repos', {}).items():
        if frontends['datum'] != vandaag or 'gepubliceerd' not in m:
            continue
        prs = [p for p in gh_json('pr', 'list', '-R', '%s/%s' % (org, repo), '--base', 'master', '--state', 'merged',
                                  '--search', '"Release %s" in:title' % m['versie'], '--json', 'title,mergeCommit')
               if p['title'] == 'Release ' + m['versie']]
        if len(prs) != 1:
            meldingen.append('%s: %d PR\'s "Release %s" naar master, verwacht 1' % (repo, len(prs), m['versie']))
            continue
        sha = prs[0]['mergeCommit']['oid']
        parent = gh_json('api', 'repos/%s/%s/commits/%s' % (org, repo, sha))['parents'][0]['sha']
        inhoud[repo] = (parent, sha)
    return inhoud, meldingen


def taggen(cfg, state, droog=False):
    """Zet de tag op de hoofdissues van alles wat in de release zit en legt ze vast in de state.

    Met droog=True worden de hoofdissues wel vastgelegd, maar wordt er niets getagd.
    """
    overzicht = laad_script('staging_overzicht')
    keys = overzicht.project_keys()
    inhoud, meldingen = release_inhoud(cfg)
    hoofd = {}
    for repo, (base, head) in sorted(inhoud.items()):
        print('%s: hoofdissues in %s...%s' % (repo, base[:12], head), file=sys.stderr)
        _, per_root, _, _, _ = overzicht.analyseer(cfg['org'], repo, keys, base, head)
        for root_id, ids in per_root.items():
            hoofd.setdefault(root_id, {}).setdefault(repo, sorted(ids - {root_id}))
    # Via de REST-API met het id: een command als `tag {release candidate}` neemt de accolades mee in de naam.
    tag_ids = [t['id'] for t in overzicht.youtrack('tags', 'id,name', '&query=%s&$top=50' % urllib.parse.quote(TAG))
               if t['name'] == TAG]
    if len(tag_ids) != 1 and not droog:
        raise SystemExit('Tag "%s" niet precies één keer gevonden in YouTrack (%d); maak hem eerst aan' % (TAG, len(tag_ids)))
    tag_id = tag_ids[0] if tag_ids else None
    getagd, al, fouten = [], [], []
    for root_id in sorted(hoofd):
        issue = overzicht.issue(root_id)
        if not issue:
            fouten.append('%s: niet gevonden in YouTrack' % root_id)
            continue
        tags = {t['name'] for t in overzicht.youtrack('issues/' + root_id, 'tags(name)')['tags']}
        if TAG in tags:
            al.append(root_id)
            continue
        if droog:
            getagd.append(root_id + ' (droog)')
            continue
        try:
            overzicht.youtrack_post('issues/%s/tags' % root_id, {'id': tag_id})
            getagd.append(root_id)
        except urllib.error.HTTPError as e:
            fouten.append('%s: HTTP %s' % (root_id, e.code))
    state['hoofdissues'] = {r: {'summary': (overzicht.issue(r) or {}).get('summary', ''),
                                'upgrade': overzicht.is_upgrade(r), 'repos': hoofd[r]} for r in sorted(hoofd)}
    state['tag'] = {'release_inhoud': {r: list(bh) for r, bh in inhoud.items()}, 'getagd': getagd,
                    'al_getagd': al, 'fouten': meldingen + fouten}
    print('tag "%s": %d gezet, %d stond er al, %d fouten' % (TAG, len(getagd), len(al), len(meldingen + fouten)),
          file=sys.stderr)


def base_ref(regel, patroon):
    return re.search(patroon, regel.strip()).group(0) if re.search(patroon, regel.strip()) else regel.strip()


def kort(image):
    return re.sub(r'@sha256:([0-9a-f]{8})[0-9a-f]+', r'@sha256:\1…', image)


def samenvatting(datum, resultaten, handmatig, tag=None):
    afwijkingen = [(r, m) for r, m in resultaten.items() if 'fout' in m]
    if any('gepusht' in m for m in resultaten.values()):
        intro = 'Klaargezet op %s in `~/staging-runs` en gepusht met `--push`.' % datum
    else:
        intro = ('Klaargezet op %s in `~/staging-runs`, nog niet gepusht. Na controle: '
                 '`staging_release_branches.py --push`.' % datum)
    regels = [START, '## Release branches', '', intro, '']
    if afwijkingen:
        regels += ['### Afwijkingen', '']
        regels += ['- **%s**%s: %s%s' % (r, ' (`%s`)' % m['branch'] if 'branch' in m else '', m['fout'],
                                         ', [run](%s)' % m['run'] if 'run' in m else '')
                   for r, m in afwijkingen] + ['']
    klaar = [(r, m) for r, m in resultaten.items() if 'fout' not in m]
    if klaar:
        regels += ['### Branches', '',
                   '| Repo | Branch | Commits | Versie | Base image | Frontends | Status |',
                   '| --- | --- | --- | --- | --- | --- | --- |']
        for r, m in klaar:
            status = ('RC `%s`' % m['rc'] if 'rc' in m else 'gepusht, run loopt' if 'gepusht' in m
                      else 'klaar voor push')
            frontends = '<br>'.join('`%s` %s → %s' % tuple(f) for f in m.get('frontends', [])) or '-'
            regels.append('| `%s` | `%s` | %d | %s | `%s` → `%s` | %s | %s |' % (
                r, m['branch'], m['commits'], '-SNAPSHOT eraf' if m['versie_gewijzigd'] else 'ongewijzigd (npm)',
                kort(m['image_oud']), kort(m['image_nieuw']), frontends, status))
        regels.append('')
    if handmatig:
        regels += ['### Met de hand', '']
        regels += ['- **%s**: %s' % (r, reden) for r, reden in handmatig] + ['']
    if tag:
        droog = any(g.endswith('(droog)') for g in tag['getagd'])
        regels += ['### Tag "%s"' % TAG, '',
                   '%s %d hoofdissues, stond al op %d. Bron: %s.' % (
                       'Droog, niets getagd: zou komen op' if droog else 'Gezet op',
                       len(tag['getagd']), len(tag['al_getagd']),
                       ', '.join('`%s`' % r for r in sorted(tag['release_inhoud'])) or 'niets'), '']
        if tag['getagd']:
            regels += ['- %s: ' % ('Zou gezet worden' if droog else 'Gezet') + ', '.join(tag['getagd'])]
        regels += ['- **Fout:** ' + f for f in tag['fouten']]
        regels.append('')
    return '\n'.join(regels + [EIND])


def schrijf_sectie(pad, sectie):
    tekst = open(pad).read() if os.path.exists(pad) else ''
    if START in tekst and EIND in tekst:
        tekst = tekst[:tekst.index(START)] + sectie + tekst[tekst.index(EIND) + len(EIND):]
    else:
        m = re.search(r'^## ', tekst, re.M)
        tekst = (tekst[:m.start()] + sectie + '\n\n' + tekst[m.start():]) if m else tekst.rstrip('\n') + '\n\n' + sectie + '\n'
    open(pad, 'w').write(tekst)


def main():
    args = sys.argv[1:]
    uit = args[args.index('--uit') + 1] if '--uit' in args else None
    alleen = set(args[args.index('--repos') + 1].split(',')) if '--repos' in args else None
    cfg = json.load(open(DATA))
    images = [e for e in cfg['repos'] if e['rol'] == 'image' and (alleen is None or e['repo'] in alleen)]
    if alleen and alleen - {e['repo'] for e in images}:
        raise SystemExit('Onbekende image-repo: %s' % ', '.join(sorted(alleen - {e['repo'] for e in images})))

    handmatig = [(e['repo'], e['handmatig']) for e in images if e.get('handmatig')]
    if '--tag' in args:
        if not os.path.exists(STATE):
            raise SystemExit('Geen %s: zet eerst de release branches klaar' % STATE)
        state = json.load(open(STATE))
        taggen(cfg, state, droog='--droog' in args)
        json.dump(state, open(STATE, 'w'), indent=2)
        uitvoer(uit, samenvatting(state['datum'], state['repos'], handmatig, state['tag']))
        return
    if '--push' in args:
        if not os.path.exists(STATE):
            raise SystemExit('Geen %s: zet eerst de release branches klaar' % STATE)
        state = json.load(open(STATE))
        gepusht = []
        for repo, m in state['repos'].items():
            if (alleen and repo not in alleen) or 'fout' in m or 'gepusht' in m:
                continue
            print('%s: push %s' % (repo, m['branch']), file=sys.stderr)
            try:
                pushen(cfg['org'], repo, m)
                m['gepusht'] = datetime.datetime.now().isoformat(timespec='seconds')
                gepusht.append(repo)
            except Afwijking as e:
                m['fout'] = str(e)
            except subprocess.CalledProcessError as e:
                m['fout'] = 'git faalde: `%s`: %s' % (' '.join(e.cmd), (e.stderr or '').strip())
            json.dump(state, open(STATE, 'w'), indent=2)
        if gepusht:
            taggen(cfg, state)
            json.dump(state, open(STATE, 'w'), indent=2)
        volgen(cfg['org'], [r for r, m in state['repos'].items()
                            if 'gepusht' in m and 'rc' not in m and 'fout' not in m], state['repos'])
        json.dump(state, open(STATE, 'w'), indent=2)
        uitvoer(uit, samenvatting(state['datum'], state['repos'], handmatig, state.get('tag')))
        return

    datum = datetime.date.today().isoformat()
    resultaten = {}
    keten = frontendketen(cfg, images)
    # Repo's zonder frontends eerst; iam en portal wachten alleen op hun eigen frontends.
    for entry in sorted(images, key=lambda e: bool(e.get('frontends'))):
        if entry.get('handmatig'):
            continue
        print('%s …' % entry['repo'], file=sys.stderr)
        try:
            mislukt = [f for f in sorted(set(entry.get('frontends', {}).values())) if not keten.gepubliceerd(f)]
            if mislukt:
                raise Afwijking('frontend %s is niet gepubliceerd (zie de sectie Frontends)' % ', '.join(mislukt))
            resultaten[entry['repo']] = klaarzetten(cfg, entry)
        except Afwijking as e:
            resultaten[entry['repo']] = {'fout': str(e)}
        except subprocess.CalledProcessError as e:
            resultaten[entry['repo']] = {'fout': 'git faalde: `%s`: %s' % (' '.join(e.cmd), (e.stderr or '').strip())}

    # Met --repos alleen die repo's bijwerken in de state van dezelfde dag.
    vorige = json.load(open(STATE)) if alleen and os.path.exists(STATE) else {}
    if vorige.get('datum') == datum:
        resultaten = {**vorige['repos'], **resultaten}
    json.dump({'datum': datum, 'repos': resultaten}, open(STATE, 'w'), indent=2)
    if keten:
        keten.afwachten()
        keten.uitvoer(uit)
    uitvoer(uit, samenvatting(datum, resultaten, handmatig))


def frontendketen(cfg, images):
    """Start de frontendketen uit staging_frontends.py voor de frontends van deze image-repo's."""
    nodig = {f for e in images for f in e.get('frontends', {}).values()}
    if not nodig:
        return None
    module = laad_script('staging_frontends')
    module.controleer_token()
    keten = module.Keten(cfg, nodig)
    keten.plannen()
    keten.starten()
    return keten


def uitvoer(uit, sectie):
    if uit:
        schrijf_sectie(uit, sectie)
        print('Samenvatting geschreven in %s' % uit, file=sys.stderr)
    else:
        print(sectie)


if __name__ == '__main__':
    main()
