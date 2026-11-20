---
description: Plan om taken in LogMyTime automatisch te archiveren zodra hun YouTrack-issue al een tijd is opgelost, als autonome agent onder launchd
tags: [vault, plan, uren, logmytime, youtrack, agents]
---

# Plan: LogMyTime-taken archiveren op basis van YouTrack

Vastgelegd op 20-11-2026.

## Probleem

Af en toe loop ik de actieve taken in LogMyTime met de hand langs en archiveer ik de taken waarvan
het issue in YouTrack is afgesloten. Dat is suf handwerk. Elke taak begint met het issue-ID
(`PKP-890 …`, zie [[urenregistratie]]), dus de koppeling met YouTrack ligt er al.

## Feiten (20-11-2026)

- LogMyTime heeft 7367 taken, waarvan 246 actief. Archiveren heet in de API `Active = false` (op de
  website "abgelegt"). Taken hangen niet aan een project.
- Van de 246 actieve taken hebben er 243 een issue-ID vooraan, allemaal uniek. Zonder ID:
  `Reistijd`, `Reistijd OV` en `Zakelijk overig`. Die blijven altijd actief.
- Steekproef van 30 actieve taken: 25 issues staan in YouTrack op opgelost (`Done`), 5 staan nog open
  (zoals PKI-587 *Monthly systems check* en PKI-983, allebei `In Progress`).
- Wijzigen gaat met `MERGE /V1/Api.svc/Tasks(<id>)` met alleen de gewijzigde velden in de body,
  antwoord `204 No Content`. Niet `PUT`: dat zet weggelaten velden terug op hun standaardwaarde.
  Schrijven mag alleen met een admin-account of met uitgebreide gebruikersrechten waarvoor schrijven
  aanstaat. Mijn sleutel mag schrijven (getest op 20-11-2026, zie `Bevindingen`).
- Limiet: 500 requests per 24 uur, dus één `MERGE` per taak telt mee. De eerste keer gaat het om
  ongeveer 200 taken, en de uren-scripts gebruiken dezelfde limiet.
- Archiveren is terug te draaien (`Active = true`). De time entries blijven bestaan.

## Beslissingen

- **Criterium:** een taak wordt gearchiveerd als het issue in YouTrack is opgelost (`resolved` is
  gezet), dat al minstens **7 dagen** zo is, en er in die 7 dagen geen tijd meer op de taak is gelogd.
  Zo blijft het naloggen na het sluiten (review, uitrol) mogelijk.
- **Moment:** elke maandagochtend, na de zondagse weekplanning.
- **Uitvoering:** een script met een plan-modus en `--uitvoeren`, zoals `uren_naar_youtrack.py`,
  dat ook autonoom onder launchd draait als agent op het [[agents-dashboard]]. Deterministisch: geen
  sessie met een model nodig.
- **Naam van de agent:** Fien, van *finished*: ze ruimt op wat af is. Gekozen door Martijn uit een
  prijsvraag met Claude als enige deelnemer (de andere kandidaten waren Archie, Bas en Toby).
- **Heropend issue:** niets doen. Wordt een issue heropend, dan zet ik de taak zelf terug in
  LogMyTime.

## Ontwerp

- `scripts/logmytime.py` krijgt een schrijffunctie `merge(resource, id, velden)`. De docstring
  ("alleen lezen") gaat mee.
- `token()` en `yt()` uit `uren_naar_youtrack.py` verhuizen naar een gedeelde `scripts/youtrack.py`,
  zoals `logmytime.py` dat al is voor LogMyTime.
- Nieuw script `scripts/logmytime_taken_archiveren.py [--uitvoeren] [--max N]`:
  1. haalt de actieve taken op (`$filter=Active eq true`, één request)
  2. haalt de time entries van de afgelopen 7 dagen op en houdt bij welke taken nog tijd hebben
  3. vraagt in YouTrack de issues op, in porties met `issue id: A, B, …`, met `resolved`
  4. per taak: `archiveren`, `wacht` (opgelost maar korter dan 7 dagen, of recent gelogd), `open`,
     `niet gevonden` (issue bestaat niet of is niet zichtbaar) of `geen ID` (de vaste lijst wordt
     stil overgeslagen)
  5. alleen met `--uitvoeren`: `MERGE` met `Active = false`, hooguit `--max` taken per run
     (standaard 100), zodat er altijd requests overblijven voor de uren-scripts
