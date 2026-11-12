#!/usr/bin/python3
"""Neemt de uren van één dag over uit LogMyTime naar work items in YouTrack (idempotent).

Gebruik: uren_naar_youtrack.py [--dag JJJJ-MM-DD] [--uitvoeren]
Standaard vandaag. Zonder --uitvoeren toont het script alleen het plan en wijzigt niets.

LogMyTime is de bron: per issue (ID vooraan in de taaknaam) telt het de DurationSeconds van
die dag op, zonder afronden. In YouTrack hoort per issue en dag één work item van mij te staan
met die duur. Per issue:
- geen work item: aanmaken;
- één work item met dezelfde duur: niets doen;
- één work item met een andere duur: duur bijwerken naar LogMyTime;
- meerdere work items: niets doen als de som klopt, anders melden en overslaan.
Taken zonder issue-ID en work items in YouTrack zonder uren in LogMyTime worden alleen gemeld.
Het script verwijdert nooit iets. De sleutels komen uit ~/vault/.env en worden nooit getoond.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from logmytime import get_all, lokale_datum, odata_datum  # noqa: E402

YT = 'https://crimsoncricket.myjetbrains.com/youtrack/api'
ISSUE_ID = re.compile(r'^([A-Z][A-Z0-9_]*-\d+)\b')


def token():
    path = os.path.expanduser('~/vault/.env')
    for line in reversed(open(path).read().splitlines()):
        if line.startswith('YOUTRACK_TOKEN='):
            return line.split('=', 1)[1].strip()
    raise SystemExit('YOUTRACK_TOKEN ontbreekt in ' + path)


def yt(pad, body=None):
    headers = {'Authorization': 'Bearer ' + token(), 'Accept': 'application/json',
               'Content-Type': 'application/json'}
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(YT + pad, data=data, headers=headers, method='POST' if data else 'GET')
    return json.load(urllib.request.urlopen(request))


def minuten_per_issue(dag):
    """Minuten per issue op de lokale dag, plus taken zonder issue-ID (naam → minuten)."""
    taken = {t['ID']: t['Description'] or '' for t in get_all('Tasks', {'$select': 'ID,Description'})}
    entries = get_all('TimeEntries', {
        '$filter': 'StartTime ge %s and StartTime lt %s' % (
            odata_datum(dag - timedelta(days=1)), odata_datum(dag + timedelta(days=2))),
        '$select': 'TaskID,StartTime,DurationSeconds,AbsenceID',
    })
    seconden = defaultdict(int)
    zonder_issue = defaultdict(int)
    for e in entries:
        if e['AbsenceID'] is not None or lokale_datum(e['StartTime']) != dag:
            continue
        naam = taken.get(e['TaskID'], '').strip()
        match = ISSUE_ID.match(naam)
        if match:
            seconden[match.group(1)] += e['DurationSeconds']
        else:
            zonder_issue[naam or '(geen taak)'] += e['DurationSeconds']
    return ({i: round(s / 60) for i, s in seconden.items()},
            {n: round(s / 60) for n, s in zonder_issue.items()})


def work_items(dag):
    """Mijn work items in YouTrack op die dag, per issue."""
    items = yt('/workItems?fields=id,duration(minutes),issue(idReadable)&author=me'
               '&startDate=%s&endDate=%s&$top=1000' % (dag.isoformat(), dag.isoformat()))
    per_issue = defaultdict(list)
    for w in items:
        per_issue[w['issue']['idReadable']].append((w['id'], w['duration']['minutes']))
    return per_issue


def duur(minuten):
    return '%d:%02d' % divmod(minuten, 60)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dag', type=date.fromisoformat, default=date.today())
    ap.add_argument('--uitvoeren', action='store_true', help='voer het plan ook echt uit in YouTrack')
    args = ap.parse_args()
    dag = args.dag
    # YouTrack slaat de dag van een work item op als middernacht UTC.
    datum_ms = int(datetime(dag.year, dag.month, dag.day, tzinfo=timezone.utc).timestamp() * 1000)

    gewenst, zonder_issue = minuten_per_issue(dag)
    bestaand = work_items(dag)
    print('Uren van %s, LogMyTime → YouTrack%s' % (dag.isoformat(), '' if args.uitvoeren else ' (alleen plan)'))

    fouten = 0
    for issue in sorted(gewenst):
        minuten = gewenst[issue]
        items = bestaand.get(issue, [])
        totaal = sum(m for _, m in items)
        if not items:
            actie, pad, body = 'aanmaken', '/issues/%s/timeTracking/workItems' % issue, {
                'date': datum_ms, 'duration': {'minutes': minuten}}
        elif totaal == minuten:
            print('  ok          %-12s %6s' % (issue, duur(minuten)))
            continue
        elif len(items) == 1:
            actie, pad, body = 'bijwerken', '/issues/%s/timeTracking/workItems/%s' % (issue, items[0][0]), {
                'duration': {'minutes': minuten}}
        else:
            print('  OVERSLAAN   %-12s %6s in LogMyTime, %d work items met samen %s in YouTrack' % (
                issue, duur(minuten), len(items), duur(totaal)))
            continue
        toelichting = '' if not items else ' (was %s)' % duur(totaal)
        if args.uitvoeren:
            try:
                yt(pad, body)
            except urllib.error.HTTPError as e:
                fouten += 1
                print('  FOUT        %-12s %6s %s: HTTP %s %s' % (issue, duur(minuten), actie, e.code, e.reason))
                continue
        print('  %-11s %-12s %6s%s' % (actie, issue, duur(minuten), toelichting))

    for naam in sorted(zonder_issue):
        print('  GEEN ISSUE  %6s  %s' % (duur(zonder_issue[naam]), naam))
    for issue in sorted(set(bestaand) - set(gewenst)):
        print('  ALLEEN YT   %-12s %6s staat in YouTrack, niet in LogMyTime' % (
            issue, duur(sum(m for _, m in bestaand[issue]))))
    print('Totaal LogMyTime met issue: %s' % duur(sum(gewenst.values())))
    if fouten:
        raise SystemExit('%d actie(s) mislukt' % fouten)


main()
