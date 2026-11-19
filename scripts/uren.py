#!/usr/bin/python3
"""Toont de urenstand uit LogMyTime (alleen lezen): het weekgebaseerde jaar, het weektarget en deze week.

Gebruik: uren.py [--tot JJJJ-MM-DD] [--vanaf JJJJ-MM-DD] [--details] [--schrijf] [--zet-week]
Peildatum (--tot) is standaard vandaag. Het jaar volgt de ISO-weken van de peildatum (2026 begint als
overgang bij week 2, ma 5-1); --vanaf (standaard het begin van dat jaar) geldt alleen voor declarabel per
klant. Tijden worden niet afgerond: de som van DurationSeconds, zoals ik ze zelf al afgerond log.
Met --schrijf (alleen voor de standaardperiode) wordt de stand ook weggeschreven naar
gebieden/werk/uren-overzicht.md. Met --zet-week (peildatum een zondag) wordt het weektarget van de week
erna vastgezet in data/weekplanning/weektargets.csv; een week die er al staat, verandert niet meer.
De sleutel komt uit LOGMYTIME_API_KEY in ~/vault/.env en wordt nooit getoond.
"""
import argparse
import csv
import os
import sys
from collections import defaultdict
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from logmytime import get_all, lokale_datum, odata_datum  # noqa: E402
import vrije_dagen  # noqa: E402

UREN_PER_WEEK = 28
VRIJ_BUDGET = 196
WEEKTARGETS = os.path.expanduser('~/vault/data/weekplanning/weektargets.csv')
OVERZICHT = os.path.expanduser('~/vault/gebieden/werk/uren-overzicht.md')


def jaar(iso_jaar):
    """Begin (maandag) en eind (zondag) van het weekgebaseerde jaar; 2026 begint als overgang bij week 2."""
    begin = date.fromisocalendar(iso_jaar, 2 if iso_jaar == 2026 else 1, 1)
    laatste_week = date(iso_jaar, 12, 28).isocalendar().week
    return begin, date.fromisocalendar(iso_jaar, laatste_week, 7)


def werkdagen(vanaf, tot):
    """Aantal werkdagen (ma t/m vr) van vanaf t/m tot."""
    return sum(1 for i in range((tot - vanaf).days + 1) if (vanaf + timedelta(days=i)).weekday() < 5)


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

    stand = {'per_dag_klant': defaultdict(float), 'per_dag': defaultdict(float),
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
            stand['per_dag_klant'][(dag, klant)] += uren
            stand['per_dag'][dag] += uren
    return stand


def declarabel(per_dag, vanaf, tot):
    return sum(uren for dag, uren in per_dag.items() if vanaf <= dag <= tot)


def jaarstand(per_dag, peildatum, iso_jaar=None):
    """Stand van het weekgebaseerde jaar t/m de peildatum en het weektarget dat daaruit volgt.

    Weektarget = (jaardoel − declarabel + nog gereserveerd) / weken over, met weken over = werkdagen na de
    peildatum / 5 (op zondag hele weken). iso_jaar is standaard het jaar van de peildatum; --zet-week geeft
    het jaar van de maandag erna, zodat de zondag aan het eind van een jaar het nieuwe jaar vastzet."""
    begin, eind = jaar(iso_jaar or peildatum.isocalendar().year)
    weken = ((eind - begin).days + 1) // 7
    s = {'begin': begin, 'eind': eind, 'weken': weken, 'jaardoel': weken * UREN_PER_WEEK - VRIJ_BUDGET,
         'declarabel': declarabel(per_dag, begin, peildatum),
         'gereserveerd': vrije_dagen.nog_gereserveerd_uren(peildatum, eind),
         'weken_over': werkdagen(max(peildatum + timedelta(days=1), begin), eind) / 5}
    s['nog_te_gaan'] = s['jaardoel'] - s['declarabel']
    s['weektarget'] = (s['nog_te_gaan'] + s['gereserveerd']) / s['weken_over'] if s['weken_over'] else None
    return s


def lees_weektargets():
    """Vastgezette weektargets per maandag: {maandag: {'weektarget', 'vrije_dagen', 'declarabel_doel'}}."""
    if not os.path.exists(WEEKTARGETS):
        return {}
    with open(WEEKTARGETS, newline='') as f:
        return {date.fromisoformat(r['maandag']): {k: float(r[k]) for k in ('weektarget', 'vrije_dagen',
                                                                            'declarabel_doel')}
                for r in csv.DictReader(f)}


def zet_week(per_dag, zondag):
    """Zet het weektarget van de week na de zondag vast, met de stand t/m die zondag."""
    if zondag.weekday() != 6:
        raise SystemExit('--zet-week kan alleen met een zondag als peildatum (--tot), niet %s' % zondag)
    maandag = zondag + timedelta(days=1)
    targets = lees_weektargets()
    if maandag in targets:
        raise SystemExit('Het weektarget van de week van %s staat al vast: %s u' % (
            maandag, nl(targets[maandag]['weektarget'])))
    s = jaarstand(per_dag, zondag, maandag.isocalendar().year)
    vrij = sum(vrije_dagen.vrije_dagen(maandag, maandag + timedelta(days=6)).values())
    rij = {'maandag': maandag.isoformat(), 'weektarget': '%.2f' % s['weektarget'], 'vrije_dagen': '%g' % vrij,
           'declarabel_doel': '%.2f' % (s['weektarget'] - vrij * vrije_dagen.UREN_PER_DAG)}
    nieuw = not os.path.exists(WEEKTARGETS)
    with open(WEEKTARGETS, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rij))
        if nieuw:
            w.writeheader()
        w.writerow(rij)
    return rij


