---
description: Urenregistratie in LogMyTime, de logica van de urenstand (voorheen Excel) en de LogMyTime API
tags: [werk, uren]
---

# Urenregistratie

Ik registreer tijd in LogMyTime (stopwatch per YouTrack-issue). Tijden rond ik zelf al af
bij het loggen (naar beneden op 3 minuten = 0,05 u); scripts rekenen dus niet nog eens af
en tellen `DurationSeconds` gewoon op. De stand komt uit `/uren`; de Excel is uitgefaseerd
op 12-11-2026. Cijfers nooit uit het hoofd rekenen: altijd via een script op data
in `data/`. Plannen staan in [[vault-roadmap]].

## Excel-logica (historisch)

De Excel `declarabele-uren-2026.xlsx` is op 12-11-2026 uit de vault verwijderd (staat nog in de
git-history). `uren.py` volgde deze logica tot 19-11-2026 (zie Weektarget):

- Target = werkdagen sinds 1-1 × uren per weekdag: ma 6,5 / di 5,5 / wo 6 / do 6 / vr 4 (28 u/week, marathonschema vanaf 16-11-2026; daarvoor ma 6,5 / di 6,5 / wo 4,5 / do 6,25 / vr 4,25).
- Declarabel = cumulatief per klant (Pompkracht, Construct), handmatig overgenomen.
- Vrij opgenomen = target − declarabel. Vrij-budget = 196 u/jaar (28 × 7).
- Gereserveerde vrije uren: lijst in kolom J (omschrijving), K (nog gereserveerd), L (gepland).
- De Excel rekent in dagfracties (1 uur = 1/24); omrekenen naar uren met ×24.
- Target telt `NETWORKDAYS.INTL` van startdatum tot en met einddatum (beide inclusief), zonder feestdagen.
- Validatiepunt: stand per 10-11-2026 (einddatum in B6): Pompkracht 1092,40 u, Construct 0,55 u
  (samen 1092,95 u declarabel), werkuren 1255,5 u, vrij opgenomen 162,55 u van 196 u, gereserveerd 33,0 u.
- Laatste validatiepunt vóór uitfaseren, stand per 11-11-2026: Pompkracht 1097,05 u, Construct 0,55 u,
  werkuren 1260,0 u, vrij opgenomen 162,4 u, gereserveerd 33,0 u. `uren.py --tot 2026-11-11` identiek.

## Weektarget

Sinds 19-11-2026 (stap 8 van [[weekplanning-plan]]) rekent `uren.py` met een weekgebaseerd jaar en
een weektarget, niet meer met het kalenderjaar en een target per dag (zie Beslissingen in het plan).

- **Jaar:** de ISO-weken van het jaar. 2026 begint als overgang bij week 2 (ma 5-1) en loopt tot en met
  week 53 (zo 3-1-2027): 52 weken. Wat ik op 1 en 2 januari 2026 werkte, telt niet mee. Vanaf 2027 week 1
  tot en met de laatste week.
- **Jaardoel** = weken × 28 − 196 (vrij-budget); 2026: 1260 u.
- **Weektarget** = (jaardoel − declarabel + nog gereserveerd) / weken over. Weken over = werkdagen na de
  peildatum / 5, op zondag dus hele weken. Op zondag wordt het weektarget van de week erna vastgezet in
  `data/weekplanning/weektargets.csv` (`--zet-week`) en daarna niet meer opnieuw berekend. Week 47
  (16-11-2026) staat er achteraf met 27 u in (op 19-11 met de hand verlaagd van 28 u, op verzoek van Martijn); de weken daarvoor hebben geen weektarget.
- **Declarabel doel** van een week = weektarget − 5,6 u per vrije dag in die week.
- **Voor of achter:** een weektarget onder 28 u is voor, boven 28 u achter. Het verschil wordt over de
  rest van het jaar verdeeld. Niet gereserveerd vrij-budget telt vanzelf als voorsprong, vrij zonder
  reservering (ziek, spontaan vrij) als minder declarabel.
- **Validatiepunt (19-11-2026):** declarabel sinds 5-1 1127,70 u, nog te gaan 132,30 u, nog gereserveerd
  39,20 u, weken over 6,2, weektarget 27,66 u. Per zondag 15-11: 1104,80 u, 7 weken over, 27,77 u.
- **Weekplanning (sinds stap 9, 19-11-2026):** `weekplanning.py` leest het declarabele doel uit
  `weektargets.csv` en verdeelt het met gelijke ruimte over de werkdagen. "Vrij na reservering" en
  `data/weekplanning/werkuren.csv` (target per dag) bestaan niet meer.

## LogMyTime API

- Sleutel: beheeromgeving → "Eigenes Profil bearbeiten" → "Neuen API-Schlüssel generieren"; in `.env` als `LOGMYTIME_API_KEY`.
- Base URL `https://api.logmytime.de/V1/Api.svc` (OData). Auth: header `X-LogMyTimeApiKey` (of basic auth met sleutel als wachtwoord).
- Resources o.a. `TimeEntries`, `Projects`, `Tasks`, `Clients`, `Absences`, `Stopwatch` (starten/stoppen/opvragen).
- Docs: https://www.logmytime.de/Api/Grundlagen, /Api/Zeiteintraege, /Api/Httpxmljson, /Api/Stoppuhr, /Api/Requestgrenzen

