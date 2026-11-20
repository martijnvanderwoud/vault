---
description: Het Pompkracht Kanban Board in YouTrack - swimlanes, welke issue types hoofdissue en subtaak zijn, en hoe je een issue op het bord zet
tags: [werk, pompkracht, youtrack]
---

# YouTrack-bord van Pompkracht

Board `Pompkracht Kanban Board`, sprint `Kanban workflow`. Alle Pompkracht-projecten staan erop
(zie [[youtrack-projecten]] voor het project per repo, en `pompkracht-infra` met key `PKI`).

## Issue types

Het bord heeft swimlanes. Een swimlane is altijd een issue van het type:

- `Maintenance`: onderhoud, zoals de Dependabot-upgrades of een aanpassing van CI-workflows
- `Support`
- `Feature`
- `Bug`

Een hoofdissue met subtaken krijgt dus een van deze vier types, anders komt het niet als swimlane
op het bord. De subtaken eronder zijn `Task`, ook als ze in een ander project staan dan het
hoofdissue.

Een losse issue zonder subtaken krijgt het type `Task`, ook als het inhoudelijk onderhoud is. Een
swimlane zonder subtaken werkt niet prettig op het bord. Vastgelegd op 20-11-2026, na PKI-1142
(eerst als `Maintenance` aangemaakt).

## Op het bord zetten

`create_issue` van de YouTrack-MCP zet een issue niet op het bord. Dat gaat met een command:

```bash
/usr/bin/python3 -I ~/vault/scripts/youtrack_command.py <issue-id> "add Board Pompkracht Kanban Board Kanban workflow"
```

Zet het hoofdissue en elke subtaak er apart op. Controleer het met `search_issues`:
`has: {Board Pompkracht Kanban Board} issue ID: <issue-id>`.
