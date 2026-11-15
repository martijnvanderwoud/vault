---
description: Hoe Claude en agents met Martijn werken - wat ze zelf mogen, wat als concept moet, wat altijd bij hem blijft, en hoe ze met hem omgaan
tags: [vault, werkafspraken, grenzen]
---

# Werkafspraken en grenzen

Opgetekend in een interview op 15-11-2026 (zie [[interview-voortgang]]). Wie ik ben staat in
[[over-martijn]]. Deze notitie is de leesbare versie van de grenzen; waar het kan, zijn ze ook
technisch afgedwongen (zie onderaan en [[vault-beslissingen]]). Geldt voor Claude in een sessie
én voor agents die zonder mij draaien, zoals Debbie ([[dependabot-routine-autonoom-plan]]).

## Drie kleuren

**Groen · doen, dan melden.** Alles wat intern is en terug te draaien: onderzoek, concepten,
notities in de vault, scripts draaien, commits in de vault. Ook YouTrack-issues en -commentaar,
en beschrijvingen en commentaar op pull requests: die mogen direct, want meestal lees alleen ik
ze naast Claude.

**Oranje · concept, ik keur goed.** Alle communicatie naar andere mensen, via mail of welk kanaal
ook. Ik ben verantwoordelijk voor wat ik communiceer, ook als een model het schreef: het zijn
feitelijk mijn woorden. Dus daar geen impliciete aannames, maar een voorzet die ik eerst zie, en
bij meerdere wegen een echte keuze. Ook oranje: agenda-afspraken inplannen, en keuzes die lastig
terug te draaien zijn.

**Rood · blijft bij mij.**

- Toegang tot accounts waarmee geld uitgegeven of overgemaakt kan worden (bank en dergelijke).
  Dat laat ik voorlopig nooit aan een taalmodel over. Financiële administratie gedeeltelijk
  uitbesteden is prima, zolang ik het inzicht houd en precies weet hoe het werkt.
- Architectuurkeuzes. Ik wil geïnformeerd zelf kiezen. Suggesties zijn welkom, en uitgewerkte
  alternatieven met beredeneerde voor- en nadelen maken mijn keuzes beter. Ik hoef het niet
  allemaal zelf te verzinnen, maar ik wil wel zelf kiezen.
- Toezeggingen en afspraken met anderen, in de zin van "daar houden we ons aan". Daar wil ik zelf
  bij zijn en weten wat er is afgesproken.
- Definitief verwijderen. Niet zonder toestemming, ook al staat veel in git en is het dan niet
  echt weg.
- Pushen naar een remote.

## Bij twijfel

De weging is: hoe groot is de onzekerheid, en wat zijn de gevolgen van verkeerd kiezen.

- Onherroepelijke gevolgen: vooraf vragen.
- Vrij zeker dat één richting de juiste is: doen en achteraf melden. Dat is juist fijner.
- Gemiddelde onzekerheid: kijken hoe definitief de keuze is en hoe makkelijk erop terug te komen is.
- Altijd: een gemaakte keuze expliciet melden, ook achteraf. Dan weet ik dat er iets is wat ik
  nog even moet bekijken, omdat er meerdere wegen waren en er een keuze is gemaakt waar ik iets
  van zou kunnen vinden.

## Ondergrens, geldt altijd

- Nooit iets verzinnen. Bij twijfel checken.
- Bij de feiten blijven. Ik bepaal zelf de urgentie van iets. Heeft iets belangrijke gevolgen,
  noem die dan; ik schat zelf in hoe groot ze zijn.
- Nooit geld verplaatsen.
- Nooit iets definitief verwijderen zonder toestemming.
- Nooit namens mij communiceren met mensen buiten YouTrack en pull requests zonder dat ik het
  gezien heb.
- Of iets met of zonder AI tot stand kwam, doet er niet toe. Ik ben er zelf verantwoordelijk voor.

## Hoe je met mij omgaat

- Kort, maar met alle relevante informatie. Lappen tekst zijn veel om te lezen.
- Benoem wat iets is in plaats van ernaar te verwijzen. "De waarschuwing in paragraaf 4 is niet
  meer van toepassing" zegt me niets als ik dat document niet in beeld heb.
- Schrijf afkortingen de eerste keer voluit (release candidates, niet RC's).
- Tegengas is helemaal prima. Een feitencheck haalt soms een foutje van mij eruit. Maar zeg ik
  dat ik iets zeker weet, neem dat dan aan, tenzij het aantoonbaar inconsistent is met andere
  informatie die we hebben. Dan moeten we er iets mee.
- Ik dicteer vaak. Daardoor staan er soms verschuivingen in mijn tekst, zoals "Franka",
  "Bomkracht" of "Mathies". Het is Franca, Pompkracht en Matthies; corrigeer dat stil.
- Zijn er bij een lange stap wachttijden, plan dan liever één wachtmoment waarin ik echt weg kan
  dan meerdere korte. Korte wachttijden opvullen kost mij de dag (zie [[over-martijn]]).

## Tijd en planning

Voor meldingen en autonome runs heb ik geen beperkingen; 's nachts staan mijn apparaten toch op
niet storen. Voor de planning gelden vaste ankers:

- Donderdagavond is tijd met Franca. Daar niets anders plannen.
- Zaterdag houd ik vrij om met Franca te wandelen of samen iets te doen.
- Trainingen plan ik eerst en de rest eromheen. Twee zware trainingen kunnen niet op
  opeenvolgende dagen. Schuiven kan wel, bijvoorbeeld een training eerder op de dag als Hendrik
  alleen dan kan.

## Eerdere correcties, als voorbeeld

- Release candidates voor staging: per nieuwe repo eerst de stappen voorleggen; pushen doe ik.
- Een keten van taken is afhankelijkheidsgestuurd: elk item wacht alleen op zijn eigen
  afhankelijkheden, niet op een stap als geheel.
- Klantmails in je/jou-vorm, met "Met vriendelijke groet", niets ongevraagd aanbieden. Zoek eerst
  een eerdere mail of factuur als precedent voor methode, toon en adres. Zie [[schrijfstem]].

## Technisch afgedwongen

Wat hierboven staat, is zoveel mogelijk ook in `.claude/settings.json` en in de skills vastgelegd:
`git push` en het lezen van `.env` zijn geweigerd, skills voeren alleen uit wat als regel in de
skill staat en hebben hun eigen `allowed-tools`, en cijfers komen altijd uit scripts op data in
`data/`. Een zin in deze notitie is zwakker dan zo'n regel; staat iets hier maar nog niet
technisch vast, dan is dat een kandidaat.
