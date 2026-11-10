---
description: Huidige stand, volgende stap (vrije dagen als CSV, skill /uren) en backlog van de vault
tags: [vault, roadmap]
---

# Roadmap van de vault

Zie [[vault-doel]] voor het waarom en [[vault-beslissingen]] voor de gemaakte keuzes.

## Huidige stand (10-11-2026)

- Structuur: `inbox/ dagboek/ gebieden/ lijsten/ data/ scripts/ .claude/skills/`, elke map een gegenereerde `index.md`.
- Hooks werken (getest): PostToolUse Write|Edit → index; SessionEnd → index + commit.
- `.gitignore` uitgebreid (secrets, `.claude/settings.local.json`, `.trash/`, Office-lockbestanden `~$*`).
- Gepusht naar GitHub.
- Daily notes: Obsidian staat ingesteld op `dagboek/` met formaat `YYYY/YYYY-MM-DD`.
- `data/declarabele-uren-2026.xlsx` staat in de vault als tussenoplossing (binair, slecht te diffen); toegevoegd op 7-11-2026.
- `scripts/uren.py` (10-11-2026) leest de uren uit de LogMyTime API en reproduceert de Excel-stand exact (gevalideerd per 10-11-2026). `LOGMYTIME_API_KEY` staat in `.env`.

## Volgende stap: vrije dagen en skill `/uren`

Details en achtergrond in [[urenregistratie]].

1. ~~`scripts/uren.py` (stdlib, alleen lezen) dat de Excel-stand reproduceert~~ (klaar 10-11-2026).
2. Gereserveerde vrije uren (Excel kolom J, K, L; nu 33,0 u nog gereserveerd) naar `data/vrije-dagen-2026.csv`, en `uren.py` laten tonen: vrij gereserveerd en het verschil met vrij over.
3. Skill `/uren`.
4. Pas als de cijfers kloppen: Excel uitfaseren.

## Backlog / ideeën (nog niet beslist)

- **Uren, vervolg:** stopwatch starten/stoppen via API (`/start PKP-123`) met afronding op 3 min — eerst checken of de API een starttijd accepteert. Alternatief: tijd schrijven in YouTrack zelf (heeft time tracking + REST API).
- **Nirvana** (GTD-taakbeheer): community-MCP `@sgoettschkes/nirvana-mcp`, 17 leestools, schrijven nog niet. Gebruikt de ongedocumenteerde API; login via MD5 van wachtwoord → langlevend token. Eerst afwegen of ik dat token aan een third-party package geef. Gebruik: ochtendoverzicht, weekly review.
- **TrainingPeaks:** trainingen klaarzetten is veel handwerk. Automatiseren via browser, Playwright of interne API is **verboden** door de Terms of Use (art. 13, 18, 23; versie 28-7-2026). Officiële API alleen voor goedgekeurde ontwikkelaars. Opties: berekening in de vault die trainingen invoerklaar opmaakt; of platform met open API (bv. intervals.icu). Nog uitzoeken.
- **Lijsten:** boeken om te lezen, bewaarplekken ("waar ligt wat").
- **Semantisch zoeken** zodra grep tekortschiet.
- **Push** automatiseren (cron of hook) als ik vertrouwd ben met de flow.
