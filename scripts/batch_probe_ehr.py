#!/usr/bin/env python3
"""Batch-probe EHR & Clinical Workflow candidate slugs across supported ATS APIs."""

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
    GREENHOUSE_API_BASE,
    LEVER_API_BASE,
    WORKABLE_API_BASE,
    load_companies,
)

HEADERS = {"Accept": "application/json", "User-Agent": "job-search-agent/1.0"}

# (display_name, slug_candidates) — first matching slug wins per ATS
# Priority: ambulatory EHR → hospital → post-acute → behavioral → specialty → workflow
CANDIDATES: list[tuple[str, list[str]]] = [
    # --- Ambulatory EHR & Practice Management (seed + expansion) ---
    ("ModMed", ["modmed", "modernizingmedicine"]),
    ("DrChrono", ["drchrono"]),
    ("Practice Fusion", ["practicefusion"]),
    ("Amazing Charts", ["amazingcharts"]),
    ("ChartLogic", ["chartlogic"]),
    ("Experity", ["experity"]),
    ("Practice EHR", ["practiceehr"]),
    ("NueMD", ["nuemd"]),
    ("PracticeSuite", ["practicesuite"]),
    ("PrognoCIS", ["prognocis"]),
    ("Benchmark Systems", ["benchmarksystems", "benchmark"]),
    ("Meditab", ["meditab"]),
    ("Azalea Health", ["azaleahealth", "azalea"]),
    ("Praxis EMR", ["praxisemr", "praxis"]),
    ("MDLand", ["mdland"]),
    ("Compulink Healthcare Solutions", ["compulink", "compulinkhealthcare"]),
    ("CollaborateMD", ["collaboratemd"]),
    ("iSalus Healthcare", ["isalus", "isalushealthcare"]),
    ("ChARM EHR", ["charmhealth", "charm"]),
    ("Kareo", ["kareo"]),
    ("Hello Health", ["hellohealth"]),
    ("Enable Healthcare", ["enablehealthcare", "enable"]),
    ("DocVilla", ["docvilla"]),
    ("Healthie", ["healthie", "gethealthie"]),
    ("Greenway Health", ["greenwayhealth", "greenway"]),
    # --- Hospital / Acute Care EHR ---
    ("Altera Digital Health", ["alteradigitalhealth", "altera", "nthrive"]),
    ("Veradigm", ["veradigm", "allscripts"]),
    ("MEDHOST", ["medhost"]),
    ("TruBridge", ["trubridge", "cpsi"]),
    ("Paragon", ["paragon", "paragonhealth"]),
    ("InterSystems", ["intersystems"]),
    ("Epic", ["epic", "epicsystems"]),
    ("Oracle Health", ["oraclehealth", "cerner", "oracle"]),
    ("MEDITECH", ["meditech"]),
    # --- Post-Acute & Long-Term Care ---
    ("Axxess", ["axxess", "axxesshomehealth"]),
    ("Homecare Homebase", ["homecarehomebase", "hchb"]),
    ("AlayaCare", ["alayacare"]),
    ("ClearCare", ["clearcare", "clearcareonline"]),
    ("KanTime", ["kantime"]),
    ("Casamba", ["casamba"]),
    ("Consolo", ["consolo", "consoloservices"]),
    ("CellTrak", ["celltrak"]),
    ("SigmaCare", ["sigmacare"]),
    ("Homecare Software Solutions", ["homecaresoftware", "hcss"]),
    ("Axxess Hospice", ["axxesshospice"]),
    # --- Behavioral Health EHR ---
    ("Qualifacts", ["qualifacts"]),
    ("Credible Behavioral Health", ["crediblebh", "crediblebehavioral"]),
    ("TherapyNotes", ["therapynotes"]),
    ("Carepatron", ["carepatron"]),
    ("Valant", ["valant", "valanthealth"]),
    ("TheraNest", ["theranest"]),
    ("CentralReach", ["centralreach"]),
    ("Procentive", ["procentive"]),
    ("ICANotes", ["icanotes"]),
    ("EchoVantage", ["echovantage"]),
    ("BestNotes", ["bestnotes"]),
    ("PIMSY", ["pimsy"]),
    ("MyClientsPlus", ["myclientsplus"]),
    ("Ensora Health", ["ensora", "ensorahealth"]),
    # --- Specialty EHRs ---
    ("Nextech", ["nextech", "nextechsystems"]),
    ("RevolutionEHR", ["revolutionehr"]),
    ("Eyefinity", ["eyefinity"]),
    ("gGastro", ["ggastro", "gmed"]),
    ("WebPT", ["webpt"]),
    ("Clinicient", ["clinicient"]),
    ("Raintree Systems", ["raintree", "raintreesystems"]),
    ("Phoenix Ortho", ["phoenixortho"]),
    ("OrthoFi", ["orthofi"]),
    ("Modernizing Medicine", ["modernizingmedicine", "modmed"]),
    ("EyeMD EMR", ["eyemdemr", "eyemd"]),
    ("Medstreaming", ["medstreaming"]),
    ("Ophthalmic Imaging Systems", ["ois", "oismedical"]),
    ("CompuGroup Medical", ["cgm", "compugroup"]),
  # --- Clinical Workflow & Documentation ---
    ("Ambra Health", ["ambra", "ambrahealth"]),
    ("RamSoft", ["ramsoft"]),
    ("NovaRad", ["novarad"]),
    ("Intelerad", ["intelerad"]),
    ("Sectra", ["sectra"]),
    ("Agfa HealthCare", ["agfa", "agfahealthcare"]),
    ("Philips Healthcare Informatics", ["philips", "philipshealthcare"]),
    ("Merge Healthcare", ["mergehealthcare", "ibmmerge"]),
    ("Ambience Healthcare", ["ambiencehealthcare", "ambience"]),
    ("Abridge", ["abridge"]),
    ("Nuance", ["nuance"]),
    ("Notable Health", ["notable", "notablehealth"]),
    ("Suki", ["suki"]),
    ("Freed", ["freed"]),
    ("Nabla", ["nabla"]),
    ("Augmedix", ["augmedix"]),
    ("Regard", ["regard", "regardhealth"]),
    # --- Additional ambulatory / PM vendors ---
    ("AdvancedMD", ["advancedmd"]),
    ("athenahealth", ["athenahealth", "athena"]),
    ("NextGen Healthcare", ["nextgen", "nextgenhealthcare"]),
    ("CureMD", ["curemd"]),
    ("eClinicalWorks", ["eclinicalworks", "ecw"]),
    ("CareCloud", ["carecloud"]),
    ("RXNT", ["rxnt"]),
    ("SimplePractice", ["simplepractice"]),
    ("Tebra", ["tebra"]),
    ("Hint Health", ["hint", "hinthealth"]),
    ("Elation Health", ["elationhealth", "elation"]),
    ("Canvas Medical", ["canvasmedical", "canvas"]),
    ("Office Ally", ["officeally"]),
    ("PerfectServe", ["perfectserve"]),
    ("TigerConnect", ["tigerconnect", "tigertext"]),
    ("Spok", ["spok", "spokinc"]),
    ("Vocera", ["vocera", "stryker"]),
    ("Epion Health", ["epion", "epionhealth"]),
    ("Iodine Software", ["iodine", "iodinesoftware"]),
    ("LogixHealth", ["logixhealth"]),
    ("HST Pathways", ["hstpathways", "hst"]),
    ("MedEvolve", ["medevolve"]),
    ("Medgen EHR", ["medgen", "medgenehr"]),
    ("ChartSpan", ["chartspan"]),
    ("Lightbeam Health", ["lightbeam", "lightbeamhealth"]),
    ("Persivia", ["persivia"]),
    ("Health Catalyst", ["healthcatalyst"]),
    ("Doximity", ["doximity"]),
]

