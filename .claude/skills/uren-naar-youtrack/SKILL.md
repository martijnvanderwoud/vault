---
name: uren-naar-youtrack
description: Neemt mijn uren van een dag over uit LogMyTime naar work items op de bijbehorende YouTrack-issues - per issue de totale tijd van die dag, idempotent, dus opnieuw draaien boekt niets dubbel. Gebruik deze skill zodra ik vraag om de uren naar YouTrack over te zetten, te boeken, te loggen of te synchroniseren, of om de uren van vandaag of een andere dag op de issues te zetten, ook als ik het woord skill niet gebruik. Niet voor de urenstand (dat is /uren) en niet voor het corrigeren van uren in LogMyTime zelf.
allowed-tools: Bash(/usr/bin/python3 -I ~/vault/scripts/uren_naar_youtrack.py*)
---

# Uren naar YouTrack

Zet de tijden van één dag uit LogMyTime om naar work items in YouTrack via
`scripts/uren_naar_youtrack.py`. Achtergrond staat in `gebieden/werk/urenregistratie.md`.

## Uitvoeren

1. Toon eerst het plan (wijzigt niets):

   ```bash
   /usr/bin/python3 -I ~/vault/scripts/uren_naar_youtrack.py
   ```

   Standaard vandaag. Noem ik een dag ("gisteren", "maandag", "10 november"), geef dan
   `--dag JJJJ-MM-DD` mee (jaar is het huidige jaar, tenzij ik een ander noem).

2. Geef het plan kort weer en vraag of het door mag. Staan alle regels op `ok`, dan is er
   niets te doen: zeg dat en stop.
3. Na mijn akkoord, dezelfde opdracht met `--uitvoeren`.

## Wat het script doet

- Het issue-ID staat vooraan in de taaknaam in LogMyTime (`PKP-890 …`). Per issue telt het
  de tijd van die dag op, zonder af te ronden.
- Per issue en dag hoort er in YouTrack één work item van mij te staan met die duur. Het
  script maakt het aan, werkt de duur bij als die afwijkt (LogMyTime is de bron) of laat het
  staan als het al klopt. Opnieuw draaien is dus veilig, ook als ik daarna nog uren heb bijgelogd.
- Het verwijdert nooit iets.

## Meldingen

Deze regels altijd aan mij doorgeven, het script slaat ze over:

- `GEEN ISSUE`: taak zonder issue-ID vooraan. Noem de taaknaam en de tijd.
- `OVERSLAAN`: meerdere work items op een issue die samen niet kloppen. Ik los het zelf op.
- `ALLEEN YT`: work item in YouTrack zonder uren in LogMyTime op die dag.
- `FOUT`: meld de HTTP-fout letterlijk, bijvoorbeeld een issue dat niet bestaat.

## Regels

- Tijden komen uit de output van het script. Reken nooit zelf.
- Het script leest de sleutels zelf uit `.env`; lees `.env` niet en roep de API's niet
  zelf aan.
- LogMyTime-limiet: 500 requests per 24 uur, het script gebruikt er 2 per run. Draai het
  niet vaker dan nodig.
- Een lopende stopwatch telt nog niet mee. Loopt er nog een, dan neemt een volgende run
  die tijd vanzelf mee.
