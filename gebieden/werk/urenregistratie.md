---
description: Urenregistratie in LogMyTime, de logica van de Excel-urenstand en de LogMyTime API
tags: [werk, uren]
---

# Urenregistratie

Ik registreer tijd in LogMyTime (stopwatch per YouTrack-issue). Tijden worden altijd
**naar beneden afgerond op 3 minuten** (= 0,05 u). Dagelijks werk ik de Excel bij vanuit
de LogMyTime-export. Cijfers nooit uit het hoofd rekenen: altijd via een script op data
in `data/`. Plannen staan in [[vault-roadmap]].

## Excel-logica

`declarabele-uren-2026.xlsx`, Blad1:

- Target = werkdagen sinds 1-1 × uren per weekdag: ma 6,5 / di 6,5 / wo 4,5 / do 6,25 / vr 4,25 (28 u/week).
- Declarabel = cumulatief per klant (Pompkracht, Construct), handmatig overgenomen.
- Vrij opgenomen = target − declarabel. Vrij-budget = 196 u/jaar (28 × 7).
- Gereserveerde vrije uren: lijst in kolom J (omschrijving), K (nog gereserveerd), L (gepland).
- Validatiepunt: stand per 6-11-2026: Pompkracht 1079,65 u, Construct 0,55 u.

## LogMyTime API

- Sleutel: beheeromgeving → "Eigenes Profil bearbeiten" → "Neuen API-Schlüssel generieren"; in `.env` als `LOGMYTIME_API_KEY`.
- Base URL `https://api.logmytime.de/V1/Api.svc` (OData). Auth: header `X-LogMyTimeApiKey` (of basic auth met sleutel als wachtwoord).
- Resources o.a. `TimeEntries`, `Projects`, `Tasks`, `Clients`, `Absences`, `Stopwatch` (starten/stoppen/opvragen).
- Docs: https://www.logmytime.de/Api/Grundlagen, /Api/Zeiteintraege, /Api/Httpxmljson, /Api/Stoppuhr, /Api/Requestgrenzen

## Export-observaties

- Het issuenummer zit alleen in het begin van de taaknaam (`PKP-890 …`); kolom `issue_id` is leeg.
- Taaknamen zijn afgekapt op ~100 tekens.