# Known Workday boards: (display_name, tenant, wd_server, workday_site)
WORKDAY_CANDIDATES: list[tuple[str, str, str, str]] = [
    ("MEDITECH", "meditech", "wd1", "MEDITECH"),
    ("Oracle Health", "cerner", "wd5", "Cerner"),
    ("MEDHOST", "medhost", "wd1", "MEDHOST"),
    ("Veradigm", "veradigm", "wd1", "Veradigm"),
    ("Altera Digital Health", "altera", "wd1", "AlteraDigitalHealth"),
    ("InterSystems", "intersystems", "wd5", "InterSystems_Careers"),
    ("TruBridge", "trubridge", "wd1", "TruBridge"),
    ("Qualifacts", "qualifacts", "wd1", "Qualifacts"),
    ("Axxess", "axxess", "wd1", "Axxess"),
    ("Homecare Homebase", "hchb", "wd1", "HCHB"),
    ("AlayaCare", "alayacare", "wd3", "AlayaCare"),
    ("KanTime", "kantime", "wd1", "KanTime"),
    ("Nextech", "nextech", "wd1", "Nextech"),
    ("WebPT", "webpt", "wd1", "WebPT"),
    ("CentralReach", "centralreach", "wd1", "CentralReach"),
    ("TheraNest", "theranest", "wd1", "TheraNest"),
    ("Valant", "valant", "wd1", "Valant"),
    ("Sectra", "sectra", "wd3", "Sectra"),
    ("Agfa HealthCare", "agfa", "wd3", "Agfa"),
    ("Philips", "philips", "wd3", "Philips"),
    ("Nuance", "nuance", "wd5", "Nuance"),
    ("Epic", "epic", "wd5", "Epic"),
    ("ModMed", "modmed", "wd1", "ModMed"),
    ("Greenway Health", "greenwayhealth", "wd1", "GreenwayHealth"),
    ("DrChrono", "drchrono", "wd1", "DrChrono"),
    ("Practice Fusion", "practicefusion", "wd1", "PracticeFusion"),
    ("Amazing Charts", "amazingcharts", "wd1", "AmazingCharts"),
    ("ChartLogic", "chartlogic", "wd1", "ChartLogic"),
    ("Experity", "experity", "wd1", "Experity"),
    ("NueMD", "nuemd", "wd1", "NueMD"),
    ("PrognoCIS", "prognocis", "wd1", "PrognoCIS"),
    ("Azalea Health", "azaleahealth", "wd1", "AzaleaHealth"),
    ("Compulink Healthcare Solutions", "compulink", "wd1", "Compulink"),
    ("MDLand", "mdland", "wd1", "MDLand"),
    ("Meditab", "meditab", "wd1", "Meditab"),
    ("Benchmark Systems", "benchmarksystems", "wd1", "BenchmarkSystems"),
    ("PracticeSuite", "practicesuite", "wd1", "PracticeSuite"),
    ("Intelerad", "intelerad", "wd3", "Intelerad"),
    ("RamSoft", "ramsoft", "wd1", "RamSoft"),
    ("Ambra Health", "ambra", "wd1", "AmbraHealth"),
    ("RevolutionEHR", "revolutionehr", "wd1", "RevolutionEHR"),
    ("Eyefinity", "eyefinity", "wd1", "Eyefinity"),
    ("Clinicient", "clinicient", "wd1", "Clinicient"),
    ("Raintree Systems", "raintree", "wd1", "Raintree"),
    ("CompuGroup Medical", "cgm", "wd3", "CGM"),
    ("iSalus Healthcare", "isalus", "wd1", "iSalus"),
    ("CollaborateMD", "collaboratemd", "wd1", "CollaborateMD"),
    ("ChARM EHR", "charmhealth", "wd1", "ChARM"),
    ("Health Catalyst", "healthcatalyst", "wd1", "HealthCatalyst"),
    ("Innovaccer", "innovaccer", "wd5", "Innovaccer"),
    ("Vocera", "vocera", "wd5", "Vocera"),
    ("Stryker", "stryker", "wd1", "Stryker"),
    ("HST Pathways", "hstpathways", "wd1", "HSTPathways"),
    ("MedEvolve", "medevolve", "wd1", "MedEvolve"),
    ("Credible Behavioral Health", "crediblebh", "wd1", "CredibleBH"),
    ("TherapyNotes", "therapynotes", "wd1", "TherapyNotes"),
    ("Carepatron", "carepatron", "wd1", "Carepatron"),
    ("Procentive", "procentive", "wd1", "Procentive"),
    ("ICANotes", "icanotes", "wd1", "ICANotes"),
    ("EchoVantage", "echovantage", "wd1", "EchoVantage"),
    ("BestNotes", "bestnotes", "wd1", "BestNotes"),
    ("PIMSY", "pimsy", "wd1", "PIMSY"),
    ("MyClientsPlus", "myclientsplus", "wd1", "MyClientsPlus"),
    ("Ensora Health", "ensora", "wd1", "Ensora"),
    ("Casamba", "casamba", "wd1", "Casamba"),
    ("Consolo", "consolo", "wd1", "Consolo"),
    ("CellTrak", "celltrak", "wd1", "CellTrak"),
    ("SigmaCare", "sigmacare", "wd1", "SigmaCare"),
    ("ClearCare", "clearcare", "wd1", "ClearCare"),
    ("Homecare Software Solutions", "hcss", "wd1", "HCSS"),
    ("Hello Health", "hellohealth", "wd1", "HelloHealth"),
    ("Enable Healthcare", "enablehealthcare", "wd1", "EnableHealthcare"),
    ("DocVilla", "docvilla", "wd1", "DocVilla"),
    ("Healthie", "healthie", "wd1", "Healthie"),
    ("Praxis EMR", "praxisemr", "wd1", "PraxisEMR"),
    ("Practice EHR", "practiceehr", "wd1", "PracticeEHR"),
    ("gGastro", "ggastro", "wd1", "gGastro"),
    ("EyeMD EMR", "eyemd", "wd1", "EyeMD"),
    ("Medstreaming", "medstreaming", "wd1", "Medstreaming"),
    ("Phoenix Ortho", "phoenixortho", "wd1", "PhoenixOrtho"),
    ("OrthoFi", "orthofi", "wd1", "OrthoFi"),
    ("NovaRad", "novarad", "wd1", "NovaRad"),
    ("Merge Healthcare", "ibm", "wd1", "IBM"),
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
        .replace("(", "")
        .replace(")", "")
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
                "category": "EHR",
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
                "category": "EHR",
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
    verified_path = out_dir / "_ehr_verified.json"
    skipped_path = out_dir / "_ehr_skipped.json"
    verified_path.write_text(json.dumps(verified, indent=2), encoding="utf-8")
    skipped_path.write_text(json.dumps(skipped, indent=2), encoding="utf-8")
    print(f"\nVerified: {len(verified)}, Skipped: {len(skipped)}")


if __name__ == "__main__":
    main()
