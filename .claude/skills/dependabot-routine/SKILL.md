---
name: dependabot-routine
description: Voert mijn Dependabot-routine uit in het huidige project - een YouTrack-issue aanmaken of hervatten, groene Dependabot- of Scala Steward-PR's squash-mergen, de oorzaak van rode PR's uitzoeken, de lokale base branch bijwerken, `.sdkmanrc` bijwerken, een schone build draaien, kwetsbaarheden zonder breaking changes patchen, alle wijzigingen in één PR samenbrengen, de build op de base branch controleren en verslag leggen in het YouTrack-issue. Gebruik deze skill zodra ik vraag om de Dependabot-routine, om Dependabot- of Scala Steward-PR's af te handelen of weg te werken, of om de wekelijkse dependency-updates te mergen, ook als ik het woord skill of routine niet gebruik. Niet voor vragen over de Dependabot-configuratie of voor het beoordelen van één losse dependency-update.
---

# Dependabot-routine

Werkt in elk project met Dependabot-PR's op GitHub. Het projectbestand kan een andere
PR-bron toevoegen, zoals Scala Steward. Draai vanuit de root van het project, zodat `gh`
de repo zelf vindt.

Uitgangspunt: voer alleen uit wat hieronder als regel staat. Elke situatie waarvoor
geen regel is, leg je aan mij voor met wat je ziet, want dat zijn beoordelingen die
ik zelf maak. Commit en push niets zonder dat ik erom vraag, behalve waar een stap
hieronder of in het projectbestand dat voorschrijft.

## Autonome modus

Start ik de skill met het argument `autonoom` (`/dependabot-routine autonoom`), dan draait
hij zonder dat ik meekijk. Stel dan nooit een vraag. De runner geeft ook het ID van de
sessie mee: `/dependabot-routine autonoom session=<uuid>`. Elk punt waar je mij iets
voorlegt, heeft hieronder een klasse, achter `Autonoom:`:

- **stop:** voer geen verdere stappen uit en wijzig niets meer, ook niet aan de working
  copy. Plaats het pauze-comment uit `Pauzeren` en eindig met de statusregels.
- **verslag:** neem het punt op in het verslag van stap 9, met wat je zag en een voorstel
  als ik iets moet beslissen, en ga door. Zo'n punt is altijd een aandachtspunt: ik moet er
  iets mee.

Een situatie zonder regel is autonoom een stop, tenzij hij maar één PR raakt en de rest van
de routine gewoon door kan. Dan is hij verslag, en laat je die PR staan.

Zonder het argument blijft alles zoals hieronder staat: je legt het mij voor en wacht.

De autonome run mag alleen commando's uit een vaste lijst, en heeft geen eigen scratchpad:

- Gebruik als `<scratchpad>` de map `~/dependabot-runs/.scratch/<repo>`. Die bestaat al.
  Schrijf nergens anders buiten de working copy, ook niet naar `/tmp`.
- Schrijf paden zoals in deze skill, met `~/` en niet uitgeschreven, en `gh api` met
  `{owner}/{repo}` en niet met de naam van de repo. De lijst kent alleen die vorm.
- Draai de commando's uit deze skill zoals ze er staan. Geen lussen, subshells of
  command substitution (`$(...)`): die worden geweigerd. Splits zo'n commando op en neem
  de uitkomst over in het volgende.
- Wordt een commando toch geweigerd, zoek dan een weg met de commando's uit de skill.
  Lukt dat niet, dan is het een stop.

### Pauzeren

Bij een stop plaats je met `add_issue_comment` een pauze-comment in de subtask uit stap 0,
in het Engels en in deze vorm:

```text
Debbie (Dependabot routine) PAUSED at step <n>
Seen: <wat je zag, met links naar PR's en runs>
Decision needed: <welke beslissing>  Proposal: <je voorstel>
State: merged #<n> #<n>, not merged #<n> (<reden>), branch <branch of none>, base <korte commit van de base branch>, uncommitted <bestanden of none>
Report so far: <de verslagpunten tot nu toe, of none>
Resume: cd <pwd> && claude --resume <uuid>
Fallback: cd <pwd> && claude "/dependabot-routine <subtask-id>" --add-dir ~/vault
```

