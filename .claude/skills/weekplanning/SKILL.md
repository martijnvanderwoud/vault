---
name: weekplanning
description: Maakt op zondag mijn weekplanning voor de komende week - haalt de agenda's (privé en zakelijk) en de urenstand op, zet de trainingen van de week uit een foto of screenshot in de vault, schrijft het weekbestand en rekent de planning door met scripts/weekplanning.py. Gebruik deze skill zodra ik vraag om de week te plannen, de weekplanning te maken of bij te werken, of om /weekplanning, ook als ik het woord skill niet gebruik. Niet voor herplannen midden in de week na een wijziging op de dag zelf (dat is stap 5 van het plan) en niet voor de urenstand alleen (dat is /uren).
allowed-tools: Bash(/usr/bin/python3 -I ~/vault/scripts/weekplanning.py*), Bash(/usr/bin/python3 -I ~/vault/scripts/trainingsduur.py*), Bash(/usr/bin/python3 -I ~/vault/scripts/uren.py*)
---

# Weekplanning

Maakt de planning van de komende week (ma t/m zo) en schrijft die naar
`gebieden/weekplanning/<maandag>.md`. Achtergrond, regels en bevindingen:
`gebieden/vault/weekplanning-plan.md`. De rekenregels zitten in `scripts/weekplanning.py`; jij
verzamelt alleen de invoer.

## Regels

- Reken nooit zelf: geen duur, werkuren, lucht of opstaantijd uit het hoofd. Alles komt uit
  `weekplanning.py` en `trainingsduur.py`. Klopt iets niet, pas dan de invoer aan, niet de uitkomst.
- `gebieden/weekplanning/*.md` en `data/weekplanning/werkuren.csv` zijn gegenereerd: niet met de
  hand bewerken.
- Reistijd zoek je niet zelf op (9292 en Google Maps laden het reisadvies via JavaScript). Vraag om
  een screenshot van Google Maps met de aankomsttijd ingesteld. Heen telt vanaf het vertrek van huis
  tot het begin van de afspraak, wachten meegerekend.
- De agenda's zijn alleen-lezen: zet niets in de agenda.

## Uitvoeren

`<maandag>` is de maandag van de komende week (op zondag: morgen), als `JJJJ-MM-DD`. Noem ik een
andere week, neem dan die maandag.

### 1. Ophalen, in één keer

Doe deze drie tegelijk:

- **Urenstand:** `/usr/bin/python3 -I ~/vault/scripts/uren.py` (zonder `--schrijf`). Neem
  "Vrij na reservering" over als `vrij_na_reservering_uren`, precies zoals het script het toont.
- **Zakelijke agenda** via `mcp__claude_ai_Google_Calendar__list_events`, ma 00:00 t/m zo 23:59:
  `martijn@crimsoncricket.nl` en `nl.dutch#holiday@group.v.calendar.google.com` (feestdagen).
- **Privé-agenda** via `mcp__google-prive__get_events` met `detailed: true`:
  `martijnvanderwoud@gmail.com` en de agenda "Auto" (`oau40nsce6ka38eoos2qbe5f50@group.calendar.google.com`).

De agenda's van Franca (privé en White Sun Qigong) haal je niet op; afspraken samen met haar staan
in mijn eigen agenda.

### 2. Trainingen

Kijk of `data/hardlopen/trainingen/` de trainingsweek voor `<maandag>` al heeft (`start` gelijk aan
`<maandag>`). Zo niet: vraag om een foto van de weekpagina uit het boek, of een screenshot van
TrainingPeaks als Nils iets heeft aangepast. Maak dan `wind-90-week-<NN>.json` naar het voorbeeld
van `wind-90-week-01.json`:

- Dagen een plek naar voren: boekdag di → `dag` ma, wo → di, do → wo, vr → do, za → vr, zo (off) →
  za, ma → zo. Zet de boekdag in `boekdag`.
