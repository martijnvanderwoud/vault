---
description: Urenregistratie in LogMyTime, de logica van de Excel-urenstand en de LogMyTime API
tags: [werk, uren]
---

# Urenregistratie

Ik registreer tijd in LogMyTime (stopwatch per YouTrack-issue). Tijden rond ik zelf al af
bij het loggen (naar beneden op 3 minuten = 0,05 u); scripts rekenen dus niet nog eens af
en tellen `DurationSeconds` gewoon op. Dagelijks werk ik de Excel bij vanuit de
LogMyTime-export. Cijfers nooit uit het hoofd rekenen: altijd via een script op data
in `data/`. Plannen staan in [[vault-roadmap]].

## Excel-logica

`declarabele-uren-2026.xlsx`, Blad1:

- Target = werkdagen sinds 1-1 × uren per weekdag: ma 6,5 / di 6,5 / wo 4,5 / do 6,25 / vr 4,25 (28 u/week).
- Declarabel = cumulatief per klant (Pompkracht, Construct), handmatig overgenomen.
- Vrij opgenomen = target − declarabel. Vrij-budget = 196 u/jaar (28 × 7).
- Gereserveerde vrije uren: lijst in kolom J (omschrijving), K (nog gereserveerd), L (gepland).
- De Excel rekent in dagfracties (1 uur = 1/24); omrekenen naar uren met ×24.
- Target telt `NETWORKDAYS.INTL` van startdatum tot en met einddatum (beide inclusief), zonder feestdagen.
- Validatiepunt: stand per 10-11-2026 (einddatum in B6): Pompkracht 1092,40 u, Construct 0,55 u
  (samen 1092,95 u declarabel), werkuren 1255,5 u, vrij opgenomen 162,55 u van 196 u, gereserveerd 33,0 u.

## LogMyTime API

- Sleutel: beheeromgeving → "Eigenes Profil bearbeiten" → "Neuen API-Schlüssel generieren"; in `.env` als `LOGMYTIME_API_KEY`.
- Base URL `https://api.logmytime.de/V1/Api.svc` (OData). Auth: header `X-LogMyTimeApiKey` (of basic auth met sleutel als wachtwoord).
- Resources o.a. `TimeEntries`, `Projects`, `Tasks`, `Clients`, `Absences`, `Stopwatch` (starten/stoppen/opvragen).
- Docs: https://www.logmytime.de/Api/Grundlagen, /Api/Zeiteintraege, /Api/Httpxmljson, /Api/Stoppuhr, /Api/Requestgrenzen

## Script

`scripts/uren.py [--tot JJJJ-MM-DD] [--vanaf JJJJ-MM-DD] [--details]` toont per klant de declarabele uren,
het target en de vrij opgenomen uren (standaard 1-1 t/m vandaag). Gebruik
`/usr/bin/python3 -I ~/vault/scripts/uren.py`. Het script is alleen-lezen, rondt niet af en leest de sleutel zelf
uit `.env`. Gevalideerd tegen de Excel: per 10-11-2026 identiek (zie validatiepunt hierboven); per 6-11-2026
Pompkracht 1079,65 u en Construct 0,55 u.

- Klant volgt uit project; projecten zonder klant ("Niet declarabel", 8,75 u per 10-11) tellen niet als declarabel.
- Entries met een `AbsenceID` worden overgeslagen. Alle 2026-entries hebben `TypeID` 2 en geen afwezigheid.
- Lokale datum (Europe/Amsterdam) bepaalt bij welke dag een entry hoort.
- Nog niet in het script: gereserveerde vrije uren (zie [[vault-roadmap]], stap 2).

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
