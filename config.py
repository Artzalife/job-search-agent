"""
Configuration for the multi-ATS job collector.

Supported platforms
-------------------
- Greenhouse: https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs
- Lever:      https://api.lever.co/v0/postings/{site}?mode=json
- Ashby:      https://api.ashbyhq.com/posting-api/job-board/{job_board_name}
- Workable:   https://www.workable.com/api/accounts/{subdomain}?details=true
- Workday:    POST https://{tenant}.{wd_server}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs

Each company board is identified by a slug from its public careers URL.
Add or remove entries below to control which companies are searched.
"""

# Map of board_token → display name written to jobs.csv.
#
# Find a company's token from its Greenhouse careers URL:
#   https://boards.greenhouse.io/{board_token}
# Boards that return HTTP 404 have no public API feed (custom ATS, private board,
# or a non-Greenhouse-hosted careers page) — remove or replace those entries.
GREENHOUSE_BOARDS = {
    # General tech (original boards)
    "stripe": "Stripe",
    "figma": "Figma",
    "anthropic": "Anthropic",
    "airtable": "Airtable",
    "vercel": "Vercel",
    "brex": "Brex",
    "dropbox": "Dropbox",
    "coinbase": "Coinbase",
    "asana": "Asana",
    "webflow": "Webflow",
    # Digital health & healthtech
    "oscar": "Oscar Health",
    "komodohealth": "Komodo Health",
    "flatironhealth": "Flatiron Health",
    "omadahealth": "Omada Health",
    "pomelocare": "Pomelo Care",
    "zocdoc": "Zocdoc",
    "doximity": "Doximity",
    "collectivehealth": "Collective Health",
    "cloverhealth": "Clover Health",
    "amwell": "Amwell",
    "transcarent": "Transcarent",
    "khealthcareers": "K Health",
    "courierhealth": "Courier Health",
    "waymark": "Waymark",
    "healthverity": "HealthVerity",
    "rightwayhealthcare": "Rightway Healthcare",
    "sidecarhealth": "Sidecar Health",
    "strivehealth": "Strive Health",
    "galileo": "Galileo",
    "healthjoy": "HealthJoy",
    # Diagnostics, biotech & medtech
    "natera": "Natera",
    "veracyte": "Veracyte",
    "10xgenomics": "10x Genomics",
    "twistbioscience": "Twist Bioscience",
    "freenome": "Freenome",
    "billiontoone": "BillionToOne",
    "butterflynetwork": "Butterfly Network",
    "recursionpharmaceuticals": "Recursion",
    "pathai": "PathAI",
    "ginkgobioworks": "Ginkgo Bioworks",
    "beaconbiosignals": "Beacon Biosignals",
    "motifneurotech": "Motif Neurotech",
    "neuropace": "NeuroPace",
    "neuralink": "Neuralink",
    "compasspathways": "Compass Pathways",
    "clicktherapeutics": "Click Therapeutics",
    "genedx": "GeneDx",
    "adaptivebiotechnologies": "Adaptive Biotechnologies",
    "ultimagenomics": "Ultima Genomics",
    "parsebiosciences": "Parse Biosciences",
    "science37": "Science 37",
    "truveta": "Truveta",
    "qventus": "Qventus",
    "current": "Current Health",
    "letsgetchecked": "LetsGetChecked",
    # Behavioral health & care delivery
    "modernhealth": "Modern Health",
    "alma": "Alma",
    "bicyclehealth": "Bicycle Health",
    "formhealth": "Form Health",
    "instridehealth": "InStride Health",
    "suki": "Suki",
    "tia": "Tia",
    "plume": "Plume",
    "folxhealth": "Folx Health",
    "parsleyhealth": "Parsley Health",
    "honor": "Honor",
    "hazel": "Hazel Health",
    "carbon": "Carbon Health",
    "patientpoint": "PatientPoint",
    "vitablehealth": "Vitable Health",
    "village": "VillageMD",
    "thirtymadison": "Thirty Madison",
    "found": "Found",
    "candid": "Candid Health",
    "curative": "Curative",
    "babylist": "Babylist",
    # Diagnostics, biotech & medtech (additional)
    "beamtherapeutics": "Beam Therapeutics",
    "elementbiosciences": "Element Biosciences",
    "generatebiomedicines": "Generate Biomedicines",
    "relaytherapeutics": "Relay Therapeutics",
    "tesseratherapeutics": "Tessera Therapeutics",
    "florencehealthcare": "Florence Healthcare",
    "biofourmis": "Biofourmis",
    # Behavioral health & care delivery (additional)
    "betterhelp": "BetterHelp",
    "talkspace": "Talkspace",
    "cerebral": "Cerebral",
    "meruhealth": "Meru Health",
    "ww": "WeightWatchers",
    "springhealth66": "Spring Health",
    "octave": "Octave",
    "twochairs": "Two Chairs",
    "charliehealth": "Charlie Health",
    "onemedical": "One Medical",
    "forward": "Forward",
    # Additional verified Greenhouse boards (tech)
    "databricks": "Databricks",
    "mongodb": "MongoDB",
    "datadog": "Datadog",
    "okta": "Okta",
    "zscaler": "Zscaler",
    "roblox": "Roblox",
    "block": "Block",
    "airbnb": "Airbnb",
    "cloudflare": "Cloudflare",
    "elastic": "Elastic",
    "pinterest": "Pinterest",
    "scaleai": "Scale AI",
    "instacart": "Instacart",
    "riotgames": "Riot Games",
    "robinhood": "Robinhood",
    "affirm": "Affirm",
    "twilio": "Twilio",
    "reddit": "Reddit",
    "lyft": "Lyft",
    "gitlab": "GitLab",
    "epicgames": "Epic Games",
    "sofi": "SoFi",
    "fivetran": "Fivetran",
    "oura": "Oura",
    "gusto": "Gusto",
    "discord": "Discord",
    "chime": "Chime",
    "hightouch": "Hightouch",
    "duolingo": "Duolingo",
    "mercury": "Mercury",
    "amplitude": "Amplitude",
    "pagerduty": "PagerDuty",
    "singlestore": "SingleStore",
    "fastly": "Fastly",
    "heartflowinc": "HeartFlow",
    "launchdarkly": "LaunchDarkly",
    "cockroachlabs": "Cockroach Labs",
    "marqeta": "Marqeta",
    "mixpanel": "Mixpanel",
    "betterment": "Betterment",
    "khanacademy": "Khan Academy",
    "labelbox": "Labelbox",
    "planetscale": "PlanetScale",
    "coursera": "Coursera",
    "stabilityai": "Stability AI",
    "masterclass": "MasterClass",
    "netlify": "Netlify",
    "calm": "Calm",
}

