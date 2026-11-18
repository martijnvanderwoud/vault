#!/usr/bin/python3
"""Watcher van de autonome agents: ververst gebieden/agents/dashboard.md zodra een run-notitie wijzigt.

Draait altijd, onder launchd (scripts/agent-watcher/nl.crimsoncricket.agent-watcher.plist). Kijkt
elke paar seconden naar de `mtime` van de notities per agent (gebieden/agents/*.md), van hun
runmappen en van de notities daarin. Wijzigt er iets, dan draait hij agent_dashboard.py; ook elke
minuut, omdat `Stil` en de grens van 7 dagen van de tijd afhangen. Elke tik schrijft hij een
heartbeat in ~/.agent-watcher/, zodat het dashboard en de runner van Debbie zien als hij wegvalt.

Daarnaast, voor alle agents:
- een `running`-run waarvan het proces al even weg is, zet hij op `failed`
- elke paar minuten de state van de issues van runs die nog niet zijn afgehandeld in `issue_state`;
  staat het issue van een `paused`- of `failed`-run op Done, dan wordt de run `done`
- een macOS-melding bij `paused` of `failed` en bij nieuwe aandachtspunten. Wat hij gemeld heeft,
  staat in ~/.agent-watcher/gemeld.json, zodat een herstart niet alles opnieuw meldt.
Plan: gebieden/vault/agents-dashboard-plan.md.

    agent_watcher.py [--tik SECONDEN] [--eenmalig]
"""
import argparse
import json
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
BUILD_INDEX = Path(__file__).resolve().parent / 'build_index.py'
GEMELD = agentruns.WATCHER / 'gemeld.json'
TIK = 2  # seconden
ELKE_MINUUT = 60
YOUTRACK_ELKE = 180  # seconden
# Zo lang moet het proces weg zijn voor de run `failed` wordt. Na het einde van het proces heeft de
# runner even nodig om de log te lezen en de eindstatus te schrijven.
PROCES_WEG = 15  # seconden


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


def runs():
    """[(agent, path, fm)] van alle run-notities van alle agents."""
    result = []
    for naam, agent in agentruns.agents().items():
        for path in agentruns.notities(agent['runs'], naam):
            result.append((naam, path, agentruns.notitie_lezen(path, agent['lijsten'])[0]))
    return result


def bijwerken(agent, path, wijzig):
    """Leest de notitie vlak voor het schrijven opnieuw en laat `wijzig(fm, tekst)` beslissen: die geeft
    de nieuwe tekst, of None om niets te schrijven. Een run die loopt met een levend proces schrijft
    de watcher nooit. Zonder `volgorde`: de notitie houdt zijn velden en hun volgorde."""
    lijsten = agentruns.agents()[agent]['lijsten']
    fm, tekst = agentruns.notitie_lezen(path, lijsten)
    if fm.get('status') == 'running' and agentruns.proces_leeft(fm.get('pid'), proces(agent)):
        return False
    tekst = wijzig(fm, tekst)
    if tekst is None:
        return False
    if fm.get('agent') and fm.get('onderwerp') and fm.get('started') and fm.get('status'):
        fm['description'] = agentruns.beschrijving(fm)
    agentruns.notitie_schrijven(path, fm, tekst)
    return True


def proces(agent):
    """De naam van het proces achter `pid`, uit `proces` in de notitie van de agent, standaard claude."""
    return agentruns.agents().get(agent, {}).get('proces') or 'claude'


def nu_lokaal():
    return datetime.now().astimezone().replace(microsecond=0)


def processen_controleren(weg_sinds):
    """Zet een `running`-run op `failed` als zijn proces al PROCES_WEG seconden weg is. `weg_sinds`
    ({path: monotonic}) houdt bij sinds wanneer. Geeft True als er een notitie geschreven is."""
    geschreven, nu = False, time.monotonic()
    gezien = set()
    for agent, path, fm in runs():
        if fm.get('status') != 'running':
            continue
        if agentruns.proces_leeft(fm.get('pid'), proces(agent)):
            weg_sinds.pop(path, None)
            continue
        gezien.add(path)
        if nu - weg_sinds.setdefault(path, nu) < PROCES_WEG:
            continue

        def failed(fm, tekst, pid=fm.get('pid')):
            if fm.get('status') != 'running' or fm.get('pid') != pid:
                return None  # intussen door de runner geschreven
            fm['status'] = 'failed'
            fm['reason'] = 'run gestopt zonder status, runner of agent is afgebroken'
            fm['ended'] = nu_lokaal().isoformat()
            fm.pop('pid', None)
            return tekst

        if bijwerken(agent, path, failed):
            log('%s: running -> failed (proces %s weg)' % (path.stem, fm.get('pid')))
            geschreven = True
        weg_sinds.pop(path, None)
    for path in set(weg_sinds) - gezien:
        weg_sinds.pop(path)
    return geschreven


