---
description: Werkwijze en logboek voor het voorbereiden van release candidates voor een uitrol naar staging bij Pompkracht, met kandidaten voor automatisering
tags: [pompkracht, release, staging, routine]
---

# Release candidates voor staging

Doel: het voorbereiden van release candidates voor een staging-uitrol stap voor stap
vastleggen, de herhalingen ontdekken en die gaandeweg automatiseren, net zoals bij
[[dependabot-routine]]. Uiteindelijk wordt dit een skill.

Gestart op 2026-11-12.

## Zo deed ik het tot nu toe

1. Het Pompkracht-bord van boven naar beneden aflopen. De swimlanes zijn hoofdissues
   (feature, bug of maintenance), met subtaken die bij verschillende repo's horen.
2. Per swimlane bepalen welke repo's erbij horen en daarvoor RC-builds maken.
3. In het infra-project zoeken naar een branch en worktree met het issuenummer en de
   suffix `rc`. Daarin staan configuratiewijzigingen die samen met die swimlane uit moeten.
4. De image tags van de RC-builds (= Docker image tags) in de juiste bestanden in die
   worktree zetten.
5. Eén PR naar `develop` van infra.

## Beslissingen

- **Altijd alle repo's van een vaste lijst.** Niet per swimlane selecteren: door Dependabot
  verandert er na een paar weken toch overal iets. Dat er geen half werk in `develop` staat,
  bewaak ik zelf.
- **Eén PR met alle image tags** naar `develop` van infra.
- **Configuratiewijzigingen in de `rc`-branches van infra mergen blijft handwerk.** Conflicten
  zitten vaak in secrets-bestanden die in hun geheel versleuteld zijn (één veld met de
  volledige properties van een applicatie). Oplossen kan alleen na decrypten en begrijpen.
- **Scripts eerst.** Wat deterministisch kan, gaat in een script in `scripts/`: dat scheelt
  tokens. Een LLM komt er alleen aan te pas waar die iets toevoegt.
- **"Nog niet uitgerold" = commits in `develop` die nog niet in `master` staan.**
- **Het overzicht van de hoofdissues komt op twee plekken:** eerst in een vault-notitie per
  uitrol om het te controleren, daarna in de beschrijving van de infra-PR.
- **De vaste lijst bestaat alleen uit repo's met een Docker image**, dus niet de lijst van de
  Dependabot-routine. Frontends die in een image meegaan, krijgen een echte release (geen
  RC) naar de private npm-repo. Die versie komt in de POM van het project dat het image
  bouwt, en dat gaat mee in de release branch:
  - `iam-login-ui` → `iam`
  - `portal-ui-common` → `portal-employee-ui` en `portal-worker-ui` → `portal`
    (een extra laag)
  - `portal-enrollment-ui` → `portal` (zonder `portal-ui-common`)
- **Tag `release candidate` op de hoofdissues** zodra de RC's gemaakt zijn. De
  Dependabot-skill slaat parents met die tag over, zodat Debbie daarna een nieuwe swimlane
  begint. Alles blijft op het bord tot de productie-uitrol; dan gaat de tag eraf. (Nog te
  bouwen: tag zetten in de RC-stap, en de zoekregel in de Dependabot-skill aanpassen.)
- **Configuratie in infra staat bovenaan in het overzicht**, want daar controleer ik het. Voor
  de rc-branches in infra maak ik nooit vooraf een PR; daar hoeft niet naar gezocht te worden.
- **Release branches via één generiek script in de vault**, met de verschillen per repo als
  configuratie in `data/staging-repos.json`. Geen just-recipe per project: er zijn geen
  programmerende collega's, en zo blijft het snel aan te passen zolang we nog leren. Het script
  werkt in schone clones (niet in `~/IdeaProjects`) en pusht met mijn eigen credentials, zodat
  `pre-release.yml` gewoon start. (Een CI-workflow die pusht met `GITHUB_TOKEN` zou dat niet
  doen.)
- **Eén stoppunt voor alle repo's, niet één per repo.** Het script bereidt alle release
  branches voor zonder te pushen en controleert per repo zelf of de diff alleen de versieregel
  en hoogstens de base-imageregel raakt. De samenvatting (afwijkingen bovenaan) komt in dezelfde
  notitie als het staging-overzicht: één controlemoment. Daarna één keer `--push`.
- **Hoofdissues worden afgeleid uit de commits.** Uit de issuenummers in de commits sinds de
  vorige release volg je de parent, en zo nodig weer de parent daarvan, tot je bij het
  hoofdissue uitkomt dat op het bord staat.

