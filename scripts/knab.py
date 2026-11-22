"""Leest een transactieoverzicht (CSV) van Knab en toont de transacties, de oudste eerst.

Bij elke transactie staat de relatie uit data/betalers-white-sun.json als de naam van de betaler
in de omschrijving of als tegenrekeninghouder voorkomt. Bedragen blijven tekst uit het bestand,
met een min voor afschrijvingen; er wordt niet mee gerekend.

Gebruik:
  knab.py <csv>
"""
import csv
import json
import os
import sys
from datetime import datetime

BETALERS = os.path.expanduser('~/vault/data/betalers-white-sun.json')


def betaler(t, betalers):
    """De bekende relatie bij een transactie, of een lege string."""
    tekst = (t['Omschrijving'] + ' ' + t['Tegenrekeninghouder']).lower()
    namen = {'%s (%s)' % (b['relatie'], b['contactid']) for b in betalers if b['bank'].lower() in tekst}
    return ', '.join(sorted(namen))


def main(bestand):
    betalers = json.load(open(BETALERS))['betalers']
    with open(bestand, encoding='utf-8-sig', newline='') as f:
        transacties = list(csv.DictReader(f, delimiter=';'))
    # Het overzicht staat met de nieuwste bovenaan; binnen een dag blijft de volgorde van het bestand.
    transacties.reverse()
    transacties.sort(key=lambda t: datetime.strptime(t['Transactiedatum'], '%d-%m-%Y'))
    print('nr\tdatum\tbedrag\ttegenpartij\tbetaalwijze\tomschrijving\treferentie\tbekende relatie')
    for nr, t in enumerate(transacties, 1):
        teken = '-' if t['CreditDebet'] == 'Afschrijvingen' else '+'
        print('\t'.join([str(nr), t['Transactiedatum'], teken + t['Bedrag'], t['Tegenrekeninghouder'],
                         t['Betaalwijze'], t['Omschrijving'], t['Referentie'], betaler(t, betalers)]))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
