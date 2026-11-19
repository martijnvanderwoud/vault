---
description: Beslissingen achter Ward, de dagelijkse bewaking van de hosts van Pompkracht, met de reden erachter
tags: [pompkracht, ward, monitoring]
cssclasses: [wide-page]
---

# Ward: beslissingen

Waarom [[ward-bewaking]] werkt zoals het werkt. Hoe het zo gekomen is, staat in
[[ward-bewaking-logboek]].

## Opzet

- **Vanaf mijn laptop, niet in het cluster.** Er is geen monitoring in het cluster, en
  UptimeRobot doet alleen HTTP-checks van buitenaf. Een CronJob ziet de HAProxy-hosts niet en
  heeft geen kanaal om te melden. Via SSH vanaf mijn laptop doen alle 20 hosts mee, zoals bij de
  handmatige check op 2026-11-17. Nadeel: staat de laptop uit, dan is er geen run (zie `Stil`
  hieronder).
- **De hosts komen uit `~/.ssh/config`** (de `Host`-regels zonder wildcard). Daar staan precies de
  20 hosts van `pompkracht-prd`, `pompkracht-dev` en `shared-hosting`. De k3s-nodes lopen via
  `ProxyJump` over de HAProxy-host van hun cluster.
- **SSH via de keychain:** `UseKeychain yes` en `AddKeysToAgent yes`, en per cluster een
  `IdentityFile`, buiten de blokken van `infra/Justfile`. Geen aparte sleutel met een forced
  command op de hosts. Werkt SSH onder launchd niet, dan meldt de check onbereikbare hosts, dus
  een stille fout is uitgesloten.
- **Dagelijks om 9:00, met launchd.** launchd haalt een gemiste run in na slaapstand, maar niet als
  de laptop uit staat.
- **De agent heet Ward,** van *ward* (bewaken, vergelijk *warden*) en omdat het een Nederlandse
  naam is. De naam staat in de sessienaam, in de meldingen en in de onderwerpregel van de mails.

## Checks en uitkomsten

- **De checks zijn deterministisch, Ward is een agent.** Een gewone dag kost geen model. De runner
  start alleen een sessie met Ward als een host slechter wordt.
- **Checks als losse modules** in `scripts/ward/checks/`, met één interface: hostlijst en referentie
  erin, per host `ok`, `warn` of `alarm` met details eruit. Het vergelijken van de hostlijst zit in
  de runner als check `hosts`, want dat geldt voor alle checks.
- **Drie uitkomsten:** `ok`, `warn` (ander CPU-model, host onbereikbaar, host erbij of weg) en
  `alarm` (`avx512vbmi` aanwezig). Een ander model zonder VBMI is nog niet gevaarlijk, maar wel een
  vroeg teken dat TransIP iets verandert.
- **De referentie pas ik met de hand aan, nooit automatisch** (`data/ward/baseline.json`).
- **Een `alarm` komt van de host, niet van de referentie.** Testen kan daarom alleen met nagemaakte
  uitkomsten (`--uitkomsten`), niet met een aangepaste referentie.

## Alleen melden bij een verandering

- **Vergelijken met de laatste geslaagde run** in `~/.ward/status.json`, buiten de vault, zodat er
  niet elke dag een bestand in git wijzigt. Een verandering is een andere uitkomst, of bij `warn`
  of `alarm` een andere reden. Een bekend probleem levert niet elke dag een nieuwe mail op.
- **Bij onbereikbaar telt de foutmelding van ssh niet,** want die verschilt van dag tot dag. Een
  host die er vorige keer niet was, telt als vorige `ok`.
- **Herstel naar `ok` gaat zonder agent:** een korte melding van de runner en een macOS-melding,
  geen mail. Mailen kan alleen via de claude.ai-koppeling, dus via een sessie, en daar is herstel
  de kosten niet waard. Wordt tegelijk een host slechter, dan start Ward en staat het herstel in
  zijn prompt.
