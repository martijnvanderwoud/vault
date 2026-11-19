#!/usr/bin/env python3
"""Rekent een weekplanning door uit soorten dagen, weekdagen, trainingen, afspraken en het weektarget.

Gebruik: python3 scripts/weekplanning.py data/weekplanning/weken/<maandag>.json [--schrijf]

Een dag = de blokken van de soort dag (data/weekplanning/dagsoorten.json) met de klusjes en de
avond van de weekdag (data/weekplanning/weekdagen.json) erbij. Werkblokken zijn 'vul' (tot het
volgende blok met een vaste tijd), een vast aantal uren, of 'rest' (wat er van het werk van die dag
over is). Een vaste tijd is 'om' (kloktijd) of 'minstens_na' (minuten na een eerder blok).

Een week (data/weekplanning/weken/<maandag>.json) noemt de trainingsweek en de afspraken. De soort dag
per weekdag komt uit de trainingen (dagsoort), de duur van Hardlopen uit trainingsduur.py, naar boven
afgerond op een kwartier (trainingsduur: de werkelijke duur, als een run langer duurde). Het declarabele
doel van de week komt uit data/weekplanning/weektargets.csv (uren.py --zet-week, op zondag). Vrije dagen
(data/vrije-dagen.csv) krijgen geen werk; een halve vrije dag krijgt 2,8 u vrij aan het eind van de werkdag.

Ruimte is wat er op een werkdag overblijft tot het eten (of het eerste vaste avondblok, zoals Ellie
bellen). Het doel wordt zo over de werkdagen verdeeld dat de ruimte per dag gelijk is, minimaal 0: een dag
met minder ruimte krijgt geen extra werk. Past het werk zo niet, dan vervalt wat verder in wijkt_eerst
staat (regels.json, de stabiliteitsroutines), op de dag waar dat de meeste ruimte geeft; past het dan nog
niet, dan is het een conflict. Niets schuift door naar volgende week.

Een afspraak (met reistijd en omschakelen ervoor en erna) die begint terwijl er gewerkt wordt, knipt het
werkblok waar hij in begint; valt hij over de training, dan schuift de training naar na de afspraak. Een
afspraak na het werk staat in de ruimte, of na het eten tussen de avondblokken.

Herplannen tijdens de week (herplannen: {vanaf, gewerkt_uren} in het weekbestand): de dagen voor vanaf
zijn voorbij. Nog te gaan = declarabel doel − gewerkt_uren (t/m de dag voor vanaf, uit uren.py),
opnieuw verdeeld over de rest van de week met gelijke ruimte.

Met --schrijf komt de planning ook als notitie in gebieden/weekplanning/<maandag>.md.
"""
import csv
import json
import math
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trainingsduur import Tempos, s_naar_tekst, training_rekenen  # noqa: E402
import vrije_dagen  # noqa: E402

VAULT = Path(__file__).resolve().parent.parent
DATA = VAULT / "data" / "weekplanning"
TRAININGEN = VAULT / "data" / "hardlopen" / "trainingen"
TEMPOS = VAULT / "data" / "hardlopen" / "tempos.json"
NOTITIES = VAULT / "gebieden" / "weekplanning"
WEEKTARGETS = DATA / "weektargets.csv"
MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september",
           "oktober", "november", "december"]
WEEKDAGEN = ["ma", "di", "wo", "do", "vr", "za", "zo"]
VOLUIT = dict(zip(WEEKDAGEN, ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag",
                              "zaterdag", "zondag"]))


def hhmm_naar_min(tekst):
    u, m = tekst.split(":")
    return int(u) * 60 + int(m)


def min_naar_hhmm(m):
    return f"{m // 60:02d}:{m % 60:02d}"


def duur_tekst(m):
    return ("-" if m < 0 else "") + f"{abs(m) // 60}:{abs(m) % 60:02d}"


def lees(naam):
    return json.loads((DATA / naam).read_text())


def op_blok(m, omhoog=True):
    """Rondt minuten af op het kleinste blok (regels.json, kleinste_blok_min), naar boven of naar beneden."""
    blok = lees("regels.json")["kleinste_blok_min"]
    return (math.ceil(m / blok) if omhoog else math.floor(m / blok)) * blok


def blokken_met_klusjes(dagsoort, weekdag, notities):
    """Zet de klusjes met 'na' en 'samen_met' tussen de blokken van de soort dag, dan de ruimte en de avond.

    Ontbreekt het blok waar een klusje aan vastzit op deze soort dag, dan komt het klusje voor de ruimte.
    De ruimte is een blok zonder duur aan het eind van de werkdag: de vrije tijd tot het eerste vaste
    avondblok volgt erna.
    """
    blokken = [dict(b) for b in dagsoort["blokken"]]
    for k in weekdag["klusjes"]:
        if "samen_met" in k:
            b = next((b for b in blokken if b["activiteit"] == k["samen_met"]), None)
            if b:
                b["activiteit"] += " en " + k["activiteit"]
            else:
                notities.append(f"{k['activiteit']}: geen '{k['samen_met']}' op deze soort dag, zelf inpassen")
        elif "na" in k:
            i = next((i + 1 for i, b in enumerate(blokken) if b["activiteit"] == k["na"]), None)
            if i is None:
                i = len(blokken)
                notities.append(f"{k['activiteit']}: geen '{k['na']}' op deze soort dag, staat aan het eind "
                                "van de werkdag")
            blokken.insert(i, {"activiteit": k["activiteit"], "duur_min": k["duur_min"]})
    ruimte = {"activiteit": "Ruimte", "soort": "ruimte", "duur_min": 0}
    return blokken + [ruimte] + [dict(b) for b in weekdag["avond"]]


def ruimte_plek(blokken):
    return next(i for i, b in enumerate(blokken) if b.get("soort") == "ruimte")


def anker_plek(blokken):
    """Het blok waar de ruimte ophoudt: het eerste blok met een vaste tijd na de ruimte, dat er niet in staat."""
    ri = ruimte_plek(blokken)
    return next(i for i in range(ri + 1, len(blokken)) if "om" in blokken[i] and not blokken[i].get("in_ruimte"))


