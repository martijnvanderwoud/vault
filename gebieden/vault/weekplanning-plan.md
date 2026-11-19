---
description: Plan voor een weekplanning die elke zondag uit trainingsschema, agenda en urenstand wordt gemaakt, en tijdens de week opnieuw door te rekenen is
tags: [weekplanning, hardlopen, uren, plan]
---

# Plan: weekplanning

Doel: elke week het weektarget declarabel (gemiddeld 28 uur), alle hardlooptrainingen gedaan en
wat ruimte over, met afspraken en klusjes tussendoor. Op zondag, tijdens de weekly review, maakt `/weekplanning` de
planning voor de komende week. Mijn handwerk is alleen nakijken en zeggen wat er moet schuiven.
Tijdens de week reken ik een wijziging ("later opgestaan", "run duurde 20 min langer") snel door.

Vervangt het vaste weekschema in de Excel (`weekschema-Two-Rivers-general-phase.xlsx`, buiten de
vault; inhoud in `data/weekschema-excel-2026-11.csv`), dat per weekdag vastligt en niet meeschuift als de trainingsdagen wisselen. Komt uit het interview,
zie [[interview-voortgang]].

Vastgelegd op 2026-11-15. Herzien op 2026-11-19: een weektarget dat op zondag wordt vastgezet uit
een weekgebaseerd jaar, en ruimte in plaats van lucht (zie Beslissingen en stap 7 t/m 9).

## Zo werken we dit af

Elke stap is één losse sessie. Start in `~/vault` en zeg: "Doe de eerste open stap uit
[[weekplanning-plan]]". Aan het eind van de sessie:

- vink je de stap af in de voortgang hieronder (de stappen staan in de volgorde van uitvoeren)
- zet je onder `Bevindingen` wat afweek van het plan of wat een latere stap verandert
- pas je latere stappen aan als dat nodig is

## Voortgang

- [x] 1. Tempo's en trainingsduur (15-11, aannames nog te bevestigen)
- [x] 2. Soorten dagen en regels als data (15-11, aannames bevestigd)
- [x] 3. Weekplanning doorrekenen (15-11, met de trainingen van week 1; week 2 nog invoeren)
- [x] 4. Skill `/weekplanning` voor zondag (15-11 gebouwd en proefgedraaid; de eerste echte run op zo 22-11 komt onder Bevindingen)
- [x] 5. Herplannen tijdens de week (15-11, getest op proefweken)
- [x] 6. Target per dag uit de weekplanning in `uren.py` (15-11; vervalt met stap 8 en 9)
- [ ] 7. Vrije dagen met datum (herzien 19-11; klaar voor zo 20-12)
- [ ] 8. Weektarget uit het weekgebaseerde jaar in `uren.py` (na stap 7)
- [ ] 9. Weektarget en ruimte in de weekplanning (na stap 8)

Tot stap 9 klaar is, werkt de weekplanning nog op de oude manier (28 u per week, lucht, voor of achter
uit "vrij na reservering").

Gelopen trainingen importeren en workouts voor TrainingPeaks genereren (eerst stap 10 en 11) staan
sinds 19-11 in [[hardlopen-plan]].

## Uitgangspunten

- **Doel per week:** het weektarget, op zondag vastgezet (zie Beslissingen), min 5,6 u per vrije dag
  in die week. Uren mogen binnen de week schuiven tussen dagen.
- **Hardlopen gaat altijd door.** Nooit opofferen.
- **Ruimte:** wat er op een werkdag overblijft tot het eten, nadat het werk is ingepland. Het werk
  wordt zo over de week verdeeld dat de ruimte per werkdag gelijk is (minimaal 0). Geen vaste
  ondergrens: zie ik geen ruimte meer in de week, dan weet ik dat ik iets moet schrappen of aanpassen.
  Vervangt de vaste 30 min lucht per werkdag.
