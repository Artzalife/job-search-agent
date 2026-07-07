#!/usr/bin/env python3
"""Batch-probe Diagnostics candidate slugs across supported ATS APIs."""

from __future__ import annotations

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
    WORKABLE_API_BASE,
    load_companies,
)

HEADERS = {"Accept": "application/json", "User-Agent": "job-search-agent/1.0"}

# (display_name, slug_candidates) — first matching slug wins per ATS
CANDIDATES: list[tuple[str, list[str]]] = [
    # Seed companies not yet in registry
    ("Foundation Medicine", ["foundationmedicine", "foundation"]),
    ("Biodesix", ["biodesix"]),
    ("Paige", ["paige", "paigeai"]),
    ("Proscia", ["proscia"]),
    ("Quibim", ["quibim"]),
    ("Prenuvo", ["prenuvo"]),
    ("Viz.ai", ["vizai", "viz"]),
    ("Arterys", ["arterys"]),
    ("Karius", ["karius"]),
    ("Genomenon", ["genomenon"]),
    ("Lucence", ["lucence", "lucencehealth"]),
    # Genomics / molecular diagnostics
    ("Myriad Genetics", ["myriad", "myriadgenetics"]),
    ("NeoGenomics", ["neogenomics", "neo"]),
    ("Fulgent Genetics", ["fulgent", "fulgentgenetics"]),
    ("Sema4", ["sema4"]),
    ("Helix", ["helix", "helixopco"]),
    ("Caris Life Sciences", ["caris", "carislifesciences"]),
    ("Invitae", ["invitae"]),
    ("GeneDx", ["genedx"]),
    ("Color Health", ["color", "colorhealth"]),
    ("Fabric Genomics", ["fabricgenomics", "fabric"]),
    ("PacBio", ["pacbio", "pacificbiosciences"]),
    ("Oxford Nanopore", ["nanopore", "oxfordnanopore"]),
    ("Akoya Biosciences", ["akoya", "akoyabio"]),
    ("Standard BioTools", ["standardbio", "fluidigm"]),
    ("Singular Genomics", ["singulargenomics", "singular"]),
    ("Mission Bio", ["missionbio"]),
    ("Strata Oncology", ["strataoncology", "strata"]),
    ("Burning Rock DX", ["burningrock", "brbiotech"]),
    ("Predicine", ["predicine"]),
    ("Foresight Diagnostics", ["foresightdx", "foresight"]),
    ("Thrive Earlier Detection", ["thrive", "thriveearlierdetection"]),
    ("Resolution Bioscience", ["resolutionbio", "resolutionbioscience"]),
    ("C2i Genomics", ["c2i", "c2igenomics"]),
    ("Inivata", ["inivata"]),
    ("Delfi Diagnostics", ["delfi", "delfidiagnostics"]),
    ("Freenome", ["freenome"]),
    # Digital pathology / histology
    ("Gestalt Diagnostics", ["gestalt", "gestaltdiagnostics"]),
    ("Digital Diagnostics", ["digitaldiagnostics"]),
    ("Inspirata", ["inspirata"]),
    ("Proscia", ["proscia"]),
    ("Paige", ["paigeai", "paige"]),
    ("Deep Bio", ["deepbio"]),
    ("OptraSCAN", ["optrascan"]),
    ("Visiopharm", ["visiopharm"]),
    # Radiology / imaging AI
    ("Qure.ai", ["qureai", "qure"]),
    ("Zebra Medical Vision", ["zebra-med", "zebramed"]),
    ("Riverain Technologies", ["riverain", "riveraintech"]),
    ("CureMetrix", ["curemetrix"]),
    ("ScreenPoint Medical", ["screenpoint", "screenpointmedical"]),
    ("Intelerad", ["intelerad"]),
    ("Nanox", ["nanox", "nanoximaging"]),
    ("Subtle Medical", ["subtlemedical", "subtle"]),
    ("Imagen Technologies", ["imagen", "imagtechnologies"]),
    ("Whiterabbit.ai", ["whiterabbit", "whiterabbitai"]),
    ("RetinAI Medical", ["retinai", "retinaimedical"]),
    ("Oxipit", ["oxipit"]),
    ("Avicenna.AI", ["avicenna", "avicennaai"]),
    ("Aidence", ["aidence"]),
    ("Kheiron Medical", ["kheiron", "kheironmedical"]),
    ("DeepHealth", ["deephealth"]),
    # Cardiac / vascular diagnostics
    ("Elucid Bioimaging", ["elucid", "elucidbioimaging"]),
    ("Caption Health", ["captionhealth", "caption"]),
    ("Us2.ai", ["us2ai", "us2"]),
    ("HeartSciences", ["heartsciences"]),
    # Infectious disease / microbiology
    ("T2 Biosystems", ["t2biosystems", "t2"]),
    ("Day Zero Diagnostics", ["dayzerodiagnostics", "dayzero"]),
    ("Visby Medical", ["visbymedical", "visby"]),
    ("Sight Diagnostics", ["sightdx", "sightdiagnostics"]),
    ("Cue Health", ["cuehealth", "cue"]),
    ("Karius", ["karius"]),
    ("Specific Diagnostics", ["specificdx", "specificdiagnostics"]),
    # Women's / reproductive diagnostics
    ("NxGen MDx", ["nxgen", "nxgenmdx"]),
    ("Natera", ["natera"]),
    ("Progyny", ["progyny"]),
    ("Kindbody", ["kindbody"]),
    ("Ovia Health", ["ovia", "oviahealth"]),
    # Screening / consumer diagnostics
    ("Ezra", ["ezra", "ezrahealth"]),
    ("Function Health", ["functionhealth", "function"]),
    ("InsideTracker", ["insidetracker"]),
    ("Everlywell", ["everlywell"]),
    ("LetsGetChecked", ["letsgetchecked"]),
    ("Thorne", ["thorne", "thornhealth"]),
    # Lab services / reference labs
    ("BioReference Laboratories", ["bioreference", "bioref"]),
    ("Labcorp", ["labcorp"]),
    ("Quest Diagnostics", ["questdiagnostics", "quest"]),
    ("Psomagen", ["psomagen"]),
    ("PreventionGenetics", ["preventiongenetics"]),
    ("Ambry Genetics", ["ambry", "ambrygenetics"]),
    ("Invitae", ["invitae"]),
    # Oncology tissue / liquid biopsy
    ("Biodesix", ["biodesix"]),
    ("Personalis", ["personalisinc", "personalis"]),
    ("Tempus", ["tempus"]),
    ("Flatiron Health", ["flatironhealth", "flatiron"]),
    # Genomics interpretation / knowledge bases
    ("Genomenon", ["genomenon"]),
    ("FDNA", ["fdna"]),
    ("N-of-One", ["nofone", "n-of-one"]),
    # Point-of-care / device diagnostics
    ("Butterfly Network", ["butterflynetwork", "butterfly"]),
    ("Huma", ["huma", "humatherapeutics"]),
    ("Current Health", ["current", "currenthealth"]),
    ("NeuroPace", ["neuropace"]),
    ("Dexcom", ["dexcom"]),
    # Allergy / autoimmune / specialty
    ("Thermo Fisher Scientific", ["thermofisher", "thermo"]),
    ("Eurofins", ["eurofins"]),
    ("Sonic Healthcare", ["sonichealthcare", "sonic"]),
    # Clinical lab software adjacent (diagnostic workflow)
    ("Sunquest Information Systems", ["sunquest"]),
    ("XIFIN", ["xifin"]),
    # Additional imaging / AI diagnostics
    ("Lunit", ["lunit"]),
    ("PathAI", ["pathai"]),
    ("Aidoc", ["aidocmedical", "aidoc"]),
    ("RapidAI", ["rapidai"]),
    ("Cleerly", ["cleerlyhealth", "cleerly"]),
    ("HeartFlow", ["heartflowinc", "heartflow"]),
]

