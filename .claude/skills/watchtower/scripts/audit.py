#!/usr/bin/env python3
"""Audit the claude-cowork control repo for drift between its parts.

scripts/validate-config.py checks the structure CI needs. This script adds the
checks that a passing CI does not catch:

  structure    validate-config.py result (every problem is an error)
  skills       description length and trigger, body length, standard sections,
               bundled scripts referenced, scripts covered by a test
  rules        labels and policy keys used in rules match their definitions
  hooks        the guard hook blocks every "never" command in CLAUDE.md;
               settings deny the merge tools the hook cannot see
  workflows    GitHub workflow hygiene; slash commands name real skills
  consistency  repo paths exist; every skill has a blend-decisions entry;
               human skills are in the CLAUDE.md list; README skill count

Severity: error (broken), warn (drift or a gap), info (style).

Usage:
  audit.py [--root <clone>] [--json] [--area <area>] [--skill <name>]
Exit 1 when any error is found, 0 otherwise.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

AREAS = ("structure", "skills", "rules", "hooks", "workflows", "consistency")
SEVERITIES = ("error", "warn", "info")
DESC_MAX = 1024
DESC_MIN = 80
BODY_MAX_LINES = 500
WORKFLOW_SECTIONS = ("Purpose", "When to use / not use", "Outputs", "Stop conditions", "Anti-rationalization")
# Slash commands that are Claude Code commands or HTTP paths, not skills.
NON_SKILL_SLASH = {"loop", "fire", "health", "compact", "clear", "help", "config", "fast", "gan-build",
                   "skill-doctor", "artifacts", "plugin"}
# Paths that exist only in this repo. Skills also name paths in target repos (`docs/adr/`), so those
# are checked only in the control-repo docs.
CONTROL_PREFIXES = (".claude/skills/", ".claude/agents/", ".claude/hooks/", "registry/", "scripts/",
                    "templates/", ".github/workflows/")
DOC_PREFIXES = CONTROL_PREFIXES + ("docs/",)
# HTML comment markers (`<!-- ai:plan ... -->`) and mentions of them are not labels.
MARKER_RE = re.compile(r"<!--.*?(-->|$)|`ai:[a-z-]+` (?:marker|comment)|ai:[a-z-]+ [a-z_]+=", re.MULTILINE)
LABEL_RE = re.compile(r"(?<![\w/-])((?:ai|size):[a-z][a-z-]*[a-z])")
NEVER_BRANCHES_RE = re.compile(r"Never push to ((?:`[a-z]+`,?\s*(?:or\s*)?)+)")
# Commands the CLAUDE.md global rules forbid. Each must be blocked by the guard hook.
HOOK_PROBES = (
    ("gh pr merge 12 --squash", "Never approve, merge, or deploy to production"),
    ("gh pr review 12 --approve", "Never approve, merge, or deploy to production"),
    ("git push --force origin ai/1-x", "Never force-push"),
    ("gh api -X PUT repos/o/r/pulls/12/merge", "Never merge a PR ... through the API"),
    ("gh api -X POST repos/o/r/merges -f base=development -f head=ai/1-x", "Never merge branches through the API"),
    ("cat ~/.aws/credentials", "No secrets. Never read credentials"),
)
MCP_MERGE_TOOLS = ("mcp__github__merge_pull_request", "mcp__github__enable_pr_auto_merge")
# A comparison against the fix cap. Only CLAUDE.md -> "Stop cleanly" may define one; other lines link to it.
FIX_CAP_COMPARE_RE = re.compile(
    r"(exceed\w*|at or above|fewer than|below|less than|more than|equal\w*|(?<!-)>=?|<=?)\s+(?:the\s+)?`?max_fix_attempts`?",
    re.IGNORECASE)


class Audit:
    def __init__(self, root: Path):
        self.root = root
        self.findings: list[dict] = []

    def add(self, severity, area, path, message):
        f = {"severity": severity, "area": area, "path": str(path), "message": message}
        if f not in self.findings:
            self.findings.append(f)

    def read(self, rel):
        p = self.root / rel
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def skill_dirs(self):
        d = self.root / ".claude" / "skills"
        return sorted(p for p in d.iterdir() if (p / "SKILL.md").exists()) if d.exists() else []


def split_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    return (fm if isinstance(fm, dict) else {}), m.group(2)


def human_skills(claude_md):
    """Names in the CLAUDE.md human-invoked list."""
    names, inside = set(), False
    for line in claude_md.splitlines():
        if line.startswith("Human-invoked skills"):
            inside = True
            continue
        if inside:
            m = re.match(r"^- `([a-z0-9-]+)`:", line)
            if not m:
                break
            names.add(m.group(1))
    return names


# --- structure ---------------------------------------------------------------

def check_structure(a: Audit):
    script = a.root / "scripts" / "validate-config.py"
    if not script.exists():
        a.add("error", "structure", "scripts/validate-config.py", "validator missing")
        return
    out = subprocess.run([sys.executable, str(script), str(a.root)], capture_output=True, text=True)
    for line in out.stdout.splitlines():
        if line.startswith("  - "):
            path, _, msg = line[4:].partition(": ")
            a.add("error", "structure", path, msg or path)
    if out.returncode not in (0, 1):
        a.add("error", "structure", "scripts/validate-config.py", f"crashed: {out.stderr.strip()[-200:]}")


# --- skills ------------------------------------------------------------------

def check_skills(a: Audit, only=None):
    unversioned = []
    tests = "\n".join(p.read_text(encoding="utf-8") for p in sorted((a.root / "tests").glob("test_*.py")))
    for d in a.skill_dirs():
        if only and d.name != only:
            continue
        rel = f".claude/skills/{d.name}/SKILL.md"
        text = (d / "SKILL.md").read_text(encoding="utf-8")
        fm, body = split_frontmatter(text)
        desc = " ".join(str(fm.get("description") or "").split())
        if len(desc) > DESC_MAX:
            a.add("error", "skills", rel, f"description has {len(desc)} chars; the limit is {DESC_MAX}")
        elif 0 < len(desc) < DESC_MIN:
            a.add("warn", "skills", rel, f"description has {len(desc)} chars; too short to trigger reliably")
        if desc and not re.search(r"\b(Use|Load|Invoke)\b", desc):
            a.add("warn", "skills", rel, "description says what, not when: add a 'Use when ...' trigger")
        lines = text.count("\n") + 1
        if lines > BODY_MAX_LINES:
            a.add("warn", "skills", rel, f"{lines} lines; move detail into references/ (limit {BODY_MAX_LINES})")
        if not (fm.get("metadata") or {}).get("version") and not d.name.startswith("stack-"):
            unversioned.append(d.name)
        if not d.name.startswith("stack-"):
            heads = set(re.findall(r"^## (.+?)\s*$", body, re.MULTILINE))
            missing = [s for s in WORKFLOW_SECTIONS if s not in heads]
            if missing:
                a.add("warn", "skills", rel, f"missing standard sections: {', '.join(missing)}")
        refs = set(re.findall(r"(?:scripts|references)/[\w.-]+\.\w+", body))
        for r in sorted(refs):
            if not (d / r).exists() and not (a.root / r).exists():
                a.add("error", "skills", rel, f"references {r}, which does not exist")
        for sub in ("scripts", "references"):
            for f in sorted((d / sub).glob("*")) if (d / sub).exists() else []:
                if f.is_file() and f.suffix != ".pyc" and f"{sub}/{f.name}" not in refs:
                    a.add("warn", "skills", f".claude/skills/{d.name}/{sub}/{f.name}", "bundled file not referenced in SKILL.md")
                if sub == "scripts" and f.suffix == ".py" and not re.search(rf"\b{re.escape(f.stem)}\b", tests):
                    a.add("warn", "skills", f".claude/skills/{d.name}/scripts/{f.name}", "script has no test in tests/")
    if unversioned:
        a.add("info", "skills", ".claude/skills/", f"metadata.version missing in {len(unversioned)} skills: {', '.join(unversioned)}")


# --- rules -------------------------------------------------------------------

def defined_labels(a: Audit):
    return set(re.findall(r'"((?:ai|size):[a-z-]+)\|', a.read("scripts/setup-labels.sh")))


def check_rules(a: Audit):
    defined = defined_labels(a)
    if not defined:
        a.add("error", "rules", "scripts/setup-labels.sh", "no label definitions found")
        return
    documented = set(re.findall(r"^\| `((?:ai|size):[a-z-]+)` \|", a.read("docs/labels-and-states.md"), re.MULTILINE))
    for lab in sorted(defined - documented):
        a.add("warn", "rules", "docs/labels-and-states.md", f"label {lab} is created by setup-labels.sh but not documented")
    for lab in sorted(documented - defined):
        a.add("error", "rules", "scripts/setup-labels.sh", f"label {lab} is documented but never created")
    sources = [a.root / "CLAUDE.md", a.root / "scripts" / "project_sync.py"]
    sources += sorted((a.root / ".claude").rglob("*.md")) + sorted((a.root / "docs").glob("*.md"))
    sources += sorted((a.root / ".claude" / "skills").rglob("*.py"))
    for p in sources:
        if p.name == "blend-decisions.md" or "__pycache__" in p.parts:
            continue  # blend-decisions quotes upstream sources
        text = MARKER_RE.sub("", p.read_text(encoding="utf-8"))
        for lab in sorted(set(LABEL_RE.findall(text)) - defined):
            a.add("error", "rules", p.relative_to(a.root), f"uses label {lab}, which setup-labels.sh does not create")
    policy = yaml.safe_load(a.read("registry/policy.yml")) or {}
    keys = set()

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                keys.add(str(k))
                walk(v)
    walk(policy)
    cap_sources = sorted((a.root / ".claude").rglob("*.md")) + sorted((a.root / "docs").glob("*.md"))
    for p in cap_sources:
        if p.name == "blend-decisions.md":
            continue
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if FIX_CAP_COMPARE_RE.search(line) and "Stop cleanly" not in line:
                a.add("error", "rules", f"{p.relative_to(a.root)}:{n}",
                      "restates the max_fix_attempts comparison; link CLAUDE.md -> \"Stop cleanly\" instead")
    for p in [a.root / "CLAUDE.md"] + sorted((a.root / ".claude").rglob("*.md")):
        for line in p.read_text(encoding="utf-8").splitlines():
            if "policy.yml" not in line:
                continue
            for k in re.findall(r"`([a-z]+(?:_[a-z]+)+)`", line):
                if k not in keys:
                    a.add("error", "rules", p.relative_to(a.root), f"policy key `{k}` is not in registry/policy.yml")


# --- hooks -------------------------------------------------------------------

def run_hook(hook: Path, command: str):
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, CLAUDE_PROJECT_DIR=tmp)
        payload = json.dumps({"tool_input": {"command": command}, "cwd": tmp})
        return subprocess.run([sys.executable, str(hook)], input=payload, capture_output=True, text=True,
                              env=env, cwd=tmp).returncode


def check_hooks(a: Audit):
    hook = a.root / ".claude" / "hooks" / "guard_bash.py"
    if not hook.exists():
        a.add("error", "hooks", ".claude/hooks/guard_bash.py", "guard hook missing")
        return
    probes = list(HOOK_PROBES)
    m = NEVER_BRANCHES_RE.search(a.read("CLAUDE.md"))
    for b in re.findall(r"`([a-z]+)`", m.group(1)) if m else []:
        probes.append((f"git push origin HEAD:{b}", f"Never push to `{b}`"))
    for cmd, rule in probes:
        if run_hook(hook, cmd) != 2:
            a.add("warn", "hooks", ".claude/hooks/guard_bash.py", f"does not block `{cmd}` (CLAUDE.md: {rule})")
    if not re.search(r"guard_bash", "\n".join(p.name + p.read_text(encoding="utf-8")
                                             for p in (a.root / "tests").glob("test_*.py"))):
        a.add("warn", "hooks", "tests/", "guard hook has no tests")
    settings = json.loads(a.read(".claude/settings.json") or "{}")
    deny = set(settings.get("permissions", {}).get("deny", []) or [])
    for tool in MCP_MERGE_TOOLS:
        if tool not in deny:
            a.add("warn", "hooks", ".claude/settings.json",
                  f"permissions.deny lacks {tool}; the Bash hook cannot see MCP calls")
    for event, groups in (settings.get("hooks") or {}).items():
        for g in groups or []:
            for h in g.get("hooks", []):
                if h.get("type") == "command" and not h.get("timeout"):
                    a.add("info", "hooks", ".claude/settings.json", f"{event} hook has no timeout")


# --- workflows ---------------------------------------------------------------

def check_workflows(a: Audit, skills: set[str]):
    for p in sorted((a.root / ".github" / "workflows").glob("*.y*ml")):
        rel = p.relative_to(a.root)
        try:
            wf = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue  # structure reports it
        if "permissions" not in wf:
            a.add("warn", "workflows", rel, "no top-level permissions; the token gets the repo default")
        for name, job in (wf.get("jobs") or {}).items():
            if "timeout-minutes" not in job:
                a.add("warn", "workflows", rel, f"job {name} has no timeout-minutes")
            for step in job.get("steps") or []:
                uses = str(step.get("uses") or "")
                if re.search(r"@(main|master|HEAD)$", uses) or (uses and "@" not in uses and not uses.startswith("./")):
                    a.add("warn", "workflows", rel, f"action {uses} is not pinned to a version")
                if uses.startswith("actions/checkout") and (step.get("with") or {}).get("persist-credentials") is not False:
                    a.add("info", "workflows", rel, f"job {name}: checkout keeps credentials; set persist-credentials: false")
    files = [a.root / "CLAUDE.md", a.root / "README.md"] + sorted((a.root / "docs").glob("*.md"))
    files += sorted((a.root / ".claude").rglob("*.md"))
    for p in files:
        if not p.exists() or p.name == "blend-decisions.md":
            continue
        for name in sorted(set(re.findall(r"`/([a-z][a-z-]+)(?:\s[^`]*)?`", p.read_text(encoding="utf-8")))):
            if name not in skills and name not in NON_SKILL_SLASH:
                a.add("error", "workflows", p.relative_to(a.root), f"slash command /{name} has no skill")


# --- consistency -------------------------------------------------------------

def check_consistency(a: Audit, skills: set[str]):
    files = [a.root / "CLAUDE.md", a.root / "README.md"] + sorted((a.root / "docs").glob("*.md"))
    files += sorted((a.root / ".claude").rglob("*.md"))
    for p in files:
        if not p.exists() or p.name == "blend-decisions.md":
            continue
        skill_dir = p.parent if p.name == "SKILL.md" else None
        control_doc = p.parent == a.root or p.parent == a.root / "docs"
        prefixes = DOC_PREFIXES if control_doc else CONTROL_PREFIXES
        for ref in sorted(set(re.findall(r"`([.\w/-]+)`", p.read_text(encoding="utf-8")))):
            if not ref.startswith(prefixes):
                continue
            if skill_dir and (skill_dir / ref).exists():
                continue
            if not (a.root / ref).exists():
                a.add("warn", "consistency", p.relative_to(a.root), f"path `{ref}` does not exist")
    blend = a.read("docs/blend-decisions.md")
    for s in sorted(skills):
        if not re.search(rf"^### {re.escape(s)}\b", blend, re.MULTILINE):
            a.add("warn", "consistency", "docs/blend-decisions.md", f"no entry for skill {s}")
    claude_md = a.read("CLAUDE.md")
    listed = human_skills(claude_md)
    for d in a.skill_dirs():
        fm, _ = split_frontmatter((d / "SKILL.md").read_text(encoding="utf-8"))
        desc = str(fm.get("description") or "")
        if re.search(r"human in an interactive session", desc) and d.name not in listed:
            a.add("warn", "consistency", "CLAUDE.md", f"human-invoked skill {d.name} is not in the human-invoked list")
    for s in sorted(listed - skills):
        a.add("error", "consistency", "CLAUDE.md", f"human-invoked list names {s}, which does not exist")
    readme = a.read("README.md")
    m = re.search(r"`\.claude/skills/`\s*\|\s*(.+?)\|", readme)
    if m:
        missing = sorted(s for s in listed if f"`{s}`" not in m.group(1))
        if missing:
            a.add("warn", "consistency", "README.md", f"skills table row omits human-invoked skills: {', '.join(missing)}")


# --- output ------------------------------------------------------------------

def run(root: Path, area=None, skill=None):
    a = Audit(root)
    skills = {d.name for d in a.skill_dirs()}
    if skill:
        check_skills(a, skill)
        return a.findings
    steps = {
        "structure": lambda: check_structure(a),
        "skills": lambda: check_skills(a),
        "rules": lambda: check_rules(a),
        "hooks": lambda: check_hooks(a),
        "workflows": lambda: check_workflows(a, skills),
        "consistency": lambda: check_consistency(a, skills),
    }
    for name in ([area] if area else AREAS):
        steps[name]()
    order = {s: i for i, s in enumerate(SEVERITIES)}
    return sorted(a.findings, key=lambda f: (AREAS.index(f["area"]), order[f["severity"]], f["path"]))


def render(findings):
    counts = {s: sum(f["severity"] == s for f in findings) for s in SEVERITIES}
    out = [f"watchtower: {counts['error']} error, {counts['warn']} warn, {counts['info']} info"]
    for area in AREAS:
        rows = [f for f in findings if f["area"] == area]
        if rows:
            out += ["", f"## {area} ({len(rows)})"]
            out += [f"- [{f['severity']}] `{f['path']}`: {f['message']}" for f in rows]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[4]))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--area", choices=AREAS)
    ap.add_argument("--skill")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    if args.skill and not (root / ".claude" / "skills" / args.skill / "SKILL.md").exists():
        print(f"error: no skill named {args.skill}", file=sys.stderr)
        return 2
    findings = run(root, args.area, args.skill)
    print(json.dumps(findings, indent=2) if args.json else render(findings))
    return 1 if any(f["severity"] == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