- `<pwd>` is de map waarin je draait, `<uuid>` het `session=` uit het argument. Ontbreekt
  dat, laat de regel `Resume` dan weg.
- Neem links naar PR's over uit `gh pr view <n> --json url --jq .url` en stel ze niet zelf
  samen. De naam van de organisatie wijkt soms af van wat je verwacht.
- `base` is de lokale base branch: `git rev-parse --short <base-branch>`. Die vergelijkt
  `Hervatten` met git.
- Plaats geen correctie-comment en wijzig geen comment. Staat er iets verkeerd in, zet de
  correctie dan in het volgende comment van Debbie (het verslag of een nieuw pauze-comment).
  Elk comment van Debbie begint met `Debbie (Dependabot routine)`.
- `Report so far` maakt het verslag compleet als ik via `Fallback` hervat: die sessie kent de
  verslagpunten van voor de pauze niet.
- Stop je voordat de subtask bestaat, plaats dan geen comment. De reden staat dan alleen in
  de statusregel.

### Statusregels

Eindig in autonome modus, bij een stop en na stap 9, met regels die de runner leest. Eerst
per aandachtspunt een regel, daarna als allerlaatste regel de status:

```text
RUN_ATTENTION: <korte tekst, met PR-nummer als het om één PR gaat>
RUN_STATUS: <done|paused> issue=<subtask-id of none> step=<n> reason="<korte reden>"
```

- Een `RUN_ATTENTION`-regel komt er voor elk punt met `Autonoom: verslag` dat zich voordeed,
  ook bij een stop. Wat de skill "alleen in het verslag" noemt, krijgt geen regel.
- `step` en `reason` alleen bij `paused`. Ook een stop voordat de subtask bestaat is
  `paused`, met `issue=none`.
- Geen open PR's in stap 0 is `RUN_STATUS: done issue=none`.

## Hervatten

Start ik de skill met het ID van een subtask (`/dependabot-routine PCATA-617`), dan hervat je
een gepauzeerde run. Lees eerst het projectbestand, zoals bij `Projectspecifieke aanvullingen`.

1. Lees de comments van de subtask (`get_issue_comments`). De comments van Debbie staan onder
   mijn account en beginnen met `Debbie (Dependabot routine)`. Het laatste daarvan moet een
   pauze-comment zijn. Is het een verslag, of is er geen, dan is er niets te hervatten: meld
   dat en stop.
2. Controleer de `State` tegen GitHub en git: welke PR's nu gemerged of nog open zijn, op
   welke branch je staat, de commit van de base branch en `git status --short`. Wijkt iets
   af, meld dan wat ik intussen veranderd lijk te hebben.
3. Ga verder bij de stap uit het pauze-comment. Doe die stap opnieuw vanaf het begin, maar
   sla over wat volgens de controle al gedaan is: merge geen PR twee keer, maak geen tweede
   branch of PR.
4. Neem `Report so far` op in het verslag van stap 9, samen met de reden van de pauze.

Hervatten is interactief, want ik ben erbij. Wil ik dat je autonoom verdergaat, dan geef ik
beide argumenten: `/dependabot-routine autonoom PCATA-617`. Hervat ik met
`claude --resume`, dan ken je de stand al en ga je bij de stap van de pauze verder, ook
interactief.

Branchnamen, commitberichten, de titel en beschrijving van PR's en alles wat je in YouTrack
zet zijn altijd in het Engels.

## Projectspecifieke aanvullingen

Bepaal voor je begint de naam van de repo:

```bash
gh repo view --json name --jq .name
```

