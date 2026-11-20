#!/usr/bin/python3
"""Ruimt oude develop-versies van onze npm-packages op in Nexus (npm-repo op sonatype.pompkracht.nl).

Gebruik: nexus_opruimen.py [--pakket NAAM] [--uitvoeren] [--max N]
Zonder --uitvoeren toont het script alleen het plan en verwijdert niets. Met --uitvoeren verwijdert
het hooguit N versies (standaard 20), de oudste eerst. Met --pakket kijkt het naar één package,
bijvoorbeeld @pompkracht/iam-login-ui.

Per package blijven staan:
- alle releases en andere versies zonder '-develop.';
- de 3 nieuwste develop-versies, op publicatietijd (niet op semver: de hash sorteert niet);
- de versie waar een dist-tag naar wijst (develop, latest).
Alle andere develop-versies gaan weg, ook als de release nog niet uit is. Zie
gebieden/vault/npm-develop-versies-opruimen-plan.md. De blob store wordt 's nachts al opgeschoond.
De servicegebruiker komt uit ~/vault/.env en wordt nooit getoond.
"""
import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nexus import componenten, packument, pakketnaam, verwijder  # noqa: E402

BEWAREN = 3


def plan(versies, publicatie, dist_tags):
    """Verdeelt de versies van één package in (blijft, weg), elk een lijst van (versie, reden)."""
    develop = sorted((v for v in versies if '-develop.' in v), key=lambda v: publicatie.get(v, ''), reverse=True)
    getagd = collections.defaultdict(list)
    for tag, versie in dist_tags.items():
        getagd[versie].append(tag)
    blijft, weg = [], []
    for v in versies:
        if '-develop.' not in v:
            blijft.append((v, 'release'))
    for positie, v in enumerate(develop):
        if v in getagd:
            blijft.append((v, 'dist-tag ' + ', '.join(sorted(getagd[v]))))
        elif positie < BEWAREN:
            blijft.append((v, 'nieuwste %d' % BEWAREN))
        else:
            weg.append((v, ''))
    return blijft, weg


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--pakket', help='alleen dit package, bijvoorbeeld @pompkracht/iam-login-ui')
    ap.add_argument('--uitvoeren', action='store_true', help='verwijder de versies ook echt uit Nexus')
    ap.add_argument('--max', type=int, default=20, help='hooguit zoveel versies verwijderen (standaard 20)')
    args = ap.parse_args()

    per_pakket = collections.defaultdict(dict)
    for c in componenten():
        per_pakket[pakketnaam(c)][c['version']] = c['id']
    if args.pakket:
        if args.pakket not in per_pakket:
            raise SystemExit('Package %s staat niet in npm-repo' % args.pakket)
        per_pakket = {args.pakket: per_pakket[args.pakket]}

    te_verwijderen = []
    totaal = collections.Counter()
    print('Packages in npm-repo: %d%s' % (len(per_pakket), '' if args.uitvoeren else ' (alleen plan)'))
    for naam in sorted(per_pakket):
        versies = per_pakket[naam]
        meta = packument(naam)
        publicatie = meta.get('time', {})
        zonder_tijd = [v for v in versies if '-develop.' in v and v not in publicatie]
        if zonder_tijd:
            # Zonder publicatietijd valt de volgorde niet te bepalen: dit package overslaan.
            print('\n%s: overgeslagen, geen publicatietijd voor %s' % (naam, ', '.join(sorted(zonder_tijd))))
            continue
        blijft, weg = plan(versies, publicatie, meta.get('dist-tags', {}))
        totaal.update(blijft=len(blijft), weg=len(weg))
        print('\n%s: %d versies, %d blijven, %d weg' % (naam, len(versies), len(blijft), len(weg)))
        for v, reden in sorted(blijft, key=lambda r: publicatie.get(r[0], '')):
            print('  blijft  %-40s %s  %s' % (v, publicatie.get(v, '')[:10], reden))
        for v, _ in sorted(weg, key=lambda r: publicatie[r[0]]):
            te_verwijderen.append((publicatie[v], naam, v, versies[v]))
        if weg:
            oudste = min(publicatie[v] for v, _ in weg)[:10]
            nieuwste = max(publicatie[v] for v, _ in weg)[:10]
            print('  weg     %d develop-versies, gepubliceerd %s t/m %s' % (len(weg), oudste, nieuwste))
    print('\nTotaal: %d blijven, %d weg' % (totaal['blijft'], totaal['weg']))

    if not args.uitvoeren:
        return
    te_doen = sorted(te_verwijderen)[:args.max]
    print('\nVerwijderen: %d van %d (--max %d)' % (len(te_doen), len(te_verwijderen), args.max))
    for nummer, (_, naam, versie, component_id) in enumerate(te_doen, 1):
        verwijder(component_id)
        print('  %3d. verwijderd: %s@%s' % (nummer, naam, versie), flush=True)
    print('Klaar: %d verwijderd, %d blijven over voor een volgende run.' % (
        len(te_doen), len(te_verwijderen) - len(te_doen)))


if __name__ == '__main__':
    main()
