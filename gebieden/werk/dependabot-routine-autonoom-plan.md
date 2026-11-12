---
description: Plan om de Dependabot-routine autonoom te laten draaien, opgedeeld in stappen van één sessie per stap
tags: [dependabot, routine, plan]
---

# Plan: Dependabot-routine autonoom

Doel: de routine uit [[dependabot-routine]] draait zonder dat ik een sessie start. Waar hij
mij nodig heeft, stopt hij met een comment in het YouTrack-issue, en vanuit dat comment kan
ik op het juiste punt verder. Een overzicht in Obsidian toont welke runs lopen en hoe ze
zijn afgelopen.

Vastgelegd op 2026-11-10. Stap 1 tot en met 9 zijn klaar op 2026-11-11.

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
- [x] 4. Handmatige headless-run met pauze en hervatting
- [x] 5. Runner: repo's selecteren (dry-run)
- [x] 6. Runner: eigen clones en omgeving
- [x] 7. Runner: run starten en status vastleggen
- [x] 8. Schedule met launchd op één repo
- [x] 9. Dashboard in Obsidian
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
  updates), of wacht op de vaste dag van een andere repo (zie `Bevindingen`, stap 5).
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

- Bouw het commando met `clone_klaarzetten()`, `omgeving()` en `claude_args()` uit stap 6, niet
  met het commando uit stap 3: dat mist de MCP-config, `--setting-sources` en
  `claudeMdExcludes`. Start `claude` met `stdin` op `/dev/null`, anders wacht hij 3 seconden op
  invoer. Een `Stop` uit `clone_klaarzetten()` is `paused` met de reden, zonder run.
- Het model als optie van de runner, standaard Opus 5.5, en doorgeven aan `claude --model`.
  Zet het model ook in de run-notitie (frontmatter `model`), zodat een vergelijking later kan.
- `session_id` vooraf maken en meegeven, aan `--session-id` en als `session=<uuid>` in de
  prompt, de sessie een naam geven met
  `-n debbie-<repo>-w<week>`, de output bewaren in een logbestand buiten de vault.
- Per run een notitie in `gebieden/werk/dependabot-runs/<jaar>-w<week>-<repo>.md`, met
  frontmatter `description`, `agent` (`debbie`), `status`, `repo`, `issue`, `step`, `session_id`, `started`,
  `ended`, `resume`, `aandacht`, `prs`. `repo` is de naam van het projectbestand, `started` een
  ISO-tijd met tijdzone. `prs` is de lijst uit `vingerafdruk()` van de runner (`#171@abc1234`),
  vastgelegd bij de start: de overslaglogica van stap 5 vergelijkt daarmee. Status: `running`, `done`, `paused`, `failed`. `aandacht` is
  de lijst met `RUN_ATTENTION`-regels, leeg als er niets is.
- `status` volgt uit de `RUN_STATUS`-regel. Geen regel of een fout in de exitcode: `failed`.
- Daarna `build_index.py` draaien, want de hooks van de vault draaien niet mee.
- Bij `paused` of `failed` een macOS-melding sturen. Een comment op mijn eigen issue levert
  waarschijnlijk geen notificatie op.
- Per repo één run tegelijk, en een lock zodat twee runner-processen niet overlappen.
- Een `running`-notitie van een runner die is gecrasht blijft anders altijd `running`: zet die
  op `failed` als het proces niet meer bestaat (pid in de notitie of in de lock).
- Een `paused`- of `failed`-run blokkeert de repo tot de status verandert (zie stap 5). Bepaal hoe
  dat gebeurt na een hervatting: met de hand, of de runner kijkt in het issue of er na de pauze
  een `Debbie (Dependabot routine) report` staat en zet de notitie dan op `done`.

Klaar als: een echte run via de runner de juiste notitie oplevert, ook bij een afgebroken run.

### 8. Schedule met launchd op één repo

Doel: de runner draait vanzelf, voorlopig voor één repo.

- Maak het pauze-comment duidelijker (zie de bevindingen van stap 7): de `Resume`-regel opent
  alleen de sessie, en bij een nieuwe clone komt eerst de trust-vraag.
- `~/Library/LaunchAgents/nl.crimsoncricket.dependabot-runner.plist`, elk half uur
  (`StartInterval` 1800), met een allowlist van één repo:
  `/usr/bin/python3 -I ~/vault/scripts/dependabot_runner.py --repo <naam>`. De runner heeft geen
  shellprofiel nodig (getest met `env -i HOME=$HOME`). Zet `StandardOutPath` en
  `StandardErrorPath` in `~/dependabot-runs/.logs/runner.log`.
