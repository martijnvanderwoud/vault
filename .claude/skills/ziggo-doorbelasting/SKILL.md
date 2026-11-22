---
name: ziggo-doorbelasting
description: Belast na een Ziggo-factuur het privé- en het White Sun-deel door - zet de factuur aan Familie van der Woud - de Jonge (tv en een derde internet) en die aan White Sun Qigong (een derde internet) als conceptfactuur in Acumulus, haalt na mijn akkoord de PDF's op naar Google Drive, zet de mail aan Franca als concept in Gmail en boekt de White Sun-factuur als uitgave in Franca's Acumulus (via inkoopfactuur). Gebruik deze skill zodra ik vraag om de Ziggo-factuur te verdelen, te verrekenen of door te belasten, de Ziggo-facturen voor de familie of White Sun te maken, of een gepauzeerde Ziggo-doorbelasting af te maken, ook als ik het woord skill niet gebruik. Niet voor het boeken van de Ziggo-factuur zelf (dat is inkoopfactuur) en niet voor de Vodafone-facturen.
allowed-tools: Bash(/usr/bin/python3 -I ~/vault/scripts/acumulus.py*), Bash(ls*), Read, Write, mcp__claude_ai_Gmail__search_threads, mcp__claude_ai_Gmail__get_thread, mcp__claude_ai_Gmail__create_draft
---

# Ziggo doorbelasten

