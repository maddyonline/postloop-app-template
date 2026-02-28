#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

UTC = getattr(datetime, "UTC", timezone.utc)  # pragma: no cover


@dataclass(frozen=True)
class AppRow:
    name: str
    state: str
    created_at: datetime | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manually clean up Modal preview apps created by PR preview workflow."
    )
    parser.add_argument(
        "--prefix",
        default="postloop-preview-",
        help="App name prefix to match (default: postloop-preview-)",
    )
    parser.add_argument(
        "--pr-number",
        type=int,
        default=0,
        help="Optional PR number to target only postloop-preview-pr-<number>-* apps.",
    )
    parser.add_argument(
        "--older-than-hours",
        type=float,
        default=0,
        help="Only stop apps older than this many hours (0 disables age filter).",
    )
    parser.add_argument(
        "--keep-latest",
        type=int,
        default=0,
        help="Keep N newest matching apps and stop the rest (default: 0).",
    )
    parser.add_argument(
        "--include-stopped",
        action="store_true",
        help="Include already stopped apps in output and filtering.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually stop apps. Without this flag, command is dry-run only.",
    )
    return parser.parse_args()


def _parse_created_at(value: str) -> datetime | None:
    raw = value.strip()
    if not raw:
        return None
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _run(command: list[str]) -> tuple[bool, str]:
    proc = subprocess.run(command, capture_output=True, text=True)
    combined = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, combined.strip()


def list_apps() -> list[AppRow]:
    ok, out = _run(["modal", "app", "list", "--json"])
    if not ok:
        raise RuntimeError(out or "modal app list failed")

    data: list[dict[str, Any]] = json.loads(out or "[]")
    rows: list[AppRow] = []
    for item in data:
        rows.append(
            AppRow(
                name=str(item.get("Description", "")).strip(),
                state=str(item.get("State", "")).strip().lower(),
                created_at=_parse_created_at(str(item.get("Created at", ""))),
            )
        )
    return rows


def main() -> int:
    args = parse_args()
    prefix = (
        f"postloop-preview-pr-{args.pr_number}-"
        if args.pr_number > 0
        else str(args.prefix).strip()
    )

    if not prefix:
        print("Prefix cannot be empty.", file=sys.stderr)
        return 2

    now = datetime.now(UTC)
    threshold = (
        now - timedelta(hours=float(args.older_than_hours))
        if args.older_than_hours and args.older_than_hours > 0
        else None
    )

    try:
        apps = list_apps()
    except Exception as exc:
        print(f"Failed to list Modal apps: {exc}", file=sys.stderr)
        return 1

    matched = [app for app in apps if app.name and app.name.startswith(prefix)]
    if not args.include_stopped:
        matched = [app for app in matched if app.state != "stopped"]

    if threshold is not None:
        matched = [
            app
            for app in matched
            if app.created_at is not None and app.created_at <= threshold
        ]

    matched.sort(
        key=lambda app: app.created_at or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )

    if args.keep_latest > 0:
        targets = matched[args.keep_latest :]
    else:
        targets = matched

    print(f"Matched apps: {len(matched)} (prefix={prefix})")
    print(f"Stop candidates: {len(targets)}")
    for app in targets:
        created = app.created_at.isoformat() if app.created_at else "unknown"
        print(f"- {app.name} state={app.state} created_at={created}")

    if not targets:
        return 0

    if not args.apply:
        print("Dry run only. Re-run with --apply to stop these apps.")
        return 0

    failures = 0
    for app in targets:
        ok, out = _run(["modal", "app", "stop", app.name])
        if ok:
            print(f"stopped {app.name}")
        else:
            failures += 1
            print(f"failed to stop {app.name}: {out}", file=sys.stderr)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