- **Wat als eerste wijkt** bij een afspraak, een dag die uitloopt of later opstaan (bv. op advies van
  de Garmin sleepcoach): de ruimte, tot 0, dan de stabiliteitsroutines (pedestal & hip stability).
  Werk schuift in de planning nooit door naar volgende week. Past het dan nog niet, dan is het een
  conflict en pas ik het plan zelf aan.
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
- **Weekgebaseerd jaar (19-11).** Het jaar volgt de ISO-weken, niet de kalender. Jaardoel = aantal
  weken × 28 − 196 (vrij-budget). 2026 begint als overgang bij week 2 (ma 5-1) en loopt tot en met
  week 53 (zo 3-1-2027): 52 weken, jaardoel 1260 u. Wat ik op 1 en 2 januari 2026 werkte, telt niet
  mee. Vanaf 2027 gewoon week 1 tot en met de laatste week. Elk jaar begint met een schone lei.
- **Weektarget, vast op zondag (19-11).** Weektarget = (jaardoel − declarabel tot en met zondag +
  nog gereserveerde vrije uren) / hele weken die nog over zijn. Het blijft de hele week staan en wordt
  opgeslagen; midden in de week opnieuw rekenen zou het met elk gewerkt uur laten verschuiven. Een
  achterstand of voorsprong wordt zo gelijk verdeeld over de rest van het jaar, in plaats van meteen
  ingehaald of opgemaakt. Het mag boven of onder 28 u uitkomen. Wat ik in werkelijkheid meer of minder
  werk (ziek, een dag die anders liep), komt vanzelf in het target van de weken erna; de planning
  schuift het nooit zelf door.
- **Vrije dag = 5,6 u (19-11).** Vaste waarde (28 / 5; halve dag 2,8 u), los van het target en de
  planning, zodat een reservering het target bepaalt en niet andersom. 196 u = 35 dagen. Declarabel
  doel van een week = weektarget − 5,6 u per vrije dag in die week. Niet gereserveerd budget telt
  vanzelf als voorsprong, vrij zonder reservering als minder declarabel; "vrij opgenomen" en "vrij na
  reservering" hoeven niet meer berekend te worden.
- **Ruimte in plaats van lucht (19-11).** Zie Uitgangspunten. Het rollende weektarget is de buffer
  over de weken heen; een vaste buffer per dag is niet meer nodig.
- **Herplannen binnen de week (19-11).** Wat nog over is van het declarabele doel van de week (doel −
  wat ik deze week al werkte), opnieuw verdeeld over de resterende werkdagen, met weer gelijke ruimte
  per dag. Uitloop van één dag wordt zo over de rest van de week uitgesmeerd.
- **Urenoverzicht (19-11).** Bevat: het jaar (declarabel, jaardoel, nog te gaan, nog gereserveerd,
  weken over, weektarget), deze week (weektarget, vrije dagen, declarabel doel, gewerkt, nog te gaan),
  de weken tot nu (target tegenover gewerkt, om te zien of het target week na week oploopt) en de
  vrije dagen met datum. Weg: per klant, per maand, target per dag, vrij opgenomen en vrij na
  reservering. Geen "nog vrij te plannen in dagen": het weektarget zegt genoeg.

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

### 6. Target per dag uit de weekplanning in `uren.py`

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

### 7. Vrije dagen met datum

Herzien op 19-11. De reserveringen in `data/vrije-dagen-2026.csv` hebben geen datum en tellen in
uren, dus de weekplanning weet niet dat een werkdag vrij is, en voorbije reserveringen moet Martijn
met de hand op 0 zetten. In het nieuwe model telt een vrije dag vast 5,6 u (zie Beslissingen), en
tellen alleen de reserveringen die nog komen; voorbije vrije dagen zitten al in het declarabele totaal.

