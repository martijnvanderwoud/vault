---
description: Plan om de Dependabot-routine autonoom te laten draaien, opgedeeld in stappen van één sessie per stap
tags: [dependabot, routine, plan]
---

# Plan: Dependabot-routine autonoom

Doel: de routine uit [[dependabot-routine]] draait zonder dat ik een sessie start. Waar hij
mij nodig heeft, stopt hij met een comment in het YouTrack-issue, en vanuit dat comment kan
ik op het juiste punt verder. Een overzicht in Obsidian toont welke runs lopen en hoe ze
zijn afgelopen.

Vastgelegd op 2026-11-10. Stap 1 tot en met 3 zijn klaar op 2026-11-11.

## Zo werken we dit af

Elke stap is één losse sessie. Start in `~/vault` en zeg: "Doe de eerste open stap uit
[[dependabot-routine-autonoom-plan]]". Aan het eind van de sessie:

- vink je de stap af in de voortgang hieronder
- zet je onder `Bevindingen` wat afweek van het plan of wat een latere stap verandert
- pas je latere stappen aan als dat nodig is

## Voortgang

- [x] 1. Stoppunten indelen in de skill
- [x] 2. Pauzeren en hervatten in de skill
- [x] 3. Handmatige headless-run zonder pauze
- [ ] 4. Handmatige headless-run met pauze en hervatting
- [ ] 5. Runner: repo's selecteren (dry-run)
- [ ] 6. Runner: eigen clones en omgeving
- [ ] 7. Runner: run starten en status vastleggen
- [ ] 8. Schedule met launchd op één repo
- [ ] 9. Dashboard in Obsidian
- [ ] 10. Uitrollen naar alle repo's

## Beslissingen

- **Groen is groen, ook zonder toezicht en ook bij een major.** We mergen naar `develop`, en
  in sommige projecten ook naar `master`, maar die komen niet zomaar automatisch in
  productie. Fouten die hieruit komen zie ik snel in mijn development-omgeving, en dat is
  juist wat ik wil. De projectstappen, zoals een release-PR, draaien dus ook autonoom.
- **Twee klassen stoppunten:** stoppen en rapporteren, of in het eindverslag opnemen en
  doorgaan.
- **Geen hook:** hooks reageren alleen op gebeurtenissen binnen een sessie, niet op GitHub.
- **Lokale schedule die GitHub pollt, geen PR-trigger.** Eén launchd-job kijkt elk half uur
  met `gh` of er per repo PR's zijn waarvan alle checks klaar zijn, en start alleen dan de
  routine, per repo één tegelijk. Bij "PR opened" lopen de checks nog, en meerdere PR's
  zouden meerdere runs tegelijk starten.
- **Niet in de cloud:** een cloud-routine heeft standaard alleen Java 21 en geen sbt, mag
  alleen naar `claude/`-branches pushen (botst met `feature/` en de GitFlow-validator) en
  kan niet bij de skill in de vault. Een GitHub Action moet per repo, en runs met Dependabot
  als trigger krijgen standaard geen gewone Actions-secrets.
- **Eigen clones:** de run werkt in `~/dependabot-runs/<repo>`, nooit in mijn working copies
  in `~/IdeaProjects`.
- **Geen `bypassPermissions`:** een vaste lijst toegestane commando's en
  `--permission-prompts none`. De run leest CI-logs en die zijn niet te vertrouwen.
- **De runner schrijft de status, niet het model,** zodat een vastgelopen run ook zichtbaar
  is als `failed`.
- **Debbie draait op Opus 5.5.** Door de check in de runner draait hij alleen als er werk is,
  ongeveer één keer per repo per week, dus het prijsverschil met Sonnet telt weinig. Het werk
  vraagt oordeel zonder toezicht: de oorzaak van een rode PR, patchen zonder breaking change,
  en vooral op tijd stoppen. Het model is een parameter van de runner (`--model`), met Opus als
  standaard. Na stap 10 eventueel Sonnet proberen op het npm-groepje en de verslagen vergelijken.