# Lever site slugs → display name (jobs.lever.co/{slug}).
# Healthcare/medtech boards listed first.
LEVER_BOARDS = {
  # Digital health & healthtech
  "lyrahealth": "Lyra Health",
  "includedhealth": "Included Health",
  "ro": "Ro",
  "swordhealth": "Sword Health",
  "aledade": "Aledade",
  "nomihealth": "Nomi Health",
  "form": "Form Health",
  "plume": "Plume",
  "florence": "Florence Healthcare",
  # Diagnostics, biotech & medtech
  "veeva": "Veeva",
  "grailbio": "GRAIL",
  "relay": "Relay Therapeutics",
  "h1": "H1",
  # Wellness & devices
  "whoop": "WHOOP",
}

# Ashby job board slugs → display name (jobs.ashbyhq.com/{slug}).
# Healthcare/medtech boards listed first.
ASHBY_BOARDS = {
  # Digital health & healthtech
  "headway": "Headway",
  "abridge": "Abridge",
  "ambiencehealthcare": "Ambience Healthcare",
  "notable": "Notable Health",
  "virtahealth": "Virta Health",
  "nabla": "Nabla",
  "cedar": "Cedar",
  "collective": "Collective Health",
  "candidhealth": "Candid Health",
  "capsule": "Capsule",
  "vitable": "Vitable Health",
  "found": "Found",
  "hatch": "Hatch",
  "levels": "Levels",
  # Diagnostics, biotech & medtech
  "benchling": "Benchling",
  "insitro": "Insitro",
  "owkin": "Owkin",
  "generate": "Generate Biomedicines",
  "adaptive": "Adaptive Biotechnologies",
  "relay": "Relay Therapeutics",
  "beam": "Beam Therapeutics",
  # Wellness & devices
  "whoop": "WHOOP",
}

