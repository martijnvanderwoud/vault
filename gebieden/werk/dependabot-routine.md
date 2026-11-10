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
