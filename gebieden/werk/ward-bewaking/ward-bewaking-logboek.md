---
description: Logboek van het opzetten van Ward, de dagelijkse bewaking van de hosts van Pompkracht, stap voor stap
tags: [pompkracht, ward, monitoring]
cssclasses: [wide-page]
---

# Ward: logboek

Hoe [[ward-bewaking]] stap voor stap tot stand kwam, op 2026-11-18. De beslissingen die eruit
volgden, staan in [[ward-bewaking-beslissingen]].

## Aanleiding

Op 17-11 bleek bij Java4Shell (CVE-2026-114938, PKI-1132) dat we niet kwetsbaar zijn: alle 20 hosts
hebben een virtuele `Intel Xeon Processor (Cascadelake)` zonder `avx512vbmi`. Het besluit om de
upgrade van het base image mee te laten gaan met de volgende reguliere staging-ronde, hangt daaraan.
Verandert TransIP het CPU-model, dan moet ik dat meteen weten. Daarvoor kwam Ward, met het plan
vastgelegd op 18-11 en YouTrack-issue PKI-1133 (subtaak van PKI-1132). Het plan had zes stappen, elk
in een eigen sessie.

## Stap 1: SSH onder launchd

Doel: een proces dat door launchd is gestart, komt op alle 20 hosts zonder te vragen, ook na een
herstart.

