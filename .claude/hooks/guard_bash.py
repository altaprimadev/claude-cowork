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

# development and staging are integration and release branches. Only a human merges into them
# (CLAUDE.md, Respect autonomy). Agents push feature branches only.
PROTECTED_BRANCHES = {"main", "master", "production", "development", "staging"}

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
    r"(^|/)\.git-credentials$",
    r"(^|/)\.aws/",                         # any file under ~/.aws, globs included
]

# Environment variables that hold credentials. printenv/echo of these is blocked.
SECRET_VAR_RE = re.compile(r"(TOKEN|SECRET|PASSWORD|PASSWD|API_?KEY|PRIVATE_KEY|CREDENTIAL)", re.IGNORECASE)

# gh api paths that change repository integrity settings.
# gh api paths whose non-GET calls change repository or account administration.
# The agent may run as the repo owner (admin), so these are blocked explicitly.
GH_API_PROTECTED_PATHS = [
    r"^/?repos/[^/]+/[^/]+/?$",            # repo settings (PATCH) and repo deletion (DELETE)
    r"/branches/[^/]+/protection",
    r"/rulesets",
    r"/collaborators",
    r"/invitations",
    r"/hooks",
    r"/keys",
    r"/actions/(secrets|variables|permissions)",
    r"/environments",
    r"/transfer",
    r"/pages",
    r"^/?user(/|$)",                       # the agent's own account settings
    r"^/?orgs/",
    r"/pulls/\d+/merge$",                 # merge a PR through the API (Gate 2)
    r"/deployments",                       # create a deployment (Gate 3)
    r"/releases",                          # create or change a release (Gate 3)
    r"/git/tags",                          # create a tag object (release tags are human-only)
    r"/auto_merge",                        # enable auto-merge (Gate 2)
    r"^/?repos/[^/]+/[^/]+/merges$",       # merge one branch into another
]

# gh subcommands that change repository administration or secrets.
GH_ADMIN_SUBCOMMANDS = {
    ("repo", "delete"),
    ("repo", "edit"),
    ("repo", "archive"),
    ("repo", "unarchive"),
    ("repo", "rename"),
    ("repo", "deploy-key"),
    ("repo", "create"),
    ("repo", "fork"),
    ("secret", "set"),
    ("secret", "delete"),
    ("variable", "set"),
    ("variable", "delete"),
    ("ruleset", "create"),
    ("ruleset", "delete"),
    ("auth", "token"),
    ("auth", "refresh"),
    ("alias", "set"),
    ("alias", "import"),
    ("release", "create"),
    ("release", "edit"),
    ("release", "delete"),
    ("release", "upload"),
}

# gh subcommands that start, enable, or disable workflows. A workflow can deploy (Gate 3).
GH_WORKFLOW_SUBCOMMANDS = {"run", "enable", "disable"}

# The only workflow an agent may dispatch: the label-to-board sync (CLAUDE.md, State lives in GitHub).
GH_DISPATCH_ALLOWED = {"project-sync.yml"}

# gh global flags that take a value and may come before the subcommand.
GH_GLOBAL_VALUE_FLAGS = {"-R", "--repo", "--hostname"}

# GraphQL mutations that merge, approve, or move refs. Matched only inside a `mutation`.
GRAPHQL_BLOCKED_MUTATIONS = re.compile(
    r"\b(mergePullRequest|enablePullRequestAutoMerge|mergeBranch|createRef|updateRefs?|deleteRef|"
    r"updateBranchProtectionRule|deleteBranchProtectionRule|"
    r"createRepository|forkRepository|cloneTemplateRepository)\b"
)
GRAPHQL_REVIEW_MUTATIONS = re.compile(r"\b(addPullRequestReview|submitPullRequestReview)\b")

# Shells that run a command string with -c, or read commands from stdin.
SH_FAMILY = {"sh", "bash", "zsh", "dash", "ksh"}
# Shell options that take a value (bash -o pipefail -c ...).
SHELL_VALUE_FLAGS = {"-o", "+o", "-O", "+O", "--rcfile", "--init-file"}

# Commands that wrap another command. The guard inspects the wrapped command.
WRAPPERS = {"sudo", "doas", "command", "exec", "nohup", "time", "nice", "env", "xargs", "timeout",
            "setsid", "stdbuf", "ionice", "unbuffer", "chronic", "busybox", "builtin"}