## Gewenste werkwijze (eerste schets)

Automatisch:

1. Per repo uit de vaste lijst een release branch maken en pushen. Dat gaat per project
   soms anders.
2. CI bouwt de RC en zet er een tag op. Die tags verzamelen.
3. Uit de commits per repo de hoofdissues afleiden en een overzicht maken: hoofdissue,
   repo's, issues.
4. Per hoofdissue zoeken of er in infra een `rc`-branch of worktree voor is.
5. Een PR naar `develop` van infra maken met alle image tags.

Handmatig (stoppunten):

- Het overzicht van de hoofdissues controleren: klopt het dat dit uitgerold wordt?
- De `rc`-branches van infra mergen en conflicten oplossen.

## Volgende stap

Stap 1 (overzicht) is klaar op 2026-11-12. Stap 2 (release branches) is bezig: per soort repo
één repo met de hand, daarna een script (zie de beslissingen). Start in `~/vault` met: "Ga verder
met stap 2 uit [[release-candidates-staging]]".

Stand aan het eind van 2026-11-12:

- `ats` (Maven + plugin): klaar, RC `12.10.0-rc.0`.
- `insights` (Gradle zonder plugin): `release/1.31.0` staat **lokaal, nog niet gepusht**. De diff
  is gecontroleerd en goedgekeurd. Eerst pushen en de run volgen.
- Daarna met de hand: `rostering-application` (Gradle + plugin; kijk ook of `rostering-engine`
  dezelfde plugin heeft), `notifications` (sbt), `rostering-api` (npm met image).
- Dan het script; de overige Maven-repo's (`cata`, `more`, `roep`) en de npm-images
  (`profile-presentation-ui`, `rostering-ui`) gaan daar meteen doorheen.
- Als laatste de frontendketen naar `portal` en `iam`.
- De lokale checkouts van `ats` en `insights` staan op hun release branch, niet op `develop`.

## Open vragen

- Welke repo's staan precies op de vaste lijst? (Voorstel staat in het antwoord van
  2026-11-12; nog bevestigen.)
- Hoe maak je per project een release branch, en waar zitten de verschillen? (Maven met
  gitflow-maven-plugin, Gradle met een gitflow-plugin of met command-line git-flow; per repo
  vastleggen.)
- Frontend-releases: hoe komt de versie in de POM van `portal` (bij `iam`: property
  `iam.login-ui.version` in het `pre-release`-profiel)?
- Infra: hoe heet de repo, waar staan de worktrees, en welke bestanden bevatten de image tags?
- Hoe bepaal je "sinds de vorige release": vanaf `master`, of vanaf de laatste tag?

## Procedure

Per stap: wat ik doe, met welk gereedschap, en per repo of eenmalig.

1. **Overzicht maken** (script): `/usr/bin/python3 -I scripts/staging_overzicht.py --uit
   gebieden/werk/staging-releases/<datum>.md`. Daarna controleer ik het zelf (stoppunt).
2. **Release branch per image-repo** (per repo, nu nog met de hand):
   1. `master` en `develop` bijwerken (`git pull --ff-only`).
   2. `sdk env` (anders draait de verkeerde Maven- of Java-versie), dan de release branch
      maken met de gitflow-tool van het project. Die haalt `-SNAPSHOT` van de versie af en
      commit ("Update versions for release").
   3. Het base Docker image in het `pre-release`-profiel naar de nieuwste versie pinnen en
      committen ("Update base Docker image for production builds"). Dit is het enige wat in
      deze workflow wordt bijgewerkt; de parent doet Dependabot.
   4. Stoppunt: de diff `develop..release/X.Y.Z` controleren.
   5. Pushen. `pre-release.yml` leidt `X.Y.Z-rc.N` af, bouwt met Jib en zet de git-tag. Die
      git-tag is de image tag.

## Automatiseringskandidaten

| Stap | Wat herhaalt zich | Idee | Status |
| --- | --- | --- | --- |
| 2 | Nieuwste base image + digest opzoeken | Docker Hub tags-API, `sort -V` op `25.0.x_y-jdk` | idee |
| 2 | Release branch, pin, push, wachten op tag | script per repo in een schone checkout | idee |

## Logboek

### 2026-11-12, eerste ronde

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
- Eerste resultaat: [[2026-11-12]] in `staging-releases/`.
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

### 2026-11-12, stap 2: `ats`

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

### 2026-11-12, stap 2: `insights`

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

