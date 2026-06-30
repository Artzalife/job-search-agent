#!/usr/bin/env python3
"""Apply Clinical AI expansion to data/companies.csv."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "companies.csv"
VERIFIED_PATH = ROOT / "data" / "_clinical_ai_verified.json"
SKIPPED_PATH = ROOT / "data" / "_clinical_ai_skipped.json"
MANUAL_REVIEW_PATH = ROOT / "data" / "manual_review_queue.csv"

# Ambiguous slug matches excluded despite API probe success.
EXCLUDE_ATS_SLUG = {
    ("workable", "celsius"),
    ("workable", "fabric"),
    ("lever", "color"),
    ("workable", "tandem"),
    ("workable", "roam"),
    ("workable", "volo"),
    ("workable", "sophia"),
    ("workable", "harrison"),
    ("workable", "myriad"),
    ("workable", "turbine"),
    ("greenhouse", "paradigm"),
    ("workable", "syllable"),
    ("workable", "avo"),
    ("workable", "babylon"),
}

# Additional verified companies from follow-up probes (not in batch JSON).
EXTRA_VERIFIED = [
    {
        "company_id": "quanthealth",
        "category": "Clinical AI",
        "display_name": "QuantHealth",
        "ats": "greenhouse",
        "slug": "quanthealth",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
    {
        "company_id": "valohealth",
        "category": "Clinical AI",
        "display_name": "Valo Health",
        "ats": "greenhouse",
        "slug": "valohealth",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
    {
        "company_id": "synapticure",
        "category": "Clinical AI",
        "display_name": "Synapticure",
        "ats": "lever",
        "slug": "synapticure",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
    {
        "company_id": "whiterabbit",
        "category": "Clinical AI",
        "display_name": "White Rabbit AI",
        "ats": "lever",
        "slug": "whiterabbit",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
    {
        "company_id": "deepcell",
        "category": "Clinical AI",
        "display_name": "Deepcell",
        "ats": "workable",
        "slug": "deepcell",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
    {
        "company_id": "biointellisense",
        "category": "Clinical AI",
        "display_name": "BioIntelliSense",
        "ats": "lever",
        "slug": "biointellisense",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
    {
        "company_id": "adahealth",
        "category": "Clinical AI",
        "display_name": "Ada Health",
        "ats": "greenhouse",
        "slug": "adahealth",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
    {
        "company_id": "heartbeathealth",
        "category": "Clinical AI",
        "display_name": "Heartbeat Health",
        "ats": "lever",
        "slug": "heartbeathealth",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
    {
        "company_id": "butlr",
        "category": "Clinical AI",
        "display_name": "Butlr",
        "ats": "greenhouse",
        "slug": "butlr",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
    {
        "company_id": "scribe",
        "category": "Clinical AI",
        "display_name": "Scribe",
        "ats": "ashby",
        "slug": "scribe",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
    {
        "company_id": "aignostics",
        "category": "Clinical AI",
        "display_name": "Aignostics",
        "ats": "workable",
        "slug": "aignostics",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
    {
        "company_id": "augmedix",
        "category": "Clinical AI",
        "display_name": "Augmedix",
        "ats": "workable",
        "slug": "augmedix",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
    {
        "company_id": "pathologywatch",
        "category": "Clinical AI",
        "display_name": "PathologyWatch",
        "ats": "workable",
        "slug": "pathologywatch",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
    {
        "company_id": "olive-ai",
        "category": "Clinical AI",
        "display_name": "Olive AI",
        "ats": "ashby",
        "slug": "olive",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
    {
        "company_id": "cleerly",
        "category": "Clinical AI",
        "display_name": "Cleerly",
        "ats": "greenhouse",
        "slug": "cleerlyhealth",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
    {
        "company_id": "lumahealth",
        "category": "Clinical AI",
        "display_name": "Luma Health",
        "ats": "greenhouse",
        "slug": "lumahealth",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
    {
        "company_id": "lumos",
        "category": "Clinical AI",
        "display_name": "Lumos",
        "ats": "ashby",
        "slug": "lumos",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
    {
        "company_id": "concertai",
        "category": "Clinical AI",
        "display_name": "ConcertAI",
        "ats": "workable",
        "slug": "concertai",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
    {
        "company_id": "innovaccer",
        "category": "Clinical AI",
        "display_name": "Innovaccer",
        "ats": "workable",
        "slug": "innovaccer",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
    {
        "company_id": "healthtensor",
        "category": "Clinical AI",
        "display_name": "HealthTensor",
        "ats": "workable",
        "slug": "healthtensor",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
    {
        "company_id": "healthify",
        "category": "Clinical AI",
        "display_name": "Healthify",
        "ats": "workable",
        "slug": "healthify",
        "enabled": "yes",
        "notes": "",
        "wd_server": "",
        "workday_site": "",
    },
]

RECATEGORIZE_TO_CLINICAL_AI = {
    "smarterdx",
    "tempus",
    "iterative-health",
}

MANUAL_REVIEW_EXTRA = [
    {
        "display_name": "Hippocratic AI",
        "category": "Clinical AI",
        "reason": "No supported ATS board found; likely custom or unsupported ATS",
        "slug_candidates": "hippocraticai, hippocratic",
    },
    {
        "display_name": "DeepScribe",
        "category": "Clinical AI",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "deepscribe",
    },
    {
        "display_name": "Glass Health",
        "category": "Clinical AI",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "glasshealth, glasshealthinc",
    },
    {
        "display_name": "Viz.ai",
        "category": "Clinical AI",
        "reason": "No supported ATS board found; may use Workday or custom portal",
        "slug_candidates": "vizai, viz, vizdotai",
    },
    {
        "display_name": "Paige",
        "category": "Clinical AI",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "paige, paigeai",
    },
    {
        "display_name": "Proscia",
        "category": "Clinical AI",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "proscia",
    },
    {
        "display_name": "Qure.ai",
        "category": "Clinical AI",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "qureai, qure",
    },
    {
        "display_name": "Kheiron Medical",
        "category": "Clinical AI",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "kheiron, kheironmedical",
    },
    {
        "display_name": "Enlitic",
        "category": "Clinical AI",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "enlitic, enliticinc",
    },
    {
        "display_name": "Riverain Technologies",
        "category": "Clinical AI",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "riverain, riveraintech",
    },
    {
        "display_name": "Subtle Medical",
        "category": "Clinical AI",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "subtlemedical",
    },
    {
        "display_name": "Quibim",
        "category": "Clinical AI",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "quibim, quibimmedical",
    },
    {
        "display_name": "Caption Health",
        "category": "Clinical AI",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "captionhealth, caption",
    },
    {
        "display_name": "Presagen",
        "category": "Clinical AI",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "presagen, presagenhealth",
    },
    {
        "display_name": "Nucleai",
        "category": "Clinical AI",
        "reason": "No supported ATS board found via API probe",
        "slug_candidates": "nucleai, nucleaihealth",
    },
    {
        "display_name": "Celsius Health",
        "category": "Clinical AI",
        "reason": "Ambiguous slug match (workable/celsius likely Celsius Network, not healthcare)",
        "slug_candidates": "celsius",
    },
    {
        "display_name": "Fabric Health",
        "category": "Clinical AI",
        "reason": "Ambiguous slug match on workable/fabric",
        "slug_candidates": "fabric, fabrichealth",
    },
    {
        "display_name": "Color Health",
        "category": "Clinical AI",
        "reason": "Ambiguous slug match on lever/color",
        "slug_candidates": "color, colorhealth",
    },
    {
        "display_name": "Tandem Health",
        "category": "Clinical AI",
        "reason": "Ambiguous slug match on workable/tandem",
        "slug_candidates": "tandem, tandemhealth",
    },
    {
        "display_name": "Roam Analytics",
        "category": "Clinical AI",
        "reason": "Ambiguous slug match on workable/roam",
        "slug_candidates": "roam, roamanalytics",
    },
    {
        "display_name": "Volocare",
        "category": "Clinical AI",
        "reason": "Ambiguous slug match on workable/volo",
        "slug_candidates": "volo, volocare",
    },
    {
        "display_name": "Sophia Genetics",
        "category": "Clinical AI",
        "reason": "Ambiguous slug match on workable/sophia",
        "slug_candidates": "sophiagenetics, sophia",
    },
    {
        "display_name": "Harrison.ai",
        "category": "Clinical AI",
        "reason": "Ambiguous slug match on workable/harrison",
        "slug_candidates": "harrison, harrisonai",
    },
    {
        "display_name": "Myriad Genetics",
        "category": "Clinical AI",
        "reason": "Ambiguous slug match on workable/myriad",
        "slug_candidates": "myriad, myriadgenetics",
    },
    {
        "display_name": "Paradigm Health",
        "category": "Clinical AI",
        "reason": "Ambiguous slug match on greenhouse/paradigm",
        "slug_candidates": "paradigm, paradigmhealth",
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


def load_rows() -> list[dict[str, str]]:
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def row_to_csv(row: dict[str, str]) -> dict[str, str]:
    return {field: row.get(field, "") for field in FIELDNAMES}


def main() -> None:
    rows = load_rows()
    existing_ats_slug = {(r["ats"].casefold(), r["slug"]) for r in rows}
    existing_ids = {r["company_id"] for r in rows}

    verified = json.loads(VERIFIED_PATH.read_text(encoding="utf-8"))
    skipped = json.loads(SKIPPED_PATH.read_text(encoding="utf-8"))

    added = 0
    for entry in verified + EXTRA_VERIFIED:
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
        if row["company_id"] in RECATEGORIZE_TO_CLINICAL_AI and row["category"] != "Clinical AI":
            row["category"] = "Clinical AI"
            recategorized += 1

    rows.sort(key=lambda r: (r["category"], r["display_name"].casefold()))

    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    manual_rows = []
    for item in skipped:
        manual_rows.append(
            {
                "display_name": item["display_name"],
                "category": "Clinical AI",
                "reason": item["reason"],
                "slug_candidates": item["slug_candidates"],
            }
        )
    for item in MANUAL_REVIEW_EXTRA:
        manual_rows.append(item)

    with MANUAL_REVIEW_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["display_name", "category", "reason", "slug_candidates"],
        )
        writer.writeheader()
        writer.writerows(manual_rows)

    clinical_ai_count = sum(1 for r in rows if r["category"] == "Clinical AI")
    print(f"Added {added} companies, recategorized {recategorized}, Clinical AI total: {clinical_ai_count}")
    print(f"Manual review queue: {len(manual_rows)} entries -> {MANUAL_REVIEW_PATH}")


if __name__ == "__main__":
    main()
