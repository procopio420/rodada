#!/usr/bin/env python3
"""Resolve an actual GitHub R3 approval on the tested PR HEAD, never from untrusted input JSON."""
import argparse
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
from urllib.request import Request, urlopen

SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
REPO_RE = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")


class ReviewBlocked(ValueError):
    pass


# This registry is injected by a maintainer-controlled GitHub Actions variable,
# never loaded from the PR being reviewed. Empty means human approvals only.
CAPABILITIES = frozenset({"general", "backend", "web", "android", "payments", "security"})
AGENT_LOGIN_RE = re.compile(r"[A-Za-z0-9-]+\[bot\]\Z", re.IGNORECASE)


def parse_qualified_agents(raw):
    if not raw or not raw.strip():
        return {}
    try:
        registry = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise ReviewBlocked("R3 qualified-agent registry must be valid JSON") from exc
    if not isinstance(registry, dict) or not registry or len(registry) > 50:
        raise ReviewBlocked("R3 qualified-agent registry must be a nonempty object of at most 50 entries")
    result = {}
    for login, item in registry.items():
        if not isinstance(login, str) or not AGENT_LOGIN_RE.fullmatch(login):
            raise ReviewBlocked("R3 agent must use a dedicated GitHub App [bot] identity")
        if not isinstance(item, dict) or set(item) != {"capabilities", "expires_on", "sponsor"}:
            raise ReviewBlocked("R3 agent requires capabilities, expiry and maintainer sponsor")
        caps = item["capabilities"]
        if (not isinstance(caps, list) or not caps or not all(isinstance(c, str) for c in caps)
                or len(set(caps)) != len(caps) or not set(caps) <= CAPABILITIES):
            raise ReviewBlocked("R3 agent capabilities must be explicit and supported")
        sponsor = item["sponsor"]
        if (not isinstance(sponsor, str) or not re.fullmatch(r"[A-Za-z0-9-]{1,39}", sponsor)
                or sponsor.casefold() == login.casefold()):
            raise ReviewBlocked("R3 agent requires a named human maintainer sponsor")
        try:
            expiry = date.fromisoformat(item["expires_on"])
        except (TypeError, ValueError) as exc:
            raise ReviewBlocked("R3 agent expiry must be an ISO date") from exc
        if login.casefold() in result:
            raise ReviewBlocked("duplicate case-insensitive R3 agent identity")
        result[login.casefold()] = {
            "capabilities": set(caps), "expires_on": expiry, "sponsor": sponsor,
        }
    return result


def required_scopes(number, fetch):
    scopes = set()
    for page in range(1, 11):
        files = fetch(f"/pulls/{number}/files?per_page=100&page={page}")
        if not isinstance(files, list):
            raise ReviewBlocked("R3 PR changed-file list malformed")
        for entry in files:
            path = entry.get("filename") if isinstance(entry, dict) else None
            if not isinstance(path, str) or not path or path.startswith("/"):
                raise ReviewBlocked("R3 changed-file path malformed")
            name = path.lower()
            matched = False
            if (name.startswith(".github/") or name.startswith("docs/ci-workflows")
                    or name.startswith("docs/agents/code-review")
                    or name.startswith("scripts/issue106_review_")
                    or name.startswith("scripts/tests/test_issue106_review_")
                    or name.startswith("scripts/e2e_evidence")
                    or name.startswith("scripts/build-issue106-report")
                    or name.startswith("scripts/r3_chatgpt_reviewer")
                    or name.startswith("scripts/tests/test_r3_chatgpt_reviewer")):
                scopes.add("security")
                matched = True
            if any(word in name for word in ("payment", "ledger", "cash", "refund", "financial", "stripe", "terminal")):
                scopes.add("payments")
                matched = True
            if any(word in name for word in ("auth", "tenant", "permission", "security", "credential", "session", "csrf")):
                scopes.add("security")
                matched = True
            if name.startswith("apps/attendance-android/"):
                scopes.add("android")
                matched = True
            if name.startswith("apps/web/") or name.startswith("apps/landing/"):
                scopes.add("web")
                matched = True
            if name.startswith("apps/api/") or name.startswith("scripts/"):
                scopes.add("backend")
                matched = True
            if not matched:
                scopes.add("general")
        if len(files) < 100:
            if not scopes:
                raise ReviewBlocked("R3 PR has no verifiable changed files")
            return scopes
    raise ReviewBlocked("R3 changed-file pagination exceeded configured limit")


