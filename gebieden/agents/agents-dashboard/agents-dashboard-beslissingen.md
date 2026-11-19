---
description: Beslissingen achter het agents-dashboard en de watcher, met de reden erachter
tags: [agents, dashboard]
cssclasses: [wide-page]
---

# Agents-dashboard: beslissingen

Waarom [[agents-dashboard]] werkt zoals het werkt. Hoe het zo gekomen is, staat in
[[agents-dashboard-logboek]].

## Opzet

- **Eén statusvorm voor alle agents.** Elke run is een notitie met vaste frontmatter
  ([[agent-runs]]). Watcher en dashboard kennen alleen die velden, niet de agents zelf. De toets:
  Ward sloot op 18-11 aan zonder één wijziging aan watcher of dashboard.
- **De runner van een agent schrijft de status, niet het model.** Zo blijft een vastgelopen run
  zichtbaar als `failed`. Komt uit het plan van Debbie en geldt voor elke agent.
- **Een eigen watcher, los van de runners.** De runner van Debbie draait elk half uur; hing het
  dashboard daaraan, dan liep het tot een half uur achter, bijvoorbeeld als ik een issue op `Done`
  zet. De watcher draait altijd (launchd `KeepAlive`).
- **Polling met de standaardbibliotheek,** elke 2 seconden de `mtime` van de mappen en notities.
  Geen `fswatch` of andere dependency; het kost een paar `stat`-aanroepen per tik. Daarnaast elke
  minuut, omdat `Stil` en de grens van 7 dagen van de tijd afhangen.
- **YouTrack pollen, geen webhook.** Een webhook vraagt een server die YouTrack kan bereiken. Elke 3
  minuten de state van de open issues ophalen kost geen modelbeurten.
- **De watcher doet wat voor alle agents geldt** (melden, `issue_state`, afgebroken runs op
  `failed`); wat specifiek is, blijft in de runner, zoals de overslaglogica en `verslag_na()` van
  Debbie.

## Weergave

- **Een gegenereerde notitie, geen plugin.** Kleur via callouts (`[!danger]`, `[!warning]`,
  `[!info]`, `[!success]`). Er draait geen JavaScript in de vault, en ik kan het dashboard zelf
  genereren en nalezen.
  - Dataview en Datacore vielen af: een community-plugin met volledige rechten, in een vault waarin
    agents tekst uit niet te vertrouwen bronnen zetten (CI-logs, uitvoer van het model), en een API
    die nog verandert.
  - Bases viel af: het blijft een tabel, zonder een opvallend blok voor wat aandacht nodig heeft. De
    base van Debbie is weggehaald, niet bewaard als geschiedenis: kosten, beurten en `geweigerd`
    staan in de run-notities zelf.
  - AgentHub is een chat-zijbalk voor interactieve agents, geen statusoverzicht. De vier
    toestanden (bezig, wacht op jou, mislukt, klaar) en de melding bij "wacht op jou" zijn
    overgenomen.
- **Alles uit een run-notitie is platte tekst.** Op één regel, met een backslash voor de tekens die
  Markdown opmaken, en de `:` zodat een kale URL geen link wordt. Wikilinks en issue-links alleen
  bij een veilige naam of een geldig ID. Een agent kan het dashboard zo nooit opmaken.
- **Per onderwerp alleen de laatste run,** bepaald door het script zelf, niet door een vlag in de
  notities.
- **Een agent zonder runs blijft staan** (`Geen runs.`), en een agent die te lang stil is, komt
  onder `Stil` (`interval` in de notitie per agent). Ook stilte is een signaal.
- **Alleen schrijven als de inhoud verandert,** zonder de regel `Bijgewerkt` mee te tellen. Anders
  herlaadt Obsidian elke paar seconden.
- **`dashboard.md` niet in git.** Het is afgeleid, net als `index.md`, maar wijzigt bij elke run.

## Robuustheid

- **Atomair schrijven** (tijdelijk bestand met een punt ervoor, dan `rename`), omdat runner,
  watcher en Obsidian dezelfde notities aanraken. De watcher schrijft nooit een notitie van een
  levende `running`-run, en leest een notitie opnieuw vlak voordat hij hem schrijft.
- **De module leest ook wat Obsidian schrijft** (zonder quotes, blok-strings, lege velden). Een leeg
  veld is een lijst als het in `lijsten` staat, anders `""`. PyYAML zit niet in de systeem-Python,
  vandaar een eigen parser.
- **Velden die een schrijver niet kent, blijven bewaard,** in de volgorde van de notitie. Een vaste
  volgorde in de module zou elke notitie omgooien die de watcher schrijft.
- **Een afgebroken run wordt pas na 15 seconden `failed`.** Zo krijgt de runner de tijd om na het
  einde van het proces zijn eindstatus te schrijven, zonder een valse melding. `proces` in de
  notitie per agent zegt hoe het proces heet, zodat een hergebruikt `pid` niet als levend telt.
- **`resume` zet de runner al bij de start,** want de watcher kent het commando niet. Een run die hij
  op `failed` zet, houdt het zo.
- **Een stille watcher moet opvallen,** ook al kan het dashboard dat zelf pas bij de volgende
  generatie tonen. Daarom een heartbeat buiten de vault (elke 2 seconden een gewijzigd bestand in de
  vault is ruis voor Obsidian en git), een waarschuwing op het dashboard, en een melding van de
  runner van Debbie, pas na haar `opruimen()` zodat een herstart geen valse melding geeft.
- **Het dashboard draait als subproces,** en elke taak in de lus heeft een eigen `try`. Een fout bij
  YouTrack of in het script blokkeert de rest niet.
- **Bij de eerste start zonder `gemeld.json` alleen de stand vastleggen,** anders kwamen er 28
  meldingen tegelijk.

## Voor later

- Een rijkere weergave (eigen plugin, Datacore) kan op dezelfde run-notities, als de gegenereerde
  notitie te sober blijkt.
- Een HTML-interface naast Obsidian: een pagina als `file://` mag geen lokale bestanden lezen, dus de
  watcher genereert de pagina met de gegevens erin, of draait een kleine lokale webserver. Knoppen
  die iets doen, zoals Hervatten, vragen een afgeschermde server (alleen `localhost`, een geheim
  token). Staat in de backlog van [[vault-roadmap]].
