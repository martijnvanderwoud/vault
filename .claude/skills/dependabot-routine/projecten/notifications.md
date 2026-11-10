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
