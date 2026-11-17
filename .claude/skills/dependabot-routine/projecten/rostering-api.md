---
description: Aanvullingen op de Dependabot-routine voor rostering-api (Gradle-codegen, de graphql-uitzondering en wachten op @apollo/server)
repo: Flow-Cloud-Systems/rostering-api
autonoom: true
---

# Dependabot-routine: rostering-api

Base branch: `develop`. Een PR heeft 3 checks: `Validate GitFlow Branch Rules`,
`codegen / build` en `node-build / build`. `/codegen` is een Gradle-project met wrapper.

## Stap 0. YouTrack-issue

- YouTrack-project: `pompkracht-roepaas` (key `RPAAS`).
- Board: `Pompkracht Kanban Board`, sprint `Kanban workflow`.
- Titel parent: `Rostering API - Dependabot upgrades <jaar> w<bereik>`.
- Titel subtask: `Rostering API - apply Dependabot upgrades <jaar> w<week>`.
- Subsystem op parent en subtask: `rostering API`.

## Stap 3. `.sdkmanrc` bijwerken

Dependabot werkt de wrapper in `/codegen` bij, maar niet `.sdkmanrc`. Neem voor Gradle
daarom de versie over uit `codegen/gradle/wrapper/gradle-wrapper.properties`, ook als dat
een nieuwe major is, in plaats van de nieuwste versie bij SDKMAN. Voor Java geldt de
regel uit de skill.

CI en `npm run codegen` draaien `./gradlew`, dus de wrapper. Zo staat in `.sdkmanrc`
dezelfde Gradle-versie als die CI test.

## Stap 5. Kwetsbaarheden patchen zonder breaking changes

### Wachten op @apollo/server voor @graphql-tools/utils

`@apollo/server` 5.5.2 beperkt `@graphql-tools/utils` tot `>=12.0.0 <12.0.2`, dus de fix
voor GHSA-c4qx-w738-7hr3 (12.0.2+) past niet. Voeg hiervoor geen override toe: de kwetsbare
`mergeIncrementalResult` wordt in dit project niet gebruikt. Controleer bij elke routine of
de nieuwste `@apollo/server` 12.0.2+ toestaat:

```bash
npm view @apollo/server dependencies
```

Is dat zo, werk `@apollo/server` dan bij en leg mij voor om deze sectie te verwijderen.
Autonoom: verslag. Is dat niet zo, noem het alleen in het verslag, zonder `Decision needed`.

## Stap 7. Projectstappen

### Uitzondering voor graphql

Major-updates van `graphql` staan op `ignore` in `.github/dependabot.yml`, omdat
`@apollo/server` graphql 17 nog niet toestaat. Controleer bij elke routine de peer
dependency van de nieuwste `@apollo/server`:

```bash
npm view @apollo/server peerDependencies.graphql
```

Staat die graphql 17 toe, leg mij dan voor om de `ignore`-regel te verwijderen. Autonoom:
verslag.

## Stap 8. Build op de base branch

Volg de build op `develop` (workflow `Develop build`).
