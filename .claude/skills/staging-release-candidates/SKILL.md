---
name: staging-release-candidates
description: Bereidt bij Pompkracht de release candidates voor een staging-uitrol voor - het overzicht van de hoofdissues maken, de frontends releasen, de release branches van alle image-repo's klaarzetten en pushen, de tag `release candidate` op de hoofdissues zetten, wachten op de RC-builds en de infra-PR met alle image tags en de rc-branches maken. Gebruik deze skill zodra ik vraag om release candidates, RC's of een staging-uitrol voor te bereiden, om release branches voor staging te maken, of om een gepauzeerde staging-uitrol te hervatten, ook als ik het woord skill niet gebruik. Niet voor de productie-uitrol, niet voor het mergen van de infra-PR en niet voor vragen over één losse repo.
---

# Release candidates voor staging

Draai vanuit `~/vault`. Alle stappen gaan via scripts in `scripts/`; jij start ze, leest hun
uitvoer en legt de stoppunten aan mij voor. Achtergrond en beslissingen:
[[release-candidates-staging]].

Uitgangspunt: voer alleen uit wat hieronder als regel staat. Een situatie zonder regel leg je
aan mij voor met wat je ziet. Ga nooit om een fout van een script heen.

## Regels

- **Nooit zelf pushen, mergen of taggen.** Geen `git push`, `gh pr merge` of YouTrack-command
  met de hand: alleen de scripts doen dat, binnen hun eigen controles. De allow-regels in
  `.claude/settings.json` staan daarom op de scripts, niet op git.
- **Wijzig niets in `~/staging-runs`**, behalve als ik het vraag. Bij een conflict in stap 4
  los ik het zelf op.
- **Wijzig de scripts of `data/staging-repos.json` niet midden in een uitrol** zonder het
  eerst voor te leggen. Een bug noteer je en leg je voor, met een voorstel.
- **De uitrolnotitie is de plek van de stoppunten.** De secties tussen `<!-- …:start -->`- en
  `<!-- …:eind -->`-markers schrijven de scripts; bewerk die niet.
- **Lange stappen op de achtergrond.** Stap 2 en 3 duren minuten tot een halfuur. Start ze met
  `run_in_background` en wacht op de melding; poll niet.
- Wat de scripts op GitHub en in YouTrack zetten, is Engels; dat regelen de scripts zelf.

## Uitrolnotitie

De uitrolnotitie is `gebieden/werk/staging-releases/<datum>.md`, met `<datum>` de dag van
stap 1. Bepaal bij de start eerst of er nog een uitrol loopt. Neem de nieuwste notitie in die map
(de namen zijn datums, dus de laatste op naam) en kijk of de infra-PR er al in staat:

```bash
ls gebieden/werk/staging-releases/ | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$' | tail -1
grep -c 'Gepusht op .*/pull/' gebieden/werk/staging-releases/<nieuwste>.md
```

- **Geen notitie, of de PR staat erin (1):** de vorige uitrol is af. Begin een nieuwe bij stap 1,
  met `<datum>` = `date +%F`.
- **De PR staat er niet in (0):** die uitrol loopt nog, ook als hij van een eerdere dag is. Ga
  verder in die notitie, met die datum, via `Hervatten`. Meld dat eerst. Wil ik toch een nieuwe
  uitrol beginnen, dan zeg ik dat.

Volgorde in de notitie: Frontends, Release branches, Infra-PR (secties van stap 2–4), daarna
Configuratie klaar in infra en de hoofdissues (stap 1).

## 1. Overzicht

Staat de uitrolnotitie van vandaag er al, draai dit dan niet zonder mijn akkoord:
`staging_overzicht.py --uit` overschrijft het hele bestand, ook de secties van stap 2–4.

```bash
/usr/bin/python3 -I scripts/staging_overzicht.py --uit gebieden/werk/staging-releases/<datum>.md
/usr/bin/python3 -I scripts/staging_frontends.py --plan
```

Het plan van de frontends schrijft niets; het laat zien welke frontends stap 2 released, met
welke versie en of er eerst gepind wordt.

**Stoppunt.** Leg voor, kort:

- waarschuwingen bovenaan de notitie (mislukte PR-lookups: dan kan een hoofdissue ontbreken);
- de rc-branches onder "Configuratie klaar in infra", met hoeveel commits ze achterlopen;
- het aantal inhoudelijke hoofdissues en de repo's met commits zonder issue;
- het plan van de frontends: per frontend de versie, en wat er vreemd aan is (een versie die al
  in de npm-repo staat, 0 commits terwijl hij wel in een image-repo zit, een release-PR die al
  open staat).

Ik controleer de hoofdissues zelf in Obsidian. Ga pas verder als ik akkoord geef: stap 2
released de frontends meteen en zonder stoppunt.

## 2. Release branches en frontends

```bash
/usr/bin/python3 -I scripts/staging_release_branches.py --uit gebieden/werk/staging-releases/<datum>.md
```

