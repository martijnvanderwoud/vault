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

1. **Groene PR's squash-mergen**: alle open Dependabot-PR's waarvan alle checks
   geslaagd zijn.
2. **`.sdkmanrc` nakijken**: kijken of er een `.sdkmanrc` is die bijgewerkt moet
   worden. Geldt voor projecten met Java-gebaseerde tooling, zoals codegen.
3. **Lokale working copy bijwerken**: de squash-merges binnenhalen, zodat de base
   branch up-to-date is.
4. **Schone install**: bij npm-projecten `npm ci` draaien en kijken of er errors of
   warnings zijn.
5. **Audit fix zonder breaking changes**: `npm audit fix` draaien om te kijken of er
   iets te patchen valt zonder breaking changes.
6. **Afronden**: geen openstaande changes en verder niets te doen, dan is de routine
   klaar.

### Commando's

```bash
# Per open Dependabot-PR: aantal checks, aantal geslaagd, mergeability
gh pr list -R <org>/<repo> --author "app/dependabot" --state open --json number --jq 'sort_by(.number)|.[].number'
gh pr view <n> -R <org>/<repo> --json statusCheckRollup,mergeable,title \
  --jq '"\(.statusCheckRollup|length) \([.statusCheckRollup[]|select(.conclusion=="SUCCESS")]|length) \(.mergeable) \(.title)"'

# Mergen
gh pr merge <n> -R <org>/<repo> --squash

# Lokaal bijwerken en schone install
ls -la .sdkmanrc
git pull --ff-only origin <base-branch>
npm ci

# Patchen zonder breaking changes (dus zonder --force), daarna effect bekijken
npm audit fix
git status --short
```

### Beslissingen van mij

- Groen betekent: alle checks geslaagd. Dat is het criterium om te squash-mergen.
- Fixes die een downgrade betekenen voer ik nooit door. `npm audit fix --force`
  valt daar in dit geval onder.

### Nog te bepalen voor de skill

Deze situaties kwamen in deze run niet voor:

- Wat ik doe met een PR die niet groen is.
- Wat ik doe als `npm audit fix` wel iets wijzigt (committen, PR, op welke branch).
- Wat ik doe als er wel een `.sdkmanrc` is en wanneer die bijgewerkt moet worden.
- Wat ik doe als `npm ci` errors of warnings geeft.

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

## Logboek 2026-11-09

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
