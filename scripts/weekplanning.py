#!/usr/bin/env python3
"""Rekent een weekplanning door uit soorten dagen, weekdagen, trainingen en afspraken.

Gebruik: python3 scripts/weekplanning.py data/weekplanning/weken/<maandag>.json [--schrijf]
         python3 scripts/weekplanning.py [--controleer]

Een dag = de blokken van de soort dag (data/weekplanning/dagsoorten.json) met de klusjes en de
avond van de weekdag (data/weekplanning/weekdagen.json) erbij. Werkblokken zijn 'vul' (tot het
volgende blok met een vaste tijd), een vast aantal uren, of 'rest' (wat er van het werkdoel van de
weekdag over is). Een vaste tijd is 'om' (kloktijd) of 'minstens_na' (minuten na een eerder blok).

Een week (data/weekplanning/weken/<maandag>.json) noemt de trainingsweek, de afspraken en de
urenstand. De soort dag per weekdag komt uit de trainingen (dagsoort), de duur van Hardlopen uit
trainingsduur.py, naar boven afgerond op een kwartier. Een afspraak (met reistijd en omschakelen
ervoor en erna) knipt het werkblok waar hij in valt; de werkdag loopt daardoor uit. Wat uitloopt
gaat bij een voorsprong op target eerst van het werk af (de week mag tot de voorsprong onder het
werkdoel uitkomen), dan van de lucht, dan van wat verder in wijkt_eerst staat (regels.json), en wat dan nog
over is van de lucht van de andere werkdagen.

Met --schrijf komt de planning ook als notitie in gebieden/weekplanning/<maandag>.md.

Zonder weekbestand bouwt het script de week uit de Excel op (regels.json, excel_week, met de duur
van Hardlopen uit de Excel). Met --controleer vergelijkt het die met data/weekschema-excel-2026-11.csv.
"""
import csv
import json
import math
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trainingsduur import Tempos, s_naar_tekst, training_rekenen  # noqa: E402

VAULT = Path(__file__).resolve().parent.parent
DATA = VAULT / "data" / "weekplanning"
TRAININGEN = VAULT / "data" / "hardlopen" / "trainingen"
TEMPOS = VAULT / "data" / "hardlopen" / "tempos.json"
EXCEL_CSV = VAULT / "data" / "weekschema-excel-2026-11.csv"
NOTITIES = VAULT / "gebieden" / "weekplanning"
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
    return f"{m // 60}:{m % 60:02d}"


def lees(naam):
    return json.loads((DATA / naam).read_text())


