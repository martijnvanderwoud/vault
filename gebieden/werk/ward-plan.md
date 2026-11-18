---
description: Plan voor Ward, de lokale bewaker van system health; eerste check is AVX-512 VBMI op de hosts (PKI-1133)
tags: [ward, monitoring, plan]
---

# Plan: Ward, bewaker van system health

Doel: Ward controleert elke ochtend de hosts van Pompkracht en waarschuwt mij als er iets
verandert. De eerste check is de CPU-check voor Java4Shell: zodra `avx512vbmi` op een host
verschijnt, zijn we kwetsbaar voor CVE-2026-114938 en is een hotfix nodig (zie PKI-1132).
Later komen er meer checks bij, zoals schijfruimte, certificaten, kernelversies en back-ups.

YouTrack: PKI-1133, subtaak van PKI-1132. Vastgelegd op 2026-11-18.

## Zo werken we dit af

Elke stap is één losse sessie. Start in `~/vault` en zeg: "Doe de eerste open stap uit
[[ward-plan]]". Aan het eind van de sessie:

- vink je de stap af in de voortgang hieronder
- zet je onder `Bevindingen` wat afweek van het plan of wat een latere stap verandert
- pas je latere stappen aan als dat nodig is

## Voortgang

- [x] 1. SSH onder launchd
- [x] 2. Runner en CPU-check
- [x] 3. Ward headless
- [x] 4. Schedule met launchd en status vastleggen
- [ ] 5. Aansluiten op het agents-dashboard
- [ ] 6. PKI-1132 bijwerken

## Beslissingen

- **Vanaf mijn laptop, niet in het cluster.** Er is geen monitoring in het cluster, en
  UptimeRobot doet alleen HTTP-checks van buitenaf. Een CronJob ziet de HAProxy-hosts niet en
  heeft geen kanaal om te melden. Via SSH vanaf mijn laptop doen alle 20 hosts mee, zoals bij
  de handmatige check op 2026-11-17.
- **De hosts komen uit `~/.ssh/config`.** Daar staan precies de 20 hosts van `pompkracht-prd`,
  `pompkracht-dev` en `shared-hosting`. De k3s-nodes lopen via `ProxyJump` over de HAProxy-host
  van hun cluster.
- **SSH via de keychain:** `UseKeychain yes` en `AddKeysToAgent yes`. Geen aparte sleutel met
  een forced command op de hosts. Werkt SSH onder launchd niet, dan meldt de check onbereikbare
  hosts, dus een stille fout is uitgesloten.
- **De checks zijn deterministisch, Ward is een agent.** Een gewone dag kost geen model. De
  runner start alleen een sessie met Ward als de status verandert.
- **Drie uitkomsten:** `ok` (alleen een logregel), `warn` (ander CPU-model, host onbereikbaar of
  ontbrekend) en `alarm` (`avx512vbmi` aanwezig). Een ander model zonder VBMI is nog niet
  gevaarlijk, maar wel een vroeg teken dat TransIP iets verandert.
- **Alleen melden bij een verandering.** Een bekend probleem levert niet elke dag een nieuwe mail op.
- **Mail via de zakelijke Gmail-koppeling van claude.ai,** niet via `google-prive`, want dit is
  werk. Daarom geen `--strict-mcp-config` (dat zet de claude.ai-koppelingen uit, zie
  [[dependabot-routine-autonoom-plan]], stap 6). Rechten: een allowlist met
  `--permission-mode dontAsk`, plus een `PreToolUse`-hook die alleen mail naar
  martijn@crimsoncricket.nl doorlaat. Een allowlist bepaalt niet aan wie een tool mailt, en Ward
  leest uitvoer van hosts.
- **Dagelijks om 9:00.** launchd haalt een gemiste run in na slaapstand, maar niet als de laptop
  uit staat. Daarom legt de runner de laatste geslaagde run vast en toont het agents-dashboard
  die ([[agents-dashboard-plan]]).
- **Geen eigen dashboard.** Ward sluit aan op de gedeelde statusvorm en het dashboard uit
  [[agents-dashboard-plan]], zoals dat plan vraagt van elke agent na Debbie.
- **De agent heet Ward,** van *ward* (bewaken, vergelijk *warden*) en omdat het een Nederlandse
  naam is. De naam staat in de sessienaam, in de notities en in de onderwerpregel van de mails.

## Stappen

### 1. SSH onder launchd

Doel: een proces dat door launchd is gestart, komt op alle 20 hosts zonder te vragen.

