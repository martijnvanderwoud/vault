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
  per omgeving met de TransIP-periode erbij. Voorbeeld: factuur 20260078 (24-10-2026).
- Hendrik Witteveen: hendrik.witteveen@pompkracht.nl, mail vanaf martijn@crimsoncricket.nl.
- Domeinregistraties (.nl, € 16,50 per jaar) belast ik door aan de domeinhouder, omgerekend
  naar een bedrag per maand op de maandelijkse hostingfactuur. Afke Hennus Coacht betaalt
  bijvoorbeeld € 1,38 per maand voor `afkehennus.nl`. De doorbelasting van domeinen komt later
  nog aan bod.

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
