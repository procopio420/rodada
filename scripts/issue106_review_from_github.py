#!/usr/bin/env python3
"""Resolve an actual GitHub R3 approval on the tested PR HEAD, never from untrusted input JSON."""
import argparse
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


def fetch_json(repo, endpoint, token):
    url = "https://api.github.com/repos/" + repo + endpoint
    req = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token,
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urlopen(req, timeout=20) as response:
        return json.load(response)


def find_review(repo, number, sha, fetch):
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
    latest = {}
    for page in range(1, 11):
        reviews = fetch(f"/pulls/{number}/reviews?per_page=100&page={page}")
        if not isinstance(reviews, list):
            raise ReviewBlocked("R3 GitHub review list malformed")
        for review in reviews:
            user = review.get("user") or {}
            login = str(user.get("login") or "").casefold()
            if login and user.get("type") == "User" and review.get("state") in {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}:
                latest[login] = review
        if len(reviews) < 100:
            break
    else:
        raise ReviewBlocked("R3 review pagination exceeded configured limit")
    if any(r.get("state") == "CHANGES_REQUESTED" for r in latest.values()):
        raise ReviewBlocked("R3 has outstanding GitHub changes-requested review")
    for login, review in reversed(list(latest.items())):
        body = review.get("body") or ""
        if (login != author and review.get("state") == "APPROVED"
                and review.get("commit_id") == sha
                and re.search(r"(?im)^\s*R3:\s*PASS\s*$", body)
                and re.search(r"(?im)^\s*P0/P1:\s*0\s*$", body)
                and isinstance(review.get("id"), int)
                and review.get("submitted_at")):
            return {
                "sha": sha, "independent": True, "open_p0_p1": 0,
                "reviewer": review["user"]["login"],
                "approved_at": review["submitted_at"],
                "reference": f"https://github.com/{repo}/pull/{number}#pullrequestreview-{review['id']}",
                "source": "github-api-reviewed-pr-exact-head",
            }
    raise ReviewBlocked("No independent approved R3 on this exact SHA with R3: PASS and P0/P1: 0")


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
    result = find_review(args.repo, args.pr, args.sha, lambda endpoint: fetch_json(args.repo, endpoint, token))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("PASS: verified independent GitHub R3 on exact checkout SHA")


if __name__ == "__main__":
    try:
        main()
    except (ReviewBlocked, OSError, ValueError) as err:
        print("REVIEW_BLOCKED: " + type(err).__name__ + ": " + str(err), file=sys.stderr)
        raise SystemExit(1)