Staat er naast deze `SKILL.md` een bestand `projecten/<repo>.md`, lees dat dan eerst.
Daarin staan extra stappen en afwijkende beslissingen voor dit project, per stap bij
naam genoemd. Bij tegenspraak wint het projectbestand. Is er geen bestand, volg dan
alleen de stappen hieronder.

## 0. YouTrack-issue

Kijk eerst of er open Dependabot-PR's zijn:

```bash
gh pr list --author "app/dependabot" --state open --limit 50 --json number --jq length
```

Is dat 0, stop dan direct: geen issue en geen verdere stappen.

Neem de YouTrack-gegevens uit `Stap 0` van `projecten/<repo>.md`: project, board, sprint,
titels en vaste velden zoals Subsystem. Ontbreken die, vraag ze mij dan en neem niets aan.
Autonoom: stop, nog voordat er een issue is.
Bepaal het jaar en de ISO-week met `date '+%G w%V'`. Deze stap vraagt verder geen akkoord.

### Parent

Staat in het projectbestand `Parent: geen`, sla dit deel dan over: dan maak je alleen de taak
uit `Titel subtask`, zonder parent.

Zoek de parent alleen in het YouTrack-project van deze repo, met `search_issues`:

```text
project: <key> #Unresolved Type: Maintenance has: {Board <board>} summary: "Dependabot upgrades"
```

Tel alleen issues waarvan de titel past op `Titel parent` uit het projectbestand.

- **Eén match:** laat het bereik in de titel eindigen op de huidige week, met
  `update_issue`: `w40-45` wordt `w40-46`, `w46` wordt `w46-47`. Staat de huidige week er
  al in, laat de titel dan staan.
- **Geen match:** maak de parent aan met `create_issue`: Type `Maintenance`, State
  `In Progress`, Assignee `Martijn_van_der_Woud`, de vaste velden, en als bereik alleen de
  huidige week. Zet hem op het board.
- **Meer dan één match, of een ander jaar in de titel:** stop en vraag het mij. Autonoom:
  stop, nog voordat er een issue is.

### Subtask

Zoek onder de parent de subtask van deze week, met de exacte titel uit het projectbestand:
`project: <key> subtask of: <parent-id> summary: "<titel>"`. Zonder parent:
`project: <key> summary: "<titel>"`.

- **Bestaat al:** de nieuwe run hoort in die subtask, ook het verslag van stap 9. Staat hij
  op `Done`, zet hem dan op `In Progress`, en daar blijft hij staan. Bij een andere state dan
  `In Progress` of `Done`: vraag het mij. Autonoom: stop.
- **Bestaat niet:** maak hem aan met `create_issue`, met `parentIssue` als er een parent is:
  Type `Task`, State `In Progress`, Assignee `Martijn_van_der_Woud`, de vaste velden, geen
  beschrijving. Zet hem op het board.

Het ID van de subtask gebruik je in stap 6 en stap 9.

### Op het board zetten

`create_issue` zet een issue niet op het board, ook niet via `customFields`. Dat gaat alleen
met een YouTrack-command via de REST-API. Het script leest het token zelf en toont het nooit:

```bash
/usr/bin/python3 -I ~/vault/scripts/youtrack_command.py <issue-id> "add Board <board> <sprint>"
```

Zet geen accolades om de sprintnaam. Controleer het met `search_issues`:
`has: {Board <board>} issue ID: <issue-id>`. Ontbreekt het token of mislukt de aanroep, leg het
mij dan voor. Autonoom: verslag.

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
  mij pas als het na een paar pogingen nog zo is. Autonoom: verslag.
- Direct na een merge kan `gh pr list` de PR nog even als open tonen. Kijk dan per
  PR met `gh pr view <n> --json state`.
- Toont een PR `0/0` checks, kijk dan eerst naar de runs van de head branch. Rode runs
  zonder jobs staan niet in `statusCheckRollup`. Die vallen onder `Storing in CI`:
  `gh run list --branch <head-branch> --json databaseId,name,status,conclusion`.
