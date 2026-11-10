#!/usr/bin/python3
"""Vergelijkt CVE-overrides met de versie die er zonder override zou staan.

Maven: properties na een XML-comment met "Override" of een CVE/GHSA, en elke
dependencyManagement-entry met een eigen versie.
Gradle: versies in gradle/libs.versions.toml met "override" of een CVE in de comment, plus
`extra["<property>"]` en constraints met `because("CVE...")` in *.gradle.kts.

BOM-overrides worden vergeleken met de property in de BOM, transitieve overrides met
de versies die de paden in de dependency-boom vragen (--tree, herhaalbaar). Een override
is alleen weg te halen als alle paden minstens even hoog zijn. Wordt de versie zonder
override hoger, dan mag hij alleen weg als de comment een security-patch noemt. Poms komen
uit ~/.m2 of de Gradle-cache, dus draai dit na een build.
"""
import argparse
import glob
import itertools
import os
import re
import xml.etree.ElementTree as ET

NS = '{http://maven.apache.org/POM/4.0.0}'
PRE = ('rc', 'cr', 'alpha', 'a', 'beta', 'b', 'm', 'ea', 'preview', 'pre', 'snapshot', 'dev')
DROP = ('final', 'ga', 'release')
M2 = os.path.expanduser('~/.m2/repository')
GRADLE_CACHE = os.path.expanduser('~/.gradle/caches/modules-2/files-2.1')
MANUAL = 'handmatig controleren'
MARKER = re.compile(r'override|CVE-|GHSA-', re.I)
SECURITY = re.compile(r'CVE-|GHSA-|security|vulnerab', re.I)
MAVEN_LINE = re.compile(r'([\w.\-]+):([\w.\-]+):[\w\-]+(?::[\w.\-]+)?:([\w.\-+]+):(?:compile|runtime|test|provided|system)')
GRADLE_LINE = re.compile(r'^([| ]*)[+\\]--- ([\w.\-]+):([\w.\-]+)(?::(\{[^}]*\}|[^\s]+))?(?: -> [\w.\-+]+)?(.*)$')


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


def verdict(override, other):
    c = cmp(override, other)
    if c < 0:
        return 'VEROUDERD: zonder override is de versie hoger, stille downgrade, override kan weg'
    if c == 0:
        return 'OVERBODIG: zonder override dezelfde versie, override kan weg'
    return 'nog nodig'


def by_comment(result, comment):
    """Zonder override hoger: alleen een security-patch mag weg."""
    if result.startswith('VEROUDERD') and not (comment and SECURITY.search(comment)):
        return 'blijft staan: zonder override is de versie hoger, maar %s' % (
            'de comment noemt geen security-patch' if comment else 'er staat geen comment boven')
    return result


class Paths:
    """Per groupId:artifactId welke versies de paden in de boom vragen."""

    def __init__(self):
        self.requested, self.direct, self.unknown, self.pins = {}, set(), set(), {}

    def pin(self, key, version):
        self.pins.setdefault(key, set()).add(version)

    def add(self, key, version, direct):
        self.requested.setdefault(key, set())
        if direct:
            self.direct.add(key)
        elif version:
            self.requested[key].add(version)
        else:
            self.unknown.add(key)

    def judge(self, key, value):
        if key not in self.requested:
            return 'geen pad in de boom, ' + MANUAL
        if key in self.direct:
            return 'directe dependency, blijft staan'
        pins = {v for v in self.pins.get(key, ()) if cmp(v, value) != 0}
        if key in self.unknown or not self.requested[key] | pins:
            return 'versie van een pad onbekend, ' + MANUAL
        low = None
        for v in self.requested[key] | pins:
            if low is None or cmp(v, low) < 0:
                low = v
        return '%s (laagste pad %s)' % (verdict(value, low), low)


def maven_paths(files):
    paths = Paths()
    for path in files:
        for line in open(path):
            m = MAVEN_LINE.search(line)
            if m:
                managed = re.search(r'version managed from ([^;)\s]+)', line)
                paths.add(m[1] + ':' + m[2], managed[1] if managed else m[3], re.match(r'[+\\]- ', line) is not None)
    return paths


def gradle_paths(files):
    paths = Paths()
    for path in files:
        for line in open(path):
            m = GRADLE_LINE.match(line.rstrip('\n'))
            if not m or '(n)' in m[5]:
                continue
            requested = m[4] if m[4] and not m[4].startswith('{') else None
            if '(c)' in m[5]:
                if requested:
                    paths.pin(m[2] + ':' + m[3], requested)
                continue
            paths.add(m[2] + ':' + m[3], requested, m[1] == '')
    return paths


