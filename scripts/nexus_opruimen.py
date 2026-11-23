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
Nexus rekent bij het verwijderen van een versie de dist-tag latest opnieuw uit (vaak naar een
develop-build, nexus-public #437) en laat latest niet terugzetten. Dat is geaccepteerd: het script
meldt per verwijdering waar latest naartoe verschoof. Verandert een andere dist-tag, dan stopt het.
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


def veranderde_tags(voor, na):
    """De dist-tags die verschillen tussen voor en na, als (tag, oud, nieuw); None als de tag ontbreekt."""
    return [(tag, voor.get(tag), na.get(tag)) for tag in sorted(set(voor) | set(na)) if voor.get(tag) != na.get(tag)]


class AndereTagVeranderd(Exception):
    """Nexus veranderde bij het verwijderen een andere dist-tag dan latest."""


Pakket = collections.namedtuple('Pakket', 'naam versies publicatie dist_tags blijft weg')


def opruimplan(pakket=None):
    """Het plan voor alle packages in npm-repo (of alleen `pakket`).

    Geeft (pakketten, te_verwijderen, overgeslagen): pakketten is een lijst van Pakket, te_verwijderen
    een lijst van (publicatietijd, naam, versie, component_id), oudste eerst, en overgeslagen een lijst
    van (naam, versies zonder publicatietijd): zonder tijd valt de volgorde niet te bepalen."""
    per_pakket = collections.defaultdict(dict)
    for c in componenten():
        per_pakket[pakketnaam(c)][c['version']] = c['id']
    if pakket:
        if pakket not in per_pakket:
            raise SystemExit('Package %s staat niet in npm-repo' % pakket)
        per_pakket = {pakket: per_pakket[pakket]}
    pakketten, te_verwijderen, overgeslagen = [], [], []
    for naam in sorted(per_pakket):
        versies = per_pakket[naam]
        meta = packument(naam)
        publicatie = meta.get('time', {})
        zonder_tijd = sorted(v for v in versies if '-develop.' in v and v not in publicatie)
        if zonder_tijd:
            overgeslagen.append((naam, zonder_tijd))
            continue
        dist_tags = meta.get('dist-tags', {})
        blijft, weg = plan(versies, publicatie, dist_tags)
        pakketten.append(Pakket(naam, versies, publicatie, dist_tags, blijft, weg))
        te_verwijderen += [(publicatie[v], naam, v, versies[v]) for v, _ in weg]
    return pakketten, sorted(te_verwijderen), overgeslagen


def verwijderen(pakketten, te_verwijderen, maximum):
    """Verwijdert hooguit `maximum` versies uit te_verwijderen, de oudste eerst. Geeft per versie
    (naam, versie, veranderde dist-tags) terug, na het verwijderen. Verandert een andere tag dan
    latest, dan volgt AndereTagVeranderd (na het teruggeven van die versie)."""
    dist_tags = {p.naam: p.dist_tags for p in pakketten}
    for _, naam, versie, component_id in te_verwijderen[:maximum]:
        verwijder(component_id)
        na = packument(naam).get('dist-tags', {})
        veranderd = veranderde_tags(dist_tags[naam], na)
        dist_tags[naam] = na
        yield naam, versie, veranderd
        if any(tag != 'latest' for tag, _, _ in veranderd):
            raise AndereTagVeranderd('Nexus veranderde een andere dist-tag dan latest bij %s@%s' % (naam, versie))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--pakket', help='alleen dit package, bijvoorbeeld @pompkracht/iam-login-ui')
    ap.add_argument('--uitvoeren', action='store_true', help='verwijder de versies ook echt uit Nexus')
    ap.add_argument('--max', type=int, default=20, help='hooguit zoveel versies verwijderen (standaard 20)')
    args = ap.parse_args()

    pakketten, te_verwijderen, overgeslagen = opruimplan(args.pakket)
    print('Packages in npm-repo: %d%s' % (len(pakketten) + len(overgeslagen), '' if args.uitvoeren else ' (alleen plan)'))
    for naam, zonder_tijd in overgeslagen:
        print('\n%s: overgeslagen, geen publicatietijd voor %s' % (naam, ', '.join(zonder_tijd)))
    for p in pakketten:
        print('\n%s: %d versies, %d blijven, %d weg' % (p.naam, len(p.versies), len(p.blijft), len(p.weg)))
        for v, reden in sorted(p.blijft, key=lambda r: p.publicatie.get(r[0], '')):
            print('  blijft  %-40s %s  %s' % (v, p.publicatie.get(v, '')[:10], reden))
        if p.weg:
            oudste = min(p.publicatie[v] for v, _ in p.weg)[:10]
            nieuwste = max(p.publicatie[v] for v, _ in p.weg)[:10]
            print('  weg     %d develop-versies, gepubliceerd %s t/m %s' % (len(p.weg), oudste, nieuwste))
    print('\nTotaal: %d blijven, %d weg' % (sum(len(p.blijft) for p in pakketten), len(te_verwijderen)))

    if not args.uitvoeren:
        return
    aantal = min(args.max, len(te_verwijderen))
    print('\nVerwijderen: %d van %d (--max %d)' % (aantal, len(te_verwijderen), args.max))
    try:
        for nummer, (naam, versie, veranderd) in enumerate(verwijderen(pakketten, te_verwijderen, args.max), 1):
            print('  %3d. verwijderd: %s@%s' % (nummer, naam, versie), flush=True)
            for tag, oud, nieuw in veranderd:
                print('       %s: %s → %s' % (tag, oud or '(geen)', nieuw or '(geen)'), flush=True)
    except AndereTagVeranderd as e:
        raise SystemExit('Gestopt: %s' % e)
    print('Klaar: %d verwijderd, %d blijven over voor een volgende run.' % (aantal, len(te_verwijderen) - aantal))


if __name__ == '__main__':
    main()
