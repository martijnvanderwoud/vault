---
description: Overzicht van alle plannen in de vault (lopend, afgerond) en de backlog van ideeën
tags: [vault, roadmap]
---

# Roadmap van de vault

Overzicht van alle plannen, niet de plannen zelf. Elk plan heeft een eigen notitie met stappen,
voortgang en bevindingen. Hier staat per plan alleen de stand en de volgende stap. Zie [[vault-doel]] voor
het waarom en [[vault-beslissingen]] voor de gemaakte keuzes.

Bijgewerkt op 12-11-2026.

## Lopend

| Plan | Stand | Volgende stap |
|---|---|---|
| [[dependabot-routine-autonoom-plan]] (Debbie) | Stap 1 t/m 9 klaar; alle 21 repo's staan sinds 11-11 op autonoom | Stap 10: controlepunt na donderdag 19-11, alle runs van week 47 nakijken in het dashboard |
| [[release-candidates-staging]] | Stap 1 (overzicht) klaar; stap 2 (release branches) bezig: `ats` klaar, `insights` lokaal klaar | `insights` pushen, daarna per soort repo met de hand en dan een script |
| [[agents-dashboard-plan]] | Vastgelegd 11-11, nog niet begonnen | Stap 1: statusvorm en gedeelde module |

## Afgerond

| Wat | Klaar | Waar |
|---|---|---|
| Fundament: mappen, indexen, hooks, GitHub | 7-11-2026 | [[vault-beslissingen]] |
| Urenstand uit LogMyTime, skill `/uren`, Excel uitgefaseerd | 12-11-2026 | [[urenregistratie]], [[uren-overzicht]] |
| Uren naar YouTrack, skill `/uren-naar-youtrack` | 12-11-2026 | [[urenregistratie]] |
| Dependabot-routine als skill `/dependabot-routine` | 9-11-2026, testruns t/m 10-11 | [[dependabot-routine]] |

Werkwijze om een terugkerende taak uit een project om te zetten in een skill:
[[vault-skill-maken-vanuit-project]].

## Backlog / ideeën (nog niet beslist)

- **Uren, vervolg:** stopwatch starten/stoppen via de API (`/start PKP-123`), met afronding op
  3 min. Eerst checken of de API een starttijd accepteert.
- **Nirvana** (GTD-taakbeheer): community-MCP `@sgoettschkes/nirvana-mcp`, 17 leestools, schrijven
  nog niet. Gebruikt de ongedocumenteerde API; login via MD5 van wachtwoord → langlevend token.
  Eerst afwegen of ik dat token aan een third-party package geef. Gebruik: ochtendoverzicht,
  weekly review.
- **TrainingPeaks:** trainingen klaarzetten is veel handwerk. Automatiseren via browser, Playwright
  of interne API is **verboden** door de Terms of Use (art. 13, 18, 23; versie 28-7-2026).
  Officiële API alleen voor goedgekeurde ontwikkelaars. Opties: berekening in de vault die
  trainingen invoerklaar opmaakt; of platform met open API (bv. intervals.icu). Nog uitzoeken.
- **Lijsten:** boeken om te lezen, bewaarplekken ("waar ligt wat").
- **Semantisch zoeken** zodra grep tekortschiet.
- **Push** automatiseren (cron of hook) als ik vertrouwd ben met de flow.

## Onderhoud

- Nieuw plan: eigen notitie met voortgang (zoals [[agents-dashboard-plan]]) en een regel onder
  `Lopend`.
- Plan klaar: regel naar `Afgerond`. Stappen en bevindingen blijven in de notitie van het plan.
- Idee wordt een plan: weg uit de backlog, regel onder `Lopend`.
