---
description: Extra stappen van de Dependabot-routine voor react-notifications (GitFlow met release naar master)
---

# Dependabot-routine: react-notifications

Base branch: `develop`. Releases gaan via een PR van `develop` naar `master`.

## Stap 0. YouTrack-issue

- YouTrack-project: `pompkracht-ui-components` (key `PRC`).
- Board: `Pompkracht Kanban Board`, sprint `Kanban workflow`.
- Parent: geen. De taak wordt direct aangemaakt, zonder parent.
- Titel subtask: `React-notifications: apply Dependabot upgrades <jaar> w<week>`.

## Stap 7. Projectstappen

### Release-PR

Bekijk wat er op `develop` staat en nog niet op `master`:

```bash
git fetch -q origin
git log --oneline origin/master..origin/develop
```

Is die lijst leeg, leg het mij dan voor. Anders maak je een PR van `develop` naar
`master`, met als titel `Release <versie>`, de versie uit `package.json`. Noem in de
beschrijving alle commits uit de lijst.

### Volgende development-versie

Doe dit terwijl de checks van de release-PR lopen.

```bash
git switch -c feature/next-version
```

Hoog de minor-versie in `package.json` op, bijvoorbeeld 4.4.0 naar 4.5.0. Het bestand
springt in met tabs. Draai daarna `npm install`, zodat `package-lock.json` meegaat.
Controleer met `git diff` dat alleen de versieregels wijzigen: één in `package.json`,
twee in `package-lock.json`. Wijzigt er meer, leg het mij dan voor.

Commit, push en maak een PR naar `develop`, met als titel
`Update for next development version`.

### Mergen

Wacht tot beide PR's groen zijn en controleer de status opnieuw zoals in stap 1. De
release-PR heeft meer checks dan een gewone PR, omdat de push-build van `develop`
meetelt.

Merge eerst de release-PR. De head daarvan is `develop` zelf, dus als de versiebump
eerder gemerged wordt, komt die in de release terecht.

```bash
gh pr merge <release-pr> --merge --subject "Release <versie>" --body ""
gh pr merge <versiebump-pr> --squash
```

De release-PR krijgt een merge commit, zonder squash, met alleen de titel als bericht.

### Opruimen

```bash
git switch develop
git pull --ff-only origin develop
git branch -d feature/next-version
git fetch --prune
git fetch origin master:master
```

De laatste regel werkt de lokale `master` bij zonder die uit te checken.

## Stap 8. Build op de base branch

Volg de build op `develop` (workflow `Develop build`) en ook die op `master` (workflow
`Master build`).
