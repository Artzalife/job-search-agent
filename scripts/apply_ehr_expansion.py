#!/usr/bin/env python3
"""Apply EHR & Clinical Workflow expansion to data/companies.csv."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "companies.csv"
VERIFIED_PATH = ROOT / "data" / "_ehr_verified.json"
SKIPPED_PATH = ROOT / "data" / "_ehr_skipped.json"
MANUAL_REVIEW_PATH = ROOT / "data" / "manual_review_queue.csv"

# Ambiguous slug matches excluded despite API probe success.
EXCLUDE_ATS_SLUG = {
    ("workable", "greenway"),
    ("workable", "benchmark"),
    ("workable", "enable"),
    ("workable", "dock"),
    ("workable", "bridge"),
    ("workable", "regal"),
    ("workable", "bamboo"),
    ("workable", "olive"),
    ("workable", "hinge"),
    ("greenhouse", "dispatch"),
    ("lever", "blinq"),
    ("ashby", "change"),
    ("workday", "ibm"),
    ("workday", "philips"),
    ("workday", "stryker"),
    ("workday", "epic"),
    ("greenhouse", "epic"),
    ("workable", "oracle"),
    ("workable", "nuance"),
    ("greenhouse", "acumen"),
    ("greenhouse", "praxis"),
    ("greenhouse", "credible"),
    ("ashby", "paragon"),
    ("workable", "epic"),
    ("lever", "enable"),
}

RECATEGORIZE_TO_EHR = {
    # Practice management / ambulatory EHR — miscategorized under Revenue Cycle.
    "advancedmd",
    "athenahealth",
    "carecloud",
    "curemd",
    "eclinicalworks",
    "elation-health",
    "hint-health",
    "nextgen-healthcare",
    "rxnt",
    "simplepractice",
    "tebra",
    "office-ally",
    "hst-pathways",
    # Clinical documentation / workflow platforms.
    "canvas-medical",
    "ambience-healthcare",
    "abridge",
    "suki",
    "freed",
    "nabla",
    "augmedix",
    "regard",
    "scribe",
    "artera",
    "corti",
    "eleos-health",
    # Clinical communication & care workflow.
    "perfectserve",
    "spok",
    "memora-health",
    "lumahealth",
    "docasap",
    "florence-healthcare",
    "synapticure",
    "heartbeathealth",
    "qgenda",
    "notable-health",
}

MANUAL_REVIEW_EXTRA = [
    {
        "display_name": "Epic",
        "category": "EHR",
        "reason": "No supported ATS board found; custom careers portal (careers.epic.com)",
        "slug_candidates": "epic, epicsystems",
    },
    {
        "display_name": "Oracle Health",
        "category": "EHR",
        "reason": "No supported ATS board found; likely Oracle/corporate careers portal",
        "slug_candidates": "cerner, oraclehealth, oracle",
    },
    {
        "display_name": "MEDITECH",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "meditech/MEDITECH",
    },
    {
        "display_name": "ModMed",
        "category": "EHR",
        "reason": "No supported ATS board found; likely custom careers portal",
        "slug_candidates": "modmed, modernizingmedicine",
    },
    {
        "display_name": "Veradigm",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "veradigm, allscripts",
    },
    {
        "display_name": "Altera Digital Health",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "altera, alteradigitalhealth",
    },
    {
        "display_name": "DrChrono",
        "category": "EHR",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "drchrono",
    },
    {
        "display_name": "Practice Fusion",
        "category": "EHR",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "practicefusion",
    },
    {
        "display_name": "Greenway Health",
        "category": "EHR",
        "reason": "Ambiguous slug match on workable/greenway",
        "slug_candidates": "greenway, greenwayhealth",
    },
    {
        "display_name": "Amazing Charts",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "amazingcharts",
    },
    {
        "display_name": "ChartLogic",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "chartlogic",
    },
    {
        "display_name": "Experity",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "experity",
    },
    {
        "display_name": "Practice EHR",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "practiceehr",
    },
    {
        "display_name": "NueMD",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "nuemd",
    },
    {
        "display_name": "PracticeSuite",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "practicesuite",
    },
    {
        "display_name": "PrognoCIS",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "prognocis",
    },
    {
        "display_name": "Benchmark Systems",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "benchmarksystems, benchmark",
    },
    {
        "display_name": "Meditab",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "meditab",
    },
    {
        "display_name": "Azalea Health",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "azaleahealth, azalea",
    },
    {
        "display_name": "Praxis EMR",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "praxisemr, praxis",
    },
    {
        "display_name": "MDLand",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "mdland",
    },
    {
        "display_name": "Compulink Healthcare Solutions",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "compulink",
    },
    {
        "display_name": "Hello Health",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "hellohealth",
    },
    {
        "display_name": "Enable Healthcare",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "enablehealthcare, enable",
    },
    {
        "display_name": "DocVilla",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "docvilla",
    },
    {
        "display_name": "Healthie",
        "category": "EHR",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "healthie, gethealthie",
    },
    {
        "display_name": "Qualifacts",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "qualifacts",
    },
    {
        "display_name": "Credible Behavioral Health",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "crediblebh, crediblebehavioral",
    },
    {
        "display_name": "TherapyNotes",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "therapynotes",
    },
    {
        "display_name": "Carepatron",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "carepatron",
    },
    {
        "display_name": "Intelerad",
        "category": "EHR",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "intelerad",
    },
    {
        "display_name": "Sectra",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "sectra",
    },
    {
        "display_name": "Merge Healthcare",
        "category": "EHR",
        "reason": "No Workday board found; IBM corporate careers portal",
        "slug_candidates": "mergehealthcare, ibm",
    },
    {
        "display_name": "Agfa HealthCare",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "agfa, agfahealthcare",
    },
    {
        "display_name": "Philips Healthcare Informatics",
        "category": "EHR",
        "reason": "No Workday board found; Philips corporate portal",
        "slug_candidates": "philips, philipshealthcare",
    },
    {
        "display_name": "InterSystems TrakCare",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "intersystems/InterSystems_Careers",
    },
    {
        "display_name": "MEDHOST",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "medhost",
    },
    {
        "display_name": "CGM (CompuGroup Medical)",
        "category": "EHR",
        "reason": "No Workday board found via API probe",
        "slug_candidates": "cgm/CGM",
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
        if row["company_id"] in RECATEGORIZE_TO_EHR and row["category"] != "EHR":
            recategorized_names.append(row["display_name"])
            row["category"] = "EHR"
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
                "category": "EHR",
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

    ehr_count = sum(1 for r in rows if r["category"] == "EHR")
    ats_dist: dict[str, int] = {}
    for r in rows:
        if r["category"] == "EHR":
            ats_dist[r["ats"]] = ats_dist.get(r["ats"], 0) + 1

    print(f"Added {added} companies, recategorized {recategorized}, EHR total: {ehr_count}")
    print(f"ATS distribution: {ats_dist}")
    print(f"Manual review queue: {len(manual_rows)} entries -> {MANUAL_REVIEW_PATH}")

    summary_path = ROOT / "data" / "_ehr_expansion_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "added": added_names,
                "recategorized": recategorized_names,
                "ehr_total": ehr_count,
                "registry_total": len(rows),
                "ats_distribution": ats_dist,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