- Zet `UseKeychain yes` en `AddKeysToAgent yes` onder `Host *` in `~/.ssh/config`, en laad de
  sleutel één keer met `ssh-add --apple-use-keychain`.
- Test met een tijdelijke LaunchAgent die `ssh -o BatchMode=yes -o ConnectTimeout=10 <host> true`
  naar alle hosts doet en het resultaat logt, ook voor de hosts achter `ProxyJump`.
- Test ook na een herstart van de laptop, want dan is de agent leeg en moet de passphrase uit de
  keychain komen.
- Debbie liep vast omdat `SSH_AUTH_SOCK` ontbrak (in `env -i`). Kijk of launchd die variabele
  aan een LaunchAgent meegeeft. Zo niet, dan zet de runner hem zelf, bijvoorbeeld via
  `launchctl getenv SSH_AUTH_SOCK`.

Klaar als: de test-LaunchAgent alle 20 hosts bereikt, ook na een herstart. Ruim de test-agent
daarna op.

### 2. Runner en CPU-check

Doel: `scripts/ward/ward_runner.py` draait de checks en geeft per check en host een uitkomst,
nog zonder agent en zonder schedule.

- Checks als losse modules in `scripts/ward/checks/`, met één interface: een check krijgt de
  hostlijst en geeft per host `ok`, `warn` of `alarm` terug, met details.
- De hostlijst komt uit `~/.ssh/config` (de `Host`-regels zonder wildcard).
- De CPU-check leest `/proc/cpuinfo` met één SSH-commando per host: `model name` en of
  `avx512vbmi` in de flags staat.
- De referentie staat in `data/ward/baseline.json`: de verwachte hosts, het CPU-model
  (`Intel Xeon Processor (Cascadelake)`) en `avx512vbmi: false`. Een host die erbij komt of
  verdwijnt, levert `warn` op. De referentie pas ik bewust aan, nooit automatisch.
- SSH met `BatchMode=yes` en een korte timeout, en hosts parallel om het snel te houden.
- `--dry-run` toont alleen de uitkomsten. Test met een aangepaste referentie dat `warn` en
  `alarm` werken.

Klaar als: een handmatige run de juiste uitkomst geeft voor alle hosts, en een aangepaste
referentie de juiste `warn` of `alarm`.

### 3. Ward headless

Doel: de runner start bij een `warn` of `alarm` een sessie met Ward, die de bevinding nagaat,
een notitie schrijft en mij mailt.

- Volg de opzet van Debbie (`scripts/dependabot_runner.py`, `scripts/dependabot-runner/`):
  `claude -p` met `--settings` (een JSON-string met de allowlist en `claudeMdExcludes`),
  `--setting-sources project,local`, `--permission-mode dontAsk`, `--session-id`,
  `-n ward-<datum>` en `stdin` op `/dev/null`.
- Geen `--strict-mcp-config`, wel een allowlist die alleen `mcp__claude_ai_Gmail__send_message`
  toelaat, plus de SSH-commando's om na te gaan (read-only, zoals `cat /proc/cpuinfo`) en het
  schrijven van de notitie. Kijk of de claude.ai-koppelingen headless laden (`connected` in het
  init-event).
- Een `PreToolUse`-hook op `send_message` die weigert als `to`, `cc` of `bcc` iets anders bevat
  dan martijn@crimsoncricket.nl. Test dat de hook een ander adres echt tegenhoudt.
- De prompt bevat de uitkomsten van de runner als data. Ward schrijft een notitie in `inbox/`
  met de bevinding, wat hij heeft nagegaan en de volgende stap (bij `alarm`: de hotfix uit
  PKI-1132). Hij mailt dezelfde inhoud, met `Ward` in het onderwerp.
- De runner schrijft de status, niet het model. Een mislukte sessie leidt tot een macOS-melding.
- Test met een nagemaakte `warn` en `alarm` via nagemaakte uitkomsten van de runner (een `alarm` komt niet uit een aangepaste referentie, zie Bevindingen).

Klaar als: een nagemaakte `alarm` een notitie en een mail oplevert, en een mail naar een ander
adres wordt geweigerd.

### 4. Schedule met launchd en status vastleggen

Doel: Ward draait elke dag om 9:00 en meldt alleen een verandering.

- LaunchAgent `nl.crimsoncricket.ward` met `StartCalendarInterval` (9:00), naar het voorbeeld van
  `nl.crimsoncricket.dependabot-runner.plist`. Log buiten de vault.
