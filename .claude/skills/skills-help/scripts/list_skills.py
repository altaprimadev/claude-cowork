#!/usr/bin/env python3
"""List the claude-cowork skills with their descriptions.

Reads every .claude/skills/<name>/SKILL.md frontmatter and groups the skills:
  human     human-invoked skills (CLAUDE.md "Human-invoked skills" list)
  pipeline  skills in the CLAUDE.md stage map
  pack      stack packs (name starts with "stack-")
  utility   everything else

Usage:
  list_skills.py [--root <claude-cowork clone>] [--json] [name]
With a name, print that skill's full description and argument hint.
"""
import argparse
import json
import re
import sys
from pathlib import Path

GROUPS = ("human", "pipeline", "utility", "pack")
TITLES = {
    "human": "Human-invoked (call these yourself)",
    "pipeline": "Pipeline stages (run by the scheduled tasks)",
    "utility": "Utilities",
    "pack": "Stack packs (loaded per repo profile)",
}
NAME_RE = re.compile(r"`([a-z0-9][a-z0-9-]*)`")


def frontmatter(path):
    import yaml
    m = re.match(r"^---\n(.*?)\n---", path.read_text(encoding="utf-8"), re.DOTALL)
    return (yaml.safe_load(m.group(1)) or {}) if m else {}


def roles(claude_md):
    """Return (human, pipeline) skill name sets parsed from CLAUDE.md."""
    text = claude_md.read_text(encoding="utf-8") if claude_md.exists() else ""
    human, pipeline = set(), set()
    in_human = False
    for line in text.splitlines():
        if line.startswith("Human-invoked skills"):
            in_human = True
            continue
        if in_human:
            m = re.match(r"^- `([a-z0-9-]+)`:", line)
            if m:
                human.add(m.group(1))
                continue
            in_human = False
        cells = [c.strip() for c in line.split("|")]
        if len(cells) >= 6 and line.startswith("|"):
            pipeline.update(NAME_RE.findall(cells[4]))
    return human, pipeline


def first_sentence(text):
    m = re.match(r"(.+?[.!?])(\s|$)", text.strip())
    return m.group(1) if m else text.strip()


def collect(root):
    human, pipeline = roles(root / "CLAUDE.md")
    skills = []
    for f in sorted((root / ".claude" / "skills").glob("*/SKILL.md")):
        fm = frontmatter(f)
        name = fm.get("name") or f.parent.name
        if name in human:
            group = "human"
        elif name in pipeline:
            group = "pipeline"
        elif name.startswith("stack-"):
            group = "pack"
        else:
            group = "utility"
        skills.append({"name": name, "group": group,
                       "description": " ".join(str(fm.get("description", "")).split()),
                       "argument_hint": fm.get("argument-hint", "")})
    return skills


def render(skills):
    out = []
    for g in GROUPS:
        rows = [s for s in skills if s["group"] == g]
        if not rows:
            continue
        out.append(f"{TITLES[g]}:")
        for s in rows:
            call = f"/{s['name']}" + (f" {s['argument_hint']}" if s["argument_hint"] else "")
            out.append(f"- {call}: {first_sentence(s['description'])}")
        out.append("")
    return "\n".join(out).rstrip()


def render_one(s):
    lines = [f"/{s['name']}" + (f" {s['argument_hint']}" if s["argument_hint"] else ""),
             f"group: {s['group']}", "", s["description"]]
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("name", nargs="?", help="show one skill in full")
    p.add_argument("--root", default=str(Path(__file__).resolve().parents[4]),
                   help="claude-cowork clone (default: this script's repo)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    a = p.parse_args(argv)
    skills = collect(Path(a.root))
    if a.name:
        match = [s for s in skills if s["name"] == a.name.lstrip("/")]
        if not match:
            print(f"error: no skill named {a.name}. Known: {', '.join(s['name'] for s in skills)}",
                  file=sys.stderr)
            return 1
        print(json.dumps(match[0], indent=2) if a.json else render_one(match[0]))
        return 0
    print(json.dumps(skills, indent=2) if a.json else render(skills))
    return 0


if __name__ == "__main__":
    sys.exit(main())
