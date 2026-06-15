"""
Configuration for the multi-ATS job collector.

Supported platforms
-------------------
- Greenhouse: https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs
- Lever:      https://api.lever.co/v0/postings/{site}?mode=json
- Ashby:      https://api.ashbyhq.com/posting-api/job-board/{job_board_name}

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
