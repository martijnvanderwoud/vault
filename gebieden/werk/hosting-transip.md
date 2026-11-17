---
description: Welke TransIP-producten ik gebruik, aan welke klant ik ze doorbelast en waar de facturen staan
tags: [werk, hosting, transip, facturatie]
---

# Hosting bij TransIP

Account `martijnvanderwoud`. TransIP mailt naar twee adressen. Facturen komen binnen op mijn
zakelijke mail (martijn@crimsoncricket.nl). Andere berichten, zoals aankondigingen van
prijswijzigingen en productnieuws, gaan naar mijn privé-Gmail (martijnvanderwoud@gmail.com).
Zoek dus in allebei.

## Facturen

TransIP stuurt twee facturen per maand, rond de 1e en rond de 15e (`TransIP-F0000_*.pdf`). Op
elke factuur staan andere OpenStack-projecten, afhankelijk van hun factuurperiode. Waar facturen
staan: [[facturen-archief]].

## OpenStack-projecten en doorbelasting

| Project | Gebruik | Doorbelast aan |
|---|---|---|
| `pompkracht-prd` | productieomgeving FLOW | Arbeidskracht (Hendrik Witteveen) |
| `pompkracht-dev` | stagingomgeving FLOW | Arbeidskracht (Hendrik Witteveen) |
| `shared-hosting` | gedeelde K8S-hosting voor Afke Hennus Coacht, Construct Bedrijfspsychologie (Beroepenzoeker), eigen projecten en projecten van Franca: White Sun Qigong (nu, ze is qigonglerares) en Studio Desta (haar eerdere bedrijf als zelfstandig interieurarchitect, domein `studiodesta.nl`) | alleen Afke Hennus en Construct, met een maandelijkse hostingfactuur; de rest wordt niet gefactureerd |
| `os2-pompkracht` | uitgefaseerd (was het migratiedoel voor OS1-project pompkracht) | geen kosten meer |

- Arbeidskracht krijgt een aparte factuur "Hosting FLOW – <maand>" (los van de urenfactuur).
  Daarop staat het bedrag excl. btw van de TransIP-regels van productie en staging, één regel
  per omgeving met de TransIP-periode erbij. Voorbeelden: 20260078 (september, 24-10-2026) en
  20260084 (oktober, 17-11-2026, de eerste via de skill `hostingfactuur-flow`).
- Welke TransIP-facturen bij welke maand horen: de factuur voor maand M gebruikt de twee
  TransIP-facturen uit maand M+1. **Productie** komt uit die van rond de 15e, **staging** uit
  die van rond de 1e. Neem per project het subtotaal van TransIP over. Voor oktober 2026:
  productie 12-10 t/m 11-11 (TransIP 15-11) en staging 17-09 t/m 16-10 (TransIP 01-11). Maak de
  factuur dus pas na de 15e van M+1.
- In Acumulus: klant Arbeidskracht, sjabloon Standaard en kostenplaats **Hosting** (niet
  Consultancy). De id's staan in [[acumulus]].
- Hendrik Witteveen: hendrik.witteveen@pompkracht.nl, mail vanaf martijn@crimsoncricket.nl.
- Domeinregistraties belast ik door aan de domeinhouder: de jaarprijs gedeeld door 12, als
  regel op de maandelijkse hostingfactuur. Nu alleen `afkehennus.nl`.
- Afke Hennus en Construct (vaste maandbedragen, prijsgeschiedenis, werkwijze bij een
  prijsverhoging): [[hostingklanten]].

## Factuurregels herkennen

Het producttype kun je afleiden door het factuurbedrag te delen door het tarief per GB. Bij het
juiste type komt er een heel aantal GB uit.

- **Server uptime (Small HD 8GB / Standard 1GB / Standard 2GB)**: een flavor met een vaste prijs
  per maand.
- **Performance Y1 volume**: NetApp-opslag, € 0,378 per GB per maand (tarief 2026), meestal
  1 tot 12 GB per volume. TransIP rekent per uur af, waardoor een regel soms 1 cent afwijkt.
- **Volume** (zonder toevoeging): HDD-opslag ("Block storage file and archive", 300 IOPS),
  € 0,1072 per GB onder 100 GB en € 0,107 daarboven (tarief 2026).
- **IP (Floating IP)** en **OpenStack router**: elk € 2,77 per maand (tarief 2026).

Tarieven staan op transip.nl/prijzen/vdc (OpenStack) en transip.nl/prijzen/domeinssl.

## Prijswijziging per 15-12-2026

Aangekondigd op 12-11-2026. Bijna alles wordt ongeveer 25% duurder. Producten die niet op de
prijslijst staan (legacy) worden ook 25% duurder.

| Product | 2026 | vanaf 15-12-2026 |
|---|---|---|
| Small HD 8GB | € 45,76 | € 57,20 |
| Standard 1GB | € 9,10 | € 11,38 |
| Standard 2GB | € 15,17 | € 18,97 |
| Floating IP / router | € 2,77 | € 3,47 |
| Performance Y1 per GB (<100 GB) | € 0,378 | € 0,4726 |
| HDD per GB (<100 / ≥100 GB) | € 0,1072 / € 0,107 | € 0,134 / € 0,1338 |
| Domein .nl per jaar | € 16,50 | € 18,99 |

Gevolg voor FLOW, berekend op de facturen van okt/nov 2026 (excl. btw, per maand):
productie € 425,89 → € 532,26 en staging € 329,58 → € 411,88. Samen is dat € 188,67 per
maand meer. Op 15-11-2026 heb ik Hendrik hierover gemaild.

Gevolg voor shared-hosting (factuur 01-11-2026): € 77,42 → € 96,81 per maand, +25,05%.
k3s-2 (Standard 1GB) vervangt k3s-1 (ook Standard 1GB); bij doorrekenen telt maar één van de
twee mee. De doorrekening aan Construct en Afke staat in [[hostingklanten]]. Op 15-11-2026
heb ik ze gemaild.
