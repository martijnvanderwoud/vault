#!/usr/bin/python3
"""Overzicht van wat er naar staging gaat: per hoofdissue de repo's en issues.

Leest de repo's uit data/staging-repos.json, haalt per repo de commits op die in develop
staan en niet in master (via gh, zonder lokale clones), en volgt de issuenummers in de
commits via de YouTrack-parents tot het hoofdissue. Toont ook de rc-branches in infra.
Gebruik: staging_overzicht.py [--uit BESTAND]. Zonder --uit gaat de markdown naar stdout.
Het token komt uit YOUTRACK_TOKEN in ~/vault/.env en wordt nooit getoond.
"""
import datetime
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = 'https://crimsoncricket.myjetbrains.com/youtrack/api'
DATA = os.path.expanduser('~/vault/data/staging-repos.json')
ISSUE_RE = re.compile(r'\b([A-Z][A-Z0-9]+-\d+)\b')
UPGRADE_RE = re.compile(r'(Dependabot|Scala Steward) upgrades \d{4} w\d')
PR_RE = re.compile(r'\(#(\d+)\)$')
RC_RE = re.compile(r'([A-Z][A-Z0-9]+-\d+)-rc$')
# Automatische updates: Dependabot, Scala Steward en de lock-file-workflow van portal-ui-common.
BUMP_RE = re.compile(r'^(Bump |Update .* in develop \(#\d+\)$|chore: update portal-ui-common lock file$|Merge pull request #\d+ from \S+/dependabot/)')


def token():
    path = os.path.expanduser('~/vault/.env')
    for line in reversed(open(path).read().splitlines()):
        if line.startswith('YOUTRACK_TOKEN='):
            return line.split('=', 1)[1].strip()
    raise SystemExit('YOUTRACK_TOKEN ontbreekt in ' + path)


TOKEN = token()


def youtrack(path, fields, extra=''):
    url = '%s/%s?fields=%s%s' % (BASE, path, urllib.parse.quote(fields), extra)
    headers = {'Authorization': 'Bearer ' + TOKEN, 'Accept': 'application/json'}
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=headers)))


def gh(path, pogingen=5):
    """gh api met een paar herkansingen: de GitHub-API faalt soms kortstondig."""
    for poging in range(pogingen):
        try:
            return json.loads(subprocess.run(['gh', 'api', path], check=True, capture_output=True, text=True).stdout)
        except (subprocess.CalledProcessError, ValueError):
            if poging == pogingen - 1:
                raise
            time.sleep(3 * 2 ** poging)


def commits_alleen_in(org, repo, base, head):
    """Commits in head die niet in base staan, oudste eerst."""
    commits, page = [], 1
    while True:
        data = gh('repos/%s/%s/compare/%s...%s?per_page=100&page=%d' % (org, repo, base, head, page))
        commits += data['commits']
        if len(commits) >= data['total_commits'] or not data['commits']:
            return commits
        page += 1


def titel(commit):
    return commit['commit']['message'].split('\n')[0]


def master_titels(org, repo, commits, base='master'):
    """Titels van commits in base (meestal master) sinds de oudste commit die daar nog niet in staat."""
    if not commits:
        return set()
    since = min(c['commit']['committer']['date'] for c in commits)
    out = subprocess.run(['gh', 'api', '--paginate', 'repos/%s/%s/commits?sha=%s&per_page=100&since=%s'
                          % (org, repo, base, since), '--jq', '.[] | select(.parents | length == 1) | '
                          '.commit.message | split("\\n")[0]'],
                         check=True, capture_output=True, text=True).stdout
    return set(out.splitlines())


MISLUKT = []  # PR-lookups die ook na herkansingen mislukten


def issues_uit_pr(org, repo, msg, keys):
    """Issuenummers uit de titel en branch van de PR, als de squash-commit ze kwijt is."""
    m = PR_RE.search(msg)
    if not m:
        return []
    try:
        pr = gh('repos/%s/%s/pulls/%s' % (org, repo, m.group(1)))
    except (subprocess.CalledProcessError, ValueError) as e:
        MISLUKT.append('`%s` PR #%s: %s' % (repo, m.group(1), str(getattr(e, 'stderr', e)).strip()))
        return []
    tekst = pr['title'] + ' ' + pr['head']['ref']
    return sorted({i for i in ISSUE_RE.findall(tekst) if i.split('-')[0] in keys})


