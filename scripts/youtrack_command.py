#!/usr/bin/python3
"""Voert een YouTrack-command uit op een issue, via de REST-API.

De MCP kan geen commands uitvoeren, zoals een issue op een bord zetten. Gebruik:
youtrack_command.py ISSUE COMMAND, bijvoorbeeld "add Board Pompkracht Kanban Board Kanban workflow".
Het token komt uit YOUTRACK_TOKEN in ~/vault/.env en wordt nooit getoond.
"""
import json
import os
import sys
import urllib.request

BASE = 'https://crimsoncricket.myjetbrains.com/youtrack/api'


def token():
    path = os.path.expanduser('~/vault/.env')
    for line in reversed(open(path).read().splitlines()):
        if line.startswith('YOUTRACK_TOKEN='):
            return line.split('=', 1)[1].strip()
    raise SystemExit('YOUTRACK_TOKEN ontbreekt in ' + path)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    issue, command = sys.argv[1:]
    headers = {'Authorization': 'Bearer ' + token(), 'Content-Type': 'application/json',
               'Accept': 'application/json'}
    body = json.dumps({'query': command, 'issues': [{'idReadable': issue}]}).encode()
    urllib.request.urlopen(urllib.request.Request(BASE + '/commands', data=body, headers=headers, method='POST')).read()
    print('command uitgevoerd op %s' % issue)


main()
