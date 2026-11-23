#!/usr/bin/python3
"""Runner van Fien: archiveert elke maandag de LogMyTime-taken waarvan het issue af is.

Draait het plan en archiveert met logmytime_taken_archiveren.py (hooguit --max taken, standaard
100), zonder model. Plan: gebieden/vault/logmytime-taken-archiveren-plan.md.

    fien_runner.py [--dry-run] [--max N]

Voor het agents-dashboard schrijft de runner per run een run-notitie in
gebieden/werk/logmytime-archiveren/runs/ (gebieden/agents/agent-runs.md), één per week
(`fien-<jaar>-w<week>.md`, onderwerp `taken`): bij de start `running`, aan het eind `done` of
`failed`. Aandachtspunten zijn alleen de taken die door `--max` of een fout blijven liggen en de
taken met een issue-ID dat YouTrack niet kent. Gearchiveerde taken en taken zonder issue-ID staan
alleen in de tekst. Zonder aandachtspunten wacht de run niet op mij. De melding komt van de watcher.
Een tweede run in dezelfde week schrijft dezelfde notitie opnieuw.

`--dry-run` toont alleen het plan, zonder run-notitie en zonder te archiveren. launchd start de
runner elke maandag om 8:00 (scripts/fien/nl.crimsoncricket.fien.plist). Log in ~/.fien/logs/.
Draai met /usr/bin/python3: de pyenv-python3 heeft geen SSL.
"""
import argparse
import os
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path

# Met `python3 -I` (zoals onder launchd) staat de map van het script niet in sys.path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agentruns  # noqa: E402
import logmytime_taken_archiveren as archief  # noqa: E402

VAULT = Path(__file__).resolve().parent.parent
RUNS = VAULT / 'gebieden/werk/logmytime-archiveren/runs'
VELDEN = ('description', 'agent', 'onderwerp', 'status', 'started', 'ended', 'reason', 'step', 'aandacht',
          'resume', 'pid', 'gearchiveerd', 'wacht', 'open')
RESUME = 'launchctl kickstart gui/$(id -u)/nl.crimsoncricket.fien'
ONDERWERP = 'taken'


def nu_lokaal():
    return datetime.now().astimezone().replace(microsecond=0)


def run_schrijven(path, velden, tekst):
    """Schrijft de run-notitie. Velden met `None` vallen weg."""
    fm = {k: v for k, v in dict({'agent': 'fien', 'onderwerp': ONDERWERP, 'aandacht': []}, **velden).items()
          if v is not None}
    fm['description'] = agentruns.beschrijving(fm)
    agentruns.notitie_schrijven(path, fm, tekst, VELDEN)


def lijst(regels, leeg='geen'):
    return '\n'.join('- %s%s' % (naam, ' (%s)' % toelichting if toelichting else '')
                     for _, naam, toelichting, _ in regels) or '- %s' % leeg


def verslag(moment, aantal, grens, regels, zonder_id, gedaan, maximum, fout):
    delen = ['# Fien: %s' % moment.date().isoformat(), '',
             'Run van %s. Actieve taken vooraf: %d, grens %s (opgelost op of vóór de grens en daarna niet '
             'meer gelogd). Plan en criterium: [[logmytime-taken-archiveren-plan]].' % (
                 moment.isoformat(), aantal, grens.strftime('%d-%m-%Y'))]
    if fout:
        delen += ['', '**Mislukt:** %s' % fout]
    delen += ['', '## Gearchiveerd (%d)' % len(gedaan), '', lijst(gedaan),
              '', 'Terugzetten: in LogMyTime de taak weer actief maken.']
    over = regels['archiveren'][len(gedaan):]
    if over:
        delen += ['', '## Blijven liggen (%d, %s)' % (len(over), 'door de fout' if fout else '--max %d' % maximum),
                  '', lijst(over)]
    if regels['niet gevonden']:
        delen += ['', '## Issue niet gevonden (%d)' % len(regels['niet gevonden']), '', lijst(regels['niet gevonden'])]
    if zonder_id:
        delen += ['', '## Zonder issue-ID (%d)' % len(zonder_id), '', '\n'.join('- %s' % n for n in zonder_id)]
    delen += ['', '## Wacht (%d)' % len(regels['wacht']), '',
              'Opgelost, maar korter dan 7 dagen geleden of recent nog gelogd.', '', lijst(regels['wacht']),
              '', '## Open (%d)' % len(regels['open']), '', lijst(regels['open']),
              '', 'De runner schrijft deze notitie; zie [[fien]].']
    return '\n'.join(delen) + '\n'


