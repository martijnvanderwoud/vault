---
name: uren
description: Toont mijn urenstand uit LogMyTime - declarabel in het weekgebaseerde jaar, jaardoel, nog gereserveerde vrije uren, het weektarget en wat er deze week nog te gaan is. Gebruik deze skill zodra ik vraag naar mijn uren, mijn urenstand, hoeveel ik declarabel ben, wat mijn weektarget is, hoeveel ik deze week nog moet, of de stand per een bepaalde datum, ook als ik het woord skill of /uren niet gebruik. Niet voor het loggen of corrigeren van uren.
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

Zonder `--schrijf` toont het script alleen de stand. Peildatum is standaard vandaag; het jaar volgt de
ISO-weken (2026 loopt van ma 5-1-2026 t/m zo 3-1-2027). Met argumenten van mij:

- "per 6 november" of "tot 6-11": `--tot 2026-11-06` (peildatum)
- "vanaf oktober": `--vanaf 2026-10-01` (alleen voor declarabel per klant)
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
declarabel (per klant), het jaar (declarabel, jaardoel, nog te gaan, nog gereserveerd, weken over,
weektarget) en deze week (vastgezet weektarget, vrije dagen, declarabel doel, gewerkt, nog te gaan).
Gebruik een decimale komma. Noem de peildatum en dat het overzicht in `gebieden/werk/uren-overzicht.md`
is bijgewerkt. "Vrij na reservering" is alleen voor de weekplanning (tot stap 9 van het
weekplanning-plan); noem die niet.

Vraag ik of ik voor of achter loop, kijk dan naar het weektarget van het jaar: onder 28 u is voor,
boven 28 u is achter. Het verschil wordt over de rest van het jaar verdeeld, niet in één week
ingehaald. Zie "Weektarget" in `gebieden/werk/urenregistratie.md`.

Wijkt een stand af van wat ik eerder noemde of van het validatiepunt in de notitie,
zeg dat dan, maar trek zelf geen conclusie over de oorzaak.

## Onderhoud

Vrije dagen staan met datum in `data/vrije-dagen.csv` (`omschrijving`, `datum`, `tot`,
`half`). Een voorbije vrije dag telt vanzelf niet meer mee als gereserveerd; daar hoeft niets
aan te gebeuren. Een nieuwe vrije dag zet ik er met datum bij.