- launchd stopt een job met SIGTERM. De runner zet de lopende run dan op `failed` en stopt
  `claude`. Een tweede start terwijl er een runner loopt, stopt meteen (lock).
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
- Statussen: `running`, `done`, `paused`, `failed` en `resolved` (door mij vrijgegeven). Extra
  velden naast die uit stap 7: `reason`, `kosten`, `beurten`, `geweigerd`, `log`, `pid` (alleen
  bij `running`).

Klaar als: lopende, gepauzeerde en afgeronde runs goed zichtbaar zijn.

### 10. Uitrollen naar alle repo's

Doel: alle 21 repo's uit `projecten/` draaien autonoom.

- ~~In groepjes~~: besloten op 2026-11-11 om alles in één keer aan te zetten (zie `Bevindingen`).

De allowlist is de frontmatter `autonoom: true` in `projecten/*.md`. Die blijft staan als
uitknop per repo: regel weg, en de runner slaat de repo over.

- [x] Alle 21 repo's op `autonoom: true`, clones klaargezet met `--prepare` in `env -i HOME=$HOME`.
- [ ] Een hele ronde (maandag tot en met donderdag) gedraaid en in het dashboard nagekeken:
  verslagen, `geweigerd` en `aandacht`. Let vooral op de eigen stappen die nog nooit autonoom
  liepen: de release-PR's van `react-notifications` en `profile-presentation-design`, de codegen
  van `rostering-api` en sbt met Scala Steward in `notifications`.