def aandacht(regels, gedaan, fout):
    """Alleen wat iets van mij vraagt. `niet gevonden` bevat alleen taken met een issue-ID vooraan
    (de titel suggereert een YouTrack-issue); taken zonder ID en gearchiveerde taken zijn verwacht."""
    over = regels['archiveren'][len(gedaan):]
    reden = 'door de fout' if fout else '--max'
    return (['blijft liggen (%s): %s' % (reden, naam) for _, naam, _, _ in over]
            + ['issue niet gevonden: %s' % naam for _, naam, _, _ in regels['niet gevonden']])


def main():
    parser = argparse.ArgumentParser(description='Runner van Fien: LogMyTime-taken archiveren.')
    parser.add_argument('--dry-run', action='store_true', help='alleen het plan tonen')
    parser.add_argument('--max', type=int, default=100, help='hooguit zoveel taken archiveren (standaard 100)')
    args = parser.parse_args()
    sys.stdout.reconfigure(line_buffering=True)
    moment = nu_lokaal()
    jaar, week, _ = moment.isocalendar()
    path = RUNS / ('fien-%d-w%02d.md' % (jaar, week))
    print('--- %s' % moment.isoformat())

    if not args.dry_run:
        RUNS.mkdir(parents=True, exist_ok=True)
        run_schrijven(path, {'status': 'running', 'started': moment.isoformat(), 'ended': '',
                             'resume': RESUME, 'pid': os.getpid()},
                      '# Fien: %s\n\nDe runner draait sinds %s.\n' % (moment.date().isoformat(), moment.isoformat()))

    stap, gedaan, plan = 'plan', [], None
    try:
        plan = archief.plan(moment.date())
        aantal, grens, regels, zonder_id = plan
        print('actief %d, grens %s: %s, geen ID %d' % (aantal, grens.isoformat(), ', '.join(
            '%s %d' % (s, len(l)) for s, l in regels.items()), len(zonder_id)))
        if args.dry_run:
            for _, naam, toelichting, _ in regels['archiveren']:
                print('  archiveren: %s (%s)' % (naam, toelichting))
            return
        stap = 'archiveren'
        for regel in archief.archiveren(regels, args.max):
            gedaan.append(regel)
            print('  gearchiveerd: %s' % regel[1])
        fout = None
    except Exception as e:  # noqa: BLE001 - elke fout moet als `failed` op het dashboard komen
        traceback.print_exc()
        fout = '%s: %s' % (type(e).__name__, e)
        if args.dry_run:
            sys.exit(1)

    velden = {'status': 'failed' if fout else 'done', 'started': moment.isoformat(),
              'ended': nu_lokaal().isoformat(), 'pid': None,
              'reason': fout, 'step': stap if fout else None, 'resume': RESUME if fout else None}
    if plan:
        aantal, grens, regels, zonder_id = plan
        velden.update(aandacht=aandacht(regels, gedaan, fout), gearchiveerd=len(gedaan),
                      wacht=len(regels['wacht']), open=len(regels['open']))
        tekst = verslag(moment, aantal, grens, regels, zonder_id, gedaan, args.max, fout)
    else:
        tekst = '# Fien: %s\n\n**Mislukt bij het plan:** %s\n\nDe runner schrijft deze notitie; zie [[fien]].\n' % (
            moment.date().isoformat(), fout)
    run_schrijven(path, velden, tekst)
    subprocess.run([sys.executable, str(VAULT / 'scripts/build_index.py')], check=False, capture_output=True)
    print('%s: %s, %d gearchiveerd' % (velden['status'], path.name, len(gedaan)))
    sys.exit(1 if fout else 0)


if __name__ == '__main__':
    main()