- **`data/vrije-dagen.csv`** (niet meer per kalenderjaar, want week 53 van 2026 loopt door tot
  3-1-2027): `omschrijving`, `datum`, `tot` (optioneel, voor meer dagen) en `half` (optioneel, voor
  een halve dag). Elke werkdag (ma t/m vr) van `datum` t/m `tot` telt als 1 dag = 5,6 u, een halve
  dag als 2,8 u. Voorbije regels zonder datum mogen weg: ze tellen nergens meer mee, en git bewaart
  ze. Datums, bevestigd op 15-11: Dag voor kerst = do 24-12; Kerstvakantie = vr 25-12 en ma 28 t/m
  do 31-12. Dat zijn 6 dagen = 33,6 u (was 34 u: 6 + 28).
- **Nieuwjaarsdag vr 1-1-2027** valt in week 53 van 2026 en komt erbij als gereserveerde vrije dag
  (bevestigd op 19-11; stond er nog niet in, omdat het kalenderjaar op 31-12 ophield). Samen 7 dagen
  = 39,2 u nog gereserveerd.
- **Een functie voor de andere scripts:** vrije dagen in een periode (datum → 1 of 0,5) en de nog
  gereserveerde uren na een peildatum. Stap 8 en 9 gebruiken die.
- **Skill `/uren`:** het onderhoud (voorbije reservering op 0 zetten) vervalt; de verwijzing naar de
  oude CSV gaat eruit.

Klaar als: `data/vrije-dagen.csv` de reserveringen voor de rest van het jaar met datum bevat, en
de functie voor peildatum 2026-11-19 39,2 u en voor peildatum 2026-12-24 (na die dag) 33,6 u nog
gereserveerd geeft.

### 8. Weektarget uit het weekgebaseerde jaar in `uren.py`

`uren.py` gaat over van het kalenderjaar en een target per dag naar het weekgebaseerde jaar en een
weektarget (zie Beslissingen).

- **Stand:** declarabel vanaf het begin van het jaar (2026: ma 5-1), jaardoel (aantal weken × 28 −
  196), nog te gaan, nog gereserveerd (stap 7), hele weken over en het weektarget dat daaruit volgt.
- **Weektarget opslaan:** `data/weekplanning/weektargets.csv`, één regel per week: `maandag`,
  `weektarget`, `vrije_dagen`, `declarabel_doel` (weektarget − 5,6 × vrije dagen). Geschreven op
  zondag (met `--zet-week` of iets dergelijks, met de stand tot en met die zondag), daarna niet meer
  opnieuw berekend. Week 47 (16-11) achteraf met 28 u, de weken daarvoor leeg.
- **Deze week:** het opgeslagen weektarget, de vrije dagen, het declarabele doel, wat ik deze week tot
  en met de peildatum werkte en wat er nog te gaan is. Dit gebruikt het herplannen in stap 9.
- **Urenoverzicht** (`gebieden/werk/uren-overzicht.md`): het jaar, deze week, de weken tot nu
  (target tegenover gewerkt) en de vrije dagen met datum. Per klant, per maand, target per dag, vrij
  opgenomen en vrij na reservering gaan eruit.
- **Weg uit de code:** `WEEKSCHEMAS`, het lezen van `werkuren.csv`, `target_uren`, de berekening
  van vrij opgenomen en de tabel per maand. `--vanaf` moet ook voor datums vóór 2026 werken (liep
  vast op 29-12-2025).
- **Notities en skill:** [[urenregistratie]] (logica en validatiepunten) en de skill `/uren`
  (wat hij meldt) bijwerken.

Klaar als: `uren.py` per peildatum 2026-11-19 een weektarget geeft dat gelijk is aan (1260 −
declarabel sinds 5-1 + nog gereserveerd) / weken over, het weektarget van een week na het opslaan
niet meer verandert, en het overzicht de nieuwe indeling heeft.

### 9. Weektarget en ruimte in de weekplanning

`weekplanning.py` en de skill `/weekplanning` gaan over op het weektarget en de ruimte (zie
Uitgangspunten en Beslissingen). Verwacht: het script wordt flink kleiner.

- **Weekbestand:** het declarabele doel van de week (uit `weektargets.csv`, stap 8) in plaats van
  `vrij_na_reservering_uren`. De skill zet op zondag eerst het weektarget vast en plant daarna.