def youtrack_bijwerken():
    """Neemt de State van het issue over in `issue_state`, voor runs die niet lopen en nog niet zijn
    afgehandeld. Staat het issue van een `paused`- of `failed`-run op Done, dan wordt de run `done`.
    Geeft True als er een notitie geschreven is."""
    geschreven = False
    for agent, path, fm in runs():
        if not fm.get('issue') or fm.get('status') == 'running' or agentruns.afgehandeld(fm):
            continue
        try:
            state = agentruns.issue_state(fm['issue'])
        except Exception as e:  # noqa: BLE001 - netwerk of YouTrack: over een paar minuten opnieuw
            log('YouTrack %s niet te lezen: %s' % (fm['issue'], e))
            continue
        if not state:
            continue

        def overnemen(fm, tekst, issue=fm['issue']):
            if fm.get('issue') != issue or fm.get('status') == 'running' or agentruns.afgehandeld(fm):
                return None
            status = fm.get('status')
            klaar = status in ('paused', 'failed') and state == 'Done'
            if state == fm.get('issue_state') and not klaar:
                return None
            fm['issue_state'] = state
            if klaar:
                stap = ' bij stap %s' % fm['step'] if fm.get('step') else ''
                tekst += '\n\nOp `done` gezet op %s: na de %s%s (%s) staat %s op Done.\n' % (
                    nu_lokaal().isoformat(), status, stap, fm.get('reason') or '?', issue)
                for key in ('step', 'reason', 'resume'):
                    fm.pop(key, None)
                fm['status'] = 'done'
            return tekst

        if bijwerken(agent, path, overnemen):
            log('%s: issue %s -> %s (status was %s)' % (path.stem, fm.get('issue_state') or '?', state, fm.get('status')))
            geschreven = True
    return geschreven


def meldingen(gemeld):
    """Meldt runs die naar `paused` of `failed` gingen of nieuwe aandachtspunten hebben, en nog niet
    zijn afgehandeld. `gemeld` is {notitie: {status, aandacht}} van de vorige keer, of None bij de
    allereerste start: dan wordt alleen de stand vastgelegd. Geeft de nieuwe stand."""
    nu = {}
    for agent, path, fm in runs():
        sleutel = str(path.relative_to(agentruns.VAULT))
        aandacht = [str(a) for a in fm.get('aandacht') or []]
        nu[sleutel] = {'status': fm.get('status'), 'aandacht': aandacht}
        vorig = (gemeld or {}).get(sleutel)
        if gemeld is None or fm.get('status') == 'running' or agentruns.afgehandeld(fm):
            continue
        status = fm.get('status') if fm.get('status') in ('paused', 'failed') and \
            (vorig or {}).get('status') != fm.get('status') else None
        nieuw = [a for a in aandacht if a not in (vorig or {}).get('aandacht', [])]
        if not status and not nieuw:
            continue
        titel = '%s: %s %s' % (agent.capitalize(), fm.get('onderwerp') or path.stem, status or 'aandacht nodig')
        tekst = str(fm.get('reason') or '') if status else ''
        tekst = tekst or (nieuw[0] if nieuw else fm.get('issue') or '')
        log('melding: %s: %s' % (titel, tekst))
        agentruns.melden(titel, tekst)
    return nu


def gemeld_lezen():
    try:
        return json.loads(GEMELD.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def gemeld_schrijven(stand):
    agentruns.WATCHER.mkdir(exist_ok=True)
    agentruns.atomair_schrijven(GEMELD, json.dumps(stand, ensure_ascii=False, indent=1, sort_keys=True) + '\n')


def index_bijwerken():
    """De `description` van een run-notitie staat in index.md van zijn map."""
    subprocess.run([sys.executable, '-I', str(BUILD_INDEX)], check=False, capture_output=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--tik', type=float, default=TIK, help='seconden tussen twee keer kijken (standaard %(default)s)')
    parser.add_argument('--eenmalig', action='store_true', help='één keer kijken en het dashboard maken')
    args = parser.parse_args()
    log('watcher gestart (pid %d)' % os.getpid())
    vorige, laatst_gemaakt, laatst_youtrack = None, 0.0, None
    gemeld, weg_sinds = gemeld_lezen(), {}
    while True:
        # Elke taak een eigen try: een fout bij YouTrack of in een notitie mag het dashboard niet tegenhouden.
        geschreven = False
        try:
            agentruns.heartbeat_schrijven(datetime.now().astimezone())
        except Exception as e:  # noqa: BLE001 - de watcher moet blijven draaien
            log('fout bij heartbeat: %r' % e)
        try:
            geschreven |= processen_controleren(weg_sinds)
        except Exception as e:  # noqa: BLE001
            log('fout bij processen: %r' % e)
        if laatst_youtrack is None or time.monotonic() - laatst_youtrack >= YOUTRACK_ELKE:
            laatst_youtrack = time.monotonic()
            try:
                geschreven |= youtrack_bijwerken()
            except Exception as e:  # noqa: BLE001
                log('fout bij YouTrack: %r' % e)
        if geschreven:
            index_bijwerken()
        try:
            nu = stand()
            if nu != vorige:
                stand_meldingen = meldingen(gemeld)
                if stand_meldingen != gemeld:
                    gemeld_schrijven(stand_meldingen)
                    gemeld = stand_meldingen
                dashboard_maken('start' if vorige is None else 'wijziging')
                vorige, laatst_gemaakt = nu, time.monotonic()
            elif time.monotonic() - laatst_gemaakt >= ELKE_MINUUT:
                dashboard_maken('elke minuut')
                laatst_gemaakt = time.monotonic()
        except Exception as e:  # noqa: BLE001
            log('fout: %r' % e)
        if args.eenmalig:
            return
        time.sleep(args.tik)


if __name__ == '__main__':
    main()