def load(path):
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    return ET.parse(path, parser).getroot()


def is_comment(el):
    return el.tag is ET.Comment


def text(el, name):
    child = el.find(NS + name)
    return child.text.strip() if child is not None and child.text else None


def m2_pom(group, artifact, version):
    path = os.path.join(M2, group.replace('.', '/'), artifact, version, '%s-%s.pom' % (artifact, version))
    return load(path) if os.path.exists(path) else None


def resolve(value, props):
    for _ in range(5):
        m = re.search(r'\$\{([^}]+)\}', value or '')
        if not m or m[1] not in props:
            break
        value = value.replace(m[0], props[m[1]])
    return value


def own_props(pom, inherited):
    props = dict(inherited)
    block = pom.find(NS + 'properties')
    for el in ([] if block is None else block):
        if not is_comment(el):
            props[el.tag.replace(NS, '')] = (el.text or '').strip()
    return props


def chain(root):
    """Properties en managed versions van alle parents, dichtstbijzijnde wint."""
    poms, parent = [], root.find(NS + 'parent')
    while parent is not None:
        pom = m2_pom(text(parent, 'groupId'), text(parent, 'artifactId'), text(parent, 'version'))
        if pom is None:
            raise SystemExit('parent niet in ~/.m2: %s:%s' % (text(parent, 'artifactId'), text(parent, 'version')))
        poms.append(pom)
        parent = pom.find(NS + 'parent')
    props, managed, seen = {}, {}, set()
    for pom in reversed(poms):
        props = own_props(pom, props)
    for pom in poms:
        collect(pom, props, managed, seen)
    return props, managed


def collect(pom, props, managed, seen):
    block = pom.find(NS + 'dependencyManagement/' + NS + 'dependencies')
    for dep in ([] if block is None else block):
        if is_comment(dep):
            continue
        group, artifact = text(dep, 'groupId'), text(dep, 'artifactId')
        version = resolve(text(dep, 'version'), props)
        if text(dep, 'scope') == 'import':
            key = (group, artifact, version)
            imported = None if key in seen else m2_pom(*key)
            seen.add(key)
            if imported is not None:
                collect(imported, own_props(imported, props), managed, seen)
        elif version:
            managed.setdefault(group + ':' + artifact, version)


def check_maven(pom, trees):
    root = load(pom)
    props, managed = chain(root)
    paths = maven_paths(trees)

    count, comment = 0, None
    block = root.find(NS + 'properties')
    for el in ([] if block is None else block):
        if is_comment(el):
            comment = el.text if MARKER.search(el.text) else None
        elif comment:
            name, value = el.tag.replace(NS, ''), (el.text or '').strip()
            count += 1
            if name in props:
                print('%s=%s BOM=%s -> %s' % (name, value, props[name],
                                              by_comment(verdict(value, resolve(props[name], props)), comment)))
            else:
                print('%s=%s -> property niet in de parent, %s' % (name, value, MANUAL))

    comment, own = None, own_props(root, props)
    block = root.find(NS + 'dependencyManagement/' + NS + 'dependencies')
    for dep in ([] if block is None else block):
        if is_comment(dep):
            comment = dep.text
            continue
        value = resolve(text(dep, 'version'), own)
        if value and text(dep, 'scope') != 'import':
            key = text(dep, 'groupId') + ':' + text(dep, 'artifactId')
            count += 1
            if key in managed:
                print('%s=%s BOM=%s -> %s' % (key, value, managed[key], by_comment(verdict(value, managed[key]), comment)))
            else:
                print('%s=%s -> %s' % (key, value, by_comment(paths.judge(key, value), comment)))
        comment = None
    print('overrides: %d' % count)


def norm(name):
    return re.sub(r'[-_.]', '.', name)


def read_catalog(root):
    """Versies met override-comment, per versie-key de libraries, en alle versies met comments."""
    versions, libraries, section = {}, {}, None
    path = os.path.join(root, 'gradle', 'libs.versions.toml')
    if not os.path.exists(path):
        return {}, {}, {}, {}
    plain, comments = {}, {}
    for line in open(path):
        head = re.match(r'\[(\w+)\]', line)
        if head:
            section = head[1]
        elif section == 'versions':
            m = re.match(r'([\w.\-]+)\s*=\s*"([^"]+)"\s*(#.*)?', line)
            if m:
                plain[m[1]] = m[2]
                if m[3] and MARKER.search(m[3]):
                    versions[m[1]] = m[2]
                    comments[m[1]] = m[3]
        elif section == 'libraries':
            m = re.search(r'module\s*=\s*"([^"]+)".*version\.ref\s*=\s*"([^"]+)"', line)
            if m:
                libraries.setdefault(m[2], []).append(m[1])
    return versions, libraries, plain, comments


