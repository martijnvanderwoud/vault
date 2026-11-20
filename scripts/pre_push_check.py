#!/usr/bin/env python3
"""Weigert een push van de vault als de te pushen commits een geheim bevatten.

Wordt aangeroepen door .git/hooks/pre-push, ongeacht wie of wat de push start. Git geeft per
ref een regel op stdin: <local ref> <local sha> <remote ref> <remote sha>.

Controles op de nieuwe commits:
- een bestand met de naam `.env` of `.env.*` (behalve `.env.example`)
- een toegevoegde regel `NAAM=waarde` voor een naam uit `.env.example`
- veelvoorkomende sleutelpatronen (private key, AWS, GitHub, Slack)
"""
import re
import subprocess
import sys

ZERO = "0" * 40
PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
]


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def env_names():
    try:
        text = git("show", "HEAD:.env.example")
    except subprocess.CalledProcessError:
        return []
    return re.findall(r"^([A-Z][A-Z0-9_]*)=", text, re.M)


def commits_in(local, remote):
    if remote == ZERO:
        return git("rev-list", local, "--not", "--remotes").split()
    return git("rev-list", f"{remote}..{local}").split()


def problems(commit, names):
    found = []
    for path in git("diff-tree", "--no-commit-id", "--name-only", "-r", "--root", commit).split("\n"):
        base = path.rsplit("/", 1)[-1]
        if (base == ".env" or base.startswith(".env.")) and base != ".env.example":
            found.append(f"{commit[:8]}: bestand {path}")
    patch = git("show", "--format=", "--unified=0", commit, "--", ".", ":(exclude).env.example")
    for line in patch.split("\n"):
        if not line.startswith("+") or line.startswith("+++"):
            continue
        for name in names:
            if re.match(rf"\+\s*(export\s+)?{name}\s*=\s*\S{{8,}}", line):
                found.append(f"{commit[:8]}: waarde voor {name}")
        if any(p.search(line) for p in PATTERNS):
            found.append(f"{commit[:8]}: sleutelpatroon in een toegevoegde regel")
    return found


def main():
    names = env_names()
    found = []
    for line in sys.stdin:
        parts = line.split()
        if len(parts) != 4 or parts[1] == ZERO:
            continue
        for commit in commits_in(parts[1], parts[3]):
            found += problems(commit, names)
    if found:
        print("Push geweigerd: mogelijk een geheim in de te pushen commits.", file=sys.stderr)
        for item in sorted(set(found)):
            print(f"  {item}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
