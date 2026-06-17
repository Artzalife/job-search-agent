#!/usr/bin/env python3
"""Probe healthcare/medtech companies across all supported ATS platforms."""

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
    GREENHOUSE_BOARDS,
    LEVER_API_BASE,
    LEVER_BOARDS,
    ASHBY_BOARDS,
    WORKABLE_API_BASE,
    WORKABLE_BOARDS,
    WORKDAY_BOARDS,
)

HEADERS = {"Accept": "application/json", "User-Agent": "job-search-agent/1.0"}

# slug -> display name candidates (healthcare, medtech, biotech, diagnostics)
CANDIDATES = {
    "tempus": "Tempus", "flatiron": "Flatiron Health", "flatironhealth": "Flatiron Health",
    "guardant": "Guardant Health", "guardanthealth": "Guardant Health",
    "exactsciences": "Exact Sciences", "grail": "GRAIL", "grailbio": "GRAIL",
    "invitae": "Invitae", "myriad": "Myriad Genetics", "genedx": "GeneDx",
    "color": "Color Health", "colorhealth": "Color Health",
    "neogenomics": "NeoGenomics", "foundationmedicine": "Foundation Medicine",
    "caris": "Caris Life Sciences", "personalis": "Personalis",
    "illumina": "Illumina", "pacbio": "PacBio", "nanostring": "NanoString",
    "singularity": "Singular Genomics", "ultimagenomics": "Ultima Genomics",
    "elementbiosciences": "Element Biosciences", "benchling": "Benchling",
    "ginkgo": "Ginkgo Bioworks", "ginkgobioworks": "Ginkgo Bioworks",
    "insitro": "Insitro", "recursion": "Recursion", "recursionpharmaceuticals": "Recursion",
    "owkin": "Owkin", "pathai": "PathAI", "proscia": "Proscia", "paige": "Paige",
    "somalogic": "SomaLogic", "natera": "Natera", "veracyte": "Veracyte",
    "freenome": "Freenome", "billiontoone": "BillionToOne", "twistbioscience": "Twist Bioscience",
    "twist": "Twist Bioscience", "10xgenomics": "10x Genomics", "parsebiosciences": "Parse Biosciences",
    "synthego": "Synthego", "mammothbiosciences": "Mammoth Biosciences",
    "arborbiotechnologies": "Arbor Biotechnologies", "inscripta": "Inscripta",
    "scalebio": "Scale Biosciences", "bionano": "Bionano Genomics",
    "beamtherapeutics": "Beam Therapeutics", "beam": "Beam Therapeutics",
    "editas": "Editas Medicine", "intellia": "Intellia Therapeutics",
    "crispr": "CRISPR Therapeutics", "sana": "Sana Biotechnology",
    "moderna": "Moderna", "modernatx": "Moderna", "biontech": "BioNTech",
    "alnylam": "Alnylam Pharmaceuticals", "bluebirdbio": "bluebird bio",
    "vertex": "Vertex Pharmaceuticals", "regeneron": "Regeneron",
    "biogen": "Biogen", "amgen": "Amgen", "gilead": "Gilead Sciences",
    "veeva": "Veeva", "medidata": "Medidata", "iqvia": "IQVIA",
    "medpace": "Medpace", "parexel": "Parexel", "syneos": "Syneos Health",
    "icon": "ICON", "labcorp": "Labcorp", "quest": "Quest Diagnostics",
    "dexcom": "Dexcom", "insulet": "Insulet", "tandemdiabetes": "Tandem Diabetes",
    "medtronic": "Medtronic", "abbott": "Abbott", "bostonscientific": "Boston Scientific",
    "stryker": "Stryker", "zimmerbiomet": "Zimmer Biomet", "edwards": "Edwards Lifesciences",
    "intuitive": "Intuitive Surgical", "butterflynetwork": "Butterfly Network",
    "hologic": "Hologic", "bd": "BD", "biofourmis": "Biofourmis",
    "currenthealth": "Current Health", "current": "Current Health",
    "heartflow": "HeartFlow", "heartflowinc": "HeartFlow",
    "viz": "Viz.ai", "vizai": "Viz.ai", "aidoc": "Aidoc", "qventus": "Qventus",
    "philips": "Philips", "gehealthcare": "GE HealthCare",
    "siemenshealthineers": "Siemens Healthineers",
    "teladoc": "Teladoc", "amwell": "Amwell", "mdlive": "MDLive",
    "includedhealth": "Included Health", "grandrounds": "Included Health",
    "accolade": "Accolade", "devoted": "Devoted Health", "devotedhealth": "Devoted Health",
    "alignmenthealthcare": "Alignment Healthcare", "agilonhealth": "Agilon Health",
    "signifyhealth": "Signify Health", "somatus": "Somatus", "cityblock": "Cityblock Health",
    "oakstreethealth": "Oak Street Health", "hatch": "Hatch", "alto": "Alto Pharmacy",
    "capsule": "Capsule", "goodrx": "GoodRx", "hims": "Hims & Hers",
    "ro": "Ro", "nurx": "Nurx", "everlywell": "Everlywell",
    "letsgetchecked": "LetsGetChecked", "nourish": "Nourish",
    "virtahealth": "Virta Health", "virta": "Virta Health",
    "omadahealth": "Omada Health", "noom": "Noom", "found": "Found",
    "plume": "Plume", "folxhealth": "Folx Health", "tia": "Tia",
    "parsleyhealth": "Parsley Health", "onemedical": "One Medical",
    "forward": "Forward", "crossoverhealth": "Crossover Health",
    "wheel": "Wheel", "nabla": "Nabla", "suki": "Suki", "augmedix": "Augmedix",
    "notable": "Notable Health", "abridge": "Abridge", "deepscribe": "DeepScribe",
    "ambiencehealthcare": "Ambience Healthcare", "athelas": "Athelas",
    "healthgorilla": "Health Gorilla", "particlehealth": "Particle Health",
    "redox": "Redox", "healthcatalyst": "Health Catalyst", "innovaccer": "Innovaccer",
    "flexpa": "Flexpa", "metriport": "Metriport", "zushealth": "Zus Health",
    "bamboohealth": "Bamboo Health", "ribbonhealth": "Ribbon Health",
    "turquoisehealth": "Turquoise Health", "h1": "H1", "komodohealth": "Komodo Health",
    "truveta": "Truveta", "datavant": "Datavant", "nomihealth": "Nomi Health",
    "sidecarhealth": "Sidecar Health", "rightwayhealthcare": "Rightway Healthcare",
    "strivehealth": "Strive Health", "courierhealth": "Courier Health",
    "waymark": "Waymark", "pomelocare": "Pomelo Care", "khealthcareers": "K Health",
    "healthverity": "HealthVerity", "collectivehealth": "Collective Health",
    "cloverhealth": "Clover Health", "oscar": "Oscar Health",
    "candidhealth": "Candid Health", "candid": "Candid Health",
    "honor": "Honor", "hazel": "Hazel Health", "carbon": "Carbon Health",
    "village": "VillageMD", "patientpoint": "PatientPoint",
    "florencehealthcare": "Florence Healthcare", "medable": "Medable",
    "science37": "Science 37", "verily": "Verily", "23andme": "23andMe",
    "helix": "Helix", "generatebiomedicines": "Generate Biomedicines",
    "generate": "Generate Biomedicines", "relaytherapeutics": "Relay Therapeutics",
    "relay": "Relay Therapeutics", "tesseratherapeutics": "Tessera Therapeutics",
    "florence": "Florence Healthcare", "akili": "Akili Interactive",
    "clicktherapeutics": "Click Therapeutics", "peartherapeutics": "Pear Therapeutics",
    "bighealth": "Big Health", "woebothealth": "Woebot Health",
    "springhealth66": "Spring Health", "springhealth": "Spring Health",
    "headway": "Headway", "lyrahealth": "Lyra Health", "alma": "Alma",
    "betterhelp": "BetterHelp", "talkspace": "Talkspace", "cerebral": "Cerebral",
    "charliehealth": "Charlie Health", "octave": "Octave", "twochairs": "Two Chairs",
    "growtherapy": "Grow Therapy", "talkiatry": "Talkiatry", "equip": "Equip",
    "modernhealth": "Modern Health", "meruhealth": "Meru Health",
    "bicyclehealth": "Bicycle Health", "formhealth": "Form Health",
    "instridehealth": "InStride Health", "hingehealth": "Hinge Health",
    "swordhealth": "Sword Health", "levels": "Levels", "functionhealth": "Function Health",
    "whoop": "WHOOP", "oura": "Oura", "calm": "Calm", "weightwatchers": "WeightWatchers",
    "beaconbiosignals": "Beacon Biosignals", "motifneurotech": "Motif Neurotech",
    "neuropace": "NeuroPace", "neuralink": "Neuralink", "compasspathways": "Compass Pathways",
    "sagetherapeutics": "Sage Therapeutics", "neurocrine": "Neurocrine Biosciences",
    "acadia": "Acadia Pharmaceuticals", "exactsciences": "Exact Sciences",
    "adaptivebiotechnologies": "Adaptive Biotechnologies", "adaptive": "Adaptive Biotechnologies",
    "steadymd": "SteadyMD", "accuragen": "AccuraGen", "drug-hunter": "Drug Hunter",
    "cambridge-healthcare-research": "Cambridge Healthcare Research",
    "sokol-gxp-serivces": "SOKOL GxP Services", "aledade": "Aledade",
    "cedar": "Cedar", "vitable": "Vitable Health", "vitablehealth": "Vitable Health",
    "transcarent": "Transcarent", "galileo": "Galileo", "healthjoy": "HealthJoy",
    "zocdoc": "Zocdoc", "doximity": "Doximity", "pomelo": "Pomelo Care",
    "curative": "Curative", "thirtymadison": "Thirty Madison", "babylist": "Babylist",
    "carbonhealth": "Carbon Health", "honorcare": "Honor", "fireflyhealth": "Firefly Health",
    "firefly": "Firefly Health", "canopy": "Canopy", "agilon": "Agilon Health",
    "signify": "Signify Health", "brighthealth": "Bright Health",
    "elevancehealth": "Elevance Health", "cvshealth": "CVS Health",
    "anthem": "Elevance Health", "cigna": "Cigna", "molina": "Molina Healthcare",
    "lilly": "Eli Lilly", "merck": "Merck", "novartis": "Novartis",
    "roche": "Roche", "gsk": "GSK", "sanofi": "Sanofi", "pfizer": "Pfizer",
    "astrazeneca": "AstraZeneca", "bms": "Bristol Myers Squibb", "abbvie": "AbbVie",
    "baxter": "Baxter", "baxterhealthcare": "Baxter", "danaher": "Danaher",
    "thermofisher": "Thermo Fisher Scientific", "perkinelmer": "PerkinElmer",
    "waters": "Waters Corporation", "agilent": "Agilent", "beckman": "Beckman Coulter",
    "resmed": "ResMed", "align": "Align Technology", "dexcom": "Dexcom",
    "guardanthealth": "Guardant Health", "exact": "Exact Sciences",
    "myriadgenetics": "Myriad Genetics", "neogenomics": "NeoGenomics",
    "bioreference": "BioReference Laboratories", "arup": "ARUP Laboratories",
    "mayo": "Mayo Clinic", "clevelandclinic": "Cleveland Clinic",
    "providence": "Providence", "kaiserpermanente": "Kaiser Permanente",
    "hcahealthcare": "HCA Healthcare", "tenethealth": "Tenet Healthcare",
    "ascension": "Ascension", "commonspirit": "CommonSpirit Health",
    "sutterhealth": "Sutter Health", "northwell": "Northwell Health",
    "intermountain": "Intermountain Health", "bannerhealth": "Banner Health",
    "mckesson": "McKesson", "cardinalhealth": "Cardinal Health",
    "cencora": "Cencora", "amerisourcebergen": "AmerisourceBergen",
    "walgreens": "Walgreens", "riteaid": "Rite Aid", "cvs": "CVS Health",
    "unitedhealthgroup": "UnitedHealth Group", "optum": "Optum",
    "cambia": "Cambia Health", "premera": "Premera Blue Cross",
    "highmark": "Highmark Health", "bluecross": "Blue Cross Blue Shield",
    "exscientia": "Exscientia", "schrodinger": "Schrodinger",
    "atomwise": "Atomwise", "benevolentai": "BenevolentAI",
    "tempuslabs": "Tempus", "flatiron": "Flatiron Health",
    "grailbio": "GRAIL", "personalis": "Personalis",
    "seer": "Seer", "somabio": "SomaLogic", "nautilus": "Nautilus Biotechnology",
    "oxfordnanopore": "Oxford Nanopore", "dovetailgenomics": "Dovetail Genomics",
    "cytiva": "Cytiva", "pall": "Pall Corporation", "beckmancoulter": "Beckman Coulter",
    "cerner": "Oracle Health", "epic": "Epic", "athenahealth": "athenahealth",
    "tebra": "Tebra", "eclinicalworks": "eClinicalWorks",
    "canvas": "Canvas Medical", "akido": "Akido", "commure": "Commure",
    "rula": "Rula", "boulder": "Boulder Care", "bouldercare": "Boulder Care",
    "mantra": "Mantra Health", "mantrahealth": "Mantra Health",
    "cerebral": "Cerebral", "done": "Done", "mindbloom": "Mindbloom",
    "fieldtrip": "Field Trip Health", "atai": "atai Life Sciences",
    "mindmed": "MindMed", "garner": "Garner Health", "garnerhealth": "Garner Health",
    "tomorrow": "Tomorrow Health", "tomorrowhealth": "Tomorrow Health",
    "rightway": "Rightway Healthcare", "collective": "Collective Health",
    "sidecar": "Sidecar Health", "strive": "Strive Health", "courier": "Courier Health",
    "khealth": "K Health", "pomelo": "Pomelo Care", "cityblockhealth": "Cityblock Health",
    "devotedhealth": "Devoted Health", "clover": "Clover Health",
    "bright": "Bright Health", "agilon": "Agilon Health", "somatus": "Somatus",
    "oakstreet": "Oak Street Health", "canopycare": "Canopy",
    "empiric": "Empiric Health", "empirichealth": "Empiric Health",
    "bamboo": "Bamboo Health", "healthie": "Healthie", "wheelhealth": "Wheel",
    "smile": "Smile Digital Health", "smilecdr": "Smile Digital Health",
    "1uphealth": "1upHealth", "1up": "1upHealth", "flexpa": "Flexpa",
    "zus": "Zus Health", "ribbon": "Ribbon Health", "turquoise": "Turquoise Health",
    "komodo": "Komodo Health", "nomi": "Nomi Health", "form": "Form Health",
    "folx": "Folx Health", "parsley": "Parsley Health", "plume": "Plume",
    "foundhealth": "Found", "season": "Season Health", "seasonhealth": "Season Health",
    "nourish": "Nourish", "calibrate": "Calibrate", "weightwatchers": "WeightWatchers",
    "ww": "WeightWatchers", "noom": "Noom", "livongo": "Livongo",
    "withings": "Withings", "ihealth": "iHealth Labs", "ihealthlabs": "iHealth Labs",
    "insidetracker": "InsideTracker", "insidetracker": "InsideTracker",
    "humanapi": "Human API", "humanapi": "Human API",
    "covera": "Covera Health", "coverahealth": "Covera Health",
    "aetion": "Aetion", "komodohealth": "Komodo Health",
    "flatiron": "Flatiron Health", "tempus": "Tempus",
    "sword": "Sword Health", "hinge": "Hinge Health", "kaia": "Kaia Health",
    "bioventus": "Bioventus", "organogenesis": "Organogenesis",
    "outset": "Outset Medical", "outsetmedical": "Outset Medical",
    "irhythm": "iRhythm Technologies", "irhythmtech": "iRhythm Technologies",
    "masimo": "Masimo", "hillrom": "Hillrom", "baxter": "Baxter",
    "haemonetics": "Haemonetics", "nuvera": "Nuvera Biosciences",
    "guardian": "Guardant Health", "exact": "Exact Sciences",
}

