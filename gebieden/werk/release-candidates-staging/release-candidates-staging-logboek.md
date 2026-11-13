---
description: Logboek van het opbouwen en automatiseren van de release candidates voor staging bij Pompkracht
tags: [pompkracht, release, staging]
cssclasses: [wide-page]
---

# Release candidates voor staging: logboek

Hoe [[release-candidates-staging]] stap voor stap tot stand kwam, vanaf de eerste ronde met de hand
op 2026-11-12. De beslissingen die eruit volgden, staan in [[release-candidates-staging-beslissingen]].

## 2026-11-12, eerste ronde

- Vaste lijst bevestigd en vastgelegd in `data/staging-repos.json`. `portal-worker-ui` is ook
  een frontend van `portal`; `profile-presentation-ui` heeft een eigen image (Next.js).
- Lokale checkouts staan in `~/IdeaProjects/pompkracht/<repo>`, soms nog met de legacy-prefix
  `pk-`. Voor het overzicht zijn geen clones nodig (alles via `gh api`). Voor de release
  branches wel: eigen clones (zoals bij de dependabot-runner) of worktrees, nog te kiezen.
- Infra: repo `Flow-Cloud-Systems/infra`, branches `feature/<ISSUE>-rc` (en `-release` voor
  productie), worktrees naast de checkout als `infra-<ISSUE>-rc`.
- Stap 1 gescript: `scripts/staging_overzicht.py [--uit BESTAND]`. Per repo de commits van
  `master...develop` via de GitHub compare-API. Issuenummers in de commits worden alleen
  meegenomen als de projectkey in YouTrack bestaat (dat filtert `UTF-8` en dergelijke).
  De parents worden gevolgd via `parent(issues(idReadable))` in de YouTrack-REST-API. De
  infra-branches worden gekoppeld via `<ISSUE>-rc$`. Automatische updates (Dependabot, Scala
  Steward, de lock-file-commits van `portal-ui-common`) telt het script alleen; de overige
  commits zonder issue zet het per repo in een lijst.
- Eerste resultaat: [[staging-releases/2026-11-12|2026-11-12]] in `staging-releases/`.
- Vergeleken met de hoofdissues op het bord:
  - Dependabot-parents zonder issuenummer in de commits (PM-359, PPP-75, ROEP-1063,
    RPAAS-487/489/491) ontbreken in het overzicht. **Besluit: geen probleem.** Bumps vervuilen
    het overzicht alleen en vragen nooit om configuratie. Commits zonder issue niet aan de
    Dependabot-parent hangen: het kan ook iets heel anders zijn.
  - PKI-906 ontbrak: de squash-commit was het issuenummer kwijt, de PR-titel en de branch
    (`feature/PPP-16`) hadden het nog wel. **Opgelost:** heeft een commit geen issuenummer maar
    wel `(#N)`, dan haalt het script het uit de titel en de branch van de PR.
  - PA-1096 (bug) was een hotfix die al in productie staat. De originele commit staat in
    `develop`, de cherry-pick in `master` (via "Hotfix 12.8.1"), die later terug is gemerged.
    **Opgelost:** commits met dezelfde titel als een master-commit sinds de oudste commit die nog
    niet uitgerold is, gaan naar een aparte sectie "Al in productie".
  - Op Done, niet op het bord, wel in het overzicht: PKI-1026, PKI-1034, PKIAM-819, PPP-79,
    PRC-47 (niet-functioneel, eerder van het bord gehaald) en PKI-1090 (script in `ats` zonder
    invloed op de applicatie). Klopt zo; het overzicht laat juist zien wat er echt meegaat.
- Debbie zette het issuenummer niet in de squash-commits van de Dependabot-PR's.
  **Aangepast in de Dependabot-skill:** `gh pr merge --squash --subject "<issue-id> <PR-titel>
  (#<n>)"` in stap 1 en stap 6. Zo blijft het nummer in de commit staan, en worden er minder
  commits als "zonder issue" getoond.
- Dependabot- en Scala Steward-hoofdissues (titel `… upgrades <jaar> w<bereik>`) staan in een
  aparte, compacte sectie onder de inhoudelijke hoofdissues.