- [ ] Controlepunt na donderdag 2026-11-19: alle runs van week 47 nagekeken in het dashboard
  (verslagen, `geweigerd` en `aandacht`). Week 46 telt niet als hele ronde: alles stond pas aan
  op woensdag 2026-11-11 om 16:51, en de repo's van maandag en dinsdag hebben nog geen autonome
  run gehad. Loop daarbij na:
  - de release-PR's van `react-notifications` en `profile-presentation-design`
  - de codegen van `rostering-api`
  - sbt met Scala Steward in `notifications`
  - `cata` en `roep`: Maven-versie in `.sdkmanrc` blijft staan en staat in het verslag
  - een tweede run in dezelfde week krijgt een eigen bestandsnaam (op 2026-11-12 stond
    `ats` #318 klaar voor een tweede run in week 46)

  Gaat dat goed, dan zijn stap 10 en het plan klaar.

Klaar als: alle repo's aan staan en een hele ronde is gedraaid.

## Nog te verifiëren

Deze punten staan niet of niet duidelijk in de documentatie. Gecontroleerd in stap 3.

- Ja: de skill uit `--add-dir ~/vault` start via `/dependabot-routine` in `-p`-modus.
- Ja: de YouTrack-MCP uit `~/.claude.json` is beschikbaar (`connected` in het init-event).
- `AskUserQuestion` staat niet in de tools van de run. De run vroeg ook nergens om input.
  Ja, bij een stop pauzeert hij netjes (stap 4).
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
- 2026-11-11, stap 4: beide runs pauzeerden in stap 2 met de juiste statusregel en een goed
  pauze-comment (`insights` in PI-202, `iam` in PKIAM-840). Elke run kostte
  ongeveer $0,50 en ruim een minuut. Hervatten met `claude --resume` (`insights`) en via de
  terugval (`iam`) gingen allebei verder bij stap 2. Ze mergeden niets dubbel, maakten elk één
  eigen PR (#262 en #220) en zetten het verslag in de subtask. De terugval nam
  `Report so far` en de reden van de pauze mee.
- `permission_denials: []` is nog niet gehaald: elke run had één weigering, nu niet door de
  skill maar door eigen initiatief van het model:
  - `insights` zocht de commit van `origin/develop` op met `gh api .../commits/develop` voor
    `base` in `State`. De skill zegt nu: `base` is de lokale base branch,
    `git rev-parse --short <base-branch>`.
  - `iam` zette een zelfgebouwde PR-link (`pompkracht/iam`) in het comment, wilde die
    corrigeren met `youtrack_edit_comment.py` uit mijn globale CLAUDE.md (geweigerd) en
    plaatste toen een correctie-comment zonder de `Debbie`-kop. Dat correctie-comment was
    zinnig. De skill zegt nu: links uit `gh pr view <n> --json url`, geen bewerkte comments,
    en een correctie als nieuw comment met de kop `Debbie (Dependabot routine) correction`.
    `Hervatten` telt correcties niet mee bij het zoeken naar het pauze-comment, maar laat ze
    voorgaan op wat erin staat.
  - Controleer in stap 7 en 8 opnieuw `permission_denials` in de log.
- De `Fallback`-regel werkte niet: buiten de vault kent een sessie de skill alleen met
  `--add-dir ~/vault`, en `--add-dir` slikt een prompt die erachter staat op als map. De regel
  is nu `claude "/dependabot-routine <subtask-id>" --add-dir ~/vault`.
- De run laadt mijn globale `~/.claude/CLAUDE.md`, zie het edit-script hierboven. Voor stap 6:
  kijk of dat uit kan, of dat de skill het moet afdekken.
- `insights` heeft in de root alleen `settings.gradle.kts` en `buildSrc`, geen
  `build.gradle(.kts)`. Interactief ging dat goed, autonoom was het een stop geweest
  (buildtool niet te bepalen). `settings.gradle(.kts)` staat nu in de tabel van stap 4.
- De JVM-melding `Sharing is only supported for boot loader classes ...` tijdens de tests kwam
  in het verslag als warning. Autonoom wordt dat een `RUN_ATTENTION` bij elke Gradle-run met
  Java 25. Besloten: de skill negeert deze melding, net als deprecations in gegenereerde
  API-clients.
- Logs van handmatige runs staan in `~/dependabot-runs/.logs/`.
- 2026-11-11, stap 5: alle 21 projecten staan onder `Flow-Cloud-Systems/<bestandsnaam>`, ook de
  twee met een afwijkende mapnaam (`pk-react-notifications`, `pk-react-profile-presentation-design`).
  De skill zoekt het projectbestand op de repo-naam, dus bestandsnaam en repo-naam zijn gelijk.
  `repo` staat in elk bestand, `authors` alleen in `notifications`.
- De skill leest de auteurs nu ook uit `authors` (bij `Projectspecifieke aanvullingen`), en `notifications.md`
  verwijst daarnaar in plaats van de twee `--author`-varianten zelf te noemen.
- `scripts/dependabot_runner.py --dry-run [--repo <naam>]` geeft per project `run`, `wacht`
  (checks lopen nog), `overslaan` (met reden) of `niets`. Zonder `--dry-run` stopt hij nog met
  een melding. 21 repo's kosten ongeveer 2 seconden (`gh pr list` parallel).
- Keuzes in de selectie:
  - Een PR zonder checks telt pas na 30 minuten als klaar. Daarvoor zijn de checks waarschijnlijk
    nog niet aangemaakt. Blijft hij zonder checks, dan meldt de skill dat (run met 0 jobs).
  - "Dezelfde PR's" is nummer plus commit (`#171@abc1234`). Een rebase door Dependabot, of een
    nieuwe PR, geeft dus een nieuwe run in dezelfde week. Een PR die rood blijft niet.
  - Ook een `failed`-run slaat de repo over, net als `paused`. Anders start een run die steeds
    crasht elk half uur opnieuw.
  - De laatste run per repo is de notitie met de laatste `started`, dus de bestandsnaam doet er
    niet toe. Twee runs in één week (zie de rebase hierboven) moeten in stap 7 wel een eigen
    bestandsnaam krijgen.
- Op het moment van testen stond er in de hele organisatie geen enkele open PR, dus de dry-run gaf
  overal `niets`, wat klopt. De regels zelf zijn getest met nep-PR's en nep-run-notities.
- Daarna Dependabot handmatig gestart in `iam-login-ui`. De dry-run, elke 30 seconden, gaf
  `niets`, toen `wacht` zodra #31 open stond met `build / build` nog bezig (de validator was al
  klaar), en twee minuten later `run`. De andere 20 repo's bleven `niets`. #31 staat nog open
  voor de eerste echte run in stap 7, dus niet met de hand mergen.
- Dependabot draait niet overal op maandag. Geen `dependabot.yml` noemt een `day:`, maar per repo
  is de dag wel vast (laatste 15 PR's, UTC):
  - ma: cata, iam, react-notifications, roep, rostering-api, rostering-application, rostering-ui
  - di: insights, profile-presentation-design
  - wo: axon-stomp-event-publishing, more, portal, rostering-engine
  - do: ats, iam-login-ui (ook vr), notifications, portal-employee-ui, portal-enrollment-ui,
    portal-ui-common, portal-worker-ui, profile-presentation-ui

  Voor stap 7 en 8 is er dus bijna elke werkdag werk, en donderdag komen er veel repo's tegelijk:
  een goede test voor meerdere runs achter elkaar en de lock. Extra PR's uitlokken is niet nodig.
  Twee auteurs in `notifications` hangt af van Scala Steward, want Dependabot doet daar alleen
  `github-actions`.
- 2026-11-11, stap 6: `dependabot_runner.py --prepare --repo <naam>` zet de clone klaar en toont
  de tools zoals een Bash-commando van de run ze ziet. Getest in `env -i HOME=$HOME` op `ats`
  (Maven), `insights` (Gradle) en `iam-login-ui` (npm, nieuwe clone): overal de juiste Java,
  Maven of Node, en `gh`, `claude` en git ingelogd. Een vuile clone geeft `STOP` met de bestanden.
- In een lege omgeving vindt de Bash-tool van de run niets: geen `mvn`, `node` of `gh`, en
  `java` is de macOS-stub. Mijn `.zshrc` laadt hij dan niet. De oplossing is `CLAUDE_ENV_FILE`:
  Claude Code sourcet dat bestand voor elk Bash-commando. `scripts/dependabot-runner/env.sh`
  laadt SDKMAN en draait `sdk env`, of `sdk env install` als er een versie ontbreekt. Zo volgt de
  omgeving ook een nieuwe `.sdkmanrc` uit stap 3. `sdk env install` vraagt niets en wijzigt de
  standaardversie niet. Gradle 9.9.1 is zo getest en staat nu ook op de machine.
- `env.sh` staat in de vault en niet in `~/dependabot-runs`: daar mag de run schrijven, en een
  bestand dat voor elk commando wordt gesourced zou de allowlist omzeilen.
- Node zet de runner vooraf in `PATH`, want de skill wijzigt `.nvmrc` niet. Net als `load-nvmrc`
  in mijn `.zshrc`: `nvm which`, en alleen als er lokaal niets past `nvm install`. De CLAUDE.md
  van de npm-projecten vraagt om `nvm use 24`. De skill zegt nu dat dat autonoom niet hoeft.
- Git ging via SSH, en zonder `SSH_AUTH_SOCK` faalt dat. De clones gaan nu via HTTPS, met
  `gh auth git-credential` als credential helper in de lokale git-config. `gh` is ingelogd via de
  keychain en werkt in `env -i`, ook voor push (`--dry-run` getest). De vier bestaande clones zijn
  omgezet. Het token van `gh` heeft geen `workflow`-scope: een push die `.github/workflows/`
  wijzigt, mislukt. De skill doet dat nu niet (`dependabot.yml` valt er niet onder).
- Alleen YouTrack: `--strict-mcp-config --mcp-config scripts/dependabot-runner/mcp.json`, met
  `Bearer ${YOUTRACK_TOKEN}` in de header. De runner zet die variabele uit `.env`. Claude Code
  vult hem in (`connected`), en ook de claude.ai-connectors vallen weg. `echo $YOUTRACK_TOKEN` is
  geweigerd, ondanks `Bash(echo *)`: commando's met een variabele vallen niet onder de lijst.
- Mijn globale CLAUDE.md blijft geladen, ook met `--setting-sources project,local`. Wat werkt:
  `claudeMdExcludes` met het absolute pad. Dat pad zet de runner erin, zodat `settings.json` vrij
  blijft van paden van mijn machine. Hij geeft de settings daarom als JSON-string mee.
  `--safe-mode` en `--bare` vallen af: die zetten skills uit of lezen de keychain niet.
- `--setting-sources project,local` houdt ook mijn gebruikersinstellingen buiten de run
  (`defaultMode: auto`, plugins, taal). `--permission-mode dontAsk` blijft voor de zekerheid.
- 2026-11-11, stap 7: `dependabot_runner.py [--repo <naam>] [--model <model>] [--timeout <min>]`
  start de runs. Eerst `opruimen()`, dan per repo met `run` één run, achter elkaar. De notitie
  heet `<jaar>-w<week>-<repo>.md`, een tweede in dezelfde week krijgt `-2` (log en sessienaam ook).
  Strings in de frontmatter zijn JSON (geldige YAML), zodat een reden met quotes of een dubbele
  punt niets breekt.
- Getest met `env -i HOME=$HOME`, op `iam-login-ui` #31:
  - Vuile clone: `paused` met de reden, geen run. De macOS-melding komt aan.
  - Een tweede runner tijdens een run: `er draait al een runner` (`flock` op
    `~/dependabot-runs/.runner.lock`).
  - SIGTERM aan de runner, zoals launchd stopt: `failed`, en `claude` stopt mee. `claude` draait
    in een eigen procesgroep, zodat ook zijn kinderen stoppen.
  - `kill -9` op de runner: `claude` loopt door en de notitie blijft `running`. Pas als `claude`
    weg is, zet de volgende runner hem op `failed`. Het `pid` in de notitie is dat van `claude`,
    en telt alleen als het proces echt `claude` heet.
  - Bij de tests met afbreken had Debbie nog niets gedaan, behalve het projectbestand lezen.
  - De echte run: #31 gemerged, daarna `paused` in stap 4 (PKIAM-841), 24 beurten, $0,40, anderhalve
    minuut, `geweigerd: 0`. Notitie, `resume`-regel en melding klopten.
- De oorzaak van die pauze: `npm ci` gaf E401 op Nexus. Tien npm-repo's hebben `${NPM_TOKEN}` in
  `.npmrc`, en dat zet alleen mijn `.zshrc`. De test van stap 6 draaide geen `npm ci`. De runner
  geeft het nu mee uit `.env` (naam in `.env.example`). Ontbreekt het terwijl `.npmrc` erom vraagt,
  dan is dat een `Stop` vóór de run. Maven en Gradle gebruiken geen omgevingsvariabelen voor hun
  credentials.
- Ook in een lege omgeving gevonden: `gh pr list` in de selectie had nog geen `PATH`.
- Na een hervatting: de runner zet een `paused`- of `failed`-run met issue op `done` als er na
  `ended` een comment `Debbie (Dependabot routine) report` in het issue staat (REST-API, token uit
  `.env`). Getest na een echte hervatting: `NPM_TOKEN` in `.env`, PKIAM-841 hervat met
  `claude --resume`, Debbie zette haar verslag in het issue, en de runner zette
  `2026-w46-iam-login-ui-4` op `done`. `step`, `reason` en `resume` gaan dan naar de tekst. De
  clone stond daarna schoon op `develop`.
  Zonder issue, zoals bij een vuile clone, geef ik de repo zelf vrij met `status: "resolved"`.
  `done` zou dat niet doen: de overslaglogica zou dan dezelfde PR's deze week overslaan.
- Extra velden in de notitie: `reason`, `kosten`, `beurten`, `geweigerd` (aantal, de details in de
  tekst), `log` en `pid` (alleen bij `running`). `step` alleen bij `paused`.
- Een run duurt hooguit `--timeout` minuten (standaard 120), daarna `failed`. De runner blijft zo
  lang op één run wachten, want hij werkt de repo's achter elkaar af.
- De drie testnotities (`2026-w46-iam-login-ui`, `-2`, `-3`) staan op `resolved`. Ze kunnen weg
  zodra het dashboard er is, of als voorbeelden blijven staan.
- Hervatten met de `Resume`-regel uit het pauze-comment werkte niet meteen, om twee redenen:
  - Een clone die de runner zelf heeft aangemaakt (zoals `iam-login-ui`), kent nog geen
    interactieve sessie. `claude --resume` vraagt dan eerst "Do you trust this folder?". Een
    headless run slaat die vraag over.
  - `claude --resume` opent de sessie en wacht dan op mij. Debbie gaat pas verder als ik dat
    zeg, meestal met mijn beslissing erbij ("NPM_TOKEN staat goed, ga verder vanaf stap 4").
    Bij een pauze is dat zo bedoeld, maar uit het comment blijkt het niet.

  Voor stap 8: zet in de skill een uitleg bij `Resume` in het pauze-comment, of laat de regel
  een prompt meegeven (`claude --resume <uuid> "<beslissing>, ga verder"`). Kijk ook of trust
  op `~/dependabot-runs` zelf de vraag voor de clones eronder voorkomt.
- 2026-11-11, stap 8 (deels): de `Resume`-regel geeft nu een prompt mee,
  `claude --resume <uuid> "<your decision>, continue from step <n>"`, met eronder een regel uitleg
  over Resume, Fallback en de trust-vraag. Trust op `~/dependabot-runs` werkt niet door naar de
  clones eronder (getest met `expect` op `ats`), dus de vraag komt één keer per clone. Een script
  dat `~/.claude.json` per clone aanpast, vond ik te riskant: lopende `claude`-processen schrijven
  daar zelf in.
- De plist staat in `scripts/dependabot-runner/nl.crimsoncricket.dependabot-runner.plist` en is
  met de hand gekopieerd naar `~/Library/LaunchAgents` en geladen met `launchctl bootstrap`.
  Claude mag dat niet zelf (auto mode weigert een LaunchAgent). `RunAtLoad` staat aan. Een tweede
  `bootstrap` geeft `5: Input/output error` als de job al geladen is. Controleren met
  `launchctl list | grep crimson`. De plist bevat geen absolute paden: launchd breidt `~` en
  `$HOME` niet uit, dus de job draait via `/bin/sh -c` met `$HOME`, en de log gaat met een
  redirect naar `runner.log` in plaats van via `StandardOutPath`. Na het laden vroeg macOS één keer om wachtwoord of Touch ID,
  zonder knop "Altijd toestaan", dus waarschijnlijk het goedkeuren van het achtergrond-item
  (`sfltool dumpbtm`: `enabled, allowed`). Na het herladen met `/bin/sh` als programma kwam alleen een melding over app-activiteit op de
  achtergrond, zonder iets goed te keuren. Kijk bij de volgende runs of de vraag terugkomt.
- `launchctl kickstart gui/$(id -u)/nl.crimsoncricket.dependabot-runner` start de job meteen, in
  dezelfde omgeving. Zo hoeft een test niet op het half uur te wachten.
- `runner.log` kreeg de regels pas na de run, omdat stdout naar een bestand gaat. De runner zet
  nu `line_buffering` aan.
- De run op `ats` (Dependabot met de hand gestart, #316 en #317) startte via `kickstart`: beide
  gemerged, build groen, OSV 0 bevindingen, daarna `paused` in stap 5 (PA-1105), 44 beurten,
  $0,75, `geweigerd: 3`. Notitie, pauze-comment en melding klopten. Na hervatten met de nieuwe
  `Resume`-regel zette de runner de notitie op `done`.
- De pauze kwam door `-DoutputFile=~/...` in stap 5: na `=` breidt de shell `~` niet uit, dus
  Maven schreef naar `./~/` in de clone. Het opruimen (`rm -rf ./~`) werd terecht geweigerd. De
  skill geeft daar nu het absolute pad (`<pwd>/../.scratch/<repo>`). De andere weigering was
  `mvn clean package > ... ; echo exit=$?`: de skill verbiedt nu `; echo $?`.
- `check_overrides.py` gaf `OVERBODIG` voor `bcpkix` en `bcutil` in `ats`, maar zonder die
  overrides werden ze 1.85, onder de fix 1.86. Debbie zette ze zelf terug. In de boom hangen ze
  alleen onder `bcjmail`, dat zelf een override is, en die boom voorspelt dan niet wat er zonder
  overrides gebeurt. Waar 1.85 precies vandaan kwam, is niet uitgezocht. Het script geeft nu
  `twijfel: pad via de override van ..., blijft staan` als een pad onder een andere eigen
  override loopt en de uitslag anders "kan weg" was. Besloten: bij twijfel blijft de override
  staan en komt hij in het verslag (zonder `RUN_ATTENTION`). De andere `handmatig controleren`-
  uitslagen blijven stil, want die komen elke week terug. De skill controleert na het weghalen ook
  dat de opgeloste versie niet lager is dan de override.
- Nog open voor stap 8: een run die echt door de schedule start, niet door `kickstart`, en
  zonder pauze afloopt. De allowlist blijft tot dan `ats`.
- 2026-11-11, stap 8 (vervolg): `ats` krijgt zijn Dependabot-PR's op donderdag rond 12:35 CET
  (29 oktober, 5 november), niet op maandag. De eerste kans is dus donderdag 12 november. Omdat
  Dependabot vandaag met de hand al is gestart, kan die ronde leeg blijven. Dan wordt het
  donderdag 19 november, of zet ik er een tweede donderdag-repo bij (de plist met de hand
  aanpassen en herladen).
- `runner.log` had geen tijden, dus niet te zien of launchd elk half uur start. De runner zet nu
  bij elke start (niet bij `--dry-run` of `--prepare`) een regel `-- <ISO-tijd>` in de log.
  Controleren met `grep -- '^-- ' ~/dependabot-runs/.logs/runner.log | tail`: ongeveer elke 30
  minuten een regel, met gaten als de Mac sliep.
- Allowlist uitgebreid met `portal-employee-ui` (donderdag-repo, Dependabot met de hand te
  starten). Herladen met `bootout` en direct daarna `bootstrap` gaf toch `5: Input/output error`,
  maar daarna stond wel de nieuwe plist geladen en had `RunAtLoad` gedraaid. Vertrouw dus niet op
  die melding. Controleer met
  `launchctl print gui/$(id -u)/nl.crimsoncricket.dependabot-runner | grep exec` en kijk of er een
  nieuwe `-- `-regel in `runner.log` staat.
- Klaar-criterium gehaald op `portal-employee-ui`: Dependabot met de hand gestart om ±13:40, #251
  (minor-and-patch, 7 updates) en #252 (jsdom 30 → 31, een major) geopend. De timer tikte om 14:05,
  precies 30 minuten na het laden, en de runner startte zelf de run. `done` (PKP-909) om 14:12,
  53 beurten, $0,98, `geweigerd: 0`, `aandacht: []`. Beide PR's gemerged, een eigen PR #253 met
  `npm audit fix` gemerged, de clone stond daarna schoon op `develop`. Daarmee werken `NPM_TOKEN`
  uit `.env` en een nieuwe clone ook onder launchd.
- De allowlist in de plist is nu `ats` en `portal-employee-ui`. Stap 10 breidt hem per groepje uit.
- 2026-11-11, stap 9: `dependabot-runs/dashboard.base` (Obsidian 1.15, Bases staat aan) met drie
  weergaven: `Aandacht nodig`, `Lopend` en `Alle runs` (gegroepeerd op status, nieuwste eerst). Het
  issue is een formule met een link naar YouTrack. De globale filter is `agent == "debbie"` in de
  map, dus `index.md` valt weg. Kolombreedtes staan per weergave in `columnSize`.
- Werkwijze, besloten na het eerste bekijken: het issue in YouTrack is de bron voor "afgehandeld".
  - Een autonome run zonder aandachtspunten zet de subtask na het verslag zelf op `Done`
    (stap 9 van de skill). Met aandachtspunten, of na een pauze, blijft hij `In Progress`.
  - De runner neemt bij elke tik de state over in `issue_state`, tot die `Done` is. Een `paused`-
    of `failed`-run met een issue op `Done` zet hij op `done`: ik heb het afgehandeld, de repo is
    weer vrij.
  - `Aandacht nodig` toont runs die `paused` of `failed` zijn of aandachtspunten hebben, zolang het
    issue niet op `Done` staat en de run niet `resolved` is.
  - Ik handel een punt af en zet de subtask op `Done`. Binnen een half uur is de run weg uit
    `Aandacht nodig`. `resolved` blijft alleen voor runs zonder issue, zoals een vuile clone.
  - Een eerdere poging met een vinkje `gezien` viel af: Obsidian toont geen checkbox voor een
    property die nog in geen enkele notitie staat, en het was dubbel werk naast het issue.
  - Een directe trigger bij een state-wijziging (webhook) vraagt een server die YouTrack kan
    bereiken. Het half uur van launchd is snel genoeg.
- Indeling, na het tweede bekijken: per project alleen de laatste run, in gewone taal. Weergaven
  `Overzicht` (alle projecten met een run), `Aandacht nodig` en `Geschiedenis` (alle runs per
  project, met beurten en kosten). `Lopend` is vervallen: een lopende run is altijd de laatste en
  staat in `Overzicht` als `Bezig`. Formules geven de status in woorden met een icoon, de
  projectnaam als link naar de run en de start als leesbare datum.
- Bases kan niet zelf "de laatste per groep" kiezen. De runner zet daarom `laatste: true` op de
  nieuwste run per project (`laatste_markeren()`, bij elke `index_bijwerken()` en aan het eind van
  `opruimen()`), en de weergaven filteren daarop.
- Wijzig ik in Obsidian een property, dan schrijft Obsidian de hele frontmatter opnieuw, zonder de
  JSON-quotes van de runner en met een blok-string voor een `reason` van meer regels.
  `notitie_lezen()` deed `json.loads` op elke waarde en zou daarop crashen. Hij leest nu ook strings
  zonder quotes, met enkele quotes en blok-strings (`|-`, `>-`), en booleans. Getest: alle
  bestaande notities gaan ongewijzigd heen en terug, en een notitie in Obsidian-stijl leest goed.
  PyYAML staat niet in de systeem-Python, vandaar een eigen parser.
- De run-notities blijven in git. Ze zijn klein en de geschiedenis van status en aandacht is
  nuttig. De runner commit niet zelf: de auto-commit bij SessionEnd neemt ze mee. De logs staan
  buiten de vault.
- `started` toont het dashboard zonder formule. Obsidian kan het als tekst of als datum zien, en een
  stringfunctie zou dan breken.
- De base is een tussenoplossing. Na het bekijken wil ik iets dat visueel meer opvalt, en een
  dashboard voor al mijn agents, niet alleen Debbie, dat niet een half uur achterloopt. Dat is
  [[agents-dashboard-plan]]: één statusvorm voor alle agents, een watcher die altijd draait en een
  gegenereerde notitie met callouts. Het lezen van `issue_state` en het opruimen van afgebroken
  runs gaan daar van de runner naar de watcher. Stap 10 kan los daarvan verder.
- Een `:` gevolgd door een spatie in een formule zonder quotes maakt de base kapot
  ("nested mappings are not allowed"). Formules staan daarom tussen enkele quotes.
- De drie testnotities uit stap 7 (`2026-w46-iam-login-ui`, `-2`, `-3`) zijn weggehaald. Hun logs staan nog in
  `~/dependabot-runs/.logs/`.
- 2026-11-11, stap 10: de allowlist staat niet meer in de plist maar in de frontmatter
  `autonoom: true` van de projectbestanden. Zonder `--repo` neemt de runner alleen die projecten,
  met `--repo` precies de genoemde, ook zonder `autonoom` (voor een test). `--dry-run` noemt
  onderaan de projecten die niet autonoom zijn. Zo hoeft de plist niet bij elk groepje met de
  hand gekopieerd en herladen te worden, en is één repo uitzetten ook een wijziging in de vault.
  De plist start de runner nu zonder `--repo`, en is nog één keer met de hand herladen. Laadt de
  oude plist nog, dan draaien alleen `ats` en `portal-employee-ui`: niets breekt.
- Herladen lukte niet met `bootout` en `bootstrap` in één regel: `bootstrap` gaf
  `5: Input/output error` en de oude job bleef geladen. Wat wel werkt, in twee stappen:
  `launchctl bootout gui/$(id -u)/nl.crimsoncricket.dependabot-runner`, dan controleren dat
  `launchctl print` `Could not find service` geeft (de eerste regel is `Bad request.`), en pas dan
  `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/nl.crimsoncricket.dependabot-runner.plist`.
  Om 16:51 controleerde de runner na het laden de acht autonome projecten.
- De skill zegt dat `autonoom` voor de runner is, zodat Debbie er niets mee doet.
- Groepje 1 klaargezet: vijf nieuwe clones met `--prepare` in `env -i HOME=$HOME`, allemaal schoon
  op `develop` met Node 24. Vijf van de zes hebben `${NPM_TOKEN}` in `.npmrc` (niet
  `rostering-ui`), en dat staat in `.env`. Geen van deze repo's heeft een CLAUDE.md, en hun
  projectbestanden hebben alleen YouTrack-gegevens, dus geen eigen stappen die een vraag stellen.
- Voor groepje 2: in `cata` en `roep` gaat een nieuwe Maven-versie ook naar
  `.github/workflows/*.yml`, en het token van `gh` mag dat niet pushen (geen `workflow`-scope,
  zie stap 6). De projectbestanden zeggen nu: autonoom de Maven-versie in `.sdkmanrc` laten staan
  en in het verslag noemen. De scope toevoegen viel af: de run leest CI-logs die niet te
  vertrouwen zijn, en met die scope kan een run workflows wijzigen die bij de secrets kunnen.
- Na groepje 1 besloten: alles meteen aan, niet in groepjes. Een run die vastloopt, pauzeert en
  blokkeert alleen zijn eigen repo. De releases naar `master` in `react-notifications` en
  `profile-presentation-design` zijn niet gevaarlijk (zie "Groen is groen" bij `Beslissingen`).
  Het risico van een fout in de skill die in veel repo's tegelijk terugkomt, is opruimwerk, geen
  schade. De eigen stappen van groepje 3 zijn daarom niet vooraf nagelopen. Dat gebeurt bij het
  bekijken van de eerste ronde.
- De dertien nieuwe repo's zijn klaargezet met `--prepare` in `env -i HOME=$HOME`: alle 21 clones
  schoon op hun base branch, git via HTTPS werkt. `--prepare` toont nu ook `sbt`. In
  `notifications` geeft `env.sh` sbt 2.0.12, Java 25.0.5 en Scala 3.10.0 uit `.sdkmanrc`.
  Onder `/bin/bash` (3.2) faalt `sdk env` met `${candidate_name^^}: bad substitution`, onder zsh
  niet. De runs gebruiken zsh, zie de echte Maven- en Gradle-runs onder launchd.

- `laatste_markeren()` herschreef ook `debbie-dashboard.md`: `notities()` nam elk `.md`-bestand in
  `dependabot-runs/`. Daarbij vielen `tags` en `cssclasses: [wide-page]` weg en kwam er
  `laatste: true` bij. Leek op Obsidian, maar was de runner. `notities()` neemt nu alleen notities
  met `agent: debbie`, net als het filter van `dashboard.base`. Andere notities mogen dus in die map.