- Leg aan mij voor: een PR die niet groen is en niet onder `Storing in CI` of
  `Rode PR's` valt (ook bij lopende, overgeslagen, neutrale, afgebroken of ontbrekende
  checks), `mergeable=CONFLICTING`, en een merge die mislukt. Merge de overige groene
  PR's wel. Autonoom: verslag.
- Hebben de PR's verschillende base branches, vraag dan hoe ik verder wil. Autonoom: stop,
  voordat je iets merget.

### Storing in CI

Een rode run is een storing als de log geen compile-, test- of dependencyfout toont en
een van deze twee geldt:

- De log toont een 5xx van GitHub, een registry of een andere externe dienst.
- De run heeft 0 jobs, en er is dus geen log. Bevestig dat met een incident rond de
  starttijd van de run. Is er geen incident, leg het mij dan voor. Autonoom: verslag.

```bash
gh api repos/{owner}/{repo}/actions/runs/<run-id>/jobs --jq .total_count
curl -fsS https://www.githubstatus.com/api/v2/incidents.json
```

`gh run view` kan een 404 geven bij een workflow uit een ruleset van de organisatie.
Gebruik dan `gh api repos/{owner}/{repo}/actions/runs/<run-id>`.

Start de run opnieuw en wacht op het resultaat, maximaal twee keer per run:

```bash
gh run rerun <run-id> --failed
```

Heeft de run 0 jobs, weigert GitHub met `cannot be retried`, of geeft `gh run rerun` een
404 (workflow uit een ruleset van de organisatie), start dan de hele run opnieuw:

```bash
gh api -X POST repos/{owner}/{repo}/actions/runs/<run-id>/rerun
```

Groen daarna: ga verder zoals bij elke groene PR. Nog steeds rood: behandel de PR als
rode PR en leg hem aan mij voor. Autonoom: verslag. Gebruik geen `@dependabot recreate`: Dependabot reageerde
daar binnen enkele minuten niet op.

### Rode PR's

Een PR met een mislukte check (`FAILURE`) die geen storing is, merge en wijzig je niet.
Zoek de oorzaak op en maak de routine af:

```bash
gh pr view <n> --json statusCheckRollup \
  --jq '.statusCheckRollup[] | select(.conclusion=="FAILURE") | "\(.name) \(.detailsUrl)"'
gh run view --job <job-id> --log-failed
```

Het job-id is het laatste deel van de URL.

Alleen bij npm-projecten: een major-update die een andere dependency nog niet
ondersteunt, handel je zelf af. Dat is het geval als de log een peer-conflict toont
(`ERESOLVE`) en ook de nieuwste versie van die dependency de update niet toestaat:

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
peer-conflict, leg je in het verslag aan mij voor met een voorstel. Autonoom: verslag.

## 2. Lokale working copy bijwerken

Haal de squash-merges binnen, zodat de base branch up-to-date is:

```bash
git status --short --branch
git pull --ff-only origin <base-branch>
git fetch --prune
```

De `fetch --prune` ruimt de lokale verwijzingen naar de branches van de gemerged PR's op.

Sta je op een andere branch, is de working copy niet schoon, of lukt een fast-forward
niet, stop dan en vraag het mij. Autonoom: stop.

## 3. `.sdkmanrc` bijwerken

Dit is relevant voor projecten met Java-gebaseerde tooling, zoals codegen. Is er geen
`.sdkmanrc`, ga dan door. Staat hij er wel, werk dan zonder te vragen elke SDK bij naar
de nieuwste versie binnen dezelfde major. De beschikbare versies haal je bij SDKMAN op:

```bash
curl -fsS "https://api.sdkman.io/2/candidates/<sdk>/darwinarm64/versions/list?installed="
```

- Behoud de vendor-suffix van de huidige versie, bijvoorbeeld `-tem`.
- Pre-releases (`-rc`, `-alpha`, `-beta`, `-M`) tellen niet mee als nieuwste versie.
- Een nieuwere major voer je niet door. Die noem je alleen in het verslag.
- De wijziging gaat mee in de PR van stap 6.

