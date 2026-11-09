---
name: dependabot-routine
description: Voert mijn Dependabot-routine uit in het huidige project - groene Dependabot-PR's squash-mergen, de lokale base branch bijwerken, een schone install draaien, audit-fixes zonder breaking changes via een PR doorvoeren en de build op de base branch controleren. Gebruik deze skill zodra ik vraag om de Dependabot-routine, om Dependabot-PR's af te handelen of weg te werken, of om de wekelijkse dependency-updates te mergen, ook als ik het woord skill of routine niet gebruik. Niet voor vragen over de Dependabot-configuratie of voor het beoordelen van één losse dependency-update.
---

# Dependabot-routine

Werkt in elk project met Dependabot-PR's op GitHub. Draai vanuit de root van het
project, zodat `gh` de repo zelf vindt.

Uitgangspunt: voer alleen uit wat hieronder als regel staat. Elke situatie waarvoor
geen regel is, leg je aan mij voor met wat je ziet, want dat zijn beoordelingen die
ik zelf maak. Commit en push niets zonder dat ik erom vraag, behalve waar een stap
hieronder of in het projectbestand dat voorschrijft.

Branchnamen, commitberichten en de titel en beschrijving van PR's zijn altijd in het
Engels.

## Projectspecifieke aanvullingen

Bepaal voor je begint de naam van de repo:

```bash
gh repo view --json name --jq .name
```

Staat er naast deze `SKILL.md` een bestand `projecten/<repo>.md`, lees dat dan eerst.
Daarin staan extra stappen en afwijkende beslissingen voor dit project, per stap bij
naam genoemd. Bij tegenspraak wint het projectbestand. Is er geen bestand, volg dan
alleen de stappen hieronder.

## 1. Groene PR's squash-mergen

Haal de open Dependabot-PR's op:

```bash
gh pr list --author "app/dependabot" --state open --limit 50 \
  --json number,title,baseRefName,mergeable,statusCheckRollup \
  --jq 'sort_by(.number)[] | "#\(.number) base=\(.baseRefName) mergeable=\(.mergeable) checks=\([.statusCheckRollup[]|select((.conclusion // .state)=="SUCCESS")]|length)/\(.statusCheckRollup|length) \(.title)"'
```

Een PR is groen als er minstens één check is en alle checks geslaagd zijn. Hoeveel
checks dat zijn verschilt per project, dus reken niet op een vast aantal. Een
major-update volgt dezelfde regel: groen is groen.

Merge de groene PR's één voor één, oplopend op nummer. Controleer vlak voor elke merge
de status opnieuw, want de vorige merge kan die veranderen:

```bash
gh pr view <n> --json mergeable,statusCheckRollup \
  --jq '"mergeable=\(.mergeable) checks=\([.statusCheckRollup[]|select((.conclusion // .state)=="SUCCESS")]|length)/\(.statusCheckRollup|length)"'
gh pr merge <n> --squash
```

- `mergeable=UNKNOWN` betekent meestal dat GitHub nog aan het herberekenen is na de
  vorige merge. Sla de PR dan niet over: kijk na een paar seconden opnieuw, en vraag het
  mij pas als het na een paar pogingen nog zo is.
- Direct na een merge kan `gh pr list` de PR nog even als open tonen. Kijk dan per
  PR met `gh pr view <n> --json state`.
- Leg aan mij voor: een PR die niet groen is (ook bij lopende, overgeslagen of neutrale
  checks), `mergeable=CONFLICTING`, en een merge die mislukt. Merge de overige groene
  PR's wel.
- Zijn er helemaal geen open Dependabot-PR's, of hebben de PR's verschillende base
  branches, vraag dan hoe ik verder wil.

## 2. `.sdkmanrc` nakijken

Dit is relevant voor projecten met Java-gebaseerde tooling, zoals codegen. Is er geen
`.sdkmanrc`, ga dan door. Staat hij er wel, laat de inhoud zien en vraag of hij
bijgewerkt moet worden.

## 3. Lokale working copy bijwerken

Haal de squash-merges binnen, zodat de base branch up-to-date is:

```bash
git status --short --branch
git pull --ff-only origin <base-branch>
git fetch --prune
```

De `fetch --prune` ruimt de lokale verwijzingen naar de `dependabot/*`-branches op.

Sta je op een andere branch, is de working copy niet schoon, of lukt een fast-forward
niet, stop dan en vraag het mij.

## 4. Schone install

