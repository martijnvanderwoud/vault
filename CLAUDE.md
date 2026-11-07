# Persoonlijke agentic OS

Obsidian-vault voor dagelijkse werk- en privézaken: urenregistratie, terugkerende
taken, lijsten en kennis. Claude Code werkt hier als assistent.

## Mapstructuur

- `inbox/` ongesorteerde input
- `dagboek/` daily notes: `dagboek/JJJJ/JJJJ-MM-DD.md`
- `gebieden/` werk, klanten, privé-domeinen
- `lijsten/` boeken, bewaarplekken, ideeën
- `data/` gestructureerde data (CSV, xlsx)
- `scripts/` deterministische helpers
- `.claude/skills/` skills (komen later)

Achtergrond, beslissingen en roadmap van de vault: `gebieden/vault/`.

## Conventies

- Elke notitie heeft YAML-frontmatter met minimaal `description` (één regel) en
  optioneel `tags`.
- Eén onderwerp per notitie. Bestandsnamen in kebab-case, houd ze stabiel
  (hernoem niet zonder reden: links breken).
- Links tussen notities als `[[notitie]]`.
- Cijfers (uren, bedragen) nooit uit het hoofd rekenen: altijd via een script in
  `scripts/` op data in `data/`.
- Antwoord in het Nederlands.

## Gegenereerde bestanden

- `index.md` in elke map is gegenereerd door `scripts/build_index.py`.
  Nooit met de hand bewerken: het script overschrijft ze.
- Hooks (`.claude/settings.json`): na elke Write/Edit wordt `build_index.py`
  gedraaid; bij SessionEnd worden de indexen herbouwd en wordt automatisch
  gecommit (geen push).

## Geheimen

- API-sleutels staan in `.env` (niet in git); `.env.example` toont de namen.
