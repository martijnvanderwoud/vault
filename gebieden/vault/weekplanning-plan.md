---
description: Plan voor een weekplanning die elke zondag uit trainingsschema, agenda en urenstand wordt gemaakt, en tijdens de week opnieuw door te rekenen is
tags: [weekplanning, hardlopen, uren, plan]
---

# Plan: weekplanning

Doel: elke week 28 uur declarabel, alle hardlooptrainingen gedaan en een beetje lucht over, met
afspraken en klusjes tussendoor. Op zondag, tijdens de weekly review, maakt `/weekplanning` de
planning voor de komende week. Mijn handwerk is alleen nakijken en zeggen wat er moet schuiven.
Tijdens de week reken ik een wijziging ("later opgestaan", "run duurde 20 min langer") snel door.

Vervangt het vaste weekschema in de Excel (`weekschema-Two-Rivers-general-phase.xlsx`, buiten de
vault; inhoud in `data/weekschema-excel-2026-11.csv`), dat per weekdag vastligt en niet meeschuift als de trainingsdagen wisselen. Komt uit het interview,
zie [[interview-voortgang]].

Vastgelegd op 2026-11-15.

## Zo werken we dit af

Elke stap is één losse sessie. Start in `~/vault` en zeg: "Doe de eerste open stap uit
[[weekplanning-plan]]". Aan het eind van de sessie:

- vink je de stap af in de voortgang hieronder
- zet je onder `Bevindingen` wat afweek van het plan of wat een latere stap verandert
- pas je latere stappen aan als dat nodig is

## Voortgang

- [x] 1. Tempo's en trainingsduur (15-11, aannames nog te bevestigen)
- [x] 2. Soorten dagen en regels als data (15-11, aannames bevestigd)
- [x] 3. Weekplanning doorrekenen (15-11, met de trainingen van week 1; week 2 nog invoeren)
- [ ] 4. Skill `/weekplanning` voor zondag
- [ ] 5. Herplannen tijdens de week
- [ ] 6. Gelopen trainingen importeren
- [ ] 7. Workouts voor TrainingPeaks genereren
- [ ] 8. Target per dag uit de weekplanning in `uren.py`

## Uitgangspunten

- **Doel per week:** 28 u declarabel (ma 6,5 / di 5,5 / wo 6 / do 6 / vr 4 als startpunt, zie
  [[urenregistratie]]). Uren mogen binnen de week schuiven tussen dagen.
- **Hardlopen gaat altijd door.** Nooit opofferen.
- **Lucht: 30 min per werkdag blijft in het schema.** Loop ik achter, dan haal ik er werk mee in;
  zo niet, dan stop ik met werken en begin ik aan inbox en kleine taken. Het is de buffer voor
  dingen als de auto naar de garage.
- **Wat als eerste wijkt** bij een afspraak of tekort: lucht, dan de stabiliteitsroutines
  (pedestal & hip stability). Later opstaan op advies van de Garmin sleepcoach hangt af van voor of
  achter op target.
- **Voor of achter op target** = "vrij na reservering" uit `uren.py`, zie [[urenregistratie]].
- **Easy run:** vroeg lopen, een banaan is genoeg, daarna stabiliteitsroutines, ontbijt en werken.
- **Zware of lange training:** eerst ontbijten, 2 tot 3 uur later lopen.
- **Kracht:** twee keer per week, op de workout-dagen (nu di en zo), niet direct na de training.
  Eerst lunchen en de lunch laten zakken. Kracht op di 17-11 vervalt (last van de rechterknie).
- **Rolling hills:** eens in de twee weken op de lange loop, bij het Doornse Gat, met reistijd.
- **Weekend:** nooit werkuren. Zaterdag vrij, wandelen met Franca. Zondag geen tijdsindeling,
  alleen de training en de weekly review.
- **Trainingsschema:** *Marathon Excellence for Everyone* (John Davis), plan Wind. Ik zet het zelf
  in TrainingPeaks; Nils (Loopwijzer) geeft feedback en helpt met aanpassingen.
- **Dagen een plek naar voren:** de lange loop van zaterdag doe ik op vrijdag, zodat zaterdag vrij
  is. Boek di → ma, wo → di, do → wo, vr → do, za → vr, zo (off) → za, en ma → de zondag aan het eind
  van de week.

## Beslissingen

