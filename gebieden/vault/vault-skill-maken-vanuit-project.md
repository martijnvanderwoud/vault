---
description: Stappenplan om een terugkerende taak in een project samen te doen en er daarna een vault-skill van te maken
tags: [vault, skills, werkwijze]
---

# Vault-skill maken vanuit een project

Eerst de taak samen interactief uitvoeren, daarna pas de skill maken. Zo komt in de
skill wat er echt gebeurde, en niet wat ik vooraf dacht dat er zou gebeuren.

Zie [[vault-roadmap]] voor de stand van de vault.

## Stappen

1. **Kies een project waar nu echt wat te doen is**, liefst met iets lastigs erin
   (bij Dependabot: een security-alert of deprecation warning). Een sessie waarin
   alles meteen goed gaat, leert weinig.
2. **Start in het project, met de vault erbij:**

   ```bash
   cd ~/pad/naar/project
   claude --add-dir ~/vault
   ```

   Dan werken de CLAUDE.md, permissies, hooks en `gh`-repo-detectie van het project
   zoals ze dat straks bij een automatische run ook doen, en kan Claude toch in de
   vault schrijven.
3. **Geef de openingsprompt** (hieronder).
4. **Doe de taak samen.** Vertel hardop waarom ik iets beslis: juist die afwegingen
   moeten in de skill komen. Let op welke commando's nodig zijn, want dat wordt de
   lijst van wat een run zonder mij mag doen.
5. **Maak de skill aan het eind van diezelfde sessie**, zolang alle ervaring nog in
   de context zit: `~/vault/.claude/skills/<naam>/SKILL.md`, op basis van de lopende
   notitie.
6. **Probeer de skill op een tweede project.** Dan zie je wat echt generiek is en wat
   nog aan het eerste project vastzit. Controleer daarbij of de skill via `--add-dir`
   beschikbaar is (nog niet getest).

## Openingsprompt

Voorbeeld voor de Dependabot-routine; pas taak en bestandsnaam aan.

> Dit is een verkenningssessie: we doen samen mijn Dependabot-routine, zodat we er
> daarna een skill van kunnen maken. Die skill komt in `~/vault`, mijn persoonlijke
> agentic OS met kennis en skills voor al mijn projecten, en moet dus
> projectoverstijgend worden. Voer de routine nu gewoon concreet in dit project uit,
> maar houd in de notitie apart bij wat generiek is en wat alleen voor dit project
> geldt. Lees eerst `~/vault/CLAUDE.md`. Houd tijdens het werk een notitie bij in
> `~/vault/gebieden/werk/dependabot-routine.md` met de stappen, de commando's, de
> beslissingen die ik neem en wat ons verrast. Doe niets automatisch dat ik normaal
> zelf zou beoordelen, maar vraag het me.

De lopende notitie is belangrijk: bij een lange sessie kan de context worden
samengevat, en dan raak je anders details kwijt.

## Waar je op moet letten

- De CLAUDE.md van de vault wordt niet automatisch geladen. Daarom staat het lezen
  ervan in de openingsprompt.
- De index-hook en autocommit van de vault draaien niet mee in een projectsessie. Dat
  wordt rechtgetrokken zodra de volgende vault-sessie eindigt.
