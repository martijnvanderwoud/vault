---
description: Werknotitie van mijn Dependabot-routine, als basis voor een projectoverstijgende skill
tags: [dependabot, routine, skill-in-wording]
---

# Dependabot-routine

Verkenning, eerste keer uitgevoerd op 2026-11-09 in `rostering-ui`. Doel: hieruit
een skill maken die in alle projecten werkt. Ik leid de routine stap voor stap,
de notitie volgt alleen mijn stappen en beslissingen.

## Generiek

### Stappen

De actuele stappen staan in `.claude/skills/dependabot-routine/SKILL.md`.

### Beslissingen van mij

- Groen betekent: alle checks geslaagd. Dat is het criterium om te squash-mergen.
- Fixes die een downgrade betekenen voer ik nooit door. `npm audit fix --force`
  valt daar in dit geval onder.

### Verrassingen

- Na een merge staat de volgende PR even op `mergeable: UNKNOWN`, omdat GitHub dat
  opnieuw berekent. De skill moet per PR kort wachten en opnieuw kijken, niet
  overslaan.
- De checks van een latere PR zijn gedraaid tegen de oude base, dus zonder de PR
  die net gemerged is.
- Direct na een merge kan `gh pr list --state open` de PR nog even meetellen.
- `npm audit fix` eindigt met exit 1 als er nog kwetsbaarheden overblijven, ook als
  het commando zelf goed is gegaan. De skill mag dat niet als mislukking lezen.
- In zsh splitst `set -- $var` niet op spaties. Gebruik `read -r a b c <<< "$var"`.

## Alleen dit project (rostering-ui)

- Aantal checks per PR: 2 (`Validate GitFlow Branch Rules` en `build / build`).
- Base branch: `develop`. Branches worden na merge automatisch verwijderd.
- Puur npm-project zonder Java-gebaseerde codegen, dus geen `.sdkmanrc`.

## Alleen dit project (react-notifications)

- Repo: `react-notifications` (lokale map `pk-react-notifications`), npm-pakket
  `@pompkracht/react-notifications`.
- Aantal checks per PR: 2, een release-PR naar `master` heeft er 3.
- Base branch: `develop` (default branch van het project; `master` is de main branch).
- Geen `.sdkmanrc`.
- Extra stappen staan in `.claude/skills/dependabot-routine/projecten/react-notifications.md`.

## Alleen dit project (rostering-api)

- Projectgegevens en extra stappen staan in
  `.claude/skills/dependabot-routine/projecten/rostering-api.md`.

## Logboek 2026-11-09 (rostering-ui)

| PR | Inhoud | Checks | Actie |
| --- | --- | --- | --- |
| #159 | minor/patch-groep: @apollo/client, graphql, sass, vite, vitest | 2/2 groen | squash-merge |
| #160 | jsdom 30.1.3 naar 31.0.0 (major) | 2/2 groen | squash-merge |

`develop` fast-forward van 22a7663 naar 4908ae7. `npm ci` (Node 24.21.0, npm
11.19.0): exit 0, 525 packages, geen errors of deprecation-warnings, wel de melding
`12 moderate severity vulnerabilities`.

`npm audit fix`: niets gewijzigd, working copy schoon, nog steeds 12 moderate. Alle
12 komen van `minimatch` 7.0.0 - 11.0.0 (GHSA-g3hv-75wg-m249), via eslint,
typescript-eslint en `@graphql-codegen/cli`. `--force` zou eslint naar 9.39.5
zetten, een downgrade en breaking change. Besluit: niet doorvoeren. Geen openstaande
changes, routine klaar.

## Logboek 2026-11-09 (react-notifications, testrun van de skill)

Testrun van de skill `dependabot-routine`, die na één project is gemaakt. De skill is
tijdens de run niet aangepast. Per afwijking: wat er gebeurde, wat ik besloot, en of
het generiek of projectspecifiek lijkt.

| PR | Inhoud | Checks | Actie |
| --- | --- | --- | --- |
| #46 | minor-and-patch groep, 5 updates | 2/2 groen | squash-merge |

Stappen tot nu toe: repo-naam `react-notifications`, geen `projecten/react-notifications.md`.
Stap 1 één PR gemerged. Stap 2 geen `.sdkmanrc`. Stap 3 `develop` fast-forward van
dac20d5 naar dc74d45. Stap 4 `npm ci`: exit 0, 363 packages, geen errors of warnings,
wel `15 moderate severity vulnerabilities`. Stap 5 `npm audit fix`: exit 1, wijzigt
alleen `package-lock.json` (glob 13.0.6 naar 13.0.7, geen downgrade), 15 moderate
blijven (glob/minimatch). De `--force`-fixes (`@storybook/react-vite@8.5.3`,
`@microsoft/api-extractor@7.52.9`) zijn downgrades (nu 10.6.6 en 7.60.1).

### Afwijkingen

1. **Stap 5: wat te doen met openstaande wijzigingen na `npm audit fix`.**
   - Wat gebeurde: `npm audit fix` wijzigde `package-lock.json` (glob 13.0.6 naar
     13.0.7). De skill zegt alleen "diff laten zien en vragen wat ik ermee wil" en
     verbiedt committen/pushen zonder verzoek.
   - Besluit: extra stap, een pull request maken met de openstaande wijzigingen. Branch
     `feature/audit-fix-glob` vanaf `develop`, commit, push, PR #47 naar `develop`.
   - Indeling: **generiek** (geldt voor elke uitkomst met openstaande wijzigingen),
     maar de branch-conventie (`feature/`-prefix, base `develop`) is
     **projectspecifiek**.
   - Gaten die dit liet zien: de skill noemt geen branchnaam-conventie, geen
     commitbericht-stijl en geen PR-beschrijving. Ik koos zelf `feature/audit-fix-glob`
     (uit geheugen), een korte commit-titel en een PR-body met wijziging en resterende
     kwetsbaarheden.
2. **Na de PR: wachten tot de checks groen zijn.**
   - Wat gebeurde: de skill stopt na het voorleggen van de diff en kent geen wachtstap.
     Met `gh pr checks 47 --watch` gewacht: `Validate GitFlow Branch Rules` (3s) en
     `build / build` (1m12s) beide geslaagd, 2/2.
   - Besluit: extra stap, wachten op groene checks van de eigen PR.
   - Indeling: **generiek** (volgt uit de PR-stap), met het aantal checks en de
     duur als projectspecifieke details.
3. **PR-beschrijving was in het Nederlands.**
   - Wat gebeurde: ik schreef de beschrijving van PR #47 in het Nederlands, omdat de
     skill niets over de taal zegt en de rest van de sessie Nederlands is.
   - Besluit: PR-beschrijvingen zijn altijd Engels, in alle projecten. Beschrijving van
     #47 aangepast naar Engels (commitbericht en PR-titel waren al Engels).
   - Indeling: **generiek**. Hoort in SKILL.md bij de PR-stap (en eventueel ook voor
     commitberichten en branchnamen).
4. **Eigen PR squash-mergen.**
   - Wat gebeurde: status vlak voor de merge opnieuw gecontroleerd (`MERGEABLE`, 2/2),
     daarna `gh pr merge 47 --squash`. PR #47 gemerged als 758b4e8. De remote branch
     `feature/audit-fix-glob` is automatisch verwijderd.
   - Besluit: extra stap, de PR met de audit-fix zelf squash-mergen zodra de checks groen zijn.
   - Indeling: **generiek** (volgt uit de PR-stap), met dezelfde groen-regel als stap 1.
   - Openstaand: de lokale working copy staat nog op `feature/audit-fix-glob`; de skill
     zegt niet of je daarna terug naar de base branch gaat en die opnieuw pullt.