## Script

`scripts/uren.py [--tot JJJJ-MM-DD] [--vanaf JJJJ-MM-DD] [--details] [--schrijf] [--zet-week]` toont
declarabel per klant, het jaar (declarabel, jaardoel, nog te gaan, nog gereserveerd, weken over, weektarget)
en deze week (vastgezet weektarget, vrije dagen, declarabel doel, gewerkt, nog te gaan). `--tot` is de
peildatum (standaard vandaag) en bepaalt het jaar; `--vanaf` geldt alleen voor declarabel per klant en mag
vóór 2026 liggen. Gebruik `/usr/bin/python3 -I ~/vault/scripts/uren.py`. Met `--schrijf` (alleen
standaardperiode) schrijft het ook [[uren-overzicht]] weg: het jaar, deze week, de weken tot nu (weektarget
tegenover gewerkt) en de vrije dagen. Met `--zet-week` (peildatum een zondag) zet het het weektarget van de
week erna vast; een week die al vaststaat, verandert niet. Het script is alleen-lezen richting LogMyTime,
rondt niet af en leest de sleutel zelf uit `.env`. Gevalideerd tegen de Excel (oude logica): per 10-11-2026
identiek; per 6-11-2026 Pompkracht 1079,65 u en Construct 0,55 u.

- Klant volgt uit project; projecten zonder klant ("Niet declarabel", 8,75 u per 10-11) tellen niet als declarabel.
- Entries met een `AbsenceID` worden overgeslagen. Alle 2026-entries hebben `TypeID` 2 en geen afwezigheid.
- Lokale datum (Europe/Amsterdam) bepaalt bij welke dag een entry hoort.
- Vrije dagen staan met datum in `data/vrije-dagen.csv` (kolommen `omschrijving`, `datum`, `tot` voor meer
  dagen, `half` voor een halve dag; niet per kalenderjaar, want week 53 van 2026 loopt door tot 3-1-2027).
  `scripts/vrije_dagen.py` geeft de vrije dagen in een periode en de nog gereserveerde uren na een
  peildatum (5,6 u per dag), in `uren.py` begrensd op het eind van het jaar: per 19-11 39,2 u (do 24-12,
  vr 25-12, ma 28 t/m do 31-12 en vr 1-1-2027). Voorbije dagen tellen vanzelf niet meer mee.
- `weekplanning.py` gebruikt `haal_stand(vanaf, tot)["per_dag"]` voor het gewerkte declarabele werk per dag.

## Skill

`/uren` (`.claude/skills/uren/SKILL.md`) draait `uren.py --schrijf` (ververst dus ook [[uren-overzicht]]), vertaalt "per 6 november" of "details" naar de
juiste opties en vat de stand samen. Alleen lezen; uren loggen valt erbuiten.

## Uren naar YouTrack

`/uren-naar-youtrack` (`.claude/skills/uren-naar-youtrack/SKILL.md`) draait
`scripts/uren_naar_youtrack.py [--dag JJJJ-MM-DD] [--uitvoeren]` en vervangt het dagelijks met de hand
overnemen van de tijd per taak naar YouTrack. Zonder `--uitvoeren` toont het alleen het plan.

- Issue-ID = begin van de taaknaam (`Tasks.Description`, via `TimeEntries.TaskID`). Taken zonder ID worden gemeld en overgeslagen.
- Per issue en dag precies één work item van mij (zoals ik het altijd met de hand deed: zonder tekst en
  zonder type, datum = middernacht UTC van de lokale dag). Idempotent: aanmaken als het ontbreekt,
  duur bijwerken als die afwijkt, niets doen als die klopt. Meerdere items met een andere som worden
  gemeld, niet aangepast. Er wordt nooit iets verwijderd.
- Gevalideerd 12-11-2026: voor 10-11 en 11-11 komt het script precies uit op mijn handmatige boekingen.
- De LogMyTime-toegang (`key`, `get_all`, datums) staat in `scripts/logmytime.py` en wordt gedeeld met `uren.py`.

## Export-observaties

- Het issuenummer zit alleen in het begin van de taaknaam (`PKP-890 …`); kolom `issue_id` is leeg.
- Taaknamen zijn afgekapt op ~100 tekens.

## API-observaties

- Sleutel werkt (gecontroleerd 10-11-2026). Limieten: 500 requests per 24 uur per account, max 10.000 entities per
  response (daarna `__next`/skiptoken), geen parallelle requests.
- Er is geen rapportage-endpoint met totalen; alleen `$inlinecount`. Totalen tellen we zelf op uit `TimeEntries`.
- De klant volgt uit `TimeEntries.ProjectID` → `Projects.ClientID` → `Clients.Name`.
- `StartTime` komt als `/Date(ms)/` (UTC). `TypeID` kan niet in `$filter`, dus client-side filteren.
- Alle 2026-entries elke run ophalen (`$filter` op `StartTime`, `$select` op de nodige velden). Geen incrementele
  cache: via `LastChangeTime` mis je verwijderde entries en dan klopt een totaal stil niet meer.