def agent_review_evidence(repo, number, sha, login, body, fetch):
    if not re.search(r"(?im)^R3-Agent-Context:\s*isolated\s*$", body):
        raise ReviewBlocked("R3 agent must attest independent isolated review context")
    match = re.search(
        rf"(?im)^R3-Evidence:\s*(https://github\.com/{re.escape(repo)}/pull/{number}#issuecomment-(\d+))\s*$",
        body,
    )
    if not match:
        raise ReviewBlocked("R3 agent must link a same-PR GitHub evidence comment")
    comment = fetch(f"/issues/comments/{match.group(2)}")
    if (not isinstance(comment, dict)
            or (comment.get("user") or {}).get("login", "").casefold() != login
            or comment.get("html_url") != match.group(1)):
        raise ReviewBlocked("R3 evidence must originate from this approved agent on the PR")
    evidence = comment.get("body") or ""
    if (not re.search(rf"(?im)^R3-Reviewed-SHA:\s*{re.escape(sha)}\s*$", evidence)
            or not re.search(r"(?im)^R3-Tests-Checked:\s*\S.+$", evidence)
            or not re.search(r"(?im)^R3-Risks-Checked:\s*\S.+$", evidence)):
        raise ReviewBlocked("R3 agent evidence lacks exact-SHA, tests and risks")
    return match.group(1)


def fetch_json(repo, endpoint, token):
    url = "https://api.github.com/repos/" + repo + endpoint
    req = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token,
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urlopen(req, timeout=20) as response:
        return json.load(response)


def find_review(repo, number, sha, fetch, qualified_agents=None, today=None):
    if not REPO_RE.fullmatch(repo) or not SHA_RE.fullmatch(sha) or not isinstance(number, int) or number < 1:
        raise ReviewBlocked("R3 requires validated repository, PR and exact 40-character SHA")
    pr = fetch(f"/pulls/{number}")
    if pr.get("head", {}).get("sha") != sha:
        raise ReviewBlocked("R3 PR HEAD differs from executed SHA")
    if pr.get("head", {}).get("repo", {}).get("full_name") != repo:
        raise ReviewBlocked("R3 PR must belong to the same repository")
    author = pr.get("user", {}).get("login", "").casefold()
    if not author:
        raise ReviewBlocked("R3 PR author unavailable")
    qualified_agents = qualified_agents or {}
    today = today or datetime.now(timezone.utc).date()
    latest = {}
    for page in range(1, 11):
        reviews = fetch(f"/pulls/{number}/reviews?per_page=100&page={page}")
        if not isinstance(reviews, list):
            raise ReviewBlocked("R3 GitHub review list malformed")
        for review in reviews:
            user = review.get("user") or {}
            login = str(user.get("login") or "").casefold()
            if login and user.get("type") in {"User", "Bot"} and review.get("state") in {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}:
                latest[login] = review
        if len(reviews) < 100:
            break
    else:
        raise ReviewBlocked("R3 review pagination exceeded configured limit")
    if any(r.get("state") == "CHANGES_REQUESTED" for r in latest.values()):
        raise ReviewBlocked("R3 has outstanding GitHub changes-requested review")
    for login, review in reversed(list(latest.items())):
        body = review.get("body") or ""
        if not (login != author and review.get("state") == "APPROVED"
                and review.get("commit_id") == sha
                and re.search(r"(?im)^\s*R3:\s*PASS\s*$", body)
                and re.search(r"(?im)^\s*P0/P1:\s*0\s*$", body)
                and isinstance(review.get("id"), int)
                and review.get("submitted_at")):
            continue
        proof = {
            "sha": sha, "independent": True, "open_p0_p1": 0,
            "reviewer": review["user"]["login"],
            "approved_at": review["submitted_at"],
            "reference": f"https://github.com/{repo}/pull/{number}#pullrequestreview-{review['id']}",
            "source": "github-api-reviewed-pr-exact-head",
        }
        if review["user"].get("type") == "User":
            return proof
        qualification = qualified_agents.get(login)
        if not qualification or qualification["expires_on"] < today:
            continue
        scopes = required_scopes(number, fetch)
        if not scopes <= qualification["capabilities"]:
            continue
        evidence = agent_review_evidence(repo, number, sha, login, body, fetch)
        return dict(proof, source="github-api-qualified-agent-exact-head",
                    reviewer_kind="qualified-agent", qualification_sponsor=qualification["sponsor"],
                    capabilities=sorted(qualification["capabilities"]),
                    reviewed_scopes=sorted(scopes), evidence_url=evidence)
    raise ReviewBlocked("No independent qualified human/agent approved R3 on this exact SHA; veto, qualification and provenance are mandatory")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    token = os.environ.get("GH_TOKEN")
    if not token:
        raise ReviewBlocked("GH_TOKEN required for authenticated review verification")
    agents = parse_qualified_agents(os.environ.get("RODADA_R3_QUALIFIED_AGENT_REVIEWERS", ""))
    result = find_review(args.repo, args.pr, args.sha, lambda endpoint: fetch_json(args.repo, endpoint, token), qualified_agents=agents)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("PASS: verified independent GitHub R3 on exact checkout SHA")


if __name__ == "__main__":
    try:
        main()
    except (ReviewBlocked, OSError, ValueError) as err:
        print("REVIEW_BLOCKED: " + type(err).__name__ + ": " + str(err), file=sys.stderr)
        raise SystemExit(1)
