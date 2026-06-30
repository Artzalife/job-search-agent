#!/usr/bin/env python3
"""Validate the operational company registry in data/companies.csv."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import (
    ASHBY_API_BASE,
    COMPANIES_CSV,
    GREENHOUSE_API_BASE,
    LEVER_API_BASE,
    VALID_ATS,
    VALID_CATEGORIES,
    WORKABLE_API_BASE,
    load_boards,
    load_companies,
)

HEADERS = {"Accept": "application/json", "User-Agent": "job-search-agent/1.0"}
REQUIRED_COLUMNS = (
    "company_id",
    "category",
    "display_name",
    "ats",
    "slug",
    "enabled",
    "notes",
    "wd_server",
    "workday_site",
)
SNAPSHOT_PATH = Path(__file__).resolve().parents[1] / "data" / "_migration_snapshot.json"


def _is_enabled(value: str) -> bool:
    return value.strip().casefold() in {"yes", "y", "true", "1"}


def validate_registry() -> list[str]:
    errors: list[str] = []

    if not COMPANIES_CSV.exists():
        return [f"Missing registry file: {COMPANIES_CSV}"]

    with COMPANIES_CSV.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return ["Registry CSV has no header row."]
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in reader.fieldnames]
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")
            return errors
        rows = list(reader)

    if not rows:
        errors.append("Registry CSV contains no company rows.")
        return errors

    seen_ats_slug: set[tuple[str, str]] = set()
    enabled_count = 0

    for index, row in enumerate(rows, start=2):
        row_label = f"row {index} ({row.get('display_name') or row.get('slug') or 'unknown'})"

        for field in ("company_id", "category", "display_name", "ats", "slug", "enabled"):
            if not row.get(field, "").strip():
                errors.append(f"{row_label}: missing required field '{field}'")

        category = row.get("category", "").strip()
        if category and category not in VALID_CATEGORIES:
            errors.append(f"{row_label}: unknown category '{category}'")

        ats = row.get("ats", "").strip().casefold()
        if ats and ats not in VALID_ATS:
            errors.append(f"{row_label}: unknown ats '{ats}'")

        slug = row.get("slug", "").strip()
        if ats and slug:
            key = (ats, slug)
            if key in seen_ats_slug:
                errors.append(f"{row_label}: duplicate enabled/disabled entry for ({ats}, {slug})")
            seen_ats_slug.add(key)

        if not _is_enabled(row.get("enabled", "")):
            continue

        enabled_count += 1
        if ats == "workday":
            if not row.get("wd_server", "").strip():
                errors.append(f"{row_label}: workday row missing wd_server")
            if not row.get("workday_site", "").strip():
                errors.append(f"{row_label}: workday row missing workday_site")

    if enabled_count == 0:
        errors.append("No enabled company rows found.")

    return errors


def check_migration_snapshot() -> list[str]:
    if not SNAPSHOT_PATH.exists():
        return []

    expected = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    greenhouse, lever, ashby, workable, workday = load_boards()
    loaded = {
        "GREENHOUSE_BOARDS": greenhouse,
        "LEVER_BOARDS": lever,
        "ASHBY_BOARDS": ashby,
        "WORKABLE_BOARDS": workable,
        "WORKDAY_BOARDS": workday,
    }

    errors: list[str] = []
    for key in expected:
        if loaded[key] != expected[key]:
            errors.append(f"Migration mismatch in {key}.")
    return errors


def probe_enabled_boards() -> list[str]:
    errors: list[str] = []
    for row in load_companies():
        if not _is_enabled(row.get("enabled", "")):
            continue

        ats = row.get("ats", "").strip().casefold()
        slug = row.get("slug", "").strip()
        name = row.get("display_name", "").strip()
        label = f"{name} [{ats}/{slug}]"

        try:
            if ats == "greenhouse":
                url = f"{GREENHOUSE_API_BASE}/{slug}/jobs"
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status != 200:
                        errors.append(f"{label}: HTTP {response.status}")
            elif ats == "lever":
                url = f"{LEVER_API_BASE}/{slug}?mode=json"
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, timeout=8) as response:
                    if response.status != 200:
                        errors.append(f"{label}: HTTP {response.status}")
            elif ats == "ashby":
                url = f"{ASHBY_API_BASE}/{slug}"
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status != 200:
                        errors.append(f"{label}: HTTP {response.status}")
            elif ats == "workable":
                url = f"{WORKABLE_API_BASE}/{slug}?details=true"
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status != 200:
                        errors.append(f"{label}: HTTP {response.status}")
                time.sleep(0.3)
            elif ats == "workday":
                tenant = slug
                wd_server = row.get("wd_server", "").strip()
                site = row.get("workday_site", "").strip()
                url = (
                    f"https://{tenant}.{wd_server}.myworkdayjobs.com/"
                    f"wday/cxs/{tenant}/{site}/jobs"
                )
                body = json.dumps(
                    {"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""}
                ).encode()
                req = urllib.request.Request(
                    url,
                    data=body,
                    method="POST",
                    headers={**HEADERS, "Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=12) as response:
                    if response.status != 200:
                        errors.append(f"{label}: HTTP {response.status}")
        except urllib.error.HTTPError as exc:
            errors.append(f"{label}: HTTP {exc.code}")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            errors.append(f"{label}: {exc}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--probe",
        action="store_true",
        help="Probe each enabled board against its ATS public API.",
    )
    parser.add_argument(
        "--check-migration",
        action="store_true",
        help="Verify loaded board dicts match data/_migration_snapshot.json.",
    )
    args = parser.parse_args()

    errors = validate_registry()
    if args.check_migration:
        errors.extend(check_migration_snapshot())
    if args.probe:
        errors.extend(probe_enabled_boards())

    if errors:
        print(f"Validation failed with {len(errors)} issue(s):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    companies = load_companies()
    enabled = sum(1 for row in companies if _is_enabled(row.get("enabled", "")))
    print(f"OK: {len(companies)} company row(s), {enabled} enabled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
