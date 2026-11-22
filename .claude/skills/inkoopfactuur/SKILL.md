---
name: inkoopfactuur
description: Boekt een inkoopfactuur als uitgave in Acumulus en archiveert de PDF in de inkoopmap op Google Drive, voor The Crimson Cricket (mijn administratie) of voor White Sun Qigong (de administratie van Franca) - haalt de PDF uit Downloads, als bijlage uit mijn privémail of uit mijn eigen verkoopmap, slaat hem op als <Leverancier>-<factuurnummer>.pdf, neemt omschrijving, kostensoort, kostenplaats en rekening over van de vorige boeking bij die leverancier en boekt na mijn akkoord. Corrigeert ook een boeking die ik in Acumulus heb verwijderd. Gebruik deze skill zodra ik vraag om een inkoopfactuur, een ontvangen factuur of een rekening van een leverancier (Ziggo, TransIP, Google, LogMyTime, enz.) in te boeken, te archiveren of op te slaan, om een factuur die Franca me mailt in te boeken bij White Sun, om een factuur van mij aan White Sun in Franca's Acumulus te boeken, of een geboekte uitgave opnieuw te boeken, ook als ik het woord skill niet gebruik. Niet voor verkoopfacturen (zie hostingfactuur-flow) en niet voor het privédeel van een factuur.
allowed-tools: Bash(/usr/bin/python3 -I ~/vault/scripts/acumulus.py*), Bash(ls*), Bash(cp -n*), Bash(cmp*), Read, Write, mcp__google-prive__search_gmail_messages, mcp__google-prive__get_gmail_message_content, mcp__google-prive__get_gmail_attachment_content
---

# Inkoopfactuur boeken en archiveren