- De status per check en host in een bestand buiten de vault, of in `data/ward/`. De runner start
  Ward alleen als die status verandert, ook bij herstel naar `ok`. Dat laatste komt als korte
  mail zonder agent, of via Ward: bepaal dat in deze stap.
- De tijd van de laatste geslaagde run vastleggen, voor het dashboard.
- Een lock, zodat twee runs niet overlappen.

Klaar als: de LaunchAgent op een gegeven tijdstip draait en een gewone dag niets meer oplevert
dan een logregel en een tijdstempel.

### 5. Aansluiten op het agents-dashboard

Doel: Ward staat op het agents-dashboard uit [[agents-dashboard-plan]], met zijn laatste run en
de status per check.

- Hangt af van stap 1 van [[agents-dashboard-plan]] (statusvorm en gedeelde module). Is die nog
  niet klaar, doe dan eerst die stap, of sla deze stap over en ga door met stap 6.
- De runner schrijft zijn status in de gedeelde statusvorm, via de gedeelde module. Een run zonder
  bevinding hoort er ook in, want juist de tijd van de laatste geslaagde run moet zichtbaar zijn.
- Een laatste run die ouder is dan twee dagen valt op. Kan dat niet met de statusvorm zoals die
  is, leg het dan vast als bevinding in [[agents-dashboard-plan]], niet als eigen oplossing in
  Ward.

Klaar als: Ward met de echte status op het agents-dashboard staat, zonder dat de watcher of het
dashboard voor Ward is aangepast, en een verouderde run opvalt.

### 6. PKI-1132 bijwerken

Doel: in PKI-1132 en PKI-1133 staat dat de check draait en wat er bij een alarm gebeurt.

- Een comment in PKI-1132 en PKI-1133, en in de beschrijving van PKI-1132 het "to do" bij de
  CPU-check vervangen.

Klaar als: beide issues bijgewerkt zijn en PKI-1133 op `Done` kan.

## Bevindingen

- **Stap 4, 2026-11-18 (klaar).** De runner vergelijkt met de status van de laatste geslaagde run in
  `~/.ward/status.json` (`laatste_run` en de uitkomsten per check en host), buiten de vault zodat
  er niet elke dag een bestand in git wijzigt. Een verandering is een andere uitkomst, of bij een
  `warn` of `alarm` een andere reden. Bij onbereikbaar telt de foutmelding van ssh niet, want die
  verschilt van dag tot dag. Een host die er vorige keer niet was, telt als vorige `ok`.
- **Herstel naar `ok` gaat zonder agent:** de runner schrijft zelf een korte notitie in `inbox/`
  ("weer ok") en geeft een macOS-melding. Geen mail: mailen kan alleen via de claude.ai-koppeling,
  dus via een sessie, en daar is herstel de kosten niet waard. Is er tegelijk een host slechter
  geworden, dan start Ward en staat het herstel in zijn prompt bij de veranderingen.
- **Ward krijgt de veranderingen in de prompt** (`[vorige, nu]` per host), naast alle hosts die
  niet `ok` zijn. Notitie en mail gaan over de verandering.
- **Mislukt Ward, dan blijft de oude status staan.** Zo probeert de volgende run het opnieuw, in
  plaats van dat een alarm alleen in een gemiste macOS-melding staat. De status (met
  `laatste_run`) schrijft alleen een geslaagde run; `laatste_run` is dus de laatste geslaagde run
  voor het dashboard (stap 5).
- **Lock** met `flock` op `~/.ward/runner.lock`; een tweede runner stopt meteen met exitcode 0.
  `--dry-run` neemt de lock niet, want Ward draait die zelf binnen de sessie van de runner.
- **Tests:** met `--uitkomsten` of een andere `--referentie` geldt de status alleen met
  `--status PAD`. Zonder vergelijkt de runner met niets en schrijft hij niets, zodat een test de
  echte status nooit raakt. Getest met een testscript dat de checks, de sessie en de meldingen
  vervangt: nieuw alarm, zelfde alarm (niets), andere ssh-fout (niets), andere warn-reden, herstel,
  mislukte sessie (status blijft, volgende run opnieuw), dry-run en een bezette lock.