- Agent: een runner schrijft per run een run-notitie volgens [[agent-runs]] (gearchiveerd, wachtend
  en `niet gevonden` als aandachtspunten), een plist in `~/Library/LaunchAgents` en een notitie
  `gebieden/agents/fien.md`. Elke maandagochtend, met `interval` op 8 dagen voor `Stil`.

## Zo werken we dit af

Start in `~/vault` en zeg: "Doe de eerste open stap uit [[logmytime-taken-archiveren-plan]]". Aan
het eind van de sessie vink je de stap af, zet je onder `Bevindingen` wat anders liep, en pas je
de latere stappen aan als dat nodig is.

## Voortgang

- [x] 1. **Schrijfrecht testen.** Eén taak waarvan het issue duidelijk klaar is, met `MERGE`
  archiveren en controleren in LogMyTime. Dan `uren.py` draaien en kijken of de totalen gelijk
  blijven (de time entries van een gearchiveerde taak moeten blijven meetellen). Mag de sleutel niet
  schrijven, dan eerst de rechten in LogMyTime aanpassen (Martijn).
- [x] 2. **Gedeelde code.** `scripts/youtrack.py` maken, `uren_naar_youtrack.py` erop overzetten en
  controleren dat de uitvoer voor een gevalideerde dag gelijk blijft. `merge()` in `logmytime.py`.
- [ ] 3. **Script bouwen**, alleen met de plan-modus. De uitvoer naast een handmatige blik op een paar
  taken leggen.
- [ ] 4. **Eerste run met de hand.** Martijn bekijkt het plan, daarna `--uitvoeren`. Met `--max 100`
  verspreid over twee dagen.
- [ ] 5. **Agent Fien.** Runner, run-notitie, plist, agentnotitie, en controleren
  dat het dashboard hem toont. Een paar weken laten draaien.
- [ ] 6. **Afronden** volgens het onderhoud in [[vault-roadmap]]: map met documentatie, beslissingen
  en logboek, en een regel onder `Afgerond`.

## Bevindingen

- **Stap 1 (20-11-2026):** de sleutel mag schrijven. `MERGE /Tasks(436168)` met `{"Active": false}`
  gaf `204`, en daarna gaf de API `Active: False` terug voor *PKI-1111 Test data renewal* (opgelost op
  20-10, 2 time entries, 2,3 u). De uitvoer van `uren.py --details` was voor en na byte voor byte
  gelijk: de time entries van een gearchiveerde taak tellen dus mee. De taak blijft gearchiveerd.
- `uren_naar_youtrack.py` roept `main()` aan zonder `if __name__ == '__main__'`: wie het importeert,
  draait het plan voor vandaag (alleen lezen, maar wel LogMyTime- en YouTrack-requests). Lost zichzelf
  op in stap 2, als `token()` en `yt()` naar `youtrack.py` verhuizen; zet de guard er dan wel bij.
- **Stap 2 (20-11-2026):** `scripts/youtrack.py` heeft `token()`, `yt()` en ook `ISSUE_ID` (het
  archiveerscript heeft die regex ook nodig). `uren_naar_youtrack.py` gebruikt de module en heeft nu
  de `__main__`-guard. De plan-uitvoer voor 19-11 was voor en na byte voor byte gelijk. `merge()` in
  `logmytime.py` getest door `Active = false` nog eens te zetten op taak 436168 (al gearchiveerd):
  geen fout, `Active: False`. `youtrack_command.py`, `youtrack_edit_comment.py` en
  `staging_overzicht.py` hebben nog een eigen `token()`. Bewust zo gelaten: de eerste twee draaien
  met `python3 -I`, en dan staat de map van het script niet op `sys.path`.
