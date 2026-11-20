---
description: Plan om oude develop-versies van onze npm-packages in Nexus (sonatype.pompkracht.nl) automatisch op te ruimen, later als taak van agent Fien
tags: [vault, plan, pompkracht, nexus, npm, agents]
---

# Plan: oude npm-develop-versies opruimen in Nexus

Vastgelegd op 20-11-2026.

## Probleem

De frontends publiceren elke develop-build naar `npm-repo` op sonatype.pompkracht.nl als
`X.Y.Z-develop.<commit-hash>`. Daardoor staan er tientallen develop-versies per package. Die ruim
ik met de hand op in de Sonatype-UI, en dat is veel klikwerk.

## Feiten (20-11-2026)

- Packages heten `@pompkracht/<repo>`, registry `https://sonatype.pompkracht.nl/repository/npm-repo`.
- Voorbeelden: portal-employee-ui 76 versies (50 × 2.0.0-develop, 23 × 2.1.0-develop, 3 releases),
  portal-ui-common 36, iam-login-ui 33. Elke package heeft de dist-tags `latest` en `develop`.
- `npm view <pkg> --json` geeft versies, dist-tags en publicatietijden (`time`). Dat werkt met het
  npm-token.
- De REST API (`/service/rest/v1/search`, `DELETE /service/rest/v1/components/{id}`) geeft zonder
  login niets terug. Het npm-token werkt daar niet: er is een Nexus-gebruiker nodig.
- Nexus draait 3.91.0 Community Edition, beheerd vanuit de chart `helm/charts/sonatype` in infra.
  Die staat niet in Argo CD: productie werk je met de hand bij met `helm secrets upgrade`.
- De taak "Cleanup blob store" draait al elke nacht en maakt de ruimte vrij na het verwijderen.

## Beslissingen

- **Regel:** per package blijven alle releases, de **3 nieuwste** `-develop.`-versies (op
  publicatietijd) en de versie waar de dist-tag `develop` naar wijst staan. Alle andere
  `-develop.`-versies gaan weg, ook als de bijbehorende release nog niet uit is.
- **Geen controle op lock files:** de CI van de frontends werkt de lock files automatisch bij zodra
  er een nieuwe develop-versie is gepubliceerd (Martijn, 20-11).
- **Geen cleanup-policy van Nexus:** "Retain last N versions" vraagt Nexus Pro met PostgreSQL
  (3.95.4 of later) en sorteert npm-versies op semver, dus `-develop.<hash>` op de hash in plaats
  van de bouwtijd. Policies op leeftijd in Community Edition ruimen bij een stilliggend project ook
  de laatste develop-builds op.
- **Servicegebruiker via infra, niet met de hand:** rol `nx-npm-cleanup` (browse, read en delete op
  `npm-repo`) en gebruiker `repo-cleanup` in `helm/charts/sonatype/values.yaml`, issue PKI-1142.
  Eén gebruiker voor alle opruimtaken, met een rol per repository: een latere Docker-opruiming krijgt
  een eigen rol op dezelfde gebruiker (daarvoor komt een apart plan).