- **Vrije dagen** (stap 7) in de week krijgen geen werk; een halve dag de helft van de dag.
- **Ruimte gelijk verdelen:** het declarabele doel over de werkdagen zo verdelen dat de ruimte tot het
  eten (of tot het eerste vaste avondblok, zoals Ellie bellen om 17:30) per werkdag gelijk is,
  minimaal 0. Een dag met minder ruimte dan de rest krijgt geen extra werk; het schuift naar de
  ruimere dagen. `werkdoel_uren` per weekdag in `weekdagen.json` vervalt.
- **Wijkregels:** `wijkt_eerst` wordt ruimte, dan stabiliteit. Wat niet past, is een conflict met een
  melding; niets schuift door naar volgende week.
- **Weg:** de lucht (`lucht_min_per_werkdag`, de lucht-blokken in `dagsoorten.json`), `minder` en de
  voorsprong-logica, `achterstand_ingehaald`, `vrij_inzetten`, `lucht_inzetten`, en waarschijnlijk
  `werkuren.csv` (stap 6).
- **Herplannen:** `herplannen: {vanaf, reden}`. Nog te gaan = declarabel doel − wat ik deze week
  werkte tot en met de dag voor `vanaf` (uit `uren.py`, stap 8), opnieuw verdeeld over de resterende
  werkdagen met gelijke ruimte. Voorbije dagen staan in de notitie kort als "voorbij".
- **Notitie per week:** kolom lucht wordt ruimte. Uitgangspunten, skill `/weekplanning` en
  [[urenregistratie]] bijwerken waar ze nog over lucht, voor of achter, of 28 u spreken.

Klaar als: de week van 21-12 een planning geeft met do 24-12 en vr 25-12 vrij, een declarabel doel
van weektarget − 11,2 u en gelijke ruimte op ma t/m wo, en herplannen na een uitgelopen dag de ruimte
van de rest van de week gelijk verlaagt.

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
  Elke dag eindigt met 20 min `Bedroutine` (`bedroutine_min`, van 21:30) en `Naar bed` om 21:50. Na
  een avondafspraak geen downtime maar bijkomen en spullen wegleggen, de bedroutine en dan naar bed,
  ook als dat later is.
- **Na een late avond:** na thuiskomst van een avondafspraak eerst 10 min bijkomen en spullen
  wegleggen (`bijkomen_na_afspraak_min`), dan de bedroutine: 30 min na aankomst in bed. Zoveel later in bed
  dan 21:50, zoveel later opstaan de volgende dag, naar boven afgerond op 5 min (`kleinste_blok_min`;
  tot 17-11 per begonnen kwartier); het script rekent dat uit (`opstaan` in het weekbestand alleen voor een
  zelf gekozen tijd). Later opstaan laat de dag uitlopen; dat gaat zoals bij een afspraak eerst van
  de vrije tijd voor het eten, dan van de lucht, dan vervallen de stabiliteitsroutines. Di 17-11 om
  22:44 in bed, dus wo 18-11 op om 7:00: stabiliteitsroutines vervallen, lucht blijft 30 min.
- **Leesbare weergave:** `weekplanning.py <weekbestand> --schrijf` schrijft de planning als notitie
  naar `gebieden/weekplanning/<maandag>.md`: een overzicht van de week (soort dag, training, opstaan,
  werk, lucht) en per dag een tabel met tijden, plus de meldingen. Gegenereerd, niet met de hand
  bewerken. De skill (stap 4) draait altijd met `--schrijf`.
- **Afspraak thuis** (`"thuis": true`, zoals M❤️F met Franca): geen reistijd, geen bijkomen erna; de
  afspraak loopt hooguit tot de bedroutine (21:30), en dan op de normale tijd naar bed, ook als de
  agenda tot later loopt.
