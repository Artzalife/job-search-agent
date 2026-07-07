#!/usr/bin/env python3
"""Apply Population Health expansion to data/companies.csv."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "companies.csv"
VERIFIED_PATH = ROOT / "data" / "_population_health_verified.json"
SKIPPED_PATH = ROOT / "data" / "_population_health_skipped.json"
MANUAL_REVIEW_PATH = ROOT / "data" / "manual_review_queue.csv"

# Ambiguous slug matches excluded despite API probe success.
EXCLUDE_ATS_SLUG = {
    ("workable", "hinge"),
    ("greenhouse", "dispatch"),
    ("workable", "landmark"),
    ("workable", "ribbon"),
    ("ashby", "change"),
    ("workable", "claim"),
    ("workable", "pearl"),
    ("greenhouse", "guide"),
    ("greenhouse", "equality"),
    ("lever", "thyme"),
    ("greenhouse", "concerto"),
    ("greenhouse", "milliman"),
    ("greenhouse", "rti"),
    ("greenhouse", "cognizant"),
}

RECATEGORIZE_TO_POPULATION_HEALTH = {
    # Seed companies already in registry under other categories.
    "innovaccer",
    "clarify-health",
    "komodo-health",
    "aledade",
    "cityblock-health",
    "cotiviti",
    "closedloop-ai",
    "medeanalytics",
    "signify-health",
    "homeward",
    "unite-us",
    "omada-health",
    "strive-health",
    "cohere-health",
    "healthverity",
    "inovalon",
    "macrohealth",
    "villagemd",
    "covera-health",
    "garner-health",
    # Care management / chronic disease at population scale.
    "lark-health",
    "vida-health",
    "healthsnap",
    "findhelp",
    "curative",
    "oshi-health",
    # Employer population health / care navigation.
    "collective-health",
    "transcarent",
    "included-health",
    "rightway-healthcare",
    "healthjoy",
    # Value-based programs and population data infrastructure.
    "sword-health",
    "virta-health",
    "pomelo-care",
    "waymark",
    "particle-health",
    "zus-health",
    "truveta",
    "nomi-health",
    "biofourmis",
    "boulder-care",
    "tomorrow-health",
    "glooko",
    "steadymd",
    "redox",
    "metriport",
    "health-gorilla",
    "k-health",
    "galileo",
    "flatiron-health",
    "courier-health",
}

MANUAL_REVIEW_EXTRA = [
    {
        "display_name": "Health Catalyst",
        "category": "Population Health",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "healthcatalyst",
    },
    {
        "display_name": "Cedar Gate Technologies",
        "category": "Population Health",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "cedargate",
    },
    {
        "display_name": "Lightbeam Health Solutions",
        "category": "Population Health",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "lightbeam, lightbeamhealth",
    },
    {
        "display_name": "Bamboo Health",
        "category": "Population Health",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "bamboohealth, bamboo",
    },
    {
        "display_name": "Datavant",
        "category": "Population Health",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "datavant",
    },
    {
        "display_name": "Evolent Health",
        "category": "Population Health",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "evolent, evolenthealth",
    },
    {
        "display_name": "Privia Health",
        "category": "Population Health",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "privia, priviahealth",
    },
    {
        "display_name": "Guidehealth",
        "category": "Population Health",
        "reason": "Ambiguous slug match on workable/guide (unverified company name)",
        "slug_candidates": "guidehealth, guide",
    },
    {
        "display_name": "Equality Health",
        "category": "Population Health",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "equalityhealth, equality",
    },
    {
        "display_name": "Thyme Care",
        "category": "Population Health",
        "reason": "Ambiguous slug match on workable/thyme (unverified company name)",
        "slug_candidates": "thymecare, thyme",
    },
    {
        "display_name": "Somatus",
        "category": "Population Health",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "somatus",
    },
    {
        "display_name": "Emcara Health",
        "category": "Population Health",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "emcara, emcarahealth",
    },
    {
        "display_name": "HealthEC",
        "category": "Population Health",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "healthec, healthecinc",
    },
    {
        "display_name": "Innovista Health",
        "category": "Population Health",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "innovista, innovistahealth",
    },
    {
        "display_name": "Vytalize Health",
        "category": "Population Health",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "vytalize, vytalizehealth",
    },
    {
        "display_name": "Agilon Health",
        "category": "Population Health",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "agilon, agilonhealth",
    },
    {
        "display_name": "Oak Street Health",
        "category": "Population Health",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "oakstreethealth, oakstreet",
    },
    {
        "display_name": "Iora Health",
        "category": "Population Health",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "iorahealth, iora",
    },
    {
        "display_name": "Cano Health",
        "category": "Population Health",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "canohealth, cano",
    },
    {
        "display_name": "Devoted Health",
        "category": "Population Health",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "devotedhealth, devoted",
    },
    {
        "display_name": "Bright Health Group",
        "category": "Population Health",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "brighthealth, brighthealthgroup",
    },
    {
        "display_name": "DispatchHealth",
        "category": "Population Health",
        "reason": "Ambiguous slug match on greenhouse/dispatch (unverified company name)",
        "slug_candidates": "dispatch, dispatchhealth",
    },
    {
        "display_name": "Hinge Health",
        "category": "Population Health",
        "reason": "Ambiguous slug match on workable/hinge (likely Hinge dating app)",
        "slug_candidates": "hinge, hingehealth",
    },
    {
        "display_name": "Landmark Health",
        "category": "Population Health",
        "reason": "Ambiguous slug match on workable/landmark",
        "slug_candidates": "landmark, landmarkhealth",
    },
    {
        "display_name": "Ribbon Health",
        "category": "Population Health",
        "reason": "Ambiguous slug match on workable/ribbon",
        "slug_candidates": "ribbon, ribbonhealth",
    },
    {
        "display_name": "Change Healthcare",
        "category": "Population Health",
        "reason": "Ambiguous slug match on ashby/change (likely Change.org)",
        "slug_candidates": "change, changehealthcare",
    },
    {
        "display_name": "Premise Health",
        "category": "Population Health",
        "reason": "Ambiguous slug match on workable/premise (Premise Data Corporation)",
        "slug_candidates": "premisehealth, premise",
    },
    {
        "display_name": "ChenMed",
        "category": "Population Health",
        "reason": "Workable board found with 0 jobs; careers portal unverified",
        "slug_candidates": "chenmed",
    },
    {
        "display_name": "Alignment Healthcare",
        "category": "Population Health",
        "reason": "Ambiguous slug match on workable/alignment",
        "slug_candidates": "alignmenthealthcare, alignment",
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


def main() -> None:
    rows = load_rows()
    existing_ats_slug = {(r["ats"].casefold(), r["slug"]) for r in rows}
    existing_ids = {r["company_id"] for r in rows}

    verified = json.loads(VERIFIED_PATH.read_text(encoding="utf-8"))
    skipped = json.loads(SKIPPED_PATH.read_text(encoding="utf-8"))

    added = 0
    added_entries: list[dict] = []
    for entry in verified:
        key = (entry["ats"].casefold(), entry["slug"])
        if key in EXCLUDE_ATS_SLUG:
            continue
        if key in existing_ats_slug or entry["company_id"] in existing_ids:
            continue
        rows.append(row_to_csv(entry))
        existing_ats_slug.add(key)
        existing_ids.add(entry["company_id"])
        added_entries.append(entry)
        added += 1

    recategorized = 0
    recategorized_names: list[str] = []
    for row in rows:
        if row["company_id"] in RECATEGORIZE_TO_POPULATION_HEALTH and row["category"] != "Population Health":
            recategorized_names.append(row["display_name"])
            row["category"] = "Population Health"
            recategorized += 1

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
                "category": "Population Health",
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

    population_health_count = sum(1 for r in rows if r["category"] == "Population Health")
    ats_dist: dict[str, int] = {}
    for entry in added_entries:
        ats_dist[entry["ats"]] = ats_dist.get(entry["ats"], 0) + 1

    print(f"Added {added} companies, recategorized {recategorized}, Population Health total: {population_health_count}")
    print(f"Registry total: {len(rows)}")
    print(f"Manual review queue: {len(manual_rows)} entries -> {MANUAL_REVIEW_PATH}")
    if added_entries:
        print("ATS distribution (newly added):")
        for ats, count in sorted(ats_dist.items()):
            print(f"  {ats}: {count}")
    if recategorized_names:
        print("Recategorized:", ", ".join(sorted(recategorized_names)))


if __name__ == "__main__":
    main()