5. **Terug naar de base branch en de lokale PR-branch opruimen.**
   - Wat gebeurde: `git switch develop`, `git pull --ff-only origin develop`
     (758b4e8, alleen de lockfile-wijziging), lokale branch `feature/audit-fix-glob`
     verwijderd. `git branch -d` waarschuwde dat de branch niet in HEAD gemerged was
     (een squash-merge heeft een andere commit), maar verwijderde hem wel omdat
     hij gemerged was met de remote branch.
   - Besluit: extra stap, na de merge van de eigen PR `develop` uitchecken, up-to-date
     brengen met origin en de lokale PR-branch verwijderen.
   - Indeling: **generiek**. Opmerking voor de skill: na een squash-merge werkt
     `git branch -d` niet altijd zonder waarschuwing, dat is normaal.
   - Aanvulling: daarna `git fetch --prune`, zodat verwijderde remote branches ook
     lokaal uit `origin/*` verdwijnen. Verwijderd: `origin/feature/audit-fix-glob` en
     `origin/dependabot/npm_and_yarn/minor-and-patch-4d4d7bcceb` (die van PR #46).
     Ook **generiek**, onderdeel van dezelfde opruimstap.
6. **Release-PR van `develop` naar `master`.**
   - Wat gebeurde: PR #48 aangemaakt, base `master`, head `develop`, titel
     `release 4.4.0` (versie uit `package.json`). Beschrijving in het Engels met de
     commits sinds `origin/master` (#47, #46, #45, #44, #41). De beschrijving mist
     `6d531bc` (merge van #40): die commit stond wel in de lijst en zat niet in de
     vorige `master`, dus dit was een fout van mij. Besluit: zo laten staan.
     Er stond geen andere open PR naar `master`.
   - Besluit: extra stap, alleen voor dit project: na de routine een release-PR maken.
   - Indeling: **projectspecifiek** (GitFlow met `develop` en `master`). Hoort in
     `projecten/react-notifications.md`.
   - Open punt: of de titel `release 4.4.0` of `Release 4.4.0` moet zijn; ik nam de
     schrijfwijze letterlijk over uit je opdracht (kleine letter). Ook is de versie
     niet verhoogd: 4.4.0 is wat er al in `package.json` stond.
7. **Tijdens het wachten op de release-PR: PR voor de volgende development-versie.**
   - Wat gebeurde: PR #48 had inmiddels 3/3 checks groen (`Validate GitFlow Branch
     Rules`, `Develop build` van de push en `Pull request build`). Intussen
     branch `feature/next-version` vanaf `develop`, minor in `package.json` verhoogd
     van 4.4.0 naar 4.5.0, `npm install` zodat `package-lock.json` meeging (twee
     plekken daarin), commit, push, PR #49 naar `develop` met titel
     `Update for next development version` (zelfde titel als #40), beschrijving Engels.
   - Let op: mijn eerste `sed` paste niet, omdat `package.json` met tabs is
     ingesprongen; de versie bleef eerst 4.4.0 en is daarna gecorrigeerd. Geen
     gevolgen voor de uitkomst.
   - Besluit: extra stap, alleen voor dit project (GitFlow met release-PR): direct
     na de release-PR de minor-versie op `develop` ophogen.
   - Indeling: **projectspecifiek**, hoort in `projecten/react-notifications.md`.
     Het is wel een mooi voorbeeld van een stap die de skill met een lokaal
     patroon moet beschrijven (branchnaam `feature/next-version`, minor ophogen).
   - Opmerking: #48 heeft 3 checks in plaats van 2; "groen is groen" uit de skill
     blijft werken, maar het aantal checks is dus niet vast per PR.
8. **Release-PR #48 mergen met merge commit, daarna #49 squash-mergen.**
   - Wat gebeurde: status van beide PR's opnieuw gecontroleerd (#48 3/3, #49 2/2,
     beide `MERGEABLE`). #48 gemerged met `gh pr merge 48 --merge --subject
     "release 4.4.0" --body ""`: commit `117be94` op `master`, bericht precies
     `release 4.4.0` zonder GitHub-standaardtekst. Daarna #49 met `--squash`: commit
     `d04cfb2` op `develop`.
   - Besluit: volgorde eerst release-PR, dan versiebump-PR. Release-PR met merge commit
     (geen squash) en het bericht alleen de titel; versiebump-PR squash.
   - Indeling: **projectspecifiek** (GitFlow): mergemethode en commitbericht van de
     release-PR. De `--merge`-regel hoort dus niet in SKILL.md, wel in
     `projecten/react-notifications.md`.
9. **Opruimen na de laatste PR's.**
   - Wat gebeurde: dezelfde opruimstap als bij afwijking 5: `develop` uitgecheckt en
     gepulld (`d04cfb2`), lokale `feature/next-version` verwijderd (zelfde
     squash-waarschuwing van `git branch -d`), `git fetch --prune` haalde
     `origin/feature/next-version` weg. Working copy schoon.
   - Let op: de lokale `master` is niet bijgewerkt en loopt achter op `origin/master`
     (release-merge `117be94`). Niet gevraagd, dus niet aangeraakt.
   - Indeling: **generiek** (dezelfde opruimstap als afwijking 5).
   - Aanvulling: lokale `master` bijgewerkt zonder uit te checken, met
     `git fetch origin master:master` (fast-forward naar `117be94`). Ik bleef op
     `develop`. **Projectspecifiek** (alleen projecten met een aparte release-branch);
     hoort bij de release-stappen in `projecten/react-notifications.md`.
10. **Build na de merges bewaken (develop en master).**
   - Wat gebeurde: de skill stopt na de merges en kijkt niet naar de CI op de base
     branch zelf. Met `gh run list --branch <branch>` gekeken naar de push-builds op
     de merge-commits: workflow `Develop build` op `d04cfb2` (run 42602058439) en
     `Master build` op `117be94` (run 42602017775), beide `completed/success`.
     Eerder liep ook `Develop build` groen op `758b4e8` (#47).
   - Besluit: extra stap aan het eind, wachten tot de push-builds op de base branch
     groen zijn, zodat het CI-resultaat van de samengevoegde stand bekend is. Bij
     de meeste projecten alleen `develop`, hier ook `master`.
   - Indeling: **generiek** voor de base branch (stap in SKILL.md). Het kijken naar
     `master` is **projectspecifiek**. De workflownamen (`Develop build`,
     `Master build`) ook.
   - Gat voor de skill: wat te doen als zo'n build rood wordt (niet beschreven, dus
     voorleggen), en hoe lang je wacht als hij nog loopt (hier waren ze al klaar).

### Plaatsing na de run

Doorgevoerd op 2026-11-09. Stapnummers zijn die van de bijgewerkte `SKILL.md`.

| Afwijking | Plaats | Waar |
| --- | --- | --- |
| 1. PR met openstaande wijzigingen | `SKILL.md` | stap 5 en 6; ook `feature/`-prefix bij base `develop` |
| 2. Wachten op checks | `SKILL.md` | stap 6 |
| 3. Engelse PR-beschrijving | `SKILL.md` | inleiding; ook titels, commitberichten en branchnamen |
| 4. Eigen PR squash-mergen | `SKILL.md` | stap 6 |
| 5. Opruimen en `fetch --prune` | `SKILL.md` | stap 6; `fetch --prune` ook in stap 3 |
| 6. Release-PR | projectbestand | stap 7; titel met hoofdletter: `Release <versie>`, alleen als `develop` voorloopt op `master` |
| 7. Volgende development-versie | projectbestand | stap 7 |
| 8. Mergemethode en volgorde release | projectbestand | stap 7 |
| 9. Opruimen, lokale `master` bijwerken | projectbestand | stap 7 |
| 10. Build na de merges | `SKILL.md` en projectbestand | stap 8; `master` alleen in het projectbestand |

Overige besluiten: bij stap 5 de diff tonen en doorgaan, alleen stoppen als er een
versie omlaag gaat. Nieuwe stap 7 als vaste plek voor projectstappen. De beschrijving
van #48 blijft zoals die is.

## Logboek 2026-11-10 (rostering-api, testrun van de skill)

Testrun van de skill `dependabot-routine`. De skill is tijdens de run niet aangepast.
Per afwijking: wat er gebeurde, wat ik besloot, en of het generiek of projectspecifiek
lijkt. Afwijkingen 1 tot en met 3 had ik vooraf opgegeven.

| PR | Inhoud | Checks | Actie |
| --- | --- | --- | --- |
| #89 | graphql 16.14.2 naar 17.1.0 (major) | 2/3, `node-build / build` rood | niet gemerged, voorgelegd, later gesloten |
| #90 | gradle-wrapper 9.8.2 naar 9.9.0 in `/codegen` | 3/3 groen | squash-merge (691fd78) |
| #91 | eigen PR: Gradle 9.9.0 in `.sdkmanrc` | 3/3 groen | squash-merge (4297a8e) |
| #92 | eigen PR na de run: `ignore` voor graphql-majors in `.github/dependabot.yml` | 3/3 groen | squash-merge (b2df812) |

Stappen: repo-naam `rostering-api`, geen `projecten/rostering-api.md`. Stap 1 #90
gemerged, #89 niet. Stap 3 `develop` fast-forward van f4887fd naar 691fd78. Stap 4
`npm ci` (Node 24.21.0, npm 11.19.0): exit 0, 225 packages, geen errors of warnings,
wel `2 moderate severity vulnerabilities`. Stap 5 `npm audit fix`: exit 1, niets
gewijzigd, 2 moderate blijven (`minimatch` 7.0.0 - 11.0.0, GHSA-g3hv-75wg-m249, via
`nodemon`). De `--force`-fix `nodemon@3.1.11` is een downgrade (nu 3.1.14), dus niet
doorgevoerd. Stap 6 PR #91, `develop` toen op 4297a8e. Stap 8 `Develop build` op 4297a8e
(run 42795151491): success, `codegen / build` en `node-build / build` geslaagd.
Working copy schoon.

### Afwijkingen

1. **`.sdkmanrc` bijwerken in plaats van voorleggen, en pas na de pull.**
   - Wat gebeurde: de skill zet deze stap vóór de pull en zegt alleen "laat de inhoud
     zien en vraag". Vooraf bepaald: bijwerken naar de meest recente versies die een
     minor of patch update betekenen, pas na de pull van stap 3. Beschikbare versies
     opgehaald via de SDKMAN-API (`api.sdkman.io/2/candidates/<sdk>/darwinarm64/versions/list?installed=`).
     Gradle 9.8.2 naar 9.9.0. Java blijft `25.0.5.0+8-tem`: dat is de nieuwste binnen
     major 25, 26 en 27 zijn major-updates.
   - Besluit: bijwerken zonder te vragen, na de pull.
   - Indeling: **generiek**.
   - Gaten die dit liet zien: de skill zegt niet hoe je de versies vindt, en niet dat
     je de vendor-suffix (`-tem`) behoudt. Een Gradle-major of Java-major kent geen regel.
2. **Eén gezamenlijke PR, met een branchnaam die bij de inhoud past.**
   - Wat gebeurde: stap 6 gaat alleen over audit-fixes en schrijft
     `feature/audit-fix-<package>` voor. Vooraf bepaald: `.sdkmanrc` en audit-fixes in
     één PR, om het aantal builds te beperken. Hier wijzigde alleen `.sdkmanrc`:
     branch `feature/sdkman-gradle-9.9.0`, PR #91 naar `develop`.
   - Besluit: één PR, de naam volgt de inhoud.
   - Indeling: **generiek**. De `feature/`-prefix bij base `develop` stond al in de skill.
3. **Rode Dependabot-PR: oorzaak uit de CI-log halen, niet alleen melden.**
   - Wat gebeurde: de skill zegt alleen "leg aan mij voor". Vooraf bepaald: niet mergen,
     niets wijzigen, de oorzaak in de CI-logs zoeken en met een voorstel voorleggen. Via
     de job-URL uit `statusCheckRollup` en `gh run view --job <id> --log-failed`
     gevonden: `npm ci` faalt in `node-build / build` met `ERESOLVE`. `@apollo/server`
     5.5.1 heeft peer `graphql@^16.11.0`, #89 zet graphql op 17.1.0. 5.5.1 is de
     nieuwste versie van `@apollo/server`, er is dus nog geen release die graphql 17
     toestaat.
   - Besluit: #89 sluiten en major-updates van graphql uitsluiten in
     `.github/dependabot.yml`, zodat minor- en patch-updates blijven komen (PR #92).
     Deze afhandeling wordt standaard in de skill voor een update die niet gemerged
     kan worden omdat de nieuwe versie nog niet ondersteund wordt.
   - Indeling: de werkwijze is **generiek**, de oorzaak (graphql en Apollo) is
     **projectspecifiek**.
4. **Doorgaan met de routine terwijl een rode PR openstaat.**
   - Wat gebeurde: de skill zegt dat de overige groene PR's wel gemerged worden, maar
     niet of stap 2 en verder dan doorgaan. Ik ben doorgegaan, omdat de opdracht de
     bevindingen van #89 los van de rest behandelde.
   - Besluit: geen; viel onder mijn opdracht vooraf.
   - Indeling: **generiek**, geen regel in de skill.
5. **Groene checks zeggen weinig over `.sdkmanrc`.**
   - Wat gebeurde: CI en `npm run codegen` draaien `./gradlew`, dus de wrapper. De
     Gradle uit `.sdkmanrc` wordt daar niet gebruikt, en Gradle 9.9.0 is lokaal niet
     gedraaid. De 3/3 op #91 toont dus niet dat die versie werkt.
   - Besluit: geen; meegenomen voor het voorstel.
   - Indeling: **projectspecifiek** (Gradle via wrapper in `/codegen`).
6. **Volgorde van `.sdkmanrc` en de wrapper-update.**
   - Wat gebeurde: #90 zette de wrapper op 9.9.0 en de update van `.sdkmanrc` volgde
     daarna. Zonder de bijwerkstap lopen wrapper en `.sdkmanrc` uit elkaar, omdat
     Dependabot `.sdkmanrc` niet bijwerkt.
   - Besluit: geen; meegenomen voor het voorstel.
   - Indeling: **projectspecifiek**.
7. **Controle op een PR-template mislukte in zsh.**
   - Wat gebeurde: `ls .github/PULL_REQUEST_TEMPLATE*` brak af met `no matches found`,
     omdat zsh een glob zonder treffers als fout ziet. Met `find` opnieuw gedaan: er is
     geen template. De skill noemt templates niet.
   - Besluit: geen.
   - Indeling: **generiek**, klein. Past bij de eerdere zsh-opmerking in Verrassingen.

### Plaatsing na de run

Doorgevoerd op 2026-11-10. Stapnummers zijn die van de bijgewerkte `SKILL.md`. De
projectgegevens van `rostering-api` staan in
`.claude/skills/dependabot-routine/projecten/rostering-api.md`.

| Afwijking | Plaats | Waar |
| --- | --- | --- |
| 1. `.sdkmanrc` bijwerken, na de pull | `SKILL.md` | stap 2 en 3 omgewisseld; nieuwe tekst in stap 3 |
| 2. Eén gezamenlijke PR | `SKILL.md` | stap 6; branchnaam volgt de inhoud |
| 3. Rode PR | `SKILL.md` | stap 1 (`Rode PR's`), stap 6 en stap 9 |
| 3. Uitzondering voor graphql | projectbestand | stap 7; PR #92 |
| 4. Doorgaan bij een rode PR | `SKILL.md` | stap 1: de routine afmaken |
| 5. Groene checks en `.sdkmanrc` | projectbestand | stap 3; opgelost doordat Gradle de wrapper volgt |
| 6. Wrapper en `.sdkmanrc` gelijk houden | projectbestand | stap 3; Gradle volgt de wrapper, ook bij een major |
| 7. Zsh-glob op een PR-template | geen | de skill schrijft die controle niet voor |

Na de run: PR #92 squash-gemerged (b2df812) en #89 gesloten met een opmerking. Het
waren twee eigen PR's ondanks afwijking 2, omdat het besluit over #89 pas viel nadat #91
gemerged was. Eindstand: `develop` op b2df812, `Develop build` (run 42796660662) success.

## Logboek 2026-11-10 (roep, testrun van de skill)

Testrun van de skill `dependabot-routine`. De skill is tijdens de run niet aangepast.
Per afwijking: wat er gebeurde, wat ik besloot, en of het generiek of projectspecifiek
lijkt. Afwijkingen 1 tot en met 4 had ik vooraf opgegeven.

Stappen: repo-naam `roep` (`Flow-Cloud-Systems/roep`), geen `projecten/roep.md`. Maven-project
(`pom.xml`, geen `package-lock.json`). Eén open Dependabot-PR: #204 (groep
`minor-and-patch`, 3 updates), base `develop`.

| PR | Inhoud | Checks | Actie |
| --- | --- | --- | --- |
| #204 | aws sdk 2.57.9 naar 2.57.11, axon-stomp-event-publishing 5.5.0 naar 5.6.0, kotlin-logging-jvm 8.0.4 naar 8.0.6 | eerst 0/0 (storing), na volledige herstart 2/2 groen | squash-merge (676669d6) |

Eindstand na de routine (PR #205 kwam daarna, zie onderaan): `develop` op 676669d6, `Develop build` (run 42802769311) success, working copy
schoon, geen open Dependabot-PR's. Geen eigen PR nodig (`.sdkmanrc` ongewijzigd, geen fixes).

### Afwijkingen

1. **Vooraf opgegeven: herstart van een check die door een storing faalt.**
   - Wat gebeurde: #204 toont in de routine `checks=0/0` en `gh pr checks` zegt `no checks
     reported`. De regel "Een PR is groen als er minstens één check is" maakt hem dus niet
     groen, en `Rode PR's` matcht niet, want er is geen `FAILURE` in `statusCheckRollup`.
     De storing is alleen zichtbaar via `gh run list --branch <head-branch>`: runs
     42671486902 (`GitFlow Pull Request Validator`) en 42671487183 (`Pull request build`),
     allebei `completed/failure`, event `pull_request`, attempt 1. Er zijn twee rode runs,
     niet één.
   - Foutmelding: niet op te halen. Er is geen job, dus ook geen job-id voor
     `gh run view --job <id> --log-failed`. Beide runs hebben 0 jobs en 0 check-runs, de
     log-zip is een lege zip van 22 bytes en de commit heeft `statusCheckRollup: null`.
     De tekst "internal server error" heb ik dus niet zelf gezien, die komt uit de opdracht.
   - Hoe herkend als storing: (a) 0 jobs, dus er is geen code, Maven of dependency gedraaid;
     (b) beide runs duurden ongeveer een minuut (18:09:24 tot 18:10:2x UTC op 2026-11-09);
     (c) githubstatus.com meldt `Incident with Actions and Checks API` (critical, 18:12:37
     tot 18:59:32 UTC, "elevated errors affecting GitHub Actions and the Checks API");
     (d) de vorige PR-runs op dezelfde workflows (5 november) waren groen.
   - Bijzonderheid: `gh run view 42671486902` faalt zelf met een 404 op de workflow.
     `git-workflow.yml` staat niet in de repo, de validator komt uit een ruleset op
     organisatieniveau. `gh api repos/.../actions/runs/<id>` werkt wel.
   - Indeling: **generiek** (herkennen zonder job-log, ook als de PR 0 checks toont). De
     validator via een ruleset is **projectspecifiek** of organisatiespecifiek.
   - Herstart: 0 keer gelukt. `gh run rerun 42671487183 --failed` gaf `This workflow run
     cannot be retried`. `gh run rerun 42671486902 --failed` strandde op dezelfde 404 op de
     workflow, en rechtstreeks via `POST .../actions/runs/42671486902/rerun-failed-jobs`
     kwam HTTP 403 `This workflow run cannot be retried`. Elke run dus één poging, geen
     tweede omdat de weigering definitief is. Beide runs staan nog op attempt 1.
   - Gevolg: de regel "maximaal twee keer herstarten" is hier niet toepasbaar. Een run
     zonder jobs kan niet herstart worden. Volgens de opdracht behandeld als rode PR: niet
     gemerged, niets gewijzigd, voorgelegd.
   - Uitweg: `@dependabot recreate` als comment op #204 (voorgesteld door Claude).
   - Besluit: comment geplaatst op 2026-11-10. Mogelijk standaard opnemen in de skill.
   - Resultaat comment: na enkele minuten geen reactie van Dependabot, geen update-run en
     geen nieuwe commit op de PR. Hielp dus niet (of nog niet). Op mijn verzoek de comment
     weer verwijderd, zodat Dependabot er niet alsnog op reageert terwijl de herstarte
     runs lopen.
   - Wat wel werkte: de volledige run herstarten, op aanwijzing van mij (knop in de
     GitHub-UI). Niet `rerun-failed-jobs` maar `gh api -X POST
     repos/{owner}/{repo}/actions/runs/<id>/rerun`, voor beide runs. Antwoord `{}`, beide
     runs op attempt 2 met jobs in de wachtrij. Een run zonder jobs heeft geen gefaalde
     jobs om te herstarten; daarom weigert `--failed` en kan de hele run wel. `gh run rerun
     <id>` zonder `--failed` is niet geprobeerd: `gh` struikelt op de validator over de 404
     op de workflow.
   - Uitkomst: beide runs op attempt 2 groen, #204 2/2 en `merge=CLEAN`. Squash-merge
     (676669d6). Volledig herstart: 1 keer per run, en dat hielp.
2. **Vooraf opgegeven: security scan via IntelliJ of een alternatief.**
   - IntelliJ, wat werkte: de MCP-server is bereikbaar en het project is open.
     `get_project_dependencies` geeft alle jars met versie, maar zonder groupId en zonder
     kwetsbaarheden. `search_ide_actions` vindt `PCAnalyzeVulnerableDependencies`
     (`Vulnerable Dependencies…`, Package Checker).
   - IntelliJ, wat niet werkte: `get_file_problems` en `get_inspections` op `pom.xml`
     (ook op INFORMATION) geven geen kwetsbaarheden, alleen naamloze INFORMATION-regels en
     een typo. `invoke_ide_action` met de actie geeft alleen `{actionId, isToggleAction}`
     terug: het toolvenster gaat open bij de gebruiker, maar de inhoud komt niet bij Claude.
     `run_inspection_kts_project` is niet geprobeerd: die draait alleen op Java- en
     Kotlin-bronbestanden, en de bevindingen staan in `pom.xml` en de bibliotheken.
     Conclusie: de scanner is te starten, maar het resultaat niet uit te lezen.
   - Alternatieven: `gh api repos/{owner}/{repo}/dependabot/alerts` gaf 403 `Dependabot
     alerts are disabled for this repository`. `osv-scanner`, `trivy` en `grype` zijn niet
     geïnstalleerd en ik heb ze niet geïnstalleerd. Wel gewerkt: `mvn -q -o dependency:list`
     naar een tekstbestand (353 dependencies, inclusief test, zonder `com.crimsoncricket`)
     en daarmee de OSV-API (`api.osv.dev/v1/querybatch`).
   - Uitkomst OSV: 2 van de 353 met bevindingen. `org.webjars.npm:jquery` 3.0.0-rc1: 5
     advisories (1 high, 4 moderate), eerste versie die alles dekt 3.5.0.
     `org.webjars:bootstrap` 3.3.5: 6 moderate, eerste versie die alles dekt 3.4.1.
   - Beperking: OSV koppelt advisories aan coördinaten. `org.webjars:jquery` 1.11.1 en
     `org.webjars.bower:jquery` 4.0.0-beta krijgen geen treffer, terwijl 1.11.1 inhoudelijk
     onder dezelfde jQuery-advisories valt. De scan onderschat de webjars dus.
   - Vergelijking met IntelliJ (Package Checker, resultaten van Mend.io, lijst van mij
     geplakt). IntelliJ meldt 5 dependencies, allemaal webjars, 23 meldingen:

     | Dependency | IntelliJ | OSV op Maven-coördinaat | OSV op npm-naam |
     | --- | --- | --- | --- |
     | `org.webjars:bootstrap` 3.3.5 | 7 | 6 gelijk, mist CVE-2024-6484 | dezelfde 6, plus CVE-2024-6485 |
     | `org.webjars.npm:jquery` 3.0.0-rc1 | 5 | 5, waarvan 4 gelijk | gelijk aan Maven |
     | `org.webjars:jquery` 1.11.1 | 4 | 0 | 3 (CVE-2015-9251, CVE-2019-11358, CVE-2020-11023) |
     | `org.webjars:momentjs` 2.10.3 | 5 | 0 | 3 (mist CVE-2022-31129 en WS-2016-0075) |
     | `org.webjars.bower:datatables.net` 1.10.12 | 2 | 0 | 2 gelijk |

     Bij jQuery 3.0.0-rc1 heeft IntelliJ CVE-2017-16027 en OSV CVE-2015-9251. Buiten de
     webjars melden beide niets (OSV 0 van de overige dependencies, IntelliJ niets).
   - Waarom het verschilt: OSV koppelt GitHub-advisories aan exacte coördinaten, en die
     staan meestal op npm en niet op `org.webjars*`. Mend koppelt de webjars wel aan het
     npm-pakket en heeft eigen meldingen (`WS-...`). Opvragen op npm-naam dicht het gat
     grotendeels, maar niet helemaal.
   - Waarde van de validatie: de uitkomst is gelijk voor wat telt (buiten de webjars
     niets), maar dat zijn twee nullen. Er is in dit project dus geen positieve controle
     dat OSV een echte Maven-bevinding vindt die IntelliJ ook vindt, behalve bootstrap en
     jQuery.
   - Fixes: geen doorgevoerd. Maven heeft geen `audit fix`, en `.github/dependabot.yml`
     negeert `org.webjars*:*` bewust.
   - Besluit: kwetsbaarheden in webjars negeren in dit project. Die code is sterk
     verouderd en wordt geport naar de React-applicatie; daar gaat geen energie meer in.
   - Besluit over de scanner: OSV voorlopig accepteren als tegenhanger. Ik kijk zelf nog na
     of dat voor andere Java-projecten goede resultaten geeft.
   - Besluit over fixes: patchen hoort wél in de skill, niet alleen melden. JVM wordt de
     standaard in de skill en npm de uitzondering, omdat de meeste projecten JVM zijn.
   - Indeling: het negeren van webjars geldt voor de twee projecten die webjars gebruiken,
     `roep` en `cata`, allemaal oude legacy die we negeren. Daarom
     staat het in de projectbestanden en niet in `SKILL.md`. Dat OSV webjars onderschat,
     is hier geen probleem. De scanner en het patchen zijn **generiek** voor
     JVM-projecten.
3. **Vooraf opgegeven: `.sdkmanrc` zelf uitzoeken, na de pull.**
   - Wat gebeurde: SDKMAN-API zoals in stap 3 van de skill. Java `25.0.5.0+8-tem` is de
     nieuwste Temurin binnen major 25 (26.0.2.1+1 en 27.0.0.0+35 zijn nieuwere majors).
     Maven 3.10.0 is de nieuwste stabiele versie binnen major 3 (4.0.0-rc-7 is een
     release candidate van een nieuwe major). Niets gewijzigd.
   - De stap stond in de skill al na de pull, dus dit was geen afwijking meer.
   - Gat in de skill: er staat niet dat pre-releases (`-rc-`) niet meetellen. Ook niet dat
     `maven_version` in `.github/workflows/*.yml` mee moet als Maven wél wijzigt.
   - Indeling: pre-releases **generiek**, de workflow-versies **projectspecifiek**.
4. **Vooraf opgegeven: één PR.**
   - Wat gebeurde: geen wijzigingen, dus geen PR nodig. De werkwijze stond al in stap 6.
   - Indeling: **generiek**, geen wijziging nodig.
5. **De skill gaat uit van npm, dit project is Maven.**
   - Rode PR's: de afhandeling leunt op `ERESOLVE` en `npm view`. Hier niet nodig geweest.
   - Stap 4 en 5: geen `package-lock.json`, dus volgens de skill gevraagd. Besluit: stap 4
     is `mvn clean package`, stap 5 is scannen via OSV en melden, op voorwaarde dat de
     uitkomsten overeenkomen met IntelliJ (zie afwijking 2).
   - Stap 4 uitgevoerd op 676669d6 (Java 25.0.5, Maven 3.10.0): `mvn clean package` exit 0,
     `BUILD SUCCESS`, 546 tests, 0 failures, 0 errors, 25 s. 8 warnings, allemaal in
     gegenereerde OpenAPI-code in `target/generated-sources/` (`swagger-more` en
     `swagger-iam`).
   - Stap 5 herhaald op 676669d6: 354 dependencies, dezelfde 2 met bevindingen in OSV
     (bootstrap en npm-jquery, beide webjars). Na het negeren van webjars blijft niets over.
   - Indeling: **generiek** dat de skill een niet-npm-tak nodig heeft, de commando's
     **projectspecifiek**.
6. **`statusCheckRollup` is leeg bij een run zonder jobs.**
   - Wat gebeurde: de opdracht uit stap 1 toonde `0/0`. De skill legt dat voor ("ontbrekende
     checks") maar kijkt niet naar `gh run list --branch <head>`, waardoor de rode runs
     onzichtbaar blijven.
   - Besluit: geen; meegenomen voor het voorstel.
   - Indeling: **generiek**.
7. **Kleine dingen.**
   - `.github/workflows/pre-release.yml` heeft `maven_version: '3.10.06'`, vermoedelijk een
     typefout. Niet aangepast, buiten deze routine. Later hersteld naar `'3.10.0'`, zoals
     `pr.yml`, `develop.yml` en `.sdkmanrc`: PR #206 naar `develop`
     (`feature/fix-pre-release-maven-version`). De workflow draait alleen bij een push naar
     `hotfix/*` of `release/*`, dus de fout viel niet op.
   - De pyenv-Python 3.11.1 mist de `ssl`-module, `/usr/bin/python3` werkte wel. Opgenomen
     in `SKILL.md`, stap 5.
   - De SessionEnd-hook van de vault commit automatisch, ook dit logboek. Dat botst met
     "Commit niets in ~/vault". Voorgelegd.
     - Uitgezocht met de `claude-code-guide`-agent (docs van code.claude.com, niet zelf
       getest): bij `claude --add-dir ~/vault` in een ander project draaien de hooks,
       permissions en het model van de vault niet. Alleen `enabledPlugins` en
       `extraKnownMarketplaces` uit `settings.json` worden meegenomen. Skills uit
       `.claude/skills/` laden wel (met live reload; bij een naamconflict met prefix),
       `CLAUDE.md` alleen met `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`.
       `$CLAUDE_PROJECT_DIR` is de map waar de sessie startte.
     - Gevolg: bij een routine in het projectrepo met `--add-dir ~/vault` is er geen
       auto-commit en geen `build_index.py`; wijzigingen in logboek en skill blijven
       uncommitted staan, en ik loop ze zelf na. De routine start in het project (zo staat
       het in de skill), dus de botsing raakt de routine niet. Die speelt alleen bij een
       sessie die in `~/vault` start: daar commit de hook bij afsluiten alles wat openstaat,
       ook wijzigingen aan de skill die ik nog niet had nagelopen. Dat past bij de roep-run:
       de wijzigingen stonden daarna uncommitted in de vault.
     - Besluit: geen aanpassing aan de skill of de hook nodig. Afwijking 7 is hiermee
       afgehandeld.
     - Niet onderzocht en alleen relevant bij een sessie in de vault: SessionEnd-hooks
       hebben standaard 1,5 seconde, tenzij `timeout` is gezet (maximaal 60). De commit in
       de vault-hook kan daar tegenaan lopen.

### Plaatsing na de run

Doorgevoerd op 2026-11-10. De projectgegevens staan in
`.claude/skills/dependabot-routine/projecten/roep.md`, de scripts in
`.claude/skills/dependabot-routine/scripts/`.

| Afwijking | Plaats | Waar |
| --- | --- | --- |
| 1. Herstart bij een storing | `SKILL.md` | stap 1, nieuw kopje `Storing in CI`; volledige herstart als `--failed` niet kan, maximaal twee keer per run |
| 1. `@dependabot recreate` | `SKILL.md` | niet gebruiken, in `Storing in CI` |
| 2. Scan en patchen | `SKILL.md` en `scripts/` | stap 5, tak `JVM-projecten`; `osv_jvm.py` en `check_overrides.py` |
| 2. Overrides controleren | `SKILL.md` en `scripts/` | stap 5, 6 en 9; verouderde en overbodige overrides zelf verwijderen, terugzetten als build of scan faalt; BOM én transitief, Maven én Gradle |
| 2. Webjars negeren | projectbestanden | stap 5, in `roep.md` en `cata.md` |
| 3. Pre-releases in `.sdkmanrc` | `SKILL.md` | stap 3 |
| 3. `maven_version` in workflows | projectbestand | stap 3 |
| 4. Eén PR | geen wijziging | stond al in stap 6; patches toegevoegd aan de opsomming |
| 5. JVM standaard, npm uitzondering | `SKILL.md` | stap 4 kiest op buildbestand in de root, stap 5 met aparte takken, `ERESOLVE` alleen bij npm |
| 5. Warnings in gegenereerde code | projectbestand | stap 4 |
| 6. `0/0` checks | `SKILL.md` | stap 1 |
| 7. Pyenv zonder SSL | `SKILL.md` | stap 5, `/usr/bin/python3 -I` |
| 7. Typefout `maven_version` | geen | PR #206 in `roep`, buiten de skill |
| 7. SessionEnd-hook en `--add-dir` | geen | geen botsing voor de routine, die in het project start; alleen vastgelegd in dit logboek |

Getest: beide scripts op `roep` (Maven, 354 dependencies; 10 overrides: `asm` overbodig,
de rest nog nodig) en op `insights` (Gradle, 364 dependencies, 15 overrides: `asm` overbodig,
`handlebars` handmatig, de rest nog nodig). Bij `insights` klopt `asm`: `jobrunr-bom` 9.0.3
zet die zelf op 9.11.1, de comment in de catalog is verouderd. De scan vond daar ook guava
33.6.0-android (CVE-2026-102554) in `compileClasspath` en `testCompileClasspath`. De
patchstappen en het verwijderen van overrides zijn nog niet echt uitgevoerd, omdat deze
run niets te patchen of te verwijderen had. De keuze
voor OSV is voorlopig: ik kijk nog na of dat voor andere Java-projecten goede resultaten
geeft.

Na de run: PR #205 verwijderde de overbodige `asm`-override uit `pom.xml`, op mijn verzoek
als aparte PR. Eerste echte uitvoering van de override-controle: `mvn clean package` groen
(546 tests), `asm` bleef 9.11.1, opgeloste dependency-lijst ongewijzigd, scan zonder
bevindingen. Squash-merge (b5eabab7).

## Logboek 2026-11-10 (cata, testrun van de skill met YouTrack-issue)

Testrun van de skill `dependabot-routine`, met twee uitbreidingen: vooraf een
YouTrack-issue aanmaken en achteraf via dat issue verslag leggen. De skill is tijdens de
run niet aangepast. Per afwijking: wat er gebeurde, wat ik besloot, en of het generiek of
projectspecifiek lijkt.

### Fase 1: YouTrack-issue

- Eerste poging: vier meerkeuzevragen tegelijk (parent, samenvatting, velden, beschrijving),
  op basis van eerdere issues. Afgewezen: ik wil Claude stap voor stap door het proces leiden
  in plaats van vragen beantwoorden.
- Stap 1, parent bepalen: uitgangspunt is het Pompkracht Kanban-bord. Gevraagd of Claude
  kan zien wat daarop staat.
  - De YouTrack-MCP heeft geen tool voor agile boards. Het kan wel via `search_issues`.
  - De boardnaam is `Pompkracht Kanban Board`, gevonden in de opgeslagen zoekopdracht
    `Pompkracht Kanban Board Backlog` (`get_saved_issue_searches`). De namen `Pompkracht
    Kanban` en `Board: {...}` geven stil 0 treffers, geen foutmelding.
  - Werkende query: `has: {Board Pompkracht Kanban Board} #Unresolved`. Toont wel welke
    issues op het bord staan, niet de kolom of volgorde.
  - Herkenning van de parent (mijn regel): Type `Maintenance`, en de titel begint met
    `Dependabot upgrades <jaar> w<bereik>`. In PCATA matcht precies één onopgelost issue op
    het bord: PCATA-594 (`Dependabot upgrades 2026 w40-45`, In Progress).
  - Let op voor de skill: in RPAAS beginnen de titels met de naam van de applicatie
    (`Rostering API - Dependabot upgrades ...`), en daar staan meerdere parents op het bord.
    De regel "begint met Dependabot" dekt die niet.
  - Besluit: de match zoek je altijd in het YouTrack-project dat bij de huidige repository
    hoort. Voor `cata` is dat `pompkracht-cata` (key `PCATA`), en daarmee is PCATA-594 de
    enige match. Indeling: de regel is **generiek**, de koppeling repo naar YouTrack-project
    is **projectspecifiek** (`projecten/<repo>.md`).
- Stap 2, parent aanmaken als er geen match is. Hier bestaat de parent al, maar we testen
  het proces met een tijdelijk issue dat daarna weer weg moet.
  - Velden (mijn regel): Type `Maintenance`, State `In Progress`, Assignee ik
    (`Martijn_van_der_Woud`), Board ingevuld.
  - Tegenvaller 1: `Board` staat niet in `get_issue_fields_schema` van PCATA, omdat het geen
    custom field is. De YouTrack-MCP heeft ook geen tool voor commands of boards.
  - Tegenvaller 2: de YouTrack-MCP heeft geen tool om een issue te verwijderen. Weghalen kan
    dus niet via Claude. Ik haal het testissue zelf weg.
  - Titel: `Dependabot upgrades 2026 w46`, zonder `TEST`, op mijn akkoord.
  - Poging om het board te zetten met `create_issue` en `customFields`
    `"Board Pompkracht Kanban Board": "Current sprint"`: geweigerd met `Issue field 'Board
    Pompkracht Kanban Board' not found`. De hele aanmaak mislukt dan, er ontstaat geen issue.
  - Daarna zonder board aangemaakt: PCATA-616 (testissue). Type, State en Assignee zijn
    gezet, Priority kreeg de default `Normal`. Het issue komt niet vanzelf op het bord.
  - Het veld heet in YouTrack `Boards` (meervoud). Claude leest het niet als veld: `get_issue`
    toont het niet, alleen de zoekfilter `has: {Board <naam>}` werkt.
  - Documentatie YouTrack (niet getest): schrijven kan via de REST-API, niet via de MCP. Twee
    routes: `POST /api/commands` met het command `Board <boardnaam> <sprint>`, en `POST
    /api/agiles/<id>/sprints/<id>/issues` (alleen bij handmatige toewijzing op het bord; bron
    is een antwoord op het JetBrains-forum). Beide hebben een eigen YouTrack-token nodig. De
    combinatie van `/api/commands` met het Board-command staat niet letterlijk in de docs.
  - Token: de YouTrack-MCP gebruikt een token dat letterlijk in `~/.claude.json` staat, onder
    `mcpServers.YouTrack.headers.Authorization`, en een tweede item onder
    `projects["/Users/martijn"]`. Dit is alleen de vindplaats, de waarde is niet uitgelezen.
    Ik heb hem zelf als `YOUTRACK_TOKEN` in `~/vault/.env` gezet.
  - Board zetten via REST, werkt met dat token. Het MCP-token werkt dus ook voor de REST-API.
    `GET /youtrack/api/agiles` geeft het bord (`87-6`) met één sprint, `Kanban workflow`
    (`91-28`). Het command is `add Board Pompkracht Kanban Board Kanban workflow`, via
    `POST /youtrack/api/commands` met `issues: [{idReadable: ...}]`. Vooraf gecontroleerd
    met `POST /youtrack/api/commands/assist`, dat niets uitvoert. De vorm met accolades
    (`{Kanban workflow}`) geeft een fout. Uitgevoerd op PCATA-616: HTTP 200.
    Indeling: bordnaam en sprint **organisatiespecifiek**, de werkwijze **generiek**.
  - PCATA-616 is door mij verwijderd.
- Stap 3, bestaande parent bijwerken (mijn regel): bij een match werk je de titel bij, zodat
  het weekbereik tot en met de huidige ISO-week loopt. PCATA-594 van `w40-45` naar `w40-46`.
  Het weeknummer komt uit `date '+%G w%V'`. Indeling: **generiek**.
- Stap 4, subtask aanmaken onder de parent (mijn regel): hetzelfde project, Type `Task`,
  State `In Progress` (we gaan er direct mee aan de slag), Assignee ik. Dit wijkt af van de
  globale regel (State `Open`) voor subtasks.
  - Titel: `Apply Dependabot upgrades 2026 w46`, patroon van de eerdere subtasks, op mijn
    akkoord.
  - `create_issue` met `parentIssue: PCATA-594`, daarna het `add Board`-command via REST,
    want een issue komt niet automatisch op het bord.
  - **Issue-ID voor deze run: PCATA-617.** Geen beschrijving, zoals de eerdere subtasks.

### Fase 2: de routine

Stappen: repo-naam `cata`, `projecten/cata.md` gelezen. Eén open Dependabot-PR.

| PR | Inhoud | Checks | Actie |
| --- | --- | --- | --- |
| #163 | axon-stomp-event-publishing 5.5.0 naar 5.6.0, kotlin-logging-jvm 8.0.4 naar 8.0.6, jaxb2-maven-plugin (groep `minor-and-patch`) | 2/2 groen | squash-merge (7f35cf70) |
| #164 | eigen PR: overbodige `asm`-pin uit `pom.xml` | 2/2 groen | squash-merge (75cbb9cd) |

Stap 2: `develop` fast-forward van bb9b931f naar 7f35cf70, inclusief PCATA-615 (#162, niet van
deze routine). Stap 3: `.sdkmanrc` ongewijzigd, Java 25.0.5.0+8-tem en Maven 3.10.0 zijn de
nieuwste binnen hun major. Stap 4 op 7f35cf70 (Java 25.0.5, Maven 3.10.0): `mvn clean package`
exit 0, `BUILD SUCCESS`, 1254 tests, 0 failures, 0 errors, 26,6 s. 0 errors, 4 warnings.

Stap 6: PR #164, branch `feature/PCATA-617-remove-redundant-asm-override`, opgeruimd. Stap 7:
geen projectstappen. Stap 8: `Develop build` op 75cbb9cd (run 42823545033) success. Working copy
schoon, geen open Dependabot-PR's.

### Afwijkingen

1. **Stap 4: warnings in gegenereerde code.**
   - Wat gebeurde: alle 4 de warnings zijn deprecations (`Jackson2JsonEncoder`,
     `Jackson2JsonDecoder` en hun `jackson2Json...`-methoden, marked for removal) in
     `target/generated-sources/swagger-iam/.../ApiClient.java`, regels 183 en 184.
     `projecten/roep.md` zegt dat je die daar niet hoeft te melden, `projecten/cata.md` niet.
     Dus volgens stap 4 voorgelegd voordat ik verderging.
   - Besluit: deprecation-warnings in gegenereerde API-clients negeren we in alle projecten.
   - Indeling: **generiek**. Hoort in `SKILL.md` stap 4; de uitzondering in
     `projecten/roep.md` kan dan weg.
2. **Stap 5: `check_overrides.py` ziet de overrides in `cata` niet.**
   - Wat gebeurde: scan op 7f35cf70: 362 dependencies, 0 met bevindingen. De override-controle
     gaf `overrides: 0`, terwijl `dependencyManagement` in `pom.xml` er 4 heeft. Het script
     zoekt een XML-comment met het woord `Override`. De comments in `cata` zijn
     `Transitive...; patches CVE-...`, en `asm` heeft geen comment.
   - Op een kopie in de scratchpad met aangepaste comments (skill en `pom.xml` niet gewijzigd):
     `asm` 9.11.1 `OVERBODIG`, `ognl` 3.4.17, `json-smart` 2.6.1 en `kafka-clients` 4.4.0
     `nog nodig`.
   - Voorgelegd: geen regel voor overrides die het script niet herkent.
   - Besluit: `asm`-pin weghalen uit `pom.xml`, nog niet committen. Ik controleer eerst zelf
     of de IntelliJ-scanner meer kwetsbaarheden vindt dan OSV.
   - Controle na het weghalen: `mvn clean package` exit 0, 1254 tests groen, dezelfde 4
     warnings in gegenereerde code. `asm` blijft 9.11.1, opgeloste dependency-lijst
     ongewijzigd, scan 362 dependencies en 0 bevindingen.
   - IntelliJ-scanner (door mij gedraaid): alleen kwetsbaarheden in webjars, dus geen extra
     bevindingen ten opzichte van OSV.
3. **Stap 6: issuenummer in branch en commit.**
   - Besluit: altijd het issuenummer van de subtask in de branchnaam en in het commitbericht.
     Hier `feature/PCATA-617-remove-redundant-asm-override` en
     `PCATA-617 Remove redundant asm override`.
   - Indeling: **generiek**, hoort in `SKILL.md` stap 6.

### Fase 3: verslag via het issue

- Verslag eerst in de chat getoond, na mijn akkoord als Engels comment in PCATA-617 gezet.
  Webjars zijn weggelaten; de tekst zegt daardoor `no findings`, terwijl de scan ze uitsluit.
- State en uren: PCATA-617 blijft op `In Progress`. Besluit: na een run kijk ik zelf wat er
  gebeurd is en schrijf ik eventueel zelf uren. In de skill hoeft na het comment niets meer
  met het issue te gebeuren. Indeling: **generiek**.

### Fase 4: besluiten bij het voorstel

- Meer dan één parent: stoppen en vragen.
- De subtask van deze week bestaat al: een nieuwe run binnen die subtask, het comment gaat weer
  in dezelfde subtask. Staat die op `Done`, dan eerst terug op `In Progress`, en daar blijft
  hij staan.
- Dat verwijderen niet via de MCP kan, hoort niet in de skill.
- Geen handmatige stappen in de skill. Het verslag gaat zonder goedkeuring als comment in het
  issue.
- Een lijst in de vault met alle projecten en hun YouTrack-keys, en alvast voor alle projecten
  een projectbestand met de YouTrack-projectnaam erin. `diis` en `infra` doen niet mee,
  `notifications` en `portal` wel.
- De nieuwe stap krijgt nummer 0.
- Overrides: blijft de versie zonder override gelijk, dan mag hij sowieso weg. Wordt de versie
  zonder override hoger, dan beslist de comment: security-patch mag weg, bewuste pin wegens
  incompatibiliteit blijft, geen comment blijft voor de veiligheid staan.
- Geen open Dependabot-PR's: direct stoppen, ook geen YouTrack-issue.
- Bij de rostering-repo's onder `pompkracht-roepaas` vullen we ook altijd Subsystem in.

### Plaatsing na de run

Doorgevoerd op 2026-11-10. Stapnummers zijn die van de bijgewerkte `SKILL.md`, de nieuwe stap
is stap 0, zodat de bestaande nummers blijven kloppen.

| Les | Plaats | Waar |
| --- | --- | --- |
| Geen open PR's: direct stoppen | `SKILL.md` | begin stap 0; de vraag in stap 1 vervalt |
| Parent zoeken, bijwerken of aanmaken | `SKILL.md` | stap 0, `Parent`; meer dan één match of ander jaar: vragen |
| Subtask aanmaken of hervatten, `Done` terug op `In Progress` | `SKILL.md` | stap 0, `Subtask` |
| Board zetten via REST met `YOUTRACK_TOKEN` | `SKILL.md` | stap 0, `Op het board zetten` |
| Project zonder YouTrack-gegevens: vragen | `SKILL.md` | stap 0 |
| YouTrack-gegevens per repo, titels en Subsystem | projectbestanden | kopje `Stap 0` in 21 bestanden, 17 daarvan nieuw |
| Overzicht repo's en keys | `lijsten/youtrack-projecten.md` | nieuw |
| 1. Deprecations in gegenereerde clients | `SKILL.md` en `roep.md` | stap 4; uitzondering in `roep.md` weg |
| 2. Overrides en de comment-regel | `scripts/check_overrides.py` en `SKILL.md` | elke entry met eigen versie in `dependencyManagement`; stap 5 |
| 3. Issuenummer in branch, commit en PR-titel | `SKILL.md` | stap 6 |
| IntelliJ gelijk aan OSV | geen | alleen dit logboek |
| Verslag via het issue, zonder goedkeuring | `SKILL.md` | stap 9; state en uren doe ik zelf |
| Verwijderen kan niet via de MCP | geen | niet relevant voor de skill |
| Engels in YouTrack, frontmatter | `SKILL.md` | inleiding en beschrijving |

Getest: `check_overrides.py` op een kunstmatige pom voor alle comment-gevallen, en op `cata`
(3 overrides, nog nodig), `roep` (9, gelijk aan de oude uitvoer) en `insights` (1 extra regel:
`org-json`, directe dependency, blijft staan). De zoekopdrachten voor parent en subtask gaven
PCATA-594 en PCATA-617, en voor RPAAS de vier parents. Stap 0 is als geheel nog niet gedraaid
met de nieuwe tekst.

Besluit achteraf: PRC en PMD (`react-notifications`, `profile-presentation-design`,
`axon-stomp-event-publishing`) hebben een afwijkende flow, daar wordt direct een taak
aangemaakt zonder parent. In `SKILL.md` stap 0 als `Parent: geen`, in de drie projectbestanden
ingevuld. Die taken gaan wel op het board: daar komen ze als ongecategoriseerd onderaan te
staan, en na controle haal ik ze er zelf af. Daarom staan oudere taken als PRC-59 en PMD-8 er
niet meer op.

`notifications` is een Scala-project: Dependabot ondersteunt Scala niet, dus daar gebruiken we
Scala Steward, voor de rest grotendeels hetzelfde proces. In `projecten/notifications.md`
staan de titels (`Scala Steward upgrades`, parent PN-55) en de twee PR-auteurs: de routine
handelt `app/flow-cloud-scala-steward` en `app/dependabot` af. Ik doe later een aparte testrun
met `notifications` om de afwijkingen te behandelen. Voor `sbt` is er nog geen build- of scanregel: `build.sbt` staat
niet in stap 4 en `osv_jvm.py` is alleen getest op Maven en Gradle. Bij de eerste run legt de
skill dat dus voor.