# Workable account subdomains → display name (apply.workable.com/{subdomain}).
# Healthcare/medtech boards listed first.
WORKABLE_BOARDS = {
    "editas": "Editas Medicine",
    "steadymd": "SteadyMD",
    "accuragen": "AccuraGen",
    "drug-hunter": "Drug Hunter",
    "cambridge-healthcare-research": "Cambridge Healthcare Research",
    "sokol-gxp-serivces": "SOKOL GxP Services",
}

# Workday career sites → display name and API routing metadata.
# Find tenant/site from the company's myworkdayjobs.com careers URL:
#   https://{tenant}.{wd_server}.myworkdayjobs.com/{site}/...
# Healthcare/medtech boards listed first. Large boards (e.g. CVS) are omitted
# to keep run times reasonable.
WORKDAY_BOARDS = {
    "medtronic": {
        "name": "Medtronic",
        "wd_server": "wd1",
        "site": "MedtronicCareers",
    },
    "pfizer": {
        "name": "Pfizer",
        "wd_server": "wd1",
        "site": "PfizerCareers",
    },
    "stryker": {
        "name": "Stryker",
        "wd_server": "wd1",
        "site": "StrykerCareers",
    },
    "novartis": {
        "name": "Novartis",
        "wd_server": "wd3",
        "site": "Novartis_Careers",
    },
    "gsk": {
        "name": "GSK",
        "wd_server": "wd5",
        "site": "GSKCareers",
    },
    "gilead": {
        "name": "Gilead",
        "wd_server": "wd1",
        "site": "gileadcareers",
    },
    "sanofi": {
        "name": "Sanofi",
        "wd_server": "wd3",
        "site": "SanofiCareers",
    },
    "humana": {
        "name": "Humana",
        "wd_server": "wd5",
        "site": "Humana_External_Career_Site",
    },
    "centene": {
        "name": "Centene",
        "wd_server": "wd5",
        "site": "Centene_External",
    },
    "baxter": {
        "name": "Baxter",
        "wd_server": "wd1",
        "site": "Baxter",
    },
    "dexcom": {
        "name": "Dexcom",
        "wd_server": "wd1",
        "site": "Dexcom",
    },
    "iqvia": {
        "name": "IQVIA",
        "wd_server": "wd1",
        "site": "IQVIA",
    },
}

# Job titles must contain at least one of these phrases (case-insensitive).
TITLE_INCLUDES = [
    "Product Designer",
    "Product Design",
    "UX Designer",
    "UI Designer",
    "UX/UI Designer",
    "UI/UX Designer",
]

# Job titles containing any of these phrases are excluded (case-insensitive).
TITLE_EXCLUDES = [
    "Staff",
    "Principal",
    "Lead",
    "Director",
    "Manager",
    "Intern",
    "Internship",
    "Junior",
    "Student",
    "Recruiter",
]

# Only jobs classified as fully remote are written to the CSV.
LOCATION_TYPES_INCLUDED = ("Remote",)

# Output file for collected jobs.
OUTPUT_CSV = "jobs.csv"

# Root folder for archived job description Markdown files.
DESCRIPTIONS_DIR = "job_descriptions"

# Greenhouse Job Board API base URL (public, read-only, no authentication).
GREENHOUSE_API_BASE = "https://boards-api.greenhouse.io/v1/boards"

# Lever Postings API base URL (public, read-only, no authentication).
LEVER_API_BASE = "https://api.lever.co/v0/postings"

# Ashby Job Postings API base URL (public, read-only, no authentication).
ASHBY_API_BASE = "https://api.ashbyhq.com/posting-api/job-board"

# Workable public account API base URL (public, read-only, no authentication).
WORKABLE_API_BASE = "https://www.workable.com/api/accounts"
