---
description: Aanvullingen op de Dependabot-routine voor cata (YouTrack-gegevens, build, scan-uitsluitingen, build op develop)
repo: Flow-Cloud-Systems/cata
autonoom: true
---

# Dependabot-routine: cata

Base branch: `develop`. Een PR heeft 2 checks: `Validate GitFlow Branch Rules` en
`build / build`. De validator komt uit een ruleset van de organisatie en staat niet in de
repo.

## Stap 0. YouTrack-issue

- YouTrack-project: `pompkracht-cata` (key `PCATA`).
- Board: `Pompkracht Kanban Board`, sprint `Kanban workflow`.
- Titel parent: `Dependabot upgrades <jaar> w<bereik>`.
- Titel subtask: `Apply Dependabot upgrades <jaar> w<week>`.

## Stap 4. Schone install

`mvn clean package`, zoals in CI.

## Stap 5. Kwetsbaarheden patchen zonder breaking changes

Sluit bij de scan uit: `--exclude com.crimsoncricket --exclude nl.pompkracht`.

## Stap 8. Build op de base branch

Volg de build op `develop` (workflow `Develop build`).