def week_van(per_dag, peildatum, targets):
    """Deze week: het vastgezette weektarget, vrije dagen, declarabel doel, gewerkt t/m de peildatum."""
    maandag = peildatum - timedelta(days=peildatum.weekday())
    w = {'maandag': maandag, 'week': maandag.isocalendar().week, 'vast': targets.get(maandag),
         'vrije_dagen': vrije_dagen.vrije_dagen(maandag, maandag + timedelta(days=6)),
         'gewerkt': declarabel(per_dag, maandag, peildatum)}
    if w['vast']:
        w['nog_te_gaan'] = w['vast']['declarabel_doel'] - w['gewerkt']
    return w


def nl(getal):
    return ('%.2f' % getal).replace('.', ',')


def dag_nl(dag):
    return '%s %s' % (vrije_dagen.WEEKDAGEN[dag.weekday()], dag.strftime('%d-%m-%Y'))


def schrijf_overzicht(tot, stand, s, w, targets):
    jaar_naam = s['begin'].isocalendar().year
    regels = [
        '---',
        'description: Urenoverzicht %s (weekgebaseerd jaar) met jaardoel, weektarget, deze week, de weken tot nu'
        ' en de vrije dagen' % jaar_naam,
        'tags: [werk, uren]',
        '---',
        '',
        '# Urenoverzicht %s' % jaar_naam,
        '',
        '> Gegenereerd door `scripts/uren.py --schrijf` (skill `/uren`) uit LogMyTime. Niet met de hand bewerken.',
        '> Peildatum **%s**. Achtergrond en logica: [[urenregistratie]].' % dag_nl(tot),
        '',
        '## Jaar',
        '',
        'Week %d (%s) t/m week %d (%s): %d weken.' % (
            s['begin'].isocalendar().week, dag_nl(s['begin']), s['eind'].isocalendar().week, dag_nl(s['eind']),
            s['weken']),
        '',
        '| Jaar | Uren |',
        '|---|---:|',
        '| Declarabel | %s |' % nl(s['declarabel']),
        '| Jaardoel (%d × %d − %d) | %s |' % (s['weken'], UREN_PER_WEEK, VRIJ_BUDGET, nl(s['jaardoel'])),
        '| Nog te gaan | %s |' % nl(s['nog_te_gaan']),
        '| Nog gereserveerd | %s |' % nl(s['gereserveerd']),
        '| Weken over | %s |' % nl(s['weken_over']),
        '| **Weektarget** | **%s** |' % (nl(s['weektarget']) if s['weektarget'] is not None else '–'),
        '',
        'Weektarget = (nog te gaan + nog gereserveerd) / weken over. Het weektarget van een week staat vast'
        ' vanaf de zondag ervoor (`--zet-week`).',
        '',
        '## Deze week',
        '',
        '| Week %d (vanaf %s) | Uren |' % (w['week'], dag_nl(w['maandag'])),
        '|---|---:|',
    ]
    if w['vast']:
        regels += ['| Weektarget | %s |' % nl(w['vast']['weektarget']),
                   '| Vrije dagen | %g |' % w['vast']['vrije_dagen'],
                   '| Declarabel doel | %s |' % nl(w['vast']['declarabel_doel']),
                   '| Gewerkt t/m %s | %s |' % (dag_nl(tot), nl(w['gewerkt'])),
                   '| **Nog te gaan** | **%s** |' % nl(w['nog_te_gaan'])]
    else:
        regels += ['| Weektarget | niet vastgezet |',
                   '| Gewerkt t/m %s | %s |' % (dag_nl(tot), nl(w['gewerkt']))]
    regels += ['',
               '## Weken tot nu',
               '',
               '| Week | Maandag | Weektarget | Vrije dagen | Declarabel doel | Gewerkt |',
               '|---:|---|---:|---:|---:|---:|']
    maandag = s['begin']
    while maandag <= tot:
        vast = targets.get(maandag)
        gewerkt = declarabel(stand['per_dag'], maandag, min(maandag + timedelta(days=6), tot))
        regels.append('| %d | %s | %s | %s | %s | %s |' % (
            maandag.isocalendar().week, maandag.strftime('%d-%m-%Y'),
            nl(vast['weektarget']) if vast else '', '%g' % vast['vrije_dagen'] if vast else '',
            nl(vast['declarabel_doel']) if vast else '', nl(gewerkt)))
        maandag += timedelta(days=7)
    regels += ['',
               'Weken zonder weektarget liggen voor het weektarget (sinds week 47). Bron:'
               ' `data/weekplanning/weektargets.csv`.',
               '',
               '## Vrije dagen',
               '',
               '| Datum | Omschrijving | Dag |',
               '|---|---|---:|']
    regels += ['| %s | %s | %s |' % (dag_nl(d), o, '1' if deel == 1 else '½')
               for d, deel, o in vrije_dagen.lees() if d > tot]
    regels += ['',
               'Bron: `data/vrije-dagen.csv`. Een vrije dag telt %s u, een halve dag de helft. Voorbije vrije dagen'
               ' zitten al in het declarabele totaal.' % nl(vrije_dagen.UREN_PER_DAG).rstrip('0')]
    with open(OVERZICHT, 'w') as f:
        f.write('\n'.join(regels) + '\n')


