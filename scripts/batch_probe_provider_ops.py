#!/usr/bin/env python3
"""Batch-probe Provider Operations candidate slugs across supported ATS APIs."""

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
    # Sample list
    ("NexHealth", ["nexhealth"]),
    ("Phreesia", ["phreesia"]),
    ("Kyruus Health", ["kyruus", "kyruushealth"]),
    ("ModMed", ["modmed", "modernizingmedicine"]),
    ("Weave", ["weave", "getweave"]),
    ("Health Catalyst", ["healthcatalyst"]),
    ("Ribbon Health", ["ribbonhealth", "ribbon"]),
    ("Awell", ["awell", "awellhealth"]),
    ("DocASAP", ["docasap"]),
    ("QGenda", ["qgenda"]),
    ("Healthie", ["healthie", "gethealthie"]),
    ("Availity", ["availity"]),
    # Practice management / EHR-adjacent ops
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
    ("Hinge Health", ["hingehealth", "hinge"]),
    ("RecoveryOne", ["recoveryone"]),
    ("Biofourmis", ["biofourmis"]),
    ("DispatchHealth", ["dispatchhealth", "dispatch"]),
    ("Signify Health", ["signifyhealth", "signify"]),
    ("Landmark Health", ["landmarkhealth", "landmark"]),
    ("Hometeam", ["hometeam", "hometeamcare"]),
    ("CareBridge", ["carebridge"]),
    ("CarePort", ["careport", "careporthealth"]),
    ("WellSky", ["wellsky"]),
    ("MatrixCare", ["matrixcare"]),
    ("PointClickCare", ["pointclickcare", "pcc"]),
    ("Netsmart", ["ntst", "netsmart"]),
    ("Waystar", ["waystar"]),
    ("R1 RCM", ["r1rcm", "r1"]),
    ("Adonis", ["adonis", "adonishealth"]),
    ("Turquoise Health", ["turquoisehealth", "turquoise"]),
    ("Clearstep", ["clearstep", "clearstephealth"]),
    ("Rhinogram", ["rhinogram"]),
    ("Blinq Health", ["blinq", "blinqhealth"]),
    ("Tendo", ["tendo", "tendohealth"]),
    ("symplr", ["symplr"]),
    ("Iodine Software", ["iodine", "iodinesoftware"]),
    ("LogixHealth", ["logixhealth"]),
    ("Navina", ["navina", "navinahealth"]),
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
    ("AKASA", ["akasa"]),
    ("Olive AI", ["olive", "oliveai"]),
    ("Amwell", ["amwell", "americanwell"]),
    ("Teladoc", ["teladoc"]),
    ("Hims & Hers", ["hims", "forhims"]),
    ("Ro", ["ro", "rohealth"]),
    ("Virta Health", ["virtahealth", "virta"]),
    ("Aledade", ["aledade"]),
    ("Sword Health", ["swordhealth", "sword"]),
    ("Lyra Health", ["lyrahealth", "lyra"]),
    ("Levels", ["levels", "levelshealth"]),
    ("Hatch", ["hatch", "hatchhealth"]),
    ("Moxie", ["moxie", "moxiehealth"]),
    ("SteadyMD", ["steadymd"]),
    ("Capsule", ["capsule"]),
    ("Doximity", ["doximity"]),
    ("Zocdoc", ["zocdoc"]),
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
    ("Cedar Gate", ["cedargate"]),
    ("Experian Health", ["experianhealth"]),
    ("Change Healthcare", ["changehealthcare", "change"]),
    ("FinThrive", ["finthrive", "nthrive"]),
    ("Waystar", ["waystar"]),
    ("R1 RCM", ["r1rcm"]),
    ("Olive", ["olive"]),
    ("Notable Health", ["notable"]),
    ("Suki", ["suki"]),
    ("Qventus", ["qventus"]),
    ("Artera", ["artera", "arteraai"]),
    ("Memora Health", ["memora", "memorahealth"]),
    ("Luma Health", ["lumahealth", "luma"]),
    ("Innovaccer", ["innovaccer"]),
    ("Commure", ["commure"]),
    ("Hint Health", ["hint", "hinthealth"]),
    ("Elation Health", ["elationhealth", "elation"]),
    ("Tebra", ["tebra"]),
    ("Cedar", ["cedar"]),
    ("LeanTaaS", ["leantaas"]),
    ("PerfectServe", ["perfectserve"]),
    ("Findhelp", ["findhelp"]),
    ("Honor", ["honor"]),
    ("Papa", ["papa"]),
    ("Unite Us", ["uniteus"]),
    ("Jukebox Health", ["jukeboxhealth"]),
    ("Homeward", ["homeward"]),
    ("WelbeHealth", ["welbehealth"]),
    ("Wellthy", ["wellthy"]),
    ("Wellth", ["wellth"]),
    ("Wheel", ["wheel"]),
    ("Maven", ["mavenclinic", "maven"]),
    ("Cleo", ["cleo"]),
    ("Thirty Madison", ["thirtymadison"]),
    ("Carrot Fertility", ["carrotfertility"]),
    ("Candid Health", ["candid", "candidhealth"]),
    ("Curative", ["curative"]),
    ("Cityblock Health", ["cityblock"]),
    ("Babylist", ["babylist"]),
    ("Found", ["found"]),
    ("Medallion", ["medallion"]),
    ("HealthSnap", ["healthsnap"]),
    ("ClosedLoop", ["closedloop", "closedloopai"]),
    ("Cohere Health", ["coherehealth", "cohere"]),
    ("Cedar Care", ["cedarcare"]),
    ("Oshi Health", ["oshi", "oshihealth"]),
    ("Season Health", ["seasonhealth", "season"]),
    ("Vida Health", ["vida", "vidahealth"]),
    ("Omada Health", ["omada", "omadahealth"]),
    ("Lark Health", ["lark", "larkhealth"]),
    ("Big Health", ["bighealth"]),
    ("Ginger", ["ginger", "gingerio"]),
    ("Cerebral", ["cerebral"]),
    ("Brightside Health", ["brightside", "brightsidehealth"]),
    ("CirrusMD", ["cirrusmd"]),
    ("98point6", ["98point6"]),
    ("Firefly Health", ["firefly", "fireflyhealth"]),
    ("Iora Health", ["iora", "iorahealth"]),
    ("Oak Street Health", ["oakstreethealth", "oakstreet"]),
    ("ChenMed", ["chenmed"]),
    ("VillageMD", ["village", "villagemd"]),
    ("One Medical", ["onemedical"]),
    ("Carbon Health", ["carbon", "carbonhealth"]),
    ("Forward", ["forward", "goforward"]),
    ("Parsley Health", ["parsleyhealth"]),
    ("Tia", ["tia"]),
    ("Hazel Health", ["hazel", "hazelhealth"]),
    ("SchoolCare", ["schoolcare"]),
    ("Bamboo Health", ["bamboohealth", "bamboo"]),
    ("Collective Medical", ["collectivemedical"]),
    ("PatientPing", ["patientping", "bamboohealth"]),
    ("Audacious Inquiry", ["audaciousinquiry", "aihealth"]),
    ("Lightbeam Health", ["lightbeam", "lightbeamhealth"]),
    ("Arcadia", ["arcadia", "arcadiahealth"]),
    ("ClosedLoop", ["closedloop"]),
    ("Persivia", ["persivia"]),
    ("ClosedLoop", ["closedloop"]),
    ("HealthVerity", ["healthverity"]),
    ("Datavant", ["datavant"]),
    ("Ciox Health", ["ciox", "cioxhealth"]),
    ("MRO", ["mro", "mrocorp"]),
    ("Verisma", ["verisma"]),
    ("Epion Health", ["epion", "epionhealth"]),
    ("Relatient", ["relatient"]),
    ("Luma", ["luma"]),
    ("Relatient", ["relatient"]),
    ("Kyruus", ["kyruus"]),
    ("Phreesia", ["phreesia"]),
    ("NexHealth", ["nexhealth"]),
    ("Symplr", ["symplr"]),
    ("Vocera", ["vocera", "stryker"]),
    ("PerfectServe", ["perfectserve"]),
    ("Spok", ["spok"]),
    ("TigerText", ["tigertext", "tigerconnect"]),
    ("QGenda", ["qgenda"]),
    ("Healthie", ["healthie"]),
    ("Awell", ["awell"]),
    ("DocASAP", ["docasap"]),
    ("Ribbon Health", ["ribbonhealth"]),
    ("Availity", ["availity"]),
    ("ModMed", ["modmed"]),
    ("Weave", ["weave"]),
    ("DrChrono", ["drchrono"]),
    ("Kareo", ["kareo"]),
    ("SimplePractice", ["simplepractice"]),
    ("AdvancedMD", ["advancedmd"]),
    ("NextGen", ["nextgen"]),
    ("CureMD", ["curemd"]),
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
    ("Waystar", ["waystar"]),
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
]


def configured_slugs() -> dict[str, set[str]]:
    grouped: dict[str, set[str]] = {
        "greenhouse": set(),
        "lever": set(),
        "ashby": set(),
        "workable": set(),
    }
    for row in load_companies():
        ats = row.get("ats", "").strip().casefold()
        slug = row.get("slug", "").strip()
        if ats in grouped and slug:
            grouped[ats].add(slug)
    return grouped


def probe(url: str, timeout: int = 10) -> tuple[bool, int]:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read())
        if "jobs" in data:
            return True, len(data["jobs"])
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


def slugify(name: str) -> str:
    return name.lower().replace(" ", "-").replace(".", "").replace("&", "and")


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

        # Skip if already in registry (apply script handles recategorization).
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
                "category": "Provider Operations",
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

    out_dir = Path(__file__).resolve().parents[1] / "data"
    verified_path = out_dir / "_provider_ops_verified.json"
    skipped_path = out_dir / "_provider_ops_skipped.json"
    verified_path.write_text(json.dumps(verified, indent=2), encoding="utf-8")
    skipped_path.write_text(json.dumps(skipped, indent=2), encoding="utf-8")
    print(f"\nVerified: {len(verified)}, Skipped: {len(skipped)}")


if __name__ == "__main__":
    main()
