#!/usr/bin/python3
"""Schrijft gebieden/agents/dashboard.md uit de run-notities van alle agents.

Bovenaan wat op mij wacht, dan wat nu draait, dan per agent de laatste run per onderwerp van de
afgelopen 7 dagen. Alles uit een run-notitie komt er als platte tekst in: een agent kan het
dashboard niet opmaken. Het bestand wordt alleen geschreven als de inhoud verandert (de regel
`Bijgewerkt` telt niet mee). Afspraak: gebieden/agents/agent-runs.md, plan:
gebieden/vault/agents-dashboard-plan.md.

    agent_dashboard.py [--agents MAP] [--uit BESTAND]
"""
import argparse
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Met `python3 -I` (zoals onder launchd) staat de map van het script niet in sys.path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agentruns  # noqa: E402

UIT = agentruns.AGENTS / 'dashboard.md'
YOUTRACK = 'https://crimsoncricket.myjetbrains.com/youtrack/issue/'
DAGEN = 7
ICONEN = {'running': '⏳', 'paused': '⏸️', 'failed': '❌', 'done': '✅', 'resolved': '☑️'}
WOORDEN = {'running': 'bezig', 'paused': 'wacht op jou', 'failed': 'mislukt', 'done': 'klaar',
           'resolved': 'vrijgegeven'}
WEEKDAGEN = ('ma', 'di', 'wo', 'do', 'vr', 'za', 'zo')
SPECIAAL = set('\\`*_[]<>#|~=$%^!&{}:')
VEILIG = re.compile(r'^[\w.-]+$')
ISSUE = re.compile(r'^[A-Z][A-Z0-9_]*-\d+$')
BIJGEWERKT = 'Bijgewerkt: '
INTERVAL = re.compile(r'^(\d+)([mhd])$')
EENHEDEN = {'m': 'minutes', 'h': 'hours', 'd': 'days'}


def tekst(value):
    """Platte tekst uit een run-notitie: op één regel, en alles wat Markdown of HTML kan worden
    (ook `|` in een tabel) met een backslash ervoor."""
    if isinstance(value, list):
        value = ', '.join(str(v) for v in value)
    return ''.join('\\' + c if c in SPECIAAL else c for c in ' '.join(str(value).split()))


def tijd(value):
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def wanneer(value):
    t = tijd(value)
    if t is None:
        return tekst(value) or '-'
    t = t.astimezone()
    return '%s %s' % (WEEKDAGEN[t.weekday()], t.strftime('%d-%m %H:%M'))


def issue_link(issue):
    if not issue:
        return '-'
    if ISSUE.match(str(issue)):
        return '[%s](%s%s)' % (issue, YOUTRACK, issue)
    return tekst(issue)


def wikilink(doel, label, tabel=False):
    """In een tabel moet de `|` van een alias ontsnapt worden."""
    return '[[%s%s%s]]' % (doel, '\\|' if tabel else '|', label)


def run_link(path, label, tabel=False):
    """Een wikilink naar de run-notitie, alleen als naam en label geen opmaak kunnen bevatten."""
    if VEILIG.match(path.stem) and VEILIG.match(str(label)):
        return wikilink(path.stem, label, tabel)
    return tekst(label)


def status_cel(fm):
    status = str(fm.get('status', ''))
    if status not in ICONEN:
        return '❓ ' + tekst(status)
    if status == 'done' and agentruns.wacht_op_mij(fm):
        return '⚠️ klaar, met aandachtspunten'
    return '%s %s' % (ICONEN[status], WOORDEN[status])


def kosten(fm):
    try:
        return '\\$%.2f' % float(fm['kosten'])
    except (KeyError, ValueError, TypeError):
        return '-'


def runs_lezen(agents):
    """[(agent, path, fm)] met per agent en onderwerp de laatste run."""
    result = []
    for naam, agent in agents.items():
        paden = agentruns.notities(agent['runs'], naam)
        for path, fm, _ in agentruns.laatste_per_onderwerp(paden, agent['lijsten']).values():
            result.append((naam, path, fm))
    return sorted(result, key=lambda r: str(r[2].get('started', '')), reverse=True)


def aandacht_blok(runs):
    wachtend = [r for r in runs if agentruns.wacht_op_mij(r[2])]
    if not wachtend:
        return ['> [!success] Niets wacht op jou']
    regels = ['> [!danger] Aandacht nodig (%d)' % len(wachtend)]
    for naam, path, fm in wachtend:
        kop = '**%s · %s** · %s' % (wikilink(naam, naam.capitalize()), run_link(path, fm.get('onderwerp', '')),
                                     status_cel(fm))
        regels += ['>', '> ' + kop + ' · ' + issue_link(fm.get('issue')) + ' · ' + wanneer(fm.get('started'))]
        if fm.get('status') in ('paused', 'failed'):
            waar = ('bij stap %s: ' % tekst(fm['step'])) if fm.get('step') else ''
            regels.append('> - %s%s' % (waar, tekst(fm.get('reason')) or 'geen reden opgegeven'))
        for punt in fm.get('aandacht') or []:
            regels.append('> - ' + tekst(punt))
        if fm.get('resume'):
            regels.append('> - hervatten: ' + tekst(fm['resume']))
    return regels