# Shell words that start a compound command. The command after them is the one that runs.
SHELL_KEYWORDS = {"{", "}", "!", "if", "then", "else", "elif", "fi", "do", "done", "while", "until",
                  "time", "coproc"}

# git -c / git config keys that change what a push sends or run another command.
GIT_RISKY_CONFIG_RE = re.compile(r"^(alias\.|remote\.[^=]*\.push|push\.|url\..*\.pushinsteadof|core\.hookspath)",
                                 re.IGNORECASE)

# Maximum nesting of shells, eval, and substitutions the guard follows. Deeper is blocked.
MAX_DEPTH = 4

# Wrapper options that take a value, so the value is not mistaken for the wrapped command.
WRAPPER_VALUE_FLAGS = {
    "sudo": {"-u", "-g", "-h", "-p", "-C", "-D", "-R", "-T", "-U", "--user", "--group", "--host",
             "--prompt", "--chdir", "--chroot", "--close-from", "--other-user", "--command-timeout"},
    "timeout": {"-s", "-k", "--signal", "--kill-after"},
    "ionice": {"-c", "-n", "-p", "--class", "--classdata", "--pid"},
    "nice": {"-n", "--adjustment"},
    "env": {"-u", "-C", "--unset", "--chdir"},
    "xargs": {"-I", "-n", "-P", "-L", "-s", "-d", "-E", "-a", "--max-args", "--max-procs",
              "--delimiter", "--arg-file", "--max-lines", "--max-chars", "--eof", "--replace"},
}