WORKDAY_CANDIDATES = [
    ("medtronic", "wd1", "MedtronicCareers", "Medtronic"),
    ("pfizer", "wd1", "PfizerCareers", "Pfizer"),
    ("stryker", "wd1", "StrykerCareers", "Stryker"),
    ("novartis", "wd3", "Novartis_Careers", "Novartis"),
    ("gsk", "wd5", "GSKCareers", "GSK"),
    ("gilead", "wd1", "gileadcareers", "Gilead"),
    ("sanofi", "wd3", "SanofiCareers", "Sanofi"),
    ("humana", "wd5", "Humana_External_Career_Site", "Humana"),
    ("centene", "wd5", "Centene_External", "Centene"),
    ("baxter", "wd1", "Baxter", "Baxter"),
    ("dexcom", "wd1", "Dexcom", "Dexcom"),
    ("iqvia", "wd1", "IQVIA", "IQVIA"),
    ("johnsonandjohnson", "wd1", "External", "Johnson & Johnson"),
    ("johnsonandjohnson", "wd1", "JNJ", "Johnson & Johnson"),
    ("abbott", "wd5", "abbott", "Abbott"),
    ("bostonscientific", "wd1", "bostonscientific", "Boston Scientific"),
    ("medtronic", "wd1", "MedtronicCareers", "Medtronic"),
    ("zimmerbiomet", "wd5", "ZimmerBiomet", "Zimmer Biomet"),
    ("edwards", "wd5", "Edwards", "Edwards Lifesciences"),
    ("intuitive", "wd1", "Intuitive", "Intuitive Surgical"),
    ("bd", "wd1", "BDExternalSite", "BD"),
    ("bectondickinson", "wd1", "BDExternalSite", "BD"),
    ("danaher", "wd1", "DanaherCareers", "Danaher"),
    ("thermofisher", "wd5", "ThermoFisherScientific", "Thermo Fisher"),
    ("merck", "wd5", "Merck_Careers", "Merck"),
    ("lilly", "wd5", "LillyCareers", "Eli Lilly"),
    ("amgen", "wd1", "AmgenCareers", "Amgen"),
    ("biogen", "wd1", "biogen", "Biogen"),
    ("regeneron", "wd1", "Regeneron", "Regeneron"),
    ("vertex", "wd1", "VertexPharmaceuticals", "Vertex"),
    ("modernatx", "wd1", "Moderna", "Moderna"),
    ("illumina", "wd1", "illumina", "Illumina"),
    ("agilent", "wd5", "Agilent", "Agilent"),
    ("waters", "wd1", "Waters", "Waters"),
    ("perkinelmer", "wd1", "PerkinElmer", "PerkinElmer"),
    ("resmed", "wd3", "ResMed", "ResMed"),
    ("align", "wd1", "AlignTechnology", "Align Technology"),
    ("insulet", "wd1", "Insulet", "Insulet"),
    ("haemonetics", "wd1", "Haemonetics", "Haemonetics"),
    ("masimo", "wd1", "Masimo", "Masimo"),
    ("gehealthcare", "wd5", "GEHC_External_Site", "GE HealthCare"),
    ("philips", "wd3", "Philips_Careers", "Philips"),
    ("siemens", "wd1", "Siemens_Careers", "Siemens Healthineers"),
    ("teladoc", "wd1", "Teladoc", "Teladoc"),
    ("veeva", "wd1", "Veeva", "Veeva"),
    ("medpace", "wd1", "Medpace", "Medpace"),
    ("parexel", "wd1", "Parexel", "Parexel"),
    ("syneos", "wd1", "SyneosHealth", "Syneos Health"),
    ("icon", "wd3", "ICON", "ICON"),
    ("labcorp", "wd1", "Labcorp", "Labcorp"),
    ("questdiagnostics", "wd1", "QuestDiagnostics", "Quest Diagnostics"),
    ("cvshealth", "wd1", "CVS_Health_Careers", "CVS Health"),
    ("walgreens", "wd1", "External", "Walgreens"),
    ("unitedhealthgroup", "wd5", "UHGExternal", "UnitedHealth Group"),
    ("optum", "wd5", "optum", "Optum"),
    ("cigna", "wd5", "cigna", "Cigna"),
    ("elevancehealth", "wd1", "ElevanceHealth", "Elevance Health"),
    ("anthem", "wd1", "Anthem", "Anthem"),
    ("molina", "wd5", "MolinaHealthcare", "Molina Healthcare"),
    ("hcahealthcare", "wd1", "HCAHealthcare", "HCA Healthcare"),
    ("tenethealth", "wd5", "TenetHealthcare", "Tenet Healthcare"),
    ("ascension", "wd1", "Ascension", "Ascension"),
    ("commonspirit", "wd1", "CommonSpirit", "CommonSpirit Health"),
    ("providence", "wd5", "ProvidenceExternal", "Providence"),
    ("kaiserpermanente", "wd1", "KP", "Kaiser Permanente"),
    ("mckesson", "wd1", "McKesson", "McKesson"),
    ("cardinalhealth", "wd1", "CardinalHealth", "Cardinal Health"),
    ("cencora", "wd1", "Cencora", "Cencora"),
    ("bms", "wd5", "BMS", "Bristol Myers Squibb"),
    ("abbvie", "wd5", "abbvie", "AbbVie"),
    ("astrazeneca", "wd3", "astrazeneca", "AstraZeneca"),
    ("roche", "wd3", "roche", "Roche"),
    ("takeda", "wd1", "Takeda", "Takeda"),
    ("bayer", "wd3", "BayerCareers", "Bayer"),
    ("novonordisk", "wd1", "NovoNordisk", "Novo Nordisk"),
]