- **Voorsprong op target:** ligt Martijn voor (`vrij_na_reservering_uren` > 0), dan gaat wat een dag
  uitloopt eerst van het werk af, tot de voorsprong op is; lucht en stabiliteitsroutines blijven dan
  staan. Daarna gelden de gewone wijkregels. Wo 18-11: 45 min minder werk, week 27:15 bij 1:06
  voorsprong.
- **Stap 6 (15-11):** `weekplanning.py <weekbestand> --schrijf` zet per datum `gepland_min` en
  `target_min` in `data/weekplanning/werkuren.csv` (regels van andere weken blijven staan). Target =
  gepland + `minder` (van de voorsprong) + werk dat nergens in de lucht paste, dus de week telt altijd
  op tot 28 u; een dag zonder tijdsindeling houdt het werkdoel van de weekdag. `uren.py` neemt het
  target uit dat bestand voor datums die erin staan, anders `WEEKSCHEMAS`. Week van 16-11: ma 6,5 /
  di 5,5 / wo 6 / do 6 / vr 4, gelijk aan het vaste schema, want alleen wo had `minder` (45 min).
  `uren.py --vanaf 2026-11-16`: tot ma 6,50 u, tot wo 18,00 u, tot zo 28,00 u.
- **Stap 4 (15-11):** skill in `.claude/skills/weekplanning/SKILL.md`. Haalt in één keer de urenstand
  (`uren.py` zonder `--schrijf`), de zakelijke agenda (CrimsonCricket en Feestdagen in Nederland)
  en de privé-agenda (Martijn en Auto) op; de agenda's van Franca niet, afspraken samen met haar
  staan in Martijns eigen agenda (bevestigd op 15-11). Ontbreekt de trainingsweek, dan
  vraagt de skill om de foto of screenshot, maakt het trainingsbestand met `dagsoort` en laat de duur
  uit `trainingsduur.py` controleren. Afspraken legt de skill eerst voor (thuis of op locatie,
  reistijd uit een screenshot van Google Maps), dan schrijft hij het weekbestand en draait
  `weekplanning.py --schrijf`. Proefgedraaid op `weken/2026-11-23.json`; week 1 vervangen door
  `wind-90-week-02.json` gebeurt op 22-11 in de skill zelf (stap 2 daarvan: geen trainingsweek met
  `start` 2026-11-23).
- **Nog niet in het script (wordt stap 7):** een feestdag of vrije dag op een werkdag. De skill meldt die en vraagt
  wat er met de werkuren moet; de eerstvolgende is 25-12 (vr).
- **Voor stap 5 (opgelost in stap 5):** herplannen midden in de week met `--schrijf` overschrijft ook het
  target van de dagen die al voorbij zijn. Dat moet dan blijven staan (of uit de gelopen dagen komen),
  anders verschuift de stand van eerdere dagen mee.