- GitHub gaf bij een run herhaaldelijk een 503. `gh()` probeert het nu tot vijf keer, met
  steeds langere pauzes. Een PR-lookup die dan nog mislukt, verschijnt als waarschuwing
  bovenaan het overzicht, zodat een ontbrekend hoofdissue niet onopgemerkt blijft.
- Nieuwe sectie bovenaan: "Configuratie klaar in infra". Per rc-branch staan er het
  hoofdissue, of er commits in de repo's bij horen, hoeveel commits de branch voor en achter
  loopt op `develop` van infra, en welke bestanden erin gewijzigd zijn.
- De GitHub-API faalt soms kortstondig. Daardoor viel PKI-906 bij één run weer uit het
  overzicht. `gh()` probeert het nu drie keer, en een PR-lookup die echt mislukt, meldt het
  script op stderr.

## 2026-11-12, stap 2: `ats`

- Vorige release (`release/12.9.0`) nagekeken: twee commits, "Update versions for release" (de
  gitflow-maven-plugin) en "Update base Docker image for production builds" (met de hand).
- `ats`: Maven, gitflow-maven-plugin 1.21.0. `mvn -B gitflow:release-start` maakte
  `release/12.10.0` zonder vragen (de versie uit de POM, zonder `-SNAPSHOT`) en pusht niet zelf.
- Zonder `sdk env` draaide Maven 3.9.16 in plaats van 3.10.0 uit `.sdkmanrc`.
- Base image: `jib.from.image` in het `pre-release`-profiel van `eclipse-temurin:25.0.4_7-jdk`
  naar `25.0.5_8-jdk@sha256:b8705e93…`. Het veld `digest` uit
  `hub.docker.com/v2/repositories/library/eclipse-temurin/tags` is de multi-arch index: voor
  `25.0.4_7` gaf het precies de digest die al in de POM stond.
- Gepusht; run 43250762775 was groen. RC-tag **`12.10.0-rc.0`** (op `c6fb246c`).
- Lokale checkout was prima voor deze ronde. Bij automatiseren een schone checkout gebruiken.

## 2026-11-12, stap 2: `insights`