- **De agent heet Debbie,** vanwege Dependabot. De naam staat in de sessienaam, in de
  run-notities en boven de comments. Die comments komen onder mijn YouTrack-account te staan,
  dus zo is ook te zien dat ze van de agent zijn.

## Stappen

### 1. Stoppunten indelen in de skill

Doel: `SKILL.md` kent een autonome modus, en bij elk stoppunt staat wat er dan gebeurt.

- Autonome modus via een argument: `/dependabot-routine autonoom`. Zonder argument blijft
  de skill vragen zoals nu.
- Neem de indeling hieronder door en verwerk hem in de stappen van `SKILL.md`.
- Pas de inleiding aan: een situatie zonder regel is autonoom `stoppen`, tenzij hij maar één
  PR raakt en de rest gewoon door kan.
- Vervang in stap 0 van de skill, bij `Op het board zetten`, de `grep` op `.env` en de `curl`
  door `/usr/bin/python3 -I ~/vault/scripts/youtrack_command.py <issue> "add Board <board>
  <sprint>"`. Dan werkt het in vault- en projectsessies hetzelfde en hoeft de run `.env` niet
  zelf te lezen. Neem het script mee in de `--allowedTools` van stap 3.
- Controleer de projectbestanden op eigen stoppunten. Bij een eerste grep had geen enkel
  bestand er een, maar de grep zocht alleen op vaste zinnen.

Klaar als: elk stoppunt een klasse heeft en de interactieve werking niet is veranderd.

Voorstel voor de indeling:

| Stap | Situatie | Klasse |
| --- | --- | --- |
| 0 | YouTrack-gegevens ontbreken | stoppen, nog geen issue |
| 0 | Meer dan één parent, of een ander jaar in de titel | stoppen, nog geen issue |
| 0 | Subtask in een andere state dan `In Progress` of `Done` | stoppen |
| 0 | Op het board zetten mislukt | verslag, plus aandachtspunt (zie stap 2) |
| 1 | `mergeable=UNKNOWN` blijft na een paar pogingen | verslag |
| 1 | PR niet groen, `CONFLICTING`, of merge mislukt | verslag |
| 1 | Run met 0 jobs zonder incident, of na herstart nog rood | verslag |
| 1 | Rode PR met een andere oorzaak dan `ERESOLVE`, met voorstel | verslag |
| 1 | PR's met verschillende base branches | stoppen |
| 2 | Andere branch, vuile working copy, of geen fast-forward | stoppen |
| 4 | Buildtool niet te bepalen | stoppen |
| 4 | Build-errors, of 0 tests terwijl er tests zijn | stoppen |
| 4 | Warnings | verslag |
| 5 | Fix alleen in een nieuwere major, of alleen een breaking fix | verslag |
| 5 | `npm audit fix` zet een versie omlaag | stoppen |
| 6 | Base branch anders dan `develop` | stoppen |
| 6 | Eigen PR niet groen of `CONFLICTING` | stoppen |
| 6 | `git branch -d` weigert | verslag |
| 8 | Geen run op de base branch na een paar pogingen | stoppen |
| 8 | Build op de base branch rood, of hij loopt niet af | stoppen |

### 2. Pauzeren en hervatten in de skill

Doel: een gepauzeerde run is vanuit het issue voort te zetten.

- Beschrijf in `SKILL.md` het pauze-comment, in het Engels, in de subtask:

  ```text
  Debbie (Dependabot routine) PAUSED at step 6
  Seen: PR #171 build red (...)
  Decision needed: ...  Proposal: ...
  State: merged #168 #169, branch feature/..., base abc123
  Resume: cd ~/dependabot-runs/cata && claude --resume <uuid>
  ```

- Voeg hervatten toe: `/dependabot-routine <issue-id>` leest het laatste pauze-comment en
  de stand in GitHub en git, en gaat verder bij de genoemde stap. Dit is de terugval als
  `--resume` niet kan (de transcripts blijven standaard 30 dagen op deze machine).
- Laat de run in autonome modus eindigen met een regel die de runner kan lezen, bijvoorbeeld
  `RUN_STATUS: paused step=6 issue=PCATA-617`. Mogelijke statussen: `done`, `paused`.
