---
description: Hoe Martijn schrijft in mail, pull requests en YouTrack - aanhef, groet en toon per relatie, met voorbeeldzinnen uit zijn eigen mails
tags: [werk, prive, schrijfstem, mail]
---

# Schrijfstem

Opgetekend op 15-11-2026 uit verzonden mail (zakelijk en privé, laatste half jaar) en bevestigd
in het interview ([[interview-voortgang]]). Gebruik dit bij elke voorzet voor een bericht. Een
voorzet is altijd oranje: ik zie hem voordat hij de deur uit gaat ([[werkafspraken]]). Zoek bij
een terugkerend bericht eerst de vorige mail als precedent voor methode, toon en adres; zie ook
[[hostingklanten]] en [[facturen-archief]].

## Kern

- Geen aanloop. De eerste zin is de boodschap. Geen "ik hoop dat alles goed gaat", geen
  samenvatting van wat de ander al weet.
- Korte zinnen, één ding per zin. Bedragen, versies, data en percentages staan er concreet in.
- Meer dan één vraag of onderwerp: nummeren.
- Vraag expliciet om de reactie die ik nodig heb: "Wil je dat even laten weten?", "Controleer jij
  voor de zekerheid even of het zo klopt?"
- Je/jou-vorm bij iedereen die ik ken. U-vorm alleen bij onbekenden en organisaties.
- Geen emoji in zakelijke mail. Privé af en toe één, nooit veel.
- Niets ongevraagd aanbieden en geen verkooppraat.
- Geen gedachtestreepjes.

## Aanhef en groet per relatie

| Relatie | Aanhef | Afsluiting |
|---|---|---|
| Klant, formeel of eerste mail in een onderwerp (factuur, tarief, prijswijziging) | Beste Hendrik, / Beste Afke, / Beste Jeroen, | Met vriendelijke groet, Martijn van der Woud, The Crimson Cricket Internet Services |
| Klant, vervolg in een lopend onderwerp | Hoi Hendrik, / Hoi Jeroen, | Met vriendelijke groet, Martijn (of: groetjes Martijn) |
| Klant tijdens een incident | Hi Bert, of meteen "Heads up:" / "Update:" | Met vriendelijke groet, Martijn |
| Franca | Hee lieverd, / Lieve Franca, | x M / x Pimz / een grap als "je liefhebbende accountant" |
| Vrienden en familie | Hoi Véronique, | Liefs, Martijn en Franca |
| Zakelijk privé (aannemer, schilder), namens ons beiden | Hoi Dille en Wick, | Hartelijke groet, Franca de Jonge en Martijn van der Woud |
| Onbekenden en organisaties | Goedenavond, (u-vorm) | Met hartelijke groet, Martijn van der Woud |
| Zoons | geen aanhef | geen groet |

## Voorbeelden, woordelijk

**Factuur** (maandelijks, altijd hetzelfde):
> Beste Hendrik, Bijgevoegd stuur ik je de factuur en tijdverantwoording, in verband met mijn
> werkzaamheden voor Arbeidskracht in de maand oktober 2026.

**Tarief**:
> Per 1 januari wil ik een inflatiecorrectie van 3,7% toepassen op mijn uurtarief. Het tarief komt
> daarmee op €95,83 exclusief BTW. Ik hoop dat je hiermee akkoord kunt gaan. Wil je dat even laten
> weten?

**Vragen aan een klant**:
> Twee vragen: 1. Ik zag op de cbpsy.com site een linkje "English", wat uitkomt bij [...]. Zal ik
> die instellen voor het logo in de Engelstalige versie? 2. Welke link zal ik instellen voor
> [To the interest profiler] in de Engelstalige versie?

**Klaar, graag controleren**:
> De links zijn aangepast. Controleer jij voor de zekerheid even of het zo klopt?

**Incident, status eerst, eigen fout zonder omhaal, redenering erbij**:
> Heads up: DIIS is tijdelijk niet beschikbaar. Ik had tijdelijke wijzigingen doorgevoerd en deze
> getest met PHP versie 8.3. Dit ging allemaal goed, maar ik heb dit iets te voorbarig doorgezet
> naar productie met PHP versie 8.5.

> Ik durf het niet aan om de applicatie vannacht door te laten draaien zonder dat ik er toezicht
> op kan houden. Daarom haal ik al onze PHP applicaties offline, waaronder dus ook DIIS.

> Inmiddels heb ik de PHP update kunnen installeren. De tijdelijke maatregelen zijn dus niet meer
> nodig. DIIS is weer online.

**Prijswijziging doorgeven** (15-11-2026, met Claude opgesteld op basis van mijn mail van vorig
jaar, voelde als mijn eigen stem): de boodschap in de eerste zin, dan een tabel met nu, nieuw en
verschil per onderdeel, het totaal per maand en per jaar, en wanneer de klant het op de factuur
ziet.

**Franca, administratie**:
> Ingeboekt

> Hee lieverd, Nog even een gentle reminder: voor Jennifer moet nog een factuur worden gemaakt
> voor Rooted to Rise, voor haar werkgever.

**Vrienden, meedenken met de ander**:
> Voor het etentje: is het OK als we uiterlijk 2 oktober laten weten of we met z'n tweeën komen
> eten? Dan heb jij nog een dag voor de deadline om het door te geven.

**Zakelijk privé, gestructureerd**:
> Voor we tekenen hebben we nog een paar vragen, en we willen graag even afstemmen over de
> planning en volgorde. Wij hadden dit bedacht: 1. Planning en volgorde [...] 2. Achterdeur [...]

## Pull requests en YouTrack

Dit is geen schrijfstem maar een conventie: de teksten worden door Claude gegenereerd en mogen
zonder mijn blik geplaatst worden ([[werkafspraken]]).

- Altijd in het Engels, ook als het gesprek Nederlands is.
- Titel van een PR begint met de YouTrack-key: `PA-1071 Add ON_SITE_INTERVIEW_FINISHED action
  point rule`. Merge-PR's heten `Merge hotfix/4.13.1 into develop`.
- Beschrijving met de kopjes Summary, Assumptions en Test plan (met afvinklijst). Afwijkingen
  tussen plan en implementatie expliciet benoemen.
- YouTrack-issues en -commentaar in het Engels, feitelijk, met wat er is gedaan en wat open staat.
