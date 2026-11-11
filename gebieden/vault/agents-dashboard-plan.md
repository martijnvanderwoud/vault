---
description: Plan voor één statusvorm voor al mijn autonome agents, een watcher die altijd draait en een dashboard in Obsidian
tags: [agents, dashboard, plan]
---

# Plan: agents-dashboard

Doel: in één notitie zie ik meteen wat er nu draait, wat er de afgelopen tijd is gebeurd en wat
op mij wacht, voor alle autonome agents in deze vault. Wat aandacht nodig heeft, valt op met een
kleur. Het dashboard loopt hooguit een paar seconden achter op de run-notities, en een paar
minuten op YouTrack.

Debbie ([[dependabot-routine-autonoom-plan]]) is de eerste agent. De volgende moet zich kunnen
aansluiten zonder dat de watcher of het dashboard verandert.

Vastgelegd op 2026-11-11, na stap 9 van het plan van Debbie.

## Zo werken we dit af

Elke stap is één losse sessie. Start in `~/vault` en zeg: "Doe de eerste open stap uit
[[agents-dashboard-plan]]". Aan het eind van de sessie:

- vink je de stap af in de voortgang hieronder
- zet je onder `Bevindingen` wat afweek van het plan of wat een latere stap verandert
- pas je latere stappen aan als dat nodig is

## Voortgang

- [ ] 1. Statusvorm en gedeelde module
- [ ] 2. Dashboard genereren
- [ ] 3. Watcher die altijd draait
- [ ] 4. Taken uit de runner naar de watcher
- [ ] 5. Opruimen

## Beslissingen

- **Eén statusvorm voor alle agents.** Elke run is een notitie met vaste frontmatter (zie stap 1).
  Watcher en dashboard kennen alleen die velden, niet de agents zelf.
- **De runner van een agent schrijft de status, niet het model.** Zo blijft een vastgelopen run
  zichtbaar als `failed`. Dit komt uit het plan van Debbie en geldt voor elke agent.
- **Een eigen watcher, los van de runners.** De runner van Debbie draait elk half uur. Hangt het
  dashboard daaraan, dan loopt het tot een half uur achter, bijvoorbeeld als ik een issue op
  `Done` zet. De watcher draait altijd (launchd `KeepAlive`), en ververst het dashboard zodra een
  run-notitie wijzigt.
- **Een gegenereerde notitie, geen plugin.** Kleur via callouts van Obsidian (`[!danger]`,
  `[!info]`, `[!success]`). Er draait geen JavaScript in de vault, en ik kan het dashboard zelf
  genereren en nalezen. Dataview en Datacore vielen af: een community-plugin met volledige rechten,
  in een vault waarin agents tekst uit niet te vertrouwen bronnen zetten (CI-logs, uitvoer van het
  model), en een API die nog verandert. Bases viel af omdat het een tabel blijft, zonder een
  opvallend blok voor wat aandacht nodig heeft. Gekeken naar AgentHub: dat is een chat-zijbalk voor
  interactieve agents, geen statusoverzicht. De vier toestanden per tab (bezig, wacht op jou,
  mislukt, klaar) en de melding bij "wacht op jou" heb ik overgenomen.
- **YouTrack pollen, geen webhook.** Een webhook vraagt een server die YouTrack kan bereiken. Elke
  paar minuten de state van de open issues ophalen via de REST-API kost geen modelbeurten.
- **Afgehandeld is: het issue staat op `Done`**, of de run staat op `resolved` als hij geen issue
  heeft. Een run zonder aandachtspunten zet zijn issue zelf op `Done`.

## Stappen

### 1. Statusvorm en gedeelde module

Doel: de afspraak staat vast, en Debbie gebruikt hem via een gedeelde module.

