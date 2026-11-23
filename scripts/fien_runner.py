#!/usr/bin/python3
"""Runner van Fien: ruimt op wat af is, zonder model. Twee taken:

- `taken`: archiveert de LogMyTime-taken waarvan het issue af is, met logmytime_taken_archiveren.py
  (hooguit --max taken, standaard 100). Plan: gebieden/vault/logmytime-taken-archiveren-plan.md.
- `npm`: verwijdert de oude develop-versies van onze npm-packages uit Nexus, met nexus_opruimen.py
  (hooguit --max-npm versies, standaard 50). Plan: gebieden/vault/npm-develop-versies-opruimen-plan.md.

    fien_runner.py [--dry-run] [--alleen taken|npm] [--max N] [--max-npm N]

Zonder --alleen draait de runner beide taken na elkaar; mislukt de ene, dan draait de andere toch.
launchd start ze apart: `taken` elke maandag om 8:00 (scripts/fien/nl.crimsoncricket.fien.plist) en
`npm` elke dag om 8:05 (scripts/fien/nl.crimsoncricket.fien-npm.plist). Logs in ~/.fien/logs/.

Voor het agents-dashboard schrijft de runner per taak een run-notitie in
gebieden/werk/logmytime-archiveren/runs/ (gebieden/agents/agent-runs.md): `fien-<jaar>-w<week>.md`
(onderwerp `taken`, één per week) en `fien-<jjjj-mm-dd>-npm.md` (onderwerp `npm`, één per dag). Bij
de start `running`, aan het eind `done` of `failed`.
Aandachtspunten bij `taken`: taken die door `--max` of een fout blijven liggen en taken met een
issue-ID dat YouTrack niet kent. Bij `npm`: versies die door `--max-npm` of een fout blijven liggen
en packages die zijn overgeslagen omdat een publicatietijd ontbreekt. Wat gearchiveerd of verwijderd
is, taken zonder issue-ID en een verschoven `latest` (verwacht, nexus-public #437) staan alleen in de
tekst. Verandert een andere dist-tag dan `latest`, dan stopt `npm` als `failed`. Zonder
aandachtspunten wacht een run niet op mij. De melding komt van de watcher. Een tweede run in dezelfde
week (`taken`) of op dezelfde dag (`npm`) schrijft dezelfde notitie opnieuw.

`--dry-run` toont alleen de plannen, zonder run-notitie en zonder iets te veranderen.
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
import nexus_opruimen  # noqa: E402

VAULT = Path(__file__).resolve().parent.parent
RUNS = VAULT / 'gebieden/werk/logmytime-archiveren/runs'
VELDEN = ('description', 'agent', 'onderwerp', 'status', 'started', 'ended', 'reason', 'step', 'aandacht',
          'resume', 'pid', 'gearchiveerd', 'wacht', 'open', 'verwijderd', 'over')
RESUME = {'taken': 'launchctl kickstart gui/$(id -u)/nl.crimsoncricket.fien',
          'npm': 'launchctl kickstart gui/$(id -u)/nl.crimsoncricket.fien-npm'}


def nu_lokaal():
    return datetime.now().astimezone().replace(microsecond=0)


def run_schrijven(path, onderwerp, velden, tekst):
    """Schrijft de run-notitie. Velden met `None` vallen weg."""
    fm = {k: v for k, v in dict({'agent': 'fien', 'onderwerp': onderwerp, 'aandacht': []}, **velden).items()
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


def run_starten(path, onderwerp, moment, titel):
    RUNS.mkdir(parents=True, exist_ok=True)
    run_schrijven(path, onderwerp, {'status': 'running', 'started': moment.isoformat(), 'ended': '',
                                    'resume': RESUME[onderwerp], 'pid': os.getpid()},
                  '# %s\n\nDe runner draait sinds %s.\n' % (titel, moment.isoformat()))


def eindvelden(onderwerp, moment, stap, fout):
    return {'status': 'failed' if fout else 'done', 'started': moment.isoformat(),
            'ended': nu_lokaal().isoformat(), 'pid': None,
            'reason': fout, 'step': stap if fout else None, 'resume': RESUME[onderwerp] if fout else None}


def mislukt_bij_plan(titel, fout):
    return '# %s\n\n**Mislukt bij het plan:** %s\n\nDe runner schrijft deze notitie; zie [[fien]].\n' % (titel, fout)


def taken(moment, path, args):
    """Taak `taken`: LogMyTime-taken archiveren. Geeft True als de taak mislukte."""
    titel = 'Fien: %s' % moment.date().isoformat()
    if not args.dry_run:
        run_starten(path, 'taken', moment, titel)
    stap, gedaan, plan = 'plan', [], None
    try:
        plan = archief.plan(moment.date())
        aantal, grens, regels, zonder_id = plan
        print('taken: actief %d, grens %s: %s, geen ID %d' % (aantal, grens.isoformat(), ', '.join(
            '%s %d' % (s, len(l)) for s, l in regels.items()), len(zonder_id)))
        if args.dry_run:
            for _, naam, toelichting, _ in regels['archiveren']:
                print('  archiveren: %s (%s)' % (naam, toelichting))
            return False
        stap = 'archiveren'
        for regel in archief.archiveren(regels, args.max):
            gedaan.append(regel)
            print('  gearchiveerd: %s' % regel[1])
        fout = None
    except Exception as e:  # noqa: BLE001 - elke fout moet als `failed` op het dashboard komen
        traceback.print_exc()
        fout = '%s: %s' % (type(e).__name__, e)
        if args.dry_run:
            return True

    velden = eindvelden('taken', moment, stap, fout)
    if plan:
        aantal, grens, regels, zonder_id = plan
        velden.update(aandacht=aandacht(regels, gedaan, fout), gearchiveerd=len(gedaan),
                      wacht=len(regels['wacht']), open=len(regels['open']))
        tekst = verslag(moment, aantal, grens, regels, zonder_id, gedaan, args.max, fout)
    else:
        tekst = mislukt_bij_plan(titel, fout)
    run_schrijven(path, 'taken', velden, tekst)
    print('taken %s: %s, %d gearchiveerd' % (velden['status'], path.name, len(gedaan)))
    return bool(fout)


def npm_verslag(moment, pakketten, te_verwijderen, overgeslagen, gedaan, maximum, fout):
    delen = ['# Fien: npm-versies %s' % moment.date().isoformat(), '',
             'Run van %s. Per package blijven alle releases, de %d nieuwste develop-versies en de versies '
             'met een dist-tag staan; de andere develop-versies gaan weg uit npm-repo op '
             'sonatype.pompkracht.nl. Plan en regel: [[npm-develop-versies-opruimen-plan]].' % (
                 moment.isoformat(), nexus_opruimen.BEWAREN)]
    if fout:
        delen += ['', '**Mislukt:** %s' % fout]
    delen += ['', '## Verwijderd (%d)' % len(gedaan), '',
              '\n'.join('- %s@%s' % (naam, versie) for naam, versie, _ in gedaan) or '- geen']
    verschoven = ['- %s: %s %s → %s' % (naam, tag, oud or '(geen)', nieuw or '(geen)')
                  for naam, _, veranderd in gedaan for tag, oud, nieuw in veranderd]
    if verschoven:
        delen += ['', '## Verschoven dist-tags (%d)' % len(verschoven), '',
                  'Nexus zet `latest` bij verwijderen op de hoogste versie volgens semver (nexus-public #437). '
                  'Verwacht: de volgende release zet het goed.', '', '\n'.join(verschoven)]
    over = te_verwijderen[len(gedaan):]
    if over:
        delen += ['', '## Blijven liggen (%d, %s)' % (len(over), 'door de fout' if fout else '--max-npm %d' % maximum),
                  '', '\n'.join('- %s@%s' % (naam, versie) for _, naam, versie, _ in over)]
    if overgeslagen:
        delen += ['', '## Overgeslagen (%d)' % len(overgeslagen), '',
                  'Zonder publicatietijd valt de volgorde niet te bepalen.', '',
                  '\n'.join('- %s: %s' % (naam, ', '.join(v)) for naam, v in overgeslagen)]
    delen += ['', '## Per package, vóór de run (%d)' % len(pakketten), '',
              '\n'.join('- %s: %d versies, %d blijven, %d weg' % (p.naam, len(p.versies), len(p.blijft), len(p.weg))
                        for p in pakketten) or '- geen',
              '', 'De runner schrijft deze notitie; zie [[fien]].']
    return '\n'.join(delen) + '\n'


def npm_aandacht(te_verwijderen, overgeslagen, gedaan, fout):
    over = te_verwijderen[len(gedaan):]
    reden = 'door de fout' if fout else '--max-npm'
    return (['blijft liggen (%s): %s@%s' % (reden, naam, versie) for _, naam, versie, _ in over]
            + ['overgeslagen, geen publicatietijd: %s' % naam for naam, _ in overgeslagen])


def npm(moment, path, args):
    """Taak `npm`: oude develop-versies uit Nexus verwijderen. Geeft True als de taak mislukte."""
    titel = 'Fien: npm-versies %s' % moment.date().isoformat()
    if not args.dry_run:
        run_starten(path, 'npm', moment, titel)
    stap, gedaan, plan = 'plan', [], None
    try:
        plan = nexus_opruimen.opruimplan()
        pakketten, te_verwijderen, overgeslagen = plan
        print('npm: %d packages, %d versies weg, %d overgeslagen' % (
            len(pakketten), len(te_verwijderen), len(overgeslagen)))
        if args.dry_run:
            for _, naam, versie, _ in te_verwijderen:
                print('  verwijderen: %s@%s' % (naam, versie))
            return False
        stap = 'verwijderen'
        for naam, versie, veranderd in nexus_opruimen.verwijderen(pakketten, te_verwijderen, args.max_npm):
            gedaan.append((naam, versie, veranderd))
            print('  verwijderd: %s@%s%s' % (naam, versie, ''.join(
                ' (%s: %s → %s)' % (tag, oud, nieuw) for tag, oud, nieuw in veranderd)))
        fout = None
    except Exception as e:  # noqa: BLE001 - elke fout moet als `failed` op het dashboard komen
        traceback.print_exc()
        fout = '%s: %s' % (type(e).__name__, e)
        if args.dry_run:
            return True

    velden = eindvelden('npm', moment, stap, fout)
    if plan:
        pakketten, te_verwijderen, overgeslagen = plan
        velden.update(aandacht=npm_aandacht(te_verwijderen, overgeslagen, gedaan, fout), verwijderd=len(gedaan),
                      over=len(te_verwijderen) - len(gedaan))
        tekst = npm_verslag(moment, pakketten, te_verwijderen, overgeslagen, gedaan, args.max_npm, fout)
    else:
        tekst = mislukt_bij_plan(titel, fout)
    run_schrijven(path, 'npm', velden, tekst)
    print('npm %s: %s, %d verwijderd' % (velden['status'], path.name, len(gedaan)))
    return bool(fout)


def main():
    parser = argparse.ArgumentParser(description='Runner van Fien: LogMyTime-taken archiveren en npm-versies opruimen.')
    parser.add_argument('--dry-run', action='store_true', help='alleen de plannen tonen')
    parser.add_argument('--alleen', choices=('taken', 'npm'), help='alleen deze taak draaien')
    parser.add_argument('--max', type=int, default=100, help='hooguit zoveel taken archiveren (standaard 100)')
    parser.add_argument('--max-npm', type=int, default=50, help='hooguit zoveel npm-versies verwijderen (standaard 50)')
    args = parser.parse_args()
    sys.stdout.reconfigure(line_buffering=True)
    moment = nu_lokaal()
    jaar, week, _ = moment.isocalendar()
    print('--- %s' % moment.isoformat())

    mislukt = False
    if args.alleen in (None, 'taken'):
        mislukt |= taken(moment, RUNS / ('fien-%d-w%02d.md' % (jaar, week)), args)
    if args.alleen in (None, 'npm'):
        start = nu_lokaal()
        mislukt |= npm(start, RUNS / ('fien-%s-npm.md' % start.date().isoformat()), args)
    if not args.dry_run:
        subprocess.run([sys.executable, str(VAULT / 'scripts/build_index.py')], check=False, capture_output=True)
    sys.exit(1 if mislukt else 0)


if __name__ == '__main__':
    main()
