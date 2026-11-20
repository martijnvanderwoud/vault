---
description: Overzicht van alle plannen in de vault (lopend, afgerond) en de backlog van ideeën
tags: [vault, roadmap]
---

# Roadmap van de vault

Overzicht van alle plannen, niet de plannen zelf. Elk lopend plan heeft een eigen notitie met
stappen, voortgang en bevindingen. Hier staat per plan alleen de stand en de volgende stap. Zie [[vault-doel]] voor
het waarom en [[vault-beslissingen]] voor de gemaakte keuzes.

Bijgewerkt op 20-11-2026.

## Lopend

| Plan | Stand | Volgende stap |
|---|---|---|
| [[release-candidates-staging]] | Alle stappen gescript, eerste uitrol op 13-11 (infra-PR #999), skill `staging-release-candidates` | Testen bij de volgende uitrol, met de skill |
| [[interview-voortgang]] (vault vullen) | Blok 1 t/m 4 klaar op 15-11: [[over-martijn]], [[werkafspraken]], [[schrijfstem]] | Weekschema loopt via [[weekplanning-plan]]; daarna de kennisnotities in de volgorde uit de interviewnotitie |
| [[weekplanning-plan]] | Alle stappen klaar op 19-11 (skill `/weekplanning`, weektarget en ruimte); wacht op de eerste echte zondagrun | Zo 22-11 de week plannen met de skill, daarna afronden naar `gebieden/weekplanning/` |
| [[hardlopen-plan]] | Afgesplitst van [[weekplanning-plan]] op 19-11, nog niet begonnen | Stap 1: gelopen trainingen importeren (eerst een Garmin-export van week 47) |
| [[gmail-zakelijk-concepten-plan]] | Vastgelegd 17-11, nog niet begonnen | Stap 1: voorwerk in de Google Cloud-console (Martijn) |
| [[logmytime-taken-archiveren-plan]] | Vastgelegd 20-11, nog niet begonnen | Stap 1: testen of de LogMyTime-sleutel taken mag archiveren |

## Afgerond

| Wat | Klaar | Waar |
|---|---|---|
| Fundament: mappen, indexen, hooks, GitHub | 7-11-2026 | [[vault-beslissingen]] |
| Urenstand uit LogMyTime, skill `/uren`, Excel uitgefaseerd | 12-11-2026 | [[urenregistratie]], [[uren-overzicht]] |
| Uren naar YouTrack, skill `/uren-naar-youtrack` | 12-11-2026 | [[urenregistratie]] |
| Dependabot-routine als skill `/dependabot-routine` | 9-11-2026, testruns t/m 10-11 | [[dependabot-routine]] |
| Agents-dashboard: één statusvorm voor alle agents, een watcher onder launchd die het dashboard ververst, `issue_state` bijhoudt en meldt | 19-11-2026 (stappen op 18-11, Ward sloot aan zonder wijzigingen) | [[agents-dashboard]] |
| Debbie: de Dependabot-routine autonoom in alle 21 repo's, onder launchd, op het agents-dashboard | 19-11-2026, na een hele ronde (week 47) | [[dependabot-routine]], [[debbie]] |
| Analyse AI-Brein Bootcamp, context- en grenzenlaag van de vault | 15-11-2026 | [[vault-leren-van-bootcamp]] |
| Hostingfactuur FLOW via Acumulus-API, skill `/hostingfactuur-flow` (PDF nog met de hand bijvoegen) | 17-11-2026, eerste factuur 20260084 | [[hosting-transip]], [[acumulus]] |
| Ward: elke ochtend de hosts van Pompkracht controleren (eerst AVX-512 VBMI voor Java4Shell), melden bij een verandering, op het agents-dashboard | 18-11-2026 (PKI-1133) | [[ward-bewaking]] |

Werkwijze om een terugkerende taak uit een project om te zetten in een skill:
[[vault-skill-maken-vanuit-project]].

## Backlog / ideeën (nog niet beslist)

- **Uren, vervolg:** stopwatch starten/stoppen via de API (`/start PKP-123`), met afronding op
  3 min. Eerst checken of de API een starttijd accepteert.
- **Nirvana** (GTD-taakbeheer): community-MCP `@sgoettschkes/nirvana-mcp`, 17 leestools, schrijven
  nog niet. Gebruikt de ongedocumenteerde API; login via MD5 van wachtwoord → langlevend token.
  Eerst afwegen of ik dat token aan een third-party package geef. Gebruik: ochtendoverzicht,
  weekly review.
- **TrainingPeaks en coach:** uitzoeken of intervals.icu (open API) naar TrainingPeaks kan schrijven, of
  hoe ik anders met Nils (Loopwijzer) kan samenwerken zonder handwerk in TrainingPeaks.
- **TrainingPeaks:** trainingen klaarzetten is veel handwerk. Automatiseren via browser, Playwright
  of interne API is **verboden** door de Terms of Use (art. 13, 18, 23; versie 28-7-2026).
  Officiële API alleen voor goedgekeurde ontwikkelaars. Opties: berekening in de vault die
  trainingen invoerklaar opmaakt; of platform met open API (bv. intervals.icu). Nog uitzoeken.
- **Lijsten:** boeken om te lezen, bewaarplekken ("waar ligt wat").
- **Kennisnotities en plannen uit het interview** (Pompkracht, hardlopen, privéfinanciën, Nirvana,
  vloerverwarming, berichtenkanalen, website): volgorde in [[interview-voortgang]].
- **HTML-dashboard:** data in een los JS-bestand naast statische HTML, zie [[vault-leren-van-bootcamp]].
- **Debbie op Sonnet:** Sonnet proberen op de npm-repo's (`--model` van de runner) en de verslagen
  en kosten vergelijken met Opus (`kosten`, `beurten` en `geweigerd` in de run-notities). Zie
  [[dependabot-routine-beslissingen]].
- **Semantisch zoeken** zodra grep tekortschiet.
- **Push** automatiseren (cron of hook) als ik vertrouwd ben met de flow.

## Onderhoud

- Nieuw plan: eigen notitie met voortgang (zoals [[weekplanning-plan]]) en een regel onder
  `Lopend`.
- Plan klaar: regel naar `Afgerond`, en het plan wordt een eigen map met drie notities, zoals
  [[release-candidates-staging]] en [[ward-bewaking]]:
  - `<onderwerp>.md`: de documentatie, wat het doet en hoe ik het gebruik, leesbaar voor mensen
  - `<onderwerp>-beslissingen.md`: de beslissingen met de reden erachter
  - `<onderwerp>-logboek.md`: hoe het chronologisch verliep, met de stappen en bevindingen
  De plannotitie verdwijnt. Wat het proces later oplevert (uitrolnotities, meldingen) komt in een
  submap van dezelfde map, zodat alles over één onderwerp bij elkaar staat.
- Idee wordt een plan: weg uit de backlog, regel onder `Lopend`.
