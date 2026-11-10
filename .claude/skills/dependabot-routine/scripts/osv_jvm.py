#!/usr/bin/python3
"""Controleert opgeloste JVM-dependencies tegen de OSV-database.

Leest een of meer bestanden met de output van `mvn dependency:list` of
`gradle dependencies` en toont per dependency met bevindingen de advisories en de
doelversie: de laagste versie binnen de huidige major (bij 0.x dezelfde minor) die alle
advisories dekt.

Draaien met /usr/bin/python3 -I: niet elke pyenv-Python heeft de ssl-module.
"""
import argparse
import itertools
import json
import re
import urllib.request

MAVEN = re.compile(r'\s*([\w.\-]+):([\w.\-]+):[\w\-]+(?::[\w.\-]+)?:([\w.\-+]+):(compile|runtime|test|provided|system)')
GRADLE = re.compile(r'.*[+\\]--- ([\w.\-]+):([\w.\-]+)(?::([\w.\-+]+|\{[^}]*\}))?(?: -> ([\w.\-+]+))?')
PRE = ('rc', 'cr', 'alpha', 'a', 'beta', 'b', 'm', 'ea', 'preview', 'pre', 'snapshot', 'dev')
DROP = ('final', 'ga', 'release')
OSV = 'https://api.osv.dev/v1'


def vkey(version):
    key = []
    for t in re.findall(r'\d+|[a-zA-Z]+', version):
        if t.isdigit():
            key.append((1, int(t)))
        elif t.lower() in PRE:
            key.append((0, t.lower()))
        elif t.lower() not in DROP:
            key.append((2, t.lower()))
    return key


def cmp(a, b):
    for x, y in itertools.zip_longest(vkey(a), vkey(b), fillvalue=(1, 0)):
        if x != y:
            return -1 if x < y else 1
    return 0


def same_line(a, b):
    ka, kb = vkey(a) + [(1, 0)] * 2, vkey(b) + [(1, 0)] * 2
    return ka[0] == kb[0] and (ka[0] != (1, 0) or ka[1] == kb[1])


def parse(paths, excludes):
    deps, skipped = set(), 0
    for path in paths:
        for line in open(path):
            m = MAVEN.match(line)
            if m:
                group, artifact, version, scope = m[1], m[2], m[3], m[4]
            else:
                m = GRADLE.match(line)
                if not m or line.rstrip().endswith('(n)'):
                    continue
                group, artifact, version, scope = m[1], m[2], m[4] or m[3], 'gradle'
                if not version or version.startswith('{'):
                    continue
            if group.startswith(tuple(excludes)):
                skipped += 1
                continue
            deps.add((group + ':' + artifact, version, scope))
    return sorted(deps), skipped


def post(url, body):
    req = urllib.request.Request(url, json.dumps(body).encode(), {'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=60))


def get(url):
    return json.load(urllib.request.urlopen(url, timeout=60))


def fixes(vuln, name):
    return sorted({e['fixed'] for a in vuln.get('affected', [])
                   if a.get('package', {}).get('name') == name
                   for r in a.get('ranges', []) for e in r.get('events', []) if 'fixed' in e})


def target(version, fixed_per_vuln):
    best = None
    for fixed in fixed_per_vuln:
        usable = [f for f in fixed if cmp(f, version) > 0 and same_line(f, version)]
        if not usable:
            return None
        low = usable[0]
        for f in usable:
            if cmp(f, low) < 0:
                low = f
        if best is None or cmp(low, best) > 0:
            best = low
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('files', nargs='+')
    ap.add_argument('--exclude', action='append', default=[], help='groupId-prefix, herhaalbaar')
    args = ap.parse_args()

    deps, skipped = parse(args.files, args.exclude)
    print('dependencies: %d (uitgesloten regels: %d)' % (len(deps), skipped))
    if not deps:
        raise SystemExit('geen dependencies gevonden in de invoer')

    hits, truncated = {}, False
    for i in range(0, len(deps), 200):
        chunk = deps[i:i + 200]
        queries = [{'package': {'name': d[0], 'ecosystem': 'Maven'}, 'version': d[1]} for d in chunk]
        for dep, res in zip(chunk, post(OSV + '/querybatch', {'queries': queries})['results']):
            truncated = truncated or 'next_page_token' in res
            if res.get('vulns'):
                hits[dep] = [v['id'] for v in res['vulns']]
    print('met bevindingen: %d' % len(hits))
    if truncated:
        print('LET OP: OSV gaf niet alle resultaten terug (next_page_token)')

    for dep, ids in sorted(hits.items()):
        vulns = [get(OSV + '/vulns/' + vid) for vid in ids]
        fixed = [fixes(v, dep[0]) for v in vulns]
        goal = target(dep[1], fixed)
        print('\n%s %s (%s) doel=%s' % (dep[0], dep[1], dep[2], goal or 'GEEN-BINNEN-MAJOR'))
        for vuln, f in zip(vulns, fixed):
            cves = [a for a in vuln.get('aliases', []) if a.startswith('CVE')]
            sev = vuln.get('database_specific', {}).get('severity')
            print('  %s %s sev=%s fixed=%s :: %s' % (vuln['id'], cves, sev, f, (vuln.get('summary') or '')[:110]))


if __name__ == '__main__':
    main()
