---
description: Analyse van het startpakket van de AI-Brein Bootcamp (Brand it Up) en wat de vault daarvan heeft overgenomen
tags: [vault, analyse, bootcamp]
---

# Leren van de AI-Brein Bootcamp

Analyse op 15-11-2026 van het zip-pakket waarmee Franca de AI-Brein Bootcamp van Brand it Up
(Manon van der Weegen, 4 t/m 6 november 2026) begon. Vervolg: het interview in
[[interview-voortgang]].

## Wat het pakket is

Drie dagen waarin een niet-technische ondernemer in gesprek met Claude vijf contextbestanden
vult: bedrijf, ondernemer, aanbod, klant en grenzen. Daarnaast een voortgangsbestand, een
kladje over hoe de persoon praat, en een HTML-dashboard ("breinkaart") dat zijn gegevens uit één
JavaScript-bestand leest. Dag 3 eindigt in een AI-roadmap: taken per afdeling, elk groen (AI doet
het), oranje (concept, jij keurt goed) of rood (blijft bij jou), naar "Your AI Operating System:
The Map" van AI Her Way. De bootcamp bouwt niets en eindigt met een advies waar te beginnen.

## Overgenomen

- **Interviewvorm** om context te verzamelen: één vraag per keer, eerst voorleggen wat al
  bekend is, "skip" mag, spiegelen voor het schrijven, letterlijke zinnen bewaren.
- **Drie kleuren en een ondergrens** als leesbare laag naast de technische guardrails:
  [[werkafspraken]].
- **Een notitie over de persoon** (energie, sterke punten, wat uit handen): [[over-martijn]].
- **Schrijfstem met echte voorbeelden**: [[schrijfstem]].
- **Geparkeerd-sectie** in de voortgangsnotitie voor zijsporen die ergens anders horen.

## Bruikbaar voor later

- **Breinkaart-techniek:** statische HTML die nooit verandert, met de data in een los
  `gegevens.js` dat via een script-tag laadt. Omzeilt de beperking dat een `file://`-pagina geen
  lokale bestanden kan lezen. Kandidaat voor de HTML-interface in [[agents-dashboard-beslissingen]];
  data dan via `json.dumps` schrijven en in de pagina als tekst tonen, nooit als HTML.
- **Scoren van taken** om te kiezen wat je eerst automatiseert: hoe vaak, tijd per keer, heb
  jij het specifiek nodig, wat staat er op het spel. "Admin is de leerschool, marketing is de
  beloning."
- **Definieer klaar** voordat je automatiseert; staat al als "Klaar als:" in de plannotities.

## Niet overgenomen

- Dagvergrendeling en verplichte affiliate-link: cohort- en funnelmechaniek.
- Volledige inhoud van elk bestand gedupliceerd in het datafile van het dashboard: drift.
- Hoofdletterbestanden in de root zonder frontmatter, en alles elke sessie inladen. Werkt voor
  vijf bestanden, niet voor een groeiende vault.
- Het continuïteitsbestand: plannotities met voortgang en bevindingen plus git doen dat al.
