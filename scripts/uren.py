#!/usr/bin/python3
"""Toont de urenstand uit LogMyTime (alleen lezen), als vervanger van de Excel-urenstand.

Gebruik: uren.py [--tot JJJJ-MM-DD] [--vanaf JJJJ-MM-DD] [--details] [--schrijf]
Standaard van 1 januari van dit jaar tot en met vandaag. Tijden worden niet afgerond:
de som van DurationSeconds, zoals ik ze zelf al afgerond log.
Met --schrijf (alleen voor de standaardperiode) wordt de stand ook weggeschreven naar
gebieden/werk/uren-overzicht.md. De sleutel komt uit LOGMYTIME_API_KEY in ~/vault/.env en wordt nooit getoond.
"""
import argparse
import csv
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
VRIJE_DAGEN = os.path.expanduser('~/vault/data/vrije-dagen-2026.csv')
OVERZICHT = os.path.expanduser('~/vault/gebieden/werk/uren-overzicht.md')
MAANDEN = ['jan', 'feb', 'mrt', 'apr', 'mei', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec']


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


def vrije_dagen():
    """Regels uit data/vrije-dagen-2026.csv als (omschrijving, gepland, nog gereserveerd)."""
    with open(VRIJE_DAGEN, newline='') as f:
        return [(r['omschrijving'], float(r['gepland_uren']), float(r['nog_gereserveerd_uren']))
                for r in csv.DictReader(f)]


def gereserveerd_uren():
    """Som van de nog gereserveerde vrije uren uit data/vrije-dagen-2026.csv."""
    return sum(nog for _, _, nog in vrije_dagen())


def haal_stand(vanaf, tot):
    klanten = {k['ID']: k['Name'] for k in get_all('Clients', {'$select': 'ID,Name'})}
    # Projecten zonder klant (zoals "Niet declarabel") tellen niet mee als declarabel.
    projecten = {p['ID']: klanten.get(p['ClientID']) for p in get_all('Projects', {'$select': 'ID,ClientID'})}
    # Ruim filteren op UTC; de lokale datum wordt hieronder exact bepaald.
    entries = get_all('TimeEntries', {
        '$filter': 'StartTime ge %s and StartTime lt %s' % (
            odata_datum(vanaf - timedelta(days=1)), odata_datum(tot + timedelta(days=2))),
        '$select': 'ProjectID,StartTime,DurationSeconds,TypeID,AbsenceID',
    })

    stand = {'per_klant': defaultdict(float), 'per_maand': defaultdict(float),
             'niet_declarabel': 0.0, 'per_type': defaultdict(float)}
    for e in entries:
        dag = lokale_datum(e['StartTime'])
        if not vanaf <= dag <= tot:
            continue
        uren = e['DurationSeconds'] / 3600
        stand['per_type'][(e['TypeID'], e['AbsenceID'] is not None)] += uren
        if e['AbsenceID'] is not None:
            continue
        klant = projecten.get(e['ProjectID'])
        if klant is None:
            stand['niet_declarabel'] += uren
        else:
            stand['per_klant'][klant] += uren
            stand['per_maand'][(dag.month, klant)] += uren
    stand['declarabel'] = sum(stand['per_klant'].values())
    stand['target'] = target_uren(vanaf, tot)
    stand['vrij'] = stand['target'] - stand['declarabel']
    stand['gereserveerd'] = gereserveerd_uren()
    return stand


def nl(getal):
    return ('%.2f' % getal).replace('.', ',')


def schrijf_overzicht(vanaf, tot, stand):
    klanten = sorted(stand['per_klant'], key=lambda k: -stand['per_klant'][k])
    over = VRIJ_BUDGET - stand['vrij']
    na_reservering = over - stand['gereserveerd']
    regels = [
        '---',
        'description: Urenoverzicht %s met declarabel per klant, target, vrij-budget en gereserveerde vrije uren' % vanaf.year,
        'tags: [werk, uren]',
        '---',
        '',
        '# Urenoverzicht %s' % vanaf.year,
        '',
        '> Gegenereerd door `scripts/uren.py --schrijf` (skill `/uren`) uit LogMyTime. Niet met de hand bewerken.',
        '> Peildatum **%s**. Achtergrond en logica: [[urenregistratie]].' % tot.strftime('%d-%m-%Y'),
        '',
        '## Stand',
        '',
        '| Stand | Uren | | Declarabel per klant | Uren |',
        '|---|---:|---|---|---:|',
    ]
    stand_rijen = [
        ('Declarabel', nl(stand['declarabel'])),
        ('Target (werkuren)', nl(stand['target'])),
        ('Vrij opgenomen', nl(stand['vrij'])),
        ('Vrij-budget', '%d,00' % VRIJ_BUDGET),
        ('Vrij over', nl(over)),
        ('Nog gereserveerd', nl(stand['gereserveerd'])),
        ('**Vrij na reservering**', '**%s**' % nl(na_reservering)),
    ]
    klant_rijen = [(k, nl(stand['per_klant'][k])) for k in klanten]
    klant_rijen += [('**Totaal declarabel**', '**%s**' % nl(stand['declarabel'])),
                    ('Niet declarabel', nl(stand['niet_declarabel']))]
    klant_rijen += [('', '')] * (len(stand_rijen) - len(klant_rijen))
    regels += ['| %s | %s | | %s | %s |' % (sl, su, kl, ku)
               for (sl, su), (kl, ku) in zip(stand_rijen, klant_rijen)]
    regels += ['',
               '## Vrije uren: gepland en gereserveerd',
               '',
               '| Omschrijving | Gepland | Nog gereserveerd |',
               '|---|---:|---:|']
    dagen = vrije_dagen()
    regels += ['| %s | %s | %s |' % (o, nl(g), nl(n)) for o, g, n in dagen]
    regels += ['| **Totaal** | **%s** | **%s** |' % (nl(sum(g for _, g, _ in dagen)), nl(stand['gereserveerd'])),
               '',
               'Bron: `data/vrije-dagen-2026.csv`. Is een geplande dag voorbij, zet dan `nog_gereserveerd_uren` op 0.']
    regels += ['',
               '## Declarabel per maand',
               '',
               '| Maand | %s | Totaal |' % ' | '.join(klanten),
               '|---|%s---:|' % ('---:|' * len(klanten))]
    for m in range(1, tot.month + 1):
        cellen = [stand['per_maand'].get((m, k), 0.0) for k in klanten]
        regels.append('| %s | %s | %s |' % (MAANDEN[m - 1], ' | '.join(nl(c) for c in cellen), nl(sum(cellen))))
    with open(OVERZICHT, 'w') as f:
        f.write('\n'.join(regels) + '\n')


def main():
    vandaag = date.today()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--vanaf', type=date.fromisoformat, default=date(vandaag.year, 1, 1))
    ap.add_argument('--tot', type=date.fromisoformat, default=vandaag)
    ap.add_argument('--details', action='store_true', help='toon ook uren per TypeID en afwezigheid')
    ap.add_argument('--schrijf', action='store_true', help='schrijf de stand naar gebieden/werk/uren-overzicht.md')
    args = ap.parse_args()
    if args.schrijf and (args.vanaf != date(vandaag.year, 1, 1) or args.tot != vandaag):
        raise SystemExit('--schrijf kan alleen voor de standaardperiode (1 januari t/m vandaag)')

    stand = haal_stand(args.vanaf, args.tot)
    print('Stand van %s t/m %s' % (args.vanaf, args.tot))
    for naam, uren in sorted(stand['per_klant'].items(), key=lambda kv: -kv[1]):
        print('  %-20s %9.2f u' % (naam, uren))
    print('Declarabel           %9.2f u' % stand['declarabel'])
    print('Niet declarabel      %9.2f u' % stand['niet_declarabel'])
    print('Target (werkuren)    %9.2f u' % stand['target'])
    print('Vrij opgenomen       %9.2f u (budget %d u, over %.2f u)' % (
        stand['vrij'], VRIJ_BUDGET, VRIJ_BUDGET - stand['vrij']))
    print('Vrij gereserveerd    %9.2f u' % stand['gereserveerd'])
    print('Vrij na reservering  %9.2f u (vrij over min gereserveerd)' % (
        VRIJ_BUDGET - stand['vrij'] - stand['gereserveerd']))
    if args.details:
        print('Per TypeID (afwezigheid ja/nee):')
        for (type_id, afwezig), uren in sorted(stand['per_type'].items()):
            print('  TypeID %s, afwezigheid=%s: %.2f u' % (type_id, afwezig, uren))
    if args.schrijf:
        schrijf_overzicht(args.vanaf, args.tot, stand)
        print('Geschreven naar %s' % OVERZICHT)


main()
