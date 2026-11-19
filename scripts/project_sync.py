#!/usr/bin/env python3
"""Mirror pipeline issue state into a GitHub Project (Projects v2).

Agents read and write issues and labels through REST. Cloud agent sessions
cannot reach the Projects API, so this script runs in GitHub Actions
(.github/workflows/project-sync.yml) with a token that can.

For every pipeline issue in the control repo and in each active managed repo:
  1. Add the issue to the Project (idempotent).
  2. Set the single-select Status field from the issue's labels.

Config: registry/policy.yml -> project (owner, number, status_field).
Token:  env PROJECT_SYNC_TOKEN. The owner may be a user or an organization.
        User-owned Projects need a classic token with `project` and `repo` scopes.

Usage: python3 scripts/project_sync.py [--dry-run]
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.github.com"
CLOSED_LOOKBACK_DAYS = 7

# Status option -> rule. The first matching entry wins.
STATUS_ORDER = [
    "Done",
    "In review",
    "Blocked",
    "Ready to merge",
    "In progress",
    "Ready",
    "Draft",
    "Design",
    "Brief",
    "Backlog",
]
LABEL_STATUS = {
    "ai:needs-human": "In review",
    "ai:blocked": "Blocked",
    "ai:in-progress": "In progress",
    "ai:ready": "Ready",
    "ai:draft": "Draft",
    "ai:needs-design": "Design",
    "ai:brief": "Brief",
}
SKIP_LABELS = {"ai:report"}
REVIEW_PASSED = "ai:review-passed"
CLOSING_RE = re.compile(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)\b", re.IGNORECASE)


def ready_to_merge_issues(items: list[dict]) -> set[int]:
    """Issue numbers closed by an open PR in the same list that carries ai:review-passed."""
    numbers: set[int] = set()
    for item in items:
        if "pull_request" not in item or item.get("state") != "open":
            continue
        if REVIEW_PASSED not in {lbl["name"] for lbl in item.get("labels", [])}:
            continue
        numbers.update(int(n) for n in CLOSING_RE.findall(item.get("body") or ""))
    return numbers


def status_for(issue: dict, ready_to_merge: set[int] | frozenset[int] = frozenset()) -> str | None:
    """Return the Status option for an issue, or None when it is not a pipeline item.

    ready_to_merge holds issue numbers whose open PR passed agent review (ai:review-passed).
    """
    labels = {lbl["name"] for lbl in issue.get("labels", [])}
    if labels & SKIP_LABELS or "pull_request" in issue:
        return None
    body = issue.get("body") or ""
    is_task = "<!-- ai:plan" in body or any(line.startswith("Parent: ") for line in body.splitlines())
    pipeline_labels = {lbl for lbl in labels if lbl in LABEL_STATUS}
    if not pipeline_labels and not is_task:
        return None
    if issue.get("state") == "closed":
        return "Done"
    in_pr_review = issue.get("number") in ready_to_merge
    for status in STATUS_ORDER:
        if status == "Ready to merge" and in_pr_review:
            return status
        if any(LABEL_STATUS.get(lbl) == status for lbl in pipeline_labels):
            return status
    return "Backlog"


def managed_repos(registry: dict, control_repo: str) -> list[str]:
    repos = [control_repo]
    for entry in registry.get("repos") or []:
        if entry.get("status") == "active" and entry["name"] not in repos:
            repos.append(entry["name"])
    return repos


class GitHub:
    def __init__(self, token: str) -> None:
        self.token = token

    def _call(self, method: str, url: str, payload: dict | None = None) -> object:
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())

    def issues(self, repo: str, state: str, since: str | None = None) -> list[dict]:
        out: list[dict] = []
        page = 1
        while True:
            url = f"{API}/repos/{repo}/issues?state={state}&per_page=100&page={page}"
            if since:
                url += f"&since={since}"
            batch = self._call("GET", url)
            assert isinstance(batch, list)
            out.extend(batch)
            if len(batch) < 100:
                return out
            page += 1

    def graphql(self, query: str, variables: dict) -> dict:
        result = self._call("POST", f"{API}/graphql", {"query": query, "variables": variables})
        assert isinstance(result, dict)
        if result.get("errors"):
            raise RuntimeError(json.dumps(result["errors"]))
        return result["data"]


PROJECT_QUERY = """
query($owner: String!, $number: Int!) {
  repositoryOwner(login: $owner) {
    ... on ProjectV2Owner {
      projectV2(number: $number) {
        id
        fields(first: 50) {
          nodes { ... on ProjectV2SingleSelectField { id name options { id name } } }
        }
      }
    }
  }
}
"""
ADD_ITEM = """
mutation($project: ID!, $content: ID!) {
  addProjectV2ItemById(input: {projectId: $project, contentId: $content}) { item { id } }
}
"""
SET_STATUS = """
mutation($project: ID!, $item: ID!, $field: ID!, $option: String!) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $project, itemId: $item, fieldId: $field,
    value: {singleSelectOptionId: $option}
  }) { projectV2Item { id } }
}
"""


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    policy = yaml.safe_load((ROOT / "registry/policy.yml").read_text())
    registry = yaml.safe_load((ROOT / "registry/repos.yml").read_text())
    cfg = policy.get("project") or {}
    if not cfg.get("number"):
        print("project.number is 0 or missing in registry/policy.yml: sync disabled.")
        return 0
    token = os.environ.get("PROJECT_SYNC_TOKEN")
    if not token:
        print("ERROR: PROJECT_SYNC_TOKEN is not set.", file=sys.stderr)
        return 1

    gh = GitHub(token)
    project = gh.graphql(PROJECT_QUERY, {"owner": cfg["owner"], "number": int(cfg["number"])})
    owner = project.get("repositoryOwner") or {}
    project = owner.get("projectV2")
    if not project:
        print(f"ERROR: Project {cfg['owner']}#{cfg['number']} not found or not readable with this token.", file=sys.stderr)
        return 1
    field = next((f for f in project["fields"]["nodes"] if f and f.get("name") == cfg.get("status_field", "Status")), None)
    if field is None:
        print(f"ERROR: single-select field '{cfg.get('status_field')}' not found in the Project.", file=sys.stderr)
        return 1
    options = {o["name"]: o["id"] for o in field["options"]}
    missing = [s for s in STATUS_ORDER if s not in options]
    if missing:
        print(f"ERROR: Status field is missing options: {', '.join(missing)}", file=sys.stderr)
        return 1

    since = (datetime.now(timezone.utc) - timedelta(days=CLOSED_LOOKBACK_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    synced = failed = 0
    for repo in managed_repos(registry, policy["control_repo"]):
        try:
            issues = gh.issues(repo, "open") + gh.issues(repo, "closed", since)
        except urllib.error.HTTPError as exc:
            print(f"WARN  {repo}: cannot list issues ({exc.code}); skipped")
            failed += 1
            continue
        merge_ready = ready_to_merge_issues(issues)
        for issue in issues:
            status = status_for(issue, merge_ready)
            if status is None:
                continue
            ref = f"{repo}#{issue['number']}"
            if dry_run:
                print(f"DRY   {ref} -> {status}")
                continue
            try:
                item = gh.graphql(ADD_ITEM, {"project": project["id"], "content": issue["node_id"]})
                item_id = item["addProjectV2ItemById"]["item"]["id"]
                gh.graphql(SET_STATUS, {"project": project["id"], "item": item_id,
                                        "field": field["id"], "option": options[status]})
                print(f"OK    {ref} -> {status}")
                synced += 1
            except (urllib.error.HTTPError, RuntimeError) as exc:
                print(f"WARN  {ref}: {exc}")
                failed += 1
    print(f"Synced {synced} item(s), {failed} failure(s).")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
