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

- [x] 1. Statusvorm en gedeelde module (18-11)
- [x] 2. Dashboard genereren (18-11)
- [x] 3. Watcher die altijd draait (18-11)
- [x] 4. Taken uit de runner naar de watcher (18-11)
- [x] 5. Opruimen (18-11)

Nog nakijken uit stap 1. Dit blokkeert stap 2 niet: het dashboard leest alleen notities via de
module, en dat is getest. Het gaat om de runner van Debbie zelf.

- [x] De eerste runner-tik onder launchd op de nieuwe code (vanaf 14:03 op 18-11):
  `sed -n '/^-- 2026-11-18T14:/,$p' ~/dependabot-runs/.logs/runner.log` toont de projecten
  zonder traceback. Gecontroleerd: de tikken van 14:03 en 14:33 liepen goed.
- [x] De eerste echte run van Debbie op de module (bij de volgende Dependabot-PR's): de nieuwe
  run-notitie heeft `onderwerp` en geen `repo`, en er staan geen `.tmp`-bestanden in
  `gebieden/werk/dependabot-runs/`. Gecontroleerd op `2026-w47-portal` (18-11 14:33): klopt.

Nog nakijken uit stap 3:

- [x] Een property van een run-notitie wijzigen in Obsidian en het dashboard binnen een paar
  seconden zien veranderen. Gecontroleerd op 18-11 met een testnotitie: `status` op `resolved` in
  Obsidian (frontmatter zonder quotes opnieuw geschreven) gaf binnen seconden ☑️ op het dashboard.

Nog nakijken uit stap 4:

- [ ] De eerste runner-tik onder launchd op de nieuwe code (vanaf 15:33 op 18-11):
  `sed -n '/^-- 2026-11-18T15:3/,$p' ~/dependabot-runs/.logs/runner.log` toont geen traceback.
- [ ] De eerste echte run van Debbie na stap 4: de notitie heeft `resume` al tijdens `running`, en
  na `done` niet meer; bij `paused` of `failed` komt er één melding (van de watcher, in
  `~/.agent-watcher/watcher.log`), niet twee.

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
- Naast wijzigingen draait de watcher `agent_dashboard.py` ook elke minuut. Het blok `Stil` en de
  grens van 7 dagen hangen af van de tijd, niet van een bestand (zie de bevindingen van stap 2).
  Het script schrijft alleen bij een andere inhoud, dus dat kost niets.
- Kijk ook naar `gebieden/agents/*.md` zelf, niet alleen naar de runmappen: een nieuwe agent of een
  ander `interval` moet ook op het dashboard komen.
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
- De watcher leest en schrijft met `lijsten` uit `agents()` en zonder `volgorde`, zodat een
  notitie zijn velden, hun volgorde en lege lijsten houdt (zie de bevindingen van stap 1).

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
  Antwoord (18-11): Ward ([[ward-bewaking-logboek]], stap 5) sloot aan zonder wijzigingen aan watcher of
  dashboard, met een run-notitie per check die elke run opnieuw geschreven wordt en `proces: Python`.
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

- 2026-11-18, stap 1:
  - Gekozen: `repo` hernoemd naar `onderwerp`, geen uitzondering in de module. Een eenmalig script
    zette de 27 run-notities om (de diff is per notitie alleen die regel), en `dashboard.base`
    gebruikt nu `onderwerp` (formule `project`, sortering, groepering), zodat de base werkt tot
    stap 5. Het plan van Debbie noemt de hernoeming onder `Bevindingen`.
  - De afspraak staat in [[agent-runs]], de notitie van Debbie in [[debbie]] met
    `runs: gebieden/werk/dependabot-runs` en `lijsten: [prs]`.
  - `scripts/agentruns.py`: `notitie_lezen(path, lijsten)`, `notitie_schrijven(path, fm, tekst,
    volgorde)`, `notities(runs, agent)`, `laatste_per_onderwerp(paden)`, `proces_leeft(pid, naam)`
    en `agents()`. De runner houdt dunne wrappers met zijn eigen `VELDEN` (volgorde) en `LIJSTEN`.
  - Zonder `volgorde` schrijft de module de velden in de volgorde van de notitie zelf. Een eigen
    vaste volgorde in de module zou elke notitie omgooien die de watcher in stap 4 schrijft.
  - Velden die de runner niet kent, blijven nu bewaard (ze komen achteraan). De oude runner gooide
    ze weg, zoals `tags` als ik die in Obsidian toevoegde.
  - Een leeg veld is dubbelzinnig: Obsidian kan een lege lijst en een lege tekst allebei als
    `veld:` schrijven. De lezer maakt er een lijst van als het veld in `lijsten` staat, anders `""`.
    Daarom `lijsten` in de notitie van de agent, en `agents()` geeft `aandacht` plus die velden
    terug. **Stap 4:** de watcher moet bij lezen en schrijven `agents()[agent]['lijsten']`
    meegeven, anders wordt `prs: []` bij Debbie `prs: ""`.
  - De lezer kent nu ook inline lijsten (`[a, b]`), voor de notities per agent.
  - Atomair schrijven: `.<naam>.<willekeurig>.tmp` in dezelfde map, dan `os.replace`. Obsidian
    negeert bestanden met een punt ervoor.
  - Getest: alle 27 notities gaan byte voor byte heen en terug, zowel via de runner als generiek
    (zoals de watcher straks), vóór en na de hernoeming; een notitie in Obsidian-stijl (blok-string,
    enkele quotes, `issue:` leeg, extra `tags`) leest goed. Op een kopie van de runmap: een
    `running`-run met een dood pid wordt `failed` met `resume`, zonder `pid`, en wordt de laatste
    van zijn onderwerp; de overslaglogica geeft `run loopt al`, `vorige run is failed`, `deze week
    al gedaan met dezelfde PR's` en `run` waar dat hoort. `--dry-run` onder `env -i` werkt.
  - Een echte run kon niet: geen enkel project had open PR's. Een handmatige runner-tik weigerde
    de auto-modus, en op de tik van launchd hebben we niet gewacht. Beide staan onder `Voortgang`
    als nog na te kijken.
  - Voor stap 2: het dashboard kan `agents()`, `notities()` en `laatste_per_onderwerp()` direct
    gebruiken.
- 2026-11-18, stap 2:
  - `scripts/agent_dashboard.py` schrijft `gebieden/agents/dashboard.md`: `[!danger] Aandacht
    nodig` of `[!success] Niets wacht op jou`, dan `[!warning] Stil` (alleen als er iets stil is),
    `[!info] Nu bezig`, en per agent een tabel `Afgelopen 7 dagen`. Opties `--agents` en `--uit`
    voor tests.
  - Nieuw, niet in het oorspronkelijke plan: `interval` in de notitie per agent (zoals `8d`), de
    langste tijd tussen twee runs. Is er langer geen run begonnen en loopt er geen, dan staat de
    agent onder `Stil`; een onleesbaar interval staat daar ook. Debbie heeft `interval: 8d`. Het
    veld staat in [[agent-runs]].
  - Agents zonder runs in de afgelopen 7 dagen blijven staan met `Geen runs.`: ook dat is een
    signaal. Aandacht nodig is één lijst voor alle agents, op starttijd; groeperen per agent is nog
    niet nodig.
  - In de tabel krijgt een `done`-run met aandachtspunten op een open issue ⚠️. Een run in de
    tabel: gestart binnen 7 dagen, of nog bezig, of wacht op mij.
  - Tekst uit een run-notitie: op één regel, met een backslash voor ``\`*_[]<>#|~=$%^!&{}:``. De `:`
    houdt een kale URL ongelinkt. Wikilinks naar de run alleen als bestandsnaam en onderwerp
    `[\w.-]+` zijn, issue-links alleen bij een geldig ID. In een tabel krijgt de alias `\|`,
    erbuiten niet. Getest in Obsidian met een notitie vol Markdown, HTML, callout, embed en URL:
    alles komt als letterlijke tekst.
  - `atomair_schrijven()` zit nu in `agentruns.py`, voor run-notities en het dashboard;
    `agents(map)` kan een andere map lezen. De 27 notities gaan nog byte voor byte heen en terug.
  - `gebieden/agents/dashboard.md` staat in `.gitignore`.
  - Voor stap 3: `Stil` en de grens van 7 dagen hangen van de tijd af, dus de watcher maakt het
    dashboard ook elke minuut opnieuw, en kijkt ook naar de notities per agent (staat bij stap 3).
- 2026-11-18, stap 3:
  - `scripts/agent_watcher.py` kijkt elke 2 seconden naar de `mtime` van `gebieden/agents/` en de
    notities daarin, van elke runmap en van de `.md`-bestanden daarin (geen `dashboard.md`). De map
    zelf vangt nieuwe, verwijderde en atomair geschreven notities, de bestanden een bewerking ter
    plekke. De stand wordt vóór het genereren opgenomen, zodat een wijziging tijdens het genereren
    de volgende tik alsnog telt. Daarnaast elke minuut. Het dashboard draait als subproces
    (`python3 -I`): een fout of een gewijzigd script raakt de watcher niet. Een fout in een tik wordt
    gelogd en de watcher loopt door. Optie `--tik` en `--eenmalig` voor tests.
  - Heartbeat en log buiten de vault, in `~/.agent-watcher/` (`heartbeat`, `watcher.log`), want
    elke 2 seconden een gewijzigd bestand in de vault is ruis voor Obsidian en git.
    `agentruns.heartbeat_schrijven()` en `watcher_stil()`, grens `HEARTBEAT_MAX` 3 minuten.
  - Het dashboard toont bovenaan `[!danger] De watcher draait niet` met de laatste heartbeat. De
    runner van Debbie controleert de heartbeat bij elke echte tik (niet bij `--dry-run`) en stuurt
    dan een macOS-melding, elk half uur zolang de watcher weg is. Dat gebeurt pas na `opruimen()`:
    na het inloggen starten runner en watcher tegelijk, en een controle vooraf kon de heartbeat van
    vóór de herstart zien en onterecht melden. Een aparte test na een herstart is niet nodig: de
    runner van Debbie laadt via dezelfde map in `~/Library/LaunchAgents/` en draaide na een herstart.
  - Plist in `scripts/agent-watcher/`, met `KeepAlive`, `RunAtLoad` en `ThrottleInterval` 30 (een
    watcher die meteen crasht, start niet eindeloos opnieuw). De shell maakt `~/.agent-watcher` aan.
  - Gevonden: `agent_dashboard.py` uit stap 2 werkte niet onder `python3 -I` (de scriptmap staat dan
    niet in `sys.path`). Nu met dezelfde `sys.path.insert` als de runner.
  - Getest, de watcher los: een nieuwe en een verwijderde run, een bewerking ter plekke en een nieuwe
    notitie per agent staan binnen 1 seconde op het dashboard; de verversing per minuut loopt; een
    oude heartbeat geeft de waarschuwing op het dashboard en de melding van de runner. Onder launchd:
    draait na `bootstrap`, en na `kill` startte launchd hem binnen 20 seconden opnieuw (de throttle
    telt vanaf de vorige start).
  - Voor stap 4: de YouTrack-poll en het opruimen horen in de lus van de watcher, met een eigen
    interval (elke paar minuten), en ná die schrijfacties ververst de volgende tik het dashboard
    vanzelf. Een fout bij YouTrack mag de tik voor het dashboard niet blokkeren: eigen `try`. De
    melding kan `melden()` uit de runner naar `agentruns.py` verhuizen.
- 2026-11-18, stap 4:
  - In de lus van de watcher, elk met een eigen `try`: heartbeat, processen (elke tik), YouTrack
    (`YOUTRACK_ELKE` 3 minuten, de eerste keer bij de start), dan meldingen en dashboard als de stand
    wijzigt. Na een eigen schrijfactie draait hij `build_index.py`, want `description` staat in de
    index van de runmap.
  - Een afgebroken run wordt pas `failed` als het proces `PROCES_WEG` (15 s) weg is. Anders zou de
    watcher in de seconde tussen het einde van `claude` en de eindstatus van de runner `failed`
    schrijven en melden. Het plan zei "binnen een paar seconden"; het werden er 15 tot 17.
  - Nieuw: `proces` in de notitie per agent (standaard `claude`), want de watcher moet weten hoe het
    proces achter `pid` heet. Staat in [[agent-runs]].
  - De oude runner zette bij een afgebroken run `resume` uit `session_id`; dat is specifiek voor
    Debbie. Nu schrijft de runner `resume` al bij de start, en haalt hij het weg bij `done`. De
    afspraak vraagt dat van elke agent.
  - `description` schrijft de watcher opnieuw met `agentruns.beschrijving()`, met de agentnaam met
    hoofdletter: voor Debbie dezelfde tekst als voorheen.
  - Naar `agentruns.py`: `melden()`, `env_waarde()` (met `ENV`), `youtrack_get()`, `issue_state()`
    (gooit nu een fout in plaats van `None`), `beschrijving()`, `afgehandeld()` en `wacht_op_mij()`
    (uit het dashboard). De runner gebruikt ze; `verslag_na()` blijft in de runner, op
    `youtrack_get()`.
  - `opruimen()` in de runner doet nu alleen `verslag_na()`, en leest de notitie opnieuw vlak voor het
    schrijven. De runner meldt geen `paused` of `failed` meer; alleen nog een stille watcher. Valt de
    watcher weg, dan zijn er dus ook geen meldingen per run, maar wel die over de watcher zelf.
  - Meldingen: bij een andere status naar `paused`/`failed` of een nieuw aandachtspunt, alleen voor
    runs die niet lopen en niet zijn afgehandeld. `~/.agent-watcher/gemeld.json` houdt per notitie
    status en aandachtspunten bij. Ontbreekt het bestand, dan legt de watcher alleen de stand vast
    (anders 28 meldingen bij de eerste start).
  - Gevonden: de pyenv-`python3` in mijn shell heeft geen SSL (`unknown url type: https`). Test
    YouTrack-code met `/usr/bin/python3`, zoals launchd.
  - Getest in een tijdelijke vault (16 gevallen: wachttijd, velden en volgorde, lege lijsten, Obsidian-
    stijl, YouTrack-fout, meldingen, herstart zonder dubbele meldingen, afgehandeld zonder melding,
    notitie zonder `agent`). Op een kopie van de runmap met de echte YouTrack: geen wijzigingen, en
    een verzonnen `issue_state` komt byte voor byte terug. Onder launchd met twee testnotities: dood
    pid na 17 s `failed` met melding, `paused` op een Done-issue (PA-1105) na 3 minuten `done`,
    beide op het dashboard. De testnotities zijn weg.
  - Voor stap 5: de runner-docstring noemt `dashboard.base` nog als overzicht.
- 2026-11-18, stap 5:
  - Gekozen: `dashboard.base` en `debbie-dashboard.md` helemaal weg, niet gehouden als geschiedenis.
    Kosten, beurten en `geweigerd` per run staan in de run-notities zelf. Voor een vergelijking
    tussen Opus en Sonnet moet je die dus uit de notities halen (met een script, niet uit het hoofd).
  - `laatste_markeren()` en het veld `laatste` zijn uit de runner, en `laatste: true` is uit de 21
    notities gehaald waar het stond (alleen die regel). De runner-docstring noemt alleen nog
    `gebieden/agents/dashboard.md`.
  - Verwijzingen bijgewerkt: [[dependabot-routine]], stap 9, 10 en de bevindingen van
    [[dependabot-routine-autonoom-plan]], de skill (`de watcher haalt de run uit Aandacht nodig`),
    [[vault-roadmap]] en `CLAUDE.md` (mapstructuur en gegenereerde bestanden).