## 4. Schone install

Kijk in de root van het project welk buildbestand er staat:

| Bestand | Commando |
| --- | --- |
| `pom.xml` | `mvn clean package` |
| `build.gradle`, `build.gradle.kts` of `settings.gradle(.kts)` | `./gradlew clean build` |
| `package-lock.json` | `npm ci` |

Staan er meerdere, of staat de buildtool niet in deze tabel, volg dan het projectbestand.
Staat het daar niet in, vraag het mij dan. Autonoom: stop.

Kijk of er errors of warnings zijn. Leg die aan mij voor voordat je verder gaat. Autonoom:
errors zijn een stop, warnings zijn verslag. Een
melding over vulnerabilities is geen reden om te stoppen: die is voor stap 5.
Deprecation-warnings in gegenereerde API-clients negeer je, die hoef je niet te melden.

Alleen bij npm-projecten: voor `npm warn deprecated` volg je `Deprecation-warnings van npm`.

Meldt de build 0 uitgevoerde tests terwijl het project tests heeft, leg dat dan ook aan mij
voor: exit 0 is dan geen geslaagde build. Autonoom: stop.

### Deprecation-warnings van npm

Alleen voor npm-projecten (`package-lock.json`). Bij Maven, Gradle en sbt geldt dit niet.

Zoek per warning de keten op met `npm ls <pakket>`. De ouder is het pakket dat de
verouderde versie vereist, de aanvrager is het pakket dat die ouder vereist.

Voeg zonder te vragen een override toe als dit allemaal geldt:

- Het pakket en de ouder zijn transitief, en `npm ls <pakket> --omit=dev` vindt het pakket
  niet (exit 1 is hier het gewenste resultaat). Runtime-dependencies vallen hierbuiten:
  `overrides` werkt niet door bij afnemers van een gepubliceerde library.
- Een nieuwere stabiele versie van de ouder vereist een versie van het pakket die niet
  deprecated is (`npm view <ouder>@<versie> dependencies`, `npm view <pakket>@<versie> deprecated`).
- De `engines` van die versie van de ouder passen bij `.nvmrc`. Ontbreekt `.nvmrc`, dan is
  dit niet te toetsen: voeg geen override toe en noem dat in het verslag.
- De nieuwste versie van de aanvrager staat die ouder nog niet toe.

Maak de override zo smal mogelijk, genest onder de aanvrager. Bij meerdere aanvragers
krijgt elke aanvrager een eigen entry:

```json
"overrides": { "<aanvrager>": { "<ouder>": "^<versie>" } }
```

Bewaar `package-lock.json` vooraf in de scratchpad, draai `npm install` en daarna `npm ci`,
en controleer:

- De warning is weg en er is geen nieuwe warning bij gekomen.
- Geen versie in de lockfile gaat omlaag.
- Alleen de ouder en het deprecated pakket wijzigen. Verder verdwijnen er alleen pakketten
  (ook de dependencies van het deprecated pakket), er komt geen pakket bij.
- De build slaagt. Gebruik de `build_command` uit `.github/workflows`, anders
  `npm run build`. Bestaat geen van beide, dan telt de schone `npm ci` als build.
- Heeft het project een `test`-script, dan slagen de tests.

Voldoet iets hiervan niet, of is de override niet mogelijk, draai hem dan terug. Noem de
warning met de reden alleen in het verslag en ga door. De override gaat mee in de PR van
stap 6.

## 5. Kwetsbaarheden patchen zonder breaking changes

### JVM-projecten

De scripts staan in `~/vault/.claude/skills/dependabot-routine/scripts/`, naast deze
`SKILL.md`. Draai ze met `/usr/bin/python3 -I`,
want niet elke pyenv-Python heeft SSL. Sla de dependency-lijst op in de scratchpad en sluit
met `--exclude` de eigen groupIds uit en alles wat het projectbestand noemt. Staat de
buildtool hieronder niet, volg dan `Stap 5` van het projectbestand.

