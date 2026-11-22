---
name: betalingen-white-sun
description: Helpt bij het verwerken van de betalingen op de Knab-rekening van White Sun Qigong (de zakelijke rekening van Franca) in Acumulus - leest het Knab-transactieoverzicht uit Downloads, haalt de openstaande facturen op, loopt de transacties één voor één met me door, zet na mijn akkoord facturen klaar voor lessen die zonder factuur zijn betaald (en maakt nieuwe klanten aan), zodat ik in Acumulus alleen nog de match hoef te accepteren, en houdt het logboek bij. Gebruik deze skill zodra ik vraag om de betalingen, mutaties, bankmutaties of het bankoverzicht van White Sun of Franca te verwerken, af te handelen of na te lopen, of om facturen voor betaalde lessen klaar te zetten, ook als ik het woord skill niet gebruik. Niet voor inkoopfacturen boeken (dat is inkoopfactuur) en niet voor de bankmutaties van The Crimson Cricket.
allowed-tools: Bash(/usr/bin/python3 -I ~/vault/scripts/acumulus.py*), Bash(/usr/bin/python3 -I ~/vault/scripts/knab.py*), Bash(ls*), Read, Write, Edit
---

# Betalingen White Sun verwerken

Draai vanuit `~/vault`. Achtergrond: [[betalingen-white-sun]] (soorten transacties en logboek),
[[acumulus]] (API, script, valkuilen). Alle Acumulus-commando's hier zijn voor Franca's
administratie: `/usr/bin/python3 -I ~/vault/scripts/acumulus.py --administratie white-sun <commando>`
(hieronder afgekort tot `acumulus.py <commando>`). Gebruik `/usr/bin/python3`: de pyenv-Python
heeft geen SSL.

Uitgangspunt: voer alleen uit wat hieronder als regel staat. Een transactie die bij geen soort
past, leg je aan mij voor met wat je ziet. Ga nooit om een fout van het script heen.

## Hoe het werkt

Ik download een transactieoverzicht (CSV) uit Knab en importeer het zelf in Acumulus. De lijst
met mutaties die in Acumulus verwerkt moeten worden, is niet op te vragen via de API. Daarom
werk jij vanuit dezelfde CSV, en verwerk ik de mutaties zelf in Acumulus. Jouw werk is: per
transactie uitzoeken waar hij bij hoort, en waar nodig vooraf een factuur klaarzetten, zodat
Acumulus bij de mutatie zelf de match vindt.

## Regels

- **Eén voor één, samen.** Loop de transacties met me door en beslis niets zelf. Groepeer
  gelijksoortige transacties gerust, maar wacht op mijn akkoord voor je iets aanmaakt.
- **Facturen zijn meteen definitief** en kunnen niet terug via de API. Maak ze pas aan na mijn
  akkoord op een tabel (stap 4), en altijd eerst met `--test`.
- **Reken niet zelf.** Prijzen komen uit `acumulus.py producten`, totalen uit de uitvoer van
  `factuur`.
- **Raak in Acumulus niets anders aan.** Geen betaalstatus zetten, niets verwijderen, geen
  bestaande relaties wijzigen. Verwerken van mutaties doe ik.
- **Lees `.env` niet.** Het script leest de inloggegevens zelf.

## 1. Overzicht inlezen

`ls ~/Downloads`. Het bestand heet `Knab Transactieoverzicht … .csv`. Staat er meer dan één,
vraag welke. Dan:

```bash
/usr/bin/python3 -I ~/vault/scripts/knab.py "<csv>"
acumulus.py openstaand
```

`knab.py` nummert de transacties (oudste eerst) en zet de bekende relatie erbij uit
`data/betalers-white-sun.json`. Dat is een hint, geen zekerheid: controleer dat het klopt bij de
omschrijving.

Begin een logboekblok in [[betalingen-white-sun]] onder `## Logboek`: `### <vandaag>: overzicht
<van> t/m <tot>`, een regel met de openstaande posten en een tabel met per transactie nr, datum,
bedrag, tegenpartij, omschrijving en een lege kolom Beslissing.

## 2. Soort bepalen

Zie [[betalingen-white-sun]], `Soorten transacties`:

