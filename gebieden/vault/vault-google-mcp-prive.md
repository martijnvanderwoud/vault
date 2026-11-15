---
description: Opzet en onderhoud van de MCP-server voor mijn privé-Gmail en -agenda (workspace-mcp) naast de zakelijke claude.ai-koppelingen
tags: [vault, mcp, google]
---

# Google-MCP voor privé-account

Opgezet op 15-11-2026. Beslissing en reden in [[vault-beslissingen]].

## Welke server bij welk account

| Account | Server in Claude Code | Rechten |
|---|---|---|
| martijn@crimsoncricket.nl (zakelijk) | `claude.ai Gmail`, `claude.ai Google Calendar` | zoals ingesteld in claude.ai |
| martijnvanderwoud@gmail.com (privé) | `google-prive` (workspace-mcp, stdio) | Gmail: lezen, labelen, concepten (`gmail:drafts`, geen versturen). Agenda: alleen lezen (`calendar:readonly`). |

Let op: zakelijke post van o.a. TransIP komt binnen op het privé-adres.

## Waar alles staat

- **Google Cloud-project:** `claude-gmail-prive-514810` (onder privé-account, in de console `authuser=1`).
  - APIs aan: Gmail API, Google Calendar API.
  - Google Auth Platform: audience External, status *Testing*, test user = privé-adres.
  - OAuth-client van type *Desktop app* ("workspace-mcp"), vinkje "AI-powered agent" uit.
- **Startscript:** `~/.local/bin/workspace-mcp-prive`. Zet client-ID, account en rechten, en start een vaste versie van workspace-mcp via `uvx`.
- **Client secret:** macOS-keychain, item `workspace-mcp-prive`. Staat niet in config of vault.
- **Tokens:** `~/.google_workspace_mcp/credentials/` (alleen leesbaar voor mij).
- **Registratie:** `claude mcp add --scope user google-prive -- ~/.local/bin/workspace-mcp-prive`.

## Onderhoud

**Elke 7 dagen opnieuw inloggen.** Zolang de app op *Testing* staat, verloopt de login na een week. Claude geeft dan een inloglink; kies het privé-account en klik door de waarschuwing over de niet-geverifieerde app. Om hiervan af te zijn moet de app naar *In production*; daarvoor vraagt de Branding-pagina een homepage, privacy- en voorwaardenlink en authorized domain (bijv. `crimsoncricket.nl`). Geen logo uploaden: dat start merkverificatie.

**Rechten uitbreiden.** In het startscript `--permissions` aanpassen (Gmail: `readonly`, `organize`, `drafts`, `send`, `full`; agenda en overige diensten: `readonly`, `full`). Drive erbij: `drive:readonly` toevoegen en Google Drive API aanzetten in het project. Bij het volgende gebruik opnieuw inloggen. Vraagt hij niet vanzelf om de nieuwe scope, dan het tokenbestand in de credentials-map verwijderen.

**Bijwerken.** Het versienummer in het startscript staat bewust vast (code van derden met toegang tot mijn mail). Bij bijwerken een release kiezen die minstens twee weken oud is.

**Secret vervangen.** Nieuw secret in de console aanmaken, dan:
`security add-generic-password -U -a "$USER" -s workspace-mcp-prive -w` (in een gewone terminal).

## Valkuilen van de opzet

- Google's eigen MCP-servers (`gmailmcp.googleapis.com`, `calendarmcp.googleapis.com`) werken alleen als het Cloud-project in het Workspace Developer Preview Program zit. Zonder dat verbinden ze wel, maar weigert elke tool-aanroep.
- Claude Code herkent claude.ai-koppelingen aan hun URL. Een lokale server met dezelfde URL verbergt de koppeling. Een query string maakt de URL wel uniek, maar Google geeft dan 404; een fragment (`#…`) telt niet als ander adres.
- `uvx` pakte de pyenv-Python 3.11.1, waarvan de SSL-module kapot is (gelinkt tegen een verdwenen openssl 1.1). Het startscript gebruikt daarom `--managed-python --python 3.12`.
- `claude mcp add … --client-secret` en `security … -w` vragen om invoer en werken niet via `!` in Claude Code (geen TTY). Draai ze in een gewone terminal; zet een secret nooit in een env-var in de chat.
- MCP-servers die je buiten de sessie toevoegt, zijn pas zichtbaar na een herstart (`claude --continue`).