- Gradle (multi-module), geen gitflow-plugin; command-line `git flow` 0.4.1 met de config in de
  repo. Vorige release (`1.30.0`) had één commit "Update for the upcoming release": de versie in
  `gradle.properties` en het base image in `application/build.gradle.kts` (de tak
  `buildProfile == "preRelease"` in `jib.from.image`). Afgerond via een PR naar `master` (#236).
- `git flow release start 1.31.0`, daarna dezelfde commit met `1.31.0` en temurin `25.0.5_8`.
  Nog niet gepusht.
- Inventaris per soort: Maven + plugin (`ats`, `cata`, `iam`, `more`, `portal`, `roep`), Gradle +
  plugin (`rostering-application` `hyas.gitflow`, `rostering-engine` `libs.plugins.gitflow`),
  Gradle zonder plugin (`insights`), sbt (`notifications`), npm met image (`rostering-api`,
  `profile-presentation-ui`, `rostering-ui`).

## 2026-11-13, stap 2: `insights` gepusht

- `release/1.31.0` gepusht (`develop` was sinds gisteren niet veranderd). Run 43404376764 van
  "Pre-release build" was groen in ongeveer 5 minuten. RC-tag **`1.31.0-rc.0`** (op `ea99bee`).
- Claude kreeg geen toestemming voor `git push`, dus deze keer pushte ik met de hand via
  `! git -C … push`. Voor het script is dat geen optie; zie de beslissing over de allow-regel.

## 2026-11-13, stap 2: `rostering-application`

- Gradle 9.9.0 en Java 25.0.5 uit `.sdkmanrc`, plugin `com.hyas.gitflow` 1.0.2 (alias
  `hyas.gitflow`). `rostering-engine` heeft dezelfde plugin onder de alias `gitflow`. De
  taak heet `releaseStart`, zonder opties. Uit de bytecode blijkt dat hij niet pusht: hij
  controleert op snapshot-dependencies, haalt `-SNAPSHOT` van de versie in `gradle.properties`
  af, maakt `release/X.Y.Z` en commit "Updated gradle.properties for vX.Y.Z release".
- **Valkuil:** de commit van `releaseStart` nam ook `gradlew.bat` mee, CRLF → LF (globaal
  `core.autocrlf=input`, en het bestand staat met CRLF in de repo). Opgelost door de twee
  commits opnieuw te maken met `gradlew.bat` van `develop`. Het script moet dit opvangen: de
  diff-controle op alleen de versie- en base-imageregel vangt het, en het script zet
  `core.autocrlf=false` in zijn schone clones. Structureel: `.gitattributes` in `insights`,
  `rostering-api`, `rostering-application` en `rostering-engine` (PKI-1125, op het bord).
- Base image in `application/build.gradle.kts` (preRelease-tak van `jib.from.image`) van
  `25.0.4_7-jdk` naar `25.0.5_8-jdk@sha256:b8705e93…`. De Docker Hub-digest van `25.0.4_7`
  kwam overeen met de bestaande pin.
- `release/1.13.0` (`a26b3fc`, `5238682`) gepusht. Run 43406389260 van "Pre-release build" was
  groen in ongeveer 4 minuten. RC-tag **`1.13.0-rc.0`** (op `5238682`). De back-upbranch van
  voor de fix is weggegooid.

## 2026-11-13, stap 2: `notifications`

- sbt 2.0.12, geen gitflow- of `sbt-release`-plugin. Command-line `git flow` met de config in
  de repo, net als bij `insights`. De vorige release (`1.5.0`) had één commit "Update for the
  upcoming release": `ThisBuild / version` en de preRelease-tak van `jibBaseImage`, beide in
  `build.sbt`. Geen CRLF-bestanden in de index.
- `git flow release start 1.6.0` maakte alleen de branch. Daarna dezelfde commit (`d80de6e`) met
  `1.6.0` en temurin `25.0.5_8-jdk@sha256:b8705e93…`. Alleen `build.sbt` gestaged.
- Voor het script: dit is dezelfde soort als `insights` ("git flow + bestanden aanpassen"),
  alleen met andere bestanden en regex'en. Het verschil kan in `data/staging-repos.json`.
- Gepusht. Run 43407696727 van "Pre-release build" was groen in ongeveer 2 minuten. RC-tag
  **`1.6.0-rc.0`** (op `d80de6e`).

## 2026-11-13, stap 2: `rostering-api`

- npm (Node 24), command-line `git flow`. De versie in `package.json` staat op `develop` al op
  de releaseversie (`1.10.0`; npm kent geen `-SNAPSHOT`). Na de release zet "Update for next
  development version" de versie verder en de `Dockerfile` terug op `FROM node:24`. De release
  zelf is daardoor één commit: "Pin base Docker image".
- Base image: `FROM node:24` → `node:24.22.3@sha256:9d266751…` (Docker Hub, regex `24\.\d+\.\d+`).
- De oude pin (`node:24.21.0@sha256:64af38…`, gezet op 2026-09-22) is niet meer de digest die
  Docker Hub nu voor `24.21.0` geeft: de tag is op 2026-10-06 opnieuw gebouwd. De oude index
  bestaat nog. De digest onder een volledige versietag kan dus verschuiven; pinnen op de digest
  blijft daarom zinvol, en de controle "oude digest = Hub-digest" werkt niet voor node.
- Voor het script: bij npm de versie in `package.json` vergelijken met de branchnaam en alleen
  de `FROM`-regel aanpassen.
- `git flow release start 1.10.0`, commit `40f1928`, alleen de `Dockerfile` gestaged. Gepusht;
  run 43408965593 van "Pre-release build" was groen in ongeveer 2 minuten. RC-tag
  **`1.10.0-rc.0`** (op `40f1928`).

## 2026-11-13, stap 2: script, klaarzetfase

- `data/staging-repos.json` uitgebreid: bovenaan `versies` (maven, gradle, sbt, npm: bestand,
  regex van de versieregel, globs voor de snapshot-controle) en `images` (temurin, node,
  node-slim, nginx-alpine: Docker Hub-repo, tagpatroon, patroon van de huidige referentie,
  sjabloon). Per repo `versie`, `image` (bestand en soort) en bij `iam` en `portal` `handmatig`.
- `scripts/staging_release_branches.py [--repos A,B] [--uit BESTAND]`: clones in
  `~/staging-runs/<repo>`, state in `~/staging-runs/state.json`. Met `--uit` komt de samenvatting
  als sectie tussen markers in de uitrolnotitie (vóór de eerste `##`), en een volgende run
  vervangt die sectie. Let op: `staging_overzicht.py --uit` overschrijft het hele bestand, dus
  eerst het overzicht maken en daarna de release branches.
- Eerste run: `cata`, `more`, `roep`, `rostering-engine`, `profile-presentation-ui` en
  `rostering-ui` klaar voor push. De vijf repo's van vandaag kwamen als afwijking (release branch
  staat al op de remote), `iam` en `portal` onder "Met de hand". Diffs van `cata`,
  `profile-presentation-ui` en `rostering-engine` met de hand nagekeken: alleen de versie- en
  imageregel. `rostering-ui`: `nginx:alpine` → `nginx:1.31.8-alpine@sha256:713fc2eb…`.

