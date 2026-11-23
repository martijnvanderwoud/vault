---
name: membirds-facturen
description: Zet facturen klaar in Franca's Acumulus (White Sun Qigong) voor bestellingen uit MemBirds - leest de bestellingenexport (CSV) uit Downloads, legt per bestelling relatie, product en bedrag aan me voor, maakt na mijn akkoord per bestelling één definitieve factuur op rekening Mollie (niet betaald, factuurdatum vandaag, beschrijving "Membirds bestelling <bestelnummer>") en houdt het logboek bij. Gebruik deze skill zodra ik vraag om de MemBirds-bestellingen, Membirds-facturen of de bestellingen van White Sun te verwerken of te factureren, of na het downloaden van een bestellingenexport, ook als ik het woord skill niet gebruik. Niet voor de bankmutaties van Knab (dat is betalingen-white-sun), niet voor een creditfactuur na een terugbetaling (leg die aan mij voor) en niet voor de facturen die MemBirds zelf maakt.
allowed-tools: Bash(/usr/bin/python3 -I ~/vault/scripts/membirds.py*), Bash(/usr/bin/python3 -I ~/vault/scripts/acumulus.py*), Bash(ls*), Read, Write, Edit
---

# Facturen voor MemBirds-bestellingen

Draai vanuit `~/vault`. Achtergrond en logboek: [[membirds]]. API, script en valkuilen van
Acumulus: [[acumulus]]. Alle Acumulus-commando's hier zijn voor Franca's administratie:
`/usr/bin/python3 -I ~/vault/scripts/acumulus.py --administratie white-sun <commando>`
(hieronder afgekort tot `acumulus.py <commando>`). Gebruik `/usr/bin/python3`: de pyenv-Python heeft
geen SSL.

Uitgangspunt: voer alleen uit wat hieronder als regel staat. Een bestelling die bij geen regel
past, leg je aan mij voor met wat je ziet. Ga nooit om een fout van het script heen.

## Hoe het werkt

Voor elke MemBirds-bestelling maak ik in Acumulus één eigen factuur. De facturen die MemBirds
zelf maakt, gebruik ik niet. Ik exporteer de bestellingen in MemBirds (Shop > Bestellingen >
Export, CSV, met "Elk product op nieuwe regel" aan) en jij werkt vanuit dat bestand. De MemBirds
MCP-koppeling gebruik je hier niet: de export is de bron.

## Regels

- **Alle bestellingen krijgen een factuur**, ook die nog niet betaald zijn. De meeste zijn
  automatische incasso's die pas later via de Mollie-uitbetaling betaald worden. De factuur
  staat dus altijd op **niet betaald**; de match in Acumulus zet hem op betaald.
- **Factuurdatum is altijd vandaag**, niet de besteldatum, zodat de factuurnummers in Acumulus op
  volgorde blijven. Het script doet dit.
- **Beschrijving** is "Membirds bestelling <bestelnummer>", bijvoorbeeld "Membirds bestelling
  MB2026-00000150". Het bestelnummer, niet het factuurnummer van MemBirds. Het script doet dit.
- **Rekening Mollie (227282)**, sjabloon White Sun Qigong (133249), kostenplaats Algemeen (10213).
- **Facturen zijn meteen definitief** en kunnen niet terug via de API. Maak ze pas aan na mijn
  akkoord op een tabel (stap 3), en altijd eerst met `--test`.
- **Reken niet zelf.** Bedragen komen uit de export en uit de uitvoer van `acumulus.py factuur`.
- **Raak in Acumulus niets anders aan.** Geen betaalstatus zetten, niets verwijderen, geen
  bestaande relaties wijzigen. Matches in Acumulus accepteer ik zelf.
- **Lees `.env` niet.** Het script leest de inloggegevens zelf.

## 1. Export inlezen

`ls ~/Downloads`. Het bestand heet `bestellingen_<van>_<tot>.csv` (soms met `.csv.csv` of `(1)`
erachter). Staat er meer dan één, vraag welke. Dan:

```bash
/usr/bin/python3 -I ~/vault/scripts/membirds.py "<csv>"
acumulus.py openstaand
```

Het script toont per bestelling de relatie, het Acumulus-product en de bedragen, en zegt bij elke
bestelling `klaar` of waarom niet. Het controleert de prijs in de export tegen de prijs van het
Acumulus-product. Het schrijft niets zonder `--schrijf`.