Maven:

```bash
rm -f <scratchpad>/deps.txt
mvn -q -o dependency:list -DoutputFile=<scratchpad>/deps.txt -DappendOutput=true -DoutputAbsoluteArtifactFilename=false
/usr/bin/python3 -I ~/vault/.claude/skills/dependabot-routine/scripts/osv_jvm.py <scratchpad>/deps.txt --exclude <groupId-prefix>
```

Gradle:

```bash
./gradlew -q projects | grep -oE "Project '[^']+'"
# elk subproject uit de vorige regel als <project>:dependencies, bijvoorbeeld :model:dependencies
./gradlew -q dependencies <project>:dependencies ... > <scratchpad>/tree.txt
/usr/bin/python3 -I ~/vault/.claude/skills/dependabot-routine/scripts/osv_jvm.py <scratchpad>/tree.txt --exclude <groupId-prefix>
```

Het script toont per bevinding `doel=<versie>`, de laagste versie binnen de huidige major
(bij 0.x dezelfde minor) die alle advisories dekt, met de suffix van de huidige versie
(zoals `-jre`).

- **Doel bekend en hoger dan de huidige versie:** patch, zonder te vragen.
  - Directe dependency: pas de versie of de property aan.
  - Beheerd door een BOM: overschrijf de property, met
    `<!-- Override Spring Boot managed version to fix <artifact> <CVE> -->`.
  - Transitief: voeg een entry toe aan `dependencyManagement`, met
    `<!-- Override transitive dep from <bron> to fix <artifact> <CVE> -->`.
  - Gradle: de tegenhanger via de version catalog of `constraints`, met
    `because("<CVE>")`.
- **`doel=GEEN-BINNEN-MAJOR`:** is er wel een fix in een nieuwere major, vraag het mij dan.
  Autonoom: verslag. Is er geen fix, of alleen een downgrade, noem het dan alleen in het
  verslag.

Controleer na het patchen: de dependency-tree toont de nieuwe versie
(`mvn dependency:tree -Dincludes=<groupId>:<artifactId>`), de build uit stap 4 is groen en
een nieuwe scan vindt de bevinding niet meer. Faalt de build, draai die patch dan terug
en noem hem in het verslag. De patches gaan mee in de PR van stap 6.

Controleer ook of bestaande overrides verouderd zijn. Een override geldt alleen als
weg te halen als de BOM of alle paden in de dependency-boom minstens even hoog zijn:

```bash
# Maven
rm -f <scratchpad>/tree.txt
mvn -q -o dependency:tree -Dverbose -DoutputFile=<scratchpad>/tree.txt -DappendOutput=true
/usr/bin/python3 -I ~/vault/.claude/skills/dependabot-routine/scripts/check_overrides.py pom.xml --tree <scratchpad>/tree.txt

# Gradle, met de boom van de scan hierboven
/usr/bin/python3 -I ~/vault/.claude/skills/dependabot-routine/scripts/check_overrides.py --gradle . --tree <scratchpad>/tree.txt
```

Het script beoordeelt bij Maven elke entry met een eigen versie in `dependencyManagement`.
Blijft de versie zonder override gelijk, dan is dat `OVERBODIG` en gaat hij sowieso weg. Wordt
de versie zonder override hoger, dan beslist de comment: een security-patch is `VEROUDERD` en
gaat weg, een bewuste pin of een entry zonder comment is `blijft staan`.

Verwijder zonder te vragen elke override met `VEROUDERD` of `OVERBODIG`, samen met de
comment erboven. Blijft er onder die comment nog een andere override staan, laat de comment
dan staan. Bij Gradle staat een override op meerdere plekken: haal de versie uit
`libs.versions.toml` weg, en ook de library-entry, de `extra`-regel en de constraint, voor
zover niets anders ze gebruikt. Controleer daarna opnieuw: de build uit stap 4 is groen en
een nieuwe scan vindt geen nieuwe bevindingen. Faalt een van beide, zet die override dan
terug en noem hem in het verslag. De verwijderingen gaan mee in de PR van stap 6.

