---
description: Acumulus (SIEL), mijn boekhoud- en factuurprogramma - de API, de API-gebruiker en het script waarmee Claude verkoopfacturen als concept aanmaakt en de PDF ophaalt
tags: [werk, facturatie, administratie, acumulus]
---

# Acumulus

Mijn verkoopfacturen maak ik in Acumulus (van SIEL; ik schrijf het zelf vaak als "Accumulus").
Ik verstuur nooit facturen vanuit Acumulus: ik download de PDF, zet die in de verkoopmap op
Google Drive (zie [[facturen-archief]]) en stuur hem als bijlage in een mail die ik zelf opstel.

## API

Documentatie: https://www.siel.nl/acumulus/API/. Elke aanroep is een POST naar
`https://api.sielsystems.nl/acumulus/stable/<pad>.php` met één formulierveld `xmlstring`: een
`<myxml>`-bericht met een `<contract>`-blok (contractcode, gebruikersnaam, wachtwoord). Antwoord
in JSON met `<format>json</format>`. Met `<testmode>1</testmode>` controleert Acumulus de invoer
zonder iets te veranderen.

Valkuilen:

- Bij `invoice_add` hoort `<invoice>` **binnen** `<customer>`, niet ernaast.
- Een factuur met `concept=1` geeft alleen een `conceptid` terug, geen nummer of token. Na het
  definitief maken: `invoice_concept_info` (geeft `entryid`) en dan `entry_info` (geeft
  `invoicenumber` en `token`). Met de token haal je de PDF op via `invoice_get_pdf.php`, zonder
  inloggen.
- Een bestaand concept aanpassen kan niet via de API. Fout in een concept: ik verwijder het en
  het wordt opnieuw aangemaakt.

## API-gebruiker

Aparte gebruiker voor Claude, sinds 17-11-2026, met de rol **API gebruiker**. Gegevens in
`~/vault/.env` (`ACUMULUS_*`, namen in `.env.example`). Fouten en waarschuwingen mailt Acumulus
naar `ACUMULUS_EMAILONERROR`.

De rollen zijn anders dan je zou denken: een **API invoerder** mag minder dan een API gebruiker.
Een invoerder mag facturen toevoegen, maar geen klanten opzoeken (`contacts_list`) en geen
boekingen lezen (`entry_info`). Zonder dat laatste lukt het ophalen van de PDF na een concept niet.
Een API beheerder mag alles.

## Script

`scripts/acumulus.py`:

- `klanten <zoekterm>`, `sjablonen`, `kostenplaatsen`: opzoeken van de vaste id's.
- `factuur <json> [--test]`: maakt een conceptfactuur uit een bestand in `data/facturen/`, en
  toont de regels en de totalen (btw per regel afgerond, zoals Acumulus dat doet). Met `--test`
  verandert er niets.
- `pdf <conceptid>`: na het definitief maken nummer en token opzoeken en de PDF opslaan als
  `verkoop/<jaar>/Factuur_<nummer>.pdf`. Controleert dat het echt een PDF is en overschrijft
  geen bestaand bestand.

## Vaste id's

| Wat | Id |
|---|---|
| Klant Arbeidskracht Personeelsdiensten B.V. | contactid 2318938 |
| Sjabloon Standaard / UK | 2982 / 134714 |
| Kostenplaats Hosting / Consultancy / Contracting / Web Development / Algemeen | 9418 / 104381 / 9419 / 9421 / 9410 |

Gebruikt door de skill `hostingfactuur-flow` (zie [[hosting-transip]]).
