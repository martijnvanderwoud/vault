#!/usr/bin/python3
"""Infra-PR voor een staging-uitrol: rc-branches gerebased en alle RC-image tags, naar develop.

Werkt in een eigen clone in ~/staging-runs/infra. Maakt feature/staging-rc-<datum> vanaf
origin/develop en rebaset daar de rc-branches (feature/<ISSUE>-rc) op, alleen van hoofdissues die
in de release zitten (de hoofdissues in ~/staging-runs/state.json, van staging_release_branches.py
--tag of --push). Daarna één commit met de image tags: per image-repo met een open release branch
de hoogste tag X.Y.Z-rc.N, en die moet op de tip van die branch staan. De diff van die commit mag
alleen de tag-regels uit data/staging-repos.json raken.
Slaagt alles, dan pusht het script alleen die branch (nooit --force) en maakt het de PR naar
develop. Mergen doe ik zelf. Geeft een rebase een conflict, dan stopt het script: los het op in de
clone, rond af met `git rebase --continue` en draai het script opnieuw; het gaat dan verder waar
het was. --opnieuw gooit die stand weg, --droog pusht niet en maakt geen PR.
Gebruik: staging_infra_pr.py [--droog] [--opnieuw] [--uit BESTAND]. Met --uit komt de samenvatting
als sectie in de uitrolnotitie, na de release branches.
"""
import datetime
import importlib.util
import json
import os
import re
import subprocess
import sys

RUNS = os.path.expanduser('~/staging-runs')
INFRA_STATE = os.path.join(RUNS, 'infra.json')
START, EIND = '<!-- infra-pr:start -->', '<!-- infra-pr:eind -->'
YOUTRACK = 'https://crimsoncricket.myjetbrains.com/youtrack/issue/'


