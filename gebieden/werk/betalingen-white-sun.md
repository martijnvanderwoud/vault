---
description: Betalingen op de Knab-rekening van White Sun Qigong (Franca) verwerken in Acumulus - werkwijze in het kort, beslissingen per soort transactie en het logboek per sessie; de stappen staan in de skill betalingen-white-sun
tags: [werk, administratie, acumulus, white-sun]
---

# Betalingen White Sun verwerken

Franca's zakelijke rekening staat bij Knab (NL11 KNAB 0776 5411 61, in Acumulus rekening 227201).
Ik download een transactieoverzicht (CSV) uit Knab en importeer het in Acumulus. Daarna staat
in Acumulus een lijst mutaties die verwerkt moeten worden. Zie ook [[acumulus]].

## Werkwijze

De skill `betalingen-white-sun` (`.claude/skills/betalingen-white-sun/SKILL.md`) beschrijft de
stappen. Kort:

1. Martijn downloadt het Knab-overzicht (CSV) naar `~/Downloads` en importeert het in Acumulus.
   De lijst met mutaties die verwerkt moeten worden, is niet op te vragen via de API.
2. Claude leest de CSV met `scripts/knab.py` en haalt de openstaande facturen op met
   `acumulus.py --administratie white-sun openstaand`.
3. Per transactie samen beslissen. Voor lessen die zonder factuur betaald zijn, zet Claude na
   akkoord een definitieve factuur klaar (`producten`, `relatie`, `factuur`); Martijn accepteert in
   Acumulus de match.
4. Bekende betalers staan in `data/betalers-white-sun.json`, de facturen in
   `data/facturen/white-sun/`.

## Soorten transacties

- **Betaling van een inkoopfactuur** (afschrijving, bedrag en leverancier gelijk aan een
  onbetaalde inkoopfactuur op Knab): Acumulus vindt de match zelf als je op de mutatie klikt.
  Met de verwerklink staat de factuur in één klik op betaald, op de juiste datum. Martijn doet dit
  zelf in Acumulus; Claude bevestigt alleen de match.
- **Betaling van een les zonder factuur** (iDEAL/Wero via KNAB, omschrijving als "les Jaartraject
  van …", "les buiten van …", of een directe overboeking zoals "… proefles"): het bedrag past bij
  een standaard product, bijv. 5,00 = *Qigong | les buiten - abonnement* (voor wie een abonnement
  heeft, zoals het jaartraject), 15,00 = *Qigong | les buiten*, 10,00 = *Qigong | Proefles*. Zondag
  is de buitenles. Martijn maakte hiervoor met de hand een factuur vanuit de relatie: omschrijving
  "Qigong", het product als regel, factuurdatum vandaag, niet betaald. Daarna vindt Acumulus bij
  de mutatie de match en klikt hij op verwerken.
  Nieuw (2026-11-22): Claude zet de facturen klaar via de API, meteen definitief, na akkoord op
  een tabel met relatie, product en bedrag. Martijn accepteert daarna alleen de matches.
  Factuurgegevens: sjabloon White Sun Qigong (133249), kostenplaats Algemeen (10213), rekening Knab
  (227201). Een regel kan in de API niet naar een standaard product verwijzen: omschrijving, prijs
  exclusief btw en btw worden uit `picklist_products` overgenomen.

- **Uitbetaling van Mollie** (bijschrijving van Stichting Mollie Payments, omschrijving "REF
  T…"): een interne overboeking van rekening Mollie (227282) naar Knab. Martijn klikt op de
  mutatie, kiest "interne overboeking" en de vanafrekening Mollie. Er hoeft niets klaargezet te
  worden. De Membirds-facturen die via Mollie worden betaald, staan op rekening Mollie en horen
  niet bij deze verwerking.

## Logboek

### 2026-11-22: overzicht 16-11-2026 t/m 22-11-2026

Negen transacties. Openstaand op dat moment: 7 verkoopfacturen (5 op rekening Mollie voor
Membirds-bestellingen, 1 op Knab voor Stichting Woonin en 1 op Mollie voor Nelette Brouwer)
en 3 inkoopfacturen (Brand it Up 419,87, Centrum voor Zijn 193,60, The Crimson Cricket 18,54).

| # | Datum | Bedrag | Tegenpartij | Omschrijving | Beslissing |
|---|---|---|---|---|---|
| 1 | 16-11 | -193,60 | Centrum voor Zijn | RF9055TAH3SS | Betaling inkoopfactuur 63605862 (huur cursusruimte oktober); Martijn verwerkt via de verwerklink |
| 2 | 16-11 | +5,00 | KNAB (iDEAL/Wero) | les Jaartraject van Hr MJJ Gauthier | Factuur 20260315 gemaakt door Claude (definitief, niet betaald); Martijn heeft de match geaccepteerd |
| 3 | 16-11 | +5,00 | KNAB (iDEAL/Wero) | les Jaartraject van Mw HE Tollenaar | Factuur 20260317 gemaakt door Claude (definitief, niet betaald); Martijn heeft de match geaccepteerd |
| 4 | 16-11 | +15,00 | KNAB (iDEAL/Wero) | les buiten van P.A.J. de Korte e/o I. de Korte-Grundlehner | Factuur 20260313 gemaakt door Claude (definitief, niet betaald); Martijn heeft de match geaccepteerd |
| 5 | 16-11 | +5,00 | KNAB (iDEAL/Wero) | les Jaartraject van T.M. de Vaal | Factuur 20260314 gemaakt door Claude (definitief, niet betaald); Martijn heeft de match geaccepteerd |
| 6 | 16-11 | +5,00 | KNAB (iDEAL/Wero) | les Jaartraject van B OTT | Factuur 20260316 gemaakt door Claude (definitief, niet betaald); Martijn heeft de match geaccepteerd |
| 7 | 16-11 | +15,00 | KNAB (iDEAL/Wero) | les buiten van SM Van Ipkens | Factuur 20260318 gemaakt door Claude (definitief, niet betaald); Martijn heeft de match geaccepteerd |
| 8 | 17-11 | +10,00 | J.L.M. Ulrich e/o A.R. van Korlaar | Leonne proefles | Nieuwe relatie Leonne van Korlaar (11170681, geen e-mail); factuur 20260319 gemaakt door Claude |
| 9 | 18-11 | +41,87 | Stichting Mollie Payments | REF T19287849.2611.02, T19287849.2611.0 | Interne overboeking Mollie naar Knab; Martijn boekt die zelf vanuit de mutatie |
