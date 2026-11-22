---
description: Acumulus (SIEL), het boekhoud- en factuurprogramma van mij en van White Sun Qigong (Franca) - de API, de API-gebruikers en het script waarmee Claude verkoopfacturen als concept aanmaakt, de PDF ophaalt en uitgaven boekt
tags: [werk, facturatie, administratie, acumulus]
---

# Acumulus

Mijn verkoopfacturen maak ik in Acumulus (van SIEL; ik schrijf het zelf vaak als "Accumulus").
Ik verstuur nooit facturen vanuit Acumulus: ik download de PDF, zet die in de verkoopmap op
Google Drive (zie [[facturen-archief]]) en stuur hem als bijlage in een mail die ik zelf opstel.

Franca heeft een eigen Acumulus voor White Sun Qigong, waarin ik beheerrechten heb. Daarin boek
ik haar inkoopfacturen, ook de facturen die ik haar zelf stuur (zoals [[ziggo-doorbelasting]]).

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
- Uitgaven (inkoopfacturen) gaan via `expenses/expense_add.php`. Ook daar hoort `<expense>`
  **binnen** `<supplier>`; staat het ernaast, dan krijg je een misleidende HTTP 400 "Ongeldige
  numerieke waarde voor accountnumber". Een uitgave heeft geen concept: hij is meteen definitief.
  Er is geen veld voor het factuurnummer van de leverancier en geen bijlage-upload (de PDF gaat
  naar Drive, zie [[facturen-archief]]).
- `contacts/contact_invoices_incoming.php` (ontvangen facturen per relatie) verwisselt
  `costcenterid` en `costheadingid`. De juiste waarden staan in `entry_info`.
- Inactieve relaties komen gewoon mee in `contacts_list` (`contactstatus` 0). Neem de actieve.

## API-gebruikers

Per administratie een aparte gebruiker voor Claude, met de rol **API gebruiker**. Gegevens in
`~/vault/.env` (namen in `.env.example`):

- **The Crimson Cricket**: sinds 17-11-2026, `ACUMULUS_*`.
- **White Sun Qigong**: `ACUMULUS_WHITESUN_*`. Maak ik zelf aan in Franca's Acumulus.

Fouten en waarschuwingen mailt Acumulus naar het adres in `..._EMAILONERROR`.

De rollen zijn anders dan je zou denken: een **API invoerder** mag minder dan een API gebruiker.
Een invoerder mag facturen toevoegen, maar geen klanten opzoeken (`contacts_list`) en geen
boekingen lezen (`entry_info`). Zonder dat laatste lukt het ophalen van de PDF na een concept niet.
Een API beheerder mag alles.

## Script

`scripts/acumulus.py`. Standaard werkt het op The Crimson Cricket; met `--administratie
white-sun` vóór het commando op White Sun Qigong. Een databestand voor White Sun heeft
`"administratie": "white-sun"`, en `factuur` en `uitgave` weigeren een bestand van de andere
administratie. `pdf` kan alleen voor The Crimson Cricket.

- `klanten <zoekterm>` (met actief/inactief), `sjablonen`, `kostenplaatsen`, `kostensoorten`,
  `rekeningen`: opzoeken van de vaste id's. Het veld `accountnumber` in een uitgave is de
  `accountid` uit `rekeningen`, niet het rekeningnummer.
- `factuur <json> [--test]`: maakt een conceptfactuur uit een bestand in `data/facturen/`, met
  betaalstatus niet betaald (tenzij het bestand `"paymentstatus": 2` heeft), en
  toont de regels en de totalen (btw per regel afgerond, zoals Acumulus dat doet). Met `--test`
  verandert er niets.
- `pdf <conceptid>`: na het definitief maken nummer en token opzoeken en de PDF opslaan als
  `verkoop/<jaar>/Factuur_<nummer>.pdf`. Controleert dat het echt een PDF is en overschrijft
  geen bestaand bestand.
- `ontvangen <contactid>`: de laatste ontvangen facturen van een leverancier, met omschrijving,
  rekening, kostensoort en kostenplaats. Het voorbeeld voor een nieuwe boeking.
- `uitgave <json>`: boekt een uitgave uit `data/uitgaven/<Leverancier>-<factuurnummer>.json`
  (White Sun: `data/uitgaven/white-sun/`; zelfde naam als de PDF in het archief) en zet het `entryid` in het bestand. Staat er al een
  `entryid` in, dan boekt het alleen opnieuw als ik dat boekstuk in Acumulus heb verwijderd (zo
  corrigeer ik een boeking: verwijderen, databestand aanpassen, opnieuw boeken). Geen testmode:
  ik kijk de boeking zelf na in Acumulus.

## Vaste id's The Crimson Cricket

| Wat | Id |
|---|---|
| Klant Arbeidskracht Personeelsdiensten B.V. | contactid 2318938 |
| Sjabloon Standaard / UK | 2982 / 134714 |
| Kostenplaats Hosting / Consultancy / Contracting / Web Development / Algemeen | 9418 / 104381 / 9419 / 9421 / 9410 |
| Leverancier Ziggo B.V. (actief) | contactid 10445127 |
| Rekening NL79 INGB 0005 0608 34 / ING Businesscard | accountnumber 13039 / 25072 |
| Kostensoort Telefoon en internet | costheading 6 |

## Vaste id's White Sun Qigong

Aanvullen bij nieuwe leveranciers (`--administratie white-sun` met `klanten`, `kostensoorten`,
`kostenplaatsen` en `rekeningen`).

| Wat | Id |
|---|---|
| Leverancier The Crimson Cricket Internet Services (actief) | contactid 141521 |
| Kostenplaats Algemeen (de enige) | costcenter 10213 |
| Rekening Knab (NL11 KNAB …) | accountnumber 227201 |
| Kostensoort Telefoon en internet | costheading 6 |

Gebruikt door de skills `hostingfactuur-flow` (zie [[hosting-transip]]), `inkoopfactuur` en `ziggo-doorbelasting`.