- **LaunchAgent** `nl.crimsoncricket.ward`: `scripts/ward/nl.crimsoncricket.ward.plist`, gekopieerd
  naar `~/Library/LaunchAgents/` en geladen met `launchctl bootstrap`. Log in
  `~/.ward/logs/runner.log` (een `---`-regel met de tijd per run, de uitkomsten en `veranderd:`).
  Na een wijziging van de plist: `launchctl bootout gui/$(id -u)/nl.crimsoncricket.ward`, opnieuw
  kopiëren en `bootstrap`.
- **Echte run onder launchd** (`launchctl kickstart`, door Martijn, 16:05): 20 keer `ok` voor
  `hosts` en `cpu`, `veranderd: niets`, exitcode 0, `status.json` geschreven, geen sessie of
  notitie. De run duurde ruim een minuut. Het log toont elke dag de hele tabel (ruim 40 regels);
  maak dat korter als het log te groot wordt.

- **Stap 3, 2026-11-18 (klaar).** Bij een `warn` of `alarm` start `ward_runner.py` (zonder
  `--dry-run`) een sessie met Ward: `claude -p` in `~/.ward/` (buiten de vault, dus geen
  projectinstellingen, hooks of auto-commit van de vault), met `--add-dir ~/vault/inbox`. De prompt
  staat in `scripts/ward/headless/prompt.md`, de allowlist in `scripts/ward/headless/settings.json`.
  De runner voegt toe: `Edit` alleen op het pad van de notitie van die run
  (`inbox/ward-<datum>[-n].md`), `claudeMdExcludes` en de hook. Log in `~/.ward/logs/<notitie>.jsonl`.
  De runner keurt de sessie goed als die exitcode 0 heeft, geen fout geeft, de notitie bestaat,
  een `send_message` gelukt is en `WARD_STATUS: done` in het resultaat staat. Anders volgt een
  macOS-melding (`Ward-run mislukt`).
- **Geen vrije SSH voor Ward.** Een allowlist op `ssh host *` laat elk commando op de host toe.
  Ward krijgt `scripts/ward/nagaan.py HOST ONDERWERP`: een vast read-only commando per onderwerp
  (`cpu`, `lscpu`, `uname`, `uptime`, `dmi`), alleen voor hosts uit `~/.ssh/config`. Daarnaast mag
  hij `ward_runner.py --dry-run` draaien.
- **SSH werkt headless.** De sessie (`dontAsk`, geen auto mode) kwam via `nagaan.py` gewoon op de
  hosts. De runner geeft `SSH_AUTH_SOCK` door aan de sessie.
- **De claude.ai-koppelingen laden headless,** maar staan niet in `mcp_servers` van het init-event
  (die lijst was leeg). Ward laadt `send_message` uitgesteld via `ToolSearch`, en de mail kwam aan.
  Een check op `connected` in het init-event werkt hier dus niet; de runner kijkt naar het
  resultaat van `send_message`.
- **De hook** (`scripts/ward/mail_hook.py`, `PreToolUse` op `mcp__claude_ai_Gmail__.*`) laat alleen
  `send_message` door met `martijn@crimsoncricket.nl` in `to`, `cc` en `bcc`. Hij weigert ook een
  `draftId` (een concept gaat met zijn eigen ontvangers de deur uit), een reply in een thread en
  onleesbare invoer. In een echte sessie getest: een mail aan `ward-hooktest@example.com` (met
  mij in cc) werd geweigerd, met de reden in `permission_denials`.
- **Test met `--uitkomsten PAD`**: nagemaakte uitkomsten uit JSON in plaats van de checks. Ward
  krijgt dan in de prompt dat het een test is, en `TEST` komt in het onderwerp. De testrun met
  een nagemaakte `alarm` (prd-k3s-4) en `warn` (dev-k3s-2) kostte $0,22 in 7 beurten. Ward ging
  het na op de echte hosts, zag geen `avx512vbmi`, schreef `inbox/ward-2026-11-18.md` en mailde
  "Ward TEST: CPU-alarm niet bevestigd".
- Gevolg voor stap 4: nu start Ward bij elke `warn` of `alarm`. Het vergelijken met de vorige
  status hoort vóór `ward_starten` in `main()`. Model: `claude-opus-5-5` (`--model` om te wisselen).