- **Stap 5 (15-11), keuzes van Martijn:** wat ik op voorbije dagen echt werkte, telt mee via de urenstand
  (niet via de gelogde uren per dag); herplannen zit in de skill `/weekplanning` (sectie "Herplannen
  tijdens de week"), geen aparte skill; afspraken over de lucht en over de training gaan mee, later
  opstaan bij een voorsprong niet (blijft een zelf gekozen `opstaan`).
- **Herplannen:** `herplannen: {vanaf, vrij_na_reservering_uren, reden}` in het weekbestand, één blok
  (een nieuwe herplanning vervangt het). Urenstand uit `uren.py --tot <dag voor vanaf>`, anders telt
  het target van vandaag al mee. De dagen voor `vanaf` zijn voorbij: hun gepland werk en target komen
  uit `werkuren.csv` en blijven bij `--schrijf` staan; in de notitie staan ze kort als "voorbij". Eerst
  had ik voorbije dagen opnieuw uitgerekend met de oude urenstand, maar dan veranderde het target van
  maandag alsnog als een afspraak later in de week werd afgezegd (werk van vrijdag stond in de lucht van
  maandag). Vanaf `vanaf` rekent het script opnieuw, en de week telt op tot 28 u: werk dat van een
  voorbije dag naar later schoof, gaat weer in de lucht van de rest van de week; werk dat al op een
  voorbije dag stond, gaat eraf bij de laatste werkdagen (minder werkdoel). Vandaag wordt helemaal opnieuw
  doorgerekend, vanaf het opstaan; een aparte "nu"-tijd is niet nodig zolang de ochtend volgens plan liep.
- **Vooraf herplannen** (bv. "morgen later op"): de wijziging voor die dag in het weekbestand (`opstaan`),
  en herplannen altijd vanaf vandaag, met de urenstand tot en met gisteren. Vanaf morgen zou de stand
  tot en met vandaag nodig zijn, en daarin telt het target van vandaag al mee terwijl de uren nog niet
  gelogd zijn.
- **Run duurde langer:** `trainingsduur: [{dag, duur_min, reden}]`. Het einde van de dag (waartegen de
  wijkregels rekenen) komt uit de berekende duur; de werkelijke duur loopt uit zoals later opstaan. Eerst
  rekende het einde mee met de langere run, dan kostte die niets en schoof de avond op (conflict met
  Week(end) bespreken om 18:30).
- **Afspraak over de lucht heen:** een afspraak die in een werkblok begint, mag over de blokken erna heen
  lopen, zolang daar geen blok met een vaste tijd of de training tussen zit; die blokken schuiven op. Een
  afspraak die in de lucht of later begint (bv. 16:30 na het werk), komt tussen de avondblokken en gaat
  zo nodig van de lucht af; begint hij terwijl er nog gewerkt wordt, dan is het een conflict.
- **Te veel werk na een afspraak:** een afspraak laat in het laatste werkblok maakt het stuk ervoor vast
  ('vul' tot de afspraak). Vielen daarna de stabiliteitsroutines weg, dan werd de ochtend langer en
  kwam er meer werk uit dan het werkdoel. Nu gaat het teveel van de laatste 'vul'-blokken af; het gat is
  lucht. Kanttekening: de stabiliteitsroutines (45 min) vervallen ook als de lucht maar 5 min tekort komt,
  zoals de wijkregels zeggen; wat dan overblijft wordt lucht.
- **Afspraak over de training:** past een afspraak ook na het weglaten van de stabiliteitsroutines niet,
  en raakt hij de training, dan schuift de training naar na de afspraak, met het blok ervoor (naar
  buiten, warming-up) en de blokken erna tot het volgende werkblok (uitloop, douchen). Op een zware dag
  komt de lunch om 12:00 dan vaak in conflict (proef: afspraak 9:30, lunch pas om 12:25); dat beslist
  Martijn per geval. Nooit eerder dan gepland: op een zware dag mag lopen niet eerder dan 2 uur na het
  ontbijt.
- **Voor of achter automatisch verwerken (15-11, besloten met Martijn):** "vrij na reservering" is de
  maat, ook over weken heen, omdat Martijn aan het begin van het jaar het hele vrij-budget (196 u)
  reserveert: dan is het 0 bij de start, blijft het 0 bij een vrije dag die gereserveerd was, en meet het
  precies hoeveel hij voor of achter ligt op target min de voorbije vrije uren. Niet gereserveerd budget
  telt als voorsprong; vrij zonder reservering (ziek, spontaan vrij) als achterstand, tenzij het achteraf
  in `vrije-dagen-2026.csv` komt. **Achter:** inhalen vanaf de eerste werkdag
  (sinds 16-11 eerst in de vrije tijd na het werk, dan in de lucht; zie hieronder)
  (`achterstand_ingehaald`, telt niet mee in het target van die dag, want het hoort bij eerdere dagen);
  wat niet past, wordt gemeld en schuift door naar volgende week. **Voor:** eerst minder werk op dagen die
  uitlopen (zoals al), wat dan over is maakt de laatste werkdagen korter, tot het vaste werk van die soort
  dag; lucht en stabiliteitsroutines blijven staan. De lucht is de buffer, niet de voorsprong. Week van
  16-11 (+1,10 u): wo 45 min minder (uitloop), vr 21 min korter. Ook gevonden: een klusje met een vaste
  tijd (vr 15:30 was aanzetten) gaf een conflict op een korte dag; nu staat het na het werk op zijn tijd.
- **Blokken van 5 min (15-11, op verzoek van Martijn):** `kleinste_blok_min` in `regels.json`. Afgerond
  bij de invoer, de rest volgt vanzelf: reistijd plus omschakelen naar boven (Ledig Erf terug 44 → 45 min,
  in bed 22:45), begin van een afspraak naar beneden en einde naar boven, werkelijke trainingsduur naar
  boven, voorsprong naar beneden en achterstand naar boven. Eerste proef: ma 16-11 om 6:20 op (20 min
  later), 15 min van de vrije tijd voor het eten en 5 min minder werk van de voorsprong; vr 15 min korter.
- **Herplannen na meer of minder werken:** dat zit in de urenstand. 's Avonds, als de uren van vandaag
  in LogMyTime staan, mag herplannen vanaf morgen met de stand tot en met vandaag; anders vanaf vandaag.
- **Voor stap 7:** een gereserveerde vrije dag verlaagt het werkdoel van de week; bij herplannen moet de
  berekening van wat de rest van de week nog moet doen (`over` in `week_plannen`) dat werkdoel gebruiken,
  niet vast 28 u.
- **Inhalen eerst in de vrije tijd (16-11, op verzoek van Martijn):** een korte dag met een vast
  avondblok (eten om 18:00, Ellie bellen om 17:30) gaf `Vrij` in het gat ervoor, terwijl inhalen in de
  lucht ging. Dan had hij eerst een halfuur vrij en werkte daarna verder in de lucht; logischer is gewoon
  doorwerken. Nu gaat alle inhalen (achterstand op target, werk van een andere dag, werk van een voorbije
  dag) eerst in de vrije tijd na het werk, in de hele week, en pas als die op is in de lucht. Het script
  plant de dag dan opnieuw met een hoger werkdoel (`vrij_inzetten`), zodat lucht en avondblokken het gat
  in schuiven, en neemt dat alleen als lucht, bedtijd, conflicten en meldingen gelijk blijven. Het
  ingehaalde werk loopt door in het gewone werkblok (geen apart "Werken (inhalen)"). Proef op week 16-11
  met -1,50 u: di 30 min en vr 45 min doorwerken (werk tot 16:15 en 17:00), daarna 15 min lucht op ma;
  eerst ging het naar de lucht van ma t/m do en bleven di en vr vrij. Targets ongewijzigd (week 28 u).
- **Herziening (19-11, gesprek met Martijn):** het urenoverzicht was een kopie van de Excel, met het
  kalenderjaar en voor of achter tegenover een target per dag. Nu: een weekgebaseerd jaar, een
  weektarget dat op zondag wordt vastgezet, vrije dagen van 5,6 u en ruimte in plaats van lucht (zie
  Beslissingen, stap 7 t/m 9). Het weektarget is wiskundig gelijk aan 28 − (vrij na reservering) /
  weken over: het meet hetzelfde, maar verdeelt het verschil over de rest van het jaar. Met het jaar
  vanaf 1 januari (53 weken) lag Martijn 16 u achter, omdat 29 t/m 31-12-2025 dan bij 2026 hoorden;
  daarom begint 2026 bij week 2. Illustratie per 19-11 (niet de echte stand op zondag): declarabel
  sinds 5-1 1127,7 u, nog 132,3 u + 34 u gereserveerd over 6,2 weken = 26,8 u per week. Stap 6 en de
  oude versie van stap 7 (vrije dagen in uren) zijn hierdoor vervangen. Op 19-11 ook de stappen
  opnieuw genummerd in de volgorde van uitvoeren (oud 8 → 6, 9 → 7; 10 en 11 nieuw als 8 en 9); de oude
  stappen 6 en 7 (gelopen trainingen, workouts voor TrainingPeaks) gingen naar [[hardlopen-plan]].