def project_keys():
    return {p['shortName'] for p in youtrack('admin/projects', 'shortName', '&$top=1000')}


ISSUES = {}


def issue(id_):
    if id_ not in ISSUES:
        try:
            data = youtrack('issues/' + id_, 'idReadable,summary,parent(issues(idReadable)),'
                                            'customFields(name,value(name))')
        except urllib.error.HTTPError:
            ISSUES[id_] = None
            return None
        fields = {c['name']: c['value'] for c in data['customFields']}
        parents = (data.get('parent') or {}).get('issues') or []
        ISSUES[id_] = {
            'id': data['idReadable'],
            'summary': data['summary'],
            'type': (fields.get('Type') or {}).get('name', ''),
            'state': (fields.get('State') or {}).get('name', ''),
            'parent': parents[0]['idReadable'] if parents else None,
        }
    return ISSUES[id_]


def hoofdissue(id_):
    gezien = set()
    huidig = issue(id_)
    while huidig and huidig['parent'] and huidig['id'] not in gezien:
        gezien.add(huidig['id'])
        huidig = issue(huidig['parent']) or huidig
        if huidig['id'] in gezien:
            break
    return huidig


def rc_branches(org, infra):
    out = subprocess.run(['gh', 'api', '--paginate', 'repos/%s/%s/branches?per_page=100' % (org, infra),
                          '--jq', '.[].name'], check=True, capture_output=True, text=True).stdout
    result = {}
    for name in out.split():
        m = RC_RE.search(name)
        if m:
            result[m.group(1)] = name
    return result


def infra_status(org, infra, branch):
    """Stand van een rc-branch ten opzichte van develop."""
    data = gh('repos/%s/%s/compare/develop...%s' % (org, infra, branch))
    return {'vooruit': data['ahead_by'], 'achter': data['behind_by'],
            'commits': [titel(c) for c in data['commits'] if len(c['parents']) == 1],
            'bestanden': sorted(f['filename'] for f in data.get('files', []))}


def analyseer(org, repo, keys, base='master', head='develop'):
    """Commits in head die niet in base staan, gekoppeld aan hun hoofdissues.

    Geeft (aantal commits, {hoofdissue-id: set(issue-ids)}, titels zonder issue, aantal bumps,
    titels die als hotfix al in master staan).
    """
    commits = commits_alleen_in(org, repo, base, head)
    # Hotfixes worden naar develop gecherrypickt: zelfde titel, andere SHA.
    in_master = master_titels(org, repo, commits, base)
    per_root, zonder, bumps, gepickt = {}, [], 0, []
    for c in commits:
        msg = titel(c)
        if len(c['parents']) == 1 and msg in in_master:
            gepickt.append(msg)
            continue
        ids = [i for i in ISSUE_RE.findall(c['commit']['message']) if i.split('-')[0] in keys]
        if not ids:
            if BUMP_RE.match(msg):
                bumps += 1
                continue
            if len(c['parents']) > 1 or msg.startswith('Update for the next development version') \
                    or msg.startswith('Update for next development version'):
                continue
            ids = issues_uit_pr(org, repo, msg, keys)
            if not ids:
                zonder.append(msg)
                continue
        for id_ in ids:
            root = hoofdissue(id_)
            per_root.setdefault(root['id'] if root else id_, set()).add(id_)
    return len(commits), per_root, zonder, bumps, gepickt


def is_upgrade(root_id):
    return bool(UPGRADE_RE.search((issue(root_id) or {}).get('summary', '')))


