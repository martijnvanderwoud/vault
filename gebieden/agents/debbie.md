---
description: Debbie, de autonome Dependabot-routine - handelt elke week de Dependabot-PR's in mijn repo's af
tags: [agents, dependabot]
runs: gebieden/werk/dependabot-runs
lijsten: [prs]
interval: 8d
---

# Debbie

Debbie handelt de Dependabot- en Scala Steward-PR's af in de projecten met `autonoom: true` in
`.claude/skills/dependabot-routine/projecten/`. De runner (`scripts/dependabot_runner.py`, onder
launchd elk half uur) start per project met open PR's waarvan de checks klaar zijn een run met de
skill [[dependabot-routine]]. Per project (het `onderwerp`) loopt hooguit één run tegelijk.

Dependabot opent elke week PR's, dus Debbie draait minstens één keer per week. Is er langer dan acht
dagen geen run begonnen (`interval: 8d`), dan staat ze op het dashboard onder `Stil`.

- Run-notities: `gebieden/werk/dependabot-runs/`, één per run (`<jaar>-w<week>-<project>.md`).
- Logs: `~/dependabot-runs/.logs/`.
- Plan en beslissingen: [[dependabot-routine-autonoom-plan]].

## Hervatten

Een `paused`- of `failed`-run heeft in `resume` het commando, zoals
`cd ~/dependabot-runs/cata && claude --resume <sessie>`. Na een hervatting zet de runner de run op
`done` zodra er een verslag van Debbie in het issue staat. Zonder issue geef ik hem vrij met
`status: resolved`. Een `paused`- of `failed`-run blokkeert zijn project tot hij is afgehandeld.
