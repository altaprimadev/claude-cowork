#!/usr/bin/env python3
"""Validate the claude-cowork configuration.

Checks:
  1. Every JSON and YAML file in the repo parses (.git excluded).
  2. .claude/settings.json has the expected shape; hook command paths exist.
  3. Every .claude/skills/<dir>/SKILL.md has frontmatter `name` == <dir> and a
     non-empty `description`.
  4. Every skill has a `Skill(<name>)` rule in permissions.allow.
  5. Every .claude/agents/<file>.md has frontmatter `name` == <file>,
     `description`, and `tools`. Read-only reviewers have no write tools.
  6. Every skill referenced by an agent (frontmatter `skills:` or a backticked
     skill-like name in the body) and by CLAUDE.md exists. Every agent in the
     CLAUDE.md stage map exists.
  7. Registry, policy, and profile template have valid values.
  8. Every SKILL.md and agent file ends with an attribution line.
  9. No obvious secrets are committed.

Usage: python3 scripts/validate-config.py [repo_root]
Exit 0 when all checks pass, 1 otherwise.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: PyYAML is required (pip install pyyaml).", file=sys.stderr)
    sys.exit(1)

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".pytest_cache"}
READ_ONLY_AGENTS = {"spec-reviewer", "quality-reviewer", "task-reviewer"}
WRITE_TOOLS = {"Write", "Edit", "NotebookEdit", "MultiEdit"}
ATTRIBUTION_RE = re.compile(r"Adapted from .+\(MIT\)", re.IGNORECASE)
SECRET_PATTERNS = {
    "GitHub token": r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{40,}\b",
    "Anthropic key": r"\bsk-ant-[A-Za-z0-9_-]{20,}\b",
    "AWS access key": r"\bAKIA[0-9A-Z]{16}\b",
    "Private key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
}

errors: list[str] = []


def err(msg: str) -> None:
    if msg not in errors:
        errors.append(msg)


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def walk(suffixes: tuple[str, ...]):
    for p in sorted(ROOT.rglob("*")):
        if p.is_file() and p.suffix in suffixes and not (set(p.relative_to(ROOT).parts) & SKIP_DIRS):
            yield p


def frontmatter(path: Path) -> tuple[dict | None, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    if not m:
        err(f"{rel(path)}: missing YAML frontmatter")
        return None, text
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as exc:
        err(f"{rel(path)}: invalid frontmatter YAML: {exc}")
        return None, m.group(2)
    if not isinstance(data, dict):
        err(f"{rel(path)}: frontmatter is not a mapping")
        return None, m.group(2)
    return data, m.group(2)


def as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    if isinstance(value, list):
        return [str(v).strip() for v in value]
    return []


# ---------------------------------------------------------------------------


def check_parse_all() -> None:
    for p in walk((".json",)):
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except ValueError as exc:
            err(f"{rel(p)}: invalid JSON: {exc}")
    for p in walk((".yml", ".yaml")):
        try:
            list(yaml.safe_load_all(p.read_text(encoding="utf-8")))
        except yaml.YAMLError as exc:
            err(f"{rel(p)}: invalid YAML: {exc}")


def load_settings() -> dict:
    path = ROOT / ".claude" / "settings.json"
    if not path.exists():
        err(".claude/settings.json: missing")
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return {}  # already reported
    if not isinstance(data.get("permissions", {}).get("allow"), list):
        err(".claude/settings.json: permissions.allow must be a list")
    return data


def check_hooks(settings: dict) -> None:
    hooks = settings.get("hooks", {})
    if not isinstance(hooks, dict):
        err(".claude/settings.json: hooks must be an object")
        return
    found = False
    for event, groups in hooks.items():
        for group in groups if isinstance(groups, list) else []:
            for hook in group.get("hooks", []):
                if hook.get("type") != "command":
                    continue
                cmd = hook.get("command", "")
                for token in re.findall(r"[\w$./{}\"-]*\.claude/[\w./-]+", cmd):
                    path = re.sub(r"^.*?\.claude/", ".claude/", token.strip('"'))
                    found = True
                    if not (ROOT / path).exists():
                        err(f".claude/settings.json: {event} hook path does not exist: {path}")
    if not found:
        err(".claude/settings.json: no hook command references a .claude/ script")


def check_skills(settings: dict) -> set[str]:
    skills: set[str] = set()
    skills_dir = ROOT / ".claude" / "skills"
    for d in sorted(p for p in skills_dir.iterdir() if p.is_dir()) if skills_dir.exists() else []:
        md = d / "SKILL.md"
        if not md.exists():
            err(f"{rel(d)}: missing SKILL.md")
            continue
        fm, body = frontmatter(md)
        skills.add(d.name)
        if fm is None:
            continue
        if fm.get("name") != d.name:
            err(f"{rel(md)}: frontmatter name '{fm.get('name')}' != folder '{d.name}'")
        if not str(fm.get("description") or "").strip():
            err(f"{rel(md)}: missing description")
        if not ATTRIBUTION_RE.search(body.strip().splitlines()[-1] if body.strip() else ""):
            err(f"{rel(md)}: last line must be the attribution line")
    allow = set(settings.get("permissions", {}).get("allow", []) or [])
    for s in sorted(skills):
        if f"Skill({s})" not in allow:
            err(f".claude/settings.json: permissions.allow lacks Skill({s})")
    for rule in sorted(allow):
        m = re.fullmatch(r"Skill\(([^)* ]+)\)", rule)
        if m and m.group(1) not in skills:
            err(f".claude/settings.json: Skill({m.group(1)}) allowed but the skill does not exist")
    return skills


def referenced_skill_names(text: str, skills: set[str]) -> set[str]:
    """Backticked names that look like skills of this repo."""
    names = set()
    for tok in re.findall(r"`([a-z0-9][a-z0-9-]*)`", text):
        if tok.startswith("stack-") or tok in skills:
            names.add(tok)
    return names


def check_agents(skills: set[str]) -> set[str]:
    agents: set[str] = set()
    agents_dir = ROOT / ".claude" / "agents"
    if not agents_dir.exists():
        err(".claude/agents: missing")
        return agents
    for md in sorted(agents_dir.glob("*.md")):
        fm, body = frontmatter(md)
        agents.add(md.stem)
        if fm is None:
            continue
        if fm.get("name") != md.stem:
            err(f"{rel(md)}: frontmatter name '{fm.get('name')}' != file name '{md.stem}'")
        if not str(fm.get("description") or "").strip():
            err(f"{rel(md)}: missing description")
        tools = set(as_list(fm.get("tools")))
        if not tools:
            err(f"{rel(md)}: missing tools allowlist")
        if md.stem in READ_ONLY_AGENTS and tools & WRITE_TOOLS:
            err(f"{rel(md)}: read-only reviewer has write tools {sorted(tools & WRITE_TOOLS)}")
        for s in as_list(fm.get("skills")):
            if s not in skills:
                err(f"{rel(md)}: frontmatter skill '{s}' does not exist")
        for s in referenced_skill_names(body, skills):
            if s not in skills:
                err(f"{rel(md)}: references unknown skill '{s}'")
        if not ATTRIBUTION_RE.search(body.strip().splitlines()[-1] if body.strip() else ""):
            err(f"{rel(md)}: last line must be the attribution line")
    return agents


def check_claude_md(skills: set[str], agents: set[str]) -> None:
    path = ROOT / "CLAUDE.md"
    if not path.exists():
        err("CLAUDE.md: missing")
        return
    text = path.read_text(encoding="utf-8")
    rows = [r for r in text.splitlines() if r.startswith("|") and not re.match(r"^\|[-\s|]+\|$", r)]
    map_rows = [r for r in rows if "`" in r]
    if not map_rows:
        err("CLAUDE.md: stage map table not found")
    mapped_agents = set()
    for row in map_rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) < 4:
            continue
        for a in re.findall(r"`([a-z0-9-]+)`", cells[2]):
            mapped_agents.add(a)
            if a not in agents:
                err(f"CLAUDE.md: stage map agent '{a}' has no .claude/agents/{a}.md")
        for s in re.findall(r"`([a-z0-9-]+)`", cells[3]):
            if s not in skills:
                err(f"CLAUDE.md: stage map skill '{s}' does not exist")
    for a in sorted(agents - mapped_agents):
        err(f"CLAUDE.md: agent '{a}' is missing from the stage map")
    for s in referenced_skill_names(text, skills):
        if s not in skills:
            err(f"CLAUDE.md: references unknown skill '{s}'")


def check_registry(skills: set[str]) -> None:
    def load(p: str):
        path = ROOT / p
        if not path.exists():
            err(f"{p}: missing")
            return None
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            return None

    repos = load("registry/repos.yml")
    if isinstance(repos, dict):
        for i, r in enumerate(repos.get("repos") or []):
            where = f"registry/repos.yml: repos[{i}]"
            if not re.fullmatch(r"[\w.-]+/[\w.-]+", str(r.get("name", ""))):
                err(f"{where}: name must be owner/repo")
            if r.get("status") not in {"detected", "onboarding", "active", "frozen"}:
                err(f"{where}: invalid status {r.get('status')!r}")
            if r.get("autonomy") not in {0, 1, 2}:
                err(f"{where}: autonomy must be 0, 1, or 2")
            if r.get("environment") not in {"hosted", "self-hosted"}:
                err(f"{where}: environment must be hosted or self-hosted")
            if "branch_protection" in r and r["branch_protection"] != "unavailable":
                err(f"{where}: branch_protection must be 'unavailable' or absent")
    elif repos is not None:
        err("registry/repos.yml: top level must be a mapping with 'repos'")

    policy = load("registry/policy.yml")
    if isinstance(policy, dict):
        for key in ("max_parallel_sessions", "max_parallel_tasks_per_repo", "trivial_change_max_lines"):
            if not isinstance(policy.get(key), int) or policy[key] < 1:
                err(f"registry/policy.yml: {key} must be a positive integer")
        gates = policy.get("gates") or {}
        if gates.get("production") != "human_only":
            err("registry/policy.yml: gates.production must be human_only")
        for g in ("design", "code"):
            if g not in gates:
                err(f"registry/policy.yml: gates.{g} missing")

    profile = load("templates/profile.yml")
    if isinstance(profile, dict):
        for key in ("stack", "packs", "commands", "test_types", "coverage_target", "coverage_paths",
                    "deploy", "autonomy", "environment", "depends_on"):
            if key not in profile:
                err(f"templates/profile.yml: missing field {key}")
        for p in profile.get("packs") or []:
            if p not in skills or not p.startswith("stack-"):
                err(f"templates/profile.yml: pack '{p}' is not a stack skill")
        for c in ("install", "lint", "typecheck", "test", "build"):
            if c not in (profile.get("commands") or {}):
                err(f"templates/profile.yml: commands.{c} missing")
        if profile.get("autonomy") != 0:
            err("templates/profile.yml: autonomy must default to 0")


def check_secrets() -> None:
    for p in walk((".md", ".json", ".yml", ".yaml", ".py", ".sh", ".txt", "")):
        if p.name == "validate-config.py":
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, rx in SECRET_PATTERNS.items():
            if re.search(rx, text):
                err(f"{rel(p)}: possible {label} committed")


def main() -> int:
    check_parse_all()
    settings = load_settings()
    check_hooks(settings)
    skills = check_skills(settings)
    agents = check_agents(skills)
    check_claude_md(skills, agents)
    check_registry(skills)
    check_secrets()

    if errors:
        print(f"FAIL: {len(errors)} problem(s)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK: {len(skills)} skills, {len(agents)} agents, settings, registry, and templates are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
