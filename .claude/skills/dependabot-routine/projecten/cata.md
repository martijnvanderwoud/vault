---
description: Aanvullingen op de Dependabot-routine voor cata (Maven, webjars negeren, Maven-versie in de workflows)
---

# Dependabot-routine: cata

Base branch: `develop`. Een PR heeft 2 checks: `Validate GitFlow Branch Rules` en
`build / build`. De validator komt uit een ruleset van de organisatie en staat niet in de
repo.

## Stap 3. `.sdkmanrc` bijwerken

Wijzigt de Maven-versie, werk dan ook `maven_version` bij in `.github/workflows/*.yml`
(`pr.yml`, `develop.yml` en `pre-release.yml`).

## Stap 4. Schone install

`mvn clean package`, zoals in CI.

## Stap 5. Audit fix zonder breaking changes

Sluit bij de scan uit: `--exclude com.crimsoncricket --exclude nl.pompkracht --exclude org.webjars`.

Kwetsbaarheden in webjars negeren we: die code is sterk verouderd. Noem ze ook niet in het
verslag. `.github/dependabot.yml` negeert `org.webjars*:*` om dezelfde reden.

## Stap 8. Build op de base branch

Volg de build op `develop` (workflow `Develop build`).