- Laat de run elk verslagpunt waar ik iets mee moet ook apart melden, per punt een regel
  `RUN_ATTENTION: <korte tekst>`. Volgens stap 1 is dat elk punt met `Autonoom: verslag`.
  Punten die de skill al "alleen in het verslag" noemt, krijgen geen regel. Bijvoorbeeld: op
  het board zetten mislukt, een rode PR met een voorstel, een PR die niet gemerged kon worden. Zo valt een run met status `done` die
  toch iets van mij nodig heeft op in het dashboard, ook als het issue niet op het bord staat.
- Stoppen vóór de subtask bestaat: geen comment, alleen de statusregel met de reden.
- Vervang in `Autonome modus` van `SKILL.md` de voorlopige omschrijving van `stop` ("meld wat
  je zag ...") door een verwijzing naar het pauze-comment.
- Stap 9: in autonome modus geen chatverslag nodig, het comment is het verslag.

Klaar als: de teksten staan in de skill en de interactieve werking niet is veranderd.

### 3. Handmatige headless-run zonder pauze

Doel: de routine loopt één keer van begin tot eind via `claude -p`, door mij gestart, in
een repo met open Dependabot-PR's.

- Maak met de hand de clone in `~/dependabot-runs/<repo>`.
- Bepaal het commando, ongeveer:
  `claude -p "/dependabot-routine autonoom session=<uuid>" --add-dir ~/vault --session-id <uuid>
  --permission-prompts none --allowedTools ... --output-format stream-json --verbose`
- Stel de lijst `--allowedTools` samen uit de commando's in de skill en de YouTrack-tools.
- Lees na afloop `permission_denials` uit de output en vul de lijst aan.
- Controleer de punten onder `Nog te verifiëren`.

Klaar als: de run `done` geeft zonder geweigerde tools, en het commando in dit plan staat.

Het commando, vanuit `~/dependabot-runs/<repo>`:

```bash
U=$(uuidgen | tr A-Z a-z)
claude -p "/dependabot-routine autonoom session=$U" --session-id $U \
  --add-dir ~/vault --add-dir ~/dependabot-runs/.scratch/<repo> \
  --permission-mode dontAsk --permission-prompts none \
  --settings ~/vault/scripts/dependabot-runner/settings.json \
  --model claude-opus-5-5 --output-format stream-json --verbose > <log>
```

De allowlist staat in `scripts/dependabot-runner/settings.json`, niet in `--allowedTools`.
`--permission-mode dontAsk` is nodig, want mijn gebruikersinstellingen hebben
`defaultMode: auto`: dan zou de classifier beslissen in plaats van de lijst.

### 4. Handmatige headless-run met pauze en hervatting

Doel: het hervatten werkt echt.

- Twee repo's, met het commando uit stap 3: `insights` (#260, #261) voor de interactieve
  hervatting, `iam` (#219) voor de terugval. De pauze valt in stap 2 van de skill, dus de
  PR's zijn dan al gemerged: elke pauzetest kost een repo. Te weinig PR's: start Dependabot
  handmatig in een ander project (Insights → Dependency graph → Dependabot → Check for
  updates), of wacht op maandag, de standaarddag van het wekelijkse schema.
- Controleer ook dat beide runs `permission_denials: []` geven, na de aanpassingen uit de
  bevindingen van stap 3. In stap 3 lukte dat nog niet.
- Lok een pauze uit: zet een onschuldig ongecommit bestand in de clone, zodat stap 2 stopt.
- Controleer het comment in YouTrack en de statusregel.
- Haal het bestand weg en hervat met `claude --resume <uuid>`, interactief.
- Herhaal met de terugval: een nieuwe sessie met `/dependabot-routine <issue-id>`. Controleer
  dat de punten uit `Report so far` in het eindverslag staan.

Klaar als: beide manieren op de juiste stap verdergaan en niets dubbel doen.

### 5. Runner: repo's selecteren (dry-run)

Doel: `scripts/dependabot_runner.py --dry-run` toont welke repo's nu een run zouden krijgen,
zonder iets te wijzigen.

- De repo's komen uit `projecten/*.md`. Daarin staat nog geen GitHub-owner (bijvoorbeeld
  `Flow-Cloud-Systems/roep`), dus voeg die toe als frontmatter `repo` in elk bestand (zie
  `Bevindingen`). Bepaal de waarde eenmalig uit de `origin` van de bestaande working copies.
  Mapnamen wijken soms af van de repo-naam (`pk-react-notifications`).
- Een repo komt in aanmerking als er open PR's zijn van de auteurs in de frontmatter
  `authors` (standaard `app/dependabot`, in `notifications` ook Scala Steward), en alle
  checks klaar zijn.
- Een repo met een lopende of gepauzeerde run, of een run die deze week al klaar is met
  dezelfde PR's, slaat de runner over.

Klaar als: de dry-run op alle repo's klopt met wat ik op GitHub zie.

### 6. Runner: eigen clones en omgeving

Doel: de runner maakt een clone klaar en draait daarin de juiste tools, ook buiten mijn shell.

- Clone aanmaken als die ontbreekt, anders `fetch`, en controleren dat hij schoon is. Een
  vuile clone na een run is een reden om te stoppen, niet om op te ruimen.
- De scratch-map `~/dependabot-runs/.scratch/<repo>` aanmaken. De skill rekent erop.
- Alleen de YouTrack-MCP laden: `--strict-mcp-config --mcp-config <bestand>`. Nu laadt de
  run ook GitHub, JetBrains, Gmail en de claude.ai-connectors (geweigerd door `dontAsk`,
  maar wel in de prompt). De config van `~/.claude.json` bevat het token in een
  `Authorization`-header en mag dus niet in de vault: zet in het bestand
  `${YOUTRACK_TOKEN}` en laat de runner die variabele uit `.env` vullen. Kijk of de
  claude.ai-connectors daarmee ook wegvallen.
- SDKMAN (`.sdkmanrc`) en Node (`.nvmrc`) opzetten binnen het script, want launchd laadt
  mijn zsh-profiel niet.
- Testen met een lege omgeving (`env -i`): `java`, `mvn` of `gradle`, `node`, `gh` en
  `claude` zijn er in de juiste versie, en `gh` en `claude` zijn ingelogd.

Klaar als: dit werkt in `env -i` voor één Maven-, één Gradle- en één npm-repo.

### 7. Runner: run starten en status vastleggen

Doel: de runner start één run en legt de uitkomst vast.

- Het model als optie van de runner, standaard Opus 5.5, en doorgeven aan `claude --model`.
  Zet het model ook in de run-notitie (frontmatter `model`), zodat een vergelijking later kan.
- `session_id` vooraf maken en meegeven, aan `--session-id` en als `session=<uuid>` in de
  prompt, de sessie een naam geven met
  `-n debbie-<repo>-w<week>`, de output bewaren in een logbestand buiten de vault.
- Per run een notitie in `gebieden/werk/dependabot-runs/<jaar>-w<week>-<repo>.md`, met
  frontmatter `description`, `agent` (`debbie`), `status`, `repo`, `issue`, `step`, `session_id`, `started`,
  `ended`, `resume`, `aandacht`. Status: `running`, `done`, `paused`, `failed`. `aandacht` is
  de lijst met `RUN_ATTENTION`-regels, leeg als er niets is.
- `status` volgt uit de `RUN_STATUS`-regel. Geen regel of een fout in de exitcode: `failed`.
- Daarna `build_index.py` draaien, want de hooks van de vault draaien niet mee.
- Bij `paused` of `failed` een macOS-melding sturen. Een comment op mijn eigen issue levert
  waarschijnlijk geen notificatie op.
- Per repo één run tegelijk, en een lock zodat twee runner-processen niet overlappen.

Klaar als: een echte run via de runner de juiste notitie oplevert, ook bij een afgebroken run.

### 8. Schedule met launchd op één repo

Doel: de runner draait vanzelf, voorlopig voor één repo.

- `~/Library/LaunchAgents/nl.crimsoncricket.dependabot-runner.plist`, elk half uur,
  met een allowlist van één repo.
- De Mac moet aan staan: een gemist interval tijdens slaap wordt bij het wakker worden
  ingehaald, staat de Mac uit dan niet. Omdat de runner pollt, is dat geen probleem.
- Eén Dependabot-ronde meekijken.

Klaar als: een run zonder mijn tussenkomst is gestart en goed is afgelopen.

### 9. Dashboard in Obsidian

Doel: één overzicht van alle runs.

- `gebieden/werk/dependabot-runs/dashboard.base`, een tabel per status met links naar het
  issue en een kolom `aandacht`, plus een aparte weergave van runs met aandachtspunten.
  De kernplugin Bases staat al aan, dus geen community-plugin nodig. Controleer of
  mijn Obsidian-versie het aankan (vanaf 1.9).
- Bepaal of de run-notities in git moeten. Bij elke run komen er commits bij.

Klaar als: lopende, gepauzeerde en afgeronde runs goed zichtbaar zijn.

### 10. Uitrollen naar alle repo's

Doel: alle 21 repo's uit `projecten/` draaien autonoom.

- In groepjes: eerst npm, dan Maven en Gradle, als laatste `notifications` (sbt, Scala
  Steward) en de projecten met eigen stappen (`react-notifications`,
  `profile-presentation-design`, `rostering-api`).
- Controleer per groepje of de eigen stappen zonder vragen kunnen.
- Allowlist weghalen zodra een groepje goed is gelopen.

Klaar als: de allowlist weg is en een hele ronde is gedraaid.

## Nog te verifiëren

Deze punten staan niet of niet duidelijk in de documentatie. Gecontroleerd in stap 3.

- Ja: de skill uit `--add-dir ~/vault` start via `/dependabot-routine` in `-p`-modus.
- Ja: de YouTrack-MCP uit `~/.claude.json` is beschikbaar (`connected` in het init-event).
- `AskUserQuestion` staat niet in de tools van de run. De run vroeg ook nergens om input.
  Of hij bij een twijfelgeval netjes pauzeert, blijkt in stap 4.
- Hervatten met `claude --resume` is interactief en gebruikt mijn eigen instellingen, daar
  horen de flags niet bij. Een autonome hervatting (`/dependabot-routine autonoom <issue>`)
  is een nieuwe run en krijgt het hele commando uit stap 3.

## Bevindingen

- 2026-11-11, vóór stap 1: tokens besparen door de check of er werk is in een script te doen,
  en niet in Claude. Een run zonder werk kost toch een paar modelbeurten op een prompt van
  tienduizenden tokens, en prompt caching vangt dat maar voor een klein deel op. De
  systeemprompt verschilt per repo (werkmap, git-status, datum), de cache verloopt na 5 minuten
  (of na 1 uur, maar dan kost het schrijven 2×), en output en denkwerk betaal je altijd
  volledig. Bij 21 repo's elk half uur zijn dat ongeveer 1000 starts per dag. Dit bevestigt de
  aanpak in stap 5. De overslaglogica daar is net zo belangrijk: anders start een PR die rood
  blijft elk half uur een nieuwe run.
- Voor stap 5: leg repo en auteurs vast in de frontmatter van `projecten/*.md`, zodat runner en
  skill één bron hebben. `authors` weglaten betekent `[app/dependabot]`, alleen
  `notifications` vult het in:

  ```yaml
  repo: Flow-Cloud-Systems/notifications
  authors: [app/dependabot, app/flow-cloud-scala-steward]
  ```

  Laat de tekst van `notifications.md` over de twee auteurs dan naar die frontmatter verwijzen.
- 2026-11-11, stap 1: de klassen staan in `SKILL.md` als `Autonoom: stop` of `Autonoom: verslag`
  direct achter elk voorlegpunt, en de definities in een nieuwe sectie `Autonome modus`. Elk
  `verslag`-punt is een aandachtspunt, omdat het een vraag aan mij vervangt. Een aparte markering
  per punt was dus niet nodig.
- De voorgestelde tabel is ongewijzigd overgenomen. Erbij gekomen: een PR uit de projectstappen
  die niet groen of `CONFLICTING` is, is een stop. Daarvoor stond nog geen regel in stap 7.
- Eigen stoppunten in de projectbestanden, die de eerste grep miste:
  - `react-notifications` en `profile-presentation-design`: lege release-lijst is verslag, en dan
    vervalt de rest van stap 7 (ook de versiebump). Een versiebump die meer wijzigt dan de
    versieregels is een stop.
  - `rostering-api`: graphql 17 toegestaan is verslag, met het voorstel de `ignore` weg te halen.
  - `notifications`: een lege lijst projecten in stap 5 is een stop, en `0 tests passed` volgt de
    regel over 0 tests uit stap 4.
- `Op het board zetten` gebruikt nu `youtrack_command.py`. Dat script stopt met een melding als
  het token ontbreekt, wat onder `mislukt` valt.
- 2026-11-11, stap 2: de run kent zijn eigen sessie-ID niet vanzelf. De runner geeft het mee als
  argument, `/dependabot-routine autonoom session=<uuid>`, naast `--session-id`. Zonder dat
  argument laat de skill de regel `Resume` weg. Stap 3 en 7 zijn daarop aangepast.
- Het pauze-comment kreeg twee regels extra. `Report so far` bevat de verslagpunten van vóór de
  pauze, anders mist een hervatting via de terugval die in het eindverslag. `Fallback` geeft het
  commando voor de terugval, `/dependabot-routine <subtask-id>`. `State` noemt ook PR's die niet
  gemerged zijn en ongecommitte bestanden.
- Statusregel: `RUN_STATUS: <done|paused> issue=<id|none> step=<n> reason="..."`, met `step` en
  `reason` alleen bij `paused`, als allerlaatste regel na de `RUN_ATTENTION`-regels. Een stop vóór
  de subtask is `paused` met `issue=none`, geen open PR's is `done issue=none`. Stap 7 kan hierop
  parsen.
- Hervatten via het issue is interactief. Met `/dependabot-routine autonoom <issue-id>` gaat het
  autonoom verder. De skill herkent de comments van Debbie aan de eerste regel
  `Debbie (Dependabot routine)`, omdat ze onder mijn account staan. Het verslag van stap 9 begint
  in autonome modus met `Debbie (Dependabot routine) report`, zodat hervatten ziet dat er na een
  pauze al een verslag is.
- 2026-11-11, stap 3: proefrun op `ats` zonder open PR's gaf `done issue=none`, in 3 beurten
  voor $0,29. Dat bevestigt dat de check of er werk is in de runner hoort.
- Echte run op `rostering-engine`: `done issue=RPAAS-518`, 45 beurten, 9 minuten, $1,13.
  #75 gemerged, een eigen PR #76 voor Gradle 9.9.1 in `.sdkmanrc`, build op `develop` groen,
  verslag in het issue, één `RUN_ATTENTION` (een Gradle-deprecation).
- Zes commando's geweigerd. Het model vond voor elk zelf een weg, maar het klaar-criterium
  "zonder geweigerde tools" is hiermee niet gehaald. Een tweede run zou PR's kosten, dus
  dat controleren we in stap 4. De oorzaken:
  - Twee commando's stonden zo in de skill: de Gradle-subshell met `xargs` in stap 5 en
    `$(git rev-parse ...)` in stap 8. Beide zijn opgesplitst.
  - Backticks in `gh pr create --body`. De beschrijving gaat nu via Write naar een bestand
    en `--body-file`.
  - In `-p`-modus is er geen scratchpad, dus het model schreef naar `/tmp`. De skill noemt
    in autonome modus nu `~/dependabot-runs/.scratch/<repo>`, en het commando geeft die map
    mee met `--add-dir`. Ook staat in de skill: geen lussen, subshells of `$(...)`.
  - `sort`, `uniq` en `tr` toegevoegd aan de allowlist, `xargs` eruit.
  - De allowlist bevat geen paden of namen van mijn machine: alleen `~/` en `{owner}/{repo}`,
    en de skill vraagt het model die vorm te gebruiken. Werkt dat niet in stap 4, dan kan de
    runner de regels met absolute paden genereren in plaats van ze in het bestand te zetten.
- Dependabot is ook handmatig te starten per repo, mocht stap 4 of later meer PR's nodig
  hebben (Insights → Dependency graph → Dependabot → Check for updates).