Laat overrides met `nog nodig`, `blijft staan` of `handmatig controleren` staan en noem
ze niet. Overrides op dependencies van Maven- of Gradle-plugins vallen buiten deze controle.

### npm-projecten

Controleer eerst of geneste overrides verouderd zijn. Overrides die je in stap 4 zelf hebt
toegevoegd sla je over. Vereist de geïnstalleerde aanvrager nu zelf een versie die binnen
de override valt (`npm view <aanvrager>@<versie> dependencies`), haal de override dan
zonder te vragen weg. Bewaar `package-lock.json` vooraf in de scratchpad, haal de
override uit `package.json`, draai `npm install` en daarna `npm ci`, en controleer:

- Het lockfile wijzigt niet, of er verdwijnen alleen pakketten.
- Er is geen nieuwe deprecation-warning bij gekomen.
- De build en de tests slagen, zoals bij `Deprecation-warnings van npm`.

Voldoet iets niet, zet de override dan terug en noem hem in het verslag. Overrides op het
hoogste niveau laat je staan. De verwijderingen gaan mee in de PR van stap 6.

Alleen als `npm ci` vulnerabilities meldt:

```bash
npm audit fix
git status --short
```

- Gebruik nooit `--force`.
- `npm audit fix` eindigt met exit 1 als er kwetsbaarheden overblijven, ook als het
  commando zelf goed ging. Lees dat dus niet als mislukking.
- Heeft het iets gewijzigd, laat dan de diff zien, draai nog één keer `npm ci` en ga door
  naar stap 6. Een nieuwe deprecation-warning handel je af volgens
  `Deprecation-warnings van npm`. Gaat er een versie omlaag, stop dan en leg het mij voor.
  Autonoom: stop.
- Blijven er kwetsbaarheden over, kijk dan wat `npm audit` als fix noemt. Fixes die een
  downgrade betekenen voer ik nooit door, dus die laat je staan en noem je alleen in het
  verslag. Vergelijk daarvoor de genoemde versie met `npm ls <package> --depth=0`. Is de
  enige fix geen downgrade maar wel breaking, vraag het mij dan. Autonoom: verslag.

## 6. Openstaande wijzigingen via één PR

Alleen als er wijzigingen zijn: de `.sdkmanrc` uit stap 3, npm-overrides uit stap 4,
patches, audit-fixes of verwijderde overrides uit stap 5 of een `ignore`-regel uit stap 1.
Breng ze samen in één PR, om het aantal builds te beperken.

Maak vanaf de base branch een branch, commit alleen de gewijzigde bestanden, push en
maak een PR naar de base branch:

```bash
git switch -c feature/<issue-id>-<beschrijving-van-de-inhoud>
git add <gewijzigde bestanden>
git commit -m "<issue-id> <korte beschrijving>"
git push -u origin feature/<issue-id>-<beschrijving-van-de-inhoud>
gh pr create --base <base-branch> --title "<issue-id> <titel>" --body-file <scratchpad>/pr-body.md
```

- `<issue-id>` is het ID van de subtask uit stap 0.
- Schrijf de beschrijving eerst met Write naar `<scratchpad>/pr-body.md`. Backticks in
  `--body` lijken op command substitution en worden in autonome modus geweigerd.
- Bij een base branch `develop` begint de branchnaam met `feature/`. Bij een andere base
  branch: vraag het mij. Autonoom: stop.
- Zet in de beschrijving elke wijziging, en welke kwetsbaarheden blijven staan en waarom.

Wacht tot de checks klaar zijn, controleer de status opnieuw zoals in stap 1 en
squash-merge als de PR groen is:

```bash
gh pr checks <n> --watch --interval 10
gh pr merge <n> --squash
```

