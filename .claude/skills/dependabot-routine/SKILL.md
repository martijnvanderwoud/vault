---
name: dependabot-routine
description: Voert mijn Dependabot-routine uit in het huidige project - groene Dependabot-PR's squash-mergen, de lokale base branch bijwerken, een schone install draaien en audit-fixes zonder breaking changes proberen. Gebruik deze skill zodra ik vraag om de Dependabot-routine, om Dependabot-PR's af te handelen of weg te werken, of om de wekelijkse dependency-updates te mergen, ook als ik het woord skill of routine niet gebruik. Niet voor vragen over de Dependabot-configuratie of voor het beoordelen van één losse dependency-update.
---

# Dependabot-routine

Werkt in elk project met Dependabot-PR's op GitHub. Draai vanuit de root van het
project, zodat `gh` de repo zelf vindt.

Uitgangspunt: voer alleen uit wat hieronder als regel staat. Elke situatie waarvoor
geen regel is, leg je aan mij voor met wat je ziet, want dat zijn beoordelingen die
ik zelf maak. Commit en push niets zonder dat ik erom vraag.

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
```

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
- Heeft het iets gewijzigd, laat dan de diff zien en vraag wat ik ermee wil. Wijs op
  elke versie die omlaag gaat.
- Blijven er kwetsbaarheden over, kijk dan wat `npm audit` als fix noemt. Fixes die een
  downgrade betekenen voer ik nooit door, dus die laat je staan en noem je alleen in het
  verslag. Vergelijk daarvoor de genoemde versie met `npm ls <package> --depth=0`. Is de
  enige fix geen downgrade maar wel breaking, vraag het mij dan.

## 6. Afronden

Geen openstaande changes in `git status --short` en verder niets te doen: de routine
is klaar. Geef een kort verslag:

- welke PR's gemerged zijn en welke niet, met de reden
- de commit waarop de base branch nu staat
- resultaat van de install en de audit, met de kwetsbaarheden die blijven staan
- als er meer dan één PR gemerged is: dat de checks van latere PR's tegen de oude base
  draaiden, dus zonder de PR's die net daarvoor gemerged zijn
