"""Toegang tot de Acumulus API (SIEL), voor het maken van verkoopfacturen.

De inloggegevens komen uit ACUMULUS_CONTRACTCODE, ACUMULUS_USERNAME, ACUMULUS_PASSWORD en
ACUMULUS_EMAILONERROR in ~/vault/.env en worden nooit getoond.
Documentatie: https://www.siel.nl/acumulus/API/

Gebruik:
  acumulus.py klanten <zoekterm>   contacten zoeken (contactid, naam, e-mail)
  acumulus.py sjablonen            factuursjablonen (invoicetemplateid, naam)
  acumulus.py kostenplaatsen       kostenplaatsen (costcenterid, naam)
  acumulus.py factuur <json> [--test]
                                   conceptfactuur aanmaken uit een bestand in data/facturen/;
                                   met --test alleen controleren (testmode), er verandert niets
  acumulus.py pdf <conceptid>      na het definitief maken: nummer en token opzoeken en de PDF
                                   opslaan in de verkoopmap op Google Drive
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from decimal import ROUND_HALF_UP, Decimal
from xml.sax.saxutils import escape

BASE = 'https://api.sielsystems.nl/acumulus/stable/'
CENT = Decimal('0.01')
VERKOOP = os.path.expanduser('~/Mijn Drive/crimsoncricket-documents/verkoop')


def env(naam):
    path = os.path.expanduser('~/vault/.env')
    for line in reversed(open(path).read().splitlines()):
        if line.startswith(naam + '='):
            waarde = line.split('=', 1)[1].strip()
            if waarde:
                return waarde
    raise SystemExit(naam + ' ontbreekt of is leeg in ' + path)


def xml(velden):
    """Zet een dict (met geneste dicts en lijsten) om naar XML-elementen, met escaping."""
    delen = []
    for tag, waarde in velden.items():
        for w in (waarde if isinstance(waarde, list) else [waarde]):
            inhoud = xml(w) if isinstance(w, dict) else escape(str(w))
            delen.append('<%s>%s</%s>' % (tag, inhoud, tag))
    return ''.join(delen)


def call(pad, velden=None, testmode=False):
    """Roept een API-pad aan (bijv. 'contacts/contacts_list.php') en geeft het response-deel terug."""
    bericht = {
        'contract': {
            'contractcode': env('ACUMULUS_CONTRACTCODE'),
            'username': env('ACUMULUS_USERNAME'),
            'password': env('ACUMULUS_PASSWORD'),
            'emailonerror': env('ACUMULUS_EMAILONERROR'),
            'emailonwarning': env('ACUMULUS_EMAILONERROR'),
        },
        'format': 'json',
        'testmode': 1 if testmode else 0,
        'lang': 'nl',
    }
    bericht.update(velden or {})
    body = urllib.parse.urlencode({'xmlstring': '<?xml version="1.0" encoding="UTF-8"?><myxml>%s</myxml>' % xml(bericht)})
    try:
        antwoord = json.load(urllib.request.urlopen(BASE + pad, body.encode(), timeout=30))
    except urllib.error.HTTPError as e:
        raise SystemExit('Acumulus API gaf HTTP %s %s voor %s' % (e.code, e.reason, pad))
    meldingen(antwoord, pad)
    return antwoord


def meldingen(antwoord, pad):
    """Toont fouten en waarschuwingen; stopt bij fouten. Status: 0 ok, 1 fouten, 2 waarschuwingen, 3 exceptie."""
    for soort in ('errors', 'warnings'):
        blok = antwoord.get(soort) or {}
        for lijst in blok.values():
            if isinstance(lijst, dict):
                lijst = next(iter(lijst.values()), [])
            for m in (lijst if isinstance(lijst, list) else []):
                print('%s %s: %s' % (soort[:-1].upper(), m.get('code', ''), m.get('message', '')), file=sys.stderr)
    if str(antwoord.get('status')) in ('1', '3'):
        raise SystemExit('Acumulus API gaf status %s voor %s' % (antwoord.get('status'), pad))


def lijst(antwoord, *sleutels):
    """Haalt een lijst uit het antwoord; Acumulus geeft bij één element een dict in plaats van een lijst."""
    for s in sleutels:
        antwoord = (antwoord or {}).get(s)
    if antwoord is None:
        return []
    return antwoord if isinstance(antwoord, list) else [antwoord]


def klanten(zoekterm):
    antwoord = call('contacts/contacts_list.php', {'filter': zoekterm, 'rowcount': 50})
    for c in lijst(antwoord, 'contacts', 'contact'):
        print('%s\t%s\t%s' % (c.get('contactid'), c.get('contactname'), c.get('contactemail') or ''))


def sjablonen():
    antwoord = call('picklists/picklist_invoicetemplates.php')
    for t in lijst(antwoord, 'invoicetemplates', 'invoicetemplate'):
        print('%s\t%s' % (t.get('invoicetemplateid'), t.get('invoicetemplatename')))


def kostenplaatsen():
    antwoord = call('picklists/picklist_costcenters.php')
    for k in lijst(antwoord, 'costcenters', 'costcenter'):
        print('%s\t%s' % (k.get('costcenterid'), k.get('costcentername')))


def factuur(bestand, testmode):
    """Maakt een conceptfactuur aan. Bedragen komen als string uit het bestand (geen floats)."""
    f = json.load(open(bestand))
    regels = [{'product': r['product'], 'unitprice': r['unitprice'], 'vatrate': r['vatrate'],
               'quantity': r['quantity']} for r in f['regels']]
    invoice = {'concept': 1, 'description': f['description'], 'template': f['template'],
               'costcenter': f['costcenter'], 'line': regels}
    if f.get('issuedate'):
        invoice['issuedate'] = f['issuedate']
    antwoord = call('invoices/invoice_add.php', {
        'customer': {'contactid': f['contactid'], 'overwriteifexists': 0, 'invoice': invoice},
    }, testmode)
    for r in regels:
        print('%s\t%s x %s\t%s%% btw' % (r['product'], r['quantity'], r['unitprice'], r['vatrate']))
    # Zoals Acumulus het op de factuur zet: btw per regel afgerond, daarna opgeteld.
    subtotalen = [(Decimal(str(r['unitprice'])) * Decimal(str(r['quantity']))).quantize(CENT, ROUND_HALF_UP)
                  for r in regels]
    btw = sum((s * Decimal(r['vatrate']) / 100).quantize(CENT, ROUND_HALF_UP) for s, r in zip(subtotalen, regels))
    print('Totaal excl. btw %s, btw %s, totaal %s' % (sum(subtotalen), btw, sum(subtotalen) + btw))
    if testmode:
        print('Testmode: geen fouten, er is niets aangemaakt.')
    else:
        print('Concept aangemaakt, conceptid %s' % (antwoord.get('invoice') or {}).get('conceptid'))


def pdf(conceptid):
    """Zoekt bij een definitief gemaakt concept het nummer en de token op en slaat de PDF op."""
    concept = call('invoices/invoice_concept_info.php', {'conceptid': conceptid})
    entryids = lijst(concept, 'concept', 'entryid')
    if not entryids:
        raise SystemExit('Concept %s is nog niet definitief gemaakt.' % conceptid)
    if len(entryids) > 1:
        raise SystemExit('Concept %s is meerdere keren definitief gemaakt (boekstukken %s); kies zelf.'
                         % (conceptid, ', '.join(map(str, entryids))))
    entry = call('entry/entry_info.php', {'entryid': entryids[0]})['entry']
    if entry.get('deleted'):
        raise SystemExit('Boekstuk %s is verwijderd op %s.' % (entryids[0], entry['deleted']))
    nummer, token = str(entry['invoicenumber']), entry['token']
    url = BASE + 'invoices/invoice_get_pdf.php?' + urllib.parse.urlencode({'token': token})
    inhoud = urllib.request.urlopen(url, timeout=30).read()
    if not inhoud.startswith(b'%PDF'):
        raise SystemExit('Acumulus gaf geen PDF terug voor factuur %s.' % nummer)
    pad = os.path.join(VERKOOP, nummer[:4], 'Factuur_%s.pdf' % nummer)
    if os.path.exists(pad):
        raise SystemExit('%s bestaat al; niet overschreven.' % pad)
    with open(pad, 'wb') as uit:
        uit.write(inhoud)
    print('Factuur %s (boekstuk %s, %s incl. btw) opgeslagen in %s'
          % (nummer, entryids[0], entry.get('totalvalue'), pad))


if __name__ == '__main__':
    args = sys.argv[1:]
    if args[:1] == ['klanten'] and len(args) == 2:
        klanten(args[1])
    elif args == ['sjablonen']:
        sjablonen()
    elif args == ['kostenplaatsen']:
        kostenplaatsen()
    elif args[:1] == ['factuur'] and len(args) in (2, 3) and args[2:] in ([], ['--test']):
        factuur(args[1], args[2:] == ['--test'])
    elif args[:1] == ['pdf'] and len(args) == 2:
        pdf(args[1])
    else:
        raise SystemExit(__doc__)
