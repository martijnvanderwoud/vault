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
- **Dist-tags herstellen, met meer rechten voor `repo-cleanup`:** Nexus zet `latest` bij het
  verwijderen van een versie op de hoogste versie volgens semver, dus vaak op een develop-build.
  Martijn zag dat eerder ook bij opruimen met de hand en houdt het voor een bug in Nexus (20-11).
  Het script legt daarom per package de dist-tags vóór het verwijderen vast en zet ze daarna terug.
  De rol `nx-npm-cleanup` krijgt daarvoor via een infra-PR het recht dat Nexus voor dist-tags vraagt,
  zodat Fien het later zonder het npm-token van Martijn kan.
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
- [ ] 5. **Rechten voor dist-tags in infra.** Uitzoeken welk recht Nexus 3.91 vraagt voor
  `PUT /repository/npm-repo/-/package/<pkg>/dist-tags/<tag>` (verwacht `edit`, anders `add` op
  `npm-repo`) en dat toevoegen aan de rol `nx-npm-cleanup` in `helm/charts/sonatype/values.yaml`. Als
  Task op het bord, net als PKI-1142, met PR's naar develop, staging en master. Martijn doet de
  `helm secrets upgrade` en kijkt of de configuratie-job slaagt.
- [ ] 6. **Script herstelt dist-tags.** `nexus.py` krijgt een functie om een dist-tag te zetten.
  `nexus_opruimen.py` legt per package de dist-tags vast voordat het iets verwijdert, haalt na het
  verwijderen de npm-metadata opnieuw op en zet elke tag terug die veranderd is, met een regel in de
  uitvoer per hersteld tag. Lukt het herstellen niet, dan stopt het script met een foutmelding en het
  commando om het met de hand te doen. Testen met `--pakket @pompkracht/portal-worker-ui --uitvoeren
  --max 2` en controleren dat `latest` en `develop` daarna kloppen.
- [ ] 7. **De rest uitvoeren.** Per run hooguit 20 versies, tot het plan leeg is. Na elke run de
  dist-tags van alle packages controleren.
- [ ] 8. **Taak voor Fien.** Toevoegen aan de runner van Fien zodra die er is (stap 5 van
  [[logmytime-taken-archiveren-plan]]), met de verwijderde versies en herstelde dist-tags in de
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
