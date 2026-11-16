#!/usr/bin/python3
"""Schrijft de dependency-lijsten van een sbt-project, met en zonder overrides.

Draai vanuit de root van het project. De projecten komen uit `sbt projects`, zonder `root`,
zodat een nieuwe module vanzelf meegaat. Per project en per configuratie (Compile, Test)
schrijft `dependencyTree list` een bestand naar <map>/met/<project>-<config>.txt en, met
`set ThisBuild / dependencyOverrides := Seq()`, naar <map>/zonder/. De map wordt eerst leeg
gemaakt, maar alleen als hij niets anders bevat dan `met` en `zonder`. Het script sluit de
achtergrondserver van sbt vooraf en achteraf af: de `set` blijft daar anders hangen, en een
`set` uit een eerdere sessie zou de lijst met overrides beïnvloeden.

Een script, want lussen en $(...) weigert de autonome run.
Exit 1 als er geen projecten zijn (dan klopt het filter op de uitvoer van sbt niet meer), als
de map iets anders bevat of als er een bestand ontbreekt.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

CONFIGS = ('Compile', 'Test')
ANSI = re.compile(r'\x1b\[[0-9;?]*[A-Za-z]')
PROJECT = re.compile(r'^\[info\]\s+\*?\s*([A-Za-z0-9_-]+)\s*$')


def sbt(*args):
    result = subprocess.run(['sbt', *args], capture_output=True, text=True)
    return result.returncode, ANSI.sub('', result.stdout + result.stderr)


def projects():
    code, out = sbt('projects')
    if code != 0:
        sys.exit(f'sbt projects mislukt (exit {code}):\n{out[-2000:]}')
    names = [m.group(1) for m in map(PROJECT.match, out.splitlines()) if m]
    return [n for n in names if n != 'root']


def tasks(names, out_dir):
    return [f'{p}/{c}/dependencyTree list --out {os.path.join(out_dir, f"{p}-{c}.txt")}'
            for p in names for c in CONFIGS]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('map', help='absolute map voor de lijsten, bijvoorbeeld <scratchpad>/deps')
    args = parser.parse_args()
    root = os.path.abspath(args.map)
    if os.path.isdir(root) and not set(os.listdir(root)) <= {'met', 'zonder'}:
        sys.exit(f'{root} bevat meer dan met/ en zonder/: kies een eigen map, bijvoorbeeld <scratchpad>/deps')

    sbt('shutdown')
    names = projects()
    print(f'projecten ({len(names)}): {" ".join(names)}')
    if not names:
        sys.exit('geen projecten gevonden: het filter op `sbt projects` klopt niet meer')

    met, zonder = os.path.join(root, 'met'), os.path.join(root, 'zonder')
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(met)
    os.makedirs(zonder)

    try:
        for label, commands in (
            ('met', tasks(names, met)),
            ('zonder', ['set ThisBuild / dependencyOverrides := Seq()'] + tasks(names, zonder)),
        ):
            code, out = sbt('; '.join(commands))
            if code != 0:
                sys.exit(f'sbt {label} overrides mislukt (exit {code}):\n{out[-2000:]}')
    finally:
        sbt('shutdown')

    missing = [os.path.join(d, f'{p}-{c}.txt')
               for d in (met, zonder) for p in names for c in CONFIGS
               if not os.path.isfile(os.path.join(d, f'{p}-{c}.txt'))]
    if missing:
        sys.exit('ontbrekende lijsten:\n' + '\n'.join(missing))
    print(f'lijsten: {len(names) * len(CONFIGS)} met, {len(names) * len(CONFIGS)} zonder overrides in {root}')


if __name__ == '__main__':
    main()