def main():
    vandaag = date.today()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--vanaf', type=date.fromisoformat, help='begin voor declarabel per klant')
    ap.add_argument('--tot', type=date.fromisoformat, default=vandaag, help='peildatum')
    ap.add_argument('--details', action='store_true', help='toon ook uren per TypeID en afwezigheid')
    ap.add_argument('--schrijf', action='store_true', help='schrijf de stand naar gebieden/werk/uren-overzicht.md')
    ap.add_argument('--zet-week', action='store_true',
                    help='zet het weektarget van de week na de peildatum (een zondag) vast')
    args = ap.parse_args()
    if args.schrijf and (args.vanaf or args.tot != vandaag):
        raise SystemExit('--schrijf kan alleen voor de standaardperiode (begin van het jaar t/m vandaag)')

    begin = jaar(args.tot.isocalendar().year)[0]
    vanaf = args.vanaf or begin
    maandag = args.tot - timedelta(days=args.tot.weekday())
    stand = haal_stand(min(vanaf, begin, maandag), args.tot)
    per_dag = stand['per_dag']

    if args.zet_week:
        rij = zet_week(per_dag, args.tot)
        print('Weektarget vastgezet voor de week van %s: %s u, %s vrije dag(en), declarabel doel %s u' % (
            rij['maandag'], rij['weektarget'].replace('.', ','), rij['vrije_dagen'],
            rij['declarabel_doel'].replace('.', ',')))

    s = jaarstand(per_dag, args.tot)
    targets = lees_weektargets()
    w = week_van(per_dag, args.tot, targets)

    per_klant = defaultdict(float)
    for (dag, klant), uren in stand['per_dag_klant'].items():
        if vanaf <= dag <= args.tot:
            per_klant[klant] += uren
    print('Declarabel per klant van %s t/m %s' % (vanaf, args.tot))
    for naam, uren in sorted(per_klant.items(), key=lambda kv: -kv[1]):
        print('  %-20s %9.2f u' % (naam, uren))
    print('Jaar %d: %s t/m %s, %d weken' % (s['begin'].isocalendar().year, s['begin'], s['eind'], s['weken']))
    print('  Declarabel           %9.2f u' % s['declarabel'])
    print('  Jaardoel             %9.2f u' % s['jaardoel'])
    print('  Nog te gaan          %9.2f u' % s['nog_te_gaan'])
    print('  Nog gereserveerd     %9.2f u' % s['gereserveerd'])
    print('  Weken over           %9.2f' % s['weken_over'])
    if s['weektarget'] is not None:
        print('  Weektarget           %9.2f u (als het nu werd vastgezet)' % s['weektarget'])
    print('Deze week (week %d, vanaf %s)' % (w['week'], w['maandag']))
    if w['vast']:
        print('  Weektarget           %9.2f u (vastgezet)' % w['vast']['weektarget'])
        print('  Vrije dagen          %9g' % w['vast']['vrije_dagen'])
        print('  Declarabel doel      %9.2f u' % w['vast']['declarabel_doel'])
        print('  Gewerkt t/m %s %9.2f u' % (args.tot.strftime('%d-%m'), w['gewerkt']))
        print('  Nog te gaan          %9.2f u' % w['nog_te_gaan'])
    else:
        print('  Weektarget niet vastgezet; gewerkt t/m %s %.2f u' % (args.tot.strftime('%d-%m'), w['gewerkt']))
    print('Niet declarabel      %9.2f u' % stand['niet_declarabel'])
    if args.details:
        print('Per TypeID (afwezigheid ja/nee):')
        for (type_id, afwezig), uren in sorted(stand['per_type'].items()):
            print('  TypeID %s, afwezigheid=%s: %.2f u' % (type_id, afwezig, uren))
    if args.schrijf:
        schrijf_overzicht(args.tot, stand, s, w, targets)
        print('Geschreven naar %s' % OVERZICHT)


if __name__ == '__main__':
    main()
