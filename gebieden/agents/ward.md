---
description: Ward, de bewaker van system health - controleert elke ochtend de hosts van Pompkracht en meldt een verandering
tags: [agents, ward, monitoring]
runs: gebieden/werk/ward-runs
interval: 2d
proces: Python
---

# Ward

Ward controleert elke dag om 9:00 de 20 hosts van Pompkracht uit `~/.ssh/config`. De runner
(`scripts/ward/ward_runner.py`, onder launchd: `nl.crimsoncricket.ward`) draait de checks zonder
model en vergelijkt ze met de referentie in `data/ward/baseline.json` en met de vorige run. Alleen
als een host slechter wordt, start een sessie met Ward: die gaat de bevinding na, schrijft een
notitie in `gebieden/werk/ward-meldingen/` en mailt mij. Herstel naar `ok` geeft daar een korte
notitie en een melding, zonder model.

- Run-notities: `gebieden/werk/ward-runs/`, één per check (`ward-<check>.md`; het `onderwerp` is
  de check, zoals `hosts` of `cpu`). De runner schrijft ze bij elke run opnieuw, dus er staat altijd alleen de laatste run. Ze staan niet
  in git; de geschiedenis staat in `gebieden/werk/ward-meldingen/` en in de logs.
- Een check met hosts die niet `ok` zijn, heeft die als aandachtspunten. Die blijven op het
  dashboard tot de host weer `ok` is, of tot ik de referentie bewust aanpas.
- Is er langer dan twee dagen geen run begonnen (`interval: 2d`), bijvoorbeeld omdat de laptop
  uit stond, dan staat Ward op het dashboard onder `Stil`.
- `proces: Python`: de runner draait als `/usr/bin/python3`, en dat heet `Python` in `ps`.
- Logs: `~/.ward/logs/` (`runner.log` en per sessie een `.jsonl`), status in `~/.ward/status.json`.
- Plan en beslissingen: [[ward-plan]].

## Hervatten

Een `failed`-run (de sessie met Ward mislukte) heeft in `resume` het commando om de runner opnieuw
te starten: `launchctl kickstart gui/$(id -u)/nl.crimsoncricket.ward`. De status van de laatste
geslaagde run blijft staan, dus de nieuwe run ziet dezelfde verandering en start Ward opnieuw. Doe
ik niets, dan probeert de run van de volgende ochtend het ook.
