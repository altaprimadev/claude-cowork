#!/usr/bin/env python3
"""PreToolUse guard for the Bash tool.

Second safety layer. The first layer is GitHub branch protection, required
checks, and CODEOWNERS. This hook never replaces them.

Contract:
- Reads the hook payload (JSON) from stdin. The command is in
  payload["tool_input"]["command"].
- Exit 2 with a reason on stderr: the command is blocked.
- Exit 0: the command is allowed.
- Malformed or unexpected input: allow (exit 0) and warn on stderr, so a
  broken payload never kills the session.

Extend the rules by editing the constants below, or by adding entries to
.claude/hooks/guard_bash.config.json (see CONFIG_KEYS).
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------
# Rule constants. Edit here or override/extend via the config file.
# --------------------------------------------------------------------------

PROTECTED_BRANCHES = {"main", "master", "production"}

# Shells and interpreters that must never receive a network download on stdin.
SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "fish", "python", "python3", "perl", "ruby", "node", "bun"}
DOWNLOADERS = {"curl", "wget"}

# Credential files. Any command that references a matching token is blocked.
CREDENTIAL_PATTERNS = [
    r"(^|/)\.aws/credentials$",
    r"(^|/)\.aws/config$",
    r"(^|/)id_(rsa|dsa|ecdsa|ed25519)$",
    r"(^|/)\.env\.(production|prod)(\.local)?$",
    r"(^|/)\.netrc$",
    r"(^|/)\.config/gh/hosts\.yml$",
]

# gh api paths that change repository integrity settings.
GH_API_PROTECTED_PATHS = [
    r"/branches/[^/]+/protection",
    r"/rulesets",
    r"/collaborators/",
]

# Commands that wrap another command. The guard inspects the wrapped command.
WRAPPERS = {"sudo", "command", "exec", "nohup", "time", "nice", "env", "xargs", "timeout"}

CONFIG_PATH = Path(__file__).with_name("guard_bash.config.json")
CONFIG_KEYS = {
    "protected_branches": "list[str], replaces PROTECTED_BRANCHES",
    "allowed_rm_roots": "list[str], absolute dirs where recursive rm is allowed (besides workspace, cwd, /tmp)",
    "extra_blocked_regex": "list[str], regexes matched against the raw command",
}

OPERATORS = {";", "&&", "||", "|", "&", "|&", "\n", "(", ")"}


@dataclass
class Context:
    cwd: str
    project_dir: str
    protected: set[str]
    rm_roots: list[str]
    extra_regex: list[str] = field(default_factory=list)


class Blocked(Exception):
    """Raised with a human-readable reason when a command must be blocked."""


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def warn(msg: str) -> None:
    print(f"guard_bash: warning: {msg}", file=sys.stderr)


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError) as exc:
        warn(f"ignoring unreadable config {CONFIG_PATH}: {exc}")
        return {}


def tokenize(command: str) -> list[str]:
    lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=";&|()")
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def split_segments(tokens: list[str]) -> list[tuple[list[str], str]]:
    """Split tokens into simple commands. Returns (argv, operator_after)."""
    segments: list[tuple[list[str], str]] = []
    current: list[str] = []
    for tok in tokens:
        if tok in OPERATORS or set(tok) <= set(";&|()"):
            segments.append((current, tok))
            current = []
        else:
            current.append(tok)
    segments.append((current, ""))
    return [(argv, op) for argv, op in segments if argv]


def strip_wrappers(argv: list[str]) -> list[str]:
    argv = list(argv)
    while argv:
        head = os.path.basename(argv[0])
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", argv[0]):
            argv = argv[1:]
        elif head in WRAPPERS:
            argv = argv[1:]
            # Drop wrapper options such as `sudo -u x`, `timeout 10`, `env -i`.
            while argv and (argv[0].startswith("-") or re.fullmatch(r"\d+[smhd]?", argv[0])):
                argv = argv[1:]
        else:
            break
    return argv


def current_branch(cwd: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "symbolic-ref", "--short", "-q", "HEAD"],
            cwd=cwd or None,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    branch = out.stdout.strip()
    return branch if out.returncode == 0 and branch else None


def expand_home(path: str) -> str:
    return os.path.expanduser(path)


# --------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------


def check_git(argv: list[str], ctx: Context) -> None:
    # Skip git global options: -C <dir>, -c <k=v>, --git-dir=..., etc.
    i, git_cwd = 1, ctx.cwd
    while i < len(argv) and argv[i].startswith("-"):
        if argv[i] in ("-C", "-c") and i + 1 < len(argv):
            if argv[i] == "-C":
                git_cwd = os.path.join(ctx.cwd, expand_home(argv[i + 1]))
            i += 2
        else:
            i += 1
    if i >= len(argv):
        return
    sub, args = argv[i], argv[i + 1 :]

    if sub == "commit":
        for a in args:
            if a == "--no-verify" or (re.fullmatch(r"-[A-Za-z]+", a) and "n" in a[1:]):
                raise Blocked("git commit --no-verify/-n skips hooks. Fix the hook failure instead.")
        return

    if sub != "push":
        return

    positional: list[str] = []
    skip_next = False
    for a in args:
        if skip_next:
            skip_next = False
            continue
        if a in ("--no-verify",):
            raise Blocked("git push --no-verify skips hooks.")
        if a in ("--force", "-f") or (re.fullmatch(r"-[A-Za-z]+", a) and "f" in a[1:]):
            raise Blocked("git push --force is not allowed. Use --force-with-lease on a non-protected branch.")
        if a in ("--mirror", "--all"):
            raise Blocked(f"git push {a} can overwrite protected branches.")
        if a in ("-o", "--push-option", "--repo", "--receive-pack", "--exec"):
            skip_next = True
            continue
        if a.startswith("-"):
            continue  # --force-with-lease, -u, --tags, --delete, --dry-run ...
        positional.append(a)

    refspecs = positional[1:]
    branch = None
    if not refspecs:
        branch = current_branch(git_cwd)
        if branch in ctx.protected:
            raise Blocked(f"git push from protected branch '{branch}' is not allowed. Push a feature branch.")
        return

    for spec in refspecs:
        if spec.startswith("+"):
            raise Blocked(f"force refspec '{spec}' is not allowed.")
        dst = spec.split(":", 1)[1] if ":" in spec else spec
        if dst in ("HEAD", ""):
            dst = spec.split(":", 1)[0] if dst == "" else dst
        if dst == "HEAD":
            branch = branch or current_branch(git_cwd)
            dst = branch or "HEAD"
        dst = re.sub(r"^refs/heads/", "", dst)
        if dst in ctx.protected:
            raise Blocked(f"git push to protected branch '{dst}' is not allowed. Open a PR instead.")


def _under(path: str, root: str) -> bool:
    try:
        return os.path.commonpath([os.path.realpath(path), os.path.realpath(root)]) == os.path.realpath(root)
    except ValueError:
        return False


def check_rm(argv: list[str], ctx: Context) -> None:
    recursive = False
    targets: list[str] = []
    end_of_opts = False
    for a in argv[1:]:
        if not end_of_opts and a == "--":
            end_of_opts = True
            continue
        if not end_of_opts and a.startswith("--"):
            recursive |= a == "--recursive"
            continue
        if not end_of_opts and a.startswith("-") and len(a) > 1:
            recursive |= "r" in a or "R" in a
            continue
        targets.append(a)
    if not recursive:
        return

    for t in targets:
        if t in ("/", "/*", "~", "~/", "~/*", "$HOME", "${HOME}", "$HOME/", "${HOME}/", ".", "./"):
            raise Blocked(f"recursive rm on '{t}' is not allowed.")
        if t.startswith(("~", "$HOME", "${HOME}")):
            raise Blocked(f"recursive rm under the home directory ('{t}') is not allowed.")
        if t == ".." or t.startswith("../") or "/../" in t or t.endswith("/.."):
            raise Blocked(f"recursive rm with a parent path ('{t}') is not allowed.")
        if t.startswith("/"):
            roots = [ctx.project_dir, ctx.cwd, "/tmp", *ctx.rm_roots]
            roots = [r for r in roots if r]
            if any(os.path.realpath(t) == os.path.realpath(r) for r in roots if r != "/tmp"):
                raise Blocked(f"recursive rm of the workspace root ('{t}') is not allowed.")
            if not any(_under(t, r) for r in roots):
                raise Blocked(f"recursive rm of absolute path outside the workspace ('{t}') is not allowed.")


def check_gh(argv: list[str], ctx: Context) -> None:
    args = argv[1:]
    if len(args) >= 2 and args[0] == "pr" and args[1] == "merge":
        raise Blocked("gh pr merge is not allowed. Merging is a human decision (Gate 2).")
    if len(args) >= 2 and args[0] == "pr" and args[1] == "review":
        if any(a in ("--approve", "-a") or (re.fullmatch(r"-[A-Za-z]+", a) and "a" in a[1:]) for a in args[2:]):
            raise Blocked("gh pr review --approve is not allowed. Agents never approve.")
    if len(args) >= 2 and args[0] == "repo" and args[1] == "delete":
        raise Blocked("gh repo delete is not allowed.")
    if args and args[0] == "api":
        rest = args[1:]
        path = next((a for a in rest if not a.startswith("-") and ("/" in a)), "")
        method = "GET"
        has_fields = False
        for j, a in enumerate(rest):
            if a in ("-X", "--method") and j + 1 < len(rest):
                method = rest[j + 1].upper()
            elif a.startswith("--method="):
                method = a.split("=", 1)[1].upper()
            elif a.startswith("-X") and len(a) > 2:
                method = a[2:].upper()
            elif a in ("-f", "-F", "--field", "--raw-field", "--input"):
                has_fields = True
        if method == "GET" and has_fields:
            method = "POST"
        if method != "GET" and any(re.search(p, path) for p in GH_API_PROTECTED_PATHS):
            raise Blocked(f"gh api {method} {path} changes repository protection. Humans run scripts/setup-branch-protection.sh.")


def check_credentials(argv: list[str], ctx: Context) -> None:
    for a in argv:
        candidate = a.split("=", 1)[1] if a.startswith("-") and "=" in a else a
        candidate = candidate.replace("${HOME}", "~").replace("$HOME", "~")
        if any(re.search(p, candidate) for p in CREDENTIAL_PATTERNS):
            raise Blocked(f"access to credential file '{a}' is not allowed.")


def check_pipe_to_shell(segments: list[tuple[list[str], str]]) -> None:
    downloading = False
    for argv, op in segments:
        name = os.path.basename(argv[0]) if argv else ""
        if downloading and name in SHELLS:
            raise Blocked("piping a network download into a shell/interpreter is not allowed.")
        if name in DOWNLOADERS:
            downloading = True
        if op not in ("|", "|&"):
            downloading = False


def check_process_substitution(command: str) -> None:
    shells = "|".join(sorted(SHELLS))
    if re.search(rf"\b({shells})\b[^|;&]*<\(\s*(curl|wget)\b", command):
        raise Blocked("running a downloaded script via process substitution is not allowed.")
    if re.search(rf"\b({shells})\b\s+-c\s+[\"']?\$\(\s*(curl|wget)\b", command):
        raise Blocked("running a downloaded script via command substitution is not allowed.")


# --------------------------------------------------------------------------
# Entry points
# --------------------------------------------------------------------------


def evaluate(command: str, ctx: Context, depth: int = 0) -> None:
    """Raise Blocked if the command violates a rule."""
    if depth > 3 or not command.strip():
        return
    for rx in ctx.extra_regex:
        if re.search(rx, command):
            raise Blocked(f"command matches blocked pattern '{rx}'.")
    check_process_substitution(command)
    try:
        tokens = tokenize(command)
    except ValueError as exc:
        warn(f"could not tokenize command ({exc}); applying regex checks only")
        tokens = command.split()
    segments = split_segments(tokens)
    check_pipe_to_shell([(strip_wrappers(a), op) for a, op in segments])

    # Inspect nested command substitutions: $(...) and `...`.
    for inner in re.findall(r"\$\(([^()]*)\)|`([^`]*)`", command):
        evaluate(inner[0] or inner[1], ctx, depth + 1)

    for raw_argv, _ in segments:
        argv = strip_wrappers(raw_argv)
        if not argv:
            continue
        name = os.path.basename(argv[0])
        check_credentials(argv, ctx)
        if name in SHELLS and "-c" in argv[1:]:
            idx = argv.index("-c")
            if idx + 1 < len(argv):
                evaluate(argv[idx + 1], ctx, depth + 1)
        elif name == "git":
            check_git(argv, ctx)
        elif name == "rm":
            check_rm(argv, ctx)
        elif name == "gh":
            check_gh(argv, ctx)


def build_context(payload: dict) -> Context:
    cfg = load_config()
    cwd = payload.get("cwd") or os.getcwd()
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or cwd
    protected = set(cfg.get("protected_branches") or PROTECTED_BRANCHES)
    rm_roots = [os.path.expanduser(r) for r in cfg.get("allowed_rm_roots", []) if isinstance(r, str)]
    extra = [r for r in cfg.get("extra_blocked_regex", []) if isinstance(r, str)]
    return Context(cwd=cwd, project_dir=project_dir, protected=protected, rm_roots=rm_roots, extra_regex=extra)


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
        command = payload["tool_input"]["command"]
        if not isinstance(command, str):
            raise TypeError("tool_input.command is not a string")
    except (ValueError, KeyError, TypeError) as exc:
        warn(f"could not parse hook input ({type(exc).__name__}: {exc}); allowing command")
        return 0

    try:
        evaluate(command, build_context(payload))
    except Blocked as reason:
        print(f"BLOCKED by .claude/hooks/guard_bash.py: {reason}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - the guard must never crash the session
        warn(f"internal error ({type(exc).__name__}: {exc}); allowing command")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