- **Stap 2, 2026-11-18 (klaar).** `scripts/ward/ward_runner.py`
  met `scripts/ward/ssh.py` (hostlijst en parallelle SSH) en `scripts/ward/checks/cpu.py`; de
  referentie staat in `data/ward/baseline.json` met de 20 hosts uit `~/.ssh/config`. Het
  vergelijken van de hostlijst met de referentie zit in de runner als check `hosts`, want het
  geldt voor alle checks. Exitcode 0/1/2 voor `ok`/`warn`/`alarm`. Getest met nagemaakte
  SSH-uitvoer: `ok`, ander model (`warn`), onbereikbaar (`warn`), nieuwe en ontbrekende host
  (`warn`), `avx512vbmi` (`alarm`), en `avx512_vbmi2` zonder `avx512vbmi` blijft `ok`. SSH naar de
  hosts kan ik in auto mode niet (zie stap 1), dus de echte run doet Martijn:
  `/usr/bin/python3 -I scripts/ward/ward_runner.py --dry-run`, en met een kopie van de referentie
  met een ander `model` voor `warn`. De echte run van Martijn (18-11) gaf 20 keer `ok` voor `hosts` en
  voor `cpu`, alle hosts Cascadelake. De `warn` met een aangepaste referentie is alleen getest met
  nagemaakte uitvoer, niet op de echte hosts.
- **Een echte `alarm` komt niet uit een aangepaste referentie.** Het alarm hangt aan de flag op de
  host, niet aan de referentie: zet je `avx512vbmi: true`, dan geeft elke host `warn` (verwacht
  aanwezig, is afwezig). Gevolg voor stap 3: een nagemaakte `alarm` kan niet via de referentie.
  Laat Ward daar testen met een nagemaakte uitkomst van de runner (de prompt krijgt de uitkomsten
  als data), bijvoorbeeld een testoptie die de uitkomsten uit een JSON-bestand leest in plaats van
  de checks te draaien.
- **Stap 1, 2026-11-18 (klaar).** In een Claude-sessie in auto mode blokkeert de classifier
  SSH naar de hosts ("Unauthorized Access"). De test draait dus Martijn zelf. Voor stap 3 telt
  dat niet direct (Ward draait met `--permission-mode dontAsk` en een allowlist, niet in auto
  mode), maar test daar of SSH headless wel doorkomt.
- De eerste run van de test-LaunchAgent (15:38) bevestigde dat launchd `SSH_AUTH_SOCK`
  meegeeft en dat de agent bereikbaar is, maar alle 20 hosts weigerden `~/.ssh/id_rsa`
  (`Permission denied (publickey)` op de HAProxy-hosts). De config noemde geen `IdentityFile`;
  de clustersleutels zaten op 17-11 vermoedelijk met de hand in de agent. Daarom staat er nu
  onderaan `~/.ssh/config` per cluster een `IdentityFile` (`Host pompkracht-prd-*` naar
  `~/.ssh/pompkracht-prd`, enzovoort), buiten de blokken van `infra/Justfile` zodat de Justfile
  ze niet overschrijft. Vorige versie: `~/.ssh/config.before-ward-identity`.
- Na `ssh-add --apple-use-keychain` van de drie clustersleutels (in een gewone Terminal; `!` in
  Claude Code kan geen passphrase ontvangen) haalde de test-LaunchAgent om 15:40 alle 20 hosts,
  ook die achter `ProxyJump`. Daarmee is de koppeling sleutel–cluster bevestigd.
- Na een herstart (run 15:47) was de agent leeg (`The agent has no identities`, nieuwe socket)
  en haalde de test toch alle 20 hosts: `AddKeysToAgent` en `UseKeychain` laden de sleutels uit
  de keychain. Gevolg voor stap 2: de runner hoeft `SSH_AUTH_SOCK` niet zelf te zetten en geen
  sleutels te laden. De test-agent en het testscript zijn opgeruimd; het log staat nog in
  `~/Library/Logs/ward-ssh-test.log`.
- `UseKeychain yes` en `AddKeysToAgent yes` staan onder `Host *` onderaan `~/.ssh/config`, buiten
  de blokken van `infra/Justfile`. De vorige versie staat in `~/.ssh/config.before-ward`.
- In een interactieve shell wijst `SSH_AUTH_SOCK` naar de socket van launchd
  (`/var/run/com.apple.launchd.*/Listeners`), en `launchctl getenv SSH_AUTH_SOCK` geeft hem ook.
  Of een LaunchAgent hem meekrijgt, laat de test zien.
- De test-LaunchAgent staat klaar in `~/Library/Application Support/ward-ssh-test/`
  (`ssh_test.sh` en `nl.crimsoncricket.ward-ssh-test.plist`) en logt naar
  `~/Library/Logs/ward-ssh-test.log`: `SSH_AUTH_SOCK`, `ssh-add -l` en per host `OK` of `FAIL`.