Controleer dat een bestelling nog geen factuur heeft. De beschrijving van de openstaande
verkoopfacturen op Mollie noemt het bestelnummer; een bestelling die daar al staat, sla je over
en meld je. Een factuur die al betaald is, staat niet meer in `openstaand`: zoek het bestelnummer
dan ook in het logboek van [[membirds]] en in `data/facturen/white-sun/`, en vraag het me bij
twijfel.

## 2. Wat het script niet klaarzet

Het script zet een bestelling **niet** klaar bij: korting, terugboeking, btw verlegd, bedrijfsnaam,
een andere status dan `completed`, een ander land dan NL, een onbekend lid of een onbekend product,
of als de prijs in de export afwijkt van Acumulus. Leg die aan mij voor met wat je ziet.

- **Onbekend lid:** zoek met `acumulus.py klanten "<achternaam>"` de actieve relatie en stel die
  voor. Zeg erbij als het e-mailadres in Acumulus ontbreekt of afwijkt. Na mijn bevestiging zet je
  de koppeling in `data/membirds-white-sun.json` onder `leden` (sleutel is het lidnummer uit de
  export).
- **Geen relatie:** vraag de volledige naam. Na mijn akkoord `acumulus.py relatie "<voornaam
  achternaam>"` (maakt een particuliere debiteur zonder aanhef; zie de valkuil in [[acumulus]]).
  Maak nooit zelf een relatie aan met andere velden.
- **Onbekend product:** zoek met `acumulus.py producten` het passende product. Past het bedrag
  niet, of zijn er meer kandidaten, leg het voor. Na mijn bevestiging zet je het in
  `data/membirds-white-sun.json` onder `producten`: de naam uit de export als sleutel, met
  `acumulus` (de naam), `unitprice` (excl. btw, vier decimalen, letterlijk uit `producten`) en
  `vatrate`.
- **Terugboeking (creditfactuur):** maak niets. Een terugbetaling krijgt een creditfactuur in
  Acumulus, die ik zelf maak. Meld de bestelling met het bedrag en de reden, en noteer hem in het
  logboek.

## 3. Voorstel: stoppunt

Laat me een tabel zien met nr, bestelnummer, klant, relatie (contactid), Acumulus-product, excl.
en incl. btw en de beschrijving. Noem erbij wat afwijkt of nieuw is (nieuwe koppeling, relatie
zonder e-mailadres). Wacht op mijn akkoord.

## 4. Aanmaken

```bash
/usr/bin/python3 -I ~/vault/scripts/membirds.py "<csv>" --schrijf
acumulus.py factuur data/facturen/white-sun/<bestand>.json --test
acumulus.py factuur data/facturen/white-sun/<bestand>.json
```

`--schrijf` maakt per klare bestelling `data/facturen/white-sun/<vandaag>-<achternaam>-<laatste 3
cijfers van het bestelnummer>.json` en weigert als een bestand al bestaat. `--test` per bestand
voordat je ze aanmaakt; de totalen moeten gelijk zijn aan de export. Het script `factuur` zet
`factuurnummer` en `entryid` in het bestand en weigert een bestand dat al is aangemaakt. Geeft het
een fout, stop en meld het.

## 5. Logboek en afronden

Zet in [[membirds]] onder `## Logboek` een regel: datum, de bestelnummers en de facturen (nummer,
relatie, bedrag incl. btw). Noem ook wat is overgeslagen of aan mij voorgelegd. Gebeurde er iets
nieuws (een nieuw product, een nieuwe koppeling, een andere soort bestelling), werk dan ook
`data/membirds-white-sun.json` en de werkwijze in [[membirds]] bij.

Herinner me aan het eind aan het opruimen: de export in `~/Downloads` en op de pagina Exports van
MemBirds bevat namen en e-mailadressen (zes dagen beschikbaar, zichtbaar voor alle beheerders).
Verwijder ze niet zelf.

## Antwoord

Kort, in het Nederlands: welke facturen je hebt aangemaakt (nummer, relatie, bedrag), welke
bestellingen je hebt overgeslagen of aan mij hebt voorgelegd, en wat ik nog moet doen (matches
accepteren zodra de Mollie-uitbetaling er is, exports opruimen, creditfacturen).