- **Mislukt Ward, dan blijft de oude status staan.** Zo probeert de volgende run het opnieuw, in
  plaats van dat een alarm alleen in een gemiste macOS-melding staat.
- **Een lock** (`flock` op `~/.ward/runner.lock`), zodat twee runs niet overlappen.

## De sessie met Ward

- **Mail via de zakelijke Gmail-koppeling van claude.ai,** niet via `google-prive`, want dit is
  werk. Daarom geen `--strict-mcp-config` (dat zet de claude.ai-koppelingen uit, zie
  [[dependabot-routine-logboek]], stap 6).
- **Rechten:** `--permission-mode dontAsk` met een allowlist, plus een `PreToolUse`-hook die alleen
  `send_message` aan martijn@crimsoncricket.nl doorlaat (ook in cc en bcc), en geen concept of
  reply. Een allowlist bepaalt niet aan wie een tool mailt, en Ward leest uitvoer van hosts.
- **Geen vrije SSH voor Ward.** Een allowlist op `ssh host *` laat elk commando toe. Ward krijgt
  `nagaan.py HOST ONDERWERP`, met een vast read-only commando per onderwerp, alleen voor hosts uit
  `~/.ssh/config`.
- **De runner schrijft de frontmatter van de melding van Ward opnieuw,** met quotes. Ward schrijft
  hem zelf, en één `: ` in een `description` zonder quotes maakt hem ongeldig in Obsidian.
- **De sessie draait in `~/.ward/`, buiten de vault,** zodat de projectinstellingen, hooks en de
  auto-commit van de vault niet meedoen. Ward mag alleen zijn eigen melding schrijven.
- **De runner schrijft de status, niet het model,** en keurt de sessie pas goed als de melding er
  is, een mail gelukt is en Ward `WARD_STATUS: done` meldt.
- **Ward krijgt de veranderingen in de prompt** (`[vorige, nu]` per host), naast alle hosts die niet
  `ok` zijn. Melding en mail gaan over de verandering.

## Dashboard en geschiedenis

- **Geen eigen dashboard.** Ward sluit aan op de gedeelde statusvorm en het agents-dashboard
  ([[agents-dashboard-plan]], [[agent-runs]]), zonder aanpassingen aan watcher of dashboard.
- **Eén run-notitie per check, bij elke run opnieuw geschreven.** Zo staat de status per check op
  het dashboard, en houdt de watcher per notitie bij wat hij gemeld heeft, waardoor een bekende
  bevinding niet elke dag een nieuwe melding geeft. Tijdens `running` blijven de aandachtspunten
  van de vorige run staan, om dezelfde reden. Dat de rijen op aparte runs lijken, neem ik voor lief
  (18-11): met meer checks zie je zo meteen welke check een probleem heeft.
- **Hosts die niet `ok` zijn, zijn aandachtspunten** en blijven op het dashboard tot de host weer
  `ok` is of ik de referentie aanpas. `resolved` zetten helpt niet: de volgende run schrijft de
  notitie opnieuw.
- **`failed` alleen voor de checks waarvoor Ward nodig was.** De melding komt van de watcher, niet
  van de runner, zodat er niet twee komen.
- **Een verouderde run valt op via `interval: 2d`** (het blok `Stil` op het dashboard).
- **De run-notities staan niet in git:** ze wijzigen elke dag, en de geschiedenis staat elders.
- **De geschiedenis staat in `meldingen/`, niet in `inbox/`.** Een melding per bevinding of herstel
  is geschiedenis, en die vervuilt de inbox.
- **Alles van Ward in één map** (`gebieden/werk/ward-bewaking/`): documentatie, beslissingen,
  logboek, meldingen en run-notities, zoals bij [[release-candidates-staging]]. De agentnotitie
  [[ward]] staat in `gebieden/agents/`, omdat de watcher de agents daar vindt.
