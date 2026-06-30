#!/usr/bin/env python3
"""Batch-probe Clinical AI candidate slugs across supported ATS APIs."""

from __future__ import annotations

import csv
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
    ("Hippocratic AI", ["hippocraticai", "hippocratic"]),
    ("Freed", ["freed", "getfreed", "freedhealth"]),
    ("DeepScribe", ["deepscribe"]),
    ("Glass Health", ["glasshealth", "glasshealthinc"]),
    ("Viz.ai", ["vizai", "viz"]),
    ("Artera", ["artera", "arteraai"]),
    ("Infinitus", ["infinitus", "infinitusai"]),
    ("Rad AI", ["radai", "rad"]),
    ("Sirona Medical", ["sironamedical", "sirona"]),
    ("Paige", ["paige", "paigeai"]),
    ("Proscia", ["proscia"]),
    ("Ibex Medical Analytics", ["ibex", "ibexmedical"]),
    ("Lunit", ["lunit"]),
    ("Cleerly", ["cleerly"]),
    ("CardioLogs", ["cardiologs"]),
    ("Eko Health", ["eko", "ekohealth"]),
    ("Kheiron Medical", ["kheiron"]),
    ("Enlitic", ["enlitic"]),
    ("Riverain Technologies", ["riverain", "riveraintech"]),
    ("RapidAI", ["rapidai"]),
    ("Subtle Medical", ["subtlemedical"]),
    ("Quibim", ["quibim"]),
    ("Fathom", ["fathom", "fathomhealth"]),
    ("Eleos Health", ["eleos", "eleoshealth"]),
    ("Akido Labs", ["akido", "akidolabs"]),
    ("ClosedLoop AI", ["closedloop", "closedloopai"]),
    ("Evidation", ["evidation"]),
    ("Atomwise", ["atomwise"]),
    ("Exscientia", ["exscientia"]),
    ("BenevolentAI", ["benevolentai", "benevolent"]),
    ("Caption Health", ["captionhealth", "caption"]),
    ("Imagen Technologies", ["imagen", "imagentech"]),
    ("Avicenna.AI", ["avicenna", "avicennaai"]),
    ("Paradigm Health", ["paradigm", "paradigmhealth"]),
    ("Syllable", ["syllable", "syllablehealth"]),
    ("Hyro", ["hyro"]),
    ("Fabric Health", ["fabric", "fabrichealth"]),
    ("Curai Health", ["curai", "curaihealth"]),
    ("Memora Health", ["memora", "memorahealth"]),
    ("Avo", ["avo", "avomd"]),
    ("Autonomize AI", ["autonomize", "autonomizeai"]),
    ("Pieces Technologies", ["pieces", "piecestech"]),
    ("Atropos Health", ["atropos", "atroposhealth"]),
    ("Diagnostic Robotics", ["diagnosticrobotics", "diagnostic-robotics"]),
    ("Kintsugi", ["kintsugi", "kintsugihealth"]),
    ("Docbot", ["docbot", "docbotai"]),
    ("Infermedica", ["infermedica"]),
    ("Qure.ai", ["qureai", "qure"]),
    ("Annalise.ai", ["annalise", "annaliseai"]),
    ("Harrison.ai", ["harrison", "harrisonai"]),
    ("Aetion", ["aetion"]),
    ("Sophia Genetics", ["sophiagenetics", "sophia"]),
    ("Color Health", ["color", "colorhealth"]),
    ("Tandem Health", ["tandem", "tandemhealth"]),
    ("Biobeat", ["biobeat"]),
    ("Glooko", ["glooko"]),
    ("Blackford Analysis", ["blackford", "blackfordanalysis"]),
    ("iCAD", ["icad", "icadmed"]),
    ("Digital Diagnostics", ["digitaldiagnostics"]),
    ("Gestalt Diagnostics", ["gestalt", "gestaltdiagnostics"]),
    ("Imagene", ["imagene", "imageneai"]),
    ("Presagen", ["presagen"]),
    ("Nucleai", ["nucleai"]),
    ("Turbine AI", ["turbine", "turbineai"]),
    ("Roam Analytics", ["roam", "roamanalytics"]),
    ("Syntegra", ["syntegra"]),
    ("Parlay Health", ["parlay", "parlayhealth"]),
    ("Celsius Health", ["celsius", "celsiushealth"]),
    ("Ellie Health", ["ellie", "elliehealth"]),
    ("Noom", ["noom"]),
    ("Calibrate", ["calibrate", "calibratehealth"]),
    ("98point6", ["98point6", "ninetyeightpoint6"]),
    ("Babylon Health", ["babylon", "babylonhealth"]),
    ("Perspectum", ["perspectum"]),
    ("Contextflow", ["contextflow"]),
    ("Volocare", ["volocare", "volo"]),
    ("AIMedics", ["aimedics", "aimed"]),
    ("Springbok AI", ["springbok", "springbokai"]),
    ("SomaLogic", ["somalogic"]),
    ("Verantos", ["verantos"]),
    ("Huma", ["huma", "humae"]),
    ("SmarterDx", ["smarterdx"]),
    ("Health Catalyst", ["healthcatalyst"]),
    ("Innovaccer", ["innovaccer"]),
    ("H1", ["h1"]),
    ("Commure", ["commure"]),
    ("AKASA", ["akasa"]),
    ("Wheel", ["wheel"]),
    ("Metriport", ["metriport"]),
    ("Particle Health", ["particlehealth"]),
    ("Zus Health", ["zushealth"]),
    ("Redox", ["redox"]),
    ("Health Gorilla", ["healthgorilla"]),
    ("AcuityMD", ["acuitymd"]),
    ("Iterative Health", ["iterativehealth"]),
    ("Benchling", ["benchling"]),
    ("Insitro", ["insitro"]),
    ("Owkin", ["owkin"]),
    ("HeartFlow", ["heartflowinc"]),
    ("Biofourmis", ["biofourmis"]),
    ("Butterfly Network", ["butterflynetwork"]),
    ("Recursion Pharmaceuticals", ["recursionpharmaceuticals"]),
    ("Freenome", ["freenome"]),
    ("Flatiron Health", ["flatironhealth"]),
    ("Komodo Health", ["komodohealth"]),
    ("Truveta", ["truveta"]),
    ("Definitive Healthcare", ["definitivehc"]),
    ("Verge Genomics", ["vergegenomics"]),
    ("Isomorphic Labs", ["isomorphiclabs"]),
    ("Xaira Therapeutics", ["xairatherapeutics"]),
    ("Inceptive", ["inceptive"]),
    ("Generate Biomedicines", ["generatebiomedicines", "generate"]),
    ("Relay Therapeutics", ["relaytherapeutics", "relay"]),
    ("Beam Therapeutics", ["beamtherapeutics", "beam"]),
    ("Prime Medicine", ["primemedicine"]),
    ("Verve Therapeutics", ["verve"]),
    ("Legend Biotech", ["legendcareers"]),
    ("Integrated Biosciences", ["integratedbiosciencesinc"]),
    ("Form Bio", ["formbio"]),
    ("Qualio", ["qualio"]),
    ("Dotmatics", ["dotmatics"]),
    ("Ketryx", ["ketryx"]),
    ("Florence Healthcare", ["florencehealthcare", "florence"]),
    ("Science 37", ["science37"]),
    ("Quince Therapeutics", ["quince"]),
    ("Garner Health", ["garnerhealth"]),
    ("Covera Health", ["coverahealth"]),
    ("1upHealth", ["1uphealth"]),
    ("Seer", ["seer"]),
    ("Canopy", ["canopycare"]),
    ("Mantra Health", ["mantrahealth", "mantra"]),
    ("Tomorrow Health", ["tomorrow"]),
    ("Boulder Care", ["bouldercare"]),
    ("LetsGetChecked", ["letsgetchecked"]),
    ("Current Health", ["current"]),
    ("Outset Medical", ["outsetmedical", "outset"]),
    ("Neuralink", ["neuralink"]),
    ("Compass Pathways", ["compasspathways"]),
    ("Motif Neurotech", ["motifneurotech"]),
    ("NeuroPace", ["neuropace"]),
    ("Ginkgo Bioworks", ["ginkgobioworks"]),
    ("Parse Biosciences", ["parsebiosciences"]),
    ("Tessera Therapeutics", ["tesseratherapeutics"]),
    ("Element Biosciences", ["elementbiosciences"]),
    ("Ultima Genomics", ["ultimagenomics"]),
    ("GeneDx", ["genedx"]),
    ("Adaptive Biotechnologies", ["adaptivebiotechnologies", "adaptive"]),
    ("Natera", ["natera"]),
    ("Veracyte", ["veracyte"]),
    ("10x Genomics", ["10xgenomics"]),
    ("Twist Bioscience", ["twistbioscience"]),
    ("BillionToOne", ["billiontoone"]),
    ("Personalis", ["personalisinc"]),
    ("GRAIL", ["grailbio"]),
    ("Exact Sciences", ["exactsciences"]),
    ("Guardant Health", ["guardanthealth"]),
    ("Tempus", ["tempus"]),
    ("Myriad Genetics", ["myriad", "myriadgenetics"]),
    ("Invitae", ["invitae"]),
    ("Foundation Medicine", ["foundationmedicine"]),
    ("Caris Life Sciences", ["caris", "carislifesciences"]),
    ("NeoGenomics", ["neogenomics"]),
    ("Castle Biosciences", ["castlebiosciences"]),
    ("Synthego", ["synthego"]),
    ("Everlywell", ["everlywell"]),
    ("WHOOP", ["whoop"]),
    ("Oura", ["oura"]),
    ("Align Technology", ["align"]),
    ("Dexcom", ["dexcom"]),
    ("Medtronic", ["medtronic"]),
    ("Stryker", ["stryker"]),
    ("Baxter", ["baxter"]),
    ("IDEXX", ["idexx"]),
    ("Pfizer", ["pfizer"]),
    ("Novartis", ["novartis"]),
    ("GSK", ["gsk"]),
    ("Gilead", ["gilead"]),
    ("Sanofi", ["sanofi"]),
    ("IQVIA", ["iqvia"]),
    ("Veeva", ["veeva"]),
    ("Canvas Medical", ["canvasmedical"]),
    ("Elation Health", ["elationhealth"]),
    ("Hint Health", ["hint"]),
    ("PointClickCare", ["pointclickcare"]),
    ("WellSky", ["wellsky"]),
    ("Netsmart", ["ntst"]),
    ("MatrixCare", ["matrixcare"]),
    ("Waystar", ["waystar"]),
    ("R1 RCM", ["r1rcm"]),
    ("Cedar", ["cedar"]),
    ("Headway", ["headway"]),
    ("Cityblock Health", ["cityblock"]),
    ("Wellth", ["wellth"]),
    ("Sonera Health", ["sonera", "sonerahealth"]),
    ("Talkiatry", ["talkiatry"]),
    ("SonderMind", ["sondermind"]),
    ("Rula", ["rula"]),
    ("Equip", ["equip"]),
    ("Medallion", ["medallion"]),
    ("Capsule", ["capsule"]),
    ("Found", ["found"]),
    ("Hatch", ["hatch"]),
    ("Levels", ["levels"]),
    ("Virta Health", ["virtahealth"]),
    ("Aledade", ["aledade"]),
    ("Nomi Health", ["nomihealth"]),
    ("Sword Health", ["swordhealth"]),
    ("Lyra Health", ["lyrahealth"]),
    ("Included Health", ["includedhealth"]),
    ("Ro", ["ro"]),
    ("Maven Clinic", ["mavenclinic"]),
    ("Carrot Fertility", ["carrotfertility"]),
    ("Cleo", ["cleo"]),
    ("Thirty Madison", ["thirtymadison"]),
    ("Candid Health", ["candid", "candidhealth"]),
    ("Curative", ["curative"]),
    ("Babylist", ["babylist"]),
    ("Findhelp", ["findhelp"]),
    ("LeanTaaS", ["leantaas"]),
    ("PerfectServe", ["perfectserve"]),
    ("Moxe", ["moxehealth"]),
    ("Medrio", ["medrio"]),
    ("MedeAnalytics", ["medeanalytics"]),
    ("Axuall", ["axuall"]),
    ("Medispend", ["medispend"]),
    ("SteadyMD", ["steadymd"]),
    ("Editas Medicine", ["editas"]),
    ("Drug Hunter", ["drug-hunter"]),
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
        if key in seen_names or key in existing_names:
            continue
        seen_names.add(key)

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
                "category": "Clinical AI",
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
    verified_path = out_dir / "_clinical_ai_verified.json"
    skipped_path = out_dir / "_clinical_ai_skipped.json"
    verified_path.write_text(json.dumps(verified, indent=2), encoding="utf-8")
    skipped_path.write_text(json.dumps(skipped, indent=2), encoding="utf-8")
    print(f"\nVerified: {len(verified)}, Skipped: {len(skipped)}")


if __name__ == "__main__":
    main()
