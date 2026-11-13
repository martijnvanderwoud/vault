---
description: Beslissingen achter het voorbereiden van release candidates voor een staging-uitrol bij Pompkracht
tags: [pompkracht, release, staging]
cssclasses: [wide-page]
---

# Release candidates voor staging: beslissingen

Waarom [[release-candidates-staging]] werkt zoals het werkt. Hoe het zo gekomen is, staat in
[[release-candidates-staging-logboek]].

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
  begint. Alles blijft op het bord tot de productie-uitrol; dan gaat de tag eraf.
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
- **Het script pusht zelf, met een allow-regel op alleen dat script.** Geen algemene
  `git push`-toestemming voor Claude: in `.claude/settings.json` komt een allow-regel op
  `/usr/bin/python3 -I ~/vault/scripts/<release-script>.py`. Het script bepaalt wat er gepusht
  mag worden: alleen `release/*`-branches van repo's uit `data/staging-repos.json`, en alleen
  na een geslaagde diff-controle. Met de hand pushen is geen onderdeel van de werkwijze.
- **Het script maakt de release branches zelf, zonder gitflow-tools** (besloten 2026-11-13). Alle
  Maven-repo's hebben één `pom.xml`, dus de tools doen niets anders dan een branch vanaf
  `develop`, `-SNAPSHOT` van één regel afhalen en committen. Zelf doen is sneller (geen
  `sdk env`, geen Maven- of Gradle-start), voorkomt de CRLF-valkuil van `releaseStart` en geeft
  één codepad. De snapshot-controle van de plugins neemt het script over: na het aanpassen van
  de versie mag er geen `-SNAPSHOT` meer in de buildbestanden staan.
- **Eén commit per repo: "Prepare release X.Y.Z"**, met de versie en het base image samen. De
  berichten die per soort verschilden, vervallen.
- **Clones in `~/staging-runs/<repo>`**, naar het voorbeeld van `~/dependabot-runs`. Niet in
  `~/.cache`: tussen het klaarzetten en `--push` staat daar de enige kopie van de release
  branches en het state-bestand.
- **Verschillen per repo als configuratie in `data/staging-repos.json`:** per repo het bestand
  en de regex van de versieregel (bij npm alleen lezen uit `package.json`) en het bestand en de
  soort van het base image. De soorten (`temurin`, `node`, `node-slim`, `nginx-alpine`) staan één
  keer bovenaan, met de Docker Hub-repo, het tagpatroon en het patroon van de huidige regel.
- **Diff-controle per repo:** alleen de geconfigureerde bestanden veranderen, elke gewijzigde
  regel past voor en na in het verwachte patroon, en elke regex matcht precies één keer. Een
  repo die niet slaagt, slaat `--push` over. `--push` controleert ook dat de branch en
  `origin/develop` nog gelijk zijn aan de stand bij het klaarzetten, pusht alleen
  `release/X.Y.Z` (nooit `--force`) en verzamelt de RC-tags in de notitie en in JSON voor stap 5.
- **Frontendversies in de release branch van `iam` en `portal`** (besloten 2026-11-13), niet als
  losse commit op `develop`. Per repo staat in `data/staging-repos.json` onder `frontends` welke
  property bij welke frontend hoort. `staging_release_branches.py` haalt de versie uit
  `package.json` op `master` van de frontend (niet uit de dist-tag `latest`, die soms verkeerd
  staat in Nexus), vervangt alleen een X.Y.Z-waarde (de property bovenaan met `develop` blijft
  staan) en neemt die regels mee in de diff-controle. Staat de frontend in het plan van
  `staging_frontends.py` maar is hij nog niet gepubliceerd, dan slaat het de repo over.
- **Frontends zonder stoppunt, parallel; image-repo's met één gezamenlijk stoppunt** (besloten
  2026-11-13). `staging_release_branches.py` (klaarzetten) start de frontendketen uit
  `staging_frontends.py`: elke frontend in een eigen thread, die alleen wacht op de frontends die
  hij nodig heeft. Intussen worden de image-repo's zonder frontends meteen klaargezet; `iam` wacht
  alleen op `iam-login-ui`, `portal` op zijn drie frontends. Starten is niet pushen: alle
  image-repo's samen hebben één stoppunt met de diff-controle, en daarna één `--push`.
- **De frontendketen pusht en merget zelf**, onder de allow-regel van het releasescript, maar alleen
  bij frontends uit de config: `prepare-release/*` en `next-version/*` (nooit `--force`) en PR's naar
  `develop` en `master`, na groene checks. Automatische controles in plaats van een stoppunt:
  develop moet nog op de stand uit het plan staan, de diff mag alleen de verwachte regels raken,
  en de versie moet daarna precies zo in de npm-repo staan.
- **Volgorde in de frontendketen:** eerst publiceren, dan pinnen. "Prepare release" van
  `portal-employee-ui` en `portal-worker-ui` kan pas als `portal-ui-common` echt in de npm-repo
  staat. De versie wordt letterlijk ingezet (`npm install --package-lock-only --prefer-online
  pkg@X.Y.Z`, wat `^X.Y.Z` oplevert). "Update for next development version" volgt per frontend
  direct na zijn publicatie, behalve bij `portal-ui-common`: die wacht ook op employee en worker.
  Elke push naar `develop` van `portal-ui-common` start namelijk (via de dispatch na de build)
  `update-lock-file` in employee en worker, en dat zet `portal-ui-common` weer op `@develop`. Te
  vroeg zou dat de pin ongedaan maken voordat de release-PR gemerged is.
- **Infra-PR: rc-branches gerebased, niet gemerged** (besloten 2026-11-13). `staging_infra_pr.py` maakt
  `feature/staging-rc-<datum>` vanaf `develop` (de GitFlow-validator laat naar `develop` alleen
  `feature/*` toe), rebaset daar de rc-branches op van hoofdissues die in de release zitten, en zet
  daarna in één commit de image tags. Lineaire geschiedenis, geen merge-commits. Conflicten los ik
  met de hand op in `~/staging-runs/infra` (`git rebase --continue`, daarna het script opnieuw).
  Geen apart stoppunt: slaagt alles, dan pusht het script en maakt het de PR naar `develop`. Mergen
  doe ik zelf.
- **RC-tags uit GitHub, niet uit de state:** per image-repo met een open release branch de hoogste
  `X.Y.Z-rc.N`, en die moet op de tip van de branch staan (anders loopt de build nog). Zo tellen ook
  de RC's mee die met de hand gemaakt zijn. Het pad van de tag-regel per repo staat onder `infra`
  in `data/staging-repos.json`.
- **De tag `release candidate` komt direct na het pushen van de release branches** (besloten
  2026-11-13), in `staging_release_branches.py --push`, niet pas bij de infra-PR. Vanaf dat moment
  gaat nieuw werk op `develop`, ook van Dependabot, niet meer mee. De hoofdissues komen uit wat
  echt in de release zit: `master...release/X.Y.Z` per image-repo, en bij een frontend de
  release-merge naar `master` ten opzichte van zijn eerste parent. Niet uit het overzicht van
  stap 1: daarna kan `develop` nog veranderd zijn.
- **Hoofdissues worden afgeleid uit de commits.** Uit de issuenummers in de commits sinds de
  vorige release volg je de parent, en zo nodig weer de parent daarvan, tot je bij het
  hoofdissue uitkomt dat op het bord staat.
