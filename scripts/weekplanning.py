#!/usr/bin/env python3
"""Bouwt dagen op uit soorten dagen en weekdagen, en rekent de week uit de Excel terug.

Gebruik: python3 scripts/weekplanning.py [--controleer]

Een dag = de blokken van de soort dag (data/weekplanning/dagsoorten.json) met de klusjes en de
avond van de weekdag (data/weekplanning/weekdagen.json) erbij. Werkblokken zijn 'vul' (tot het
volgende blok met een vaste tijd), een vast aantal uren, of 'rest' (wat er van het werkdoel van de
weekdag over is). De toewijzing van soorten dagen aan weekdagen staat in regels.json (excel_week).

Met --controleer vergelijkt het script de opgebouwde week met data/weekschema-excel-2026-11.csv.
"""
import csv
import json
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent
DATA = VAULT / "data" / "weekplanning"
EXCEL_CSV = VAULT / "data" / "weekschema-excel-2026-11.csv"
WEEKDAGEN = ["ma", "di", "wo", "do", "vr", "za", "zo"]
VOLUIT = dict(zip(WEEKDAGEN, ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag",
                              "zaterdag", "zondag"]))


def hhmm_naar_min(tekst):
    u, m = tekst.split(":")
    return int(u) * 60 + int(m)


def min_naar_hhmm(m):
    return f"{m // 60:02d}:{m % 60:02d}"


def blokken_met_klusjes(dagsoort, weekdag):
    """Zet de klusjes met 'na' en 'samen_met' tussen de blokken van de soort dag, en de avond erachter."""
    blokken = [dict(b) for b in dagsoort["blokken"]]
    for k in weekdag["klusjes"]:
        if "samen_met" in k:
            b = next(b for b in blokken if b["activiteit"] == k["samen_met"])
            b["activiteit"] += " en " + k["activiteit"]
        elif "na" in k:
            i = next(i for i, b in enumerate(blokken) if b["activiteit"] == k["na"])
            blokken.insert(i + 1, {"activiteit": k["activiteit"], "duur_min": k["duur_min"]})
    return blokken + [dict(b) for b in weekdag["avond"]]


def dag_opbouwen(dagsoort, weekdag, opstaan):
    """Geeft een lijst van (begin_min, activiteit, werkduur_min of None) en eventuele conflicten."""
    blokken = blokken_met_klusjes(dagsoort, weekdag)
    conflicten = []

    # Eerst de vaste en 'vul'-werkblokken op tijd zetten, zodat 'rest' weet wat er al is gewerkt.
    def tijden(blokken, rest_min):
        rij, t = [], opstaan
        for i, b in enumerate(blokken):
            if "om" in b:
                om = hhmm_naar_min(b["om"])
                if t > om:
                    conflicten.append(f"{b['activiteit']} om {b['om']}, maar het blok ervoor loopt tot "
                                      f"{min_naar_hhmm(t)}")
                t = max(t, om)
            if "werk" in b:
                if b["werk"] == "vul":
                    volgende = next(x for x in blokken[i + 1:] if "om" in x)
                    duur = max(0, hhmm_naar_min(volgende["om"]) - t)
                elif b["werk"] == "rest":
                    duur = rest_min
                else:
                    duur = round(b["werk"] * 60)
                rij.append((t, b["activiteit"], duur))
            else:
                duur = b.get("duur_min", 0)
                rij.append((t, b["activiteit"], None))
            t += duur
        return rij

    zonder_rest = tijden(blokken, 0)
    conflicten.clear()
    gewerkt = sum(w for _, _, w in zonder_rest if w)
    rest = round(weekdag["werkdoel_uren"] * 60) - gewerkt
    if rest < 0:
        conflicten.append(f"vaste werkblokken zijn {gewerkt / 60:.2f} u, meer dan het werkdoel")
        rest = 0
    rij = tijden(blokken, rest)

    # Klusjes met een vaste tijd splitsen het werkblok waar ze in vallen; de rest schuift door.
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
    return rij, conflicten


def week_opbouwen(toewijzing):
    dagsoorten = json.loads((DATA / "dagsoorten.json").read_text())
    weekdagen = json.loads((DATA / "weekdagen.json").read_text())
    regels = json.loads((DATA / "regels.json").read_text())
    opstaan = hhmm_naar_min(regels["opstaan"])
    week = {}
    for dag in WEEKDAGEN:
        soort = dagsoorten[toewijzing[dag]]
        if soort.get("tijdsindeling", True):
            week[dag] = dag_opbouwen(soort, weekdagen[dag], opstaan)
        else:
            week[dag] = ([], [])
    return week, dagsoorten


def excel_lezen():
    rijen = {}
    with EXCEL_CSV.open(newline="") as f:
        for r in csv.DictReader(f):
            werk = round(float(r["werkduur_uren"]) * 60) if r["werkduur_uren"] else None
            rijen.setdefault(r["dag"], []).append((hhmm_naar_min(r["begintijd"]), r["activiteit"], werk))
    return rijen


def main():
    regels = json.loads((DATA / "regels.json").read_text())
    toewijzing = regels["excel_week"]
    week, dagsoorten = week_opbouwen(toewijzing)

    totaal = 0
    for dag in WEEKDAGEN:
        rij, conflicten = week[dag]
        werk = sum(w for _, _, w in rij if w)
        totaal += werk
        print(f"\n{VOLUIT[dag]} ({toewijzing[dag]}), werk {werk / 60:.2f} u")
        if not rij:
            print(f"  {dagsoorten[toewijzing[dag]]['omschrijving']}")
        for begin, act, w in rij:
            print(f"  {min_naar_hhmm(begin)}  {act}" + (f"  [{w / 60:.2f} u]" if w else ""))
        for c in conflicten:
            print(f"  CONFLICT: {c}")
    print(f"\nWeek: {totaal / 60:.2f} u werk, doel {regels['werkdoel_week_uren']} u")

    if "--controleer" in sys.argv:
        excel = excel_lezen()
        verschillen = []
        for dag in WEEKDAGEN:
            ons = week[dag][0]
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


if __name__ == "__main__":
    main()
