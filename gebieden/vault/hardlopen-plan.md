---
description: Plan voor hardloopdata in de vault - gelopen trainingen uit Garmin importeren en workouts voor TrainingPeaks genereren uit de tempo's
tags: [hardlopen, trainingpeaks, garmin, plan]
---

# Plan: hardlopen

Doel: de gelopen trainingen staan in de vault naast wat er gepland was, en als mijn geschatte
5K-tempo verandert, hoef ik de workouts in TrainingPeaks niet meer met de hand om te zetten.

Afgesplitst van [[weekplanning-plan]] op 2026-11-19 (daar stap 10 en 11), omdat het meer met
hardlopen dan met de weekplanning te maken heeft. Bouwt voort op de tempo's en de trainingsduur uit
stap 1 van dat plan (`data/hardlopen/tempos.json`, `scripts/trainingsduur.py`).

## Zo werken we dit af

Elke stap is één losse sessie. Start in `~/vault` en zeg: "Doe de eerste open stap uit
[[hardlopen-plan]]". Aan het eind van de sessie:

- vink je de stap af in de voortgang hieronder (de stappen staan in de volgorde van uitvoeren)
- zet je onder `Bevindingen` wat afweek van het plan of wat een latere stap verandert
- pas je latere stappen aan als dat nodig is

## Voortgang

- [ ] 1. Gelopen trainingen importeren
- [ ] 2. Workouts voor TrainingPeaks genereren

## Uitgangspunten

- **Trainingsschema:** *Marathon Excellence for Everyone* (John Davis), plan Wind. Ik zet het zelf
  in TrainingPeaks; Nils (Loopwijzer) geeft feedback en helpt met aanpassingen.
- **Geen interne API van TrainingPeaks of Garmin.** Automatiseren via een interne API, een
  onofficiële bibliotheek, een browser of Playwright is verboden door de Terms of Use (zie de backlog
  in [[vault-roadmap]]). Alleen exports die ik zelf maak en officiële importfuncties.
- **Tempo's** als percentage van het 5K-tempo zijn percentages van tempo, niet van snelheid (zie
  Beslissingen in [[weekplanning-plan]]).

## Stappen

### 1. Gelopen trainingen importeren

Ik exporteer mijn activiteitenlijst met de hand uit Garmin Connect (CSV) naar `inbox/`; een script
zet de gelopen trainingen in `data/hardlopen/gelopen.csv`, zonder dubbele regels bij opnieuw
importeren. Daarmee: gepland tegenover gelopen per training en per week, km tegenover het weekdoel,
en de werkelijke duur van trainingen op gevoel (Kenyan-style progression) om de planning bij te
stellen. Geen automatische login bij Garmin of TrainingPeaks via een onofficiële bibliotheek,
alleen exports die ik zelf maak. Eén keer per week, in de weekly review, is genoeg; dagelijks mag.

Eerst: een export van week 47 bekijken om te zien welke kolommen erin zitten.

Klaar als: de gelopen trainingen van week 47 in de vault staan en `/weekplanning` ze naast de
planning zet.

### 2. Workouts voor TrainingPeaks genereren

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

## Bevindingen

Nog geen.
