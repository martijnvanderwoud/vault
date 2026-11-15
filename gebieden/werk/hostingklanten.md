---
description: Klanten met een vaste maandelijkse hostingfactuur (Construct, Afke Hennus), hun tarieven, prijsgeschiedenis en hoe ik een prijsverhoging doorreken
tags: [werk, hosting, klanten, facturatie]
---

# Hostingklanten

Twee klanten draaien op het OpenStack-project `shared-hosting` bij TransIP (zie
[[hosting-transip]]) en betalen een vast bedrag per maand. Arbeidskracht (FLOW) valt hier niet
onder: die krijgt de werkelijke TransIP-kosten doorbelast.

Hostingfacturen gaan maandelijks achteraf, rond de 10e, als losse factuur "Hosting - <maand>"
(zie [[facturen-archief]]). De mail erbij gaat vanaf martijn@crimsoncricket.nl. Mijn
factuurprogramma rekent de btw per regel uit, daardoor wijkt het totaal soms 1 cent af van
21% over het subtotaal.

## Construct Bedrijfspsychologie

- Contact: Jeroen Meliëzer. Mail naar **info@cbpsy.com** (niet construct.nl); jeroen@cbpsy.com
  bestaat ook. Karin Eitjes doet de administratie en leest info@cbpsy.com.
- Adres op de factuur: Postbus 5095, 1380 GB Weesp.
- Factuurregel: "Beroepenzoeker", 1 regel.

| Per 15 december | Beroepenzoeker per maand, excl. btw |
|---|---|
| 2024 | € 43,94 (+5%) |
| 2025 | € 46,14 (+5%) |
| 2026 | € 57,70 (+25,05%) |

## Afke Hennus Coacht

- Afke Hennus, met een **u** (niet Hennis). Mail naar **info@afkehennus.nl**. Ze tekent ook
  met "Praktijk Voorbij de Woorden".
- Adres op de factuur: Nijenheim 6202, 3704 BK Zeist.
- Factuurregels: "WordPress - www.afkehennus.nl", "Domeinregistratie NL" en
  "Google Workspace - afkehennus.nl".
- Google Workspace (Business Starter) bereken ik 1 op 1 door. Google wijzigt die prijs los van
  TransIP en kondigt dat via de beheerdersmail aan.

| Product per maand, excl. btw | tot 15-12-2024 | 2024 | 2025 | 2026 |
|---|---|---|---|---|
| WordPress | € 11,99 | € 12,59 | € 13,22 | € 16,53 |
| Domeinregistratie NL | | € 1,25 | € 1,38 | € 1,58 |
| Google Workspace | | € 5,99 | € 6,80 | € 6,80 |

De kolommen 2024 t/m 2026 gelden vanaf 15 december van dat jaar. Workspace ging in 2025 al
eerder in het jaar omhoog naar € 6,80, los van TransIP.

## Prijsverhoging doorrekenen

TransIP verhoogt de prijzen meestal per 15 december en kondigt dat half november aan. Zo reken
ik het door (zo gedaan in 2024, 2025 en 2026):

1. Bereken de kosten van `shared-hosting` per maand met de oude en de nieuwe tarieven, op de
   meest recente TransIP-factuur waar het project op staat. Tel tijdelijk dubbeldraaiende
   servers (een vervanger naast de oude) maar één keer mee: dat extra deel is voor mij.
2. Verhoog de vaste bedragen (Beroepenzoeker, WordPress) met hetzelfde percentage.
3. De domeinpost wordt de nieuwe jaarprijs gedeeld door 12, ook per 15 december en niet pas
   bij de volgende verlenging.
4. December wordt in halve maanden verdeeld, niet per dag: één regel tegen het oude en één
   regel tegen het nieuwe tarief, elk met aantal 0,5 (factuur 20260002, december 2025).
5. Mail elke klant half november: kort, met het percentage, de oude en nieuwe bedragen, en wat
   de decemberfactuur wordt. Noem geen totale clusterkosten, want daar draaien ook andere
   projecten op.

## Verdeling van de kosten

`shared-hosting` vanaf 15-12-2026 (excl. btw, per maand, zonder dubbeldraaien):

| | Bedrag | Aandeel |
|---|---|---|
| TransIP-kosten | € 96,81 | 100% |
| Construct | € 57,70 | 60% |
| Afke (WordPress) | € 16,53 | 17% |
| Eigen deel (eigen projecten en die van Franca) | € 22,58 | 23% |

Het eigen deel is € 270,96 per jaar; daarvoor was het € 18,06 per maand. Omdat de klantbedragen
met hetzelfde percentage meegaan, blijft de verdeling gelijk. De domeinen
`whitesunqigong.nl` en `studiodesta.nl` betaal ik zelf.

## Log

- 15-11-2026: prijsverhoging per 15-12-2026 naar Jeroen en Afke gemaild.
