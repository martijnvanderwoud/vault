#!/usr/bin/env python3
"""Schrijf in elke map van de vault een index.md (gegenereerd, niet met de hand bewerken)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".obsidian", ".claude", ".search-index", "__pycache__"}
INDEX = "index.md"


def description(note: Path) -> str:
    """Lees `description` uit de YAML-frontmatter (simpele parser, geen dependencies)."""
    lines = note.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, _, value = line.partition(":")
        if key.strip() == "description":
            return value.strip().strip("\"'")
    return ""


def render(folder: Path) -> str:
    name = folder.name if folder != ROOT else "vault"
    out = [
        "---",
        f"description: Gegenereerde index van {name}",
        "---",
        f"# {name}",
        "",
        "_Gegenereerd door scripts/build_index.py, niet met de hand bewerken._",
    ]
    entries = sorted(folder.iterdir(), key=lambda p: p.name)
    subdirs = [p for p in entries if p.is_dir() and p.name not in SKIP_DIRS]
    notes = [p for p in entries if p.is_file() and p.suffix == ".md" and p.name != INDEX]

    if subdirs:
        out += ["", "## Submappen", ""]
        for d in subdirs:
            rel = (d / INDEX).relative_to(ROOT).with_suffix("")
            out.append(f"- [[{rel}|{d.name}]]")
    if notes:
        out += ["", "## Notities", ""]
        for n in notes:
            desc = description(n)
            out.append(f"- [[{n.stem}]] — {desc}" if desc else f"- [[{n.stem}]]")
    return "\n".join(out) + "\n"


def build(folder: Path) -> None:
    content = render(folder)
    target = folder / INDEX
    if not target.exists() or target.read_text(encoding="utf-8") != content:
        target.write_text(content, encoding="utf-8")
    for d in sorted(folder.iterdir()):
        if d.is_dir() and d.name not in SKIP_DIRS:
            build(d)


if __name__ == "__main__":
    build(ROOT)