- De afspraak in `gebieden/agents/agent-runs.md`. Velden van elke run-notitie:

  | Veld | Betekenis |
  | --- | --- |
  | `agent` | naam van de agent, zoals `debbie` |
  | `onderwerp` | waar de run over gaat, per agent één run per onderwerp tegelijk (bij Debbie de repo) |
  | `status` | `running`, `paused` (wacht op mij), `done`, `failed`, `resolved` (door mij vrijgegeven) |
  | `started`, `ended` | ISO-tijd met tijdzone |
  | `issue`, `issue_state` | optioneel, het issue en de state zoals de watcher die het laatst zag |
  | `reason`, `step` | bij `paused` en `failed`: waarom en waar |
  | `aandacht` | lijst met punten waar ik iets mee moet, ook bij `done` |
  | `resume` | commando om verder te gaan |
  | `pid` | alleen bij `running`, het proces dat de run doet |
  | `kosten`, `beurten`, `model`, `log` | optioneel |

  Eigen velden van een agent mogen erbij, zoals `prs` bij Debbie. Een run waarvoor ik iets moet
  doen, is een run die niet `running` is, niet is afgehandeld, en `paused` of `failed` is of
  aandachtspunten heeft.
- Bij Debbie is `onderwerp` nu `repo`. Kies: hernoemen in de bestaande notities, of de module laat
  `repo` meetellen als `onderwerp`. De runner leest `repo` ook in zijn overslaglogica.
- Per agent een notitie in `gebieden/agents/<agent>.md`: wat hij doet, waar zijn run-notities staan
  (`runs: gebieden/werk/dependabot-runs`), waar zijn plan staat en hoe je hem hervat. De watcher
  vindt de mappen via deze notities, en het dashboard linkt ernaar.
- `scripts/agentruns.py`: lezen en schrijven van run-notities uit `dependabot_runner.py`
  (`notitie_lezen()`, `notitie_schrijven()`, de laatste run per onderwerp, controleren of een proces
  nog leeft). Schrijven gaat atomair (tijdelijk bestand en `rename`), want vanaf stap 4 schrijven
  runner en watcher in dezelfde notities.
- `dependabot_runner.py` gebruikt de module. De bestaande notities moeten ongewijzigd heen en terug
  gaan, ook na een bewerking in Obsidian.

Klaar als: de runner werkt zoals voorheen (`--dry-run` en één echte run) op de gedeelde module.

### 2. Dashboard genereren

Doel: `scripts/agent_dashboard.py` schrijft `gebieden/agents/dashboard.md` uit alle run-notities.

- Indeling, van boven naar beneden:
  - `> [!danger] Aandacht nodig (n)`: per run de agent, het onderwerp, wat er speelt (stap en reden,
    of de aandachtspunten), een link naar het issue en het commando om te hervatten. Staat er niets,
    dan `> [!success] Niets wacht op jou`.
  - `> [!info] Nu bezig`: agent, onderwerp en sinds wanneer.
  - `## Afgelopen 7 dagen`: per agent een tabel met de laatste run per onderwerp: status als icoon,
    wanneer, issue, kosten.
  - Onderaan: wanneer het dashboard is bijgewerkt.
- Per onderwerp alleen de laatste run. Het script bepaalt dat zelf, de vlag `laatste` uit stap 9 van
  Debbie is daarvoor niet nodig.
- Alles wat uit een run-notitie komt, is tekst: geen codeblokken, geen HTML, `|` en regeleinden
  ontsnappen. Een agent mag het dashboard zo nooit kunnen opmaken.
- Het bestand alleen schrijven als de inhoud verandert, en de regel `Bijgewerkt` daarbij niet
  meetellen. Anders herlaadt Obsidian elke paar seconden en ontstaan er lege commits.
- Bepaal of `dashboard.md` in git hoort. Het is afgeleid, net als `index.md`, maar wijzigt veel
  vaker. Voorstel: in `.gitignore`.
- Handmatig draaien en in Obsidian bekijken, ook met testnotities voor elke status.

Klaar als: het dashboard alle statussen goed laat zien en ik het overzichtelijk vind.

### 3. Watcher die altijd draait

Doel: het dashboard ververst binnen een paar seconden na een wijziging, zonder dat ik iets start.

- `scripts/agent_watcher.py`: kijkt elke paar seconden naar de `mtime` van de runmappen uit
  `gebieden/agents/*.md`. Wijzigt er iets, dan draait hij `agent_dashboard.py`. Polling met de
  standaardbibliotheek, zodat er geen `fswatch` of andere dependency nodig is. Kosten: een paar
  `stat`-aanroepen per tik.