- **Verschuiven van `latest` accepteren, geen extra rechten (20-11):** Nexus zet `latest` bij het
  verwijderen van een versie op de hoogste versie volgens semver, dus vaak op een develop-build
  (bug nexus-public #437), en laat `latest` via de dist-tag-API niet terugzetten. Dat accepteren we:
  de builds, de RC-skill en Dependabot gebruiken `latest` niet, en elke release zet het weer goed
  (`npm publish --tag latest`). Het script meldt wel per package waar `latest` naartoe verschoof.
  Andere tags hoeven niet hersteld te worden, want het script verwijdert nooit een versie met een
  dist-tag. Het recht `edit` uit PKI-1143 gaat daarom weer weg (PKI-1144). Een upgrade van Nexus
  (de fix zou in 3.92 zitten) kan later als losse Task.
- **Uitvoering:** een script `scripts/nexus_opruimen.py` met een plan-modus, `--uitvoeren` en
  `--max`, zoals `logmytime_taken_archiveren.py`. Later draait agent Fien het als tweede taak
  ([[logmytime-taken-archiveren-plan]]).

## Zo werken we dit af

Start in `~/vault` en zeg: "Doe de eerste open stap uit [[npm-develop-versies-opruimen-plan]]". Aan
het eind van de sessie vink je de stap af, zet je onder `Bevindingen` wat anders liep, en pas je
de latere stappen aan als dat nodig is.

## Voortgang

- [x] 1. **Servicegebruiker in infra (PKI-1142).** Rol `nx-npm-cleanup` en gebruiker `repo-cleanup`
  via #1014 (develop), #1015 (staging) en #1016 (master); `helm secrets upgrade` gedaan door Martijn
  op 20-11. `.env` is bijgewerkt.
- [x] 2. **Toegang testen.** `scripts/nexus.py` leest de gegevens uit `.env`, haalt alle componenten
  van `npm-repo` op en telt per package. Werkt op 20-11, zie `Bevindingen`.
- [x] 3. **Script in plan-modus.** `scripts/nexus_opruimen.py`: per package wat blijft en wat weg
  gaat, met aantallen. Plan gedraaid op 20-11, nog niets verwijderd.
- [x] 4. **Proefrun.** Gedaan op 20-11: 5 versies van portal-worker-ui weg, maar Nexus zette
  `latest` daarbij op `1.2.0-develop.fac2038`, zie `Bevindingen`. Terugzetten met
  `npm dist-tag add` gaf 403 voor Nexus-gebruiker `martijn`; `latest` blijft verkeerd tot stap 6 of
  tot iemand het met een admin-account terugzet.
- [x] 5. **Rechten voor dist-tags in infra.** Bezig sinds 20-11: Task PKI-1143 op het bord, recht
  `edit` toegevoegd en gemerged via infra #1017 (develop), #1018 (staging) en #1019 (master),
  `helm secrets upgrade` door Martijn op 20-11, zie `Bevindingen`. Het recht werkt (`develop` zetten
  lukt), maar `latest` weigert Nexus altijd. PKI-1143 is Done; het recht gaat weer weg in PKI-1144
  via infra #1020 (develop), #1021 (staging) en #1022 (master), gemerged op 20-11. Nog te doen:
  `helm secrets upgrade` door Martijn en controleren dat `repo-cleanup` weer 403 krijgt op
  dist-tags. Hoofdtaak op het bord: PKI-1145 (Maintenance), met PKI-1142 t/m 1144 als subtaken.
  Oorspronkelijke opdracht:
  uitzoeken welk recht Nexus 3.91 vraagt voor `PUT /repository/npm-repo/-/package/<pkg>/dist-tags/<tag>` (verwacht `edit`, anders `add` op
  `npm-repo`) en dat toevoegen aan de rol `nx-npm-cleanup` in `helm/charts/sonatype/values.yaml`. Als
  Task op het bord, net als PKI-1142, met PR's naar develop, staging en master. Martijn doet de
  `helm secrets upgrade` en kijkt of de configuratie-job slaagt.
- [ ] 6. **Script meldt verschoven dist-tags.** `nexus_opruimen.py` legt per package de dist-tags
  vast voordat het iets verwijdert, haalt na het verwijderen de npm-metadata opnieuw op en geeft per
  veranderde tag een regel (`latest: 1.1.0 → 1.2.0-develop.fac2038`). Verandert een andere tag dan
  `latest`, dan stopt het script met een foutmelding: dat hoort niet te gebeuren. Testen met
  `--pakket @pompkracht/portal-worker-ui --uitvoeren --max 2`.
- [ ] 7. **De rest uitvoeren.** Per run hooguit 20 versies, tot het plan leeg is.
- [ ] 8. **Taak voor Fien.** Toevoegen aan de runner van Fien zodra die er is (stap 5 van
  [[logmytime-taken-archiveren-plan]]), met de verwijderde versies en verschoven dist-tags in de
  run-notitie.
- [ ] 9. **Afronden** volgens het onderhoud in [[vault-roadmap]].

## Bevindingen

- **Stap 1 (20-11-2026):** volgens PKI-1101 kan een redeploy van Sonatype ook taken bijwerken. In
  Quartz-cron betekent `0 0 1 * * ?` elke dag om 01:00 (seconden, minuten, uren), niet maandelijks.
  Dat verklaart de dagelijkse run om 03:00 CEST uit dat issue: de chart en de live instantie
  verschillen dus niet. Kijk na de upgrade of de configuratie-job slaagt.
- **Stap 2 (20-11-2026):** `repo-cleanup` ziet in `npm-repo` 7 packages met 218 versies: 29 releases
  en 189 develop-versies, geen andere prereleases. Grootste: portal-employee-ui (73 develop),
  portal-ui-common (33), iam-login-ui (31), portal-enrollment-ui (25). De ontwerp-library heet
  `@pompkracht/pk-react-profile-presentation-design`. `docker-repo` geeft 0 componenten terug, dus de
  rol is beperkt tot npm. Het recht om te verwijderen is nog niet getest; dat gebeurt in stap 4.
- **Stap 3 (20-11-2026):** de publicatietijden en dist-tags komen uit de npm-metadata van Nexus zelf
  (`/repository/npm-repo/<package>`, met de servicegebruiker), niet uit `npm view`; `nexus.py` kreeg
  daarvoor `packument()` en `verwijder()`. Het plan: 169 van de 189 develop-versies weg, 49 versies
  blijven. `--uitvoeren` verwijdert de oudste eerst, standaard hooguit 20 per run; `--pakket` beperkt
  tot één package. Opvallend: bij `@pompkracht/pk-react-profile-presentation-design` wijst `latest`
  naar `2.8.0-develop.af0ee60` in plaats van release `2.7.0`, waarschijnlijk een develop-build die
  zonder `--tag develop` is gepubliceerd. Die versie blijft staan omdat er een dist-tag op zit; de tag
  zelf rechtzetten valt buiten dit plan.
- **Stap 4, proefrun (20-11-2026):** `repo-cleanup` mag verwijderen: de 5 oudste develop-versies van
  portal-worker-ui (1.1.0-develop.af2125a, db812d9, cf288b8, 2eca243, b999555) zijn weg, `npm view`
  en de npm-metadata tonen nog 12 versies, `develop` klopt. Maar `latest` wees daarna naar
  `1.2.0-develop.fac2038`, de hoogste versie op semver, en niet meer naar release `1.1.0` (dat
  laatste is afgeleid: de andere zes packages hebben `latest` op hun release, en `fac2038` stond
  in het plan niet als getagd). Nexus rekent `latest` bij het verwijderen van een versie dus
  opnieuw uit. Waarschijnlijk is de verkeerde `latest` van pk-react-profile-presentation-design zo
  ontstaan, door eerder opruimen met de hand. Gevolg voor het script: dist-tags vóór het verwijderen
  vastleggen en daarna herstellen (`PUT /repository/npm-repo/-/package/<pkg>/dist-tags/<tag>`), en
  daarvoor heeft `repo-cleanup` waarschijnlijk extra rechten nodig (edit of add op `npm-repo`).
  `npm dist-tag add @pompkracht/portal-worker-ui@1.1.0 latest` met het npm-token van Martijn
  (Nexus-gebruiker `martijn`) gaf `403 Forbidden` op
  `PUT /repository/npm-repo/-/package/@pompkracht%2fportal-worker-ui/dist-tags/latest`: ook die
  gebruiker heeft het recht voor dist-tags niet.
- **Stap 5 (20-11-2026):** Nexus beeldt de HTTP-methode van een repository-verzoek af op een
  BREAD-actie in `SecurityFacetSupport.action()` (nexus-public): GET/HEAD read, POST/PATCH add,
  PUT edit, DELETE delete. Een dist-tag zetten (PUT) vraagt dus
  `nx-repository-view-npm-npm-repo-edit`. Het npm-formaat zelf staat niet in de publieke broncode;
  dat het die afbeelding niet overschrijft, is dus niet bevestigd. Bijwerking: `npm publish` is ook
  een PUT, dus `repo-cleanup` kan daarmee waarschijnlijk ook publiceren. Geaccepteerd: de gegevens
  staan alleen in `.env`. Nexus-gebruiker `martijn` heeft waarschijnlijk alleen read en browse,
  zoals de rol `nx-npm-dev` (niet gecontroleerd), wat de 403 uit stap 4 zou verklaren; `npm-ci`
  heeft `*`.
- **Stap 5, na de upgrade (20-11-2026):** `nexus.py` kreeg `zet_dist_tag()`
  (`PUT /repository/npm-repo/-/package/<pkg>/dist-tags/<tag>` met de versie als JSON-string). Als
  `repo-cleanup` lukt `develop` zetten (op de waarde die het al had), dus `edit` is het juiste recht.
  `latest` zetten geeft altijd `400 {"success":false,"error":"Unable to update latest tag"}`, ook naar
  de waarde die het al had: Nexus beheert `latest` zelf en staat wijzigen via de dist-tag-API niet
  toe (niet officieel gedocumenteerd, wel zo beschreven op internet). `latest` van portal-worker-ui
  staat dus nog op `1.2.0-develop.fac2038`. Gevolg: herstellen na verwijderen kan alleen voor andere
  tags dan `latest`; het plan voor stap 6 klopt zo niet meer. Let op: scripts in `scripts/` draaien
  met `/usr/bin/python3`, de pyenv-Python heeft geen SSL.
- **Wie gebruikt `latest`? (20-11-2026):** niemand in de builds.
  - `portal` en `iam` halen de frontends in het profiel `develop` op met de dist-tag `develop` en in
    `pre-release` met vaste versies uit `pom.xml`.
  - De develop-workflows van portal-employee-ui en portal-worker-ui installeren
    `portal-ui-common@develop`.
  - De onderlinge afhankelijkheden zijn ranges (`^4.0.0`, `^2.1.0`, `^2.1.0-develop.c5835e7`) en
    staan vast in de lock files.
  - De master-workflows publiceren met `npm publish --tag latest`: elke release zet `latest` dus
    weer goed.
  - Dependabot leest wel uit Sonatype en werkt `pk-react-profile-presentation-design` bij in
    portal-employee-ui en profile-presentation-ui. Op 19-11 stelde het daar `2.6.0` → `2.7.0`
    voor (portal-employee-ui #276, profile-presentation-ui #210), terwijl `latest` toen
    waarschijnlijk al op `2.8.0-develop.af0ee60` stond (gepubliceerd 17-11): Dependabot slaat de
    develop-builds over. Beide lock files staan op `2.7.0`.
  - Of een admin-account `latest` wel kan zetten, is niet getest: de 400 komt pas na de
    rechtencontrole (`repo-cleanup` kreeg geen 403), dus waarschijnlijk niet.
- **Bekende bug in Nexus (20-11-2026):** het verschuiven van `latest` bij verwijderen is
  [nexus-public #437](https://github.com/sonatype/nexus-public/issues/437) ("Cleanup policy changes
  latest tag on npm repository", ook bij verwijderen met de hand, nog gemeld op 3.89.1). Gesloten
  op 7-5-2026 door een medewerker van Sonatype met "I believe this should be fixed in 3.92", dezelfde
  dag dat 3.92.0 uitkwam. In de release notes van 3.92 t/m 3.98.3 staat het niet: onbevestigd.
  Verwant: #382 (Nexus maakt zelf een `latest` aan als er een asset verdwijnt). Wij draaien 3.91.0
  (`appVersion` in `helm/charts/sonatype/Chart.yaml`). Martijn gebruikte `latest` vroeger zelf bij
  het voorbereiden van een release (portal-ui-common van develop naar de laatste release); de RC-skill
  doet dat nu met een expliciete versie (`staging_frontends.py`, `prepare_release`).
