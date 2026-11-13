---
description: Aanvullingen op de Dependabot-routine voor profile-presentation-ui (YouTrack-gegevens)
repo: Flow-Cloud-Systems/profile-presentation-ui
autonoom: true
---

# Dependabot-routine: profile-presentation-ui

## Stap 0. YouTrack-issue

- YouTrack-project: `pompkracht-profile-presentation-ui` (key `PPP`).
- Board: `Pompkracht Kanban Board`, sprint `Kanban workflow`.
- Titel parent: `Dependabot upgrades <jaar> w<bereik>`.
- Titel subtask: `Apply Dependabot upgrades <jaar> w<week>`.

## Stap 5. Kwetsbaarheden patchen zonder breaking changes

Afgehandeld, geen aandachtspunt (besloten 2026-11-13, PPP-85):

- `minimatch` <11.0.1 (GHSA-g3hv-75wg-m249) onder `@typescript-eslint/typescript-estree`. Dev-only,
  en de enige fix is een override naar minimatch 11, een major boven wat typescript-estree vraagt.
  Die voeren we niet door: we wachten op een stabiele typescript-eslint die minimatch 11 vraagt
  (in de canary `8.72.3-alpha.8` al zo). Noem de melding alleen in het verslag, zonder
  `RUN_ATTENTION`, zolang dit allemaal geldt:
  - het is nog steeds alleen deze advisory, op hetzelfde pad onder typescript-estree;
  - `npm ls minimatch --omit=dev` vindt het pakket niet;
  - de `latest` van `@typescript-eslint/typescript-estree` vraagt nog een minimatch onder 11.0.1
    (`npm view @typescript-eslint/typescript-estree@latest dependencies.minimatch`).

  Geldt een van deze punten niet meer, volg dan de skill zoals gewoonlijk.
