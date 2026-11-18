#!/usr/bin/python3
"""Watcher van de autonome agents: ververst gebieden/agents/dashboard.md zodra een run-notitie wijzigt.

Draait altijd, onder launchd (scripts/agent-watcher/nl.crimsoncricket.agent-watcher.plist). Kijkt
elke paar seconden naar de `mtime` van de notities per agent (gebieden/agents/*.md), van hun
runmappen en van de notities daarin. Wijzigt er iets, dan draait hij agent_dashboard.py; ook elke
minuut, omdat `Stil` en de grens van 7 dagen van de tijd afhangen. Elke tik schrijft hij een
heartbeat in ~/.agent-watcher/, zodat het dashboard en de runner van Debbie zien als hij wegvalt.
Plan: gebieden/vault/agents-dashboard-plan.md.

    agent_watcher.py [--tik SECONDEN] [--eenmalig]
"""
import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Met `python3 -I` (zoals onder launchd) staat de map van het script niet in sys.path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agentruns  # noqa: E402

DASHBOARD = Path(__file__).resolve().parent / 'agent_dashboard.py'
TIK = 2  # seconden
ELKE_MINUUT = 60


def mtime(path):
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return None


def stand():
    """De mtimes van alles waar het dashboard van afhangt. Een map zelf wijzigt bij een nieuw,
    verwijderd of hernoemd bestand (ook bij atomair schrijven), een notitie als Obsidian hem in
    place bewerkt. Bestanden met een punt ervoor (tijdelijke bestanden) tellen niet mee."""
    paden = [agentruns.AGENTS] + sorted(agentruns.AGENTS.glob('*.md'))
    try:
        mappen = [a['runs'] for a in agentruns.agents().values()]
    except (OSError, ValueError):  # een half bewerkte notitie per agent: de volgende tik opnieuw
        mappen = []
    for runs in mappen:
        paden += [runs] + sorted(runs.glob('*.md'))
    return {str(p): mtime(p) for p in paden if p.name != 'dashboard.md'}


def log(tekst):
    print('%s %s' % (datetime.now().astimezone().isoformat(timespec='seconds'), tekst), flush=True)


def dashboard_maken(reden):
    proc = subprocess.run([sys.executable, '-I', str(DASHBOARD)], capture_output=True, text=True)
    if proc.returncode:
        log('dashboard mislukt (%s): %s' % (reden, proc.stderr.strip().splitlines()[-1:] or proc.returncode))
    elif not proc.stdout.startswith('ongewijzigd'):
        log('dashboard %s (%s)' % (proc.stdout.split(':')[0], reden))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--tik', type=float, default=TIK, help='seconden tussen twee keer kijken (standaard %(default)s)')
    parser.add_argument('--eenmalig', action='store_true', help='één keer kijken en het dashboard maken')
    args = parser.parse_args()
    log('watcher gestart (pid %d)' % os.getpid())
    vorige, laatst_gemaakt = None, 0.0
    while True:
        try:
            agentruns.heartbeat_schrijven(datetime.now().astimezone())
            nu = stand()
            if nu != vorige:
                dashboard_maken('start' if vorige is None else 'wijziging')
                vorige, laatst_gemaakt = nu, time.monotonic()
            elif time.monotonic() - laatst_gemaakt >= ELKE_MINUUT:
                dashboard_maken('elke minuut')
                laatst_gemaakt = time.monotonic()
        except Exception as e:  # noqa: BLE001 - de watcher moet blijven draaien
            log('fout: %r' % e)
        if args.eenmalig:
            return
        time.sleep(args.tik)


if __name__ == '__main__':
    main()
