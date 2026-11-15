#!/usr/bin/env python3
"""Rekent de duur en afstand uit van de trainingen in een week.

Gebruik: python3 scripts/trainingsduur.py [data/hardlopen/trainingen/<week>.json]

Tempo's zijn percentages van het 5K-tempo uit data/hardlopen/tempos.json, als percentage van
tempo, niet van snelheid: doeltempo = 5K-tempo x (2 - p/100). Zie
https://apps.runningwritings.com/pace-percent/

Elke zone heeft een bandbreedte. De planning rekent met het midden; de langzame en de snelle kant
staan ernaast ter informatie.
"""
import json
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent
TEMPOS = VAULT / "data" / "hardlopen" / "tempos.json"
STANDAARD_WEEK = VAULT / "data" / "hardlopen" / "trainingen" / "wind-90-week-01.json"


def mmss_naar_s(tekst):
    m, s = tekst.split(":")
    return int(m) * 60 + int(s)


def s_naar_tekst(s):
    s = round(s)
    u, rest = divmod(s, 3600)
    m, s = divmod(rest, 60)
    return f"{u}:{m:02d}:{s:02d}" if u else f"{m}:{s:02d}"


class Tempos:
    def __init__(self, data):
        self.ref = mmss_naar_s(data["vijf_km_tempo"])
        self.zones = data["zones"]
        self.strides = data["strides"]

    def bereik(self, tempo):
        """Geeft (pct langzaam, pct snel) voor een zone, getal, [lo, hi] of {van, naar}."""
        if isinstance(tempo, str):
            lo, hi = self.zones[tempo]
            return lo, hi
        if isinstance(tempo, (int, float)):
            return tempo, tempo
        if isinstance(tempo, list):
            return tempo[0], tempo[1]
        # Lineair oplopend: het gemiddelde tempo hoort bij het gemiddelde percentage.
        van, naar = self.bereik(tempo["van"]), self.bereik(tempo["naar"])
        return (van[0] + naar[0]) / 2, (van[1] + naar[1]) / 2

    def tempo_s_per_km(self, pct):
        return self.ref * (2 - pct / 100)


def onderdelen_uitvouwen(onderdelen, tempos):
    """Maakt van herhalingen en strides een platte lijst van onderdelen."""
    plat = []
    for o in onderdelen:
        if "herhaal" in o:
            for i in range(o["herhaal"]):
                plat += onderdelen_uitvouwen(o["blok"], tempos)
                if i < o["herhaal"] - 1:
                    plat += onderdelen_uitvouwen(o.get("tussen", []), tempos)
        elif "strides" in o:
            n, st = o["strides"], tempos.strides
            for i in range(n):
                pct = st["eerste_pct"] + (st["laatste_pct"] - st["eerste_pct"]) * i / (n - 1)
                plat.append({"s": o["s"], "tempo": pct})
                # Herstel na elke stride, ook de laatste, zoals TrainingPeaks het opbouwt.
                plat.append({"s": st["herstel_s"], "tempo": st["herstel_tempo"]})
        else:
            plat.append(o)
    return plat


def training_rekenen(training, tempos):
    """Geeft voor het midden, de langzame en de snelle kant de afstand in km en de duur in seconden."""
    uitkomst = []
    for kies in (lambda lo, hi: (lo + hi) / 2, lambda lo, hi: lo, lambda lo, hi: hi):
        km = duur = 0.0
        for o in onderdelen_uitvouwen(training["onderdelen"], tempos):
            tempo = tempos.tempo_s_per_km(kies(*tempos.bereik(o["tempo"])))
            if "km" in o:
                km += o["km"]
                duur += o["km"] * tempo
            else:
                km += o["s"] / tempo
                duur += o["s"]
        uitkomst.append((km, duur))
    return uitkomst


def main():
    week_pad = Path(sys.argv[1]) if len(sys.argv) > 1 else STANDAARD_WEEK
    tempos = Tempos(json.loads(TEMPOS.read_text()))
    week = json.loads(week_pad.read_text())

    print(f"{week['plan']}, week {week['week']} ({week['fase']}), vanaf {week['start']}, "
          f"5K-tempo {s_naar_tekst(tempos.ref)}/km")
    print(f"{'dag':4} {'km':>6} {'duur':>8} {'langzaam':>9} {'snel':>8}  training")
    totaal_km = totaal_midden = totaal_langzaam = totaal_snel = 0.0
    for t in week["trainingen"]:
        (km, midden), (_, langzaam), (_, snel) = training_rekenen(t, tempos)
        totaal_km += km
        totaal_midden += midden
        totaal_langzaam += langzaam
        totaal_snel += snel
        print(f"{t['dag']:4} {km:6.1f} {s_naar_tekst(midden):>8} {s_naar_tekst(langzaam):>9} "
              f"{s_naar_tekst(snel):>8}  {t['omschrijving']}")
    print(f"{'week':4} {totaal_km:6.1f} {s_naar_tekst(totaal_midden):>8} {s_naar_tekst(totaal_langzaam):>9} "
          f"{s_naar_tekst(totaal_snel):>8}")
    print(f"Doel {week['doel_km']} km, verschil {totaal_km - week['doel_km']:+.1f} km")


if __name__ == "__main__":
    main()