Op de achtergrond. Dit start de frontendketen (released, pusht en merget zelf) en zet de
release branches van alle image-repo's klaar in `~/staging-runs/<repo>`, zonder te pushen. Ook
een herstart na een halve run gaat met hetzelfde commando: het script slaat over wat al gedaan
is.

**Stoppunt.** Lees de secties Frontends en Release branches in de uitrolnotitie en leg voor:

- eerst de afwijkingen, per repo met de reden;
- mislukte frontends, met de PR en de run waar het misging;
- per repo die klaarstaat: de release branch, de versie, het base image (oud → nieuw) en bij
  `iam` en `portal` de frontendversies.

Wil ik een diff zien, toon dan:

```bash
git -C ~/staging-runs/<repo> diff origin/develop..<release-branch>
```

Een afwijking los je niet zelf op. "Er staat al een release branch op de remote" betekent dat de
vorige release nog niet is afgerond, of dat ik er met de hand een heb gemaakt: dat beslis ik.
Repo's met een afwijking slaat `--push` vanzelf over; de rest kan door. Ga pas verder als ik
akkoord geef.

## 3. Pushen, taggen en wachten op de RC's

```bash
/usr/bin/python3 -I scripts/staging_release_branches.py --push --uit gebieden/werk/staging-releases/<datum>.md
```

Op de achtergrond (tot 40 minuten). Het script controleert per repo of de branch en
`origin/develop` nog zo staan als bij het klaarzetten, pusht alleen `release/X.Y.Z`, zet direct
daarna de tag `release candidate` op de hoofdissues van wat er in de release zit, en volgt de
pre-release-runs tot de RC-tags er zijn.

Meld daarna: de RC-tag per repo, het aantal getagde hoofdissues, en elke repo met een fout of
een rode run (met de link). Een rode run of een fout leg je voor; zonder fouten ga je door naar
stap 4. Mislukte het taggen, dan kan het apart, eerst droog:

```bash
/usr/bin/python3 -I scripts/staging_release_branches.py --tag --droog --uit gebieden/werk/staging-releases/<datum>.md
```

En pas na mijn akkoord zonder `--droog`.

## 4. Infra-PR

De eerste keer in een uitrol met `--opnieuw`: `~/staging-runs/infra.json` bevat anders nog de
stand van de vorige uitrol.

```bash
/usr/bin/python3 -I scripts/staging_infra_pr.py --opnieuw --uit gebieden/werk/staging-releases/<datum>.md
```

Het script rebaset de rc-branches van de hoofdissues in de release op een nieuwe
`feature/staging-rc-<datum>`, zet in één commit de image tags, pusht en maakt de PR naar
`develop`. Geen stoppunt als alles slaagt.

**Bij een conflict** stopt het script. Leg voor welke rc-branch en welke bestanden, en wacht. Ik
los het op in `~/staging-runs/infra` (vaak in versleutelde secrets-bestanden: los het nooit zelf
op) en rond af met `git rebase --continue`. Zeg ik dat het klaar is, draai dan hetzelfde
commando **zonder** `--opnieuw`: het gaat verder waar het was.

Faalt het script om een andere reden (bijvoorbeeld een RC-tag die niet op de tip van de release
branch staat, omdat een build nog loopt), leg dat dan voor.

## 5. Afsluiten

Eindig met:

- de link naar de infra-PR (uit de sectie Infra-PR van de uitrolnotitie). Mergen doe ik zelf;
- de RC-tags per repo en de repo's die niet meegingen, met de reden;
- de rc-branches die in de PR zitten;
- wat je onderweg tegenkwam aan bugs of verbeterpunten in de scripts, als voorstel.

Commit niets: de SessionEnd-hook commit de uitrolnotitie.

## Hervatten

Loopt er nog een uitrol (zie `Uitrolnotitie`), of vraag ik om er een te hervatten, bepaal dan
de stap uit de state:

```bash
jq -c '{datum, hoofdissues: (.hoofdissues|length?), repos: (.repos|map_values({branch, gepusht, rc, fout}))}' ~/staging-runs/state.json
jq -c '{datum, pr, rc: [.rc[]|{branch,status}]}' ~/staging-runs/infra.json
```

- De datum in `state.json` ligt vóór die van de uitrolnotitie: dat is nog de state van de vorige
  uitrol. Stap 1 is gedaan, het stoppunt van stap 1 komt nog. (`state.json` krijgt de datum van
  stap 2, dus die kan ook later liggen dan de notitie.)
- Repo's zonder `gepusht` en zonder `fout`: stap 2 is gedaan, het stoppunt van stap 2 komt nog.
- Alles gepusht of met een fout, geen `hoofdissues`: stap 3 opnieuw (`--push` slaat gepushte
  repo's over), of alleen `--tag`.
- `infra.json` van deze uitrol met een rc-branch op `conflict`: stap 4 zonder `--opnieuw`, na
  mijn bevestiging dat het conflict is opgelost.
- `infra.json` van deze uitrol met een `pr`: klaar, ga naar stap 5.

Meld wat je vond voordat je iets start.