Draai vanuit `~/vault`. Achtergrond: [[ziggo-doorbelasting]] (verdeling, vaste bedragen, wanneer
opnieuw rekenen, mailtekst), [[acumulus]] (API, script, vaste id's), [[facturen-archief]].

Uitgangspunt: voer alleen uit wat hieronder als regel staat. Een situatie zonder regel leg je aan
mij voor met wat je ziet. Ga nooit om een fout van het script heen.

## Regels

- **Vaste bedragen.** TV Start 13,95 en Internet Xtra 15,32 excl. btw, uit [[ziggo-doorbelasting]].
  Reken ze niet opnieuw uit. Wijkt het excl.-btw-totaal van de Ziggo-factuur af van wat daar
  staat, dan stop je en leg je het voor: dan maken we samen een nieuwe berekening.
- Totalen en btw komen uit de uitvoer van `acumulus.py factuur`. Reken nooit zelf.
- **Alleen concepten.** Ik kijk ze na en maak ze zelf definitief. De mail is ook een concept.
- **Betaalstatus niet betaald.** Het script zet dat standaard; zet geen `paymentstatus` in het
  bestand, tenzij ik het zeg.
- **Lees `.env` niet.**
- Fout in een concept: pas het databestand aan, ik verwijder het oude concept, en dan maak je
  een nieuw. Een concept aanpassen kan niet via de API.

## 1. Ziggo-factuur vinden

Neem de nieuwste Ziggo-factuur, of de factuur die ik noem:

```bash
ls ~/"Mijn Drive/crimsoncricket-documents/inkoop/<JJJJ>/" | grep Ziggo
```

Staat hij er niet, dan is hij nog niet ingeboekt: zeg dat ik eerst de inkoopfactuur moet laten
boeken en stop. Lees de PDF met de Read-tool en noteer het factuurnummer, het totaal excl. btw en
de periode van de maandelijkse kosten (bijvoorbeeld 01-12-2026 t/m 31-12-2026). De
periodemaand `<JJJJ-MM>` is de maand van die periode.

Controleer dat er nog niet is doorbelast:

- `data/facturen/<JJJJ-MM>-ziggo-familie.json` en `...-ziggo-white-sun.json` bestaan nog niet.
  Bestaan ze wel, ga dan verder bij `Hervatten`.
- Geen bestand heeft het Ziggo-factuurnummer al in `bronnen`.

## 2. Databestanden schrijven

Schrijf beide bestanden zoals `data/facturen/2026-12-ziggo-familie.json` en
`data/facturen/2026-12-ziggo-white-sun.json`. Pas alleen de periode in de regels en de
bestandsnaam van de Ziggo-factuur in `bronnen` aan; laat `conceptid` en `factuurnummer` weg.

```json
{
  "contactid": 9385039,
  "template": 2982,
  "costcenter": 9410,
  "description": "Ziggo Internet en TV",
  "bronnen": ["Ziggo-<factuurnummer>.pdf"],
  "regels": [
    {"product": "TV Start - <dd-mm-jjjj> t/m <dd-mm-jjjj>", "unitprice": "13.95", "vatrate": 21, "quantity": 1},
    {"product": "Internet Xtra - <dd-mm-jjjj> t/m <dd-mm-jjjj>", "unitprice": "15.32", "vatrate": 21, "quantity": 1}
  ]
}
```

White Sun Qigong: `contactid` 72640, `description` `Ziggo Internet`, alleen de regel Internet Xtra.
Geen `issuedate`: Acumulus neemt dan vandaag.

## 3. Testen en concepten maken

```bash
/usr/bin/python3 -I ~/vault/scripts/acumulus.py factuur data/facturen/<JJJJ-MM>-ziggo-familie.json --test
/usr/bin/python3 -I ~/vault/scripts/acumulus.py factuur data/facturen/<JJJJ-MM>-ziggo-white-sun.json --test
```

Verwacht: familie totaal 35.42, White Sun 18.54. Geen fouten en de verwachte totalen? Draai beide
zonder `--test` en zet elk `conceptid` uit de uitvoer als `"conceptid": <id>` in het bijbehorende
databestand.

## 4. Stoppunt: ik kijk de concepten na

Geef me per concept klant, regels, totaal en conceptid, en wat ik moet nakijken: titel,
factuurdatum, sjabloon Standaard, kostenplaats Algemeen en betaalstatus niet betaald. Wacht tot
ik zeg dat de facturen definitief zijn.

## 5. PDF's ophalen

```bash
/usr/bin/python3 -I ~/vault/scripts/acumulus.py pdf <conceptid>
```

Voor beide concepten. Lees elke PDF met de Read-tool en controleer klant, titel, regels en totaal
tegen het databestand. Zet `"factuurnummer": "<nummer>"` in het databestand.

## 6. Concept-mail aan Franca

Alleen voor White Sun Qigong; de familiefactuur wordt niet verstuurd. Maak met `create_draft`
(claude.ai Gmail, zakelijk account) een concept aan `franca@whitesunqigong.nl` met onderwerp
`Factuur <nummer> - Ziggo Internet` en de tekst uit [[ziggo-doorbelasting]].

**De PDF kan nog niet mee** (de koppeling vraagt de bijlage als base64, en dat is te groot). Zeg
me dat ik `Factuur_<nummer>.pdf` zelf moet bijvoegen, met het volledige pad en de link naar het
concept.

## 7. Inboeken bij White Sun

Alleen de White Sun-factuur. Volg de skill `inkoopfactuur` voor administratie White Sun Qigong,
met als bron mijn eigen factuur `verkoop/<JJJJ>/Factuur_<nummer>.pdf` (leverancier
`The-Crimson-Cricket`). Die skill heeft een eigen stoppunt voor het voorstel; boek pas na mijn
akkoord.

## Hervatten

Bestaan de databestanden al, dan per bestand:

- **Geen `conceptid`**: ga verder bij stap 3.
- **Wel een `conceptid`, geen `factuurnummer`**: vraag of de factuur definitief is en ga verder
  bij stap 5.
- **Wel een `factuurnummer`** (White Sun): kijk in Gmail of er al een concept of verzonden mail
  met dat nummer is. Zo niet, ga verder bij stap 6. Bestaat
  `data/uitgaven/white-sun/The-Crimson-Cricket-<nummer>.json` niet of zonder `entryid`, ga dan
  verder bij stap 7.

## Antwoord

Kort, in het Nederlands: beide factuurnummers en totalen uit de uitvoer, de paden van de PDF's,
de link naar het concept in Gmail, de herinnering om de PDF bij te voegen en het boekstuknummer
in Franca's Acumulus.
