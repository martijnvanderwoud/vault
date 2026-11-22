"""Toegang tot de Acumulus API (SIEL), voor het maken van verkoopfacturen en het boeken van uitgaven.

Twee administraties: crimson-cricket (standaard, The Crimson Cricket) en white-sun (White Sun
Qigong, van Franca), te kiezen met --administratie <naam> voor het commando. De inloggegevens komen
uit ~/vault/.env, met prefix ACUMULUS_ resp. ACUMULUS_WHITESUN_ voor CONTRACTCODE, USERNAME,
PASSWORD en EMAILONERROR, en worden nooit getoond. Een databestand voor white-sun heeft
"administratie": "white-sun"; factuur en uitgave weigeren een bestand van de andere administratie.
Documentatie: https://www.siel.nl/acumulus/API/

Gebruik:
  acumulus.py [--administratie white-sun] <commando> ...
  acumulus.py klanten <zoekterm>   contacten zoeken (contactid, naam, actief/inactief, e-mail)
  acumulus.py sjablonen            factuursjablonen (invoicetemplateid, naam)
  acumulus.py kostenplaatsen       kostenplaatsen (costcenterid, naam)
  acumulus.py kostensoorten        kostensoorten (costheadingid, naam)
  acumulus.py rekeningen           rekeningen (de id voor accountnumber in een uitgave, en meer)
  acumulus.py openstaand           onbetaalde verkoop- en inkoopfacturen (entryid, nummer, datum,
                                   relatie, rekening, bedrag)
  acumulus.py producten            actieve standaard producten en diensten (productid, prijs
                                   excl. en incl. btw, omschrijving)
  acumulus.py relatie <naam>       een particuliere klant (debiteur) aanmaken, met de naam als
                                   contactpersoon en zonder aanhef; weigert als de naam al bestaat
  acumulus.py factuur <json> [--test]
                                   conceptfactuur aanmaken uit een bestand in data/facturen/;
                                   met --test alleen controleren (testmode), er verandert niets;
                                   met "concept": 0 in het bestand meteen definitief, en het
                                   factuurnummer en entryid komen in het bestand
  acumulus.py pdf <conceptid>      na het definitief maken: nummer en token opzoeken en de PDF
                                   opslaan in de verkoopmap op Google Drive (alleen crimson-cricket)
  acumulus.py ontvangen <contactid>
                                   de laatste ontvangen facturen (uitgaven) van een leverancier,
                                   als voorbeeld voor een nieuwe boeking
  acumulus.py uitgave <json>       een uitgave (inkoopfactuur) boeken uit een bestand in
                                   data/uitgaven/ en het entryid in dat bestand zetten
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
# Administratie en de prefix van haar inloggegevens in .env.
ADMINISTRATIES = {'crimson-cricket': 'ACUMULUS_', 'white-sun': 'ACUMULUS_WHITESUN_'}
administratie = 'crimson-cricket'


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
    prefix = ADMINISTRATIES[administratie]
    bericht = {
        'contract': {
            'contractcode': env(prefix + 'CONTRACTCODE'),
            'username': env(prefix + 'USERNAME'),
            'password': env(prefix + 'PASSWORD'),
            'emailonerror': env(prefix + 'EMAILONERROR'),
            'emailonwarning': env(prefix + 'EMAILONERROR'),
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
        status = 'actief' if str(c.get('contactstatus')) == '1' else 'inactief'
        print('%s\t%s\t%s\t%s' % (c.get('contactid'), c.get('contactname'), status, c.get('contactemail') or ''))


def sjablonen():
    antwoord = call('picklists/picklist_invoicetemplates.php')
    for t in lijst(antwoord, 'invoicetemplates', 'invoicetemplate'):
        print('%s\t%s' % (t.get('invoicetemplateid'), t.get('invoicetemplatename')))


def kostenplaatsen():
    antwoord = call('picklists/picklist_costcenters.php')
    for k in lijst(antwoord, 'costcenters', 'costcenter'):
        print('%s\t%s' % (k.get('costcenterid'), k.get('costcentername')))


def kostensoorten():
    antwoord = call('picklists/picklist_costheadings.php')
    for k in lijst(antwoord, 'costheadings', 'costheading'):
        print('%s\t%s' % (k.get('costheadingid'), k.get('costheadingname')))


def rekeningen():
    """Toont alle velden per rekening: welke daarvan accountnumber in een uitgave is, staat in acumulus.md."""
    antwoord = call('picklists/picklist_accounts.php')
    for r in lijst(antwoord, 'accounts', 'account'):
        print('\t'.join('%s=%s' % (k, v) for k, v in r.items()))


def openstaand():
    """Onbetaalde verkoop- en inkoopfacturen, om betalingen op de bank aan te koppelen."""
    for soort, pad, sleutel in (('verkoop', 'reports/report_unpaid_debtors.php', 'unpaiddebtorinvoices'),
                                ('inkoop', 'reports/report_unpaid_creditors.php', 'unpaidcreditorinvoices')):
        for e in lijst(call(pad), sleutel, 'entry'):
            omschrijving = e.get('invoicenote') or e.get('entrydescription') or ''
            print('\t'.join(str(v) for v in (soort, e.get('entryid'), e.get('number') or '-', e.get('issuedate'),
                                              e.get('contactid'), e.get('contactname'), e.get('accountnumber'),
                                              e.get('amount'), omschrijving)))


def producten():
    """Actieve standaard producten. De prijs in Acumulus is excl. btw (vier decimalen); incl. btw is berekend."""
    antwoord = call('picklists/picklist_products.php', {'producttagid': 0})
    for p in lijst(antwoord, 'products', 'product'):
        excl, btw = Decimal(p['productprice']), Decimal(p['productvatrate'])
        incl = (excl * (100 + btw) / 100).quantize(CENT, ROUND_HALF_UP)
        print('%s\t%s\t%s%%\tincl. %s\t%s' % (p['productid'], excl, btw.normalize(), incl, p['productdescription']))


def relatie(naam):
    """Maakt een particuliere klant aan zoals Franca dat doet: naam als contactpersoon, geen aanhef.

    De velden horen binnen <contact>; ernaast maakt Acumulus een lege relatie aan, ook in testmode.
    """
    bestaand = [c for c in lijst(call('contacts/contacts_list.php', {'filter': naam, 'rowcount': 50}),
                                 'contacts', 'contact') if str(c.get('contactname')).lower() == naam.lower()]
    if bestaand:
        raise SystemExit('Er is al een relatie %s: contactid %s.' % (naam, ', '.join(c['contactid'] for c in bestaand)))
    antwoord = call('contacts/contact_manage.php', {'contact': {
        'contactperson': naam, 'contactsalutation': '', 'contacttype': 1, 'contactvattypeid': 1,
        'contactcountrycode': 'NL'}})
    c = antwoord.get('contact') or {}
    if c.get('contactproc') != 'added' or c.get('contactperson') != naam:
        raise SystemExit('Acumulus gaf %s terug; kijk in Acumulus of de relatie goed is aangemaakt.' % c)
    print('Relatie %s aangemaakt, contactid %s' % (naam, c.get('contactid')))


def databestand(bestand):
    """Leest een databestand en controleert dat het bij de gekozen administratie hoort."""
    d = json.load(open(bestand))
    if d.get('administratie', 'crimson-cricket') != administratie:
        raise SystemExit('%s hoort bij administratie %s, niet bij %s.'
                         % (bestand, d.get('administratie', 'crimson-cricket'), administratie))
    return d


def factuur(bestand, testmode):
    """Maakt een (concept)factuur aan. Bedragen komen als string uit het bestand (geen floats)."""
    f = databestand(bestand)
    regels = [{'product': r['product'], 'unitprice': r['unitprice'], 'vatrate': r['vatrate'],
               'quantity': r['quantity']} for r in f['regels']]
    # Betaalstatus 1 (niet betaald) is de standaard; 2 (betaald) alleen als het bestand dat zegt.
    # Standaard een concept; "concept": 0 maakt de factuur meteen definitief.
    concept = f.get('concept', 1)
    if concept == 0 and f.get('entryid') and not testmode:
        raise SystemExit('%s is al aangemaakt als factuur %s.' % (bestand, f.get('factuurnummer')))
    invoice = {'concept': concept, 'description': f['description'], 'template': f['template'],
               'costcenter': f['costcenter'], 'paymentstatus': f.get('paymentstatus', 1), 'line': regels}
    for veld in ('issuedate', 'accountnumber'):
        if f.get(veld):
            invoice[veld] = f[veld]
    antwoord = call('invoices/invoice_add.php', {
        'customer': {'contactid': f['contactid'], 'overwriteifexists': 0, 'invoice': invoice},
    }, testmode)
    for r in regels:
        print('%s\t%s x %s\t%s%% btw' % (r['product'], r['quantity'], r['unitprice'], r['vatrate']))
    # Zoals Acumulus het op de factuur zet: btw per regel afgerond, daarna opgeteld. De btw gaat over
    # het onafgeronde bedrag, wat telt bij prijzen met vier decimalen (8.2645 wordt 8.26 + 1.74).
    exact = [Decimal(str(r['unitprice'])) * Decimal(str(r['quantity'])) for r in regels]
    subtotaal = sum(s.quantize(CENT, ROUND_HALF_UP) for s in exact)
    btw = sum((s * Decimal(r['vatrate']) / 100).quantize(CENT, ROUND_HALF_UP) for s, r in zip(exact, regels))
    print('Totaal excl. btw %s, btw %s, totaal %s' % (subtotaal, btw, subtotaal + btw))
    resultaat = antwoord.get('invoice') or {}
    if testmode:
        print('Testmode: geen fouten, er is niets aangemaakt.')
    elif concept == 0:
        f['factuurnummer'], f['entryid'] = resultaat.get('invoicenumber'), resultaat.get('entryid')
        with open(bestand, 'w') as uit:
            uit.write(json.dumps(f, indent=2, ensure_ascii=False) + '\n')
        print('Factuur %s aangemaakt, entryid %s' % (f['factuurnummer'], f['entryid']))
    else:
        print('Concept aangemaakt, conceptid %s' % resultaat.get('conceptid'))


def pdf(conceptid):
    """Zoekt bij een definitief gemaakt concept het nummer en de token op en slaat de PDF op."""
    if administratie != 'crimson-cricket':
        raise SystemExit('pdf kan alleen voor crimson-cricket: de verkoopmap is die van The Crimson Cricket.')
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


def ontvangen(contactid):
    """Toont de laatste ontvangen facturen van een leverancier, met de details per boeking.

    contact_invoices_incoming verwisselt costcenterid en costheadingid, daarom komen die uit entry_info.
    """
    antwoord = call('contacts/contact_invoices_incoming.php', {'contactid': contactid})
    facturen = sorted(lijst(antwoord, 'contact', 'invoice'), key=lambda f: str(f.get('entrydate')))
    print('entryid\tdatum\tomschrijving\tincl. btw\texcl. btw\trekening\tkostensoort\tkostenplaats\tbetaalstatus')
    for f in facturen[-6:]:
        e = call('entry/entry_info.php', {'entryid': f['entryid']})['entry']
        print('\t'.join(str(e.get(k)) for k in ('entryid', 'entrydate', 'entrydescription', 'totalvalue',
                                                 'totalvalueexclvat', 'accountnumber', 'costheadingid',
                                                 'costcenterid', 'paymentstatus')))


def uitgave(bestand):
    """Boekt een uitgave en zet het entryid in het bestand. Het bedrag komt als string uit het bestand (geen floats)."""
    u = databestand(bestand)
    if u.get('entryid'):
        # Opnieuw boeken mag alleen als ik de vorige boeking in Acumulus heb verwijderd.
        oud = call('entry/entry_info.php', {'entryid': u['entryid']})['entry']
        if not oud.get('deleted'):
            raise SystemExit('%s is al geboekt als boekstuk %s. Verwijder dat eerst in Acumulus om opnieuw '
                             'te boeken.' % (bestand, u['entryid']))
        print('Boekstuk %s is verwijderd op %s; opnieuw boeken.' % (u['entryid'], oud['deleted']))
    expense = {k: u[k] for k in ('description', 'amountinclvat', 'vatrate', 'issuedate', 'costheading',
                                 'costcenter', 'accountnumber', 'paymentstatus')}
    antwoord = call('expenses/expense_add.php', {
        'supplier': {'contactid': u['contactid'], 'overwriteifexists': 0, 'expense': expense},
    })
    # Zoals Acumulus het splitst: excl. btw afgerond op centen, btw is het verschil.
    incl = Decimal(u['amountinclvat'])
    excl = (incl * 100 / (100 + Decimal(u['vatrate']))).quantize(CENT, ROUND_HALF_UP)
    print('%s %s: %s\tincl. btw %s, excl. btw %s, btw %s (%s%%)'
          % (u['issuedate'], u['contactid'], u['description'], incl, excl, incl - excl, u['vatrate']))
    entryid = (antwoord.get('expense') or {}).get('entryid')
    if not entryid:
        raise SystemExit('Acumulus gaf geen entryid terug; kijk in Acumulus of de uitgave is geboekt.')
    u['entryid'] = int(entryid)
    with open(bestand, 'w') as uit:
        json.dump(u, uit, indent=2, ensure_ascii=False)
        uit.write('\n')
    print('Geboekt als boekstuk (entryid) %s; entryid staat in %s' % (entryid, bestand))


if __name__ == '__main__':
    args = sys.argv[1:]
    if args[:1] == ['--administratie']:
        if args[1:2] == [] or args[1] not in ADMINISTRATIES:
            raise SystemExit('Kies een administratie: %s' % ', '.join(ADMINISTRATIES))
        administratie, args = args[1], args[2:]
    if args[:1] == ['klanten'] and len(args) == 2:
        klanten(args[1])
    elif args == ['sjablonen']:
        sjablonen()
    elif args == ['kostenplaatsen']:
        kostenplaatsen()
    elif args == ['kostensoorten']:
        kostensoorten()
    elif args == ['rekeningen']:
        rekeningen()
    elif args == ['openstaand']:
        openstaand()
    elif args == ['producten']:
        producten()
    elif args[:1] == ['relatie'] and len(args) == 2:
        relatie(args[1])
    elif args[:1] == ['factuur'] and len(args) in (2, 3) and args[2:] in ([], ['--test']):
        factuur(args[1], args[2:] == ['--test'])
    elif args[:1] == ['pdf'] and len(args) == 2:
        pdf(args[1])
    elif args[:1] == ['ontvangen'] and len(args) == 2:
        ontvangen(args[1])
    elif args[:1] == ['uitgave'] and len(args) == 2:
        uitgave(args[1])
    else:
        raise SystemExit(__doc__)