- `~/Library/LaunchAgents/nl.crimsoncricket.agent-watcher.plist` met `KeepAlive` en `RunAtLoad`,
  zonder absolute paden, net als de runner van Debbie: `/bin/sh -c` met `$HOME`. Ik kopieer en laad
  hem zelf, Claude mag geen LaunchAgent installeren.
- Een watcher die stil is weggevallen, moet opvallen. De watcher schrijft een heartbeat (tijd in
  een bestand buiten de vault). Is die ouder dan een paar minuten, dan toont het dashboard bovenaan
  een waarschuwing. Die werkt dan wel pas bij de volgende generatie, dus ook de runner van Debbie
  controleert de heartbeat en stuurt een melding.
- Testen: een run-notitie wijzigen, met de hand en via Obsidian, en het dashboard binnen een paar
  seconden zien veranderen. De watcher stoppen (`kill`) en zien dat launchd hem opnieuw start.

Klaar als: de watcher onder launchd draait en het dashboard binnen enkele seconden ververst.

### 4. Taken uit de runner naar de watcher

Doel: wat niet specifiek is voor Debbie, doet de watcher, voor alle agents.

- `issue_state`: elke paar minuten, alleen voor runs die nog niet zijn afgehandeld. Een `paused`-
  of `failed`-run met een issue op `Done` zet de watcher op `done`. Nu doet `opruimen()` in de
  runner dat elk half uur.
- Een `running`-run waarvan het proces weg is, wordt `failed`. Ook dat zit nu in `opruimen()`.
- Meldingen in macOS bij de overgang naar `paused` of `failed`, of bij nieuwe aandachtspunten. De
  watcher onthoudt wat hij al gemeld heeft, zodat een herstart niet alles opnieuw meldt.
- Wat bij Debbie hoort, blijft in de runner: de overslaglogica, en een gepauzeerde run op `done`
  zetten zodra er een verslag van Debbie in het issue staat (`verslag_na()`).
- Runner en watcher schrijven in dezelfde notities. De watcher schrijft geen notitie van een run
  die `running` is met een levend proces, en leest een notitie opnieuw vlak voordat hij hem
  schrijft.

Klaar als: een issue op `Done` binnen een paar minuten op het dashboard te zien is, en een
afgebroken run binnen een paar seconden als `failed` verschijnt, zonder de runner.

### 5. Opruimen

- `dependabot-runs/dashboard.base` weghalen, of houden als geschiedenis met kosten (zie de
  vergelijking tussen Opus en Sonnet in het plan van Debbie).
- De vlag `laatste` uit de runner halen als de base weg is.
- Het plan van Debbie en `dependabot-routine.md` laten verwijzen naar het nieuwe dashboard.
- `gebieden/agents/` in de mapstructuur van `CLAUDE.md` zetten.

Klaar als: er één dashboard is en de oude onderdelen weg of bewust gebleven zijn.

## Open vragen

- Waar komt de tweede agent vandaan? Een tweede agent die zich aansluit zonder wijzigingen aan
  watcher of dashboard, is de echte toets van de statusvorm.
- Een rijkere weergave (eigen plugin, Datacore) kan later op dezelfde run-notities, mocht de
  gegenereerde notitie te sober blijken.
- Een HTML-interface naast Obsidian, in deze repo (bijvoorbeeld `scripts/agents-ui/`). Obsidian
  toont en indexeert `.html` standaard niet, en Sync neemt het niet mee. Twee punten:
  - Een pagina die je als `file://` opent, mag geen andere lokale bestanden lezen. Dus: de watcher
    genereert de pagina met de gegevens erin, of de watcher draait een kleine lokale webserver.
  - Knoppen die iets doen, zoals Hervatten, vragen die server, en die moet afgeschermd zijn
    (alleen `localhost`, een geheim token), anders kan een willekeurige website in mijn browser
    er commando's mee starten. Dat wordt een eigen stap.

## Bevindingen

Nog geen.
