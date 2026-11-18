#!/usr/bin/python3
"""Runner van Ward, de bewaker van system health: draait de checks op de hosts van Pompkracht.

De hosts komen uit ~/.ssh/config (de `Host`-regels zonder wildcard), de verwachte waarden uit
data/ward/baseline.json. Die referentie pas ik bewust met de hand aan, nooit automatisch. Behalve
de checks uit scripts/ward/checks/ vergelijkt de runner de hostlijst met de referentie: een host die
erbij komt of uit de config verdwijnt, is een `warn` van de check `hosts`.
Plan: gebieden/werk/ward-plan.md.

    ward_runner.py [--dry-run] [--referentie PAD]

Toont per check en host de uitkomst (`ok`, `warn` of `alarm`) met details. Exitcode 0 als alles
`ok` is, 1 bij een `warn`, 2 bij een `alarm`. `--dry-run` toont alleen de uitkomsten; nu doet een
gewone run nog niets anders, later starten daar Ward en het vastleggen van de status.
`--referentie` neemt een andere referentie, om `warn` en `alarm` te testen.
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Met `python3 -I` (zoals onder launchd) staat de map van het script niet in sys.path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ssh  # noqa: E402
from checks import CHECKS, UITKOMSTEN  # noqa: E402

VAULT = Path(__file__).resolve().parent.parent.parent
REFERENTIE = VAULT / 'data/ward/baseline.json'


def hosts_check(hosts, verwacht):
    """{host: (uitkomst, details)} voor de hostlijst tegenover de hosts uit de referentie."""
    result = {}
    for host in hosts:
        result[host] = ('ok', 'in de referentie') if host in verwacht else (
            'warn', 'nieuwe host, niet in de referentie')
    for host in verwacht:
        if host not in hosts:
            result[host] = ('warn', 'ontbreekt in %s' % ssh.SSH_CONFIG)
    return result


def draaien(referentie):
    """{check: {host: (uitkomst, details)}} voor alle checks."""
    hosts = ssh.hosts()
    uitkomsten = {'hosts': hosts_check(hosts, referentie['hosts'])}
    for check in CHECKS:
        uitkomsten[check.NAAM] = check.check(hosts, referentie[check.NAAM])
    return uitkomsten


def ergste(uitkomsten):
    return max((u for per_host in uitkomsten.values() for u, _ in per_host.values()),
               key=UITKOMSTEN.index, default='ok')


def tonen(uitkomsten):
    breedte = max(len(h) for per_host in uitkomsten.values() for h in per_host)
    for naam, per_host in uitkomsten.items():
        aantallen = {u: sum(1 for v, _ in per_host.values() if v == u) for u in UITKOMSTEN}
        print('%s: %s' % (naam, ', '.join('%d %s' % (n, u) for u, n in aantallen.items() if n)))
        for host, (uitkomst, details) in per_host.items():
            print('  %-5s  %-*s  %s' % (uitkomst, breedte, host, details))


def main():
    parser = argparse.ArgumentParser(description='Runner van Ward: checks op de hosts van Pompkracht.')
    parser.add_argument('--dry-run', action='store_true', help='alleen de uitkomsten tonen')
    parser.add_argument('--referentie', type=Path, default=REFERENTIE, help='andere baseline.json')
    args = parser.parse_args()

    uitkomsten = draaien(json.loads(args.referentie.read_text()))
    tonen(uitkomsten)
    sys.exit(UITKOMSTEN.index(ergste(uitkomsten)))


if __name__ == '__main__':
    main()