VAR_RE = re.compile(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?")
ASSIGN_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=(.*)", re.DOTALL)

CONFIG_PATH = Path(__file__).with_name("guard_bash.config.json")
CONFIG_KEYS = {
    "protected_branches": "list[str], adds to PROTECTED_BRANCHES (never removes one)",
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
    # Shell variables assigned earlier in the same command (B=main; git push origin $B).
    variables: dict[str, str] = field(default_factory=dict)
    # True while checking a command that xargs runs with extra arguments.
    appended_args: bool = False


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


def split_or_block(text: str) -> list[str]:
    try:
        return shlex.split(text)
    except ValueError as exc:
        raise Blocked(f"cannot parse the command string ({exc}); the guard cannot check it.") from exc


def wrapper_names(argv: list[str]) -> set[str]:
    """Wrapper commands in front of the real command (`echo x | xargs git push` -> {"xargs"})."""
    names, rest = set(), list(argv)
    while rest:
        stripped = strip_wrappers(rest)
        if len(stripped) == len(rest):
            break
        names.add(os.path.basename(rest[0]))
        rest = rest[1:]
    return names


def find_exec_commands(argv: list[str]) -> list[list[str]]:
    """Commands that find runs with -exec, -execdir, -ok, or -okdir."""
    out, i = [], 1
    while i < len(argv):
        if argv[i] in ("-exec", "-execdir", "-ok", "-okdir"):
            j = i + 1
            while j < len(argv) and argv[j] not in (";", "+", "\\;"):
                j += 1
            out.append(argv[i + 1 : j])
            i = j
        i += 1
    return out


def strip_wrappers(argv: list[str]) -> list[str]:
    argv = list(argv)
    while argv:
        head = os.path.basename(argv[0])
        if argv[0] in SHELL_KEYWORDS:
            argv = argv[1:]
        elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", argv[0]):
            argv = argv[1:]
        elif head in WRAPPERS:
            argv = argv[1:]
            value_flags = WRAPPER_VALUE_FLAGS.get(head, set())
            # Drop wrapper options such as `sudo -u x`, `timeout -s KILL 10`, `env -i`.
            while argv and (argv[0].startswith("-") or re.fullmatch(r"\d+[smhd]?", argv[0])
                            or (head == "env" and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", argv[0]))):
                if head == "env" and argv[0] in ("-S", "--split-string") and len(argv) > 1:
                    # env -S "cmd args" splits the string into the command.
                    argv = split_or_block(argv[1]) + argv[2:]
                    break
                if head == "env" and argv[0].startswith("--split-string="):
                    argv = split_or_block(argv[0].split("=", 1)[1]) + argv[1:]
                    break
                argv = argv[2:] if argv[0] in value_flags else argv[1:]
        else:
            break
    return argv


def expand_vars(text: str, ctx: Context) -> str:
    """Expand $NAME and ${NAME} from earlier assignments in the command, then the environment."""

    def repl(m: re.Match) -> str:
        name = m.group(1)
        if name in ctx.variables:
            return ctx.variables[name]
        return os.environ.get(name, m.group(0))

    return VAR_RE.sub(repl, text)


def record_assignments(argv: list[str], ctx: Context) -> None:
    """Remember NAME=value words: a bare assignment, a prefix, or `export NAME=value`."""
    words = argv[1:] if argv and argv[0] in ("export", "declare", "local", "readonly") else argv
    for w in words:
        m = ASSIGN_RE.fullmatch(w)
        if not m:
            break
        ctx.variables[m.group(1)] = expand_vars(m.group(2), ctx)


def shell_command_string(argv: list[str]) -> str | None:
    """Return the -c command string of a shell call (bash -lc "cmd"), or None."""
    has_c, i = False, 1
    while i < len(argv):
        a = argv[i]
        if a in SHELL_VALUE_FLAGS:
            i += 2
            continue
        if a == "--":
            i += 1
            break
        if re.fullmatch(r"[-+][A-Za-z]+", a):
            has_c |= a.startswith("-") and "c" in a[1:]
            i += 1
            continue
        if a.startswith("--"):
            i += 1
            continue
        break
    if has_c and i < len(argv):
        return argv[i]
    return None


def reads_stdin(argv: list[str]) -> bool:
    """True when a sh-family shell runs commands from stdin: no -c and no script file."""
    if os.path.basename(argv[0]) not in SH_FAMILY or shell_command_string(argv) is not None:
        return False
    i = 1
    while i < len(argv):
        a = argv[i]
        if a in SHELL_VALUE_FLAGS:
            i += 2
            continue
        if a == "-s" or a == "-":
            return True
        if a.startswith(("-", "+")):
            i += 1
            continue
        return a.startswith("<")  # only a redirect follows, no script file
    return True


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
            elif GIT_RISKY_CONFIG_RE.search(argv[i + 1]):
                raise Blocked(f"git -c {argv[i + 1].split('=', 1)[0]} can change what a push sends or run "
                              "another command. The guard cannot check it.")
            i += 2
        elif argv[i].startswith("--config-env"):
            raise Blocked("git --config-env hides configuration from the guard.")
        else:
            i += 1
    if i >= len(argv):
        return
    sub, args = argv[i], argv[i + 1 :]

    if sub == "config":
        keys = [a for a in args if not a.startswith("-")]
        if keys and GIT_RISKY_CONFIG_RE.search(keys[0]) and (len(keys) > 1 or any(
                a in ("--add", "--replace-all") for a in args)):
            raise Blocked(f"git config {keys[0]} can change what a push sends or run another command.")
        return

    if sub in ("send-pack", "http-push"):
        raise Blocked(f"git {sub} pushes without the push checks. Use git push to a feature branch.")

    if sub == "credential":
        raise Blocked("git credential reads or stores credentials.")

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
        if (a in ("--force", "-f") or a.startswith(("--force-with-lease", "--force-if-includes"))
                or (re.fullmatch(r"-[A-Za-z]+", a) and "f" in a[1:])):
            raise Blocked(f"git push {a} is a force-push. Agents never force-push (CLAUDE.md). Push a new commit instead.")
        if a in ("--mirror", "--all"):
            raise Blocked(f"git push {a} can overwrite protected branches.")
        if a in ("--tags", "--follow-tags"):
            raise Blocked(f"git push {a} pushes release tags. Humans tag releases (Gate 3).")
        if a in ("-o", "--push-option", "--repo", "--receive-pack", "--exec"):
            skip_next = True
            continue
        if a.startswith("-"):
            continue  # --force-with-lease, -u, --tags, --delete, --dry-run ...
        positional.append(a)

    refspecs = positional[1:]
    branch = None
    if ctx.appended_args and len(positional) < 3:
        raise Blocked("xargs adds push arguments the guard cannot see. Name the branch literally.")
    if not refspecs:
        branch = current_branch(git_cwd)
        if branch in ctx.protected:
            raise Blocked(f"git push from protected branch '{branch}' is not allowed. Push a feature branch.")
        return

    for raw_spec in refspecs:
        spec = expand_vars(raw_spec, ctx)
        if "$" in spec or "`" in spec:
            raise Blocked(f"git push refspec '{raw_spec}' uses a variable or substitution the guard cannot resolve. "
                          "Use a literal branch name.")
        if spec.startswith("+"):
            raise Blocked(f"force refspec '{spec}' is not allowed.")
        dst = spec.split(":", 1)[1] if ":" in spec else spec
        if dst.startswith("refs/tags/") or re.fullmatch(r"v\d+(\.\d+)*", dst):
            raise Blocked(f"git push of tag '{dst}' is not allowed. Humans tag releases (Gate 3).")
        if dst == "@":
            dst = "HEAD"
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


def strip_gh_global_flags(args: list[str]) -> list[str]:
    """Drop gh global flags before the subcommand: `gh -R o/r pr merge` -> `pr merge`."""
    while args and args[0].startswith("-"):
        if args[0] in GH_GLOBAL_VALUE_FLAGS:
            args = args[2:]
        else:
            args = args[1:]  # --repo=o/r, -Ro/r, --help ...
    return args


def gh_api_fields(rest: list[str]) -> list[str]:
    """Values of -f/-F/--field/--raw-field, as `key=value` strings."""
    out = []
    for j, a in enumerate(rest):
        if a in ("-f", "-F", "--field", "--raw-field") and j + 1 < len(rest):
            out.append(rest[j + 1])
        elif a.startswith(("--field=", "--raw-field=")):
            out.append(a.split("=", 1)[1])
        elif re.fullmatch(r"-[fF].+", a):
            out.append(a[2:])
    return out


def check_gh_graphql(rest: list[str]) -> None:
    if any(a == "--input" or a.startswith("--input=") for a in rest):
        raise Blocked("gh api graphql --input hides the query from the guard. Pass the query with -f query=...")
    for field_value in gh_api_fields(rest):
        value = field_value.split("=", 1)[1] if "=" in field_value else field_value
        if "$(" in value or "`" in value:
            raise Blocked("gh api graphql with a substituted query hides it from the guard. Pass it inline.")
        if value.startswith("@"):
            raise Blocked("gh api graphql with a query file hides the query from the guard. Pass it inline.")
        if not re.search(r"\bmutation\b", value):
            continue
        if m := GRAPHQL_BLOCKED_MUTATIONS.search(value):
            raise Blocked(f"GraphQL mutation {m.group(1)} merges, creates or moves refs, or creates a repository. "
                          "Humans merge (Gate 2), tag, and create repositories. Use git push for a feature branch.")
        if GRAPHQL_REVIEW_MUTATIONS.search(value) and any(
                re.search(r"\bAPPROVE\b", f) for f in gh_api_fields(rest)):
            raise Blocked("GraphQL review with event APPROVE is not allowed. Agents never approve.")


def check_gh(argv: list[str], ctx: Context) -> None:
    args = strip_gh_global_flags(argv[1:])
    if len(args) >= 2 and args[0] == "auth" and args[1] == "status" and any(
            a in ("-t", "--show-token") for a in args[2:]):
        raise Blocked("gh auth status --show-token prints a credential.")
    if len(args) >= 2 and args[0] == "pr" and args[1] == "merge":
        raise Blocked("gh pr merge is not allowed. Merging is a human decision (Gate 2).")
    if len(args) >= 2 and args[0] == "pr" and args[1] == "review":
        if any(a in ("--approve", "-a") or a.startswith("--approve=")
               or (re.fullmatch(r"-[A-Za-z]+", a) and "a" in a[1:]) for a in args[2:]):
            raise Blocked("gh pr review --approve is not allowed. Agents never approve.")
    if len(args) >= 2 and (args[0], args[1]) in GH_ADMIN_SUBCOMMANDS:
        raise Blocked(f"gh {args[0]} {args[1]} changes repository administration or secrets. Humans do this.")
    if len(args) >= 2 and args[0] == "workflow" and args[1] in GH_WORKFLOW_SUBCOMMANDS:
        raise Blocked(f"gh workflow {args[1]} can start a deploy. Humans run workflows (Gate 3).")
    if args and args[0] == "api":
        rest = args[1:]
        value_opts = {"-X", "--method", "-f", "-F", "--field", "--raw-field", "--input", "-H", "--header",
                      "-q", "--jq", "-t", "--template", "--hostname", "--cache", "-p", "--preview"}
        path, skip = "", False
        for a in rest:
            if skip:
                skip = False
            elif a in value_opts:
                skip = True
            elif not a.startswith("-"):
                path = a
                break
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
        path = re.sub(r"[?#].*$", "", path).rstrip("/") or path
        if path.lstrip("/") == "graphql":
            check_gh_graphql(rest)
            return
        if method == "GET":
            return
        if re.search(r"/contents/", path) and method in ("PUT", "DELETE", "POST", "PATCH"):
            branch_fields = [f.split("=", 1)[1] for f in gh_api_fields(rest) if f.startswith("branch=")]
            if not branch_fields or branch_fields[-1] in ctx.protected:
                raise Blocked(f"gh api {method} {path} commits to "
                              f"'{branch_fields[-1] if branch_fields else 'the default branch'}'. "
                              "Commit to a feature branch with -f branch=<branch>.")
        if any(re.search(p, path) for p in GH_API_PROTECTED_PATHS):
            raise Blocked(f"gh api {method} {path} changes repository protection. Humans run scripts/setup-branch-protection.sh.")
        if re.search(r"/pulls/\d+/reviews(/\d+/events)?$", path) and any(
            re.fullmatch(r"event=APPROVE", f) for f in gh_api_fields(rest)
        ):
            raise Blocked("gh api review with event=APPROVE is not allowed. Agents never approve.")
        if re.search(r"/git/refs/tags(/|$)", path):
            raise Blocked(f"gh api {method} {path} changes a tag. Release tags are human-only (Gate 3).")
        if re.search(r"/git/refs$", path):
            for f in gh_api_fields(rest):
                ref = f.split("=", 1)[1] if f.startswith("ref=") else None
                if ref is None:
                    continue
                if ref.startswith("refs/tags/"):
                    raise Blocked(f"gh api {method} {path} creates tag '{ref}'. Release tags are human-only (Gate 3).")
                if ref.removeprefix("refs/heads/") in ctx.protected:
                    raise Blocked(f"gh api {method} {path} creates protected branch ref '{ref}'.")
        if re.search(r"/forks$", path) or re.search(r"^/?repos/[^/]+/[^/]+/generate$", path):
            raise Blocked(f"gh api {method} {path} creates a repository. Humans create repositories.")
        m = re.search(r"/git/refs/heads/(.+)$", path)
        if m and m.group(1) in ctx.protected:
            raise Blocked(f"gh api {method} on protected branch ref '{m.group(1)}' is not allowed.")
        m = re.search(r"/actions/workflows/([^/]+)/(dispatches|enable|disable)$", path)
        if m and not (m.group(2) == "dispatches" and m.group(1) in GH_DISPATCH_ALLOWED):
            raise Blocked(f"gh api {method} {path} can start a deploy. Only project-sync.yml may be dispatched.")


def check_credentials(argv: list[str], ctx: Context) -> None:
    for a in argv:
        candidate = a.split("=", 1)[1] if a.startswith("-") and "=" in a else a
        candidate = candidate.replace("${HOME}", "~").replace("$HOME", "~")
        resolved = os.path.join(expand_home(ctx.cwd), candidate) if candidate and not candidate.startswith(("/", "~")) else candidate
        home = os.path.expanduser("~")
        if resolved.startswith(home + "/"):
            resolved = "~" + resolved[len(home):]
        if any(re.search(p, c) for p in CREDENTIAL_PATTERNS for c in (candidate, resolved)):
            raise Blocked(f"access to credential file '{a}' is not allowed.")
    name = os.path.basename(argv[0]) if argv else ""
    if name == "printenv" and (len(argv) == 1 or any(SECRET_VAR_RE.search(a) for a in argv[1:])):
        raise Blocked("printenv can print credentials. Name a non-secret variable.")


def check_curl_github(argv: list[str]) -> None:
    """curl/wget writes to the GitHub API skip the gh api checks."""
    if os.path.basename(argv[0]) not in DOWNLOADERS:
        return
    if not any("api.github.com" in a or "/graphql" in a for a in argv):
        return
    writes = any(a in ("-X", "--request", "-d", "--data", "--data-raw", "--data-binary", "--json", "-F", "--form",
                       "-T", "--upload-file", "--method", "--post-data")
                 or a.startswith(("-X", "--request=", "--data", "--json", "--method=", "--post-data")) for a in argv[1:])
    if writes:
        raise Blocked("curl/wget writes to the GitHub API skip the guard. Use gh api.")


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


HEREDOC_RE = re.compile(r"<<-?[ \t]*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1[^\n]*\n(.*?)(?:^[ \t]*\2[ \t]*$|\Z)", re.DOTALL | re.MULTILINE)


def strip_heredocs(command: str) -> tuple[str, list[str]]:
    """Remove heredoc bodies. Bodies are data, not commands.

    A quoted delimiter (<<'EOF') disables expansion, so its body is dropped.
    An unquoted delimiter still runs $(...) and `...`, so those substitutions
    are returned for separate evaluation.
    """
    nested: list[str] = []

    def repl(m: re.Match) -> str:
        quoted, body = bool(m.group(1)), m.group(3)
        line_start = command.rfind("\n", 0, m.start()) + 1
        prefix = command[line_start : m.start()]
        try:
            words = strip_wrappers(split_segments(tokenize(prefix))[-1][0]) if prefix.strip() else []
        except (ValueError, IndexError):
            words = []
        if words and reads_stdin(words):
            # The heredoc feeds a shell, so its body is commands, quoted or not.
            nested.append(body)
        elif not quoted:
            nested.extend(a or b for a, b in re.findall(r"\$\(([^()]*)\)|`([^`]*)`", body))
        return m.group(0)[: m.start(3) - m.start(0)]

    return HEREDOC_RE.sub(repl, command), nested


def evaluate(command: str, ctx: Context, depth: int = 0) -> None:
    """Raise Blocked if the command violates a rule."""
    if not command.strip():
        return
    if depth > MAX_DEPTH:
        raise Blocked(f"the command nests shells or substitutions more than {MAX_DEPTH} levels deep. "
                      "The guard cannot check it.")
    command, heredoc_subs = strip_heredocs(command)
    for inner in heredoc_subs:
        evaluate(inner, ctx, depth + 1)
    for rx in ctx.extra_regex:
        if re.search(rx, command):
            raise Blocked(f"command matches blocked pattern '{rx}'.")
    check_process_substitution(command)
    try:
        tokens = tokenize(command)
    except ValueError as exc:
        warn(f"could not tokenize command ({exc}); falling back to whitespace split")
        tokens = command.split()
    segments = split_segments(tokens)
    check_pipe_to_shell([(strip_wrappers(a), op) for a, op in segments])

    # Inspect nested command substitutions: $(...) and `...`.
    for inner in re.findall(r"\$\(([^()]*)\)|`([^`]*)`", command):
        evaluate(inner[0] or inner[1], ctx, depth + 1)

    prev_op = ""
    for raw_argv, op in segments:
        record_assignments(raw_argv, ctx)
        argv = strip_wrappers(raw_argv)
        piped_in, prev_op = prev_op in ("|", "|&"), op
        if not argv:
            continue
        if "$" in argv[0] or "`" in argv[0]:
            expanded = expand_vars(argv[0], ctx)
            if "$" in expanded or "`" in expanded:
                raise Blocked(f"the command name '{argv[0]}' comes from a substitution the guard cannot resolve.")
            argv = split_or_block(expanded) + argv[1:]
            argv = strip_wrappers(argv)
            if not argv:
                continue
        name = os.path.basename(argv[0])
        if name == "cd":
            target = expand_home(expand_vars(argv[1], ctx)) if len(argv) > 1 else os.path.expanduser("~")
            ctx.cwd = os.path.normpath(os.path.join(ctx.cwd, target))
            continue
        ctx.appended_args = "xargs" in wrapper_names(raw_argv)
        check_credentials(argv, ctx)
        check_curl_github(argv)
        if name == "find":
            for inner in find_exec_commands(argv):
                if inner:
                    evaluate(shlex.join(inner), ctx, depth + 1)
        inner_cmd = shell_command_string(argv) if name in SHELLS else None
        if inner_cmd is not None:
            evaluate(inner_cmd, ctx, depth + 1)
        elif name in SH_FAMILY and "<<<" in argv:
            idx = argv.index("<<<")
            if idx + 1 < len(argv):
                evaluate(argv[idx + 1], ctx, depth + 1)
        elif name in SH_FAMILY and piped_in and reads_stdin(argv):
            raise Blocked(f"piping commands into {name} hides them from the guard. Use {name} -c \"...\" instead.")
        elif name == "eval":
            rest = " ".join(argv[1:])
            # eval "$(ssh-agent -s)": the substitution was checked above; its output is tool output.
            if not re.fullmatch(r"\$\([^()]*\)|`[^`]*`", rest):
                evaluate(rest, ctx, depth + 1)
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
    # The config only adds branches. An edit to the working copy can never unprotect one.
    protected = PROTECTED_BRANCHES | {b for b in cfg.get("protected_branches", []) if isinstance(b, str)}
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
