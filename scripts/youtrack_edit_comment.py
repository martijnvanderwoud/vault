#!/usr/bin/python3
"""Vervangt tekst in een bestaande YouTrack-comment, via de REST-API.

De MCP kan comments alleen toevoegen. Gebruik: youtrack_edit_comment.py ISSUE COMMENT-ID OUD NIEUW
(COMMENT-ID zoals `120-634`, uit de URL-fragment `Comments-120-634.0-0`). OUD moet precies één keer
in de comment voorkomen. Het token komt uit YOUTRACK_TOKEN in ~/vault/.env en wordt nooit getoond.
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
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    issue, comment, old, new = sys.argv[1:]
    url = '%s/issues/%s/comments/%s' % (BASE, issue, comment)
    headers = {'Authorization': 'Bearer ' + token(), 'Content-Type': 'application/json',
               'Accept': 'application/json'}
    text = json.load(urllib.request.urlopen(urllib.request.Request(url + '?fields=text', headers=headers)))['text']
    if text.count(old) != 1:
        raise SystemExit('"%s" komt %d keer voor, verwacht 1' % (old, text.count(old)))
    body = json.dumps({'text': text.replace(old, new)}).encode()
    urllib.request.urlopen(urllib.request.Request(url + '?fields=id', data=body, headers=headers, method='POST')).read()
    print('comment %s van %s bijgewerkt' % (comment, issue))


main()
