---
description: Overdracht van het opzetgesprek (7-11-2026) — beslissingen, huidige stand, volgende stappen en backlog van de vault
tags: [vault, handoff]
---

# Handoff: opzet agentic OS (7 november 2026)

Samenvatting van een verkennend gesprek in Claude (chat) over het opzetten van deze vault.
Doel: hier verder werken met volledige context. Verwerk dit in blijvende notities (zie onderaan).

## Doel van de vault

Generieke omgeving voor dagelijkse werk- en privézaken, náást mijn bestaande ontwikkelworkflow
(die blijft zoals hij is: plan → YouTrack-issue → script met `claude -p` in een worktree).
Focus: terugkerende taken automatiseren (eerst urenregistratie), daarnaast kennis, lijsten
(boeken, bewaarplekken) en gedachten ordenen.

Uitgangspunt: klein beginnen, vanuit concrete use cases, niet vanuit architectuur.
Meeste waarde zit in skills en automations; Obsidian is visualisatie.

## Beslissingen en waarom

| Beslissing | Reden |
|---|---|
| Git + private GitHub-repo `vault` onder persoonlijk account | Versiebeheer is nodig omdat Claude ook fouten schrijft; privé-inhoud; verhuizen naar bedrijfsorganisatie kan later met één klik. Actions werkt ook op gratis plan. |
| Niet in Google Drive; map `~/vault` | `.git` in een sync-map raakt corrupt; Drive heeft geen echt versiebeheer. |
| Commit via **SessionEnd**-hook, niet Stop | Stop gaat na elk antwoord af → commit per beurt. SessionEnd één keer bij afsluiten; afgebroken sessies worden door de volgende `git add -A` meegenomen. |
| Hook pusht niet | Bewust handmatig pushen. Let op: `git revert` haalt een geheim niet uit de history; alleen `reset`/`amend` vóór push. Check met `git log origin/main..HEAD -p`. |
| Indexen deterministisch via `scripts/build_index.py` | LLM vergeet indexen bij te werken. Script draait na Write/Edit (PostToolUse) en vóór elke commit (SessionEnd), zodat ook Bash-wijzigingen en handmatige Obsidian-edits meekomen. |
| Cijfers altijd via scripts | Uren/bedragen nooit door LLM laten rekenen. |
| `.obsidian/` in git, behalve `workspace*.json` | Instellingen reproduceerbaar; workspace verandert bij elke klik. Bij community-plugins `data.json` controleren op tokens. |
| Semantisch zoeken (embeddings) nog niet | Afgeleide data, later toe te voegen zonder herstructurering (bv. `qmd` via MCP). Grep/glob volstaat voorlopig. Voorbereiden door: één onderwerp per notitie, `description` in frontmatter, alles als tekst (ook samenvatting van pdf's), stabiele bestandsnamen, index in `.search-index/` (genegeerd). |
| Vault doorontwikkelen vanuit sessies in de vault zelf | Claude ziet hier de echte bestanden en kan testen. |
| Guardrails liefst technisch afdwingen | Permissies in `.claude/settings.json` of in scripts zijn sterker dan een zin in CLAUDE.md. |
| CLAUDE.md klein houden | Wordt elke sessie volledig geladen; persoonlijke context in aparte notities waarnaar verwezen wordt. |

## Huidige stand

- Structuur: `inbox/ dagboek/ gebieden/ lijsten/ data/ scripts/ .claude/skills/`, elke map een gegenereerde `index.md`.
- Hooks werken (getest): PostToolUse Write|Edit → index; SessionEnd → index + commit.
- `.gitignore` uitgebreid (secrets, `.claude/settings.local.json`, `.trash/`, Office-lockbestanden `~$*`).
- Gepusht naar GitHub.
- `data/declarabele-uren-2026.xlsx` staat in de vault (tussenoplossing; binair, slecht te diffen).

## Volgende stap: urenstand via LogMyTime API

Ik registreer tijd in LogMyTime (stopwatch per YouTrack-issue; tijden altijd **naar beneden
afgerond op 3 minuten** = 0,05 u). Dagelijks werk ik de Excel bij vanuit de LogMyTime-export.

**Excel-logica** (`declarabele-uren-2026.xlsx`, Blad1):
- Target = werkdagen sinds 1-1 × uren per weekdag: ma 6,5 / di 6,5 / wo 4,5 / do 6,25 / vr 4,25 (28 u/week).
- Declarabel = cumulatief per klant (Pompkracht, Construct), handmatig overgenomen.
- Vrij opgenomen = target − declarabel. Vrij-budget = 196 u/jaar (28 × 7).
- Gereserveerde vrije uren: lijst in kolom J (omschrijving), K (nog gereserveerd), L (gepland).
- Validatiepunt: stand per 6-11-2026: Pompkracht 1079,65 u, Construct 0,55 u.

**LogMyTime API:**
- Sleutel: beheeromgeving → "Eigenes Profil bearbeiten" → "Neuen API-Schlüssel generieren"; in `.env` als `LOGMYTIME_API_KEY`.
- Base URL `https://api.logmytime.de/V1/Api.svc` (OData). Auth: header `X-LogMyTimeApiKey` (of basic auth met sleutel als wachtwoord).
- Resources o.a. `TimeEntries`, `Projects`, `Tasks`, `Clients`, `Absences`, `Stopwatch` (starten/stoppen/opvragen).
- Docs: https://www.logmytime.de/Api/Grundlagen, /Api/Zeiteintraege, /Api/Httpxmljson, /Api/Stoppuhr, /Api/Requestgrenzen
- Export-observaties: issuenummer zit alleen in begin van taaknaam (`PKP-890 …`), kolom `issue_id` is leeg; taaknamen afgekapt op ~100 tekens.

**Plan:** `scripts/uren.py` (stdlib, alleen lezen) dat de Excel-stand reproduceert (`--tot 2026-11-06`),
gereserveerde vrije dagen naar `data/vrije-dagen-2026.csv`, daarna skill `/uren`.
Pas als de cijfers kloppen: Excel uitfaseren.

## Backlog / ideeën (nog niet beslist)

- **Uren, vervolg:** stopwatch starten/stoppen via API (`/start PKP-123`) met afronding op 3 min — eerst checken of de API een starttijd accepteert. Alternatief: tijd schrijven in YouTrack zelf (heeft time tracking + REST API).
- **Nirvana** (GTD-taakbeheer): community-MCP `@sgoettschkes/nirvana-mcp`, 17 leestools, schrijven nog niet. Gebruikt de ongedocumenteerde API; login via MD5 van wachtwoord → langlevend token. Eerst afwegen of ik dat token aan een third-party package geef. Gebruik: ochtendoverzicht, weekly review.
- **TrainingPeaks:** trainingen klaarzetten is veel handwerk. Automatiseren via browser, Playwright of interne API is **verboden** door de Terms of Use (art. 13, 18, 23; versie 28-7-2026). Officiële API alleen voor goedgekeurde ontwikkelaars. Opties: berekening in de vault die trainingen invoerklaar opmaakt; of platform met open API (bv. intervals.icu). Nog uitzoeken.
- **Lijsten:** boeken om te lezen, bewaarplekken ("waar ligt wat").
- **Semantisch zoeken** zodra grep tekortschiet.
- **Push** automatiseren (cron of hook) als ik vertrouwd ben met de flow.

## Hoe deze handoff verwerken

Verwerk dit bestand in blijvende notities volgens de vault-conventies, bijvoorbeeld:
- `gebieden/vault/beslissingen.md` — de beslissingen-tabel
- `gebieden/vault/roadmap.md` — volgende stap + backlog
- `gebieden/werk/urenregistratie.md` — LogMyTime-werkwijze, Excel-logica, API-gegevens
Verwijs vanuit CLAUDE.md alleen kort naar `gebieden/vault/`. Verwijder daarna dit handoff-bestand.
