---
name: inkoopfactuur
description: Boekt een inkoopfactuur van een leverancier als uitgave in Acumulus en archiveert de PDF in de inkoopmap op Google Drive - haalt de PDF uit Downloads of als bijlage uit mijn privémail, slaat hem op als <Leverancier>-<factuurnummer>.pdf, neemt omschrijving, kostensoort, kostenplaats en rekening over van de vorige boeking bij die leverancier en boekt na mijn akkoord. Corrigeert ook een boeking die ik in Acumulus heb verwijderd. Gebruik deze skill zodra ik vraag om een inkoopfactuur, een ontvangen factuur of een rekening van een leverancier (Ziggo, TransIP, Google, LogMyTime, enz.) in te boeken, te archiveren of op te slaan, of een geboekte uitgave opnieuw te boeken, ook als ik het woord skill niet gebruik. Niet voor verkoopfacturen (zie hostingfactuur-flow) en niet voor het privédeel van een factuur.
allowed-tools: Bash(/usr/bin/python3 -I ~/vault/scripts/acumulus.py*), Bash(ls*), Bash(cp -n*), Bash(cmp*), Read, Write, mcp__google-prive__search_gmail_messages, mcp__google-prive__get_gmail_message_content, mcp__google-prive__get_gmail_attachment_content
---

# Inkoopfactuur boeken en archiveren

Draai vanuit `~/vault`. Achtergrond: [[acumulus]] (API, script, vaste id's, valkuilen),
[[facturen-archief]] (waar de PDF's staan).

Uitgangspunt: voer alleen uit wat hieronder als regel staat. Een situatie zonder regel leg je aan
mij voor met wat je ziet. Ga nooit om een fout van het script heen.

## Regels

- **Bedragen, datum en factuurnummer neem je letterlijk over** van de PDF. Reken niet zelf: de
  split in excl. btw en btw komt uit de uitvoer van het script.
- **Een uitgave is meteen definitief**, er is geen concept. Boek daarom pas na mijn akkoord op
  het voorstel (stap 4). Ik kijk de boeking daarna zelf na in Acumulus.
- **De hele factuur is zakelijk.** Een privédeel handelen we elders af, niet in deze skill.
- **Mail blijft staan.** Haal je de PDF uit een mail, dan lees je alleen en sla je de bijlage
  op. Nooit verwijderen, archiveren, als gelezen markeren of labels aanpassen.
- **Overschrijf niets** in het archief. Bestaat het bestand al, stop en meld het.
- **Lees `.env` niet.** Het script leest de inloggegevens zelf.

## 1. PDF vinden

- **Downloads**: `ls ~/Downloads`. Is niet duidelijk welk bestand ik bedoel, vraag het.
- **Mail**: alleen mijn privémail (martijnvanderwoud@gmail.com) via `google-prive`: zoek de mail
  met `search_gmail_messages`, haal met `get_gmail_message_content` de bijlagen op en sla de PDF
  op met `get_gmail_attachment_content` (geeft een lokaal pad). Zit er geen PDF bij (Ziggo stuurt
  alleen een bericht; daar log ik zelf in), zeg dan dat ik hem moet downloaden. Bijlagen uit mijn
  zakelijke mail kun je nog niet opslaan: vraag me dan de PDF naar Downloads te halen.

## 2. Lezen en archiveren

Lees de PDF met de Read-tool en noteer: leverancier, factuurnummer, factuurdatum, bedrag incl.
btw, btw-tarief, periode en hoe er betaald wordt (incasso, creditcard, overmaken).

Leg het voor en stop als: er meer dan één btw-tarief op staat, de btw verlegd is of het een
buitenlandse leverancier zonder Nederlandse btw is, of het geen factuur is (een offerte,
herinnering of creditnota).

Archiveer naar `~/Mijn Drive/crimsoncricket-documents/inkoop/<jaar van factuurdatum>/<Leverancier>-<factuurnummer>.pdf`.
Gebruik voor `<Leverancier>` de spelling die al in de map staat (`ls` op die map, bijv.
`TransIP`, `Google-Cloud-EMEA-Limited`); is de leverancier nieuw, stel een naam voor.

```bash
cp -n <bron> "<doel>" && cmp <bron> "<doel>"
```

Komt de PDF uit Downloads, dan mag het origineel na een geslaagde `cmp` weg: `rm` op precies dat
bestand. Een bijlage uit mail laat je staan waar `get_gmail_attachment_content` hem neerzette.

## 3. Vorige boeking als voorbeeld

```bash
/usr/bin/python3 -I ~/vault/scripts/acumulus.py klanten "<leverancier>"
```

Neem de relatie die als `actief` staat; er kunnen inactieve relaties met dezelfde naam zijn.
Dan:

```bash
/usr/bin/python3 -I ~/vault/scripts/acumulus.py ontvangen <contactid>
```

Controleer dat deze factuur er nog niet bij staat (zelfde datum en bedrag), en dat
`data/uitgaven/<Leverancier>-<factuurnummer>.json` nog niet bestaat. Bestaat het wel, ga dan naar
`Opnieuw boeken`.

Leg het voor en stop als: er geen eerdere boeking is (nieuwe leverancier), de vorige boekingen
onderling verschillen in kostensoort, kostenplaats of rekening, of het bedrag sterk afwijkt van
de vorige keer.

## 4. Voorstel: stoppunt

Schrijf `data/uitgaven/<Leverancier>-<factuurnummer>.json`, met omschrijving, kostensoort,
kostenplaats en rekening van de vorige boeking, en bedrag, tarief en datum van deze factuur:

```json
{
  "contactid": 10445127,
  "issuedate": "2026-11-22",
  "description": "Zakelijk Internet en TV",
  "amountinclvat": "72.70",
  "vatrate": 21,
  "costheading": 6,
  "costcenter": 9410,
  "accountnumber": 13039,
  "paymentstatus": 1,
  "bron": "Ziggo-320246829314.pdf"
}
```

- `issuedate` is de factuurdatum, ook als die in de toekomst ligt.
- `amountinclvat` als string met een punt.
- `paymentstatus` 1 (open) bij incasso of overmaken: de bankimport zet hem later op betaald.
  2 (betaald) alleen als de factuur al betaald is (creditcard, of "betaald" op de factuur), en
  zoals de vorige boeking.

Laat me een tabel zien met de velden, de namen van kostensoort, kostenplaats en rekening (uit
[[acumulus]]), en wat er afwijkt van de vorige boeking. Wacht op mijn akkoord.

## 5. Boeken

```bash
/usr/bin/python3 -I ~/vault/scripts/acumulus.py uitgave data/uitgaven/<Leverancier>-<factuurnummer>.json
```

Het script zet het `entryid` zelf in het databestand. Controleer met `ontvangen <contactid>` dat
de nieuwe boeking naast de vorige staat met dezelfde velden.

## Opnieuw boeken

Wil ik een boeking corrigeren, dan verwijder ik hem zelf in Acumulus. Pas daarna het databestand
aan met de correctie, laat me het voorstel zien (stap 4) en boek opnieuw (stap 5). Het script
boekt alleen opnieuw als het oude boekstuk echt verwijderd is; zegt het dat het nog bestaat, meld
dat dan en stop. Het archief laat je ongemoeid, tenzij de correctie het factuurnummer betreft.

## Antwoord

Kort, in het Nederlands: het boekstuknummer (entryid), datum, omschrijving, bedrag incl. btw en
de split uit de uitvoer, het pad van de PDF in het archief, en of het origineel uit Downloads is
weggehaald.