def blokken_met_klusjes(dagsoort, weekdag, notities):
    """Zet de klusjes met 'na' en 'samen_met' tussen de blokken van de soort dag, en de avond erachter.

    Ontbreekt het blok waar een klusje aan vastzit op deze soort dag, dan komt het klusje voor de lucht.
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
                i = next(i for i, b in enumerate(blokken) if b.get("soort") == "lucht")
                notities.append(f"{k['activiteit']}: geen '{k['na']}' op deze soort dag, staat voor de lucht")
            blokken.insert(i, {"activiteit": k["activiteit"], "duur_min": k["duur_min"]})
    return blokken + [dict(b) for b in weekdag["avond"]]


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


def tijden(blokken, opstaan, rest_min, conflicten):
    """Zet de blokken op tijd. Geeft per blok (begin_min, activiteit, werkduur_min of None)."""
    rij, t, eind = [], opstaan, {}
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
            rij.append((t, b["activiteit"], duur))
        else:
            duur = b.get("duur_min", 0)
            rij.append((t, b["activiteit"], None))
        t += duur
        eind[b["activiteit"]] = t
    return rij


def dag_opbouwen(blokken, werkdoel_min, opstaan):
    """Geeft de blokken op tijd, met 'rest' zo dat het werkdoel gehaald wordt, en eventuele conflicten."""
    conflicten = []
    gewerkt = sum(w for _, _, w in tijden(blokken, opstaan, 0, []) if w)
    rest = werkdoel_min - gewerkt
    if rest < 0:
        conflicten.append(f"vaste werkblokken zijn {gewerkt / 60:.2f} u, meer dan het werkdoel")
        rest = 0
    return tijden(blokken, opstaan, rest, conflicten), conflicten


def einde_rij(rij, k):
    """Einde van rij k: het begin van de volgende rij (de laatste rij heeft geen einde)."""
    return rij[k + 1][0] if k + 1 < len(rij) else rij[k][0]


def afspraak_marges(afspraak):
    """Minuten voor en na een afspraak: reistijd (terug: reistijd_terug_min als die er is) en omschakelen."""
    heen = afspraak.get("reistijd_min", 0)
    terug = afspraak.get("reistijd_terug_min", heen)
    omschakelen = afspraak.get("omschakelen_min", 0)
    return heen + omschakelen, terug + omschakelen


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


def afspraak_invoegen(blokken, rij, afspraak, heel=True):
    """Knipt het werkblok waar de afspraak (met reistijd en omschakelen) in valt. rij hoort bij blokken.

    Geeft None als de afspraak niet helemaal in één werkblok valt (met heel=False: als het begin niet
    in een werkblok valt; zo werken klusjes met een vaste tijd).
    """
    begin_a, einde_a = afspraak_tijden(afspraak)
    for i, (begin, _, werk) in enumerate(rij):
        if werk and begin <= begin_a < begin + werk and (not heel or einde_a <= begin + werk):
            break
    else:
        return None

    b = blokken[i]
    voor = [{"activiteit": b["activiteit"], "werk": "vul"}] if begin_a > begin else []
    midden = afspraak_blokken(afspraak)
    na_werk = b["werk"]
    if isinstance(na_werk, (int, float)):
        na_werk -= (begin_a - begin) / 60
    na = [{"activiteit": b["activiteit"], "werk": na_werk}] if na_werk else []
    return blokken[:i] + voor + midden + na + blokken[i + 1:]


def wijken(blokken, werkdoel, opstaan, einde, wijkt_eerst, notities, voorsprong=0):
    """Laat de werkdag niet langer duren dan einde (het einde van de lucht zonder afspraken).

    Wat uitloopt gaat eerst van de voorsprong op target af (minder werken, tot voorsprong minuten), dan
    van de lucht, dan vervallen de blokken van de volgende soort in wijkt_eerst. Geeft de blokken, de
    rij, de conflicten, het werk in minuten dat dan nog naar andere dagen moet en het werkdoel van de dag.
    """
    lucht = next(b for b in blokken if b.get("soort") == "lucht")
    standaard = lucht["duur_min"]
    rij, _ = dag_opbouwen(blokken, werkdoel, opstaan)
    minder = min(max(0, rij[blokken.index(lucht)][0] + standaard - einde), voorsprong)
    if minder:
        werkdoel -= minder
        notities.append(f"{minder} min minder werk, van de voorsprong op target")
    for soort in wijkt_eerst:
        if soort != "lucht":
            weg = [b["activiteit"] for b in blokken if b.get("soort") == soort]
            if not weg:
                continue
            blokken = [b for b in blokken if b.get("soort") != soort]
            notities.append(f"{', '.join(weg)} vervalt")
        lucht["duur_min"] = standaard
        rij, conflicten = dag_opbouwen(blokken, werkdoel, opstaan)
        i = blokken.index(lucht)
        over = rij[i][0] + standaard - einde
        if over <= standaard:
            lucht["duur_min"] = standaard - max(0, over)
            rij, conflicten = dag_opbouwen(blokken, werkdoel, opstaan)
            return blokken, rij, conflicten, 0, werkdoel
    lucht["duur_min"] = 0
    tekort = over - standaard
    rij, conflicten = dag_opbouwen(blokken, werkdoel - tekort, opstaan)
    return blokken, rij, conflicten, tekort, werkdoel - tekort


def avond_invoegen(blokken, rij, afspraak, notities):
    """Zet een afspraak na de lucht tussen de avondblokken, op zijn eigen tijd.

    Avondblokken die voor de afspraak (met reistijd en omschakelen) niet meer af zijn, gaan naar een
    vrij gat voor een blok met een vaste tijd, en anders na de afspraak. Blokken met een vaste tijd
    voor de afspraak (zoals eten) blijven ervoor en geven zo nodig een conflict. Na de afspraak geen
    downtime: klaarmaken voor bed en dan naar bed, ook als dat later is dan de bedtijd. Een afspraak
    thuis ('thuis': true) loopt hooguit tot de bedtijd, en dan gewoon naar bed.
    """
    begin_a, _ = afspraak_tijden(afspraak)
    li = next(i for i, b in enumerate(blokken) if b.get("soort") == "lucht")
    avond = blokken[li + 1:]
    tijd = dict(zip(map(id, blokken), (r[0] for r in rij)))
    ervoor = [b for b in avond if "om" in b and hhmm_naar_min(b["om"]) < begin_a
              or "om" not in b and "duur_min" in b and tijd[id(b)] + b["duur_min"] <= begin_a]
    verplaatst = [b for b in avond if b not in ervoor and "om" not in b and "duur_min" in b]
    erna = []
    for b in avond:
        if b in ervoor or b in verplaatst or "duur_min" not in b and "om" not in b:
            continue
        if b.get("soort") == "bed" and not afspraak.get("thuis"):
            erna.append({"activiteit": "Klaarmaken voor bed", "duur_min": b["klaarmaken_min"]})
            b = {k: v for k, v in b.items() if k != "om"}
        erna.append(b)

    # Verplaatste blokken in een gat voor een vast blok zetten, zolang ze passen.
    nieuw, t, vroeger = [], rij[li][0] + blokken[li]["duur_min"], []
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
        bed = next((b["om"] for b in erna if b.get("soort") == "bed"), None)
        if bed and hhmm_naar_min(afspraak["tot"]) > hhmm_naar_min(bed):
            notities.append(f"{afspraak['activiteit']} staat tot {afspraak['tot']} in de agenda, "
                            f"naar bed op de normale tijd ({bed})")
            afspraak = afspraak | {"tot": bed}
    return blokken[:li + 1] + nieuw + afspraak_blokken(afspraak) + verplaatst + erna


def vrij_invoegen(rij, blokken):
    """Zet 'Vrij' in de gaten voor blokken met een vaste tijd en voegt aansluitend werk samen.

    rij hoort bij blokken.
    """
    uit = []
    for k, (begin, act, werk) in enumerate(rij):
        if werk and uit and uit[-1][1] == act and uit[-1][2] and uit[-1][0] + uit[-1][2] == begin:
            uit[-1] = (uit[-1][0], act, uit[-1][2] + werk)
        elif werk != 0:
            uit.append((begin, act, werk))
        einde = begin + (werk if werk is not None else blokken[k].get("duur_min", 0))
        if k + 1 < len(rij) and rij[k + 1][0] > einde and "duur_min" in blokken[k]:
            uit.append((einde, "Vrij", None))
    return uit


def dag_plannen(dagsoort, weekdag, regels, hardlopen_min=None, afspraken=(), vervalt=(), aanpassen=(),
                opstaan_dag=None, voorsprong=0):
    """Geeft een dict met de rij, conflicten, notities en het tekort aan werk (min) voor andere dagen.

    Met opstaan_dag (later opstaan) loopt de dag uit; dat gaat net als bij een afspraak van de lucht af.
    voorsprong: minuten voorsprong op target die deze dag mogen opgaan aan minder werken.
    """
    notities, conflicten_vast = [], []
    opstaan, wijkt_eerst = hhmm_naar_min(regels["opstaan"]), regels["wijkt_eerst"]
    blokken = blokken_met_klusjes(dagsoort, weekdag, notities)
    blokken.append({"activiteit": "Naar bed", "soort": "bed", "om": regels["naar_bed"], "duur_min": 0,
                    "klaarmaken_min": regels["klaarmaken_voor_bed_min"]})
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
    if hardlopen_min:
        for b in blokken:
            if b.get("soort") == "training":
                b["duur_min"] = hardlopen_min
    werkdoel = round(weekdag["werkdoel_uren"] * 60)
    rij, conflicten = dag_opbouwen(blokken, werkdoel, opstaan)

    # Klusjes met een vaste tijd knippen het werkblok waar ze in beginnen; de werkdag loopt uit.
    for k in weekdag["klusjes"]:
        if "om" not in k:
            continue
        klusje = {"activiteit": k["activiteit"], "van": k["om"],
                  "tot": min_naar_hhmm(hhmm_naar_min(k["om"]) + k["duur_min"])}
        nieuw = afspraak_invoegen(blokken, rij, klusje, heel=False)
        if nieuw is None:
            conflicten_vast.append(f"{k['activiteit']} om {k['om']} valt niet in een werkblok")
            continue
        blokken = nieuw
        rij, conflicten = dag_opbouwen(blokken, werkdoel, opstaan)

    tekort = minder = 0
    lucht = next(b for b in blokken if b.get("soort") == "lucht")
    einde = rij[blokken.index(lucht)][0] + lucht["duur_min"]
    # Vrije tijd voor het eerste vaste avondblok (zoals eten) mag de werkdag ook opmaken.
    ertussen = 0
    for b in blokken[blokken.index(lucht) + 1:]:
        if "om" in b:
            einde = max(einde, hhmm_naar_min(b["om"]) - ertussen)
            break
        ertussen += b.get("duur_min", 0)
    later =opstaan_dag is not None and hhmm_naar_min(opstaan_dag) > opstaan
    if later:
        notities.append(f"op om {opstaan_dag}")
        opstaan = hhmm_naar_min(opstaan_dag)
        rij, conflicten = dag_opbouwen(blokken, werkdoel, opstaan)
    if afspraken or later:
        overdag = [a for a in afspraken if afspraak_tijden(a)[0] < einde]
        for a in overdag:
            # Past de afspraak niet in een werkblok, dan vervallen eerst de blokken uit wijkt_eerst.
            wijkbaar = [s for s in wijkt_eerst if s != "lucht"]
            proef, proefrij, vervallen = blokken, rij, []
            while (nieuw := afspraak_invoegen(proef, proefrij, a)) is None and wijkbaar:
                soort = wijkbaar.pop(0)
                weg = [b["activiteit"] for b in proef if b.get("soort") == soort]
                if weg:
                    proef = [b for b in proef if b.get("soort") != soort]
                    vervallen += weg
                    proefrij, _ = dag_opbouwen(proef, werkdoel, opstaan)
            if nieuw is None:
                begin_a, einde_a = afspraak_tijden(a)
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
        if overdag or later:
            doel = werkdoel
            blokken, rij, conflicten, tekort, werkdoel = wijken(blokken, werkdoel, opstaan, einde, wijkt_eerst,
                                                                 notities, voorsprong)
            minder = doel - werkdoel - tekort
        for a in afspraken:
            if a not in overdag:
                blokken = avond_invoegen(blokken, rij, a, notities)
                rij, conflicten = dag_opbouwen(blokken, werkdoel, opstaan)
    return {"rij": vrij_invoegen(rij, blokken), "conflicten": conflicten_vast + conflicten,
            "notities": notities, "tekort": tekort, "minder": minder}


def lucht_inzetten(plan, max_min):
    """Zet lucht om in werk om in te halen, tot max_min. Geeft het aantal minuten."""
    rij = plan["rij"]
    for k, (begin, act, _) in enumerate(rij):
        if act == "Lucht":
            x = min(einde_rij(rij, k) - begin, max_min)
            if x > 0:
                rij[k:k + 1] = [(begin, "Werken (inhalen)", x), (begin + x, "Lucht", None)]
            return x
    return 0


def week_plannen(toewijzing, hardlopen=None, afspraken=None, vervalt=None, aanpassen=None, opstaan=None,
                 voorsprong_min=0):
    """voorsprong_min: voorsprong op target; zoveel mag de week onder het werkdoel uitkomen."""
    dagsoorten, weekdagen, regels = lees("dagsoorten.json"), lees("weekdagen.json"), lees("regels.json")
    hardlopen, afspraken = hardlopen or {}, afspraken or {}
    vervalt, aanpassen, opstaan = vervalt or {}, aanpassen or {}, opstaan or {}
    week, weekconflicten = {}, []
    naar_bed, opstaan_std = hhmm_naar_min(regels["naar_bed"]), hhmm_naar_min(regels["opstaan"])
    later_min = 0
    for dag in WEEKDAGEN:
        soort = dagsoorten[toewijzing[dag]]
        # Elk (begonnen) kwartier later naar bed dan normaal is een kwartier later opstaan.
        if later_min and dag not in opstaan:
            opstaan[dag] = min_naar_hhmm(opstaan_std + math.ceil(later_min / 15) * 15)
        if soort.get("tijdsindeling", True):
            week[dag] = dag_plannen(soort, weekdagen[dag], regels, hardlopen.get(dag), afspraken.get(dag, []),
                                    vervalt.get(dag, []), aanpassen.get(dag, []), opstaan.get(dag),
                                    voorsprong_min)
            voorsprong_min -= week[dag]["minder"]
        else:
            notities = [f"afspraak {a['activiteit']} {a['van']}-{a['tot']}, training en kracht eromheen"
                        for a in afspraken.get(dag, [])]
            week[dag] = {"rij": [], "conflicten": [], "notities": notities, "tekort": 0, "minder": 0}
        bed = next((begin for begin, act, _ in week[dag]["rij"] if act == "Naar bed"), None)
        later_min = max(0, bed - naar_bed) if bed is not None else 0
        if later_min:
            week[dag]["notities"].append(f"{later_min} min later naar bed dan normaal, morgen later op")

    # Werk dat niet op de eigen dag past, gaat van de lucht van de andere werkdagen (eerst de latere).
    for i, dag in enumerate(WEEKDAGEN):
        tekort = week[dag]["tekort"]
        if not tekort:
            continue
        for ander in WEEKDAGEN[i + 1:] + WEEKDAGEN[:i]:
            x = lucht_inzetten(week[ander], tekort)
            if x:
                week[ander]["notities"].append(f"{x} min lucht om werk van {VOLUIT[dag]} in te halen")
                week[dag]["notities"].append(f"{x} min werk ingehaald op {VOLUIT[ander]}")
                tekort -= x
            if not tekort:
                break
        if tekort:
            weekconflicten.append(f"{tekort} min werk van {VOLUIT[dag]} past nergens in de lucht")
    return week, dagsoorten, regels, weekconflicten


def lucht_min(rij):
    return sum(einde_rij(rij, k) - begin for k, (begin, act, _) in enumerate(rij) if act == "Lucht")


def week_tonen(week, toewijzing, dagsoorten, regels, weekconflicten, datums=None, trainingen=None):
    datums, trainingen = datums or {}, trainingen or {}
    totaal_werk = totaal_lucht = 0
    for dag in WEEKDAGEN:
        plan = week[dag]
        rij = plan["rij"]
        werk, lucht = sum(w for _, _, w in rij if w), lucht_min(rij)
        totaal_werk += werk
        totaal_lucht += lucht
        datum = f" {datums[dag]:%d-%m}" if dag in datums else ""
        print(f"\n{VOLUIT[dag]}{datum} ({toewijzing[dag]}), werk {werk / 60:.2f} u, lucht {duur_tekst(lucht)}")
        if dag in trainingen:
            t, km, duur_s, gepland = trainingen[dag]
            print(f"  Training: {t['omschrijving']} ({km:.1f} km, {s_naar_tekst(duur_s)}, "
                  f"gepland {duur_tekst(gepland)})")
        if not rij:
            print(f"  {dagsoorten[toewijzing[dag]]['omschrijving']}")
        for k, (begin, act, w) in enumerate(rij):
            if act == "Lucht" and einde_rij(rij, k) == begin:
                continue
            print(f"  {min_naar_hhmm(begin)}  {act}" + (f"  [{w / 60:.2f} u]" if w else ""))
        for n in plan["notities"]:
            print(f"  LET OP: {n}")
        for c in plan["conflicten"]:
            print(f"  CONFLICT: {c}")
    print(f"\nWeek: {totaal_werk / 60:.2f} u werk, doel {regels['werkdoel_week_uren']} u, "
          f"lucht {duur_tekst(totaal_lucht)}")
    for c in weekconflicten:
        print(f"CONFLICT: {c}")
    return totaal_werk


def urenstand_tekst(stand):
    if stand is None:
        return "niet opgegeven"
    if stand >= 0:
        return (f"{stand:.2f} u vrij na reservering, voor op target: lucht is voor inbox en kleine taken, "
                "later opstaan kan")
    return f"{stand:.2f} u vrij na reservering, achter op target: lucht gebruiken om werk in te halen"


def notitie_schrijven(week, toewijzing, dagsoorten, regels, weekconflicten, datums, trainingen, invoer_pad,
                      urenstand):
    """Schrijft de planning als Markdown-notitie naar gebieden/weekplanning/<maandag>.md."""
    def datum_tekst(d):
        return f"{d.day} {MAANDEN[d.month - 1]}"

    maandag, zondag = datums["ma"], datums["zo"]
    periode = (f"{maandag.day} t/m {datum_tekst(zondag)}" if maandag.month == zondag.month
               else f"{datum_tekst(maandag)} t/m {datum_tekst(zondag)}")
    totaal_werk = sum(w for d in WEEKDAGEN for _, _, w in week[d]["rij"] if w)
    totaal_lucht = sum(lucht_min(week[d]["rij"]) for d in WEEKDAGEN)
    try:
        bron = Path(invoer_pad).resolve().relative_to(VAULT)
    except ValueError:
        bron = Path(invoer_pad)
    regels_md = [
        "---",
        f"description: Weekplanning van {periode} {zondag.year}, "
        "per dag met tijden, training, werkuren en lucht",
        "tags: [weekplanning]",
        "---",
        "",
        f"# Weekplanning {periode} {zondag.year}",
        "",
        f"> Gegenereerd door `scripts/weekplanning.py --schrijf` uit `{bron}`. Niet met de hand",
        "> bewerken: wijzigingen gaan via het weekbestand. Achtergrond: [[weekplanning-plan]].",
        "",
        f"**Werk** {duur_tekst(totaal_werk)} u (doel {regels['werkdoel_week_uren']} u) · "
        f"**lucht** {duur_tekst(totaal_lucht)} · **urenstand** {urenstand_tekst(urenstand).replace('.', ',')}",
        "",
    ]
    minder = sum(week[d]["minder"] for d in WEEKDAGEN)
    if minder:
        regels_md += [f"{duur_tekst(minder)} u onder het doel, van de voorsprong op target "
                      f"({duur_tekst(round(urenstand * 60))} u): zo blijven lucht en stabiliteitsroutines staan.", ""]
    regels_md += [
        "| Dag | Soort | Training | Op | Werk | Lucht |",
        "|---|---|---|---|---:|---:|",
    ]
    for dag in WEEKDAGEN:
        rij = week[dag]["rij"]
        werk = sum(w for _, _, w in rij if w)
        training = ""
        if dag in trainingen:
            tr, km, _, gepland = trainingen[dag]
            training = f"{km:.0f} km, {duur_tekst(gepland)}"
        op = min_naar_hhmm(rij[0][0]) if rij else ""
        regels_md.append(f"| {VOLUIT[dag]} {datums[dag].day} | {dagsoorten[toewijzing[dag]]['naam']} | {training} "
                         f"| {op} | {duur_tekst(werk) if werk else ''} | {duur_tekst(lucht_min(rij)) if rij else ''} |")
    for c in weekconflicten:
        regels_md += ["", f"**Conflict:** {c}"]

    for dag in WEEKDAGEN:
        plan, rij = week[dag], week[dag]["rij"]
        regels_md += ["", f"## {VOLUIT[dag].capitalize()} {datum_tekst(datums[dag])}: "
                          f"{dagsoorten[toewijzing[dag]]['naam'].lower()}", ""]
        if dag in trainingen:
            tr, km, duur_s, gepland = trainingen[dag]
            regels_md += [f"Training: {tr['omschrijving']} ({km:.1f} km, {s_naar_tekst(duur_s)}, gepland "
                          f"{duur_tekst(gepland)}).", ""]
        if rij:
            regels_md += ["| Tijd | Activiteit | Werk |", "|---|---|---:|"]
            for k, (begin, act, w) in enumerate(rij):
                if act == "Lucht" and einde_rij(rij, k) == begin:
                    continue
                naam = f"**{act}**" if w else act
                regels_md.append(f"| {min_naar_hhmm(begin)} | {naam} | {duur_tekst(w) if w else ''} |")
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


def excel_lezen():
    rijen = {}
    with EXCEL_CSV.open(newline="") as f:
        for r in csv.DictReader(f):
            werk = round(float(r["werkduur_uren"]) * 60) if r["werkduur_uren"] else None
            rijen.setdefault(r["dag"], []).append((hhmm_naar_min(r["begintijd"]), r["activiteit"], werk))
    return rijen


def excel_week(controleer):
    toewijzing = lees("regels.json")["excel_week"]
    week, dagsoorten, regels, weekconflicten = week_plannen(toewijzing)
    week_tonen(week, toewijzing, dagsoorten, regels, weekconflicten)
    if not controleer:
        return
    excel = excel_lezen()
    verschillen = []
    for dag in WEEKDAGEN:
        ons = [r for r in week[dag]["rij"] if r[1] != "Naar bed"]
        hun = excel.get(VOLUIT[dag], [])
        for i in range(max(len(ons), len(hun))):
            a = ons[i] if i < len(ons) else None
            b = hun[i] if i < len(hun) else None
            if a != b:
                verschillen.append(f"{VOLUIT[dag]} regel {i + 1}: data {a}, Excel {b}")
    excel_werk = sum(w for rij in excel.values() for _, _, w in rij if w)
    print(f"Excel: {excel_werk / 60:.2f} u werk")
    if verschillen:
        print("\n".join(["VERSCHILLEN met de Excel:"] + verschillen))
        sys.exit(1)
    print("Gelijk aan de Excel: alle begintijden, activiteiten en werkuren.")


def week_uit_bestand(pad, schrijf=False):
    invoer = json.loads(Path(pad).read_text())
    maandag = date.fromisoformat(invoer["maandag"])
    datums = {dag: maandag + timedelta(days=i) for i, dag in enumerate(WEEKDAGEN)}
    trainingsweek = json.loads((TRAININGEN / invoer["trainingen"]).read_text())
    tempos = Tempos(json.loads(TEMPOS.read_text()))

    toewijzing = {dag: "rust" for dag in WEEKDAGEN}
    hardlopen, trainingen = {}, {}
    for t in trainingsweek["trainingen"]:
        (km, duur_s), _, _ = training_rekenen(t, tempos)
        toewijzing[t["dag"]] = t["dagsoort"]
        hardlopen[t["dag"]] = math.ceil(duur_s / 900) * 15
        trainingen[t["dag"]] = (t, km, duur_s, hardlopen[t["dag"]])
    afspraken = {}
    for a in invoer["afspraken"]:
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

    print(f"Week van {maandag:%d-%m-%Y}, trainingen {trainingsweek['plan']} week {trainingsweek['week']}")
    stand = invoer.get("vrij_na_reservering_uren")
    print(f"Urenstand: {urenstand_tekst(stand)}")

    week, dagsoorten, regels, weekconflicten = week_plannen(toewijzing, hardlopen, afspraken, vervalt, aanpassen, opstaan,
                                                           max(0, round((stand or 0) * 60)))
    week_tonen(week, toewijzing, dagsoorten, regels, weekconflicten, datums, trainingen)
    minder = sum(week[d]["minder"] for d in WEEKDAGEN)
    if minder:
        print(f"{duur_tekst(minder)} u onder het doel, van de voorsprong op target ({duur_tekst(round(stand * 60))} u)")
    if schrijf:
        notitie = notitie_schrijven(week, toewijzing, dagsoorten, regels, weekconflicten, datums, trainingen,
                                    pad, stand)
        print(f"Geschreven naar {notitie.relative_to(VAULT)}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        week_uit_bestand(args[0], "--schrijf" in sys.argv)
    else:
        excel_week("--controleer" in sys.argv)


if __name__ == "__main__":
    main()
