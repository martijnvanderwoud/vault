#!/usr/bin/env python3
"""Pusht een feature/*-branch van een repo van Pompkracht naar origin.

Vervangt de allow-regels `git -C * push [-u] origin feature/*`: daarin mocht de `*` ook opties
bevatten (bijvoorbeeld `-c core.hooksPath=/dev/null` of een extra refspec naar develop).

Gebruik: push_feature.py <repo-pad> <feature/branch> [-u]

Controles:
- de branchnaam is feature/<segmenten> met alleen letters, cijfers, `.`, `_` en `-`
- de repo is niet de vault, en origin wijst naar de GitHub-organisatie van Pompkracht
- de lokale branch bestaat

Daarna precies één push met een expliciete refspec, zonder shell en zonder extra opties.
"""
import json
import os
import re
import subprocess
import sys

VAULT = os.path.realpath(os.path.expanduser('~/vault'))
DATA = os.path.join(VAULT, 'data', 'staging-repos.json')
BRANCH = re.compile(r'^feature/[A-Za-z0-9_-][A-Za-z0-9._-]*(/[A-Za-z0-9_-][A-Za-z0-9._-]*)*$')


def fout(tekst):
    print('push_feature: ' + tekst, file=sys.stderr)
    sys.exit(2)


def git(repo, *args):
    return subprocess.run(['git', '-C', repo, *args], capture_output=True, text=True)


def main(argv):
    upstream = '-u' in argv
    rest = [a for a in argv if a != '-u']
    if len(rest) != 2:
        fout('gebruik: push_feature.py <repo-pad> <feature/branch> [-u]')
    repo, branch = os.path.realpath(os.path.expanduser(rest[0])), rest[1]

    if not BRANCH.match(branch) or '..' in branch or branch.endswith('.lock'):
        fout('ongeldige branchnaam %r: alleen feature/<naam> toegestaan' % branch)

    top = git(repo, 'rev-parse', '--show-toplevel')
    if top.returncode != 0:
        fout('%s is geen git-repo' % repo)
    if os.path.realpath(top.stdout.strip()) == VAULT:
        fout('de vault push je zelf, niet via dit script')

    with open(DATA) as f:
        org = json.load(f)['org']
    origin = git(repo, 'remote', 'get-url', 'origin').stdout.strip()
    if not re.match(r'^(git@github\.com:|https://github\.com/)%s/[^/]+$' % re.escape(org), origin):
        fout('origin %r hoort niet bij %s' % (origin, org))

    if git(repo, 'rev-parse', '--verify', '--quiet', 'refs/heads/' + branch).returncode != 0:
        fout('lokale branch %s bestaat niet' % branch)

    ref = 'refs/heads/' + branch
    cmd = ['git', '-C', repo, 'push'] + (['-u'] if upstream else []) + ['origin', '%s:%s' % (ref, ref)]
    sys.exit(subprocess.run(cmd).returncode)


if __name__ == '__main__':
    main(sys.argv[1:])
