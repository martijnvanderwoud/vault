---
description: Ward, de bewaker van system health - controleert elke ochtend de hosts van Pompkracht en meldt een verandering
tags: [agents, ward, monitoring]
runs: gebieden/werk/ward-bewaking/runs
interval: 2d
proces: Python
---

# Ward

Ward controleert elke dag om 9:00 de 20 hosts van Pompkracht en meldt alleen een verandering. Een
script doet de checks; een sessie met Ward start alleen als een host slechter wordt. Hoe het werkt:
[[ward-bewaking]].

- Run-notities: `gebieden/werk/ward-bewaking/runs/`, één per check (`ward-<check>.md`), bij elke
  run opnieuw geschreven. Hosts die niet `ok` zijn, staan erin als aandachtspunten.
- `interval: 2d`: is er langer dan twee dagen geen run begonnen, dan staat Ward onder `Stil`.
- `proces: Python`: de runner draait als `/usr/bin/python3`, en dat heet `Python` in `ps`.

## Hervatten

Een `failed`-run (de sessie met Ward mislukte) heeft in `resume` het commando om de runner opnieuw
te starten: `launchctl kickstart gui/$(id -u)/nl.crimsoncricket.ward`. De status van de laatste
geslaagde run blijft staan, dus de nieuwe run ziet dezelfde verandering en start Ward opnieuw. Doe
ik niets, dan probeert de run van de volgende ochtend het ook.