# Known Workday boards: (display_name, tenant, wd_server, workday_site)
WORKDAY_CANDIDATES: list[tuple[str, str, str, str]] = [
    ("Foundation Medicine", "foundationmedicine", "wd1", "FoundationMedicine"),
    ("Myriad Genetics", "myriad", "wd5", "Myriad"),
    ("NeoGenomics", "neogenomics", "wd1", "NeoGenomics"),
    ("Quest Diagnostics", "questdiagnostics", "wd1", "QuestDiagnostics"),
    ("Labcorp", "labcorp", "wd1", "External"),
    ("Illumina", "illumina", "wd1", "Illumina"),
    ("Hologic", "hologic", "wd1", "Hologic"),
    ("BD", "bd", "wd1", "BD"),
    ("Agilent", "agilent", "wd5", "Agilent"),
    ("Thermo Fisher Scientific", "thermofisher", "wd5", "ThermoFisherScientific"),
    ("BioReference Laboratories", "bioreference", "wd1", "BioReference"),
    ("Invitae", "invitae", "wd5", "Invitae"),
    ("Tempus", "tempus", "wd5", "Tempus_Careers"),
    ("Exact Sciences", "exactsciences", "wd1", "Exact_Sciences"),
    ("Guardant Health", "gh", "wd1", "gh"),
    ("Caris Life Sciences", "caris", "wd1", "Caris"),
    ("Fulgent Genetics", "fulgent", "wd1", "Fulgent"),
    ("Sema4", "sema4", "wd1", "Sema4"),
    ("PacBio", "pacbio", "wd1", "PacBio"),
    ("Oxford Nanopore", "nanopore", "wd3", "OxfordNanoporeCareers"),
    ("Dexcom", "dexcom", "wd1", "Dexcom"),
    ("Cue Health", "cuehealth", "wd1", "CueHealth"),
]


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


