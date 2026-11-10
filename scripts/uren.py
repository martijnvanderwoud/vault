#!/usr/bin/python3
"""Toont de urenstand uit LogMyTime (alleen lezen), als vervanger van de Excel-urenstand.

Gebruik: uren.py [--tot JJJJ-MM-DD] [--vanaf JJJJ-MM-DD] [--details]
Standaard van 1 januari van dit jaar tot en met vandaag. Tijden worden niet afgerond:
de som van DurationSeconds, zoals ik ze zelf al afgerond log.
De sleutel komt uit LOGMYTIME_API_KEY in ~/vault/.env en wordt nooit getoond.
"""
import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

BASE = 'https://api.logmytime.de/V1/Api.svc'
TZ = ZoneInfo('Europe/Amsterdam')
# Werkuren per weekdag (ma t/m vr), 28 u per week.
UREN_PER_WEEKDAG = [6.5, 6.5, 4.5, 6.25, 4.25]
VRIJ_BUDGET = 196


def key():
    path = os.path.expanduser('~/vault/.env')
    for line in reversed(open(path).read().splitlines()):
        if line.startswith('LOGMYTIME_API_KEY='):
            sleutel = line.split('=', 1)[1].strip()
            if sleutel:
                return sleutel
    raise SystemExit('LOGMYTIME_API_KEY ontbreekt of is leeg in ' + path)


def get_all(resource, params):
    """Haalt alle pagina's van een OData-resource op (max 10.000 entities per response)."""
    url = BASE + '/' + resource + '?' + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    headers = {'X-LogMyTimeApiKey': key(), 'Accept': 'application/json'}
    resultaten = []
    while url:
        try:
            data = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=headers)))['d']
        except urllib.error.HTTPError as e:
            raise SystemExit('LogMyTime API gaf HTTP %s %s voor %s' % (e.code, e.reason, resource))
        if isinstance(data, list):
            resultaten += data
            url = None
        else:
            resultaten += data['results']
            url = data.get('__next')
    return resultaten


def odata_datum(d):
    return "datetime'%sT00:00:00'" % d.isoformat()


def lokale_datum(ms):
    return datetime.fromtimestamp(int(ms[6:-2]) / 1000, timezone.utc).astimezone(TZ).date()


def target_uren(vanaf, tot):
    """Werkdagen vanaf t/m tot (beide inclusief, zonder feestdagen) × uren per weekdag."""
    totaal = 0.0
    dag = vanaf
    while dag <= tot:
        if dag.weekday() < 5:
            totaal += UREN_PER_WEEKDAG[dag.weekday()]
        dag += timedelta(days=1)
    return totaal


def main():
    vandaag = date.today()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--vanaf', type=date.fromisoformat, default=date(vandaag.year, 1, 1))
    ap.add_argument('--tot', type=date.fromisoformat, default=vandaag)
    ap.add_argument('--details', action='store_true', help='toon ook uren per TypeID en afwezigheid')
    args = ap.parse_args()

    klanten = {k['ID']: k['Name'] for k in get_all('Clients', {'$select': 'ID,Name'})}
    # Projecten zonder klant (zoals "Niet declarabel") tellen niet mee als declarabel.
    projecten = {p['ID']: klanten.get(p['ClientID']) for p in get_all('Projects', {'$select': 'ID,ClientID'})}
    # Ruim filteren op UTC; de lokale datum wordt hieronder exact bepaald.
    entries = get_all('TimeEntries', {
        '$filter': 'StartTime ge %s and StartTime lt %s' % (
            odata_datum(args.vanaf - timedelta(days=1)), odata_datum(args.tot + timedelta(days=2))),
        '$select': 'ProjectID,StartTime,DurationSeconds,TypeID,AbsenceID',
    })

    per_klant = defaultdict(float)
    niet_declarabel = 0.0
    per_type = defaultdict(float)
    for e in entries:
        if not args.vanaf <= lokale_datum(e['StartTime']) <= args.tot:
            continue
        uren = e['DurationSeconds'] / 3600
        per_type[(e['TypeID'], e['AbsenceID'] is not None)] += uren
        if e['AbsenceID'] is not None:
            continue
        klant = projecten.get(e['ProjectID'])
        if klant is None:
            niet_declarabel += uren
        else:
            per_klant[klant] += uren

    declarabel = sum(per_klant.values())
    target = target_uren(args.vanaf, args.tot)
    vrij = target - declarabel
    print('Stand van %s t/m %s' % (args.vanaf, args.tot))
    for naam, uren in sorted(per_klant.items(), key=lambda kv: -kv[1]):
        print('  %-20s %9.2f u' % (naam, uren))
    print('Declarabel           %9.2f u' % declarabel)
    print('Niet declarabel      %9.2f u' % niet_declarabel)
    print('Target (werkuren)    %9.2f u' % target)
    print('Vrij opgenomen       %9.2f u (budget %d u, over %.2f u)' % (vrij, VRIJ_BUDGET, VRIJ_BUDGET - vrij))
    if args.details:
        print('Per TypeID (afwezigheid ja/nee):')
        for (type_id, afwezig), uren in sorted(per_type.items()):
            print('  TypeID %s, afwezigheid=%s: %.2f u' % (type_id, afwezig, uren))


main()
