---
name: uren
description: Toont mijn urenstand uit LogMyTime - declarabele uren per klant, het target, vrij opgenomen uren, gereserveerde vrije uren en wat er overblijft van het vrij-budget. Gebruik deze skill zodra ik vraag naar mijn uren, mijn urenstand, hoeveel ik declarabel ben, hoeveel vrije uren ik heb opgenomen of over heb, of de stand per een bepaalde datum, ook als ik het woord skill of /uren niet gebruik. Niet voor het loggen of corrigeren van uren, en niet voor vragen over de Excel zelf.
allowed-tools: Bash(/usr/bin/python3 -I ~/vault/scripts/uren.py*)
---

# Uren

Toont de stand uit LogMyTime via `scripts/uren.py` en schrijft die weg naar
`gebieden/werk/uren-overzicht.md`. Achtergrond, logica en validatiepunten
staan in `gebieden/werk/urenregistratie.md`.

## Uitvoeren

```bash
/usr/bin/python3 -I ~/vault/scripts/uren.py --schrijf
```

Zonder `--schrijf` toont het script alleen de stand. Standaard 1 januari van dit jaar t/m vandaag. Met argumenten van mij:

- "per 6 november" of "tot 6-11": `--tot 2026-11-06`
- "vanaf oktober": `--vanaf 2026-10-01`
- "details", "per type" of "afwezigheid": `--details`

Met `--vanaf` of `--tot` laat je `--schrijf` weg: het overzicht gaat alleen over de
standaardperiode en het script weigert anders.

Zet datums om naar `JJJJ-MM-DD` (jaar is het huidige jaar, tenzij ik een ander noem).

## Regels

- Cijfers komen altijd uit de output van het script. Reken nooit zelf uit en rond niet af:
  de uren zijn al door mij afgerond bij het loggen.
- Het script is alleen-lezen richting LogMyTime; `--schrijf` overschrijft alleen
  `gebieden/werk/uren-overzicht.md` (gegenereerd, niet met de hand bewerken). Het leest de API-sleutel zelf uit `.env`; lees `.env` niet.
- Limiet van de API: 500 requests per 24 uur. Draai het script dus niet vaker dan nodig,
  één keer per vraag is genoeg.
- Lees de output door voor je antwoordt. Als het script een fout geeft (sleutel, netwerk,
  limiet), meld die dan letterlijk en probeer het niet te omzeilen.

## Antwoord

Geef de cijfers uit de output kort weer in het Nederlands, in dezelfde volgorde:
declarabel (per klant), target, vrij opgenomen met het budget van 196 u, gereserveerd
en wat er na reservering overblijft. Gebruik een decimale komma. Noem de peildatum en dat het overzicht in `gebieden/werk/uren-overzicht.md` is bijgewerkt.

Wijkt een stand af van wat ik eerder noemde of van het validatiepunt in de notitie,
zeg dat dan, maar trek zelf geen conclusie over de oorzaak.

## Onderhoud

Is een gereserveerde vrije dag voorbij, dan zet ik `nog_gereserveerd_uren` in
`data/vrije-dagen-2026.csv` op 0. Wijs me erop als de output een reservering laat zien
waarvan de omschrijving naar een datum in het verleden verwijst.