def probe(url: str, timeout: int = 10, method: str = "GET", body: bytes | None = None) -> tuple[bool, int]:
    try:
        headers = dict(HEADERS)
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read())
        if "jobs" in data:
            total = data.get("total", len(data["jobs"]))
            return True, int(total) if isinstance(total, int) else len(data["jobs"])
        if isinstance(data, list):
            return True, len(data)
        return True, 0
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
        return False, 0


def find_ats(slug: str, existing: dict[str, set[str]]) -> tuple[str, str, int] | None:
    probes = [
        ("greenhouse", f"{GREENHOUSE_API_BASE}/{slug}/jobs"),
        ("lever", f"{LEVER_API_BASE}/{slug}?mode=json"),
        ("ashby", f"{ASHBY_API_BASE}/{slug}"),
        ("workable", f"{WORKABLE_API_BASE}/{slug}?details=true"),
    ]
    for ats, url in probes:
        if slug in existing[ats]:
            continue
        ok, count = probe(url, timeout=8 if ats == "lever" else 10)
        if ok:
            return ats, slug, count
        time.sleep(0.15)
    return None


def probe_workday(tenant: str, wd_server: str, site: str) -> tuple[bool, int]:
    url = (
        f"https://{tenant}.{wd_server}.myworkdayjobs.com/"
        f"wday/cxs/{tenant}/{site}/jobs"
    )
    body = json.dumps(
        {"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""}
    ).encode()
    return probe(url, timeout=12, method="POST", body=body)


def slugify(name: str) -> str:
    return (
        name.lower()
        .replace(" ", "-")
        .replace(".", "")
        .replace("&", "and")
        .replace("'", "")
    )


def main() -> None:
    existing = configured_slugs()
    existing_ids = {r["company_id"] for r in load_companies()}
    existing_names = {r["display_name"].casefold() for r in load_companies()}

    verified: list[dict] = []
    skipped: list[dict] = []
    seen_names: set[str] = set()

    for display_name, slug_candidates in CANDIDATES:
        key = display_name.casefold()
        if key in seen_names:
            continue
        seen_names.add(key)

        if key in existing_names:
            continue

        found = None
        for slug in slug_candidates:
            result = find_ats(slug, existing)
            if result:
                found = result
                break
            time.sleep(0.1)

        if found:
            ats, slug, count = found
            company_id = slugify(display_name)
            if company_id in existing_ids:
                continue
            verified.append({
                "company_id": company_id,
                "category": "Diagnostics",
                "display_name": display_name,
                "ats": ats,
                "slug": slug,
                "enabled": "yes",
                "notes": "",
                "wd_server": "",
                "workday_site": "",
                "job_count": count,
            })
            existing[ats].add(slug)
            existing_ids.add(company_id)
            existing_names.add(key)
            print(f"OK  {display_name}: {ats}/{slug} ({count} jobs)")
        else:
            skipped.append({
                "display_name": display_name,
                "slug_candidates": ", ".join(slug_candidates),
                "reason": "No supported ATS board found via API probe",
            })
            print(f"SKIP {display_name}")

    for display_name, tenant, wd_server, site in WORKDAY_CANDIDATES:
        key = display_name.casefold()
        if key in existing_names:
            continue
        if tenant in existing["workday"]:
            continue
        company_id = slugify(display_name)
        if company_id in existing_ids:
            continue

        ok, count = probe_workday(tenant, wd_server, site)
        time.sleep(0.2)
        if ok:
            verified.append({
                "company_id": company_id,
                "category": "Diagnostics",
                "display_name": display_name,
                "ats": "workday",
                "slug": tenant,
                "enabled": "yes",
                "notes": "",
                "wd_server": wd_server,
                "workday_site": site,
                "job_count": count,
            })
            existing["workday"].add(tenant)
            existing_ids.add(company_id)
            existing_names.add(key)
            seen_names.add(key)
            print(f"OK  {display_name}: workday/{tenant} ({count} jobs)")
        else:
            if key not in {s["display_name"].casefold() for s in skipped}:
                skipped.append({
                    "display_name": display_name,
                    "slug_candidates": f"{tenant}/{site}",
                    "reason": "No Workday board found via API probe",
                })
                print(f"SKIP {display_name} (workday)")

    out_dir = Path(__file__).resolve().parents[1] / "data"
    verified_path = out_dir / "_diagnostics_verified.json"
    skipped_path = out_dir / "_diagnostics_skipped.json"
    verified_path.write_text(json.dumps(verified, indent=2), encoding="utf-8")
    skipped_path.write_text(json.dumps(skipped, indent=2), encoding="utf-8")
    print(f"\nVerified: {len(verified)}, Skipped: {len(skipped)}")


if __name__ == "__main__":
    main()