| Soort | Herken je aan | Wat jij doet |
|---|---|---|
| Betaling inkoopfactuur | afschrijving; bedrag en leverancier gelijk aan een openstaande inkoopfactuur | match noemen (entryid, omschrijving); ik verwerk hem met de verwerklink |
| Les zonder factuur | bijschrijving via iDEAL/Wero (tegenpartij KNAB) of overboeking, met "les …" of "proefles" in de omschrijving | factuur klaarzetten (stap 3–5) |
| Betaling verkoopfactuur | bijschrijving; bedrag en relatie gelijk aan een openstaande verkoopfactuur op Knab | match noemen; ik verwerk hem |
| Uitbetaling Mollie | bijschrijving van Stichting Mollie Payments, "REF T…" | niets: ik boek hem als interne overboeking vanaf rekening Mollie |

Een openstaande factuur op rekening **Mollie** is geen match voor een betaling op Knab.

## 3. Lessen: product en relatie

Product: zoek met `acumulus.py producten` het product dat bij omschrijving en bedrag past (de
kolom incl. btw). Gebruikelijk:

| Omschrijving | Bedrag | Product |
|---|---|---|
| les Jaartraject van … | 5,00 | Qigong \| les buiten - abonnement |
| les buiten van … | 15,00 | Qigong \| les buiten |
| … proefles | 10,00 | Qigong \| Proefles |

Past het bedrag bij geen product, of bij meer dan één, leg het voor.

Relatie: neem de bekende relatie uit `knab.py`. Is er geen, zoek met `acumulus.py klanten
"<achternaam>"` en stel de actieve relatie voor die past; zeg erbij als de voorletters het niet
bevestigen. Na mijn bevestiging zet je de koppeling in `data/betalers-white-sun.json` (`bank`:
de naam zoals op het overzicht; `omschrijving` erbij als de rekeninghouder iemand anders is dan
de klant).

Nieuwe klant: vraag de volledige naam (de rekeninghouder is vaak een ouder of partner, de
omschrijving noemt soms alleen een voornaam). Na mijn akkoord:

```bash
acumulus.py relatie "<voornaam achternaam>"
```

Dat maakt een particuliere debiteur met de naam als contactpersoon en zonder aanhef, zoals
Franca het doet. Maak nooit zelf een relatie aan via de API met andere velden: zie de valkuil
in [[acumulus]].

## 4. Voorstel: stoppunt

Schrijf per les een databestand `data/facturen/white-sun/<vandaag>-<achternaam>.json` (kleine
letters, kebab-case; bestaat het al, zet er `-2` achter):

```json
{
  "administratie": "white-sun",
  "contactid": 9247824,
  "template": 133249,
  "costcenter": 10213,
  "accountnumber": 227201,
  "description": "Qigong",
  "issuedate": "2026-11-22",
  "concept": 0,
  "bron": {"bank": "Knab", "referentie": "C6K16PGNBJ329BVS", "omschrijving": "les Jaartraject van Hr MJJ Gauthier"},
  "regels": [{"product": "Qigong | les buiten - abonnement", "unitprice": "4.1322", "vatrate": 21, "quantity": 1}]
}
```

- `issuedate` is vandaag, niet de betaaldatum. De factuur staat op niet betaald; de match in
  Acumulus zet hem op betaald op de juiste datum.
- `product` en `unitprice` letterlijk uit `producten` (excl. btw, vier decimalen). Een regel kan
  niet naar het product zelf verwijzen.
- Sjabloon White Sun Qigong (133249), kostenplaats Algemeen (10213), rekening Knab (227201).

Controleer elk bestand:

```bash
acumulus.py factuur data/facturen/white-sun/<bestand>.json --test
```

Laat me een tabel zien met nr, relatie (contactid), de naam op de bank, product, excl. en incl.
btw (uit de uitvoer van `--test`). Wacht op mijn akkoord.

## 5. Aanmaken

Per bestand:

```bash
acumulus.py factuur data/facturen/white-sun/<bestand>.json
```

Het script zet `factuurnummer` en `entryid` in het bestand en weigert een bestand dat al is
aangemaakt. Geeft het een fout, stop en meld het.

## 6. Logboek en afronden

Vul na elke beslissing de kolom Beslissing in het logboek in (bijv. "Factuur 20260315 gemaakt
door Claude" of "Interne overboeking Mollie; Martijn boekt zelf"). Komt er een nieuwe soort
transactie langs en beslissen we hoe die moet, voeg hem dan toe aan `Soorten transacties` in
[[betalingen-white-sun]] en aan de tabel in stap 2.

## Antwoord

Kort, in het Nederlands: per transactie wat ermee gebeurd is, welke facturen je hebt
aangemaakt (nummer, relatie, bedrag) en wat ik nog in Acumulus moet doen (matches accepteren,
verwerklinks, interne overboekingen).
