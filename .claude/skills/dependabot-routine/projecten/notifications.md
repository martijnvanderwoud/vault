---
description: Aanvullingen op de Dependabot-routine voor notifications (Scala Steward in plaats van Dependabot)
---

# Dependabot-routine: notifications

Scala-project. Dependabot ondersteunt Scala niet, de dependency-updates komen van Scala
Steward. Dependabot doet hier alleen `github-actions`. Handel in de routine de PR's van beide
auteurs af: draai de `gh pr list` uit stap 0 en stap 1 met `--author "app/dependabot"` en met
`--author "app/flow-cloud-scala-steward"`. Bij stap 0 stop je alleen als beide 0 zijn.

## Stap 0. YouTrack-issue

- YouTrack-project: `pompkracht-notifications` (key `PN`).
- Board: `Pompkracht Kanban Board`, sprint `Kanban workflow`.
- Titel parent: `Scala Steward upgrades <jaar> w<bereik>`. Zoek de parent dus met
  `summary: "Scala Steward upgrades"`.
- Titel subtask: `Apply Scala Steward upgrades <jaar> w<week>`.

## Stap 4. Schone install

sbt-project (`build.sbt`):

```bash
sbt "clean; scalafmtCheckAll; compile; test"
```

- De root-`test` draait `testFull` voor alle modules behalve `integration`. Dat is bewust: de
  incrementele `test` van sbt 2 draait bij een dependency-update vaak geen enkele test. De
  integratietests draaien in de `Develop build` van stap 8.
- Controleer dat de log `N tests passed` toont met N boven 0. `Passed: Total` zegt niets, want
  ZIO meldt zijn tests alleen als `N tests passed`. Is N 0, dan geldt de regel over 0 tests
  uit stap 4 van de skill.
- sbt 2 vereist `;` tussen taken.

## Stap 5. Kwetsbaarheden patchen zonder breaking changes

Lees de dependencies per project uit, voor `Compile` en `Test`, zonder `root` en zonder de
sbt-plugins. Doe hetzelfde zonder overrides. De `set` blijft in de achtergrondserver van sbt
hangen, dus sluit die daarna altijd af met `sbt shutdown`. Gebruik hieronder `<scratchpad>`
als absoluut pad.

```bash
rm -rf <scratchpad>/deps && mkdir -p <scratchpad>/deps/met <scratchpad>/deps/zonder
projects=$(sbt projects 2>&1 | grep -E '^\[info\][[:space:]]+[A-Za-z0-9_-]+$' | awk '{print $2}' | grep -vx root)
echo $projects
met=""; zonder="set ThisBuild / dependencyOverrides := Seq();"
for p in $projects; do
  for c in Compile Test; do
    met="$met $p/$c/dependencyTree list --out <scratchpad>/deps/met/$p-$c.txt;"
    zonder="$zonder $p/$c/dependencyTree list --out <scratchpad>/deps/zonder/$p-$c.txt;"
  done
done
sbt "${met%;}"
sbt "${zonder%;}"
sbt shutdown
/usr/bin/python3 -I ~/vault/.claude/skills/dependabot-routine/scripts/osv_jvm.py <scratchpad>/deps/met/*.txt --exclude nl.pompkracht
/usr/bin/python3 -I ~/vault/.claude/skills/dependabot-routine/scripts/check_overrides.py --sbt build.sbt --tree <scratchpad>/deps/zonder/*.txt
```

- De projecten komen uit `sbt projects`, zodat een nieuwe module vanzelf meegaat. Controleer dat
  `echo $projects` alle modules toont (nu 10, zonder `root`): een lege lijst betekent dat sbt
  de uitvoer anders opmaakt en het filter niet meer klopt. Leg dat aan mij voor. Autonoom:
  stop.
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