## 2026-11-13, stap 2: script, `--push`

- `--push` gebouwd: per repo uit de state controleert het of de lokale branch en `origin/develop`
  nog dezelfde SHA hebben als bij het klaarzetten en of er geen release branch op de remote staat.
  Daarna pusht het alleen `refs/heads/release/X.Y.Z` (zonder `--force`). Het volgt de runs met
  `gh run list` (elke 30 seconden, maximaal 40 minuten) en haalt de RC-tag op die naar de gepushte
  commit wijst. Alles komt in `~/staging-runs/state.json` (de bron voor stap 5) en in de sectie
  in de uitrolnotitie.
- Allow-regel in `.claude/settings.json` op `/usr/bin/python3 -I …/staging_release_branches.py`
  (relatief, met `~` en absoluut). De deny op `git push*` blijft staan: alleen het script mag
  pushen.
- Eerste echte run: alle zes groen. RC's: `cata` `4.16.0-rc.0`, `more` `3.16.0-rc.0`,
  `profile-presentation-ui` `1.21.0-rc.0`, `roep` `7.29.0-rc.0`, `rostering-engine`
  `1.13.0-rc.0`, `rostering-ui` `1.6.0-rc.0`.
- De vijf repo's die vandaag met de hand gingen, staan in de uitrolnotitie onder "Afwijkingen"
  (release branch stond al op de remote). Hun RC's staan in de stand hierboven. Bij de volgende
  uitrol gaan ze gewoon door het script.

## 2026-11-13, frontendketen: inventaris (nog niets veranderd)

- Werkwijze tot nu toe (uit de geschiedenis van `portal-employee-ui`): (1) een PR "Prepare release"
  naar `develop` die `portal-ui-common` van een develop-build naar de releaseversie zet (alleen bij
  `portal-employee-ui` en `portal-worker-ui`), (2) een PR `develop` → `master` "Release X.Y.Z" met
  een merge-commit, waarna `master.yml` `npm publish --tag latest` draait, (3) een PR "Update for
  next development version" naar `develop`: minor-versie omhoog en `portal-ui-common` terug naar
  een develop-build. Geen git-tags, geen branch protection.
- De releaseversie staat al op `develop` (npm kent geen `-SNAPSHOT`): `portal-ui-common` 2.0.0,
  `iam-login-ui` 1.1.0, `portal-employee-ui` 2.0.0, `portal-worker-ui` 1.1.0,
  `portal-enrollment-ui` 2.0.0. Geen van deze versies staat al in de npm-repo. Alle develop-builds
  zijn groen.
- **Valkuil:** de dist-tag `latest` wijst bij alle vijf naar een develop-build (bijvoorbeeld
  `2.0.0-develop.fc37b2e`). Een publish vanaf `master` zet hem weer goed. Een releaseversie dus
  altijd uit `package.json` op `master` halen, niet uit `latest`.