- **Geen interne API van TrainingPeaks.** Automatiseren via de interne API, een browser of
  Playwright is verboden door de Terms of Use (zie de backlog in [[vault-roadmap]]). Bron voor de
  trainingen is een foto van de weekpagina uit het boek, of een screenshot van TrainingPeaks als
  Nils iets heeft aangepast.
- **Duur uit tempo's, niet uit TrainingPeaks.** Per onderdeel afstand of tijd × tempo, in een
  script. Tempo's als percentage van het 5K-tempo zijn **percentages van tempo, niet van
  snelheid**: doeltempo = 5K-tempo × (2 − p). Bij 3:45/km is 80% dus 4:30/km, niet 4:41/km. Bron:
  https://apps.runningwritings.com/pace-percent/
- **Planning per soort dag, niet per weekdag.** Een week is een toewijzing van soorten dagen aan
  weekdagen, met de afspraken uit de agenda erbovenop. Zo schuift alles mee als het schema de
  zware training naar een andere dag zet.

## Stappen

### 1. Tempo's en trainingsduur

- `data/hardlopen/tempos.json`: 5K-tempo (nu 3:45/km) en de zones als percentage van 5K-tempo:
  very easy 40–50% (boek: onder 50%), easy 50–60%, moderate 60–75%. Jog tussen herhalingen en
  herstel tussen strides op very easy. Strides 20 s, de eerste op 95%, de laatste op 110%,
  lineair oplopend.
- Wind 90. Bij een bandbreedte in km altijd de ondergrens; het weekdoel in km is de richtlijn.
- `data/hardlopen/trainingen/<week>.json`: de trainingen van een week, per onderdeel.
- Script dat per training de duur uitrekent.

Klaar als: de duur van elke training uit Wind week 1 uit het script komt.

### 2. Soorten dagen en regels als data

Easy-dag, zware dag, lange dag, lange dag met heuvels, rustdag, met hun blokken en duur, en de
regels uit Uitgangspunten. Basis: `data/weekschema-excel-2026-11.csv`, de inhoud van de Excel
(dag, begintijd, activiteit, werkduur; de dubbele lunch op donderdag weggelaten, 28,0 u werk).

Klaar als: de huidige week uit de Excel uit de data is terug te rekenen, met dezelfde werkuren.

### 3. Weekplanning doorrekenen

Script: trainingsweek + afspraken + urenstand → planning per dag met werkuren, weektotaal tegen
28 u, lucht die overblijft en conflicten. Bouwt voort op `scripts/weekplanning.py` (stap 2): de
duur van het blok `Hardlopen` komt uit `trainingsduur.py`, de soort dag per weekdag uit de
trainingsweek in plaats van `excel_week`, en afspraken en wijkregels (`wijkt_eerst`) komen erbij.

Klaar als: de week van 23-11 (ortho-nacontrole ma 9:45–10:15) een kloppende planning geeft.

### 4. Skill `/weekplanning` voor zondag

Haalt agenda's (privé en zakelijk) en urenstand zelf op, vraagt om de foto of screenshot van de
trainingen en schrijft de planning in de vault.

Schrijft per week `data/weekplanning/weken/<maandag>.json` (trainingsweek, afspraken met reistijd
en omschakelen, `vrij_na_reservering_uren` uit `uren.py`) en draait `scripts/weekplanning.py` erop.
Bij een nieuwe trainingsweek: per training een `dagsoort` invullen. In `weken/2026-11-23.json`
week 1 vervangen door `wind-90-week-02.json`.

Klaar als: ik op zondag 22-11 met de skill de week plan zonder zelf iets uit te rekenen.

### 5. Herplannen tijdens de week

"Later opgestaan", "run duurde langer", "afspraak erbij": rest van de dag en week opnieuw.
Nog niet in stap 3: afspraken die niet in een werkblok vallen (in de avond, tijdens de training of
over de lucht heen) geven alleen een conflict, en later opstaan bij voor op target zit er nog niet in.

Klaar als: een wijziging midden in de week een bijgewerkte planning geeft.

### 6. Gelopen trainingen importeren

