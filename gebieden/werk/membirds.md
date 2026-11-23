---
description: MemBirds, het platform van White Sun Qigong (Franca) voor bestellingen en betaalpagina's - de MCP-koppeling, het aparte beheerdersaccount voor Claude en hoe dat Franca's eigen koppeling niet raakt
tags: [werk, administratie, white-sun, membirds, mcp]
---

# MemBirds

Franca verkoopt via MemBirds (lessen, cursussen, abonnementen). Betalingen lopen via Mollie; in
Acumulus staan de facturen voor MemBirds-bestellingen op rekening Mollie (227282). Zie
[[acumulus]] en [[betalingen-white-sun]].

MemBirds maakt bij elke betaalde bestelling zelf een factuur (en een creditfactuur bij een
terugbetaling). Automatisch doorzetten kan alleen naar Moneybird; naar Acumulus alleen via een
export (PDF, CSV, Excel) die je importeert. Documentatie: https://docs.membirds.com/nl/shop/invoices.

## MCP-koppeling

Documentatie: https://docs.membirds.com/nl/get-started/mcp.

- Adres `https://mcp.membirds.com/mcp`, inloggen met OAuth met een persoonlijk
  MemBirds-beheerdersaccount. Geen API-sleutel.
- De koppeling hoort bij één MemBirds-gebruiker: hij ziet alle actieve sites waar die beheerder
  is, met de rechten van zijn rol per site.
- Kan bestellingen, facturen, abonnementen, leden en meer lezen, en ook aanmaken, wijzigen en
  verwijderen. De docs geven geen lijst met tools.
- Limiet: 120 verzoeken per minuut, 3000 per uur, per beheerder.

## Apart account voor Claude (besluit 2026-11-23)

Tot nu toe logde ik in MemBirds in met Franca's account. Franca heeft vanuit haar eigen
Claude-account ook een MemBirds-koppeling. Wat er gebeurt als dezelfde MemBirds-gebruiker vanuit
twee Claude-accounts koppelt, staat niet in de docs. Daarom koppel ik met een **eigen
beheerdersaccount** op haar site, rol **Financieel manager** (bestellingen, facturen,
abonnementen, termijnen, leden; geen content, instellingen of beheerders). Rollen:
https://docs.membirds.com/nl/settings/admin-users.

Stand van zaken:

- [ ] Franca nodigt het nieuwe account uit als beheerder met rol Financieel manager
- [x] Koppeling toegevoegd in Claude Code, niet in claude.ai (2026-11-23; de knop voor een eigen
  connector ontbrak in de desktop-app): `claude mcp add --transport http --scope user membirds
  https://mcp.membirds.com/mcp`. Staat dus alleen in Claude Code op deze Mac.
- [ ] Inloggen met het nieuwe account via `/mcp` → `membirds` (niet met Franca's account)
- [ ] In Claude Code controleren dat de koppeling er is en welke tools hij heeft
- [ ] Leestools toestaan en schrijftools weigeren in `.claude/settings.json`
- [ ] Werkwijze voor facturen van MemBirds-bestellingen in Acumulus vastleggen (skill)
