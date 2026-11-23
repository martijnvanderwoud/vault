"""Leest een bestellingenexport (CSV) uit MemBirds en zet er factuurbestanden voor Acumulus van klaar.

De export maak je in MemBirds met Shop > Bestellingen > Export, met "Elk product op nieuwe regel"
aan. Het script bundelt de regels per bestelnummer tot één factuur per bestelling, zoekt de relatie
op lidnummer en het Acumulus-product op productnaam (data/membirds-white-sun.json), en controleert
de bedragen tegen de export. Er wordt niets in Acumulus aangeroepen: het aanmaken doet
acumulus.py --administratie white-sun factuur <bestand>.

Een bestelling met korting, terugboeking, btw verlegd, bedrijfsnaam, een andere status dan
completed, een onbekend lid of een onbekend product wordt niet klaargezet: die leg je voor.
De factuurdatum is altijd vandaag (factuurnummers blijven zo op volgorde).

Gebruik:
  membirds.py <csv>              toont het voorstel per bestelling, schrijft niets
  membirds.py <csv> --schrijf    schrijft per bestelling een bestand in data/facturen/white-sun/
"""
import csv
import json
import os
import re
import sys
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

ZOEK = os.path.expanduser('~/vault/data/membirds-white-sun.json')
MAP = os.path.expanduser('~/vault/data/facturen/white-sun')
CENT = Decimal('0.01')


def decimaal(tekst):
    return Decimal(tekst) if tekst not in ('', None) else Decimal(0)


def lees(bestand):
    """De bestellingen uit de export: bestelnummer -> {kop, regels}, in de volgorde van het bestand."""
    with open(bestand, encoding='utf-8-sig', newline='') as f:
        rijen = list(csv.DictReader(f))
    if rijen and 'Product Naam' not in rijen[0]:
        raise SystemExit('Geen productkolommen in %s: maak de export opnieuw met "Elk product op nieuwe regel" aan.' % bestand)
    bestellingen = {}
    for r in rijen:
        b = bestellingen.setdefault(r['Bestelnummer'], {'kop': r, 'regels': []})
        b['regels'].append(r)
    return bestellingen


def beoordeel(nr, b, kaart):
    """Geeft (factuurbestand of None, lijst met opmerkingen) voor een bestelling."""
    kop = b['kop']
    opm = []
    if kop['Status'] != 'completed':
        opm.append('status %s' % kop['Status'])
    for veld in ('Totaal Korting incl.', 'Totaal Terugboeking prijs incl.'):
        if decimaal(kop[veld]) != 0:
            opm.append('%s is %s' % (veld, kop[veld]))
    if kop['BTW verlegd'] not in ('', '0'):
        opm.append('btw verlegd')
    if kop['Bedrijfsnaam']:
        opm.append('bedrijfsnaam %s' % kop['Bedrijfsnaam'])
    if kop['Land'] != 'NL':
        opm.append('land %s' % kop['Land'])
    lid = kaart['leden'].get(kop['Lid nummer'])
    if not lid:
        opm.append('onbekend lid %s (%s %s, %s): zoek de relatie met acumulus.py klanten' %
                   (kop['Lid nummer'], kop['Voornaam'], kop['Achternaam'], kop['Email']))
    regels, totaal_incl = [], Decimal(0)
    for r in b['regels']:
        p = kaart['producten'].get(r['Product Naam'])
        if not p:
            opm.append('onbekend product "%s"' % r['Product Naam'])
            continue
        if decimaal(r['Product Korting incl.']) != 0 or decimaal(r['Product Terugboeking prijs incl.']) != 0:
            opm.append('korting of terugboeking op een productregel')
        aantal = int(r['Product Aantal'])
        regels.append({'product': p['acumulus'], 'unitprice': p['unitprice'], 'vatrate': int(p['vatrate']),
                       'quantity': aantal})
        # Controle: de prijs in de export moet gelijk zijn aan de prijs van het Acumulus-product.
        excl = Decimal(p['unitprice']) * aantal
        incl = (excl + (excl * int(p['vatrate']) / 100).quantize(CENT, ROUND_HALF_UP)).quantize(CENT, ROUND_HALF_UP)
        totaal_incl += incl
        if incl != decimaal(r['Product Prijs incl.']):
            opm.append('prijs "%s" in export %s, in Acumulus %s' % (r['Product Naam'], r['Product Prijs incl.'], incl))
    if regels and totaal_incl != decimaal(kop['Totaal Prijs incl.']):
        opm.append('totaal in export %s, berekend %s' % (kop['Totaal Prijs incl.'], totaal_incl))
    if opm or not regels:
        return None, opm
    d, m, j = kop['Datum'].split('/')
    bestand = {
        'administratie': 'white-sun', 'contactid': lid['contactid'], 'template': kaart['factuur']['template'],
        'costcenter': kaart['factuur']['costcenter'], 'accountnumber': kaart['factuur']['accountnumber'],
        'description': 'Membirds bestelling %s' % nr, 'issuedate': date.today().isoformat(), 'concept': 0,
        'bron': {'systeem': 'MemBirds', 'bestelnummer': nr, 'besteldatum': '%s-%s-%s' % (j, m, d),
                 'order_id': kop['Id'], 'lid': kop['Lid nummer'], 'klant': '%s %s' % (kop['Voornaam'], kop['Achternaam'])},
        'regels': regels}
    return bestand, opm


def bestandsnaam(nr, kop):
    achternaam = re.sub(r'[^a-z0-9]+', '-', kop['Achternaam'].lower()).strip('-')
    return os.path.join(MAP, '%s-%s-%s.json' % (date.today().isoformat(), achternaam, nr[-3:]))


def main(csvbestand, schrijf):
    kaart = json.load(open(ZOEK))
    bestellingen = lees(csvbestand)
    print('nr\tbestelnummer\tbesteld\tklant\tlid\trelatie\tproduct\taantal\texcl\tbtw\tincl\topmerking')
    te_schrijven = []
    for i, (nr, b) in enumerate(bestellingen.items(), 1):
        bestand, opm = beoordeel(nr, b, kaart)
        kop = b['kop']
        lid = kaart['leden'].get(kop['Lid nummer'])
        relatie = '%s (%s)' % (lid['relatie'], lid['contactid']) if lid else '?'
        for r in b['regels']:
            print('\t'.join([str(i), nr, kop['Datum'], '%s %s' % (kop['Voornaam'], kop['Achternaam']), kop['Lid nummer'],
                             relatie, r['Product Naam'], r['Product Aantal'], r['Product Prijs excl.'],
                             r['Product Totaal BTW'], r['Product Prijs incl.'],
                             '; '.join(opm) if opm else 'klaar']))
        if bestand:
            te_schrijven.append((bestandsnaam(nr, kop), bestand))
    print()
    print('%d bestellingen, %d klaar om te schrijven, %d voor te leggen' %
          (len(bestellingen), len(te_schrijven), len(bestellingen) - len(te_schrijven)))
    if not schrijf:
        return
    for pad, inhoud in te_schrijven:
        if os.path.exists(pad):
            raise SystemExit('Bestand bestaat al: %s' % pad)
    for pad, inhoud in te_schrijven:
        with open(pad, 'w') as f:
            json.dump(inhoud, f, indent=2, ensure_ascii=False)
            f.write('\n')
        print('geschreven: %s' % os.path.relpath(pad, os.path.expanduser('~/vault')))


if __name__ == '__main__':
    args = sys.argv[1:]
    schrijf = '--schrijf' in args
    args = [a for a in args if a != '--schrijf']
    if len(args) != 1:
        raise SystemExit(__doc__)
    main(args[0], schrijf)