Ik exporteer mijn activiteitenlijst met de hand uit Garmin Connect (CSV) naar `inbox/`; een script
zet de gelopen trainingen in `data/hardlopen/gelopen.csv`, zonder dubbele regels bij opnieuw
importeren. Daarmee: gepland tegenover gelopen per training en per week, km tegenover het weekdoel,
en de werkelijke duur van trainingen op gevoel (Kenyan-style progression) om de planning bij te
stellen. Geen automatische login bij Garmin of TrainingPeaks via een onofficiële bibliotheek,
alleen exports die ik zelf maak. Eén keer per week, in de weekly review, is genoeg; dagelijks mag.

Eerst: een export van week 47 bekijken om te zien welke kolommen erin zitten.

Klaar als: de gelopen trainingen van week 47 in de vault staan en `/weekplanning` ze naast de
planning zet.

### 7. Workouts voor TrainingPeaks genereren

Als mijn geschatte 5K-tempo verandert, moet ik nu alle workouts in TrainingPeaks met de hand
omzetten. Twee routes:

- **Importeren (voorkeur):** tijdens de weekplanning maakt een script `.zwo`-bestanden met de tempo's
  uit `tempos.json`. TrainingPeaks importeert `.zwo` (en alleen dat) in de Workout Library, ook
  meerdere tegelijk; daarna sleep ik ze naar de dag. FIT op de kalender slepen werkt volgens
  gebruikers niet. Officiële importfunctie, dus binnen de Terms of Use.
- **Alternatief, eerst met Nils bespreken:** workouts als percentage van drempeltempo, dan schalen
  ze mee als ik de drempel aanpas. Valkuil: TrainingPeaks rekent percentages om naar snelheid,
  Davis gebruikt percentages van tempo (80% tempo ≈ 83% snelheid); het script kan dat per zone
  omrekenen. Nadeel: mijn 5K-tempo als drempel verstoort TSS, fitness en fatigue.

Eerst: één workout als `.zwo` genereren en importeren, kijken of de tempo's van een hardloopworkout
goed overkomen.

Klaar als: ik na een nieuwe 5K-schatting de workouts van een week importeer in plaats van ze met de
hand om te zetten.

Bronnen: https://help.trainingpeaks.com/hc/en-us/articles/115000325647 (import),
https://forum.intervals.icu/t/training-peaks-does-not-import-exported-workout-fit/47143 (FIT),
https://help.trainingpeaks.com/hc/en-us/articles/231472468-TrainingPeaks-Athlete-User-Guide (drempel).

### 8. Target per dag uit de weekplanning in `uren.py`

Nu rekent `uren.py` het target met vaste werkuren per weekdag (`WEEKSCHEMAS`: ma 6,5 / di 5,5 /
wo 6 / do 6 / vr 4). Met de weekplanning schuiven uren binnen de week, dus klopt de stand halverwege
een week niet met de planning. Het target per dag moet dan komen uit de geplande werkuren van die dag,
voor weken met een weekbestand; voor andere weken blijft het vaste schema. Daarvoor schrijft
`weekplanning.py` de werkuren per datum weg (bv. `data/weekplanning/werkuren.csv`: datum, gepland),
en leest `uren.py` die.

**Besloten (15-11):** het weektarget blijft altijd 28 u. Komt een week onder de 28 u uit omdat Martijn
voor lag, dan slinkt de voorsprong (vrij na reservering); het target zakt niet. Doel: aan het eind
van het jaar grofweg 45 × 28 = 1260 u declarabel (52 weken min 7 weken vrij-budget, zie
[[urenregistratie]]). Het target per dag volgt dus de verdeling van de planning, maar telt per week op
tot 28 u: werk dat van de voorsprong afging (`minder`), telt op die dag wel mee in het target.

Klaar als: `uren.py` voor de week van 16-11 het target per dag uit de planning haalt.

## Bevindingen

- **Stap 1 (15-11):** `scripts/trainingsduur.py` rekent per training km en duur. De planning
  gebruikt het **midden van de bandbreedte**; de langzame en snelle kant staan ernaast. Opbouw zoals
  Martijn het in TrainingPeaks zet: progressive warm-up = 1 km very easy, 1 km easy, 0,5 km moderate;
  "easy progressing to moderate" = eerste helft easy, tweede helft moderate; strides midden in een
  easy run (8 km = 6 km easy, strides, 0,7 km easy); duur van strides per training, want niet altijd
  20 s; herstel van 1 min very easy **na elke** stride en een jog **na elke** herhaling (8 × 2 min
  heeft 8 jogs), zo werkt TrainingPeaks; Kenyan-style progression = 10 km oplopend van 1% naar 95%,
  dan 2 km easy.
