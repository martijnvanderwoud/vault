---
description: Beslissingen achter de Dependabot-routine en Debbie, de agent die hem autonoom draait, met de reden erachter
tags: [dependabot, routine, debbie]
cssclasses: [wide-page]
---

# Dependabot-routine: beslissingen

Waarom [[dependabot-routine]] werkt zoals het werkt. Hoe het zo gekomen is, staat in
[[dependabot-routine-logboek]].

## De routine

- **Groen is groen: alle checks geslaagd.** Dat is het criterium om te squash-mergen, ook zonder
  toezicht en ook bij een major. We mergen naar `develop`, en in sommige projecten ook naar
  `master`, maar die komen niet zomaar automatisch in productie. Fouten die hieruit komen zie ik
  snel in mijn development-omgeving, en dat is juist wat ik wil. De projectstappen, zoals een
  release-PR, draaien dus ook autonoom.
- **Nooit een downgrade.** Een fix die een versie omlaag zet, voer ik niet door; `npm audit fix
  --force` valt daaronder. Blijft een kwetsbaarheid daardoor staan, dan komt hij in het verslag.
- **Patchen hoort in de routine, niet alleen melden.** JVM is de standaard (scan met OSV via
  `osv_jvm.py`), npm de uitzondering, omdat de meeste projecten JVM zijn. OSV is geaccepteerd als
  tegenhanger van de IntelliJ-scanner: bij `cata` vond IntelliJ niets wat OSV miste.
- **Overrides bij twijfel laten staan.** Een override die volgens `check_overrides.py` misschien
  weg kan, maar via een andere override loopt, blijft staan en komt in het verslag. Na het
  weghalen controleert de routine dat de opgeloste versie niet lager is dan de override (bij `ats`
  werd `bcpkix` anders 1.85, onder de fix).
- **Een rode PR: de oorzaak uit de CI-log, niet alleen melden.** Wordt de nieuwe versie nog niet
  ondersteund (zoals graphql 17 door `@apollo/server` in `rostering-api`), dan de PR sluiten en de
  major uitsluiten in `dependabot.yml`, zodat minor- en patch-updates blijven komen.
- **Eén eigen PR voor alles wat de routine wijzigt** (`.sdkmanrc`, audit-fixes, patches), om het
  aantal builds te beperken. Issuenummer van de subtask in branchnaam en commitbericht. PR's,
  commits en verslagen in het Engels.
- **`.sdkmanrc` zonder vragen bijwerken** binnen de major, met behoud van de vendor-suffix
  (`-tem`). Een nieuwe Java-major noemt het verslag, maar voert de routine niet door.
- **Na de merges de build op de base branch afwachten.** De checks van een latere PR liepen tegen
  de oude base; pas de build op `develop` (en `master`) toont de samengevoegde stand.
- **Wat de routine negeert:** deprecation-warnings in gegenereerde API-clients, de JVM-melding
  `Sharing is only supported for boot loader classes`, en kwetsbaarheden in webjars in `roep` en
  `cata` (legacy die naar React wordt geport).
- **Het YouTrack-project volgt uit de repo** (`projecten/<repo>.md`). Bij PRC en PMD een taak zonder
  parent. Na de routine kijk ik zelf wat er gebeurd is en schrijf ik eventueel uren.

## Autonoom: opzet

- **Lokale schedule die GitHub pollt, geen PR-trigger en geen hook.** Eén launchd-job kijkt elk
  half uur met `gh` of er per repo PR's zijn waarvan alle checks klaar zijn. Bij "PR opened" lopen
  de checks nog, meerdere PR's zouden meerdere runs tegelijk starten, en hooks reageren alleen op
  gebeurtenissen binnen een sessie.
- **De check of er werk is, zit in een script, niet in Claude.** Een run zonder werk kostte $0,29 op
  een prompt van tienduizenden tokens; 21 repo's elk half uur zijn ongeveer 1000 starts per dag.
  Prompt caching vangt dat maar voor een klein deel op.
- **Niet in de cloud.** Een cloud-routine heeft standaard alleen Java 21 en geen sbt, mag alleen
  naar `claude/`-branches pushen (botst met `feature/` en de GitFlow-validator) en kan niet bij de
  skill in de vault. Een GitHub Action moet per repo, en runs met Dependabot als trigger krijgen
  standaard geen gewone Actions-secrets.
- **Eigen clones** in `~/dependabot-runs/<repo>`, nooit mijn working copies in `~/IdeaProjects`. Git
  via HTTPS met `gh` als credential helper, want onder launchd is er geen SSH-agent.
