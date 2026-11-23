---
description: MemBirds, het platform van White Sun Qigong (Franca) voor bestellingen en betaalpagina's - de MCP-koppeling, het aparte beheerdersaccount voor Claude en hoe dat Franca's eigen koppeling niet raakt
tags: [werk, administratie, white-sun, membirds, mcp]
---

# MemBirds

Franca verkoopt via MemBirds (lessen, cursussen, abonnementen). Betalingen lopen via Mollie; in
Acumulus staan de facturen voor MemBirds-bestellingen op rekening Mollie (227282). Zie
[[acumulus]] en [[betalingen-white-sun]].

MemBirds maakt bij elke betaalde bestelling zelf een factuur (en een creditfactuur bij een
terugbetaling), maar daar doe ik niets mee. Ik maak in Acumulus **één eigen factuur per
MemBirds-bestelling** (besluit 2026-11-23). Uitgangspunt is dus de bestelling, niet de
MemBirds-factuur. Documentatie facturen: https://docs.membirds.com/nl/shop/invoices.

## Bron van de bestellingen (besluit 2026-11-23)

- De REST API van MemBirds is alleen voor intern gebruik en heeft geen beschreven endpoints, dus
  daar bouwen we niet op (geen `membirds.py` op de API).
- Voorkeursroute: een **export van de bestellingen** (Shop → Bestellingen → Export, CSV) naar
  `~/Downloads`, die een script leest, zoals `knab.py` het Knab-overzicht leest. Opties in het
  exportvenster: periode (maximaal 12 maanden), "Elk product op nieuwe regel", filters (zoals
  Betaald). Een export bevat persoonsgegevens, blijft 6 dagen staan en is zichtbaar voor alle
  beheerders: na gebruik verwijderen. Zie https://docs.membirds.com/nl/shop/orders#exporteren.
- De kolommen van de export zijn nog niet bekend; het script volgt na een echt bestand.

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

- [x] Apart beheerdersaccount voor Claude werkt (inloggen lukte). De rol is niet gecontroleerd; bedoeld is Financieel manager.
- [x] Koppeling toegevoegd in Claude Code, niet in claude.ai (2026-11-23; de knop voor een eigen
  connector ontbrak in de desktop-app): `claude mcp add --transport http --scope user membirds
  https://mcp.membirds.com/mcp`. Staat dus alleen in Claude Code op deze Mac.
- [x] Ingelogd via `/mcp` (2026-11-23). `list_sites` geeft alleen White Sun Qigong
  (site_id `23e73fa9a497a59311634fffbac1e14f`, academy.whitesunqigong.nl).
- Tools: alleen `list_sites`, `search_tools`, `execute_tools` en wat uploads en screenshots zijn
  direct beschikbaar. Alle andere tools (ook schrijvende, zoals `send_invoice`,
  `update_site_settings`, `delete_checkout`) lopen via de ene tool `execute_tools`. Een
  permissieregel per tool in settings is dus niet mogelijk. Leestools voor ons doel:
  `list_orders`, `get_order`, `list_invoices`, `get_invoice`, `download_invoice` (alle
  `readOnlyHint`).
- [x] In Claude Code gecontroleerd dat de koppeling er is en welke tools hij heeft
- [x] Vraagregel (`ask`) op `mcp__membirds__execute_tools` in `.claude/settings.json`, zodat elke
  aanroep eerst langskomt (2026-11-23). De MCP is optioneel; de bron voor facturen is de export.
- [x] Skill `membirds-facturen` geschreven (2026-11-23).
- [ ] Werkwijze voor een creditfactuur vastleggen (nu maakt Martijn die zelf in Acumulus)

## Werkwijze facturen voor bestellingen

1. Martijn exporteert de bestellingen (CSV, "Elk product op nieuwe regel" aan) naar `~/Downloads`.
2. `membirds.py <csv>` toont per bestelling relatie (op lidnummer), Acumulus-product en bedragen;
   met `--schrijf` komt er per bestelling een bestand in `data/facturen/white-sun/`. Koppelingen
   staan in `data/membirds-white-sun.json`. Bestellingen met korting, terugboeking, btw verlegd,
   bedrijfsnaam, onbekend lid of onbekend product zet het script niet klaar.
3. Controle met `acumulus.py --administratie white-sun factuur <bestand> --test`, na akkoord
   zonder `--test`.
- Factuurdatum: altijd vandaag, zodat factuurnummers in Acumulus op volgorde blijven.
- Beschrijving: "Membirds bestelling <bestelnummer>" (het bestelnummer, niet het factuurnummer
  van MemBirds). Rekening Mollie (227282), niet betaald: de factuur wordt pas betaald als de
  Mollie-uitbetaling is verwerkt.
- Terugbetaling: creditfactuur (werkwijze nog niet vastgelegd).

## Logboek

- 2026-11-23: bestellingen MB2026-00000150, 151 en 152 (20-11-2026) verwerkt: facturen 20260320
  (Brenda Ott, 42,30), 20260321 (Cynthia van Zelm, 54,00) en 20260322 (Lucinda Heikamp, 42,30).
  Eerder, zonder script: bestellingen 144 t/m 149.
