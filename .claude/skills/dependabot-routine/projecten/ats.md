---
description: Aanvullingen op de Dependabot-routine voor ats (YouTrack-gegevens)
repo: Flow-Cloud-Systems/ats
autonoom: true
---

# Dependabot-routine: ats

## Stap 0. YouTrack-issue

- YouTrack-project: `pompkracht-ats` (key `PA`).
- Board: `Pompkracht Kanban Board`, sprint `Kanban workflow`.
- Titel parent: `Dependabot upgrades <jaar> w<bereik>`.
- Titel subtask: `Apply Dependabot upgrades <jaar> w<week>`.

## Stap 4. Schone install

Bekende openapi-generator-warnings, geen aandachtspunt: de build meldt een aantal keer
`Empty operationId found for path: <methode> <pad>. Renamed to auto-generated operationId: ...`.
Ze komen uit `src/main/swagger/swagger-diis.json`, een spec die uit een ander project komt en
daar operationIds mist. Dat lossen we niet in ats op. Besloten op 2026-11-26 in PA-1109.

- Komen deze warnings alleen uit de generatie van `swagger-diis`, zet ze dan alleen als één regel
  onder `Install` in het verslag, zonder `RUN_ATTENTION`.
- Dezelfde warning uit een andere spec is wel een aandachtspunt, zoals altijd.