def probe_greenhouse(slug: str) -> tuple[bool, int, str]:
    url = f"{GREENHOUSE_API_BASE}/{slug}/jobs"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        jobs = data.get("jobs", [])
        name = data.get("meta", {}).get("company_name") or slug
        return True, len(jobs), name
    except urllib.error.HTTPError:
        return False, 0, slug
    except (urllib.error.URLError, TimeoutError, OSError):
        return False, -1, slug


def probe_lever(slug: str) -> tuple[bool, int, str]:
    url = f"{LEVER_API_BASE}/{slug}?mode=json"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        if isinstance(data, list):
            return True, len(data), slug
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
        pass
    return False, 0, slug


def probe_ashby(slug: str) -> tuple[bool, int, str]:
    url = f"{ASHBY_API_BASE}/{slug}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        jobs = data.get("jobs", [])
        return True, len(jobs), slug
    except (urllib.error.HTTPError, urllib.error.URLError):
        return False, 0, slug


def probe_workable(slug: str) -> tuple[bool, int, str]:
    url = f"{WORKABLE_API_BASE}/{slug}?details=true"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        jobs = data.get("jobs", [])
        name = data.get("name") or slug
        return True, len(jobs), name
    except urllib.error.HTTPError as e:
        if e.code == 429:
            time.sleep(2)
        return False, 0, slug
    except urllib.error.URLError:
        return False, -1, slug


