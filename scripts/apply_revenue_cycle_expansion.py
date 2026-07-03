#!/usr/bin/env python3
"""Apply Revenue Cycle expansion to data/companies.csv."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "companies.csv"
VERIFIED_PATH = ROOT / "data" / "_revenue_cycle_verified.json"
SKIPPED_PATH = ROOT / "data" / "_revenue_cycle_skipped.json"
MANUAL_REVIEW_PATH = ROOT / "data" / "manual_review_queue.csv"

# Ambiguous slug matches excluded despite API probe success.
EXCLUDE_ATS_SLUG = {
    ("workable", "olive"),
    ("ashby", "change"),
    ("workable", "ribbon"),
    ("workable", "bridge"),
    ("workable", "regal"),
    ("workable", "dock"),
    ("workable", "hometeam"),
    ("workable", "landmark"),
    ("workable", "formstack"),
    ("lever", "blinq"),
    ("workable", "greenway"),
    ("greenhouse", "dispatch"),
    ("workable", "hinge"),
    ("workable", "cognizant"),
    ("workable", "flywire"),
    ("workable", "bamboo"),
    ("workable", "gramercy"),
    ("workable", "spiral"),
    ("workable", "assured"),
    ("workable", "sift"),
}

# Duplicate company_id rows to remove (keep the other entry).
# When deduping company_id, prefer keeping this (ats, slug) pair.
PREFER_ATS_SLUG = {
    "candid-health": ("ashby", "candidhealth"),
}

RECATEGORIZE_TO_REVENUE_CYCLE = {
    # Seed list — miscategorized RCM companies.
    "cedar",
    "cohere-health",
    "clarify-health",
    "adonis",
    "candid-health",
    # Practice management / billing platforms.
    "advancedmd",
    "athenahealth",
    "carecloud",
    "curemd",
    "eclinicalworks",
    "nextgen-healthcare",
    "rxnt",
    "simplepractice",
    "tebra",
    "hint-health",
    "elation-health",
    # RCM data, analytics, and operations.
    "healthverity",
    "leantaas",
    "medeanalytics",
    "medispend",
    "tendo",
    "moxe",
    "axuall",
    "certifyos",
    "innovaccer",
    "nomi-health",
    "notable-health",
    "closedloop-ai",
    "medrio",
    "commure",
    "qventus",
    "smarterdx",
}

MANUAL_REVIEW_EXTRA = [
    {
        "display_name": "FinThrive",
        "category": "Revenue Cycle",
        "reason": "No supported ATS board found; likely Workday or custom portal",
        "slug_candidates": "finthrive, nthrive",
    },
    {
        "display_name": "Availity",
        "category": "Revenue Cycle",
        "reason": "No supported ATS board found; likely Workday or custom portal",
        "slug_candidates": "availity",
    },
    {
        "display_name": "HealthEdge",
        "category": "Revenue Cycle",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "healthedge",
    },
    {
        "display_name": "Navina",
        "category": "Revenue Cycle",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "navina, navinahealth",
    },
    {
        "display_name": "Olive AI",
        "category": "Revenue Cycle",
        "reason": "Historical company (defunct); board may be stale",
        "slug_candidates": "olive, oliveai",
    },
    {
        "display_name": "Change Healthcare",
        "category": "Revenue Cycle",
        "reason": "Ambiguous slug match on ashby/change (likely Change.org)",
        "slug_candidates": "change, changehealthcare",
    },
    {
        "display_name": "Ribbon Health",
        "category": "Revenue Cycle",
        "reason": "Ambiguous slug match on workable/ribbon",
        "slug_candidates": "ribbon, ribbonhealth",
    },
    {
        "display_name": "Experian Health",
        "category": "Revenue Cycle",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "experianhealth, experian",
    },
    {
        "display_name": "Phreesia",
        "category": "Revenue Cycle",
        "reason": "No supported ATS board found; likely Workday or custom portal",
        "slug_candidates": "phreesia, phreesiainc",
    },
    {
        "display_name": "ModMed",
        "category": "Revenue Cycle",
        "reason": "No supported ATS board found; likely custom careers portal",
        "slug_candidates": "modmed, modernizingmedicine",
    },
    {
        "display_name": "athenahealth",
        "category": "Revenue Cycle",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "athenahealth, athena",
    },
    {
        "display_name": "eClinicalWorks",
        "category": "Revenue Cycle",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "eclinicalworks, ecw",
    },
    {
        "display_name": "Greenway Health",
        "category": "Revenue Cycle",
        "reason": "Ambiguous slug match on workable/greenway",
        "slug_candidates": "greenway, greenwayhealth",
    },
    {
        "display_name": "Flywire Health",
        "category": "Revenue Cycle",
        "reason": "Ambiguous slug match on workable/flywire (Flywire fintech vs healthcare payments)",
        "slug_candidates": "flywire, flywirehealth",
    },
]

FIELDNAMES = [
    "company_id",
    "category",
    "display_name",
    "ats",
    "slug",
    "enabled",
    "notes",
    "wd_server",
    "workday_site",
]

MANUAL_FIELDNAMES = ["display_name", "category", "reason", "slug_candidates"]


def load_rows() -> list[dict[str, str]]:
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def row_to_csv(row: dict[str, str]) -> dict[str, str]:
    return {field: row.get(field, "") for field in FIELDNAMES}


def load_existing_manual_review() -> list[dict[str, str]]:
    if not MANUAL_REVIEW_PATH.exists():
        return []
    with MANUAL_REVIEW_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def merge_manual_review(*groups: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for group in groups:
        for item in group:
            key = (item["display_name"].casefold(), item["category"])
            if key in seen:
                continue
            seen.add(key)
            merged.append({field: item.get(field, "") for field in MANUAL_FIELDNAMES})
    return merged


def dedupe_company_ids(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_id: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_id.setdefault(row["company_id"], []).append(row)

    result: list[dict[str, str]] = []
    for company_id, group in by_id.items():
        if len(group) == 1:
            result.append(group[0])
            continue
        preferred = PREFER_ATS_SLUG.get(company_id)
        if preferred:
            keep = next(
                (r for r in group if (r["ats"].casefold(), r["slug"]) == preferred),
                group[0],
            )
            result.append(keep)
        else:
            result.append(group[0])
    return result


def main() -> None:
    rows = load_rows()
    existing_ats_slug = {(r["ats"].casefold(), r["slug"]) for r in rows}
    existing_ids = {r["company_id"] for r in rows}

    verified = json.loads(VERIFIED_PATH.read_text(encoding="utf-8"))
    skipped = json.loads(SKIPPED_PATH.read_text(encoding="utf-8"))

    added = 0
    for entry in verified:
        key = (entry["ats"].casefold(), entry["slug"])
        if key in EXCLUDE_ATS_SLUG:
            continue
        if key in existing_ats_slug or entry["company_id"] in existing_ids:
            continue
        rows.append(row_to_csv(entry))
        existing_ats_slug.add(key)
        existing_ids.add(entry["company_id"])
        added += 1

    recategorized = 0
    for row in rows:
        if row["company_id"] in RECATEGORIZE_TO_REVENUE_CYCLE and row["category"] != "Revenue Cycle":
            row["category"] = "Revenue Cycle"
            recategorized += 1
        # Candid Health duplicate: recategorize ashby entry, drop greenhouse duplicate later
        if row["company_id"] == "candid-health":
            row["category"] = "Revenue Cycle"

    before_dedupe = len(rows)
    rows = dedupe_company_ids(rows)
    deduped = before_dedupe - len(rows)

    rows.sort(key=lambda r: (r["category"], r["display_name"].casefold()))

    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    new_manual_rows = []
    for item in skipped:
        new_manual_rows.append(
            {
                "display_name": item["display_name"],
                "category": "Revenue Cycle",
                "reason": item["reason"],
                "slug_candidates": item["slug_candidates"],
            }
        )
    for item in MANUAL_REVIEW_EXTRA:
        new_manual_rows.append(item)

    manual_rows = merge_manual_review(load_existing_manual_review(), new_manual_rows)
    with MANUAL_REVIEW_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANUAL_FIELDNAMES)
        writer.writeheader()
        writer.writerows(manual_rows)

    revenue_cycle_count = sum(1 for r in rows if r["category"] == "Revenue Cycle")
    print(
        f"Added {added} companies, recategorized {recategorized}, "
        f"deduped {deduped}, Revenue Cycle total: {revenue_cycle_count}"
    )
    print(f"Manual review queue: {len(manual_rows)} entries -> {MANUAL_REVIEW_PATH}")


if __name__ == "__main__":
    main()
