#!/usr/bin/env python3
"""Batch-probe Revenue Cycle candidate slugs across supported ATS APIs."""

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
    # Seed list
    ("FinThrive", ["finthrive", "nthrive"]),
    ("Candid Health", ["candidhealth", "candid"]),
    ("Cohere Health", ["coherehealth", "cohere"]),
    ("Clarify Health", ["clarifyhealth", "clarify"]),
    ("Cedar", ["cedar"]),
    ("Collectly", ["collectly"]),
    ("Inbox Health", ["inboxhealth", "inbox"]),
    ("MedEvolve", ["medevolve"]),
    ("Aspirion", ["aspirion"]),
    ("MDaudit", ["mdaudit", "md-audit"]),
    ("Navina", ["navina", "navinahealth"]),
    ("Nym", ["nym", "nymhealth"]),
    ("Thoughtful AI", ["thoughtful", "thoughtfulai"]),
    ("Availity", ["availity"]),
    ("HealthEdge", ["healthedge"]),
    # RCM / billing / claims / clearinghouse
    ("Adonis", ["adonis", "adonishealth"]),
    ("Notable Health", ["notable", "notablehealth"]),
    ("Qventus", ["qventus"]),
    ("Experian Health", ["experianhealth"]),
    ("Change Healthcare", ["changehealthcare", "change"]),
    ("Ciox Health", ["ciox", "cioxhealth"]),
    ("Datavant", ["datavant"]),
    ("Zelis", ["zelis"]),
    ("Turquoise Health", ["turquoisehealth", "turquoise"]),
    ("Cedar Gate", ["cedargate"]),
    ("Ribbon Health", ["ribbonhealth", "ribbon"]),
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
    ("MacroHealth", ["macrohealth"]),
    ("Edifecs", ["edifecs"]),
    ("SSI Group", ["ssigroup", "ssi"]),
    ("Cotiviti", ["cotiviti"]),
    ("Inovalon", ["inovalon"]),
    ("Craneware", ["craneware"]),
    ("Syntellis", ["syntellis"]),
    ("Conifer Health", ["conifer", "coniferhealth"]),
    ("Aquity Solutions", ["aquity", "aquitysolutions"]),
    ("Iodine Software", ["iodine", "iodinesoftware"]),
    ("LogixHealth", ["logixhealth"]),
    ("Parallon", ["parallon"]),
    ("HST Pathways", ["hstpathways", "hst"]),
    ("iSalus", ["isalus", "salus"]),
    ("MediRevv", ["medirevv"]),
    ("Ability Network", ["abilitynetwork", "ability"]),
    ("Trizetto", ["trizetto"]),
    ("Cognizant Healthcare", ["cognizant"]),
    ("Hyland Healthcare", ["hyland"]),
    ("Verisma", ["verisma"]),
    ("MRO", ["mro", "mrocorp"]),
    ("Epion Health", ["epion", "epionhealth"]),
    ("Digitize.AI", ["digitize", "digitizeai"]),
    ("Fathom Health", ["fathom", "fathomhealth"]),
    ("Luminai", ["luminai"]),
    ("Infinitus", ["infinitus", "infinitusai"]),
    ("AKASA", ["akasa"]),
    ("SmarterDx", ["smarterdx"]),
    ("Olive AI", ["olive", "oliveai"]),
    ("Waystar", ["waystar"]),
    ("R1 RCM", ["r1rcm", "r1"]),
    ("LeanTaaS", ["leantaas"]),
    ("PerfectServe", ["perfectserve"]),
    ("Findhelp", ["findhelp"]),
    ("Honor", ["honor"]),
    ("Papa", ["papa"]),
    ("Unite Us", ["uniteus"]),
    ("Jukebox Health", ["jukeboxhealth"]),
    ("Homeward", ["homeward"]),
    ("Wellthy", ["wellthy"]),
    ("Wellth", ["wellth"]),
    ("Wheel", ["wheel"]),
    ("Cleo", ["cleo"]),
    ("Thirty Madison", ["thirtymadison"]),
    ("Curative", ["curative"]),
    ("Cityblock Health", ["cityblock"]),
    ("Found", ["found"]),
    ("HealthSnap", ["healthsnap"]),
    ("ClosedLoop", ["closedloop", "closedloopai"]),
    ("Oshi Health", ["oshi", "oshihealth"]),
    ("Season Health", ["seasonhealth", "season"]),
    ("Vida Health", ["vida", "vidahealth"]),
    ("Omada Health", ["omada", "omadahealth"]),
    ("Lark Health", ["lark", "larkhealth"]),
    ("Big Health", ["bighealth"]),
    ("Ginger", ["ginger", "gingerio"]),
    ("Brightside Health", ["brightside", "brightsidehealth"]),
    ("CirrusMD", ["cirrusmd"]),
    ("Firefly Health", ["firefly", "fireflyhealth"]),
    ("Iora Health", ["iora", "iorahealth"]),
    ("Oak Street Health", ["oakstreethealth", "oakstreet"]),
    ("ChenMed", ["chenmed"]),
    ("Bamboo Health", ["bamboohealth", "bamboo"]),
    ("Lightbeam Health", ["lightbeam", "lightbeamhealth"]),
    ("Arcadia", ["arcadia", "arcadiahealth"]),
    ("Persivia", ["persivia"]),
    ("HealthVerity", ["healthverity"]),
    ("Memora Health", ["memora", "memorahealth"]),
    ("Luma Health", ["lumahealth", "luma"]),
    ("Innovaccer", ["innovaccer"]),
    ("Commure", ["commure"]),
    ("Hint Health", ["hint", "hinthealth"]),
    ("Elation Health", ["elationhealth", "elation"]),
    ("Tebra", ["tebra"]),
    ("Particle Health", ["particlehealth"]),
    ("Zus Health", ["zushealth"]),
    ("Redox", ["redox"]),
    ("Metriport", ["metriport"]),
    ("Canvas Medical", ["canvasmedical", "canvas"]),
    ("Ambience Healthcare", ["ambiencehealthcare", "ambience"]),
    ("Regard", ["regard", "regardhealth"]),
    ("Parachute Health", ["parachutehealth", "parachute"]),
    ("Collective Health", ["collectivehealth", "collective"]),
    ("Carrum Health", ["carrum", "carrumhealth"]),
    ("Rightway Healthcare", ["rightway", "rightwayhealthcare"]),
    ("Quantum Health", ["quantumhealth"]),
    ("HealthJoy", ["healthjoy"]),
    ("Nomi Health", ["nomihealth", "nomi"]),
    ("Garner Health", ["garnerhealth", "garner"]),
    ("Covera Health", ["coverahealth", "covera"]),
    ("Tomorrow Health", ["tomorrow", "tomorrowhealth"]),
    ("Boulder Care", ["bouldercare"]),
    ("Sonera Health", ["sonera", "sonerahealth"]),
    ("Medallion", ["medallion"]),
    ("Amwell", ["amwell", "americanwell"]),
    ("Teladoc", ["teladoc"]),
    ("Hims & Hers", ["hims", "forhims"]),
    ("Ro", ["ro", "rohealth"]),
    ("Virta Health", ["virtahealth", "virta"]),
    ("Aledade", ["aledade"]),
    ("Sword Health", ["swordhealth", "sword"]),
    ("Lyra Health", ["lyrahealth", "lyra"]),
    ("Levels", ["levels", "levelshealth"]),
    ("Moxie", ["moxie", "moxiehealth"]),
    ("SteadyMD", ["steadymd"]),
    ("Capsule", ["capsule"]),
    ("Doximity", ["doximity"]),
    ("Zocdoc", ["zocdoc"]),
    ("Suki", ["suki"]),
    ("Artera", ["artera", "arteraai"]),
    ("Phreesia", ["phreesia"]),
    ("Kyruus Health", ["kyruus", "kyruushealth"]),
    ("ModMed", ["modmed", "modernizingmedicine"]),
    ("Weave", ["weave", "getweave"]),
    ("Health Catalyst", ["healthcatalyst"]),
    ("Awell", ["awell", "awellhealth"]),
    ("DocASAP", ["docasap"]),
    ("QGenda", ["qgenda"]),
    ("Healthie", ["healthie", "gethealthie"]),
    ("DrChrono", ["drchrono"]),
    ("Kareo", ["kareo", "tebra"]),
    ("SimplePractice", ["simplepractice"]),
    ("Practice Fusion", ["practicefusion"]),
    ("AdvancedMD", ["advancedmd"]),
    ("NextGen Healthcare", ["nextgen", "nextgenhealthcare"]),
    ("CureMD", ["curemd"]),
    ("eClinicalWorks", ["eclinicalworks", "ecw"]),
    ("Greenway Health", ["greenway", "greenwayhealth"]),
    ("Chronius Health", ["chronius", "chroniushealth"]),
    ("athenahealth", ["athenahealth", "athena"]),
    ("CareCloud", ["carecloud"]),
    ("RXNT", ["rxnt"]),
    ("Progyny", ["progyny"]),
    ("RecoveryOne", ["recoveryone"]),
    ("CareBridge", ["carebridge"]),
    ("CarePort", ["careport", "careporthealth"]),
    ("WellSky", ["wellsky"]),
    ("MatrixCare", ["matrixcare"]),
    ("PointClickCare", ["pointclickcare", "pcc"]),
    ("Netsmart", ["ntst", "netsmart"]),
    ("NexHealth", ["nexhealth"]),
    ("Clearstep", ["clearstep", "clearstephealth"]),
    ("Rhinogram", ["rhinogram"]),
    ("Tendo", ["tendo", "tendohealth"]),
    ("symplr", ["symplr"]),
    ("Athelas", ["athelas", "athelashealth"]),
    ("CertifyOS", ["certifyos", "certify"]),
    ("Opmed", ["opmed", "opmedai"]),
    ("Dock Health", ["dockhealth", "dock"]),
    ("b.well", ["bwell", "bwellconnected"]),
    ("Health Gorilla", ["healthgorilla"]),
    ("AcuityMD", ["acuitymd"]),
    ("Moxe Health", ["moxehealth", "moxe"]),
    ("Axuall", ["axuall"]),
    ("Medispend", ["medispend"]),
    ("Medrio", ["medrio"]),
    ("MedeAnalytics", ["medeanalytics"]),
    ("PatientPop", ["patientpop"]),
    ("Solutionreach", ["solutionreach"]),
    ("Podium", ["podium"]),
    ("Birdeye", ["birdeye"]),
    ("Klara", ["klara", "klarahealth"]),
    ("TigerConnect", ["tigerconnect", "tigertext"]),
    ("Spok", ["spok", "spokinc"]),
    ("AmplifyMD", ["amplifymd", "amplify"]),
    ("Radix Health", ["radixhealth", "radix"]),
    ("Relatient", ["relatient"]),
    ("Solv Health", ["solvhealth", "solv"]),
    ("Regal", ["regal", "regalhealth"]),
    ("Pieces Technologies", ["pieces", "piecestech"]),
    ("Xealth", ["xealth"]),
    ("Flexpa", ["flexpa"]),
    ("Formstack Health", ["formstack", "formstackhealth"]),
    ("Bridge", ["bridge", "bridgespan"]),
    ("Headway", ["headway", "headwayhealth"]),
    ("Included Health", ["includedhealth", "grandrounds"]),
    ("Accolade", ["accolade", "accoladehealth"]),
    ("Transcarent", ["transcarent"]),
    ("Biofourmis", ["biofourmis"]),
    ("DispatchHealth", ["dispatchhealth", "dispatch"]),
    ("Signify Health", ["signifyhealth", "signify"]),
    ("Landmark Health", ["landmarkhealth", "landmark"]),
    ("Hometeam", ["hometeam", "hometeamcare"]),
    ("Blinq Health", ["blinq", "blinqhealth"]),
    ("Vocera", ["vocera", "stryker"]),
    ("SchoolCare", ["schoolcare"]),
    ("Collective Medical", ["collectivemedical"]),
    ("PatientPing", ["patientping", "bamboohealth"]),
    ("Audacious Inquiry", ["audaciousinquiry", "aihealth"]),
    ("ClosedLoop AI", ["closedloop", "closedloopai"]),
    ("HealthSnap", ["healthsnap"]),
    ("Babylist", ["babylist"]),
    ("Carrot Fertility", ["carrotfertility"]),
    ("Maven", ["mavenclinic", "maven"]),
    ("WelbeHealth", ["welbehealth"]),
    ("Hatch", ["hatch", "hatchhealth"]),
    ("Regal", ["regal"]),
    ("Luma", ["luma"]),
    ("Kyruus", ["kyruus"]),
    ("Symplr", ["symplr"]),
    ("TigerText", ["tigertext", "tigerconnect"]),
    ("NextGen", ["nextgen"]),
    ("Greenway Health", ["greenwayhealth"]),
    ("athenahealth", ["athenahealth"]),
    ("CareCloud", ["carecloud"]),
    ("Progyny", ["progyny"]),
    ("DispatchHealth", ["dispatchhealth"]),
    ("Signify Health", ["signifyhealth"]),
    ("Landmark Health", ["landmarkhealth"]),
    ("CareBridge", ["carebridge"]),
    ("CarePort", ["careport"]),
    ("WellSky", ["wellsky"]),
    ("MatrixCare", ["matrixcare"]),
    ("PointClickCare", ["pointclickcare"]),
    ("Netsmart", ["ntst"]),
    ("Adonis", ["adonis"]),
    ("Turquoise Health", ["turquoisehealth"]),
    ("Clearstep", ["clearstep"]),
    ("Rhinogram", ["rhinogram"]),
    ("Blinq Health", ["blinqhealth"]),
    ("Tendo", ["tendo"]),
    ("Iodine Software", ["iodine"]),
    ("LogixHealth", ["logixhealth"]),
    ("Navina", ["navina"]),
    ("Athelas", ["athelas"]),
    ("CertifyOS", ["certifyos"]),
    ("Dock Health", ["dockhealth"]),
    ("Health Gorilla", ["healthgorilla"]),
    ("AcuityMD", ["acuitymd"]),
    ("Moxe Health", ["moxehealth"]),
    ("Axuall", ["axuall"]),
    ("Medispend", ["medispend"]),
    ("Medrio", ["medrio"]),
    ("MedeAnalytics", ["medeanalytics"]),
    ("PatientPop", ["patientpop"]),
    ("Solutionreach", ["solutionreach"]),
    ("Podium", ["podium"]),
    ("Birdeye", ["birdeye"]),
    ("Klara", ["klara"]),
    ("AmplifyMD", ["amplifymd"]),
    ("Radix Health", ["radixhealth"]),
    ("Solv Health", ["solvhealth"]),
    ("Regal", ["regal"]),
    ("Xealth", ["xealth"]),
    ("Flexpa", ["flexpa"]),
    ("Parachute Health", ["parachutehealth"]),
    ("Collective Health", ["collectivehealth"]),
    ("Carrum Health", ["carrumhealth"]),
    ("Experian Health", ["experianhealth"]),
    ("FinThrive", ["finthrive"]),
    ("HealthSnap", ["healthsnap"]),
    ("Cohere Health", ["coherehealth"]),
    ("Oshi Health", ["oshihealth"]),
    ("Season Health", ["seasonhealth"]),
    ("Vida Health", ["vidahealth"]),
    ("Omada Health", ["omadahealth"]),
    ("Lark Health", ["larkhealth"]),
    ("Big Health", ["bighealth"]),
    ("CirrusMD", ["cirrusmd"]),
    ("Firefly Health", ["fireflyhealth"]),
    ("Iora Health", ["iorahealth"]),
    ("Oak Street Health", ["oakstreethealth"]),
    ("ChenMed", ["chenmed"]),
    ("Bamboo Health", ["bamboohealth"]),
    ("Lightbeam Health", ["lightbeamhealth"]),
    ("Arcadia", ["arcadia"]),
    ("Persivia", ["persivia"]),
    ("HealthVerity", ["healthverity"]),
    ("Datavant", ["datavant"]),
    ("Ciox Health", ["cioxhealth"]),
    ("Epion Health", ["epionhealth"]),
    ("Thoughtful AI", ["thoughtful", "thoughtfulai"]),
    ("Collectly", ["collectly"]),
    ("Inbox Health", ["inboxhealth"]),
    ("MedEvolve", ["medevolve"]),
    ("Aspirion", ["aspirion"]),
    ("MDaudit", ["mdaudit"]),
    ("Nym", ["nym"]),
    ("HealthEdge", ["healthedge"]),
    ("Clarify Health", ["clarifyhealth"]),
    ("Candid Health", ["candidhealth"]),
    ("Cedar", ["cedar"]),
    ("Availity", ["availity"]),
]