def ruimte_grens(blokken):
    """Hoe laat iets in de ruimte uiterlijk klaar moet zijn: het anker min de losse avondblokken ervoor."""
    ri, ai = ruimte_plek(blokken), anker_plek(blokken)
    ertussen = sum(b.get("duur_min", 0) for b in blokken[ri + 1:ai] if not b.get("in_ruimte"))
    return hhmm_naar_min(blokken[ai]["om"]) - ertussen


def blok_einde(rij, blokken, k):
    begin, _, werk = rij[k]
    return begin + (werk if werk is not None else blokken[k].get("duur_min", 0))


def ruimte_min(blokken, rij):
    """Minuten ruimte: de vrije gaten tot het anker. Loopt de dag over het anker heen, dan negatief."""
    ai = anker_plek(blokken)
    anker = hhmm_naar_min(blokken[ai]["om"])
    eind_voor = blok_einde(rij, blokken, ai - 1)
    if eind_voor > anker:
        return anker - eind_voor
    return sum(max(0, rij[k + 1][0] - blok_einde(rij, blokken, k)) for k in range(ai))


def in_ruimte_invoegen(blokken, nieuw):
    """Zet blokken met een vaste tijd na het werk in de ruimte, op volgorde van tijd."""
    nieuw = [b | {"in_ruimte": True} for b in nieuw]
    van = hhmm_naar_min(nieuw[0]["om"])
    i = ruimte_plek(blokken) + 1
    while i < len(blokken) and blokken[i].get("in_ruimte"):
        if "om" in blokken[i] and hhmm_naar_min(blokken[i]["om"]) > van:
            break
        i += 1
    return blokken[:i] + nieuw + blokken[i:]


def ankertijd(blok, eind):
    """De vaste tijd van een blok, of None. eind: einde van de blokken tot nu toe, per activiteit."""
    if "om" in blok:
        return hhmm_naar_min(blok["om"])
    if "minstens_na" in blok:
        na = blok["minstens_na"]
        return eind[na["activiteit"]] + na["min"]
    return None


def vul_tot(blokken, i, t, eind):
    """Waar een 'vul'-werkblok op plek i ophoudt: bij het volgende vaste blok, min de blokken ertussen."""
    ertussen = 0
    for b in blokken[i + 1:]:
        if "om" in b:
            return hhmm_naar_min(b["om"]) - ertussen
        if "minstens_na" in b:
            # Eerder klaar dan het anker mag; een minimum dat al voorbij is houdt het werkblok op nul.
            return max(t + ertussen, ankertijd(b, eind)) - ertussen
        ertussen += round(b["werk"] * 60) if isinstance(b.get("werk"), (int, float)) else b.get("duur_min", 0)
    raise ValueError(f"werkblok 'vul' op plek {i + 1} zonder vast blok erna")


def tijden(blokken, opstaan, rest_min, conflicten, inkorten=None):
    """Zet de blokken op tijd. Geeft per blok (begin_min, activiteit, werkduur_min of None).

    inkorten: minuten minder werk per plek van een 'vul'-blok; het gat erna is ruimte.
    """
    rij, t, eind, inkorten = [], opstaan, {}, inkorten or {}
    for i, b in enumerate(blokken):
        anker = ankertijd(b, eind)
        if anker is not None:
            if "om" in b and t > anker + b.get("speling_min", 0):
                conflicten.append(f"{b['activiteit']} om {b['om']}, maar het blok ervoor loopt tot "
                                  f"{min_naar_hhmm(t)}")
            t = max(t, anker)
        if "werk" in b:
            if b["werk"] == "vul":
                duur = max(0, vul_tot(blokken, i, t, eind) - t)
            elif b["werk"] == "rest":
                duur = rest_min
            else:
                duur = round(b["werk"] * 60)
            duur -= inkorten.get(i, 0)
            rij.append((t, b["activiteit"], duur))
        else:
            duur = b.get("duur_min", 0)
            rij.append((t, b["activiteit"], None))
        t += duur
        eind[b["activiteit"]] = t
    return rij


def dag_opbouwen(blokken, werkdoel_min, opstaan):
    """Geeft de blokken op tijd, met 'rest' zo dat het werkdoel gehaald wordt, en eventuele conflicten.

    Zonder werkdoel (None) is 'rest' 0: het werk dat de dag uit zichzelf heeft.
    """
    conflicten = []
    rij = tijden(blokken, opstaan, 0, [])
    if werkdoel_min is None:
        return tijden(blokken, opstaan, 0, conflicten), conflicten
    gewerkt = sum(w for _, _, w in rij if w)
    rest, inkorten = werkdoel_min - gewerkt, {}
    # Minder werk dan de 'vul'-blokken geven: eraf van de laatste 'vul'-blokken.
    for i in reversed(range(len(blokken))):
        if rest < 0 and blokken[i].get("werk") == "vul" and rij[i][2]:
            inkorten[i] = min(rij[i][2], -rest)
            rest += inkorten[i]
    if rest < 0:
        conflicten.append(f"vaste werkblokken zijn {gewerkt / 60:.2f} u, meer dan het werk van de dag")
        rest = 0
    return tijden(blokken, opstaan, rest, conflicten, inkorten), conflicten


def einde_rij(rij, k):
    """Einde van rij k: het begin van de volgende rij (de laatste rij heeft geen einde)."""
    return rij[k + 1][0] if k + 1 < len(rij) else rij[k][0]


def afspraak_marges(afspraak):
    """Minuten voor en na een afspraak: reistijd (terug: reistijd_terug_min als die er is) en omschakelen."""
    heen = afspraak.get("reistijd_min", 0)
    terug = afspraak.get("reistijd_terug_min", heen)
    omschakelen = afspraak.get("omschakelen_min", 0)
    return op_blok(heen + omschakelen), op_blok(terug + omschakelen)


def afspraak_tijden(afspraak):
    """Begin en einde van een afspraak met reistijd en omschakelen."""
    voor, na = afspraak_marges(afspraak)
    return hhmm_naar_min(afspraak["van"]) - voor, hhmm_naar_min(afspraak["tot"]) + na


def afspraak_blokken(afspraak):
    """De blokken van een afspraak, met reistijd en omschakelen ervoor en erna."""
    van, tot = hhmm_naar_min(afspraak["van"]), hhmm_naar_min(afspraak["tot"])
    voor, na = afspraak_marges(afspraak)
    blokken = [{"activiteit": afspraak["activiteit"], "om": afspraak["van"], "duur_min": tot - van}]
    if voor:
        blokken.insert(0, {"activiteit": "Reistijd en omschakelen", "om": min_naar_hhmm(van - voor),
                           "duur_min": voor})
    if na:
        blokken.append({"activiteit": "Reistijd en omschakelen", "duur_min": na})
    return blokken