- In een Claude-sessie in auto mode blokkeert de classifier SSH naar de hosts ("Unauthorized
  Access"). De test draaide ik dus zelf. Voor Ward zelf telt dat niet: die draait met
  `--permission-mode dontAsk` en een allowlist, niet in auto mode.
- In een interactieve shell wijst `SSH_AUTH_SOCK` naar de socket van launchd
  (`/var/run/com.apple.launchd.*/Listeners`). Debbie liep eerder vast omdat die variabele ontbrak.
- `UseKeychain yes` en `AddKeysToAgent yes` onder `Host *` onderaan `~/.ssh/config`, buiten de
  blokken van `infra/Justfile`. Vorige versie: `~/.ssh/config.before-ward`.
- Een test-LaunchAgent in `~/Library/Application Support/ward-ssh-test/` logde naar
  `~/Library/Logs/ward-ssh-test.log`: `SSH_AUTH_SOCK`, `ssh-add -l` en per host `OK` of `FAIL`.
- De eerste run (15:38) bevestigde dat launchd `SSH_AUTH_SOCK` meegeeft, maar alle 20 hosts
  weigerden `~/.ssh/id_rsa` (`Permission denied (publickey)`). De config noemde geen
  `IdentityFile`; de clustersleutels zaten op 17-11 vermoedelijk met de hand in de agent. Nu staat
  er per cluster een `IdentityFile` (`Host pompkracht-prd-*` naar `~/.ssh/pompkracht-prd`,
  enzovoort). Vorige versie: `~/.ssh/config.before-ward-identity`.
- Na `ssh-add --apple-use-keychain` van de drie clustersleutels (in een gewone Terminal: `!` in
  Claude Code kan geen passphrase ontvangen) haalde de test om 15:40 alle 20 hosts, ook die achter
  `ProxyJump`.
- Na een herstart (15:47) was de agent leeg (`The agent has no identities`, nieuwe socket), en toch
  haalde de test alle 20 hosts: de sleutels kwamen uit de keychain. De runner hoeft dus
  `SSH_AUTH_SOCK` niet zelf te zetten en geen sleutels te laden. Test-agent en testscript zijn
  opgeruimd.

## Stap 2: runner en CPU-check

Doel: `scripts/ward/ward_runner.py` draait de checks en geeft per check en host een uitkomst, nog
zonder agent en zonder schedule.

- `ward_runner.py` met `ssh.py` (hostlijst en parallelle SSH met `BatchMode=yes` en een korte
  timeout) en `checks/cpu.py`. De referentie in `data/ward/baseline.json` met de 20 hosts. Het
  vergelijken van de hostlijst werd de check `hosts` in de runner. Exitcode 0/1/2 voor
  `ok`/`warn`/`alarm`.
- Getest met nagemaakte SSH-uitvoer: `ok`, ander model, onbereikbaar, nieuwe en ontbrekende host,
  `avx512vbmi`, en `avx512_vbmi2` zonder `avx512vbmi` blijft `ok`.
- Mijn echte run met `--dry-run` gaf 20 keer `ok` voor `hosts` en `cpu`, alle hosts Cascadelake.
  De `warn` met een aangepaste referentie is alleen getest met nagemaakte uitvoer.
- Gevonden: een echte `alarm` komt niet uit een aangepaste referentie. Zet je `avx512vbmi: true`,
  dan geeft elke host `warn` (verwacht aanwezig, is afwezig). Ward moest daarom testen met
  nagemaakte uitkomsten van de runner.

## Stap 3: Ward headless

Doel: de runner start bij een `warn` of `alarm` een sessie met Ward, die de bevinding nagaat, een
notitie schrijft en mij mailt.

- `claude -p` in `~/.ward/` (buiten de vault), naar de opzet van Debbie: `--settings` met de
  allowlist, `claudeMdExcludes` en de hook, `--setting-sources project,local`,
  `--permission-mode dontAsk`, `--session-id`, `-n ward-<datum>`, `stdin` op `/dev/null`. De
  prompt in `scripts/ward/headless/prompt.md`, de allowlist in `scripts/ward/headless/settings.json`.
  `Edit` alleen op het pad van de notitie van die run. Model `claude-opus-5-5` (`--model`).
- De notitie kwam toen in `inbox/` (`--add-dir ~/vault/inbox`). In de opruimronde verhuisde dat
  naar `meldingen/`, zie onder.
- De runner keurt de sessie goed bij exitcode 0, geen fout, een bestaande notitie, een gelukte
  `send_message` en `WARD_STATUS: done`. Anders volgde een macOS-melding (`Ward-run mislukt`).
- Geen vrije SSH: `nagaan.py HOST ONDERWERP` met een vast read-only commando per onderwerp (`cpu`,
  `lscpu`, `uname`, `uptime`, `dmi`). Daarnaast mag Ward `ward_runner.py --dry-run` draaien.
- SSH werkt headless: de sessie (`dontAsk`) kwam via `nagaan.py` op de hosts. De runner geeft
  `SSH_AUTH_SOCK` door.
- De claude.ai-koppelingen laden headless, maar staan niet in `mcp_servers` van het init-event (de
  lijst was leeg). Ward laadt `send_message` uitgesteld via `ToolSearch`. Een check op `connected`
  werkt dus niet; de runner kijkt naar het resultaat van `send_message`.
- De hook (`mail_hook.py`, `PreToolUse` op `mcp__claude_ai_Gmail__.*`) laat alleen `send_message`
  door met mij in `to`, `cc` en `bcc`, en weigert een `draftId`, een reply en onleesbare invoer.
  Getest in een echte sessie: een mail aan `ward-hooktest@example.com` (met mij in cc) werd
  geweigerd.
- `--uitkomsten PAD` voor nagemaakte uitkomsten; Ward hoort dan dat het een test is, en `TEST` komt
  in het onderwerp. De testrun met een nagemaakte `alarm` (prd-k3s-4) en `warn` (dev-k3s-2) kostte
  $0,22 in 7 beurten. Ward ging het na op de echte hosts, zag geen `avx512vbmi`, schreef een notitie
  en mailde "Ward TEST: CPU-alarm niet bevestigd".

## Stap 4: schedule met launchd en status vastleggen

Doel: Ward draait elke dag om 9:00 en meldt alleen een verandering.

- De runner vergelijkt met `~/.ward/status.json` (`laatste_run` en de uitkomsten per check en host).
  Een verandering is een andere uitkomst, of bij `warn` of `alarm` een andere reden, zonder de
  foutmelding van ssh.
- Herstel naar `ok` zonder agent: een korte notitie en een macOS-melding, geen mail.
- Ward krijgt de veranderingen in de prompt. Mislukt Ward, dan blijft de oude status staan.
- Lock met `flock` op `~/.ward/runner.lock`; een tweede runner stopt met exitcode 0. `--dry-run`
  neemt de lock niet, want Ward draait die zelf binnen de sessie van de runner.
- Tests: met `--uitkomsten` of een andere `--referentie` geldt de status alleen met `--status PAD`.
  Getest met een testscript dat de checks, de sessie en de meldingen vervangt: nieuw alarm, zelfde
  alarm, andere ssh-fout, andere warn-reden, herstel, mislukte sessie, dry-run en een bezette lock.
- LaunchAgent `nl.crimsoncricket.ward` (`scripts/ward/nl.crimsoncricket.ward.plist`), gekopieerd
  naar `~/Library/LaunchAgents/` en geladen met `launchctl bootstrap`. Log in
  `~/.ward/logs/runner.log`.
- Echte run onder launchd (`launchctl kickstart`, 16:05): 20 keer `ok` voor `hosts` en `cpu`,
  `veranderd: niets`, exitcode 0, `status.json` geschreven, geen sessie. De run duurde ruim een
  minuut.

## Stap 5: aansluiten op het agents-dashboard

Doel: Ward staat op het agents-dashboard met zijn laatste run en de status per check, zonder dat
watcher of dashboard voor Ward veranderen.

- Stap 1 van [[agents-dashboard-plan]] was al klaar. Ward sluit aan met de agentnotitie [[ward]]
  (`runs`, `interval: 2d`, `proces: Python`). Watcher en dashboard zijn niet aangepast.
- Eén run-notitie per check (`ward-hosts.md`, `ward-cpu.md`), bij elke run opnieuw geschreven: bij
  de start `running` met het pid van de runner en `resume` (`launchctl kickstart`), aan het eind
  `done` met de hosts die niet `ok` zijn als `aandacht`. De tekst van een punt gebruikt `kern()`,
  dus een andere ssh-fout is geen nieuw punt.
- Gevonden bij het testen: als de aandachtspunten tijdens `running` leeg zijn, legt de watcher dat
  vast en meldt hij dezelfde punten aan het eind elke dag opnieuw. Daarom blijven ze tijdens
  `running` staan.
- `failed` alleen voor de checks waarvoor Ward nodig was, met `reason`, `step: ward` en `resume`.
  De runner meldt dat niet meer zelf (alleen nog bij een test zonder run-notities). Kosten,
  beurten, model en log staan bij elke check die de sessie nodig had; het is één sessie voor alle
  checks, dus tel ze niet op.
- `/usr/bin/python3` heet in `ps` `.../Python.app/Contents/MacOS/Python`, daarom `proces: Python`.
  Crasht de runner, dan zet de watcher de run na 15 s op `failed`.
- Een verouderde run valt op via `interval: 2d` (blok `Stil`). `Stil` kijkt naar de laatste
  `started`, niet naar de laatste geslaagde run, maar een mislukte run staat al onder `Aandacht
  nodig`.
- De run-notities kwamen in `.gitignore`. Op mijn verzoek gingen de notities van Ward en van herstel
  niet langer naar `inbox/`, want geschiedenis vervuilt de inbox.
- Getest met een testscript in een tijdelijke map, met de echte meldlogica van de watcher en het
  echte dashboard: eerste run, ok, nieuw alarm (één melding), zelfde alarm (geen), mislukte sessie
  (`failed`, één melding), daarna gelukt (geen), andere ssh-fout (geen), herstel (melding van de
  runner), dry-run schrijft niets, `Stil` na twee dagen. Tijdens de test kwam een herstelnotitie in
  de echte `inbox/` terecht; die is weggehaald.
- Echte run (kickstart 16:12): 20 keer `ok` voor beide checks, geen sessie, de run-notities gingen
  in 15 s van `running` naar `done`, op het dashboard ✅, en de watcher meldde niets.

## Stap 6: PKI-1132 en PKI-1133 bijwerken

- In de beschrijving van PKI-1132 is punt 4 van het plan ("to do") doorgestreept en vervangen door
  de werkende check; de hotfix-trigger noemt de mail van Ward.
- Comments in PKI-1132 (wat de check doet, wat er bij een alarm gebeurt) en PKI-1133 (samenvatting
  van de zes stappen, en dat de laptop aan moet staan). PKI-1133 staat sinds 18-11 op Done.

## Opruimen

- Het plan (`ward-plan.md`) is opgesplitst in [[ward-bewaking]] (documentatie),
  [[ward-bewaking-beslissingen]] en dit logboek, zoals bij [[release-candidates-staging]]. Alles
  van Ward staat nu in `gebieden/werk/ward-bewaking/`, met `meldingen/` (eerst
  `gebieden/werk/ward-meldingen/`) en `runs/` (eerst `gebieden/werk/ward-runs/`). De beschrijving
  van PKI-1133 is bijgewerkt naar de nieuwe map.
- Een rij per check op het dashboard blijft, ook al lijken de rijen op aparte runs.
- De testmelding van stap 3 is weg. Obsidian gaf er "ongeldige eigenschappen" bij: Ward had de
  `description` zonder quotes geschreven, met `(TEST): ` erin, en de voorbeeldopbouw in de prompt
  had zelf al een `: ` na de uitkomst. Nu vraagt de prompt om quotes (en heeft de opbouw geen `: `
  meer), en schrijft de runner na de sessie de frontmatter opnieuw met `agentruns`, dat altijd
  quotes zet. Getest op een kopie van de testmelding.