- Bij een bandbreedte in km de ondergrens; `doel_km` is het weekdoel uit het boek.
- Opbouw van de onderdelen zoals in de bevindingen van stap 1 van het plan (progressive warm-up,
  strides midden in een easy run met herstel na elke stride, jog na elke herhaling, "easy progressing
  to moderate" in twee helften, Kenyan-style progression).
- `dagsoort` per training: `easy` (easy run, ook met strides), `zwaar` (herhalingen, tempo,
  workout), `lang_heuvels` (lange loop door rolling hills, met reistijd naar het Doornse Gat), `lang`
  (lange loop zonder heuvels), `weekend_training` (de training op zondag). Dagen zonder training
  worden vanzelf `rust`. Twijfel je over de soort, vraag het.

Draai daarna `/usr/bin/python3 -I ~/vault/scripts/trainingsduur.py data/hardlopen/trainingen/wind-90-week-<NN>.json`
en laat de tabel zien: km, duur en het weekdoel. Vraag of het klopt met wat ik in TrainingPeaks zie.

### 3. Afspraken uitzoeken

Zet alle gevonden agenda-items in één lijst (dag, tijd, titel, agenda, locatie) en deel ze in:

- **Neem mee:** afspraken met een tijd op ma t/m vr, en avondafspraken in de hele week.
- **Laat weg en noem:** wat al vastligt in `data/weekplanning/weekdagen.json` (Week(end) bespreken,
  Ellie bellen), hele-dag-items die geen tijd kosten, en wat duidelijk niet van mij is.
- **Feestdag of vrije dag op een werkdag:** meld het; het script kent nog geen vrije werkdag, dus
  vraag wat er met de werkuren van die dag moet gebeuren.
- **Afspraak op za of zo:** meenemen mag, het script meldt hem alleen (geen tijdsindeling).

Leg de lijst aan mij voor en vraag per afspraak wat ontbreekt:

- Thuis of op locatie? Thuis: `"thuis": true` (geen reistijd, op de normale tijd naar bed).
- Op locatie: reistijd heen en terug uit een screenshot van Google Maps (`reistijd_min`,
  `reistijd_terug_min` als die anders is) en omschakelen (`omschakelen_min`). Staat dezelfde
  afspraak al in een eerder weekbestand in `data/weekplanning/weken/`, stel die waarden dan voor.
- Vervalt er deze week iets (`vervalt`, bv. kracht bij een blessure) of gaat een blok anders
  (`aanpassen`, bv. Franca doet de afwas)? Zelf gekozen opstaantijd (`opstaan`)?

Twijfel je of een item meetelt, vraag het; neem niets aan.

### 4. Weekbestand schrijven

Schrijf `data/weekplanning/weken/<maandag>.json` met de velden zoals in `weken/2026-11-16.json`:
`toelichting` (bronnen, zoals de reistijd uit Google Maps), `maandag`, `trainingen` (bestandsnaam),
`vrij_na_reservering_uren`, `afspraken`, en waar nodig `vervalt`, `aanpassen`, `opstaan`. Bestaat
het bestand al (zoals een voorlopige versie met de trainingen van een andere week), lees het eerst,
neem over wat nog klopt en vervang de rest.

### 5. Doorrekenen

```bash
/usr/bin/python3 -I ~/vault/scripts/weekplanning.py ~/vault/data/weekplanning/weken/<maandag>.json --schrijf
```

Altijd met `--schrijf`: dat zet de notitie in `gebieden/weekplanning/<maandag>.md` en het target per
dag in `data/weekplanning/werkuren.csv` voor `uren.py`. Geeft het script een fout, meld die letterlijk
en zoek de oorzaak in de invoer.

## Antwoord

Kort, in het Nederlands, met getallen uit de output:

- het overzicht per dag (soort dag, training, opstaan, werk, lucht) en het weektotaal tegen 28 u
- de urenstand en wat die betekent (voor of achter op target)
- alle meldingen en conflicten van het script, en wat ik daarvoor moet beslissen
- welke agenda-items je hebt weggelaten

Vraag wat er moet schuiven. Pas bij een wijziging het weekbestand aan en reken opnieuw door, tot ik
tevreden ben. Noem tot slot dat de planning in `gebieden/weekplanning/<maandag>.md` staat.