def afspraak_invoegen(blokken, rij, afspraak, heel=True, erna=()):
    """Knipt het werkblok waar de afspraak (met reistijd en omschakelen) in begint. rij hoort bij blokken.

    Loopt de afspraak over het werkblok heen, dan schuiven de blokken erna op, zolang er geen blok met een
    vaste tijd of de training tussen zit. Geeft None als dat wel zo is, of als het begin niet in een
    werkblok valt. Met heel=False mag de afspraak overal overheen lopen; zo werken klusjes met een vaste
    tijd. erna: blokken die direct na de afspraak komen.
    """
    begin_a, einde_a = afspraak_tijden(afspraak)
    for i, (begin, _, werk) in enumerate(rij):
        if werk and begin <= begin_a < begin + werk:
            break
    else:
        return None
    if heel and any(r[0] < einde_a and ("om" in b or "minstens_na" in b or b.get("soort") == "training")
                    for r, b in zip(rij[i + 1:], blokken[i + 1:])):
        return None

    b = blokken[i]
    voor = [{"activiteit": b["activiteit"], "werk": "vul"}] if begin_a > begin else []
    midden = afspraak_blokken(afspraak) + list(erna)
    na_werk = b["werk"]
    if isinstance(na_werk, (int, float)):
        na_werk -= (begin_a - begin) / 60
    na = [{"activiteit": b["activiteit"], "werk": na_werk}] if na_werk else []
    return blokken[:i] + voor + midden + na + blokken[i + 1:]


def training_na_afspraak(blokken, rij, afspraak, werkdoel, opstaan):
    """Zet de training na een afspraak die erover valt. rij hoort bij blokken.

    De training schuift mee met het blok ervoor (naar buiten) en de blokken erna tot het volgende
    werkblok (uitloop, douchen). Geeft None als de afspraak die blokken niet raakt, of als hij ook
    zonder die blokken niet in een werkblok past.
    """
    ti = next((i for i, b in enumerate(blokken) if b.get("soort") == "training"), None)
    if ti is None:
        return None
    van = ti - 1 if ti and "werk" not in blokken[ti - 1] else ti
    tot = ti + 1
    while tot < len(blokken) and not ({"werk", "om"} & blokken[tot].keys()) and blokken[tot].get("soort") != "ruimte":
        tot += 1
    begin_a, einde_a = afspraak_tijden(afspraak)
    if not (rij[van][0] < einde_a and begin_a < einde_rij(rij, tot - 1)):
        return None
    zonder = blokken[:van] + blokken[tot:]
    zonder_rij, _ = dag_opbouwen(zonder, werkdoel, opstaan)
    return afspraak_invoegen(zonder, zonder_rij, afspraak, erna=blokken[van:tot])


def avond_invoegen(blokken, rij, afspraak, notities):
    """Zet een afspraak die na het werk begint en over het anker heen loopt tussen de avondblokken.

    Avondblokken die voor de afspraak niet meer af zijn, gaan naar een vrij gat voor een blok met een
    vaste tijd, en anders na de afspraak. Blokken met een vaste tijd voor de afspraak (zoals eten)
    blijven ervoor en geven zo nodig een conflict. Na de afspraak geen downtime: bijkomen en spullen
    wegleggen, de bedroutine en dan naar bed, ook als dat later is dan de bedtijd. Een afspraak thuis
    ('thuis': true) loopt hooguit tot de bedroutine, en dan op de normale tijd naar bed.
    """
    begin_a, _ = afspraak_tijden(afspraak)
    ri = ruimte_plek(blokken)
    avond = blokken[ri + 1:]
    tijd = dict(zip(map(id, blokken), (r[0] for r in rij)))
    ervoor = [b for b in avond if "om" in b and hhmm_naar_min(b["om"]) < begin_a
              or "om" not in b and "duur_min" in b and tijd[id(b)] + b["duur_min"] <= begin_a]
    verplaatst = [b for b in avond if b not in ervoor and "om" not in b and "duur_min" in b]
    erna = []
    for b in avond:
        if b in ervoor or b in verplaatst or "duur_min" not in b and "om" not in b:
            continue
        if b.get("soort") in ("bedroutine", "bed") and not afspraak.get("thuis"):
            if b.get("soort") == "bedroutine":
                erna.append({"activiteit": "Bijkomen, spullen wegleggen", "duur_min": b["bijkomen_min"]})
            b = {k: v for k, v in b.items() if k != "om"}
        erna.append(b)

    # Verplaatste blokken in een gat voor een vast blok zetten, zolang ze passen.
    nieuw, t, vroeger = [], rij[ri][0], []
    for b in ervoor:
        if "om" in b:
            while verplaatst and t + verplaatst[0]["duur_min"] <= hhmm_naar_min(b["om"]):
                v = verplaatst.pop(0)
                nieuw.append(v)
                vroeger.append(v["activiteit"])
                t += v["duur_min"]
            t = max(t, hhmm_naar_min(b["om"]))
        nieuw.append(b)
        t += b["duur_min"]
    if vroeger:
        notities.append(f"voor {afspraak['activiteit']}: {', '.join(vroeger)}")
    if verplaatst:
        notities.append(f"na {afspraak['activiteit']}: {', '.join(b['activiteit'] for b in verplaatst)}")
    if afspraak.get("thuis"):
        routine = next((b["om"] for b in erna if b.get("soort") == "bedroutine"), None)
        if routine and hhmm_naar_min(afspraak["tot"]) > hhmm_naar_min(routine):
            notities.append(f"{afspraak['activiteit']} staat tot {afspraak['tot']} in de agenda, "
                            f"bedroutine op de normale tijd ({routine})")
            afspraak = afspraak | {"tot": routine}
    return blokken[:ri + 1] + nieuw + afspraak_blokken(afspraak) + verplaatst + erna


