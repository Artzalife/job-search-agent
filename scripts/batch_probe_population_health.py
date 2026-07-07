#!/usr/bin/env python3
"""Batch-probe Population Health candidate slugs across supported ATS APIs."""

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
    ("Evolent Health", ["evolent", "evolenthealth"]),
    ("Privia Health", ["privia", "priviahealth"]),
    ("ZeOmega", ["zeomega"]),
    ("Guidehealth", ["guidehealth", "guide"]),
    ("Navvis", ["navvis", "navvishealth"]),
    ("Equality Health", ["equalityhealth", "equality"]),
    ("Thyme Care", ["thymecare", "thyme"]),
    ("Quartet Health", ["quartethealth", "quartet"]),
    ("Monogram Health", ["monogramhealth", "monogram"]),
    ("Somatus", ["somatus"]),
    ("Emcara Health", ["emcara", "emcarahealth"]),
    ("HealthEC", ["healthec", "healthecinc"]),
    ("Innovista Health", ["innovista", "innovistahealth"]),
    ("Vytalize Health", ["vytalize", "vytalizehealth"]),
    # Value-based care / MSO / ACO enablement
    ("Agilon Health", ["agilon", "agilonhealth"]),
    ("Oak Street Health", ["oakstreethealth", "oakstreet"]),
    ("ChenMed", ["chenmed"]),
    ("Iora Health", ["iorahealth", "iora"]),
    ("Cano Health", ["canohealth", "cano"]),
    ("Alignment Healthcare", ["alignmenthealthcare", "alignment"]),
    ("Devoted Health", ["devoted", "devotedhealth"]),
    ("Bright Health Group", ["brighthealth", "brighthealthgroup"]),
    ("Premise Health", ["premisehealth", "premise"]),
    ("Pearl Health", ["pearlhealth", "pearl"]),
    ("Biofourmis", ["biofourmis"]),
    ("Welldoc", ["welldoc"]),
    ("Glooko", ["glooko"]),
    ("Conversa Health", ["conversa", "conversahealth"]),
    ("Health Recovery Solutions", ["hrs", "healthrecoverysolutions"]),
    ("Transcarent", ["transcarent"]),
    ("Included Health", ["includedhealth", "grandrounds"]),
    ("Quantum Health", ["quantumhealth", "quantum"]),
    ("Rightway Healthcare", ["rightway", "rightwayhealthcare"]),
    ("HealthJoy", ["healthjoy"]),
    ("Carrum Health", ["carrumhealth", "carrum"]),
    ("Firefly Health", ["fireflyhealth", "firefly"]),
    ("Season Health", ["seasonhealth", "season"]),
    ("DispatchHealth", ["dispatchhealth", "dispatch"]),
    ("CareBridge", ["carebridge"]),
    ("CarePort", ["careport", "careporthealth"]),
    ("MatrixCare", ["matrixcare"]),
    ("Persivia", ["persivia"]),
    ("Enli Health Intelligence", ["enli", "enlihealth"]),
    ("Citra Health", ["citra", "citrahealth"]),
    ("Eccovia", ["eccovia"]),
    ("Casenet Healthcare", ["casenet", "casenethealthcare"]),
    ("Concerto HealthAI", ["concertohealthai", "concerto"]),
    ("Ontada", ["ontada"]),
    ("Navigating Cancer", ["navigatingcancer"]),
    ("Cricket Health", ["crickethealth", "cricket"]),
    ("Socially Determined", ["sociallydetermined"]),
    ("Audacious Inquiry", ["audaciousinquiry", "aihealth"]),
    ("Collective Medical", ["collectivemedical"]),
    ("PatientPing", ["patientping"]),
    ("Appriss Health", ["appriss", "apprisshealth"]),
    ("NextHealth", ["nexthealth"]),
    ("Milliman", ["milliman"]),
    ("RTI International", ["rti", "rtiinternational"]),
    ("CitiusTech", ["citiustech"]),
    ("CynergisTek", ["cynergistek"]),
    ("HealthPrize", ["healthprize"]),
    ("Sparta Science", ["sparta", "spartascience"]),
    ("Pieces Technologies", ["pieces", "piecestech"]),
    ("Regard", ["regard", "regardhealth"]),
    ("Ambience Healthcare", ["ambiencehealthcare", "ambience"]),
    ("Nomi Health", ["nomihealth", "nomi"]),
    ("Tomorrow Health", ["tomorrow", "tomorrowhealth"]),
    ("Boulder Care", ["bouldercare"]),
    ("Sonera Health", ["sonera", "sonerahealth"]),
    ("SteadyMD", ["steadymd"]),
    ("Lyra Health", ["lyrahealth", "lyra"]),
    ("98point6", ["98point6"]),
    ("CirrusMD", ["cirrusmd"]),
    ("SchoolCare", ["schoolcare"]),
    ("Cedar Gate Technologies", ["cedargate"]),
    ("Lightbeam Health Solutions", ["lightbeam", "lightbeamhealth"]),
    ("Bamboo Health", ["bamboohealth", "bamboo"]),
    ("Health Catalyst", ["healthcatalyst"]),
    ("Datavant", ["datavant"]),
    ("Ribbon Health", ["ribbonhealth", "ribbon"]),
    ("Turquoise Health", ["turquoisehealth", "turquoise"]),
    ("LeanTaaS", ["leantaas"]),
    ("AKASA", ["akasa"]),
    ("SmarterDx", ["smarterdx"]),
    ("Fathom Health", ["fathom", "fathomhealth"]),
    ("Notable Health", ["notable", "notablehealth"]),
    ("Suki", ["suki"]),
    ("Memora Health", ["memora", "memorahealth"]),
    ("Luma Health", ["lumahealth", "luma"]),
    ("Commure", ["commure"]),
    ("Hint Health", ["hint", "hinthealth"]),
    ("Elation Health", ["elationhealth", "elation"]),
    ("Tebra", ["tebra"]),
    ("Moxe Health", ["moxehealth", "moxe"]),
    ("Axuall", ["axuall"]),
    ("Medispend", ["medispend"]),
    ("Medrio", ["medrio"]),
    ("Flexpa", ["flexpa"]),
    ("Opmed", ["opmed", "opmedai"]),
    ("Iodine Software", ["iodine", "iodinesoftware"]),
    ("LogixHealth", ["logixhealth"]),
    ("Clearstep", ["clearstep", "clearstephealth"]),
    ("Adonis", ["adonis", "adonishealth"]),
    ("Olive AI", ["olive", "oliveai"]),
    ("Epion Health", ["epion", "epionhealth"]),
    ("Verisma", ["verisma"]),
    ("MRO", ["mro", "mrocorp"]),
    ("Digitize.AI", ["digitize", "digitizeai"]),
    ("Luminai", ["luminai"]),
    ("Infinitus", ["infinitus", "infinitusai"]),
    ("Nym", ["nym", "nymhealth"]),
    ("Thoughtful AI", ["thoughtful", "thoughtfulai"]),
    ("Collectly", ["collectly"]),
    ("Inbox Health", ["inboxhealth", "inbox"]),
    ("MedEvolve", ["medevolve"]),
    ("MDaudit", ["mdaudit", "md-audit"]),
    ("HealthEdge", ["healthedge"]),
    ("Availity", ["availity"]),
    ("Zelis", ["zelis"]),
    ("XIFIN", ["xifin"]),
    ("Quadax", ["quadax"]),
    ("Cloudmed", ["cloudmed"]),
    ("AGS Health", ["agshealth", "ags"]),
    ("Omega Healthcare", ["omegahealthcare", "omega"]),
    ("GeBBS Healthcare", ["gebbs", "gebbshealthcare"]),
    ("Ensemble Health Partners", ["ensemble", "ensemblehealthpartners"]),
    ("CorroHealth", ["corrohealth", "panacea"]),
    ("Alpha II", ["alphaii", "alpha2"]),
    ("MediStreams", ["medistreams"]),
    ("RevSpring", ["revspring"]),
    ("PatientCo", ["patientco"]),
    ("VisitPay", ["visitpay"]),
    ("Salucro", ["salucro"]),
    ("AccessOne", ["accessone", "accessonehealth"]),
    ("Flywire", ["flywire"]),
    ("Payspan", ["payspan"]),
    ("ClearGage", ["cleargage"]),
    ("PatientPay", ["patientpay"]),
    ("Office Ally", ["officeally"]),
    ("CollaborateMD", ["collaboratemd"]),
    ("Claim.MD", ["claimmd", "claim"]),
    ("pVerify", ["pverify"]),
    ("Stedi", ["stedi"]),
    ("Enter Health", ["enterhealth"]),
    ("Edifecs", ["edifecs"]),
    ("SSI Group", ["ssigroup", "ssi"]),
    ("Craneware", ["craneware"]),
    ("Syntellis", ["syntellis"]),
    ("Conifer Health", ["conifer", "coniferhealth"]),
    ("Aquity Solutions", ["aquity", "aquitysolutions"]),
    ("Parallon", ["parallon"]),
    ("HST Pathways", ["hstpathways", "hst"]),
    ("iSalus", ["isalus", "salus"]),
    ("MediRevv", ["medirevv"]),
    ("Ability Network", ["abilitynetwork", "ability"]),
    ("Trizetto", ["trizetto"]),
    ("Cognizant Healthcare", ["cognizant"]),
    ("Hyland Healthcare", ["hyland"]),
    ("Change Healthcare", ["changehealthcare", "change"]),
    ("FinThrive", ["finthrive", "nthrive"]),
    ("Waystar", ["waystar"]),
    ("R1 RCM", ["r1rcm", "r1"]),
    ("Ciox Health", ["ciox", "cioxhealth"]),
    ("Experian Health", ["experianhealth"]),
    ("Hinge Health", ["hingehealth", "hinge"]),
    ("Landmark Health", ["landmarkhealth", "landmark"]),
]

