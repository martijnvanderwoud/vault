---
description: De organisatiebrede git-flow-regels van Flow-Cloud-Systems - welke branchnamen een PR naar develop, master, release en hotfix mogen hebben, waar de check vandaan komt en voor welke repo's hij geldt
tags: [werk, pompkracht, github, git-flow]
---

# Git-flow-branchregels bij Pompkracht

Een PR naar `develop` met een branchnaam als `PA-1108-iets` wordt rood op de check
`Validate GitFlow Branch Rules`. Geef branches dus altijd een prefix uit de tabel hieronder.
Ontdekt op 2026-11-20 bij de testbranch voor PKI-1140 (CI-versies uit `.sdkmanrc`).

## Waar de regel vandaan komt

- Drie organisatiebrede rulesets in `Flow-Cloud-Systems` (Settings, Rules): `git-flow-permanent-branches`
  (`develop` en `master`), `git-flow-temporary-branches` (`release/*` en `hotfix/*`) en
  `protected-master`.
- De eerste twee dwingen de required workflow af die in de repo `.github` staat:
  `.github/workflows/git-workflow.yml` (naam `GitFlow Pull Request Validator`). De logica van de
  check staat dus in dat bestand. Een wijziging daar werkt direct door in alle repo's.
- Ophalen kan met `gh api orgs/Flow-Cloud-Systems/rulesets` en per repo met
  `gh api repos/Flow-Cloud-Systems/<repo>/rules/branches/develop`.

## Welke branch mag naar welke

Standaardflow:

| Doel | Bron |
|---|---|
| `master` | `release/*` of `hotfix/*` |
| `develop` | `feature/*`, `release/*`, `hotfix/*`, `dependabot/*` of `update/develop/*` |
| `release/*` | `release-fix/*` of `hotfix/*` |
| `hotfix/*` | `hotfix-fix/*` |

Vereenvoudigde flow (zonder release-branches) voor zeven npm-bibliotheken: `portal-ui-common`,
`portal-worker-ui`, `portal-employee-ui`, `portal-enrollment-ui`, `profile-presentation-design`,
`react-notifications` en `iam-login-ui`:

| Doel | Bron |
|---|---|
| `master` | `develop` of `hotfix/*` |
| `develop` | `feature/*`, `hotfix/*` of `dependabot/*` |

Daar staat `update/develop/*` dus niet bij. Voor `hotfix/*` geldt in beide flows `hotfix-fix/*`.

## Voor welke repo's

- De check en de pull-request-regels gelden voor alle repo's van de organisatie, behalve
  `.github`, `infra`, `axoniq-data-protection`, `mail-template`, `funnel-design` en
  `candidate-matching-exploration`. Gecontroleerd op `ats` en `website`: daar zitten de
  rulesets op `develop`. Het zijn dus ook de JVM-repo's, zoals ats, iam, more, portal en roep.
- `infra` heeft een eigen regelset (alleen delete, non-fast-forward en pull request) en de
  check slaat `infra` en `.github` expliciet over: daar mag elke branchnaam.
- `protected-master` (alleen squash, lineaire historie) geldt voor `.github`,
  `axoniq-data-protection`, `mail-template` en `funnel-design`.
- Beheerders van de organisatie kunnen de regels omzeilen via een PR, maar reken daar niet op.

## Gevolg voor mijn werk

- Branches voor een issue: `feature/PA-1108-korte-omschrijving`. Dat geldt ook voor tijdelijke
  testbranches, zoals bij [[youtrack-bord-pompkracht]] de subtaken van een Maintenance-issue.
- Alleen de `.github`-repo en `infra` laten elke naam toe, maar volg daar dezelfde stijl.