def vrij_invoegen(rij, blokken):
    """Zet de gaten in de rij als 'Ruimte' (tot het anker) of 'Vrij' (erna) en voegt aansluitend werk samen.

    rij hoort bij blokken.
    """
    ai = anker_plek(blokken)
    uit = []
    for k, (begin, act, werk) in enumerate(rij):
        ruimte = blokken[k].get("soort") == "ruimte"
        if ruimte:
            pass
        elif werk and uit and uit[-1][1] == act and uit[-1][2] and uit[-1][0] + uit[-1][2] == begin:
            uit[-1] = (uit[-1][0], act, uit[-1][2] + werk)
        elif werk != 0:
            uit.append((begin, act, werk))
        einde = blok_einde(rij, blokken, k)
        # Een blok zonder duur (Downtime) loopt door tot het volgende blok.
        if k + 1 < len(rij) and rij[k + 1][0] > einde and ("duur_min" in blokken[k] or werk or ruimte):
            uit.append((einde, "Ruimte" if k < ai else "Vrij", None))
    return uit


def dag_plannen(dagsoort, weekdag, regels, werkdoel, hardlopen_min=None, afspraken=(), vervalt=(), aanpassen=(),
                opstaan_dag=None, hardlopen_werkelijk=None, zonder=(), half_vrij=False):
    """Plant een dag met werkdoel minuten werk (None: het werk dat de dag uit zichzelf heeft, 'rest' 0).

    Geeft een dict met de rij, de ruimte (min), het geplande werk (min), conflicten en notities.
    zonder: soorten blokken die vervallen omdat de week anders te vol is (uit wijkt_eerst).
    Met opstaan_dag (later opstaan) of hardlopen_werkelijk (de training duurde langer) loopt de dag uit;
    dat gaat van de ruimte af.
    """
    notities, conflicten_vast = [], []
    opstaan, wijkt_eerst = hhmm_naar_min(regels["opstaan"]), regels["wijkt_eerst"]
    # Aanpassen van een klusje (zoals een andere tijd) gaat in het klusje zelf, voor het ingepland wordt.
    namen = {k["activiteit"] for k in weekdag["klusjes"]}
    klusjes = [k | next(({x: v for x, v in a.items() if x not in ("dag", "activiteit")}
                         for a in aanpassen if a["activiteit"] == k["activiteit"]), {})
               for k in weekdag["klusjes"]]
    klusjes = [k | {"activiteit": k.pop("wordt")} if "wordt" in k else k for k in klusjes]
    weekdag = weekdag | {"klusjes": klusjes}
    aanpassen = [a for a in aanpassen if a["activiteit"] not in namen]
    blokken = blokken_met_klusjes(dagsoort, weekdag, notities)
    # De bedroutine eindigt op de bedtijd; na een avondafspraak eerst nog bijkomen en spullen wegleggen.
    bed = hhmm_naar_min(regels["naar_bed"])
    blokken.append({"activiteit": "Bedroutine", "soort": "bedroutine",
                    "om": min_naar_hhmm(bed - regels["bedroutine_min"]), "duur_min": regels["bedroutine_min"],
                    "bijkomen_min": regels["bijkomen_na_afspraak_min"]})
    blokken.append({"activiteit": "Naar bed", "soort": "bed", "om": regels["naar_bed"], "duur_min": 0})
    for a in aanpassen:
        b = next((b for b in blokken if b["activiteit"] == a["activiteit"]), None)
        if b is None:
            conflicten_vast.append(f"aanpassen: geen '{a['activiteit']}' op deze dag")
            continue
        b.update({k: v for k, v in a.items() if k not in ("dag", "activiteit", "wordt")})
        b["activiteit"] = a.get("wordt", b["activiteit"])
    for soort in vervalt:
        weg = [b["activiteit"] for b in blokken if b.get("soort") == soort]
        blokken = [b for b in blokken if b.get("soort") != soort]
        if weg:
            notities.append(f"{', '.join(weg)} vervalt deze week")
    for soort in zonder:
        weg = [b["activiteit"] for b in blokken if b.get("soort") == soort]
        blokken = [b for b in blokken if b.get("soort") != soort]
        notities.append(f"{', '.join(weg)} vervalt: anders past het werk van de week niet")
    if half_vrij:
        # Een halve vrije dag: de helft van een vrije dag vrij aan het eind van de werkdag.
        ri = ruimte_plek(blokken)
        blokken.insert(ri + 1, {"activiteit": "Vrij (halve vrije dag)",
                                "duur_min": op_blok(vrije_dagen.UREN_PER_DAG * 30)})
    if hardlopen_min:
        for b in blokken:
            if b.get("soort") == "training":
                b["duur_min"] = hardlopen_min
    if opstaan_dag is not None and hhmm_naar_min(opstaan_dag) > opstaan:
        notities.append(f"op om {opstaan_dag}")
        opstaan = hhmm_naar_min(opstaan_dag)
    if hardlopen_werkelijk:
        next(b for b in blokken if b.get("soort") == "training")["duur_min"] = hardlopen_werkelijk
    rij, conflicten = dag_opbouwen(blokken, werkdoel, opstaan)

    def na_het_werk(nieuw, begin):
        """Zet blokken met een vaste tijd na het werk: in de ruimte als ze voor de grens af zijn."""
        if begin + sum(b["duur_min"] for b in nieuw) <= ruimte_grens(blokken):
            return in_ruimte_invoegen(blokken, nieuw)
        return None

    # Klusjes met een vaste tijd knippen het werkblok waar ze in beginnen; is de werkdag dan al klaar,
    # dan staat het klusje op zijn tijd in de ruimte.
    for k in weekdag["klusjes"]:
        if "om" not in k:
            continue
        klusje = {"activiteit": k["activiteit"], "van": k["om"],
                  "tot": min_naar_hhmm(hhmm_naar_min(k["om"]) + k["duur_min"])}
        nieuw = afspraak_invoegen(blokken, rij, klusje, heel=False)
        if nieuw is None and hhmm_naar_min(k["om"]) >= rij[ruimte_plek(blokken)][0]:
            nieuw = na_het_werk([{"activiteit": k["activiteit"], "om": k["om"], "duur_min": k["duur_min"]}],
                                hhmm_naar_min(k["om"]))
        if nieuw is None:
            conflicten_vast.append(f"{k['activiteit']} om {k['om']} valt niet in een werkblok of de ruimte")
            continue
        blokken = nieuw
        rij, conflicten = dag_opbouwen(blokken, werkdoel, opstaan)

    for a in afspraken:
        begin_a, einde_a = afspraak_tijden(a)
        if begin_a >= rij[ruimte_plek(blokken)][0]:
            # Na het werk: in de ruimte, of tussen de avondblokken als hij over het anker heen loopt.
            nieuw = na_het_werk(afspraak_blokken(a), begin_a)
            blokken = nieuw if nieuw is not None else avond_invoegen(blokken, rij, a, notities)
            rij, conflicten = dag_opbouwen(blokken, werkdoel, opstaan)
            continue
        # Past de afspraak niet in een werkblok, dan vervallen eerst de blokken uit wijkt_eerst.
        wijkbaar = [s for s in wijkt_eerst if s != "ruimte"]
        proef, proefrij, vervallen = blokken, rij, []
        while (nieuw := afspraak_invoegen(proef, proefrij, a)) is None and wijkbaar:
            soort = wijkbaar.pop(0)
            weg = [b["activiteit"] for b in proef if b.get("soort") == soort]
            if weg:
                proef = [b for b in proef if b.get("soort") != soort]
                vervallen += weg
                proefrij, _ = dag_opbouwen(proef, werkdoel, opstaan)
        if nieuw is None:
            # Hardlopen gaat altijd door: dan schuift de training naar na de afspraak.
            nieuw = training_na_afspraak(blokken, rij, a, werkdoel, opstaan)
            if nieuw is not None:
                vervallen = []
                notities.append(f"Hardlopen schuift naar na {a['activiteit']}")
        if nieuw is None:
            geraakt = [act for k, (begin, act, _) in enumerate(rij)
                       if begin < einde_a and begin_a < einde_rij(rij, k)]
            conflicten_vast.append(
                f"{a['activiteit']} {a['van']}-{a['tot']} (met reistijd {min_naar_hhmm(begin_a)}-"
                f"{min_naar_hhmm(einde_a)}) valt niet in één werkblok: " + ", ".join(geraakt))
            continue
        if vervallen:
            notities.append(f"{', '.join(vervallen)} vervalt voor {a['activiteit']}")
        blokken = nieuw
        rij, conflicten = dag_opbouwen(blokken, werkdoel, opstaan)
    return {"rij": vrij_invoegen(rij, blokken), "ruimte": ruimte_min(blokken, rij),
            "gepland": sum(w for _, _, w in rij if w), "conflicten": conflicten_vast + conflicten,
            "notities": notities}


