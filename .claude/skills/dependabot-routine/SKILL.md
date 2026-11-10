---
name: dependabot-routine
description: Voert mijn Dependabot-routine uit in het huidige project - groene Dependabot-PR's squash-mergen, de oorzaak van rode PR's uitzoeken, de lokale base branch bijwerken, `.sdkmanrc` bijwerken, een schone install draaien, audit-fixes zonder breaking changes doorvoeren, alle wijzigingen in één PR samenbrengen en de build op de base branch controleren. Gebruik deze skill zodra ik vraag om de Dependabot-routine, om Dependabot-PR's af te handelen of weg te werken, of om de wekelijkse dependency-updates te mergen, ook als ik het woord skill of routine niet gebruik. Niet voor vragen over de Dependabot-configuratie of voor het beoordelen van één losse dependency-update.
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
- Leg aan mij voor: een PR die niet groen is en niet onder `Rode PR's` valt (ook bij
  lopende, overgeslagen, neutrale, afgebroken of ontbrekende checks),
  `mergeable=CONFLICTING`, en een merge die mislukt. Merge de overige groene PR's wel.
- Zijn er helemaal geen open Dependabot-PR's, of hebben de PR's verschillende base
  branches, vraag dan hoe ik verder wil.

### Rode PR's

Een PR met een mislukte check (`FAILURE`) merge en wijzig je niet. Zoek de oorzaak op
en maak de routine af:

```bash
gh pr view <n> --json statusCheckRollup \
  --jq '.statusCheckRollup[] | select(.conclusion=="FAILURE") | "\(.name) \(.detailsUrl)"'
gh run view --job <job-id> --log-failed
```

Het job-id is het laatste deel van de URL.

Een major-update die een andere dependency nog niet ondersteunt, handel je zelf af. Dat
is het geval als de log een peer-conflict toont (`ERESOLVE`) en ook de nieuwste versie
van die dependency de update niet toestaat:

```bash
npm view <package> peerDependencies
```

Voeg dan in stap 6 aan de juiste `updates`-regel in `.github/dependabot.yml` deze
`ignore` toe, zodat minor- en patch-updates blijven komen. Heeft die regel al een
`ignore`-blok, vul dat dan aan:

```yaml
    ignore:
      - dependency-name: "<dependency>"
        update-types:
          - "version-update:semver-major"
```

De PR sluit je in stap 6. Elke andere oorzaak, ook een minor- of patch-update met een
peer-conflict, leg je in het verslag aan mij voor met een voorstel.

## 2. Lokale working copy bijwerken

Haal de squash-merges binnen, zodat de base branch up-to-date is:

```bash
git status --short --branch
git pull --ff-only origin <base-branch>
git fetch --prune
```

De `fetch --prune` ruimt de lokale verwijzingen naar de `dependabot/*`-branches op.

Sta je op een andere branch, is de working copy niet schoon, of lukt een fast-forward
niet, stop dan en vraag het mij.

## 3. `.sdkmanrc` bijwerken

Dit is relevant voor projecten met Java-gebaseerde tooling, zoals codegen. Is er geen
`.sdkmanrc`, ga dan door. Staat hij er wel, werk dan zonder te vragen elke SDK bij naar
de nieuwste versie binnen dezelfde major. De beschikbare versies haal je bij SDKMAN op:

```bash
curl -fsS "https://api.sdkman.io/2/candidates/<sdk>/darwinarm64/versions/list?installed="
```

- Behoud de vendor-suffix van de huidige versie, bijvoorbeeld `-tem`.
- Een nieuwere major voer je niet door. Die noem je alleen in het verslag.
- De wijziging gaat mee in de PR van stap 6.

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

## 6. Openstaande wijzigingen via één PR

Alleen als er wijzigingen zijn: de `.sdkmanrc` uit stap 3, audit-fixes uit stap 5 of een
`ignore`-regel uit stap 1. Breng ze samen in één PR, om het aantal builds te beperken.

Maak vanaf de base branch een branch, commit alleen de gewijzigde bestanden, push en
maak een PR naar de base branch:

```bash
git switch -c feature/<beschrijving-van-de-inhoud>
git add <gewijzigde bestanden>
git commit -m "<korte beschrijving>"
git push -u origin feature/<beschrijving-van-de-inhoud>
gh pr create --base <base-branch> --title "<titel>" --body "<beschrijving>"
```

- Bij een base branch `develop` begint de branchnaam met `feature/`. Bij een andere base
  branch: vraag het mij.
- Zet in de beschrijving elke wijziging, en welke kwetsbaarheden blijven staan en waarom.

Wacht tot de checks klaar zijn, controleer de status opnieuw zoals in stap 1 en
squash-merge als de PR groen is:

```bash
gh pr checks <n> --watch --interval 10
gh pr merge <n> --squash
```

Is de PR niet groen, of `mergeable=CONFLICTING`, leg het mij dan voor.

Sluit na de merge elke rode PR waarvoor je een `ignore`-regel hebt toegevoegd, met een
Engelse opmerking die de oorzaak noemt en naar de PR met de `ignore`-regel verwijst:

```bash
gh pr close <rode-pr> --comment "<oorzaak en verwijzing>"
```

Ruim daarna op:

```bash
git switch <base-branch>
git pull --ff-only origin <base-branch>
git branch -d feature/<beschrijving-van-de-inhoud>
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
- per rode PR de oorzaak en wat ermee is gebeurd, of een voorstel als ik moet beslissen
- elke nieuwe `ignore`-regel, wanneer die weg kan, en een voorstel om dat bij elke routine
  te controleren via `projecten/<repo>.md`
- de commit waarop de base branch nu staat
- resultaat van de install en de audit, met de kwetsbaarheden die blijven staan
- resultaat van de build uit stap 8
- als er meer dan één Dependabot-PR gemerged is: dat de checks van latere PR's tegen de
  oude base draaiden, en dat de build uit stap 8 de samengevoegde stand dekt
