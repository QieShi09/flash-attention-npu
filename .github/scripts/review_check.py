#!/usr/bin/env python3
"""Create or update the stable Check Run used by the trusted PR review."""

import argparse
from datetime import datetime, timezone
import json
import os
import re
import subprocess


CHECK_NAME = "Trusted PR Review"
SHA = re.compile(r"^[0-9a-f]{40}$")


def gh_api(args, payload=None):
    command = ["gh", "api", *args]
    result = subprocess.run(
        command,
        input=json.dumps(payload) if payload is not None else None,
        text=True,
        check=True,
        capture_output=True,
    )
    return json.loads(result.stdout) if result.stdout.strip() else {}


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def repository():
    value = os.environ.get("GITHUB_REPOSITORY", "")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
        raise SystemExit("GITHUB_REPOSITORY must be OWNER/REPO")
    return value


def start(head_sha, summary):
    if not SHA.fullmatch(head_sha):
        raise SystemExit("invalid head SHA")
    repo = repository()
    existing = gh_api([f"repos/{repo}/commits/{head_sha}/check-runs?per_page=100"])
    candidates = [
        item
        for item in existing.get("check_runs", [])
        if item.get("name") == CHECK_NAME
    ]
    payload = {
        "name": CHECK_NAME,
        "head_sha": head_sha,
        "status": "in_progress",
        "started_at": now(),
        "output": {"title": "Review in progress", "summary": summary},
    }
    if candidates:
        check_id = candidates[-1]["id"]
        gh_api(
            [
                "--method",
                "PATCH",
                "--input",
                "-",
                f"repos/{repo}/check-runs/{check_id}",
            ],
            payload,
        )
    else:
        created = gh_api(
            ["--method", "POST", "--input", "-", f"repos/{repo}/check-runs"],
            payload,
        )
        check_id = created["id"]
    print(check_id)


def complete(check_id, conclusion, summary):
    if not check_id.isdigit():
        raise SystemExit("invalid check run ID")
    if conclusion not in {
        "success",
        "failure",
        "neutral",
        "cancelled",
        "timed_out",
        "action_required",
    }:
        raise SystemExit("invalid check conclusion")
    repo = repository()
    payload = {
        "status": "completed",
        "completed_at": now(),
        "conclusion": conclusion,
        "output": {"title": f"Review {conclusion}", "summary": summary},
    }
    gh_api(
        ["--method", "PATCH", "--input", "-", f"repos/{repo}/check-runs/{check_id}"],
        payload,
    )


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action", required=True)
    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--head-sha", required=True)
    start_parser.add_argument("--summary", required=True)
    complete_parser = subparsers.add_parser("complete")
    complete_parser.add_argument("--check-run-id", required=True)
    complete_parser.add_argument("--conclusion", required=True)
    complete_parser.add_argument("--summary", required=True)
    args = parser.parse_args()
    if args.action == "start":
        start(args.head_sha, args.summary)
    else:
        complete(args.check_run_id, args.conclusion, args.summary)


if __name__ == "__main__":
    main()