def main():
    uit = None
    if sys.argv[1:2] == ['--uit'] and len(sys.argv) == 3:
        uit = sys.argv[2]
    elif len(sys.argv) > 1:
        raise SystemExit(__doc__)

    config = json.load(open(DATA))
    org = config['org']
    keys = project_keys()

    hoofd = {}  # hoofdissue-id -> {'repos': {repo: set(issue-ids)}}
    per_repo = []
    gepickt = []  # (repo, titel) van commits die als hotfix al in master staan
    for entry in config['repos']:
        repo = entry['repo']
        try:
            n, per_root, zonder, bumps, al_in_master = analyseer(org, repo, keys)
        except subprocess.CalledProcessError as e:
            per_repo.append((entry, None, [], 0, e.stderr.strip()))
            continue
        gepickt += [(repo, msg) for msg in al_in_master]
        for root_id, ids in per_root.items():
            hoofd.setdefault(root_id, {}).setdefault(repo, set()).update(ids)
        per_repo.append((entry, n, zonder, bumps, None))

    rc = rc_branches(org, config['infra'])
    regels = ['# Staging-overzicht', '']
    if MISLUKT:
        regels += ['> [!warning] Niet alle PR\'s konden worden opgehaald',
                   '> Commits uit deze PR\'s staan bij "Zonder issue" en kunnen een hoofdissue missen. '
                   'Draai het script opnieuw.', '>']
        regels += ['> - ' + m for m in MISLUKT]
        regels.append('')

    regels += ['## Configuratie klaar in infra', '']
    if rc:
        regels += ['| Hoofdissue | Branch | Commits in repo\'s | Voor/achter develop | Commits in branch | Bestanden |',
                   '| --- | --- | --- | --- | --- | --- |']
        for root_id in sorted(rc):
            st = infra_status(org, config['infra'], rc[root_id])
            root = issue(root_id)
            naam = '%s %s' % (root_id, root['summary']) if root else root_id
            regels.append('| %s | `%s` | %s | %d / %d | %s | %s |' % (
                naam, rc[root_id], 'ja' if root_id in hoofd else '**nee, controleren**',
                st['vooruit'], st['achter'], '<br>'.join(m.replace('|', '/') for m in st['commits']),
                '<br>'.join('`%s`' % f for f in st['bestanden'])))
    else:
        regels.append('- geen rc-branches')
    regels.append('')

    regels += ['## Hoofdissues', '']
    for root_id in sorted(r for r in hoofd if not is_upgrade(r)):
        root = issue(root_id)
        if root:
            kop = '### %s %s' % (root_id, root['summary'])
            meta = '%s, %s' % (root['type'], root['state'])
        else:
            kop, meta = '### %s' % root_id, 'niet gevonden in YouTrack'
        regels += [kop, '', '- ' + meta]
        regels.append('- infra: `%s`' % rc[root_id] if root_id in rc else '- infra: geen rc-branch')
        for repo in sorted(hoofd[root_id]):
            ids = sorted(hoofd[root_id][repo] - {root_id})
            regels.append('- `%s`%s' % (repo, ': ' + ', '.join(ids) if ids else ''))
        regels.append('')

    regels += ['## Dependabot- en Scala Steward-hoofdissues', '',
               '| Hoofdissue | State | infra | Repo\'s |', '| --- | --- | --- | --- |']
    for root_id in sorted(r for r in hoofd if is_upgrade(r)):
        root = issue(root_id)
        repos = '<br>'.join('`%s`: %s' % (repo, ', '.join(sorted(hoofd[root_id][repo] - {root_id})))
                            for repo in sorted(hoofd[root_id]))
        regels.append('| %s %s | %s | %s | %s |' % (root_id, root['summary'], root['state'],
                                                    '`%s`' % rc[root_id] if root_id in rc else '-', repos))
    regels.append('')

    regels += ['## Al in productie (cherry-pick van een hotfix)', '']
    regels += ['- `%s`: %s' % g for g in gepickt] or ['- geen']
    regels.append('')

    regels += ['## Per repo', '', '| Repo | Rol | Commits | Bumps | Zonder issue |', '| --- | --- | --- | --- | --- |']
    for entry, n, zonder, bumps, fout in per_repo:
        rol = entry['rol'] + (' → ' + entry['in'] if entry.get('in') else '')
        if fout:
            regels.append('| `%s` | %s | fout: %s | | |' % (entry['repo'], rol, fout.replace('|', '/')))
        else:
            regels.append('| `%s` | %s | %d | %d | %s |' % (entry['repo'], rol, n, bumps, '<br>'.join(zonder)))
    regels.append('')

    tekst = '\n'.join(regels)
    if uit:
        kop = '---\ndescription: Staging-overzicht van %s, gegenereerd door scripts/staging_overzicht.py\n' \
              'tags: [pompkracht, staging]\ncssclasses: [wide-page]\n---\n\n' % datetime.date.today().isoformat()
        open(uit, 'w').write(kop + tekst)
        print('geschreven naar ' + uit)
    else:
        print(tekst)


if __name__ == '__main__':
    main()
