---
description: Aanvullingen op de Dependabot-routine voor notifications (Scala Steward in plaats van Dependabot)
repo: Flow-Cloud-Systems/notifications
autonoom: true
authors: [app/dependabot, app/flow-cloud-scala-steward]
---

# Dependabot-routine: notifications

Scala-project. Dependabot ondersteunt Scala niet, de dependency-updates komen van Scala
Steward. Dependabot doet hier alleen `github-actions`. Handel in de routine de PR's van beide
auteurs uit de frontmatter `authors` af.

## Stap 0. YouTrack-issue

- YouTrack-project: `pompkracht-notifications` (key `PN`).
- Board: `Pompkracht Kanban Board`, sprint `Kanban workflow`.
- Titel parent: `Scala Steward upgrades <jaar> w<bereik>`. Zoek de parent dus met
  `summary: "Scala Steward upgrades"`.
- Titel subtask: `Apply Scala Steward upgrades <jaar> w<week>`.

## Stap 4. Schone install

sbt-project (`build.sbt`):

```bash
sbt "clean; scalafmtCheckAll; compile; test" > <scratchpad>/build.log 2>&1
grep -nE "\[error\]|\[warn\]|tests passed|tests failed" <scratchpad>/build.log
```

- De log gaat naar de scratchpad, want hij is lang. Autonoom schrijf je het doel van de
  redirect volledig uit: `/Users/martijn/dependabot-runs/.scratch/notifications/build.log`
  (zie de regel over redirects in de skill). Draai de build met een timeout van 600000, want
  hij duurt langer dan de standaard van 2 minuten. Bekijk bij een exitcode die niet 0 is ook
  het einde van de log met `tail`. Exitcode 1 van `grep` betekent alleen dat niets matchte.
- De root-`test` draait `testFull` voor alle modules behalve `integration`. Dat is bewust: de
  incrementele `test` van sbt 2 draait bij een dependency-update vaak geen enkele test. De
  integratietests draaien in de `Develop build` van stap 8.
- Controleer dat de log `N tests passed` toont met N boven 0. `Passed: Total` zegt niets, want
  ZIO meldt zijn tests alleen als `N tests passed`. Is N 0, dan geldt de regel over 0 tests
  uit stap 4 van de skill.
- sbt 2 vereist `;` tussen taken.

## Stap 5. Kwetsbaarheden patchen zonder breaking changes

Lees de dependencies per project uit, voor `Compile` en `Test`, zonder `root` en zonder de
sbt-plugins. Doe hetzelfde zonder overrides. `sbt_deps.py` doet dat in één keer en sluit
daarna de achtergrondserver van sbt af, want de `set` voor de lijst zonder overrides blijft
daar anders hangen. Het script sluit die server ook vooraf af, zodat een `set` uit een eerdere
sessie de lijst met overrides niet beïnvloedt. Draai het met een timeout van 600000: als de
tool het script afbreekt, slaat het de `sbt shutdown` aan het eind over.

```bash
/usr/bin/python3 -I ~/vault/.claude/skills/dependabot-routine/scripts/sbt_deps.py <scratchpad>/deps
/usr/bin/python3 -I ~/vault/.claude/skills/dependabot-routine/scripts/osv_jvm.py <scratchpad>/deps/met/*.txt --exclude nl.pompkracht
/usr/bin/python3 -I ~/vault/.claude/skills/dependabot-routine/scripts/check_overrides.py --sbt build.sbt --tree <scratchpad>/deps/zonder/*.txt
```

- De projecten komen uit `sbt projects`, zodat een nieuwe module vanzelf meegaat. Controleer dat
  de regel `projecten (<n>)` alle modules toont (nu 10, zonder `root`). Stopt het script met
  `geen projecten gevonden`, dan maakt sbt de uitvoer anders op en klopt het filter niet meer.
  Leg dat aan mij voor, net als elke andere exitcode die niet 0 is. Autonoom: stop.
- Overrides staan in `ThisBuild / dependencyOverrides` in `build.sbt`, de versies in
  `project/Versions.scala`.
- Patchen: een directe dependency pas je aan in `project/Versions.scala`. Een transitieve krijgt
  een regel in `dependencyOverrides`, een `val` in `Versions.scala` en een comment in de
  lijst boven `dependencyOverrides`:
  `// <artifact> <huidige versie> (via <bron>): <CVE> (fixed in <doel>)`.
- Een override verwijderen: haal de regel, de comment en de `val` weg, voor zover niets anders
  die `val` gebruikt.
- Controleer na het patchen of verwijderen met `sbt "<project>/Compile/dependencyTree list"`
  dat de versie klopt, draai de build uit stap 4 en scan opnieuw.