def week_plannen(toewijzing, doel_min, dagen=WEEKDAGEN, vrij=None, hardlopen=None, afspraken=None, vervalt=None,
                 aanpassen=None, opstaan=None, werkelijk=None, later_min=0):
    """Plant de dagen en verdeelt doel_min werk zo dat de ruimte per werkdag gelijk is, minimaal 0.

    Elke werkdag begint met het werk dat hij uit zichzelf heeft ('rest' 0). Een dag met te weinig ruimte
    geeft eerst werk af; dan gaat er steeds een blok werk bij op de dag met de meeste ruimte, zolang die
    niet onder 0 komt (of eraf op de dag met de minste, als het doel kleiner is). Is de week vol, dan
    vervalt wat verder in wijkt_eerst staat, op de dag waar dat de meeste ruimte geeft. Wat dan nog niet
    past, is een conflict. vrij: {dag: 1 of 0,5}, een vrije dag krijgt geen werk. later_min: zoveel later
    naar bed dan normaal op de dag voor de eerste dag (bij herplannen).
    """
    dagsoorten, weekdagen, regels = lees("dagsoorten.json"), lees("weekdagen.json"), lees("regels.json")
    vrij, hardlopen, afspraken = vrij or {}, hardlopen or {}, afspraken or {}
    vervalt, aanpassen, werkelijk = vervalt or {}, aanpassen or {}, werkelijk or {}
    opstaan = dict(opstaan or {})
    stap = regels["kleinste_blok_min"]
    wijkbaar = [s for s in regels["wijkt_eerst"] if s != "ruimte"]
    naar_bed, opstaan_std = hhmm_naar_min(regels["naar_bed"]), hhmm_naar_min(regels["opstaan"])
    week, plannen, stand, weekconflicten = {}, {}, {}, []

    def bedtijd(plan):
        return next((begin for begin, act, _ in plan["rij"] if act == "Naar bed"), None)

    for dag in dagen:
        soort = dagsoorten[toewijzing[dag]]
        # Later naar bed dan normaal is evenveel later opstaan, naar boven afgerond op het kleinste blok.
        if later_min and dag not in opstaan:
            opstaan[dag] = min_naar_hhmm(opstaan_std + op_blok(later_min))
        if vrij.get(dag) == 1 or not soort.get("tijdsindeling", True):
            notities = [f"afspraak {a['activiteit']} {a['van']}-{a['tot']}, training en kracht eromheen"
                        for a in afspraken.get(dag, [])]
            week[dag] = {"rij": [], "ruimte": None, "gepland": 0, "conflicten": [], "notities": notities,
                         "vrij": vrij.get(dag) == 1}
        else:
            cache = {}

            def plan(w, zonder=(), dag=dag, soort=soort, cache=cache):
                if (w, zonder) not in cache:
                    cache[w, zonder] = dag_plannen(
                        soort, weekdagen[dag], regels, w, hardlopen.get(dag), afspraken.get(dag, []),
                        vervalt.get(dag, []), aanpassen.get(dag, []), opstaan.get(dag), werkelijk.get(dag),
                        zonder, vrij.get(dag) == 0.5)
                return cache[w, zonder]
            plannen[dag] = plan
            week[dag] = plan(None)
            stand[dag] = (week[dag]["gepland"], ())
        bed = bedtijd(week[dag])
        later_min = max(0, bed - naar_bed) if bed is not None else 0

    def zetten(dag, w, zonder):
        stand[dag] = (w, zonder)
        week[dag] = plannen[dag](w, zonder)

    def kan(dag, w, zonder=None):
        """Het plan van de dag met w werk, als dat precies w geeft en geen nieuwe conflicten."""
        p = plannen[dag](w, stand[dag][1] if zonder is None else zonder)
        return p if p["gepland"] == w and len(p["conflicten"]) <= len(week[dag]["conflicten"]) else None

    def totaal():
        return sum(week[d]["gepland"] for d in plannen)

    # Een dag met te weinig ruimte (later op, afspraak) geeft werk af aan de andere dagen.
    for dag in plannen:
        while week[dag]["ruimte"] < 0 and stand[dag][0] >= stap:
            p = kan(dag, stand[dag][0] - stap)
            if p is None or p["ruimte"] <= week[dag]["ruimte"]:
                break
            zetten(dag, stand[dag][0] - stap, stand[dag][1])

    while totaal() < doel_min:
        kandidaten = [d for d in plannen if (p := kan(d, stand[d][0] + stap)) and p["ruimte"] >= 0]
        if kandidaten:
            dag = max(kandidaten, key=lambda d: week[d]["ruimte"])
            zetten(dag, stand[dag][0] + stap, stand[dag][1])
            continue
        # De week is vol: dan vervalt het volgende uit wijkt_eerst, op de dag waar dat de meeste ruimte geeft.
        opties = []
        for soort in wijkbaar:
            for d in plannen:
                w, zonder = stand[d]
                if soort not in zonder and (p := kan(d, w, zonder + (soort,))) and p["ruimte"] > week[d]["ruimte"]:
                    opties.append((p["ruimte"], d, soort))
            if opties:
                break
        if not opties:
            weekconflicten.append(f"{duur_tekst(doel_min - totaal())} u werk past niet in de week, ook niet "
                                  "zonder ruimte en " + ", ".join(wijkbaar))
            break
        _, dag, soort = max(opties, key=lambda o: o[0])
        zetten(dag, stand[dag][0], stand[dag][1] + (soort,))

    while totaal() > doel_min:
        kandidaten = [d for d in plannen if stand[d][0] >= stap and kan(d, stand[d][0] - stap)]
        if not kandidaten:
            weekconflicten.append(f"{duur_tekst(totaal() - doel_min)} u meer werk dan het doel: de vaste "
                                  "werkblokken zijn niet korter te maken")
            break
        dag = min(reversed(kandidaten), key=lambda d: week[d]["ruimte"])
        zetten(dag, stand[dag][0] - stap, stand[dag][1])

    for dag in plannen:
        if week[dag]["ruimte"] < 0:
            week[dag]["conflicten"] = week[dag]["conflicten"] + [
                f"{-week[dag]['ruimte']} min te weinig ruimte, ook zonder werk"]
    for dag in dagen:
        bed = bedtijd(week[dag])
        if bed is not None and bed > naar_bed:
            week[dag]["notities"] = week[dag]["notities"] + [
                f"{bed - naar_bed} min later naar bed dan normaal, morgen later op"]
    return week, weekconflicten


