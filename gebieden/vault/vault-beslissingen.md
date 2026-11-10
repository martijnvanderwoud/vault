---
description: Beslissingen over de opzet van de vault (git, hooks, indexen, zoeken) met de reden erachter
tags: [vault, beslissingen]
---

# Beslissingen over de vault

Opgesteld tijdens het opzetgesprek van 7-11-2026. Context in [[vault-doel]], vervolg
in [[vault-roadmap]].

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
| Notitienamen met voorvoegsel per gebied (`vault-…`) | Algemene namen als `beslissingen.md` geven dubbelzinnige `[[links]]` zodra een ander gebied dezelfde naam gebruikt. |
| Urenscript haalt elke run alle uren van de periode op, geen incrementele cache (10-11-2026) | Eén klein request (`$filter` + `$select`, ~3 requests totaal, limiet 500 per dag). Incrementeel via `LastChangeTime` mist verwijderde entries, waardoor een totaal stil fout kan zijn. Alleen afgesloten maanden cachen kan later als het te zwaar wordt. |
| Urenscript rondt niets af (10-11-2026) | Ik rond zelf al af bij het loggen (3 minuten); het script telt `DurationSeconds` op. |
| Uren van projecten zonder klant tellen als niet-declarabel (10-11-2026) | Het LogMyTime-project "Niet declarabel" heeft geen klant en wordt in de Excel ook niet meegeteld. |
