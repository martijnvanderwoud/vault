---
description: De afspraak voor run-notities van alle autonome agents - velden, statussen, wanneer iets op mij wacht en wie schrijft
tags: [agents, afspraak]
---

# Run-notities van agents

Elke run van een autonome agent is één notitie met vaste frontmatter. Het dashboard en de watcher
kennen alleen deze velden, niet de agents zelf. Een nieuwe agent sluit aan door zich hieraan te
houden en een notitie `gebieden/agents/<agent>.md` te krijgen (zie onderaan). Plan:
[[agents-dashboard-plan]].

## Velden

| Veld | Betekenis |
| --- | --- |
| `agent` | naam van de agent, zoals `debbie` |
| `onderwerp` | waar de run over gaat; per agent één run per onderwerp tegelijk (bij Debbie het project, de repo) |
| `status` | `running`, `paused` (wacht op mij), `done`, `failed`, `resolved` (door mij vrijgegeven) |
| `started`, `ended` | ISO-tijd met tijdzone, zoals `2026-11-18T12:25:20+01:00` |
| `issue`, `issue_state` | optioneel: het issue, en de state zoals die het laatst gezien is |
| `reason`, `step` | bij `paused` en `failed`: waarom en waar |
| `aandacht` | lijst met punten waar ik iets mee moet, ook bij `done` |
| `resume` | commando om verder te gaan |
| `pid` | alleen bij `running`: het proces dat de run doet |
| `kosten`, `beurten`, `model`, `log` | optioneel |

Eigen velden van een agent mogen erbij, zoals `prs` en `session_id` bij Debbie. Een leeg veld is
`""`, een lege lijst `[]`.

## Wanneer iets op mij wacht

- **Afgehandeld** is een run waarvan het issue op `Done` staat, of die op `resolved` staat (voor
  een run zonder issue). Een run zonder aandachtspunten zet zijn issue zelf op `Done`.
- **Wacht op mij** is een run die niet `running` is, niet afgehandeld, en `paused` of `failed` is
  of aandachtspunten heeft.
- Per onderwerp telt alleen de laatste run (de laatste `started`).

## Wie schrijft

- De runner van de agent schrijft de status, niet het model. Zo blijft een vastgelopen run
  zichtbaar als `failed`.
- Lezen en schrijven gaat via `scripts/agentruns.py`: `notitie_lezen()`, `notitie_schrijven()`,
  `laatste_per_onderwerp()`, `proces_leeft()` en `agents()`. Schrijven gaat atomair (tijdelijk
  bestand en `rename`), omdat runner, watcher en Obsidian dezelfde notities aanraken.
- Obsidian schrijft de hele frontmatter opnieuw als ik een property wijzig, zonder quotes en met
  blok-strings. De module leest beide vormen.
- Alleen notities met het juiste `agent`-veld zijn run-notities. Andere notities mogen in dezelfde
  map staan en worden nooit opnieuw geschreven.

## Notitie per agent

`gebieden/agents/<agent>.md`, met in de frontmatter:

- `runs`: de map met de run-notities, vanaf de vault, zoals `gebieden/werk/dependabot-runs`
- `lijsten`: optioneel, eigen velden die een lijst zijn (naast `aandacht`), zodat een lege lijst
  bij het opnieuw schrijven een lijst blijft
- `interval`: optioneel, de langste tijd tussen twee runs, zoals `8d`, `12h` of `30m`. Is er
  langer dan dat geen run begonnen en loopt er geen, dan zet het dashboard de agent onder `Stil`.

En in de tekst: wat de agent doet, waar zijn plan staat en hoe je een run hervat. De watcher
vindt de runmappen via deze notities, en het dashboard linkt ernaar.
