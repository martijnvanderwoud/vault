#!/usr/bin/python3
"""Archiveert actieve LogMyTime-taken waarvan het YouTrack-issue al een tijd is opgelost.

Gebruik: logmytime_taken_archiveren.py [--uitvoeren] [--max N]
Zonder --uitvoeren toont het script alleen het plan en wijzigt niets. Met --uitvoeren archiveert het
hooguit N taken (standaard 100), zodat er requests overblijven voor de uren-scripts (limiet 500 per
24 uur, één request per gearchiveerde taak).

Een taak wordt gearchiveerd als het issue (ID vooraan in de taaknaam) in YouTrack opgelost is,
dat al minstens 7 dagen zo is en er in die 7 dagen geen tijd meer op de taak is gelogd.
Per taak:
- archiveren: aan alle voorwaarden voldaan;
- wacht: opgelost, maar korter dan 7 dagen geleden of er is recent nog tijd gelogd;
- open: het issue is niet opgelost;
- niet gevonden: het issue bestaat niet in YouTrack of is niet zichtbaar;
- geen ID: geen issue-ID vooraan (de vaste taken zoals Reistijd worden stil overgeslagen).
De sleutels komen uit ~/vault/.env en worden nooit getoond.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from logmytime import TZ, get_all, lokale_datum, merge, odata_datum  # noqa: E402
from youtrack import ISSUE_ID, yt  # noqa: E402

DAGEN = 7
# Taken zonder issue-ID die altijd actief blijven.
VAST = {'Reistijd', 'Reistijd OV', 'Zakelijk overig'}
PORTIE = 50
ONBEKEND = re.compile(r'The value "([^"]+)" isn\'t used for the issue id field')


def opgelost_op(issues):
    """Per gevonden issue de lokale datum waarop het is opgelost (None als het open is)."""
    resultaat = {}
    for i in range(0, len(issues), PORTIE):
        portie = issues[i:i + PORTIE]
        while portie:
            query = 'issue id: ' + ', '.join(portie)
            try:
                gevonden = yt('/issues?fields=idReadable,resolved&$top=%d&query=%s' % (
                    len(portie), urllib.parse.quote(query)))
            except urllib.error.HTTPError as e:
                # Eén onbekend ID laat de hele query mislukken; de fout noemt welke.
                fouten = json.loads(e.read()).get('error_children', []) if e.code == 400 else []
                onbekend = {m for f in fouten for m in ONBEKEND.findall(f.get('error', ''))}
                if not onbekend & set(portie):
                    raise
                portie = [p for p in portie if p not in onbekend]
                continue
            for issue in gevonden:
                ms = issue['resolved']
                resultaat[issue['idReadable']] = None if ms is None else datetime.fromtimestamp(
                    ms / 1000, timezone.utc).astimezone(TZ).date()
            break
    return resultaat


def volgorde(regel):
    """Sorteert op project en dan op issuenummer, dus PKI-587 voor PKI-1111."""
    project, nummer = regel[0].rsplit('-', 1)
    return project, int(nummer)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--uitvoeren', action='store_true', help='archiveer de taken ook echt in LogMyTime')
    ap.add_argument('--max', type=int, default=100, help='hooguit zoveel taken archiveren (standaard 100)')
    args = ap.parse_args()
    grens = date.today() - timedelta(days=DAGEN)

    taken = get_all('Tasks', {'$filter': 'Active eq true', '$select': 'ID,Description'})
    entries = get_all('TimeEntries', {
        '$filter': 'StartTime ge %s' % odata_datum(grens),
        '$select': 'TaskID,StartTime',
    })
    laatst_gelogd = {}
    for e in entries:
        dag = lokale_datum(e['StartTime'])
        if e['TaskID'] is not None and dag > grens:
            laatst_gelogd[e['TaskID']] = max(dag, laatst_gelogd.get(e['TaskID'], dag))

    met_id = {}
    zonder_id = []
    for t in taken:
        naam = (t['Description'] or '').strip()
        match = ISSUE_ID.match(naam)
        if match:
            met_id[t['ID']] = (match.group(1), naam)
        elif naam not in VAST:
            zonder_id.append(naam or '(geen naam, ID %d)' % t['ID'])
    opgelost = opgelost_op(sorted({issue for issue, _ in met_id.values()}))

    regels = {'archiveren': [], 'wacht': [], 'open': [], 'niet gevonden': []}
    for taak_id, (issue, naam) in met_id.items():
        if issue not in opgelost:
            regels['niet gevonden'].append((issue, naam, '', taak_id))
        elif opgelost[issue] is None:
            regels['open'].append((issue, naam, '', taak_id))
        elif opgelost[issue] > grens or taak_id in laatst_gelogd:
            redenen = ['opgelost %s' % opgelost[issue].strftime('%d-%m')]
            if taak_id in laatst_gelogd:
                redenen.append('gelogd %s' % laatst_gelogd[taak_id].strftime('%d-%m'))
            regels['wacht'].append((issue, naam, ', '.join(redenen), taak_id))
        else:
            regels['archiveren'].append((issue, naam, 'opgelost %s' % opgelost[issue].strftime('%d-%m-%Y'), taak_id))

    print('Actieve LogMyTime-taken: %d, grens %s%s' % (
        len(taken), grens.strftime('%d-%m-%Y'), '' if args.uitvoeren else ' (alleen plan)'))
    for status, lijst in regels.items():
        print('\n%s: %d' % (status, len(lijst)))
        for issue, naam, toelichting, _ in sorted(lijst, key=volgorde):
            print('  %-50.50s %s' % (naam, toelichting))
    print('\ngeen ID: %d' % len(zonder_id))
    for naam in sorted(zonder_id):
        print('  %s' % naam)

    if not args.uitvoeren:
        return
    te_doen = sorted(regels['archiveren'], key=volgorde)[:args.max]
    print('\nArchiveren: %d van %d (--max %d)' % (len(te_doen), len(regels['archiveren']), args.max))
    for nummer, (issue, naam, _, taak_id) in enumerate(te_doen, 1):
        merge('Tasks', taak_id, {'Active': False})
        print('  %3d. gearchiveerd: %s' % (nummer, naam), flush=True)
    print('Klaar: %d gearchiveerd, %d blijven over voor een volgende run.' % (
        len(te_doen), len(regels['archiveren']) - len(te_doen)))


if __name__ == '__main__':
    main()