# Known Workday boards: (display_name, tenant, wd_server, workday_site)
WORKDAY_CANDIDATES: list[tuple[str, str, str, str]] = [
    ("Evolent Health", "evolent", "wd5", "Evolent"),
    ("Privia Health", "privia", "wd5", "PriviaHealth"),
    ("Molina Healthcare", "molina", "wd5", "MolinaHealthcare"),
    ("Agilon Health", "agilonhealth", "wd5", "Agilon_Health"),
    ("Alignment Healthcare", "alignmenthealthcare", "wd5", "AlignmentHealthcare"),
    ("Premise Health", "premisehealth", "wd1", "Premise"),
    ("Milliman", "milliman", "wd1", "Milliman"),
    ("RTI International", "rti", "wd1", "RTI"),
    ("CitiusTech", "citiustech", "wd1", "CitiusTech"),
    ("ZeOmega", "zeomega", "wd1", "ZeOmega"),
    ("HealthEC", "healthec", "wd1", "HealthEC"),
    ("Guidehealth", "guidehealth", "wd1", "Guidehealth"),
    ("Navvis", "navvis", "wd5", "Navvis"),
    ("Somatus", "somatus", "wd5", "Somatus"),
    ("Monogram Health", "monogramhealth", "wd5", "MonogramHealth"),
    ("Vytalize Health", "vytalizehealth", "wd5", "Vytalize"),
    ("Innovista Health", "innovista", "wd5", "Innovista"),
    ("Emcara Health", "emcara", "wd5", "Emcara"),
    ("Equality Health", "equalityhealth", "wd5", "EqualityHealth"),
    ("ChenMed", "chenmed", "wd5", "ChenMed"),
    ("Oak Street Health", "oakstreethealth", "wd5", "OakStreetHealth"),
    ("Cano Health", "canohealth", "wd5", "CanoHealth"),
    ("Bright Health Group", "brighthealth", "wd5", "BrightHealth"),
    ("Devoted Health", "devotedhealth", "wd5", "Devoted"),
    ("Quartet Health", "quartethealth", "wd5", "QuartetHealth"),
    ("Thyme Care", "thymecare", "wd5", "ThymeCare"),
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
                "category": "Population Health",
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
                "category": "Population Health",
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
    verified_path = out_dir / "_population_health_verified.json"
    skipped_path = out_dir / "_population_health_skipped.json"
    verified_path.write_text(json.dumps(verified, indent=2), encoding="utf-8")
    skipped_path.write_text(json.dumps(skipped, indent=2), encoding="utf-8")
    print(f"\nVerified: {len(verified)}, Skipped: {len(skipped)}")


if __name__ == "__main__":
    main()