def build_files(root):
    found = []
    for base, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ('build', '.gradle', 'node_modules', '.git', 'target')]
        found += [os.path.join(base, n) for n in names if n.endswith('.gradle.kts')]
    return sorted(found)


def gradle_bom_props(plain, sources):
    version = plain.get('spring-boot')
    if not version:
        for src in sources:
            m = re.search(r'org\.springframework\.boot"\)\s*version\s*"([^"]+)"', src)
            if m:
                version = m[1]
                break
    if not version:
        return {}
    pattern = os.path.join(GRADLE_CACHE, 'org.springframework.boot', 'spring-boot-dependencies', version, '*', '*.pom')
    poms = glob.glob(pattern)
    return own_props(load(poms[0]), {}) if poms else {}


def check_gradle(root, trees):
    versions, libraries, plain, comments = read_catalog(root)
    files = build_files(root)
    sources = [open(f).read() for f in files]
    bom = gradle_bom_props(plain, sources)
    paths = gradle_paths(trees)
    count = 0

    # extra["prop"] per catalog-key, of met een letterlijke versie
    extras, literal = {}, []
    for src in sources:
        previous = ''
        for line in src.splitlines():
            m = re.match(r'\s*extra\["([^"]+)"\]\s*=\s*(.+)', line)
            if m:
                ref = re.search(r'libs\.versions\.([\w.]+?)(?:\.asProvider\(\))?\.get\(\)', m[2])
                value = re.match(r'"([^"]+)"', m[2])
                if ref:
                    extras.setdefault(norm(ref[1]), []).append(m[1])
                elif value and re.search(r'CVE-|override', previous, re.I):
                    literal.append((m[1], value[1], previous))
            previous = line

    for key, value in sorted(versions.items()):
        count += 1
        props = extras.get(norm(key), [])
        known = [p for p in props if p in bom]
        if known:
            for prop in known:
                print('%s=%s BOM %s=%s -> %s' % (key, value, prop, bom[prop],
                                                 by_comment(verdict(value, resolve(bom[prop], bom)), comments.get(key))))
        elif props:
            print('%s=%s -> property %s niet in de BOM, %s' % (key, value, props[0], MANUAL))
        elif key in libraries:
            results = [(lib, by_comment(paths.judge(lib, value), comments.get(key))) for lib in libraries[key]]
            removable = [r.startswith(('VEROUDERD', 'OVERBODIG')) for _, r in results]
            mixed = any(removable) and not all(removable)
            for lib, result in results:
                print('%s=%s %s -> %s' % (key, value, lib, 'blijft staan, gemengd: ' + result if mixed else result))
        else:
            print('%s=%s -> geen library of extra gevonden, %s' % (key, value, MANUAL))

    for prop, value, previous in literal:
        count += 1
        if prop in bom:
            print('%s=%s BOM=%s -> %s' % (prop, value, bom[prop], by_comment(verdict(value, resolve(bom[prop], bom)), previous)))
        else:
            print('%s=%s -> property niet in de BOM, %s' % (prop, value, MANUAL))

    constraint = re.compile(r'"([\w.\-]+:[\w.\-]+):([\w.\-+]+)"\s*\)?\s*\{[^}]*because\(\s*"[^"]*CVE-', re.S)
    for f, src in zip(files, sources):
        matched = set()
        for m in constraint.finditer(src):
            count += 1
            print('%s=%s (%s) -> %s' % (m[1], m[2], os.path.relpath(f, root), paths.judge(m[1], m[2])))
            matched.update(range(src.count('\n', 0, m.start()), src.count('\n', 0, m.end()) + 1))
        lines = src.splitlines()
        for i, line in enumerate(lines):
            from_catalog = 'libs.' in line or (i > 0 and 'libs.' in lines[i - 1])
            if 'CVE-' in line and i not in matched and not line.lstrip().startswith('//') and not from_catalog:
                print('%s:%d -> stijl niet herkend, %s' % (os.path.relpath(f, root), i + 1, MANUAL))
    print('overrides: %d' % count)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('pom', nargs='?', default='pom.xml')
    ap.add_argument('--gradle', metavar='ROOT', help='root van een Gradle-project, in plaats van een pom')
    ap.add_argument('--tree', action='append', default=[], help='output van de dependency-boom, herhaalbaar')
    args = ap.parse_args()
    if not args.tree:
        raise SystemExit('--tree is verplicht')
    if args.gradle:
        check_gradle(args.gradle, args.tree)
    else:
        check_maven(args.pom, args.tree)


if __name__ == '__main__':
    main()