Draai vanuit `~/vault`. Achtergrond: [[acumulus]] (API, script, administraties, vaste id's,
valkuilen), [[facturen-archief]] (waar de PDF's staan).

Uitgangspunt: voer alleen uit wat hieronder als regel staat. Een situatie zonder regel leg je aan
mij voor met wat je ziet. Ga nooit om een fout van het script heen.

## Administratie

Bepaal eerst voor wie de factuur is. Twijfel je, vraag het.

| | The Crimson Cricket | White Sun Qigong |
|---|---|---|
| Wanneer | mijn eigen inkoopfacturen (standaard) | facturen die Franca me mailt, en mijn facturen aan White Sun |
| Script | `acumulus.py <commando>` | `acumulus.py --administratie white-sun <commando>` |
| Archief | `~/Mijn Drive/crimsoncricket-documents/inkoop/<jaar>/` | `~/Mijn Drive/studiodesta/05-ALGEMEEN/03-administratie/inkoop/<jaar>/` |
| Databestand | `data/uitgaven/<naam>.json` | `data/uitgaven/white-sun/<naam>.json`, met `"administratie": "white-sun"` |

`<jaar>` is het jaar van de factuurdatum, `<naam>` is `<Leverancier>-<factuurnummer>`, zoals de PDF
in het archief. Gebruik in elke stap hieronder het script, het archief en de map van deze
administratie.

## Regels

- **Bedragen, datum en factuurnummer neem je letterlijk over** van de PDF. Reken niet zelf: de
  split in excl. btw en btw komt uit de uitvoer van het script.
- **Een uitgave is meteen definitief**, er is geen concept. Boek daarom pas na mijn akkoord op
  het voorstel (stap 4). Ik kijk de boeking daarna zelf na in Acumulus.
- **De hele factuur is zakelijk.** Een privédeel handelen we elders af, niet in deze skill.
- **Mail blijft staan.** Haal je de PDF uit een mail, dan lees je alleen en sla je de bijlage
  op. Nooit verwijderen, archiveren, als gelezen markeren of labels aanpassen.
- **Overschrijf niets** in het archief. Bestaat het bestand al, stop en meld het.
- **Lees `.env` niet.** Het script leest de inloggegevens zelf. Meldt het dat de sleutels van
  White Sun ontbreken, zeg dan dat ik `ACUMULUS_WHITESUN_*` in `.env` moet zetten, en stop.

## 1. PDF vinden

- **Downloads**: `ls ~/Downloads`. Is niet duidelijk welk bestand ik bedoel, vraag het.
- **Mail**: alleen mijn privémail (martijnvanderwoud@gmail.com) via `google-prive`: zoek de mail
  met `search_gmail_messages` (een factuur voor White Sun meestal van Franca), haal met
  `get_gmail_message_content` de bijlagen op en sla de PDF op met `get_gmail_attachment_content`
  (geeft een lokaal pad). Zit er geen PDF bij (Ziggo stuurt alleen een bericht; daar log ik zelf
  in), zeg dan dat ik hem moet downloaden. Bijlagen uit mijn zakelijke mail kun je nog niet
  opslaan: vraag me dan de PDF naar Downloads te halen.
- **Mijn eigen factuur aan White Sun**: `~/Mijn Drive/crimsoncricket-documents/verkoop/<jaar>/Factuur_<nummer>.pdf`.
  Leverancier is `The-Crimson-Cricket`, dus de naam wordt `The-Crimson-Cricket-<nummer>`.

## 2. Lezen en archiveren

Lees de PDF met de Read-tool en noteer: leverancier, factuurnummer, factuurdatum, bedrag incl.
btw, btw-tarief, periode en hoe er betaald wordt (incasso, creditcard, overmaken).

Leg het voor en stop als: er meer dan één btw-tarief op staat, de btw verlegd is of het een
buitenlandse leverancier zonder Nederlandse btw is, of het geen factuur is (een offerte,
herinnering of creditnota).

Archiveer naar `<archief>/<jaar>/<Leverancier>-<factuurnummer>.pdf`. Gebruik voor `<Leverancier>`
de spelling die al in de map staat (`ls` op die map, bijv. `TransIP`,
`Google-Cloud-EMEA-Limited`); is de leverancier nieuw, stel een naam voor. Staat er geen
factuurnummer op, gebruik dan de factuurdatum (`Tempofix-2026-01-14`), zoals in het archief van
White Sun.

```bash
cp -n <bron> "<doel>" && cmp <bron> "<doel>"
```

Komt de PDF uit Downloads, dan mag het origineel na een geslaagde `cmp` weg: `rm` op precies dat
bestand. Een bijlage uit mail laat je staan waar `get_gmail_attachment_content` hem neerzette, en
een factuur uit mijn verkoopmap blijft daar natuurlijk ook staan.

## 3. Vorige boeking als voorbeeld

```bash
/usr/bin/python3 -I ~/vault/scripts/acumulus.py [--administratie white-sun] klanten "<leverancier>"
```

Neem de relatie die als `actief` staat; er kunnen inactieve relaties met dezelfde naam zijn.
Dan:

```bash
/usr/bin/python3 -I ~/vault/scripts/acumulus.py [--administratie white-sun] ontvangen <contactid>
```

Controleer dat deze factuur er nog niet bij staat (zelfde datum en bedrag), en dat het
databestand nog niet bestaat. Bestaat het wel, ga dan naar `Opnieuw boeken`.

Leg het voor en stop als: er geen eerdere boeking is (nieuwe leverancier), de vorige boekingen
onderling verschillen in kostensoort, kostenplaats of rekening, of het bedrag sterk afwijkt van
de vorige keer.

## 4. Voorstel: stoppunt

Schrijf het databestand, met omschrijving, kostensoort, kostenplaats en rekening van de vorige
boeking, en bedrag, tarief en datum van deze factuur:

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

- Voor White Sun komt er `"administratie": "white-sun"` bij, bovenaan.
- `issuedate` is de factuurdatum, ook als die in de toekomst ligt.
- `amountinclvat` als string met een punt.
- `accountnumber` is de `accountid` van de rekening, niet het rekeningnummer.
- `paymentstatus` 1 (open) bij incasso of overmaken: de bankimport zet hem later op betaald.
  2 (betaald) alleen als de factuur al betaald is (creditcard, of "betaald" op de factuur), en
  zoals de vorige boeking.

Laat me een tabel zien met de administratie, de velden, de namen van kostensoort, kostenplaats en
rekening en wat er afwijkt van de vorige boeking. De namen staan in [[acumulus]]; staan ze er
niet (bij White Sun), zoek ze op met `kostensoorten`, `kostenplaatsen` en `rekeningen` en zet ze
in de tabel `Vaste id's White Sun Qigong` daar. Wacht op mijn akkoord.

## 5. Boeken

```bash
/usr/bin/python3 -I ~/vault/scripts/acumulus.py [--administratie white-sun] uitgave <databestand>
```

Het script zet het `entryid` zelf in het databestand. Controleer met `ontvangen <contactid>` dat
de nieuwe boeking naast de vorige staat met dezelfde velden.

## Opnieuw boeken

Wil ik een boeking corrigeren, dan verwijder ik hem zelf in Acumulus. Pas daarna het databestand
aan met de correctie, laat me het voorstel zien (stap 4) en boek opnieuw (stap 5). Het script
boekt alleen opnieuw als het oude boekstuk echt verwijderd is; zegt het dat het nog bestaat, meld
dat dan en stop. Het archief laat je ongemoeid, tenzij de correctie het factuurnummer betreft.

## Antwoord

Kort, in het Nederlands: de administratie, het boekstuknummer (entryid), datum, omschrijving,
bedrag incl. btw en de split uit de uitvoer, het pad van de PDF in het archief, en of het
origineel uit Downloads is weggehaald.