# Known Workday boards: (display_name, tenant, wd_server, workday_site)
WORKDAY_CANDIDATES: list[tuple[str, str, str, str]] = [
    ("FinThrive", "finthrive", "wd1", "FinThrive"),
    ("Zelis", "zelis", "wd1", "Zelis"),
    ("Cotiviti", "cotiviti", "wd1", "Cotiviti"),
    ("Inovalon", "inovalon", "wd5", "Inovalon"),
    ("Craneware", "craneware", "wd3", "Craneware"),
    ("Experian Health", "experian", "wd5", "ExperianHealth"),
    ("HealthEdge", "healthedge", "wd1", "HealthEdge"),
    ("Availity", "availity", "wd5", "Availity"),
    ("Ensemble Health Partners", "ensemblehp", "wd1", "Ensemble"),
    ("CorroHealth", "corrohealth", "wd1", "CorroHealth"),
    ("AGS Health", "agshealth", "wd1", "AGSHealth"),
    ("Omega Healthcare", "omegahc", "wd1", "Omega"),
    ("GeBBS Healthcare", "gebbs", "wd1", "GeBBS"),
    ("Parallon", "hca", "wd1", "Parallon"),
    ("Conifer Health", "coniferhealth", "wd1", "Conifer"),
    ("Change Healthcare", "changehealthcare", "wd1", "ChangeHealthcare"),
    ("XIFIN", "xifin", "wd1", "XIFIN"),
    ("Cloudmed", "cloudmed", "wd1", "Cloudmed"),
    ("RevSpring", "revspring", "wd1", "RevSpring"),
    ("Edifecs", "edifecs", "wd1", "Edifecs"),
    ("Hyland", "hyland", "wd1", "Hyland"),
    ("Syntellis", "syntellis", "wd1", "Syntellis"),
    ("Aquity Solutions", "aquity", "wd1", "Aquity"),
    ("Ability Network", "abilitynetwork", "wd1", "AbilityNetwork"),
    ("Trizetto", "trizetto", "wd1", "Trizetto"),
    ("SSI Group", "ssigroup", "wd1", "SSI"),
    ("Quadax", "quadax", "wd1", "Quadax"),
    ("MedEvolve", "medevolve", "wd1", "MedEvolve"),
    ("Aspirion", "aspirion", "wd1", "Aspirion"),
    ("MDaudit", "mdaudit", "wd1", "MDaudit"),
    ("Flywire", "flywire", "wd3", "Flywire"),
    ("Cognizant", "cognizant", "wd3", "Cognizant"),
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
                "category": "Revenue Cycle",
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
        if key in seen_names and key in existing_names:
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
                "category": "Revenue Cycle",
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
    verified_path = out_dir / "_revenue_cycle_verified.json"
    skipped_path = out_dir / "_revenue_cycle_skipped.json"
    verified_path.write_text(json.dumps(verified, indent=2), encoding="utf-8")
    skipped_path.write_text(json.dumps(skipped, indent=2), encoding="utf-8")
    print(f"\nVerified: {len(verified)}, Skipped: {len(skipped)}")


if __name__ == "__main__":
    main()