def weekdoel(maandag, regels, vrij):
    """Het weektarget van de week (weektargets.csv), de vrije dagen en het declarabele doel, in uren.

    Staat de week er nog niet in (nog niet vastgezet met uren.py --zet-week), dan voorlopig het weektarget
    uit regels.json.
    """
    vast = None
    if WEEKTARGETS.exists():
        with WEEKTARGETS.open(newline="") as f:
            vast = next((r for r in csv.DictReader(f) if r["maandag"] == maandag.isoformat()), None)
    dagen = sum(vrij.values())
    if vast:
        return {"weektarget": float(vast["weektarget"]), "vrije_dagen": float(vast["vrije_dagen"]),
                "declarabel_doel": float(vast["declarabel_doel"]), "vast": True}
    target = regels["voorlopig_weektarget_uren"]
    return {"weektarget": target, "vrije_dagen": dagen,
            "declarabel_doel": target - dagen * vrije_dagen.UREN_PER_DAG, "vast": False}


def ruimte_tekst(week, dagen=WEEKDAGEN):
    waarden = [week[d]["ruimte"] for d in dagen if week[d].get("ruimte") is not None]
    if not waarden:
        return "geen werkdagen"
    laag, hoog = min(waarden), max(waarden)
    return duur_tekst(laag) if laag == hoog else f"{duur_tekst(laag)} tot {duur_tekst(hoog)}"


def doel_tekst(doel):
    tekst = f"declarabel doel {doel['declarabel_doel']:.2f} u"
    if doel["vrije_dagen"]:
        tekst += (f" (weektarget {doel['weektarget']:.2f} u − {doel['vrije_dagen']:g} vrije dag(en) × "
                  f"{vrije_dagen.UREN_PER_DAG:g} u)")
    if not doel["vast"]:
        tekst += ", weektarget nog niet vastgezet: voorlopig"
    return tekst


def week_tonen(week, toewijzing, dagsoorten, weekconflicten, datums, trainingen, doel, vrij_namen, gewerkt_min=0):
    totaal_werk = gewerkt_min
    for dag in WEEKDAGEN:
        plan = week[dag]
        rij = plan["rij"]
        datum = f" {datums[dag]:%d-%m}"
        if plan.get("voorbij"):
            gewerkt = f", {plan['gewerkt'] / 60:.2f} u gewerkt" if plan.get("gewerkt") is not None else ""
            print(f"\n{VOLUIT[dag]}{datum}: voorbij{gewerkt}")
            if not plan.get("vandaag"):
                continue
            # Vandaag is het werk voorbij, maar de avond nog niet: die bepaalt de bedtijd en morgen het opstaan.
            print("  Vandaag zoals gepland (het werk telt niet meer mee):")
            plan = plan["vandaag"]
            rij = plan["rij"]
        else:
            totaal_werk += plan["gepland"]
            soort = f"vrije dag: {vrij_namen[dag]}" if plan.get("vrij") else toewijzing[dag]
            ruimte = f", ruimte {duur_tekst(plan['ruimte'])}" if plan["ruimte"] is not None else ""
            print(f"\n{VOLUIT[dag]}{datum} ({soort}), werk {plan['gepland'] / 60:.2f} u{ruimte}")
        if dag in trainingen and not week[dag].get("voorbij"):
            t, km, duur_s, gepland = trainingen[dag]
            print(f"  Training: {t['omschrijving']} ({km:.1f} km, {s_naar_tekst(duur_s)}, "
                  f"gepland {duur_tekst(gepland)})")
        if not rij:
            print("  Vrije dag: geen werk en geen tijdsindeling" if plan.get("vrij")
                  else f"  {dagsoorten[toewijzing[dag]]['omschrijving']}")
        for begin, act, w in rij:
            print(f"  {min_naar_hhmm(begin)}  {act}" + (f"  [{w / 60:.2f} u]" if w else ""))
        for n in plan["notities"]:
            print(f"  LET OP: {n}")
        for c in plan["conflicten"]:
            print(f"  CONFLICT: {c}")
    print(f"\nWeek: {totaal_werk / 60:.2f} u werk, {doel_tekst(doel)}, ruimte per werkdag {ruimte_tekst(week)}")
    for c in weekconflicten:
        print(f"CONFLICT: {c}")


