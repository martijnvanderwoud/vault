"""Gedeelde toegang tot de YouTrack REST API, voor uren_naar_youtrack.py en logmytime_taken_archiveren.py.

Het token komt uit YOUTRACK_TOKEN in ~/vault/.env en wordt nooit getoond.
"""
import json
import os
import re
import urllib.request

YT = 'https://crimsoncricket.myjetbrains.com/youtrack/api'
# Issue-ID vooraan in een LogMyTime-taaknaam, zoals 'PKP-890 …'.
ISSUE_ID = re.compile(r'^([A-Z][A-Z0-9_]*-\d+)\b')


def token():
    path = os.path.expanduser('~/vault/.env')
    for line in reversed(open(path).read().splitlines()):
        if line.startswith('YOUTRACK_TOKEN='):
            return line.split('=', 1)[1].strip()
    raise SystemExit('YOUTRACK_TOKEN ontbreekt in ' + path)


def yt(pad, body=None):
    """GET op pad, of POST met body als JSON. Geeft het JSON-antwoord terug."""
    headers = {'Authorization': 'Bearer ' + token(), 'Accept': 'application/json',
               'Content-Type': 'application/json'}
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(YT + pad, data=data, headers=headers, method='POST' if data else 'GET')
    return json.load(urllib.request.urlopen(request))