- **Vergeleken met TrainingPeaks (week 1):** ma 43:06 en di 57:57 gelijk (TP 43:06, 57:58); wo, do
  en vr binnen 15 s.
- **Kenyan-style progression** (boek p. 38–39): loop je zonder horloge, op gevoel, dus de duur is
  een schatting. Model naar het boek: 3,5 km very easy → easy, 1,5 km easy → 80–85% (week 1: op de
  helft), 3 km op 80–85%, laatste 2 km naar 92–95%, dan 2 km easy cool-down. Geeft 59:34 (midden),
  TP 1:01:56 met een simpele helling van 1% naar 95%. Op zondag staan geen werkuren, dus een paar
  minuten verschil raakt de planning niet. Na de run: werkelijke duur uit Garmin vergelijken.
- **Trainingsweek loopt ma t/m zo:** de maandagtraining van het boek komt aan het eind, op zondag.
  Week 1 begint ma 16-11; de eerste Kenyan-style progression is zo 22-11.
- **Stap 2 (15-11):** `data/weekplanning/` met `dagsoorten.json` (blokken per soort dag),
  `weekdagen.json` (werkdoel, klusjes en avond per weekdag) en `regels.json` (de Uitgangspunten,
  plus `excel_week`: de toewijzing uit de Excel). `scripts/weekplanning.py --controleer` bouwt de
  week op en vergelijkt met de CSV: alle begintijden, activiteiten en werkuren gelijk, 28,0 u.
- **Wat aan de weekdag vastzit, niet aan de soort dag:** het werkdoel, de klusjes overdag (bakker op
  ma, was op wo/do/vr) en de hele avond (Week(end) bespreken op wo, Ellie bellen op vr). De
  werkblokken rekenen zich uit: `vul` tot een vaste tijd (lunch om 12:00), een vast aantal uren
  (voor de training op zware en lange dagen), of `rest` van het werkdoel. Zo schuiven de uren mee
  als de soort dag wisselt.
- **Aannames, bevestigd op 15-11:** de soort dag `lang` (lange loop zonder heuvels) staat niet in de
  Excel; nu als `lang_heuvels` zonder reistijd, vanaf huis, met warming-up en gewone lunch. `rust`
  en `weekend_training` (zo: training, kracht, weekly review) hebben geen tijdsindeling. De
  duur van `Hardlopen` in de dagsoorten is die uit de Excel (easy 60, zwaar 75, lang 150 min,
  inclusief speling); stap 3 vervangt die door de berekende duur.
- **Open voor stap 3 (opgelost in stap 3):** wat er met de klusjes en de avond gebeurt als een soort dag op een andere
  weekdag valt (bv. een zware dag op wo met de was), en of het werkblok vóór een zware training
  vast 1 u blijft of volgt uit "2 tot 3 uur na het ontbijt".
- **Stap 3 (15-11):** `scripts/weekplanning.py data/weekplanning/weken/<maandag>.json` rekent de
  week door; zonder argument bouwt het de Excel-week op (`--controleer` is nog gelijk). De soort dag
  komt uit een nieuw veld `dagsoort` per training in de trainingsweek; dagen zonder training zijn
  `rust`. Duur van `Hardlopen` = berekende duur (midden) naar boven op een kwartier: easy 45 min
  (Excel 60), zwaar 60 (Excel 75), lang 1:45 (Excel 2:30). De werkdagen worden daardoor korter, de
  werkuren blijven gelijk.
- **Zware dag:** het werkblok vóór de training is `vul`; `Hardlopen` heeft `minstens_na` 120 min na
  het ontbijt. Geeft nu 1 u, zoals de Excel, en schuift mee als er iets tussenkomt.
- **Klusjes en avond** blijven aan de weekdag vast, ook bij een andere soort dag. Ontbreekt het blok
  waar een klusje aan vastzit (bv. `Lunch` op een lange dag met heuvels heet `Tweede lunch`), dan
  komt het klusje voor de lucht, met een melding.
- **Afspraken** krijgen reistijd en omschakelen ervoor en erna (ortho: 10 + 10 min) en knippen het
  werkblok waar ze in vallen; de werkdag loopt dan uit. Past een afspraak niet in een werkblok, dan
  vallen eerst de blokken uit `wijkt_eerst` na de lucht weg (de stabiliteitsroutines) en probeert het
  script het opnieuw. Wat de dag uitloopt gaat van de eigen lucht af, dan vervallen de
  stabiliteitsroutines, dan gaat het naar de lucht van de andere werkdagen (eerst de latere).
