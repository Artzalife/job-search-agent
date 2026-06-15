"""
Configuration for the Greenhouse ATS job collector (v1).

Greenhouse board identifiers
----------------------------
Each company on Greenhouse has a public job board identified by a *board token*
(the slug in their careers URL). For example:

    https://boards.greenhouse.io/stripe  →  board token is "stripe"

The collector uses these tokens with the public Job Board API (no API key required).
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
# Seniority levels (Staff, Principal, Lead) are intentionally kept so all IC
# product design roles are captured.
TITLE_EXCLUDES = [
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

# Greenhouse Job Board API base URL (public, read-only, no authentication).
GREENHOUSE_API_BASE = "https://boards-api.greenhouse.io/v1/boards"
