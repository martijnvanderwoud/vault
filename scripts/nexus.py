"""Toegang tot de REST API van Nexus (sonatype.pompkracht.nl), voor het opruimen van npm-develop-versies.

De servicegebruiker komt uit NEXUS_USERNAME en NEXUS_PASSWORD in ~/vault/.env en wordt nooit getoond.

Los gedraaid toont het per package in npm-repo het aantal versies, releases en develop-versies.
"""
import base64
import collections
import json
import os
import urllib.parse
import urllib.request

SONATYPE = 'https://sonatype.pompkracht.nl'
NEXUS = SONATYPE + '/service/rest/v1'
REPO = 'npm-repo'


def gegevens():
    path = os.path.expanduser('~/vault/.env')
    waarden = {}
    for line in open(path).read().splitlines():
        if line.startswith(('NEXUS_USERNAME=', 'NEXUS_PASSWORD=')):
            naam, waarde = line.split('=', 1)
            waarden[naam] = waarde.strip()
    for naam in ('NEXUS_USERNAME', 'NEXUS_PASSWORD'):
        if not waarden.get(naam):
            raise SystemExit(naam + ' ontbreekt in ' + path)
    return waarden['NEXUS_USERNAME'], waarden['NEXUS_PASSWORD']


def verzoek(url, method='GET'):
    gebruiker, wachtwoord = gegevens()
    auth = base64.b64encode(('%s:%s' % (gebruiker, wachtwoord)).encode()).decode()
    request = urllib.request.Request(url, method=method,
                                     headers={'Authorization': 'Basic ' + auth, 'Accept': 'application/json'})
    return urllib.request.urlopen(request)


def nexus(pad, params=None):
    """GET op pad met basic auth. Geeft het JSON-antwoord terug."""
    return json.load(verzoek(NEXUS + pad + ('?' + urllib.parse.urlencode(params) if params else '')))


def packument(pakket, repo=REPO):
    """De npm-metadata van een package, met onder meer dist-tags en publicatietijden (time)."""
    return json.load(verzoek('%s/repository/%s/%s' % (SONATYPE, repo, urllib.parse.quote(pakket, safe='@'))))


def verwijder(component_id):
    """Verwijdert een component (een versie van een package) met alle assets."""
    verzoek(NEXUS + '/components/' + urllib.parse.quote(component_id), method='DELETE')


def componenten(repo=REPO):
    """Alle componenten in de repo, over alle pagina's van /search heen."""
    params = {'repository': repo}
    while True:
        antwoord = nexus('/search', params)
        yield from antwoord['items']
        if not antwoord.get('continuationToken'):
            return
        params['continuationToken'] = antwoord['continuationToken']


def pakketnaam(component):
    return '@%s/%s' % (component['group'], component['name']) if component.get('group') else component['name']


def main():
    per_pakket = collections.defaultdict(collections.Counter)
    for c in componenten():
        soort = 'develop' if '-develop.' in c['version'] else 'release' if '-' not in c['version'] else 'overig'
        per_pakket[pakketnaam(c)][soort] += 1
    print('%-50s %7s %7s %7s %7s' % ('package', 'totaal', 'release', 'develop', 'overig'))
    for naam in sorted(per_pakket):
        t = per_pakket[naam]
        print('%-50s %7d %7d %7d %7d' % (naam, sum(t.values()), t['release'], t['develop'], t['overig']))
    alles = sum(per_pakket.values(), collections.Counter())
    print('%-50s %7d %7d %7d %7d' % ('totaal (%d packages)' % len(per_pakket), sum(alles.values()),
                                     alles['release'], alles['develop'], alles['overig']))


if __name__ == '__main__':
    main()
