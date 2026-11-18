---
description: Overzicht van alle plannen in de vault (lopend, afgerond) en de backlog van ideeën
tags: [vault, roadmap]
---

# Roadmap van de vault

Overzicht van alle plannen, niet de plannen zelf. Elk plan heeft een eigen notitie met stappen,
voortgang en bevindingen. Hier staat per plan alleen de stand en de volgende stap. Zie [[vault-doel]] voor
het waarom en [[vault-beslissingen]] voor de gemaakte keuzes.

Bijgewerkt op 18-11-2026.

## Lopend

| Plan | Stand | Volgende stap |
|---|---|---|
| [[dependabot-routine-autonoom-plan]] (Debbie) | Stap 1 t/m 9 klaar; alle 21 repo's staan sinds 11-11 op autonoom | Stap 10: controlepunt na donderdag 19-11, alle runs van week 47 nakijken op het agents-dashboard en in de run-notities |
| [[release-candidates-staging]] | Alle stappen gescript, eerste uitrol op 13-11 (infra-PR #999), skill `staging-release-candidates` | Testen bij de volgende uitrol, met de skill |
| [[agents-dashboard-plan]] | Stap 1 t/m 5 klaar (18-11): `scripts/agent_watcher.py` draait onder launchd, ververst `gebieden/agents/dashboard.md`, houdt `issue_state` bij en meldt; het oude `dashboard.base` is weg | Nakijken van stap 4 bij de eerste echte run van Debbie; daarna een tweede agent ([[ward-plan]]) |
| [[interview-voortgang]] (vault vullen) | Blok 1 t/m 4 klaar op 15-11: [[over-martijn]], [[werkafspraken]], [[schrijfstem]] | Weekschema loopt via [[weekplanning-plan]]; daarna de kennisnotities in de volgorde uit de interviewnotitie |
| [[weekplanning-plan]] | Stap 1 klaar op 15-11: `trainingsduur.py`, aannames nog te bevestigen | Stap 2: soorten dagen en regels als data |
| [[gmail-zakelijk-concepten-plan]] | Vastgelegd 17-11, nog niet begonnen | Stap 1: voorwerk in de Google Cloud-console (Martijn) |
| [[ward-plan]] (Ward) | Stap 1 t/m 5 klaar (18-11): launchd draait de runner elke dag om 9:00; Ward start alleen bij een verandering en staat met een run-notitie per check op het agents-dashboard | Echte run op de nieuwe code nakijken; stap 6: PKI-1132 bijwerken |

## Afgerond

| Wat | Klaar | Waar |
|---|---|---|
| Fundament: mappen, indexen, hooks, GitHub | 7-11-2026 | [[vault-beslissingen]] |
| Urenstand uit LogMyTime, skill `/uren`, Excel uitgefaseerd | 12-11-2026 | [[urenregistratie]], [[uren-overzicht]] |
| Uren naar YouTrack, skill `/uren-naar-youtrack` | 12-11-2026 | [[urenregistratie]] |
| Dependabot-routine als skill `/dependabot-routine` | 9-11-2026, testruns t/m 10-11 | [[dependabot-routine]] |
| Analyse AI-Brein Bootcamp, context- en grenzenlaag van de vault | 15-11-2026 | [[vault-leren-van-bootcamp]] |
| Hostingfactuur FLOW via Acumulus-API, skill `/hostingfactuur-flow` (PDF nog met de hand bijvoegen) | 17-11-2026, eerste factuur 20260084 | [[hosting-transip]], [[acumulus]] |

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
- **Semantisch zoeken** zodra grep tekortschiet.
- **Push** automatiseren (cron of hook) als ik vertrouwd ben met de flow.

## Onderhoud

- Nieuw plan: eigen notitie met voortgang (zoals [[agents-dashboard-plan]]) en een regel onder
  `Lopend`.
- Plan klaar: regel naar `Afgerond`. Stappen en bevindingen blijven in de notitie van het plan.
- Idee wordt een plan: weg uit de backlog, regel onder `Lopend`.