- **Debbie draait op Opus 5.5.** Ze draait alleen als er werk is, ongeveer één keer per repo per
  week, dus het prijsverschil met Sonnet telt weinig. Het werk vraagt oordeel zonder toezicht: de
  oorzaak van een rode PR, patchen zonder breaking change, en vooral op tijd stoppen. Het model is
  een optie van de runner (`--model`).
- **De agent heet Debbie,** vanwege Dependabot. De naam staat in de sessienaam, de run-notities en
  boven de comments, die onder mijn YouTrack-account staan.

## Autonoom: grenzen

- **Geen `bypassPermissions`, maar een vaste allowlist** in `scripts/dependabot-runner/settings.json`
  met `--permission-mode dontAsk` en `--permission-prompts none`. De run leest CI-logs, en die zijn
  niet te vertrouwen. De lijst bevat geen paden van mijn machine, alleen `~/` en `{owner}/{repo}`.
- **Alleen mijn instellingen die nodig zijn.** `--setting-sources project,local` houdt mijn
  gebruikersinstellingen buiten de run, `claudeMdExcludes` mijn globale CLAUDE.md, en
  `--strict-mcp-config` laadt alleen YouTrack (token uit `.env` via `${YOUTRACK_TOKEN}`).
- **`env.sh` en de scripts van de skill staan in de vault,** waar de run niet mag schrijven. Een
  bestand dat voor elk commando wordt gesourced, zou anders de allowlist omzeilen.
- **Geen `workflow`-scope voor `gh`.** Met die scope kan een run die onbetrouwbare CI-logs leest,
  workflows wijzigen die bij de secrets kunnen. Een nieuwe Maven-versie in `cata` en `roep` (die
  ook in `.github/workflows/` staat) laat Debbie daarom staan en noemt ze in het verslag.
- **Geen lussen, subshells, `$(...)` of `; echo $?` in de skill:** die vallen buiten elke allowlist.
  Wat een lus nodig heeft, zoals de dependency-lijsten van sbt, doet een script van de skill.
- **Twee klassen stoppunten.** Bij elk punt waar de skill iets voorlegt, staat `Autonoom: stop`
  (pauzeren en wachten) of `Autonoom: verslag` (aandachtspunt, doorgaan). Een situatie zonder regel
  is een stop, tenzij hij maar één PR raakt en de rest door kan.

## Status en afhandelen

- **De runner schrijft de status, niet het model,** zodat een vastgelopen run zichtbaar blijft als
  `failed`. Debbie eindigt met regels die de runner leest (`RUN_ATTENTION`, `RUN_STATUS`).
- **Het issue in YouTrack is de bron voor "afgehandeld".** Een run zonder aandachtspunten zet de
  subtask zelf op `Done`; met aandachtspunten of na een pauze zet ik hem op `Done` als ik het heb
  afgehandeld. `resolved` alleen voor een run zonder issue. Een vinkje `gezien` naast het issue
  viel af: dubbel werk.
- **Een `paused`- of `failed`-run blokkeert zijn repo,** anders start een run die steeds crasht of
  stopt elk half uur opnieuw. Een run die vastloopt, raakt alleen zijn eigen repo.
- **Hervatten kan op twee manieren:** `claude --resume` met mijn besluit als prompt, of als de sessie
  weg is een nieuwe sessie die de stand opbouwt uit het pauze-comment (`Report so far`, `State`).
  Comments worden nooit bewerkt; een correctie is een nieuw comment.
- **De run-notities staan in git,** de logs niet. De notities zijn klein en hun geschiedenis is
  nuttig. Sinds 18-11 staan ze op het gezamenlijke agents-dashboard ([[agents-dashboard]]); de
  watcher doet wat voor alle agents geldt (melden, `issue_state`, afgebroken runs).

## Uitrol

- **De allowlist van repo's staat in de projectbestanden** (`autonoom: true`), niet in de plist.
  Eén repo uitzetten is zo een wijziging in de vault, zonder launchd te herladen.
- **Alles in één keer aan, niet in groepjes** (11-11). Het risico van een fout in de skill die in
  veel repo's tegelijk terugkomt, is opruimwerk, geen schade, en de releases naar `master` zijn
  niet gevaarlijk (zie "Groen is groen").
- **Een geweigerd commando dat alleen leest, mag erbij** (19-11, na week 47): `gh pr diff` en
  `npm pkg get`. Ze blokkeerden niets, maar elk geweigerd commando kost een omweg.