def notitie_schrijven(week, toewijzing, dagsoorten, weekconflicten, datums, trainingen, invoer_pad, doel,
                      vrij_namen, herplannen=None, gewerkt_min=0):
    """Schrijft de planning als Markdown-notitie naar gebieden/weekplanning/<maandag>.md."""
    def datum_tekst(d):
        return f"{d.day} {MAANDEN[d.month - 1]}"

    maandag, zondag = datums["ma"], datums["zo"]
    periode = (f"{maandag.day} t/m {datum_tekst(zondag)}" if maandag.month == zondag.month
               else f"{datum_tekst(maandag)} t/m {datum_tekst(zondag)}")
    gepland = sum(week[d]["gepland"] for d in WEEKDAGEN if not week[d].get("voorbij"))
    try:
        bron = Path(invoer_pad).resolve().relative_to(VAULT)
    except ValueError:
        bron = Path(invoer_pad)
    werk = f"{duur_tekst(gewerkt_min + gepland)} u"
    if herplannen:
        werk += f" ({duur_tekst(gewerkt_min)} gewerkt, {duur_tekst(gepland)} gepland)"
    regels_md = [
        "---",
        f"description: Weekplanning van {periode} {zondag.year}, "
        "per dag met tijden, training, werkuren en ruimte",
        "tags: [weekplanning]",
        "---",
        "",
        f"# Weekplanning {periode} {zondag.year}",
        "",
        f"> Gegenereerd door `scripts/weekplanning.py --schrijf` uit `{bron}`. Niet met de hand",
        "> bewerken: wijzigingen gaan via het weekbestand. Achtergrond: [[weekplanning-plan]].",
        "",
        f"**Werk** {werk} · **{doel_tekst(doel).replace('.', ',')}** · **ruimte** per werkdag "
        f"{ruimte_tekst(week)}",
        "",
    ]
    if herplannen:
        vanaf = date.fromisoformat(herplannen["vanaf"])
        reden = f" ({herplannen['reden']})" if herplannen.get("reden") else ""
        regels_md += [f"Herpland vanaf {VOLUIT[WEEKDAGEN[vanaf.weekday()]]} {datum_tekst(vanaf)}{reden}: wat er "
                      "van het declarabele doel nog over is, opnieuw verdeeld over de rest van de week met gelijke "
                      "ruimte.", ""]
    regels_md += [
        "| Dag | Soort | Training | Op | Werk | Ruimte |",
        "|---|---|---|---|---:|---:|",
    ]
    for dag in WEEKDAGEN:
        plan, rij = week[dag], week[dag]["rij"]
        if plan.get("voorbij"):
            gewerkt = plan.get("gewerkt")
            regels_md.append(f"| {VOLUIT[dag]} {datums[dag].day} | voorbij | | | "
                             f"{duur_tekst(gewerkt) if gewerkt else ''} | |")
            continue
        training = ""
        if dag in trainingen:
            tr, km, _, duur = trainingen[dag]
            training = f"{km:.0f} km, {duur_tekst(duur)}"
        soort = f"Vrije dag ({vrij_namen[dag]})" if plan.get("vrij") else dagsoorten[toewijzing[dag]]["naam"]
        op = min_naar_hhmm(rij[0][0]) if rij else ""
        werk = duur_tekst(plan["gepland"]) if plan["gepland"] else ""
        ruimte = duur_tekst(plan["ruimte"]) if plan["ruimte"] is not None else ""
        regels_md.append(f"| {VOLUIT[dag]} {datums[dag].day} | {soort} | {training} | {op} | {werk} | {ruimte} |")
    for c in weekconflicten:
        regels_md += ["", f"**Conflict:** {c}"]

    for dag in WEEKDAGEN:
        plan, rij = week[dag], week[dag]["rij"]
        if plan.get("voorbij"):
            if not plan.get("vandaag"):
                continue
            plan, rij = plan["vandaag"], plan["vandaag"]["rij"]
            regels_md += ["", f"## {VOLUIT[dag].capitalize()} {datum_tekst(datums[dag])}: vandaag", "",
                          "Het werk is voorbij en staat in LogMyTime; de rest van de dag zoals gepland, voor de "
                          "bedtijd en het opstaan van morgen.", ""]
        else:
            soort = f"vrije dag ({vrij_namen[dag]})" if plan.get("vrij") else dagsoorten[toewijzing[dag]]["naam"].lower()
            regels_md += ["", f"## {VOLUIT[dag].capitalize()} {datum_tekst(datums[dag])}: {soort}", ""]
        if dag in trainingen and not week[dag].get("voorbij"):
            tr, km, duur_s, duur = trainingen[dag]
            regels_md += [f"Training: {tr['omschrijving']} ({km:.1f} km, {s_naar_tekst(duur_s)}, gepland "
                          f"{duur_tekst(duur)}).", ""]
        if rij:
            regels_md += ["| Tijd | Activiteit | Werk |", "|---|---|---:|"]
            for begin, act, w in rij:
                naam = f"**{act}**" if w else act
                regels_md.append(f"| {min_naar_hhmm(begin)} | {naam} | {duur_tekst(w) if w else ''} |")
        elif plan.get("vrij"):
            regels_md.append("Vrije dag: geen werk en geen tijdsindeling.")
        else:
            regels_md.append(dagsoorten[toewijzing[dag]]["omschrijving"] + ".")
        if plan["notities"] or plan["conflicten"]:
            regels_md.append("")
            regels_md += [f"- {n[0].upper()}{n[1:]}" for n in plan["notities"]]
            regels_md += [f"- **Conflict:** {c}" for c in plan["conflicten"]]
    NOTITIES.mkdir(exist_ok=True)
    pad = NOTITIES / f"{maandag.isoformat()}.md"
    pad.write_text("\n".join(regels_md) + "\n")
    return pad