def interval(value):
    """`interval` uit de notitie van een agent, zoals `8d`, `12h` of `30m`, als timedelta."""
    m = INTERVAL.match(str(value).strip())
    return timedelta(**{EENHEDEN[m.group(2)]: int(m.group(1))}) if m else None


def stil_blok(agents, runs, nu):
    """Agents met een `interval` die langer dan dat geen run zijn begonnen, en geen run bezig hebben."""
    stil = []
    for naam, agent in agents.items():
        if not agent.get('interval'):
            continue
        eigen = [r[2] for r in runs if r[0] == naam]
        if any(fm.get('status') == 'running' for fm in eigen):
            continue
        maximaal = interval(agent['interval'])
        if maximaal is None:
            stil.append('> - %s · `interval` onleesbaar: %s' % (wikilink(naam, naam.capitalize()), tekst(agent['interval'])))
            continue
        laatste = max((t for t in (tijd(fm.get('started')) for fm in eigen) if t), default=None)
        if laatste is None:
            stil.append('> - %s · nog nooit gedraaid (verwacht elke %s)' % (wikilink(naam, naam.capitalize()), agent['interval']))
        elif nu - laatste > maximaal:
            stil.append('> - %s · laatste run %s (verwacht elke %s)' % (
                wikilink(naam, naam.capitalize()), wanneer(laatste.isoformat()), agent['interval']))
    return ['> [!warning] Stil (%d)' % len(stil)] + stil + [''] if stil else []


def watcher_blok(nu):
    """Een waarschuwing als de watcher geen heartbeat meer schrijft: dan loopt dit dashboard achter."""
    stil = agentruns.watcher_stil(nu)
    if stil is None:
        return []
    sinds = 'nog nooit gedraaid' if stil == 'nooit' else 'laatste teken van leven %s' % wanneer(stil.isoformat())
    return ['> [!danger] De watcher draait niet', '> %s. Dit dashboard ververst niet vanzelf, zie '
            '[[agents-dashboard-plan]] (stap 3).' % sinds.capitalize(), '']


def bezig_blok(runs):
    bezig = [r for r in runs if r[2].get('status') == 'running']
    regels = ['> [!info] Nu bezig (%d)' % len(bezig)]
    if not bezig:
        return regels + ['> Geen runs bezig.']
    for naam, path, fm in bezig:
        regels.append('> - %s · %s · sinds %s' % (naam.capitalize(), run_link(path, fm.get('onderwerp', '')),
                                                 wanneer(fm.get('started'))))
    return regels


def tabellen(agents, runs, nu):
    grens = nu - timedelta(days=DAGEN)
    regels = ['## Afgelopen %d dagen' % DAGEN]
    for naam in agents:
        regels += ['', '### ' + wikilink(naam, naam.capitalize()), '']
        recent = [r for r in runs if r[0] == naam and (
            r[2].get('status') == 'running' or agentruns.wacht_op_mij(r[2])
            or (tijd(r[2].get('started')) or datetime.min.replace(tzinfo=nu.tzinfo)) >= grens)]
        if not recent:
            regels.append('Geen runs.')
            continue
        regels += ['| Onderwerp | Status | Gestart | Issue | Kosten |', '| --- | --- | --- | --- | --- |']
        for _, path, fm in recent:
            regels.append('| %s | %s | %s | %s | %s |' % (
                run_link(path, fm.get('onderwerp', ''), tabel=True), status_cel(fm), wanneer(fm.get('started')),
                issue_link(fm.get('issue')), kosten(fm)))
    return regels


def dashboard(agents, nu):
    runs = runs_lezen(agents)
    regels = [
        '---',
        'description: "Gegenereerd overzicht van alle autonome agents: wat op mij wacht, wat draait en de runs van de afgelopen %d dagen"' % DAGEN,
        'tags: [agents, dashboard]',
        'cssclasses: [wide-page]',
        '---',
        '',
        '# Agents',
        '',
    ]
    regels += watcher_blok(nu) + aandacht_blok(runs) + [''] + stil_blok(agents, runs, nu) + bezig_blok(runs) + [''] + tabellen(agents, runs, nu)
    regels += [
        '',
        '---',
        '',
        'Gegenereerd door `scripts/agent_dashboard.py`, niet met de hand bewerken. Afspraak: [[agent-runs]].',
        '',
        BIJGEWERKT + wanneer(nu.isoformat(timespec='seconds')),
    ]
    return '\n'.join(regels) + '\n'


def zonder_bijgewerkt(inhoud):
    return '\n'.join(r for r in inhoud.splitlines() if not r.startswith(BIJGEWERKT))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--agents', default=agentruns.AGENTS, help='map met de notities per agent')
    parser.add_argument('--uit', default=UIT, help='het dashboard dat geschreven wordt')
    args = parser.parse_args()
    uit = Path(args.uit)
    inhoud = dashboard(agentruns.agents(args.agents), datetime.now().astimezone())
    oud = uit.read_text(encoding='utf-8') if uit.exists() else None
    if oud is not None and zonder_bijgewerkt(oud) == zonder_bijgewerkt(inhoud):
        print('ongewijzigd: %s' % uit)
        return
    agentruns.atomair_schrijven(uit, inhoud)
    print('geschreven: %s' % uit)


if __name__ == '__main__':
    main()
