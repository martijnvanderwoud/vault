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
- [ ] 3. **Script in plan-modus.** `scripts/nexus_opruimen.py`: per package wat blijft en wat weg
  gaat, met aantallen. Nog niets verwijderen.
- [ ] 4. **Uitvoeren.** Eerst één package met `--uitvoeren --max 5`, controleren dat `npm view` en de
  dist-tags kloppen, daarna de rest.
- [ ] 5. **Taak voor Fien.** Toevoegen aan de runner van Fien zodra die er is (stap 5 van
  [[logmytime-taken-archiveren-plan]]), met de verwijderde versies in de run-notitie.
- [ ] 6. **Afronden** volgens het onderhoud in [[vault-roadmap]].

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