def probe_workday(tenant: str, wd: str, site: str) -> tuple[bool, int]:
    url = f"https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    body = json.dumps({"appliedFacets": {}, "limit": 5, "offset": 0, "searchText": ""}).encode()
    try:
        req = urllib.request.Request(
            url, data=body, method="POST",
            headers={**HEADERS, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read())
        return True, data.get("total", 0)
    except (urllib.error.HTTPError, urllib.error.URLError):
        return False, 0


def main() -> None:
    existing_gh = set(GREENHOUSE_BOARDS.keys())
    existing_lever = set(LEVER_BOARDS.keys())
    existing_ashby = set(ASHBY_BOARDS.keys())
    existing_workable = set(WORKABLE_BOARDS.keys())
    existing_workday = set(WORKDAY_BOARDS.keys())

    new_gh: list[tuple[str, str, int]] = []
    new_lever: list[tuple[str, str, int]] = []
    new_ashby: list[tuple[str, str, int]] = []
    new_workable: list[tuple[str, str, int]] = []
    new_workday: list[tuple[str, dict]] = []

    seen: set[str] = set()
    for slug, name in CANDIDATES.items():
        if slug in seen:
            continue
        seen.add(slug)

        if slug not in existing_gh:
            ok, count, display = probe_greenhouse(slug)
            if ok:
                new_gh.append((slug, display if display != slug else name, count))

        if slug not in existing_lever:
            ok, count, _ = probe_lever(slug)
            if ok:
                new_lever.append((slug, name, count))

        if slug not in existing_ashby:
            ok, count, _ = probe_ashby(slug)
            if ok:
                new_ashby.append((slug, name, count))

        if slug not in existing_workable:
            ok, count, display = probe_workable(slug)
            if ok:
                new_workable.append((slug, display if display != slug else name, count))
            time.sleep(0.3)

    seen_wd: set[tuple[str, str, str]] = set()
    for tenant, wd, site, name in WORKDAY_CANDIDATES:
        key = (tenant, wd, site)
        if key in seen_wd or tenant in existing_workday:
            continue
        seen_wd.add(key)
        ok, total = probe_workday(tenant, wd, site)
        if ok and total > 0:
            new_workday.append((tenant, {
                "name": name,
                "wd_server": wd,
                "site": site,
                "_total": total,
            }))

    new_gh.sort(key=lambda x: (-x[2], x[1]))
    new_lever.sort(key=lambda x: (-x[2], x[1]))
    new_ashby.sort(key=lambda x: (-x[2], x[1]))
    new_workable.sort(key=lambda x: (-x[2], x[1]))
    new_workday.sort(key=lambda x: -x[1]["_total"])

    print("=== NEW GREENHOUSE BOARDS ===")
    for slug, name, count in new_gh:
        print(f'    "{slug}": "{name}",  # {count}')

    print(f"\n=== NEW LEVER BOARDS ({len(new_lever)}) ===")
    for slug, name, count in new_lever:
        print(f'  "{slug}": "{name}",  # {count}')

    print(f"\n=== NEW ASHBY BOARDS ({len(new_ashby)}) ===")
    for slug, name, count in new_ashby:
        print(f'  "{slug}": "{name}",  # {count}')

    print(f"\n=== NEW WORKABLE BOARDS ({len(new_workable)}) ===")
    for slug, name, count in new_workable:
        print(f'    "{slug}": "{name}",  # {count}')

    print(f"\n=== NEW WORKDAY BOARDS ({len(new_workday)}) ===")
    for tenant, board in new_workday:
        total = board.pop("_total")
        print(f'    "{tenant}": {{')
        print(f'        "name": "{board["name"]}",')
        print(f'        "wd_server": "{board["wd_server"]}",')
        print(f'        "site": "{board["site"]}",')
        print(f"    }},  # {total}")

    print(f"\nTotals: GH={len(new_gh)} Lever={len(new_lever)} Ashby={len(new_ashby)} "
          f"Workable={len(new_workable)} Workday={len(new_workday)}")


if __name__ == "__main__":
    main()
