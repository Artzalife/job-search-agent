#!/usr/bin/env python3
"""Probe company slugs across supported ATS platforms."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import (
    ASHBY_API_BASE,
    GREENHOUSE_API_BASE,
    LEVER_API_BASE,
    WORKABLE_API_BASE,
    load_companies,
)

HEADERS = {"Accept": "application/json", "User-Agent": "job-search-agent/1.0"}


def configured_slugs() -> dict[str, set[str]]:
    grouped: dict[str, set[str]] = {
        "greenhouse": set(),
        "lever": set(),
        "ashby": set(),
        "workable": set(),
        "workday": set(),
    }
    for row in load_companies():
        ats = row.get("ats", "").strip().casefold()
        slug = row.get("slug", "").strip()
        if ats in grouped and slug:
            grouped[ats].add(slug)
    return grouped


def probe_greenhouse(slug: str) -> tuple[bool, int, str]:
    url = f"{GREENHOUSE_API_BASE}/{slug}/jobs"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
        jobs = data.get("jobs", [])
        name = data.get("meta", {}).get("company_name") or slug
        return True, len(jobs), name
    except urllib.error.HTTPError:
        return False, 0, slug
    except (urllib.error.URLError, TimeoutError, OSError):
        return False, -1, slug


def probe_lever(slug: str) -> tuple[bool, int, str]:
    url = f"{LEVER_API_BASE}/{slug}?mode=json"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read())
        if isinstance(data, list):
            return True, len(data), slug
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
        pass
    return False, 0, slug


def probe_ashby(slug: str) -> tuple[bool, int, str]:
    url = f"{ASHBY_API_BASE}/{slug}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
        jobs = data.get("jobs", [])
        return True, len(jobs), slug
    except (urllib.error.HTTPError, urllib.error.URLError):
        return False, 0, slug


def probe_workable(slug: str) -> tuple[bool, int, str]:
    url = f"{WORKABLE_API_BASE}/{slug}?details=true"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
        jobs = data.get("jobs", [])
        name = data.get("name") or slug
        return True, len(jobs), name
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            time.sleep(2)
        return False, 0, slug
    except urllib.error.URLError:
        return False, -1, slug


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Probe candidate company slugs across ATS APIs. "
            "Existing registry slugs are skipped automatically."
        )
    )
    parser.add_argument(
        "slugs",
        nargs="*",
        help="Candidate slugs to probe (e.g. tempus guardanthealth).",
    )
    parser.add_argument(
        "--name",
        default="",
        help="Display name to use in suggested CSV rows when probing multiple slugs.",
    )
    args = parser.parse_args()

    if not args.slugs:
        print("Provide one or more candidate slugs to probe.", file=sys.stderr)
        print("Example: python3 scripts/probe_all_ats.py tempus guardanthealth", file=sys.stderr)
        raise SystemExit(2)

    existing = configured_slugs()
    seen: set[str] = set()

    new_gh: list[tuple[str, str, int]] = []
    new_lever: list[tuple[str, str, int]] = []
    new_ashby: list[tuple[str, str, int]] = []
    new_workable: list[tuple[str, str, int]] = []

    for slug in args.slugs:
        if slug in seen:
            continue
        seen.add(slug)
        display_name = args.name or slug

        if slug not in existing["greenhouse"]:
            ok, count, name = probe_greenhouse(slug)
            if ok:
                new_gh.append((slug, name if name != slug else display_name, count))

        if slug not in existing["lever"]:
            ok, count, _ = probe_lever(slug)
            if ok:
                new_lever.append((slug, display_name, count))

        if slug not in existing["ashby"]:
            ok, count, _ = probe_ashby(slug)
            if ok:
                new_ashby.append((slug, display_name, count))

        if slug not in existing["workable"]:
            ok, count, name = probe_workable(slug)
            if ok:
                new_workable.append((slug, name if name != slug else display_name, count))
            time.sleep(0.3)

    new_gh.sort(key=lambda item: (-item[2], item[1]))
    new_lever.sort(key=lambda item: (-item[2], item[1]))
    new_ashby.sort(key=lambda item: (-item[2], item[1]))
    new_workable.sort(key=lambda item: (-item[2], item[1]))

    print("=== Suggested rows for data/companies.csv ===")
    print("# Copy the matching line(s) into the CSV, set category, then run validate_companies.py\n")

    for slug, name, count in new_gh:
        company_id = name.lower().replace(" ", "-")
        print(
            f'{company_id},General Tech,{name},greenhouse,{slug},yes,# {count} jobs,,'
        )

    for slug, name, count in new_lever:
        company_id = name.lower().replace(" ", "-")
        print(
            f'{company_id},Healthcare Infrastructure,{name},lever,{slug},yes,# {count} jobs,,'
        )

    for slug, name, count in new_ashby:
        company_id = name.lower().replace(" ", "-")
        print(
            f'{company_id},Healthcare Infrastructure,{name},ashby,{slug},yes,# {count} jobs,,'
        )

    for slug, name, count in new_workable:
        company_id = name.lower().replace(" ", "-")
        print(
            f'{company_id},Healthcare Infrastructure,{name},workable,{slug},yes,# {count} jobs,,'
        )

    print(
        f"\nTotals: GH={len(new_gh)} Lever={len(new_lever)} Ashby={len(new_ashby)} "
        f"Workable={len(new_workable)}"
    )


if __name__ == "__main__":
    main()
