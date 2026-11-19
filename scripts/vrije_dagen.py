#!/usr/bin/python3
"""Vrije dagen met datum uit data/vrije-dagen.csv, voor de andere scripts.

Een regel heeft `datum`, optioneel `tot` (meer dagen) en `half` (ja: een halve dag). Elke werkdag
(ma t/m vr) van datum t/m tot telt als 1 dag = 5,6 u (28 / 5), een halve dag als 2,8 u. Vaste waarde,
los van het weektarget en de planning (zie gebieden/vault/weekplanning-plan.md).

Gebruik: vrije_dagen.py [--peildatum JJJJ-MM-DD]  toont de vrije dagen en wat er na de peildatum nog
gereserveerd is.
"""
import argparse
import csv
import os
from datetime import date, timedelta

VRIJE_DAGEN = os.path.expanduser('~/vault/data/vrije-dagen.csv')
UREN_PER_DAG = 5.6
WEEKDAGEN = ['ma', 'di', 'wo', 'do', 'vr', 'za', 'zo']


def lees(pad=VRIJE_DAGEN):
    """Per vrije werkdag (datum, deel, omschrijving), op datum gesorteerd; deel is 1 of 0,5."""
    dagen = []
    with open(pad, newline='') as f:
        for r in csv.DictReader(f):
            begin = date.fromisoformat(r['datum'])
            eind = date.fromisoformat(r['tot']) if r.get('tot') else begin
            deel = 0.5 if (r.get('half') or '').strip() else 1
            dag = begin
            while dag <= eind:
                if dag.weekday() < 5:
                    dagen.append((dag, deel, r['omschrijving']))
                dag += timedelta(days=1)
    return sorted(dagen)


def vrije_dagen(vanaf, tot):
    """Vrije werkdagen van vanaf t/m tot als {datum: 1 of 0,5}."""
    return {dag: deel for dag, deel, _ in lees() if vanaf <= dag <= tot}


def nog_gereserveerd_uren(peildatum):
    """Gereserveerde vrije uren na de peildatum (de peildatum zelf telt niet mee)."""
    return sum(deel for dag, deel, _ in lees() if dag > peildatum) * UREN_PER_DAG


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--peildatum', type=date.fromisoformat, default=date.today())
    args = ap.parse_args()
    for dag, deel, omschrijving in lees():
        print('%s %s  %-4s %s' % (WEEKDAGEN[dag.weekday()], dag.strftime('%d-%m-%Y'), 'half' if deel < 1 else '', omschrijving))
    print('Nog gereserveerd na %s: %.1f u' % (args.peildatum, nog_gereserveerd_uren(args.peildatum)))


if __name__ == '__main__':
    main()
