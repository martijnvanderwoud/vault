#!/usr/bin/env python3
"""Rekent een weekplanning door uit soorten dagen, weekdagen, trainingen en afspraken.

Gebruik: python3 scripts/weekplanning.py data/weekplanning/weken/<maandag>.json
         python3 scripts/weekplanning.py [--controleer]

Een dag = de blokken van de soort dag (data/weekplanning/dagsoorten.json) met de klusjes en de
avond van de weekdag (data/weekplanning/weekdagen.json) erbij. Werkblokken zijn 'vul' (tot het
volgende blok met een vaste tijd), een vast aantal uren, of 'rest' (wat er van het werkdoel van de
weekdag over is). Een vaste tijd is 'om' (kloktijd) of 'minstens_na' (minuten na een eerder blok).

Een week (data/weekplanning/weken/<maandag>.json) noemt de trainingsweek, de afspraken en de
urenstand. De soort dag per weekdag komt uit de trainingen (dagsoort), de duur van Hardlopen uit
trainingsduur.py, naar boven afgerond op een kwartier. Een afspraak (met reistijd en omschakelen
ervoor en erna) knipt het werkblok waar hij in valt; de werkdag loopt daardoor uit. Wat uitloopt
gaat eerst van de lucht af, dan van wat verder in wijkt_eerst staat (regels.json), en wat dan nog
over is van de lucht van de andere werkdagen.

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
            if "om" in b and t > anker:
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


def afspraak_tijden(afspraak):
    """Begin en einde van een afspraak met reistijd en omschakelen, en die marge."""
    marge = afspraak.get("reistijd_min", 0) + afspraak.get("omschakelen_min", 0)
    return hhmm_naar_min(afspraak["van"]) - marge, hhmm_naar_min(afspraak["tot"]) + marge, marge


def afspraak_invoegen(blokken, rij, afspraak):
    """Knipt het werkblok waar de afspraak (met reistijd en omschakelen) in valt. rij hoort bij blokken.

    Geeft None als de afspraak niet helemaal in één werkblok valt.
    """
    van, tot = hhmm_naar_min(afspraak["van"]), hhmm_naar_min(afspraak["tot"])
    begin_a, einde_a, marge = afspraak_tijden(afspraak)
    for i, (begin, _, werk) in enumerate(rij):
        if werk and begin <= begin_a and einde_a <= begin + werk:
            break
    else:
        return None

    b = blokken[i]
    voor = [{"activiteit": b["activiteit"], "werk": "vul"}] if begin_a > begin else []
    midden = [{"activiteit": afspraak["activiteit"], "om": afspraak["van"], "duur_min": tot - van}]
    if marge:
        midden = ([{"activiteit": "Reistijd en omschakelen", "om": min_naar_hhmm(begin_a), "duur_min": marge}]
                  + midden + [{"activiteit": "Reistijd en omschakelen", "duur_min": marge}])
    na_werk = b["werk"]
    if isinstance(na_werk, (int, float)):
        na_werk -= (begin_a - begin) / 60
    na = [{"activiteit": b["activiteit"], "werk": na_werk}] if na_werk else []
    return blokken[:i] + voor + midden + na + blokken[i + 1:]


def wijken(blokken, werkdoel, opstaan, einde, wijkt_eerst, notities):
    """Laat de werkdag niet langer duren dan einde (het einde van de lucht zonder afspraken).

    Wat uitloopt gaat van de lucht af, dan vervallen de blokken van de volgende soort in wijkt_eerst.
    Geeft de rij, de conflicten en het werk in minuten dat dan nog naar andere dagen moet.
    """
    lucht = next(b for b in blokken if b.get("soort") == "lucht")
    standaard = lucht["duur_min"]
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
            return rij, conflicten, 0
    lucht["duur_min"] = 0
    tekort = over - standaard
    rij, conflicten = dag_opbouwen(blokken, werkdoel - tekort, opstaan)
    return rij, conflicten, tekort


def klusjes_om(rij, weekdag, conflicten):
    """Klusjes met een vaste tijd splitsen het werkblok waar ze in vallen; de rest schuift door."""
    for k in weekdag["klusjes"]:
        if "om" not in k:
            continue
        om = hhmm_naar_min(k["om"])
        for i, (begin, act, werk) in enumerate(rij):
            if werk and begin < om < begin + werk:
                rij[i:i + 1] = [(begin, act, om - begin), (om, k["activiteit"], None),
                                (om + k["duur_min"], act, begin + werk - om)]
                rij[i + 3:] = [(b + k["duur_min"], a, w) for b, a, w in rij[i + 3:]]
                break
        else:
            conflicten.append(f"{k['activiteit']} om {k['om']} valt niet in een werkblok")
    return rij


def dag_plannen(dagsoort, weekdag, opstaan, wijkt_eerst, hardlopen_min=None, afspraken=()):
    """Geeft een dict met de rij, conflicten, notities en het tekort aan werk (min) voor andere dagen."""
    notities = []
    blokken = blokken_met_klusjes(dagsoort, weekdag, notities)
    if hardlopen_min:
        for b in blokken:
            if b.get("soort") == "training":
                b["duur_min"] = hardlopen_min
    werkdoel = round(weekdag["werkdoel_uren"] * 60)
    rij, conflicten = dag_opbouwen(blokken, werkdoel, opstaan)
    tekort, afspraak_conflicten = 0, []
    if afspraken:
        lucht = next(b for b in blokken if b.get("soort") == "lucht")
        einde = rij[blokken.index(lucht)][0] + lucht["duur_min"]
        for a in afspraken:
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
                begin_a, einde_a, _ = afspraak_tijden(a)
                geraakt = [act for k, (begin, act, _) in enumerate(rij)
                           if begin < einde_a and begin_a < einde_rij(rij, k)]
                afspraak_conflicten.append(
                    f"{a['activiteit']} {a['van']}-{a['tot']} (met reistijd {min_naar_hhmm(begin_a)}-"
                    f"{min_naar_hhmm(einde_a)}) valt niet in één werkblok: " + ", ".join(geraakt))
                continue
            if vervallen:
                notities.append(f"{', '.join(vervallen)} vervalt voor {a['activiteit']}")
            blokken = nieuw
            rij, conflicten = dag_opbouwen(blokken, werkdoel, opstaan)
        rij, conflicten, tekort = wijken(blokken, werkdoel, opstaan, einde, wijkt_eerst, notities)
    conflicten = afspraak_conflicten + conflicten
    rij = klusjes_om(rij, weekdag, conflicten)
    return {"rij": rij, "conflicten": conflicten, "notities": notities, "tekort": tekort}


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


def week_plannen(toewijzing, hardlopen=None, afspraken=None):
    dagsoorten, weekdagen, regels = lees("dagsoorten.json"), lees("weekdagen.json"), lees("regels.json")
    hardlopen, afspraken = hardlopen or {}, afspraken or {}
    opstaan = hhmm_naar_min(regels["opstaan"])
    week, weekconflicten = {}, []
    for dag in WEEKDAGEN:
        soort = dagsoorten[toewijzing[dag]]
        if soort.get("tijdsindeling", True):
            week[dag] = dag_plannen(soort, weekdagen[dag], opstaan, regels["wijkt_eerst"],
                                    hardlopen.get(dag), afspraken.get(dag, []))
        else:
            week[dag] = {"rij": [], "conflicten": [], "notities": [], "tekort": 0}

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
        ons = week[dag]["rij"]
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


def week_uit_bestand(pad):
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

    print(f"Week van {maandag:%d-%m-%Y}, trainingen {trainingsweek['plan']} week {trainingsweek['week']}")
    stand = invoer.get("vrij_na_reservering_uren")
    if stand is None:
        print("Urenstand: niet opgegeven")
    elif stand >= 0:
        print(f"Urenstand: {stand:.2f} u vrij na reservering, voor op target: lucht is voor inbox en "
              "kleine taken, later opstaan kan")
    else:
        print(f"Urenstand: {stand:.2f} u vrij na reservering, achter op target: lucht gebruiken om werk "
              "in te halen")

    week, dagsoorten, regels, weekconflicten = week_plannen(toewijzing, hardlopen, afspraken)
    week_tonen(week, toewijzing, dagsoorten, regels, weekconflicten, datums, trainingen)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        week_uit_bestand(args[0])
    else:
        excel_week("--controleer" in sys.argv)


if __name__ == "__main__":
    main()