Is de PR niet groen, of `mergeable=CONFLICTING`, leg het mij dan voor. Autonoom: stop.

Sluit na de merge elke rode PR waarvoor je een `ignore`-regel hebt toegevoegd, met een
Engelse opmerking die de oorzaak noemt en naar de PR met de `ignore`-regel verwijst:

```bash
gh pr close <rode-pr> --comment "<oorzaak en verwijzing>"
```

Ruim daarna op:

```bash
git switch <base-branch>
git pull --ff-only origin <base-branch>
git branch -d feature/<issue-id>-<beschrijving-van-de-inhoud>
git fetch --prune
```

- Houd deze volgorde aan: `git branch -d` kijkt naar de remote branch om te zien of de
  branch gemerged is, en die verwijzing haalt `fetch --prune` weg.
- De waarschuwing `not yet merged to HEAD` is normaal na een squash-merge. Weigert
  `-d` de branch echt te verwijderen, gebruik dan geen `-D` maar leg het mij voor.
  Autonoom: verslag.

## 7. Projectstappen

Staan er in het projectbestand extra stappen, voer die hier uit. Anders ga je door.

Voor een PR uit de projectstappen gelden de regels van stap 6: is hij niet groen, of
`mergeable=CONFLICTING`, leg het mij dan voor. Autonoom: stop.

## 8. Build op de base branch

De checks van een PR zeggen niets over de samengevoegde stand. Volg daarom, na alle
merges uit de vorige stappen, de push-build op de laatste commit van de base branch:

```bash
git fetch -q origin <base-branch>
git rev-parse origin/<base-branch>
gh run list --commit <commit uit de vorige regel> --event push \
  --json databaseId,status,conclusion,workflowName \
  --jq '.[] | "\(.databaseId) \(.workflowName) \(.status)/\(.conclusion)"'
gh run watch <id> --exit-status --interval 10
```

- Staat er nog geen run, kijk dan na een paar seconden opnieuw. Komt er na een paar
  pogingen geen, leg het mij voor. Autonoom: stop.
- Loopt de run nog, wacht dan tot hij klaar is. Voor een run die rood wordt of niet
  afloopt is geen regel: leg die aan mij voor. Autonoom: stop.

## 9. Afronden

Geen openstaande changes in `git status --short` en verder niets te doen: de routine
is klaar. Plaats zonder te vragen een verslag als comment in de subtask uit stap 0
(`add_issue_comment`), met links naar de gemerged PR's (uit `gh pr view <n> --json url`):

- welke PR's gemerged zijn en welke niet, met de reden, ook de PR's uit stap 6 en 7
- per rode PR de oorzaak en wat ermee is gebeurd, of een voorstel als ik moet beslissen
- per storing in CI: welke run, wat je zag, hoe vaak je herstartte en het resultaat
- elke nieuwe `ignore`-regel, wanneer die weg kan, en een voorstel om dat bij elke routine
  te controleren via `projecten/<repo>.md`
- de commit waarop de base branch nu staat
- resultaat van de install en de audit, met de kwetsbaarheden die blijven staan
- verwijderde overrides, en overrides die terug moesten omdat de build of scan faalde
- toegevoegde npm-overrides, met de aanvrager die moet updaten voordat ze weg kunnen
  (stap 5 haalt ze dan vanzelf weg), en deprecation-warnings die blijven staan, met de
  reden
- resultaat van de build uit stap 8
- als er meer dan één Dependabot-PR gemerged is: dat de checks van latere PR's tegen de
  oude base draaiden, en dat de build uit stap 8 de samengevoegde stand dekt

Geef daarna in de chat een kort verslag met de link naar het issue. Verder doe je niets met
het issue: de state blijft `In Progress` en de uren schrijf ik zelf.

In autonome modus begint het comment met de regel `Debbie (Dependabot routine) report`, en
is het comment het verslag: geen verslag in de chat, alleen de statusregels uit
`Statusregels`.
