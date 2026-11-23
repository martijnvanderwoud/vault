---
description: Fien, van finished - archiveert elke maandag de LogMyTime-taken waarvan het YouTrack-issue al een week af is
tags: [agents, fien, logmytime, uren]
runs: gebieden/werk/logmytime-archiveren/runs
interval: 8d
proces: Python
---

# Fien

Fien ruimt op wat af is: elke maandag om 8:00 archiveert ze de actieve taken in LogMyTime waarvan
het issue in YouTrack minstens 7 dagen is opgelost en waarop in die 7 dagen geen tijd meer is gelogd.
Een script doet het werk, zonder model: `scripts/fien_runner.py` gebruikt
`scripts/logmytime_taken_archiveren.py`. Plan en beslissingen: [[logmytime-taken-archiveren-plan]].

- Run-notities: `gebieden/werk/logmytime-archiveren/runs/`, één per week (`fien-<jaar>-w<week>.md`,
  onderwerp `taken`). Daarin wat gearchiveerd is, wat wacht en wat nog open is.
- Aandachtspunten: de gearchiveerde taken, taken waarvan het issue niet gevonden is, taken zonder
  issue-ID en taken die door `--max 100` bleven liggen. Een run zonder aandachtspunten wacht niet op
  mij. Heb ik ze bekeken, dan zet ik `status: resolved`; de run van de week erna vervangt hem ook.
- Een vergissing terugzetten: in LogMyTime de taak weer actief maken. Een heropend issue zet ik ook
  zelf terug, Fien doet daar niets mee.
- `interval: 8d`: is er langer dan acht dagen geen run begonnen, dan staat Fien onder `Stil`.
- `proces: Python`: de runner draait als `/usr/bin/python3`, en dat heet `Python` in `ps`.
- Schedule: `scripts/fien/nl.crimsoncricket.fien.plist`, gekopieerd naar `~/Library/LaunchAgents/`.
  Log in `~/.fien/logs/runner.log`.
- Elke run kost twee LogMyTime-requests plus één per gearchiveerde taak (limiet 500 per 24 uur).

## Hervatten

Een `failed`-run heeft in `resume` het commando om de runner opnieuw te starten:
`launchctl kickstart gui/$(id -u)/nl.crimsoncricket.fien`. De nieuwe run maakt een nieuw plan, dus
wat al gearchiveerd was, staat er niet meer in. Doe ik niets, dan pakt de run van de maandag erna het
op. Alleen het plan bekijken: `/usr/bin/python3 -I scripts/fien_runner.py --dry-run`.
