---
description: Extra stappen van de Dependabot-routine voor axon-stomp-event-publishing (GitFlow met release-branch naar master)
repo: Flow-Cloud-Systems/axon-stomp-event-publishing
autonoom: true
---

# Dependabot-routine: axon-stomp-event-publishing

Base branch: `develop`. Releases gaan via een branch `release/<versie>` met een PR naar
`master`. De volgende development-versie gaat via een PR naar `develop`.

## Stap 0. YouTrack-issue

- YouTrack-project: `pomkracht-maven-dependencies` (key `PMD`).
- Board: `Pompkracht Kanban Board`, sprint `Kanban workflow`.
- Parent: geen. De taak wordt direct aangemaakt, zonder parent.
- Titel subtask: `Axon-stomp-event-publishing: apply Dependabot upgrades <jaar> w<week>`.

## Stap 7. Projectstappen

### Release-branch

Bekijk wat er op `develop` staat en nog niet op `master`, zonder de versiebump en de merge
commit van de vorige release:

```bash
git fetch -q origin
git log --oneline --no-merges --invert-grep --grep='^Update for next development version$' origin/master..origin/develop
```

Die twee commits komen na elke release op `develop` en pas met de volgende release op
`master`. Zonder het filter is de lijst dus nooit leeg. Is de lijst leeg, leg het mij dan
voor. Autonoom: verslag, en sla de rest van stap 7 over.

Maak de release-branch aan vanaf `develop`:

```bash
mvn -B gitflow:release-start
```

Door `-B` vraagt de plugin niets en neemt hij als versie de huidige versie zonder
`-SNAPSHOT`. De plugin controleert zelf of de working copy schoon is, of `develop` gelijk
staat met `origin/develop` en of er geen SNAPSHOT-dependencies zijn. Daarna maakt hij
`release/<versie>` aan, checkt die uit en commit `Update versions for release`. Hij pusht
niet. Mislukt het commando, leg het mij dan voor. Autonoom: stop.

Controleer dat de commit alleen de versieregel in `pom.xml` wijzigt:

```bash
git show --stat HEAD
git show HEAD -- pom.xml
```

Wijzigt er meer, leg het mij dan voor. Autonoom: stop.

Push en maak een PR naar `master`, met als titel `Release <versie>` en een lege
beschrijving:

```bash
git push -u origin release/<versie>
gh pr create --base master --head release/<versie> --title "Release <versie>" --body ""
```

### Volgende development-versie

Doe dit terwijl de checks van de release-PR lopen. De branch begint op de release-branch,
niet op `develop`. Dat is hetzelfde als een branch vanaf `develop` waarin je de
release-branch fast-forward merget, maar dan zonder extra stap. Controleer eerst dat
`develop` sinds de release-start niet verder is gegaan (exit 0):

```bash
git merge-base --is-ancestor origin/develop release/<versie>
```

Exit 1: leg het mij voor. Autonoom: stop. Anders, vanaf `release/<versie>`:

```bash
git switch -c feature/next-version
```

Hoog in `pom.xml` de projectversie op naar de volgende minor met `-SNAPSHOT`, bijvoorbeeld
`5.7.0` naar `5.8.0-SNAPSHOT`. Het bestand springt in met tabs. Controleer met `git diff`
dat alleen die ene versieregel wijzigt. Wijzigt er meer, leg het mij dan voor. Autonoom:
stop.

Commit, push en maak een PR naar `develop`:

```bash
git add pom.xml
git commit -m "Update for next development version"
git push -u origin feature/next-version
gh pr create --base develop --head feature/next-version --title "Update for next development version" --body ""
```

### Mergen

Wacht tot beide PR's groen zijn en controleer de status opnieuw zoals in stap 1. Merge
eerst de release-PR, daarna de versiebump. Beide krijgen een merge commit, zonder squash,
met alleen de titel als bericht:

```bash
gh pr merge <release-pr> --merge --subject "Release <versie>" --body ""
gh pr merge <versiebump-pr> --merge --subject "Update for next development version" --body ""
```

GitHub verwijdert de remote branches na de merge zelf (repo-instelling).

### Opruimen

```bash
git switch develop
git pull --ff-only origin develop
git branch -d feature/next-version release/<versie>
git fetch --prune
git fetch origin master:master
```

- Houd deze volgorde aan, zoals in stap 6: `git branch -d` heeft de verwijzingen naar de
  remote branches nodig, en die haalt `fetch --prune` weg. Weigert `-d` een branch te
  verwijderen, gebruik dan geen `-D` maar leg het mij voor. Autonoom: verslag.
- De laatste regel werkt de lokale `master` bij zonder die uit te checken.

## Stap 8. Build op de base branch

Volg de build op `develop` (workflow `Push snapshot to Sonatype Nexus`) en ook die op
`master` (workflow `Master build`). Beide draaien `mvn deploy`. Voor `master` gebruik je
dezelfde commando's als in `SKILL.md`, met `master` in plaats van `<base-branch>`, en
`gh run watch` op elke run.
