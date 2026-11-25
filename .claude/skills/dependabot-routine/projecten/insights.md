---
description: Aanvullingen op de Dependabot-routine voor insights (YouTrack-gegevens)
repo: Flow-Cloud-Systems/insights
autonoom: true
---

# Dependabot-routine: insights

## Stap 0. YouTrack-issue

- YouTrack-project: `pompkracht-insights` (key `PI`).
- Board: `Pompkracht Kanban Board`, sprint `Kanban workflow`.
- Titel parent: `Dependabot upgrades <jaar> w<bereik>`.
- Titel subtask: `Apply Dependabot upgrades <jaar> w<week>`.

## Stap 4. Schone install

Bekende Gradle-deprecation, geen aandachtspunt: `./gradlew clean build` meldt `Deprecated
Gradle features were used in this build, making it incompatible with Gradle 10`. De oorzaak is
`Configuration.setVisible(boolean)` in de plugin `org.openapi.generator`, niet onze eigen code. De
fix staat in upstream-PR [OpenAPITools/openapi-generator#25025](https://github.com/OpenAPITools/openapi-generator/pull/25025)
(milestone 7.28.0). Besloten op 2026-11-25 in PI-208: wachten op die release.

- Draai bij deze melding `./gradlew build --warning-mode all` en kijk welke deprecations er zijn.
  Is `Configuration.setVisible(boolean)` de enige en staat `openapi-generator` in
  `gradle/libs.versions.toml` op 7.27.0 of lager, dan zet je het alleen als één regel onder
  `Install` in het verslag, zonder `RUN_ATTENTION`.
- Zijn er andere Gradle-deprecations, dan zijn die wel een aandachtspunt, zoals altijd.
- Staat `openapi-generator` op 7.28.0 of hoger en komt de warning nog steeds, dan is het een
  aandachtspunt: de fix werkt dan niet zoals verwacht. Is de warning weg, meld dat dan onder
  `Install`, met het voorstel deze sectie te verwijderen.
