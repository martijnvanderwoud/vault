---
name: hostingfactuur-flow
description: Maakt de maandelijkse hostingfactuur voor FLOW aan Arbeidskracht (Pompkracht, Hendrik Witteveen) - leest de TransIP-facturen, zet productie en staging als conceptfactuur in Acumulus, haalt na mijn akkoord de PDF op naar Google Drive en zet de mail aan Hendrik als concept in Gmail. Gebruik deze skill zodra ik vraag om de hostingfactuur voor Pompkracht, Arbeidskracht of FLOW te maken, de TransIP-kosten van FLOW door te belasten, of een gepauzeerde hostingfactuur af te maken, ook als ik het woord skill niet gebruik. Niet voor de urenfactuur, en niet voor de hostingfacturen van Afke Hennus of Construct.
allowed-tools: Bash(/usr/bin/python3 -I ~/vault/scripts/acumulus.py*), Bash(ls*), Read, Write, mcp__claude_ai_Gmail__search_threads, mcp__claude_ai_Gmail__get_thread, mcp__claude_ai_Gmail__create_draft
---

# Hostingfactuur FLOW

Draai vanuit `~/vault`. Achtergrond: [[hosting-transip]] (welke TransIP-facturen bij welke
maand horen, welke projecten), [[acumulus]] (API, script, vaste id's), [[facturen-archief]]
(waar de PDF's staan).

Uitgangspunt: voer alleen uit wat hieronder als regel staat. Een situatie zonder regel leg je aan
mij voor met wat je ziet. Ga nooit om een fout van het script heen.

## Regels

- **Bedragen neem je letterlijk over** van de TransIP-factuur (het subtotaal per project).
  Totalen en btw komen uit de uitvoer van `acumulus.py factuur`. Reken nooit zelf.
- **Alleen concepten.** Het script maakt in Acumulus alleen concepten. Ik kijk ze na en maak ze
  zelf definitief. Ook de mail is een concept: ik verstuur hem zelf.
- **Lees `.env` niet.** Het script leest de inloggegevens zelf.
- Gaat er iets mis in een concept (een verkeerde regel, kostenplaats of datum), dan pas je het
  databestand aan en verwijder ik het oude concept. Daarna maak je een nieuw concept. Een
  concept aanpassen kan niet via de API.

## 1. Maand bepalen

De factuur voor maand M gebruikt de TransIP-facturen van rond de 1e en de 15e van M+1. Noem ik
geen maand, neem dan de vorige maand. Is het voor de 15e, dan is de factuur van de 15e er nog
niet: meld dat en stop.

Controleer dat de maand nog niet is gefactureerd:

- `data/facturen/<JJJJ-MM>-hosting-flow.json` bestaat nog niet. Bestaat het wel, ga dan verder
  bij `Hervatten`.
- In de verzonden mail aan hendrik.witteveen@pompkracht.nl staat nog geen
  "hosting FLOW - <maand> <jaar>" (`search_threads` met `in:sent`).

## 2. TransIP-facturen lezen

```bash
ls ~/"Mijn Drive/crimsoncricket-documents/inkoop/<JJJJ>/" | grep TransIP-F0000_<JJMM>
```

met `<JJMM>` van maand M+1. Verwacht twee bestanden: `_0003_` (rond de 1e) en `_0011_` (rond de
15e). Lees beide met de Read-tool.

- **Productie**: de sectie `OpenStack (martijnvanderwoud-pompkracht-prd)`, normaal op de factuur
  van de 15e. Neem het `Subtotaal` van die sectie en de factureringsperiode van de maandregels.
- **Staging**: de sectie `OpenStack (martijnvanderwoud-pompkracht-dev)`, normaal op de factuur
  van de 1e. Loopt de sectie over twee pagina's, dan staat het subtotaal aan het eind van het
  laatste stuk.
- Regels van 1 uur of een paar dagen (een volume dat even bestond) horen bij het subtotaal. Neem
  daarvoor de periode van de maandregels.
- Negeer `shared-hosting`, de domeinregistraties en de kopjes `BTH000031` zonder bedragen.

Staat een project op geen van beide facturen of op allebei, wijkt het aantal TransIP-facturen
af, of verschilt een subtotaal sterk van de vorige maand: leg het voor en stop.

## 3. Databestand schrijven

Schrijf `data/facturen/<JJJJ-MM>-hosting-flow.json` zoals `data/facturen/2026-10-hosting-flow.json`:

```json
{
  "contactid": 2318938,
  "template": 2982,
  "costcenter": 9418,
  "description": "Hosting FLOW - <maand> <jaar>",
  "bronnen": ["<bestandsnaam factuur 15e>", "<bestandsnaam factuur 1e>"],
  "regels": [
    {"product": "TransIP - productie-omgeving OpenStack: <dd-mm-jjjj> t/m <dd-mm-jjjj>", "unitprice": "<subtotaal>", "vatrate": 21, "quantity": 1},
    {"product": "TransIP - staging-omgeving OpenStack: <dd-mm-jjjj> t/m <dd-mm-jjjj>", "unitprice": "<subtotaal>", "vatrate": 21, "quantity": 1}
  ]
}
```

De maand voluit en in kleine letters ("oktober 2026"). `unitprice` als string met een punt. Geen
`issuedate`: Acumulus neemt dan vandaag.

## 4. Testen en concept maken

```bash
/usr/bin/python3 -I ~/vault/scripts/acumulus.py factuur data/facturen/<JJJJ-MM>-hosting-flow.json --test
```

Geen fouten of waarschuwingen? Maak dan het concept aan:

```bash
/usr/bin/python3 -I ~/vault/scripts/acumulus.py factuur data/facturen/<JJJJ-MM>-hosting-flow.json
```

Zet het `conceptid` uit de uitvoer als `"conceptid": <id>` in het databestand, zodat je later
kunt hervatten.

## 5. Stoppunt: ik kijk het concept na

Geef me de regels, de totalen uit de uitvoer, het conceptid en wat ik moet nakijken: klant,
titel, regels en bedragen, factuurdatum, sjabloon Standaard en kostenplaats Hosting. Wacht tot
ik zeg dat de factuur definitief is.

## 6. PDF ophalen

```bash
/usr/bin/python3 -I ~/vault/scripts/acumulus.py pdf <conceptid>
```

Lees de opgeslagen PDF met de Read-tool en controleer dat klant, titel, regels en totaal kloppen
met het databestand en de uitvoer van stap 4. Zet `"factuurnummer": "<nummer>"` in het
databestand.

## 7. Concept-mail aan Hendrik

Maak met `create_draft` (claude.ai Gmail, zakelijk account) een concept:

- Aan: `hendrik.witteveen@pompkracht.nl`
- Onderwerp: `Factuur <nummer> - hosting FLOW - <maand> <jaar>`
- Tekst:

  ```
  Beste Hendrik,

  Bijgevoegd stuur ik je mijn factuur in verband met de hosting van de diverse FLOW-systemen in de maand <maand> <jaar>.

  Met vriendelijke groet,
  Martijn van der Woud
  The Crimson Cricket Internet Services
  ```

**De PDF kan nog niet mee.** De koppeling vraagt de bijlage als base64 in de aanroep, en dat is
te groot. Zeg me dat ik `Factuur_<nummer>.pdf` zelf moet bijvoegen, en geef het volledige pad en
de link naar het concept. Dit verandert als het script uit [[gmail-zakelijk-concepten-plan]]
klaar is.

## Hervatten

Bestaat het databestand al:

- **Geen `conceptid`**: ga verder bij stap 4.
- **Wel een `conceptid`, geen `factuurnummer`**: vraag of de factuur definitief is en ga verder
  bij stap 6. Zegt het script dat het concept nog niet definitief is, meld dat dan.
- **Wel een `factuurnummer`**: kijk of er in Gmail al een concept of verzonden mail met dat
  nummer is. Is die er niet, ga dan verder bij stap 7.

## Antwoord

Kort, in het Nederlands: het factuurnummer, het totaal incl. btw uit de uitvoer, het pad van de
PDF, de link naar het concept in Gmail en de herinnering om de PDF bij te voegen.
