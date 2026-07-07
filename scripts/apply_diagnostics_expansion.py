#!/usr/bin/env python3
"""Apply Diagnostics expansion to data/companies.csv."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "companies.csv"
VERIFIED_PATH = ROOT / "data" / "_diagnostics_verified.json"
SKIPPED_PATH = ROOT / "data" / "_diagnostics_skipped.json"
MANUAL_REVIEW_PATH = ROOT / "data" / "manual_review_queue.csv"

# Ambiguous slug matches excluded despite API probe success.
EXCLUDE_ATS_SLUG = {
    ("greenhouse", "fabric"),
    ("workable", "current"),
    ("greenhouse", "current"),
    ("workable", "huma"),
    ("greenhouse", "huma"),
    ("workable", "thorne"),
    ("greenhouse", "function"),
    ("workable", "function"),
    ("greenhouse", "color"),
    ("workable", "color"),
    ("greenhouse", "helix"),
    ("workable", "helix"),
    ("greenhouse", "flatiron"),
    ("workable", "flatiron"),
    ("greenhouse", "kindbody"),
    ("workable", "kindbody"),
    ("greenhouse", "progyny"),
    ("workable", "progyny"),
    ("greenhouse", "caption"),
    ("workable", "caption"),
    ("greenhouse", "imagen"),
    ("workable", "imagen"),
    ("greenhouse", "sonic"),
    ("workable", "sonic"),
    ("greenhouse", "eurofins"),
    ("workable", "eurofins"),
    ("greenhouse", "thermo"),
    ("workable", "thermo"),
    ("greenhouse", "quest"),
    ("workable", "quest"),
    ("greenhouse", "labcorp"),
    ("workable", "labcorp"),
    ("greenhouse", "bd"),
    ("workable", "bd"),
    ("greenhouse", "agilent"),
    ("workable", "agilent"),
    ("greenhouse", "illumina"),
    ("workable", "illumina"),
    ("greenhouse", "hologic"),
    ("workable", "hologic"),
    ("greenhouse", "pacbio"),
    ("workable", "pacbio"),
    ("greenhouse", "nanopore"),
    ("workable", "nanopore"),
    ("greenhouse", "caris"),
    ("workable", "caris"),
    ("greenhouse", "myriad"),
    ("workable", "myriad"),
    ("greenhouse", "neo"),
    ("workable", "neo"),
    ("greenhouse", "sema4"),
    ("workable", "sema4"),
    ("greenhouse", "fulgent"),
    ("workable", "fulgent"),
    ("greenhouse", "foundation"),
    ("workable", "foundation"),
    ("greenhouse", "invitae"),
    ("workable", "invitae"),
    ("greenhouse", "tempus"),
    ("workable", "tempus"),
    ("greenhouse", "cue"),
    ("workable", "cue"),
    ("greenhouse", "dexcom"),
    ("workable", "dexcom"),
    ("greenhouse", "xifin"),
    ("workable", "xifin"),
    ("greenhouse", "sunquest"),
    ("workable", "sunquest"),
    ("greenhouse", "zebra-med"),
    ("workable", "zebra-med"),
    ("greenhouse", "nanox"),
    ("workable", "nanox"),
    ("greenhouse", "viz"),
    ("workable", "viz"),
    ("greenhouse", "vizai"),
    ("workable", "vizai"),
    ("greenhouse", "arterys"),
    ("workable", "arterys"),
    ("greenhouse", "qure"),
    ("workable", "qure"),
    ("greenhouse", "qureai"),
    ("workable", "qureai"),
    ("greenhouse", "riverain"),
    ("workable", "riverain"),
    ("greenhouse", "intelerad"),
    ("workable", "intelerad"),
    ("greenhouse", "bioreference"),
    ("workable", "bioreference"),
    ("greenhouse", "ambry"),
    ("workable", "ambry"),
    ("greenhouse", "ovia"),
    ("workable", "ovia"),
    ("greenhouse", "everlywell"),
    ("workable", "everlywell"),
    ("greenhouse", "insidetracker"),
    ("workable", "insidetracker"),
    ("greenhouse", "ezra"),
    ("workable", "ezra"),
    ("greenhouse", "thrive"),
    ("workable", "thrive"),
    ("greenhouse", "cuehealth"),
    ("workable", "cuehealth"),
    ("greenhouse", "questdiagnostics"),
    ("workable", "questdiagnostics"),
    ("greenhouse", "thermofisher"),
    ("workable", "thermofisher"),
}

RECATEGORIZE_TO_DIAGNOSTICS = {
    # Seed list — miscategorized diagnostic companies.
    "invitae",
    "tempus",
    "pathai",
    "lunit",
    "aidoc",
    "rapidai",
    "cleerly",
    "heartflow",
    "butterfly-network",
    # Digital pathology / histology AI.
    "pathologywatch",
    "ibex-medical-analytics",
    "deepcell",
    "aignostics",
    "diagnostic-robotics",
    # Radiology / imaging AI for diagnosis.
    "icad",
    "annaliseai",
    "blackford-analysis",
    "brainomix",
    "sirona-medical",
    "rad-ai",
    "docbot",
    # Cardiac diagnostics.
    "cardiologs",
    "eko-health",
    "biointellisense",
    # Genomics / molecular diagnostics adjacent.
    "beacon-biosignals",
    "whiterabbit",
}

MANUAL_REVIEW_EXTRA = [
    {
        "display_name": "Foundation Medicine",
        "category": "Diagnostics",
        "reason": "Ambiguous slug match on ashby/foundation (not Foundation Medicine)",
        "slug_candidates": "foundationmedicine, foundation",
    },
    {
        "display_name": "Ezra",
        "category": "Diagnostics",
        "reason": "Ambiguous slug match on greenhouse/ezra (not Ezra screening)",
        "slug_candidates": "ezra, ezrahealth",
    },
    {
        "display_name": "Sonic Healthcare",
        "category": "Diagnostics",
        "reason": "Ambiguous slug match on greenhouse/sonic",
        "slug_candidates": "sonic, sonichealthcare",
    },
    {
        "display_name": "Quest Diagnostics",
        "category": "Diagnostics",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "questdiagnostics, quest",
    },
    {
        "display_name": "Labcorp",
        "category": "Diagnostics",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "labcorp",
    },
    {
        "display_name": "Arterys",
        "category": "Diagnostics",
        "reason": "No supported ATS board found; acquired by Bayer, careers portal may be defunct",
        "slug_candidates": "arterys",
    },
    {
        "display_name": "Illumina",
        "category": "Diagnostics",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "illumina",
    },
    {
        "display_name": "Myriad Genetics",
        "category": "Diagnostics",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "myriad, myriadgenetics",
    },
    {
        "display_name": "Caris Life Sciences",
        "category": "Diagnostics",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "caris, carislifesciences",
    },
    {
        "display_name": "Gestalt Diagnostics",
        "category": "Diagnostics",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "gestalt, gestaltdiagnostics",
    },
    {
        "display_name": "Digital Diagnostics",
        "category": "Diagnostics",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "digitaldiagnostics",
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
    for group in by_id.values():
        result.append(group[0])
    return result


def main() -> None:
    rows = load_rows()
    existing_ats_slug = {(r["ats"].casefold(), r["slug"]) for r in rows}
    existing_ids = {r["company_id"] for r in rows}

    verified = json.loads(VERIFIED_PATH.read_text(encoding="utf-8"))
    skipped = json.loads(SKIPPED_PATH.read_text(encoding="utf-8"))

    added = 0
    added_names: list[str] = []
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
        added_names.append(entry["display_name"])

    recategorized = 0
    recategorized_names: list[str] = []
    for row in rows:
        if row["company_id"] in RECATEGORIZE_TO_DIAGNOSTICS and row["category"] != "Diagnostics":
            recategorized_names.append(f"{row['display_name']} ({row['category']} -> Diagnostics)")
            row["category"] = "Diagnostics"
            recategorized += 1

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
                "category": "Diagnostics",
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

    diagnostics_count = sum(1 for r in rows if r["category"] == "Diagnostics")
    print(f"Added {added} companies, recategorized {recategorized}, deduped {deduped}")
    print(f"Diagnostics total: {diagnostics_count}, registry total: {len(rows)}")
    print(f"Manual review queue: {len(manual_rows)} entries")
    if added_names:
        print("Added:", ", ".join(added_names))
    if recategorized_names:
        print("Recategorized:", ", ".join(recategorized_names))


if __name__ == "__main__":
    main()