- **Week van 23-11:** ortho om 9:25–10:35 met reistijd valt over douchen en ontbijt; de
  stabiliteitsroutines vervallen, de ochtend is 45 min eerder klaar, maandag houdt 5 min lucht,
  week 28,0 u, lucht 2:05. Getest met de trainingen van week 1.
- **Urenstand** wordt alleen gemeld (voor of achter, en wat de lucht dan is); nog niet gebruikt om
  later op te staan.
- **Eerste echte week, 16-11 (15-11):** gepland met `weken/2026-11-16.json` (Wind week 1, agenda's
  privé en zakelijk, urenstand +1,10 u). Nieuw in het script: avondafspraken komen op hun eigen tijd
  tussen de avondblokken, en wat ervoor niet meer af is komt erna; Week(end) bespreken (18:30) en Ellie
  bellen (17:30) liggen met `om` vast in `weekdagen.json`, met `Vrij` in het gat ervoor; klusjes met
  een vaste tijd knippen het werkblok vóór het opbouwen in plaats van achteraf (anders schoof een
  vaste avondtijd mee); `vervalt` in het weekbestand haalt blokken van een soort weg (kracht op
  di 17-11). Afspraken op een dag zonder tijdsindeling (zo) worden alleen gemeld.
- **Eten** ligt vast om 18:00 (`om` met `speling_min` 30: tot 18:30 geen conflict); een korte dag
  geeft vrije tijd voor het eten. Avondblokken die niet meer voor een avondafspraak af zijn, gaan eerst
  naar een vrij gat voor een vast blok, anders erna. Een afspraak kan een andere terugreis hebben
  (`reistijd_terug_min`), en `aanpassen` in het weekbestand wijzigt een blok voor één dag (di 17-11:
  eten zonder afwas, die doet Franca).
- **Reistijd** zoekt Claude niet zelf op (9292 en Google Maps laden het reisadvies via JavaScript):
  Martijn maakt een screenshot van Google Maps, met de aankomsttijd ingesteld. Heen telt vanaf het
  vertrek van huis tot het begin van de afspraak, wachten meegerekend.
- **Bedtijd:** Martijn staat om 6:00 op en ligt meestal om 21:50 in bed (`naar_bed` in `regels.json`).
  Elke dag eindigt met `Naar bed` om 21:50. Na een avondafspraak geen downtime maar klaarmaken voor
  bed en dan naar bed, ook als dat later is.
- **Na een late avond:** na een avondafspraak eerst een halfuur klaarmaken voor bed
  (`klaarmaken_voor_bed_min`). Elk begonnen kwartier later in bed dan 21:50 is de volgende dag een
  kwartier later opstaan; het script rekent dat uit (`opstaan` in het weekbestand alleen voor een
  zelf gekozen tijd). Later opstaan laat de dag uitlopen; dat gaat zoals bij een afspraak eerst van
  de vrije tijd voor het eten, dan van de lucht, dan vervallen de stabiliteitsroutines. Di 17-11 om
  22:44 in bed, dus wo 18-11 op om 7:00: stabiliteitsroutines vervallen, lucht blijft 30 min.
- **Leesbare weergave:** `weekplanning.py <weekbestand> --schrijf` schrijft de planning als notitie
  naar `gebieden/weekplanning/<maandag>.md`: een overzicht van de week (soort dag, training, opstaan,
  werk, lucht) en per dag een tabel met tijden, plus de meldingen. Gegenereerd, niet met de hand
  bewerken. De skill (stap 4) draait altijd met `--schrijf`.
- **Afspraak thuis** (`"thuis": true`, zoals M❤️F met Franca): geen reistijd, geen klaarmaken voor bed
  erna, en op de normale tijd naar bed, ook als de agenda tot later loopt.
- **Voorsprong op target:** ligt Martijn voor (`vrij_na_reservering_uren` > 0), dan gaat wat een dag
  uitloopt eerst van het werk af, tot de voorsprong op is; lucht en stabiliteitsroutines blijven dan
  staan. Daarna gelden de gewone wijkregels. Wo 18-11: 45 min minder werk, week 27:15 bij 1:06
  voorsprong.