Bij een npm-project (`package-lock.json` aanwezig):

```bash
npm ci
```

Kijk of er errors of warnings zijn. Leg die aan mij voor voordat je verder gaat. Een
melding over vulnerabilities is geen reden om te stoppen: die is voor stap 5.

Is het geen npm-project, vraag dan wat in dit project de tegenhanger van stap 4 en 5 is.

## 5. Audit fix zonder breaking changes

Alleen als `npm ci` vulnerabilities meldt:

```bash
npm audit fix
git status --short
```

- Gebruik nooit `--force`.
- `npm audit fix` eindigt met exit 1 als er kwetsbaarheden overblijven, ook als het
  commando zelf goed ging. Lees dat dus niet als mislukking.
- Heeft het iets gewijzigd, laat dan de diff zien en ga door naar stap 6. Gaat er een
  versie omlaag, stop dan en leg het mij voor.
- Blijven er kwetsbaarheden over, kijk dan wat `npm audit` als fix noemt. Fixes die een
  downgrade betekenen voer ik nooit door, dus die laat je staan en noem je alleen in het
  verslag. Vergelijk daarvoor de genoemde versie met `npm ls <package> --depth=0`. Is de
  enige fix geen downgrade maar wel breaking, vraag het mij dan.

## 6. Openstaande wijzigingen via een PR

Alleen als `git status --short` na stap 5 wijzigingen toont.

Maak vanaf de base branch een branch, commit alleen de gewijzigde bestanden, push en
maak een PR naar de base branch:

```bash
git switch -c feature/audit-fix-<package>
git add <gewijzigde bestanden>
git commit -m "<korte beschrijving>"
git push -u origin feature/audit-fix-<package>
gh pr create --base <base-branch> --title "<titel>" --body "<beschrijving>"
```

- Bij een base branch `develop` begint de branchnaam met `feature/`. Is er meer dan één
  package gewijzigd, gebruik dan `feature/audit-fix`. Bij een andere base branch: vraag
  het mij.
- Zet in de beschrijving wat er wijzigt, welke kwetsbaarheden blijven staan en waarom.

Wacht tot de checks klaar zijn, controleer de status opnieuw zoals in stap 1 en
squash-merge als de PR groen is:

```bash
gh pr checks <n> --watch --interval 10
gh pr merge <n> --squash
```

Is de PR niet groen, of `mergeable=CONFLICTING`, leg het mij dan voor.

Ruim daarna op:

```bash
git switch <base-branch>
git pull --ff-only origin <base-branch>
git branch -d feature/audit-fix-<package>
git fetch --prune
```

- Houd deze volgorde aan: `git branch -d` kijkt naar de remote branch om te zien of de
  branch gemerged is, en die verwijzing haalt `fetch --prune` weg.
- De waarschuwing `not yet merged to HEAD` is normaal na een squash-merge. Weigert
  `-d` de branch echt te verwijderen, gebruik dan geen `-D` maar leg het mij voor.

## 7. Projectstappen

Staan er in het projectbestand extra stappen, voer die hier uit. Anders ga je door.

## 8. Build op de base branch

De checks van een PR zeggen niets over de samengevoegde stand. Volg daarom, na alle
merges uit de vorige stappen, de push-build op de laatste commit van de base branch:

```bash
git fetch -q origin <base-branch>
gh run list --commit "$(git rev-parse origin/<base-branch>)" --event push \
  --json databaseId,status,conclusion,workflowName \
  --jq '.[] | "\(.databaseId) \(.workflowName) \(.status)/\(.conclusion)"'
gh run watch <id> --exit-status --interval 10
```

- Staat er nog geen run, kijk dan na een paar seconden opnieuw. Komt er na een paar
  pogingen geen, leg het mij voor.
- Loopt de run nog, wacht dan tot hij klaar is. Voor een run die rood wordt of niet
  afloopt is geen regel: leg die aan mij voor.

## 9. Afronden

Geen openstaande changes in `git status --short` en verder niets te doen: de routine
is klaar. Geef een kort verslag:

- welke PR's gemerged zijn en welke niet, met de reden, ook de PR's uit stap 6 en 7
- de commit waarop de base branch nu staat
- resultaat van de install en de audit, met de kwetsbaarheden die blijven staan
- resultaat van de build uit stap 8
- als er meer dan één Dependabot-PR gemerged is: dat de checks van latere PR's tegen de
  oude base draaiden, en dat de build uit stap 8 de samengevoegde stand dekt
