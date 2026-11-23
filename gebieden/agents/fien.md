---
description: Fien, van finished - ruimt op wat af is - elke maandag LogMyTime-taken waarvan het YouTrack-issue al een week af is, elke dag oude npm-develop-versies in Nexus
tags: [agents, fien, logmytime, uren, nexus, npm]
runs: gebieden/werk/logmytime-archiveren/runs
interval: [taken 8d, npm 4d]
proces: Python
---

# Fien

Fien ruimt op wat af is, met twee taken, zonder model, allebei met `scripts/fien_runner.py`: `taken`
elke maandag om 8:00 en `npm` elke dag om 8:05. Het zijn aparte launchd-jobs, dus mislukt de ene,
dan draait de andere toch.

- **`taken`:** archiveert de actieve taken in LogMyTime waarvan het issue in YouTrack minstens 7
  dagen is opgelost en waarop in die 7 dagen geen tijd meer is gelogd, met
  `scripts/logmytime_taken_archiveren.py`. Plan en beslissingen: [[logmytime-taken-archiveren-plan]].
- **`npm`:** verwijdert de oude develop-versies van onze npm-packages uit `npm-repo` op
  sonatype.pompkracht.nl (per package blijven de releases, de 3 nieuwste develop-versies en de
  versies met een dist-tag), met `scripts/nexus_opruimen.py`, hooguit 50 per run (`--max-npm`). Plan
  en beslissingen: [[npm-develop-versies-opruimen-plan]].

- Run-notities: `gebieden/werk/logmytime-archiveren/runs/` (de map heet nog naar de eerste taak):
  `fien-<jaar>-w<week>.md` per week (onderwerp `taken`, wat gearchiveerd is, wat wacht en wat nog
  open is) en `fien-<jjjj-mm-dd>-npm.md` per dag (onderwerp `npm`, wat verwijderd is en waar
  `latest` naartoe verschoof). Een tweede run in dezelfde week of op dezelfde dag overschrijft de
  notitie.
- Aandachtspunten bij `taken`: alleen taken die door `--max 100` of een fout bleven liggen, en taken
  met een issue-ID vooraan dat YouTrack niet kent. Gearchiveerde taken zijn verwacht gedrag en taken
  zonder issue-ID (zoals Reistijd) geen probleem: die staan alleen in de tekst.
- Aandachtspunten bij `npm`: versies die door `--max-npm` of een fout bleven liggen, en packages die
  zijn overgeslagen omdat een publicatietijd ontbreekt. Een verschoven `latest` is verwacht
  (nexus-public #437) en staat alleen in de tekst. Verandert een andere dist-tag, dan stopt de taak
  als `failed`. Een run zonder
  aandachtspunten wacht niet op mij. Heb ik ze bekeken, dan zet ik `status: resolved`; de run van de
  week erna vervangt hem ook.
- Een vergissing terugzetten: in LogMyTime de taak weer actief maken. Een heropend issue zet ik ook
  zelf terug, Fien doet daar niets mee. Een verwijderde npm-versie komt niet terug; de CI publiceert
  bij de volgende develop-build een nieuwe.
- `interval: [taken 8d, npm 4d]`: per onderwerp de langste tijd tussen twee runs. Is `taken` langer
  dan acht dagen of `npm` langer dan vier dagen niet begonnen, dan staat Fien met dat onderwerp
  onder `Stil`. Vier dagen voor de dagelijkse npm-taak overbrugt een weekend met de laptop uit.
- `proces: Python`: de runner draait als `/usr/bin/python3`, en dat heet `Python` in `ps`.
- Schedule: `scripts/fien/nl.crimsoncricket.fien.plist` (`taken`, log `~/.fien/logs/runner.log`) en
  `scripts/fien/nl.crimsoncricket.fien-npm.plist` (`npm`, log `~/.fien/logs/npm.log`), gekopieerd
  naar `~/Library/LaunchAgents/`. Na slaapstand haalt launchd gemiste runs in; dan kunnen ze op
  maandag tegelijk starten, wat kan omdat ze elk een eigen notitie schrijven.
- Elke run kost twee LogMyTime-requests plus één per gearchiveerde taak (limiet 500 per 24 uur).
- De npm-taak gebruikt de Nexus-gebruiker `repo-cleanup` uit `.env` (rol `nx-npm-cleanup`).

## Hervatten

Een `failed`-run heeft in `resume` het commando om zijn taak opnieuw te starten:
`launchctl kickstart gui/$(id -u)/nl.crimsoncricket.fien` (`taken`) of
`launchctl kickstart gui/$(id -u)/nl.crimsoncricket.fien-npm` (`npm`). Met de hand kan ook:
`/usr/bin/python3 -I scripts/fien_runner.py --alleen taken` (of `--alleen npm`; zonder `--alleen`
draaien beide). De nieuwe run maakt
een nieuw plan, dus wat al gedaan was, staat er niet meer in. Doe ik niets, dan pakt de volgende run het
op. Alleen de plannen bekijken: `/usr/bin/python3 -I scripts/fien_runner.py --dry-run`.