def laad(naam):
    spec = importlib.util.spec_from_file_location(
        naam, os.path.join(os.path.dirname(os.path.abspath(__file__)), naam + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rb = laad('staging_release_branches')
git, Afwijking = rb.git, rb.Afwijking


def rc_tag(org, repo):
    """{'branch', 'rc', 'sha'} van de open release branch, of None zonder release branch."""
    branch = rb.open_release_branch(org, repo)
    if not branch:
        return None
    versie = branch.split('/', 1)[1]
    out = subprocess.run(['git', 'ls-remote', '--heads', '--tags', 'git@github.com:%s/%s.git' % (org, repo),
                          branch, '%s-rc.*' % versie], check=True, capture_output=True, text=True).stdout
    refs = dict(reversed(r.split('\t')) for r in out.split('\n') if r)
    tip = refs['refs/heads/' + branch]
    tags = {}
    for ref, sha in refs.items():
        m = re.fullmatch(r'refs/tags/(%s-rc\.(\d+))(\^\{\})?' % re.escape(versie), ref)
        if m and (m.group(3) or m.group(1) not in tags):
            tags[m.group(1)] = sha  # de gepeelde SHA (^{}) wint van die van het tag-object
    if not tags:
        raise Afwijking('geen RC-tag op `%s`' % branch)
    rc = max(tags, key=lambda t: int(t.rsplit('.', 1)[1]))
    if tags[rc] != tip:
        raise Afwijking('`%s` staat niet op de tip van `%s`: wacht op de pre-release-build' % (rc, branch))
    return {'branch': branch, 'rc': rc, 'sha': tip}


def rebase_bezig(pad):
    return any(os.path.exists(os.path.join(pad, '.git', d)) for d in ('rebase-merge', 'rebase-apply'))


def diff_regels(pad, van, tot):
    bestanden = set(git(pad, 'diff', '--name-only', van, tot).split())
    weg, erbij = [], []
    for regel in git(pad, 'diff', '--unified=0', van, tot).split('\n'):
        if regel.startswith('-') and not regel.startswith('---'):
            weg.append(regel[1:])
        elif regel.startswith('+') and not regel.startswith('+++'):
            erbij.append(regel[1:])
    return bestanden, sorted(weg), sorted(erbij)


def voorbereiden(cfg, release):
    """Nieuwe stand: clone, branch, de image tags per repo en de rc-branches die meegaan."""
    org = cfg['org']
    if rebase_bezig(os.path.join(RUNS, cfg['infra'])):
        git(os.path.join(RUNS, cfg['infra']), 'rebase', '--abort')
    pad = rb.clone(org, cfg['infra'])
    datum = datetime.date.today().isoformat()
    s = {'datum': datum, 'branch': 'feature/staging-rc-' + datum,
         'develop': git(pad, 'rev-parse', 'origin/develop').strip(), 'tags': {}, 'rc': [], 'niet_mee': []}
    if git(pad, 'ls-remote', '--heads', 'origin', s['branch']).strip():
        raise SystemExit('%s staat al op de remote' % s['branch'])
    for entry in cfg['repos']:
        if entry['rol'] != 'image':
            continue
        try:
            t = rc_tag(org, entry['repo'])
            s['tags'][entry['repo']] = t or {'overgeslagen': 'geen open release branch'}
        except Afwijking as e:
            s['tags'][entry['repo']] = {'fout': str(e)}
    hoofd = release['hoofdissues']
    for root_id, branch in sorted(laad('staging_overzicht').rc_branches(org, cfg['infra']).items()):
        if root_id in hoofd:
            s['rc'].append({'hoofdissue': root_id, 'branch': branch, 'status': 'open',
                            'tip': git(pad, 'rev-parse', 'origin/' + branch).strip()})
        else:
            s['niet_mee'].append({'hoofdissue': root_id, 'branch': branch})
    git(pad, 'checkout', '-q', '-B', s['branch'])
    return pad, s


def rebasen(pad, s):
    """Rebaset de open rc-branches op de PR-branch; True als alles erop staat."""
    for rc in s['rc']:
        if rc['status'] == 'conflict':
            if rebase_bezig(pad):
                raise SystemExit('De rebase van %s is nog bezig in %s: los het conflict op, '
                                 '`git rebase --continue`, en draai het script opnieuw.' % (rc['branch'], pad))
            if subprocess.run(['git', 'merge-base', '--is-ancestor', s['branch'], 'HEAD'], cwd=pad).returncode:
                raise SystemExit('HEAD in %s bevat %s niet meer (rebase afgebroken?). Begin opnieuw met --opnieuw.'
                                 % (pad, s['branch']))
            git(pad, 'checkout', '-q', '-B', s['branch'])
            rc['status'] = 'opgelost'
        if rc['status'] != 'open':
            continue
        print('rebase %s' % rc['branch'], file=sys.stderr)
        r = subprocess.run(['git', 'rebase', '-q', '--onto', s['branch'], 'origin/develop', 'origin/' + rc['branch']],
                           cwd=pad, capture_output=True, text=True)
        if r.returncode:
            if not rebase_bezig(pad):
                raise SystemExit('rebase van %s faalde: %s' % (rc['branch'], (r.stderr or r.stdout).strip()))
            rc['status'] = 'conflict'
            rc['conflict'] = git(pad, 'diff', '--name-only', '--diff-filter=U').split()
            return False
        git(pad, 'checkout', '-q', '-B', s['branch'])
        rc['status'] = 'klaar'
    for rc in s['rc']:
        rc['commits'] = [c for c in git(pad, 'log', '--format=%s', '--no-merges',
                                        'origin/develop..origin/' + rc['branch']).split('\n') if c]
    return True


def tags_committen(cfg, pad, s):
    """Eén commit met de image tags, met de diff-controle op alleen de tag-regels."""
    paden = {e['repo']: e['infra'] for e in cfg['repos'] if e.get('infra')}
    wijzigingen = []
    for repo, t in s['tags'].items():
        if 'rc' not in t:
            continue
        oud, nieuw = rb.vervang_eenmaal(pad, paden[repo], cfg['infra_tag'],
                                        lambda m: m.group(0)[:m.start('tag') - m.start()] + t['rc'])
        t['oud'] = re.search(cfg['infra_tag'], oud).group('tag')
        if oud != nieuw:
            wijzigingen.append((paden[repo], oud, nieuw))
    if not wijzigingen:
        raise SystemExit('Geen image tags te wijzigen')
    git(pad, 'add', *sorted({w[0] for w in wijzigingen}))
    git(pad, 'commit', '-q', '-m', 'Release candidates for staging ' + s['datum'])
    bestanden, weg, erbij = diff_regels(pad, 'HEAD~1', 'HEAD')
    if bestanden != {w[0] for w in wijzigingen}:
        raise SystemExit('diff van de tag-commit raakt onverwachte bestanden: %s' % ', '.join(sorted(bestanden)))
    if weg != sorted(w[1] for w in wijzigingen) or erbij != sorted(w[2] for w in wijzigingen):
        raise SystemExit('diff van de tag-commit bevat andere regels dan de image tags')
    s['sha'] = git(pad, 'rev-parse', 'HEAD').strip()


def controleren_voor_push(cfg, pad, s):
    git(pad, 'fetch', '-q', '--prune', 'origin')
    if git(pad, 'rev-parse', 'origin/develop').strip() != s['develop']:
        raise SystemExit('origin/develop is veranderd sinds het begin; draai opnieuw met --opnieuw')
    for rc in s['rc']:
        if git(pad, 'rev-parse', 'origin/' + rc['branch']).strip() != rc['tip']:
            raise SystemExit('%s is veranderd sinds het begin; draai opnieuw met --opnieuw' % rc['branch'])
    if git(pad, 'rev-parse', 'refs/heads/' + s['branch']).strip() != s['sha']:
        raise SystemExit('lokale %s is veranderd na de tag-commit' % s['branch'])
    if git(pad, 'ls-remote', '--heads', 'origin', s['branch']).strip():
        raise SystemExit('%s staat intussen al op de remote' % s['branch'])


def pr_body(s, release):
    regels = ['Release candidates for staging, prepared on %s by `staging_infra_pr.py`.' % s['datum'], '',
              '## Image tags', '', '| Repo | Old | New |', '| --- | --- | --- |']
    regels += ['| `%s` | `%s` | `%s` |' % (r, t['oud'], t['rc']) for r, t in sorted(s['tags'].items()) if 'rc' in t]
    rest = [(r, t.get('overgeslagen') or t.get('fout')) for r, t in sorted(s['tags'].items()) if 'rc' not in t]
    if rest:
        regels += ['', 'Unchanged: ' + ', '.join('`%s`' % r for r, _ in rest) + '.']
    regels += ['', '## Configuration from rc branches (rebased)', '']
    regels += ['- `%s` (%s): %s' % (rc['branch'], rc['hoofdissue'], '; '.join(rc['commits']))
               for rc in s['rc']] or ['- none']
    hoofd = release['hoofdissues']
    for kop, upgrade in (('Main issues', False), ('Dependabot and Scala Steward', True)):
        ids = [r for r in sorted(hoofd) if hoofd[r]['upgrade'] == upgrade]
        if ids:
            regels += ['', '## ' + kop, '']
            regels += ['- [%s](%s%s) %s (%s)' % (r, YOUTRACK, r, hoofd[r]['summary'],
                                                 ', '.join('`%s`' % repo for repo in sorted(hoofd[r]['repos'])))
                       for r in ids]
    return '\n'.join(regels + ['', '🤖 Generated with [Claude Code](https://claude.com/claude-code)', ''])


def pushen(cfg, pad, s, release):
    controleren_voor_push(cfg, pad, s)
    ref = 'refs/heads/' + s['branch']
    git(pad, 'push', '-q', 'origin', '%s:%s' % (ref, ref))
    s['gepusht'] = datetime.datetime.now().isoformat(timespec='seconds')
    s['pr'] = subprocess.run(['gh', 'pr', 'create', '-R', '%s/%s' % (cfg['org'], cfg['infra']), '--base', 'develop',
                              '--head', s['branch'], '--title', 'Release candidates for staging ' + s['datum'],
                              '--body', pr_body(s, release)],
                             check=True, capture_output=True, text=True).stdout.strip().split('\n')[-1]


def samenvatting(s):
    pad = os.path.join(RUNS, 'infra')
    if 'pr' in s:
        intro = 'Gepusht op %s: %s. Mergen doe ik zelf.' % (s['gepusht'][:16].replace('T', ' '), s['pr'])
    elif any(rc['status'] == 'conflict' for rc in s['rc']):
        intro = ('**Conflict, wacht op mij.** Los het op in `%s`, rond af met `git rebase --continue` en draai '
                 '`staging_infra_pr.py` opnieuw.' % pad)
    elif 'sha' in s:
        intro = 'Klaar in `%s` (`%s`), niet gepusht (`--droog`).' % (pad, s['branch'])
    else:
        intro = 'Bezig in `%s`.' % pad
    regels = [START, '## Infra-PR', '', intro, '', '### Image tags', '',
              '| Repo | Release branch | Tag in infra |', '| --- | --- | --- |']
    for repo, t in sorted(s['tags'].items()):
        if 'rc' in t:
            tag = '`%s` → `%s`' % (t['oud'], t['rc']) if 'oud' in t and t['oud'] != t['rc'] else '`%s`' % t['rc']
            regels.append('| `%s` | `%s` | %s |' % (repo, t['branch'], tag))
        else:
            regels.append('| `%s` | - | %s%s |' % (repo, '**fout:** ' if 'fout' in t else 'ongewijzigd: ',
                                                    t.get('fout') or t.get('overgeslagen')))
    regels += ['', '### Rc-branches', '']
    for rc in s['rc']:
        extra = (': conflict in ' + ', '.join('`%s`' % f for f in rc.get('conflict', []))
                 if rc['status'] == 'conflict' else ': ' + '; '.join(rc.get('commits', [])) if rc.get('commits') else '')
        regels.append('- `%s` (%s), %s%s' % (rc['branch'], rc['hoofdissue'], rc['status'], extra))
    regels += ['- `%s` (%s): **niet meegenomen**, het hoofdissue zit niet in de release' % (n['branch'], n['hoofdissue'])
               for n in s['niet_mee']]
    if not s['rc'] and not s['niet_mee']:
        regels.append('- geen')
    return '\n'.join(regels + ['', EIND])


def schrijf_sectie(pad, sectie):
    """Vervangt de eigen sectie, of zet hem direct na de release branches (anders vóór de eerste ##)."""
    tekst = open(pad).read() if os.path.exists(pad) else ''
    if START in tekst and EIND in tekst:
        tekst = tekst[:tekst.index(START)] + sectie + tekst[tekst.index(EIND) + len(EIND):]
    elif rb.EIND in tekst:
        i = tekst.index(rb.EIND) + len(rb.EIND)
        tekst = tekst[:i] + '\n\n' + sectie + tekst[i:]
    else:
        m = re.search(r'^## ', tekst, re.M)
        tekst = (tekst[:m.start()] + sectie + '\n\n' + tekst[m.start():]) if m else tekst.rstrip('\n') + '\n\n' + sectie + '\n'
    open(pad, 'w').write(tekst)


def main():
    args = sys.argv[1:]
    uit = args[args.index('--uit') + 1] if '--uit' in args else None
    cfg = json.load(open(rb.DATA))
    release = json.load(open(rb.STATE)) if os.path.exists(rb.STATE) else {}
    if 'hoofdissues' not in release:
        raise SystemExit('Geen hoofdissues in %s: draai eerst staging_release_branches.py --tag' % rb.STATE)

    s = json.load(open(INFRA_STATE)) if os.path.exists(INFRA_STATE) and '--opnieuw' not in args else None
    if s and 'pr' in s:
        raise SystemExit('De PR staat er al: %s. Begin een nieuwe met --opnieuw.' % s['pr'])
    if s and any(rc['status'] == 'conflict' for rc in s['rc']):
        pad = os.path.join(RUNS, 'infra')
    else:
        pad, s = voorbereiden(cfg, release)
    try:
        if rebasen(pad, s):
            tags_committen(cfg, pad, s)
            if '--droog' not in args:
                pushen(cfg, pad, s, release)
    except Afwijking as e:
        raise SystemExit(str(e))
    except subprocess.CalledProcessError as e:
        raise SystemExit('`%s` faalde: %s' % (' '.join(e.cmd), (e.stderr or '').strip()))
    finally:
        json.dump(s, open(INFRA_STATE, 'w'), indent=2)
        sectie = samenvatting(s)
        if uit:
            schrijf_sectie(uit, sectie)
            print('Samenvatting geschreven in %s' % uit, file=sys.stderr)
        else:
            print(sectie)


if __name__ == '__main__':
    main()