def week_uit_bestand(pad, schrijf=False):
    invoer = json.loads(Path(pad).read_text())
    maandag = date.fromisoformat(invoer["maandag"])
    datums = {dag: maandag + timedelta(days=i) for i, dag in enumerate(WEEKDAGEN)}
    trainingsweek = json.loads((TRAININGEN / invoer["trainingen"]).read_text())
    tempos = Tempos(json.loads(TEMPOS.read_text()))
    regels, dagsoorten = lees("regels.json"), lees("dagsoorten.json")

    toewijzing = {dag: "rust" for dag in WEEKDAGEN}
    hardlopen, trainingen = {}, {}
    for t in trainingsweek["trainingen"]:
        (km, duur_s), _, _ = training_rekenen(t, tempos)
        toewijzing[t["dag"]] = t["dagsoort"]
        hardlopen[t["dag"]] = math.ceil(duur_s / 900) * 15
        trainingen[t["dag"]] = (t, km, duur_s, hardlopen[t["dag"]])
    afspraken = {}
    for a in invoer["afspraken"]:
        # Op het kleinste blok: begin naar beneden, einde naar boven.
        a = a | {"van": min_naar_hhmm(op_blok(hhmm_naar_min(a["van"]), False)),
                 "tot": min_naar_hhmm(op_blok(hhmm_naar_min(a["tot"])))}
        afspraken.setdefault(a["dag"], []).append(a)
    for dag in afspraken:
        afspraken[dag].sort(key=lambda a: a["van"])
    vervalt = {}
    for v in invoer.get("vervalt", []):
        vervalt.setdefault(v["dag"], []).append(v["soort"])
    aanpassen = {}
    for a in invoer.get("aanpassen", []):
        aanpassen.setdefault(a["dag"], []).append(a)
    opstaan = {o["dag"]: o["om"] for o in invoer.get("opstaan", [])}
    # Werkelijke duur van een training (liep langer of korter dan berekend).
    werkelijk = {t["dag"]: op_blok(t["duur_min"]) for t in invoer.get("trainingsduur", [])}
    vrij, vrij_namen = {}, {}
    for d, deel, omschrijving in vrije_dagen.lees():
        if maandag <= d <= datums["zo"]:
            vrij[WEEKDAGEN[d.weekday()]] = deel
            vrij_namen[WEEKDAGEN[d.weekday()]] = omschrijving + (", halve dag" if deel < 1 else "")

    doel = weekdoel(maandag, regels, vrij)
    print(f"Week van {maandag:%d-%m-%Y}, trainingen {trainingsweek['plan']} week {trainingsweek['week']}")
    print(f"Doel: {doel_tekst(doel)}")
    if not doel["vast"]:
        print("LET OP: het weektarget staat nog niet in data/weekplanning/weektargets.csv (uren.py --zet-week "
              "op zondag)")

    kw = dict(vrij=vrij, hardlopen=hardlopen, afspraken=afspraken, vervalt=vervalt, aanpassen=aanpassen,
              opstaan=opstaan, werkelijk=werkelijk)
    doel_min = op_blok(round(doel["declarabel_doel"] * 60))
    week, weekconflicten = week_plannen(toewijzing, doel_min, **kw)
    # Herplannen tijdens de week: wat er van het doel over is, opnieuw verdeeld over de rest van de week.
    herplannen, gewerkt_min = invoer.get("herplannen"), 0
    if herplannen:
        vanaf = (date.fromisoformat(herplannen["vanaf"]) - maandag).days
        if not 0 <= vanaf < 7:
            raise ValueError(f"herplannen vanaf {herplannen['vanaf']} valt niet in de week van {maandag}")
        if vanaf and "gewerkt_uren" not in herplannen:
            raise ValueError("herplannen zonder gewerkt_uren: neem 'Gewerkt t/m' over uit uren.py --tot "
                             "<dag voor vanaf>")
        gewerkt_min = round(herplannen.get("gewerkt_uren", 0) * 60)
        rest_min = op_blok(max(0, round(doel["declarabel_doel"] * 60) - gewerkt_min))
        print(f"Herpland vanaf {VOLUIT[WEEKDAGEN[vanaf]]} {herplannen['vanaf']}: {gewerkt_min / 60:.2f} u gewerkt, "
              f"nog {rest_min / 60:.2f} u te gaan")
        vorige = week
        later_min = 0
        if vanaf:
            bed = next((b for b, act, _ in vorige[WEEKDAGEN[vanaf - 1]]["rij"] if act == "Naar bed"), None)
            later_min = max(0, bed - hhmm_naar_min(regels["naar_bed"])) if bed is not None else 0
        week, weekconflicten = week_plannen(toewijzing, rest_min, WEEKDAGEN[vanaf:], later_min=later_min, **kw)
        per_dag = {}
        if vanaf:
            # Van de voorbije dagen het declarabele werk uit LogMyTime, zoals uren.py het telt.
            try:
                from uren import haal_stand
                per_dag = haal_stand(datums["ma"], datums[WEEKDAGEN[vanaf - 1]])["per_dag"]
            except (Exception, SystemExit) as fout:  # zonder LogMyTime alleen het totaal uit het weekbestand
                print(f"LET OP: gewerkte uren per dag niet uit LogMyTime gehaald ({fout})")
                per_dag = None
        for dag in WEEKDAGEN[:vanaf]:
            week[dag] = {"rij": [], "voorbij": True, "gepland": 0, "ruimte": None, "notities": [], "conflicten": [],
                         "gewerkt": round(per_dag.get(datums[dag], 0) * 60) if per_dag is not None else None}
            # Herpland vanaf morgen: vandaag blijft zichtbaar, de avond ervan bepaalt het opstaan van morgen.
            if datums[dag] == date.today():
                week[dag]["vandaag"] = vorige[dag]
    for t in invoer.get("trainingsduur", []):
        week[t["dag"]]["notities"].insert(0, f"Hardlopen duurde {duur_tekst(t['duur_min'])}"
                                             + (f" ({t['reden']})" if "reden" in t else ""))
    week_tonen(week, toewijzing, dagsoorten, weekconflicten, datums, trainingen, doel, vrij_namen, gewerkt_min)
    if schrijf:
        notitie = notitie_schrijven(week, toewijzing, dagsoorten, weekconflicten, datums, trainingen, pad, doel,
                                    vrij_namen, herplannen, gewerkt_min)
        print(f"Geschreven naar {notitie.relative_to(VAULT)}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit(__doc__)
    week_uit_bestand(args[0], "--schrijf" in sys.argv)


if __name__ == "__main__":
    main()
