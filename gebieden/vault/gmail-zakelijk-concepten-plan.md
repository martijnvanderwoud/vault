---
description: Plan voor een eigen script dat concept-mails met bijlage in mijn zakelijke Gmail zet, zodat skills zoals hostingfactuur-flow de factuur-PDF zelf kunnen bijvoegen
tags: [vault, gmail, plan, facturatie]
---

# Plan: concept-mails met bijlage in zakelijke Gmail

Vastgelegd op 17-11-2026, na de eerste hostingfactuur voor FLOW via de skill
`hostingfactuur-flow` (factuur 20260084).

## Probleem

Claude kan een concept-mail in mijn zakelijke Gmail (martijn@crimsoncricket.nl) zetten via de
claude.ai Gmail-koppeling, maar zonder een PDF als bijlage. De koppeling wil de bijlage als
base64 in de tool call zelf. Een factuur-PDF van 250 KB is zo'n 340.000 tekens, en die moet
Claude dan als output overschrijven. Ook een script dat de base64 maakt, helpt niet: alleen
Claude kan de koppeling aanroepen, dus alles gaat toch via de output. Daardoor voeg ik de PDF nu
met de hand toe.

Overwogen en afgevallen:

- **google-prive (workspace-mcp)** kan een bijlage met een bestandspad meegeven, maar het is
  mijn privé-account. Het concept zou dan in de verkeerde mailbox staan.
- **Tweede workspace-mcp voor zakelijk**: werkt wel, maar het is code van derden met toegang
  tot mijn zakelijke mail. Dan moet ik een versie vastzetten en bijhouden, en Claude Code steeds
  herstarten na wijzigingen.
- **Outlook voor Mac via AppleScript**: het nieuwe Outlook ondersteunt AppleScript nauwelijks.

## Oplossing

Een eigen script `scripts/gmail_concept.py` dat zelf met de Gmail API praat:

- Het maakt een MIME-bericht (tekst plus PDF-bijlage, base64 in het script) en zet het met één
  aanroep als concept: `users.drafts.create`. Verzenden kan het niet.
- Alleen het recht `gmail.compose`.
- Alleen de standaardbibliotheek van Python: OAuth met een loopback-redirect, en de refresh
  token en het client secret in de macOS-keychain. Het script toont ze nooit.
- Een **Internal** OAuth-app in de Workspace van crimsoncricket.nl. Daardoor geen
  verificatie en niet elke 7 dagen opnieuw inloggen, anders dan bij [[vault-google-mcp-prive]].
- Aanroep zoals `gmail_concept.py --aan <adres> --onderwerp <tekst> --tekst <bestand> --bijlage <pdf>`.
  Bijlagen alleen uit `~/Mijn Drive/crimsoncricket-documents/`.

## Zo werken we dit af

Start in `~/vault` en zeg: "Doe de eerste open stap uit [[gmail-zakelijk-concepten-plan]]". Aan
het eind van de sessie vink je de stap af, zet je onder `Bevindingen` wat anders liep, en pas je
de latere stappen aan als dat nodig is.

## Voortgang

- [ ] 1. **Voorwerk door Martijn**, ingelogd met het zakelijke account in de Google
  Cloud-console: een nieuw project maken, de Gmail API aanzetten, bij Google Auth Platform de
  audience op Internal zetten en een OAuth-client van het type *Desktop app* maken. Het secret in
  de keychain zetten, in een gewone terminal:
  `security add-generic-password -a "$USER" -s gmail-concept-zakelijk -w`. Het client-ID aan
  Claude geven. Dat is geen geheim en mag in het script.
- [ ] 2. **Script bouwen**: OAuth-login (eenmalig, via een link in de browser), refresh token
  in de keychain, en het concept maken met de bijlage. Testen met een concept aan mezelf.
- [ ] 3. **Skill `hostingfactuur-flow` aanpassen**: in stap 7 het script gebruiken in plaats
  van de claude.ai-koppeling, zodat de PDF automatisch wordt bijgevoegd. De regel "PDF zelf
  bijvoegen" eruit, en een allow-regel voor het script in de skill.
- [ ] 4. **Vastleggen**: een notitie over het script (zoals [[vault-google-mcp-prive]]), en
  een regel in [[vault-beslissingen]] over waarom een eigen script en geen tweede MCP-server.
  Daarna kijken of de hostingfacturen voor Afke en Construct ([[hostingklanten]]) hetzelfde
  pad kunnen volgen.

## Bevindingen

(nog leeg)