- `portal`: de properties `ui.worker.version`, `ui.enrollment.version` en `ui.employee.version` in
  het `pre-release`-profiel (nu 1.0.0, 1.0.0 en 1.13.0); `download-ui.sh` doet `npm pack` op die
  versie. Bij de vorige keer stond de wijziging als losse commit op `develop` ("Upgrade employee
  UI", 2026-08-11). `iam`: `iam.login-ui.version` in het `pre-release`-profiel (nu 1.0.0).

## 2026-11-13, frontendketen: gescript

- `scripts/staging_frontends.py`: plan (alleen clones en `npm view`) en `--uitvoeren`. De volgorde
  komt uit de `in`-velden: `portal-ui-common` eerst, daarna `iam-login-ui` en `portal-enrollment-ui`,
  daarna employee en worker. Status in `~/staging-runs/frontends.json`, sectie tussen
  `<!-- frontends:start -->`-markers in de uitrolnotitie, boven de release branches.
- Of een versie gepubliceerd is, controleert het script met `npm view pkg@X.Y.Z version
  --prefer-online` (exacte versie, geen dist-tag). Het script stopt als `NPM_TOKEN` ontbreekt.
- Lokaal getest in de clone van `portal-employee-ui` (daarna teruggezet): de pin-stap met een
  bestaande develop-build als stand-in verandert één regel in `package.json` (plus de lock file),
  en `npm version 2.1.0 --no-git-tag-version` verandert alleen de drie versieregels. Een pin op
  1.1.0 faalt terecht: die heeft een peer dependency op react-notifications 3.
- `staging_release_branches.py`: `"handmatig"` bij `iam` en `portal` vervangen door `frontends`.
  De regex is getest op de huidige POM's: hij vindt precies één regel per property, die in het
  `pre-release`-profiel. De tabel met release branches heeft een kolom Frontends.
- Omgebouwd naar een graaf: `Keten` in `staging_frontends.py` draait elke frontend in een eigen
  thread met `threading.Event`s voor "gepubliceerd". `staging_release_branches.py` laadt de module
  via het pad (`importlib`, want `-I` zet de scriptmap niet op `sys.path`) en wacht per image-repo
  alleen op zijn eigen frontends. Droog getest met nep-stappen: `portal-ui-common`, `iam-login-ui`
  en `portal-enrollment-ui` starten tegelijk, employee en worker zodra `portal-ui-common`
  gepubliceerd is, en de volgende versie van `portal-ui-common` pas na employee en worker. Faalt
  `portal-ui-common`, dan stoppen employee en worker en krijgt `portal-ui-common` geen volgende
  versie; de rest gaat door.

## 2026-11-13, frontendketen: eerste echte run

- Gepubliceerd: `portal-ui-common` 2.0.0 (#45), `iam-login-ui` 1.1.0 (#34) en
  `portal-enrollment-ui` 2.0.0 (#37); de release-PR's naar `master` gingen goed. `iam` staat klaar
  voor push met `iam-login-ui` 1.0.0 → 1.1.0.
- **Mislukt:** alle PR's naar `develop` (prepare release van employee #257 en worker #56, volgende
  versie van iam-login-ui #35 en enrollment #38). De org-brede verplichte workflow "GitFlow Pull
  Request Validator" (`Flow-Cloud-Systems/.github`, `git-workflow.yml`) accepteert naar `develop`
  alleen `feature/*`, `hotfix/*` en `dependabot/*`. **Opgelost:** branches heten nu
  `feature/prepare-release-X.Y.Z` en `feature/next-version-X.Y.Z`. Daardoor bleef `portal` liggen
  en kreeg `portal-ui-common` terecht geen volgende versie.
- **Bug:** het releasescript schreef de sectie Frontends met zijn eigen markers, waardoor de
  uitrolnotitie door elkaar raakte. Met de hand hersteld; de keten schrijft nu zelf
  (`Keten.uitvoer`).
- **Aangepast:** een frontend die al in de npm-repo stond terwijl `develop` nog op die versie staat,
  krijgt alsnog de volgende versie (bij een herstart na een halve run).
- Herstart na het sluiten van de vier mislukte PR's: alles groen. Employee 2.0.0 en worker 1.1.0
  gepubliceerd (prepare #258/#57, release #259/#58). Volgende versies: `portal-ui-common` 2.1.0
  (#46, als laatste, na employee en worker), `iam-login-ui` 1.2.0 (#36), enrollment 2.1.0 (#39),
  employee 2.1.0 (#260), worker 1.2.0 (#59). `iam` (`release/6.23.0`) en `portal`
  (`release/2.71.0`) klaar voor push; diffs alleen versie, base image en frontendversies.
- `--push` van `iam` en `portal`: beide groen, RC's `6.23.0-rc.0` en `2.71.0-rc.0`. Daarna crashte
  het wegschrijven van de samenvatting: na de JSON-round-trip zijn de frontend-tuples lijsten
  (`% tuple(f)` opgelost). Opnieuw `--push` slaat gepushte repo's over en schreef alleen de
  samenvatting.
- Sectiemarkers als Obsidian-commentaar (`%% … %%`) geprobeerd en teruggedraaid: ook die zijn in
  Live Preview zichtbaar. De HTML-markers blijven; in de leesweergave zijn ze onzichtbaar.

## 2026-11-13, stap 5: infra-PR gescript

- Eerdere RC-PR's in infra: één per hoofdissue ("PKIAM-805 release candidate"), één regel `  tag:` in
  `helm/vars/dev/staging/<map>/values.yaml` (`web-app-<repo>` voor de Maven- en Gradle-webapps, anders
  `<repo>`). Alle dertien bestanden hebben precies één `tag:`-regel.
- `staging_overzicht.py` importeerbaar gemaakt (`analyseer(org, repo, keys, base, head)`). **Bug
  gevonden:** de hotfix-filter vergeleek titels altijd met `master`; bij een frontend zit de release al
  in `master`, waardoor elke commit als cherry-pick wegviel. Nu vergelijkt hij met de base.
- `staging_release_branches.py --tag [--droog]` en de tagstap in `--push`. Droog: 32 hoofdissues, meer
  dan in het overzicht van 2026-11-12 (de Dependabot-parents van daarna, zoals PKP-783). De tag bestond
  nog niet in YouTrack; het command `tag {release candidate}` maakt hem aan.
- `staging_infra_pr.py --droog`: alle dertien tags goed, `feature/PKI-1106-rc` en `feature/PKI-906-rc`
  zonder conflict gerebased, drie lineaire commits bovenop `develop`.
- Dependabot-skill: de zoekregel voor de parent sluit `tag: -{release candidate}` uit.
- Claude mocht de allow-regel voor het nieuwe script niet zelf in `.claude/settings.json` zetten; die
  zet ik zelf.

## 2026-11-13, stap 5: eerste echte run

- `--tag`: 32 hoofdissues getagd. **Bug:** het command `tag {release candidate}` maakte een tag met de
  accolades in de naam. De tag (`123-6`) hernoemd naar `release candidate`; de issues hielden hem. Het
  script voegt de tag nu toe via de REST-API (`POST issues/<id>/tags` met het id van de bestaande tag)
  en stopt als die tag niet precies één keer bestaat. Opnieuw droog: 32 stonden er al.
- `staging_infra_pr.py --opnieuw`: beide rc-branches zonder conflict gerebased, gepusht, PR
  [#999](https://github.com/Flow-Cloud-Systems/infra/pull/999) naar `develop`: drie commits, dertien
  bestanden, mergeable.

## 2026-11-13, skill

- Skill `staging-release-candidates` gemaakt, in de stijl van `dependabot-routine`: vijf stappen met
  stoppunten na het overzicht (inclusief `staging_frontends.py --plan`, het laatste moment vóór de
  frontendreleases) en na het klaarzetten, en een stop bij een conflict in de infra-PR.
- Lopende uitrol herkennen: de nieuwste notitie in `staging-releases/` zonder regel "Gepusht op
  …/pull/…" in de sectie Infra-PR loopt nog, ook als hij van een eerdere dag is. `state.json` krijgt
  de datum van stap 2, niet die van stap 1, dus die datum is geen maat voor de uitrol.
- `staging_infra_pr.py` de eerste keer in een uitrol met `--opnieuw`: `infra.json` bevat anders de PR
  van de vorige uitrol.
- Allow-regels voor de leesscripts van stap 1: `staging_overzicht.py` en `staging_frontends.py
  --plan` (alleen met `--plan`).
- Planpagina ingekort tot beslissingen en logboek. De open vragen waren allemaal beantwoord: de vaste
  lijst staat in `data/staging-repos.json`, de verschillen per repo ook, de frontendversies gaan via
  `frontends`, infra is `Flow-Cloud-Systems/infra`, en "sinds de vorige release" is
  `master...develop`.
