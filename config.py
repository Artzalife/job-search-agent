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
}

# Job titles must contain at least one of these phrases (case-insensitive).
TITLE_INCLUDES = [
    "Product Designer",
    "Senior Product Designer",
    "UX Designer",
    "Senior UX Designer",
    "UX/UI Designer",
    "Senior UX/UI Designer",
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
]

# Only jobs with these location_type values are written to the CSV.
LOCATION_TYPES_INCLUDED = ("Remote", "Ambiguous")

# Output file for collected jobs.
OUTPUT_CSV = "jobs.csv"

# Greenhouse Job Board API base URL (public, read-only, no authentication).
GREENHOUSE_API_BASE = "https://boards-api.greenhouse.io/v1/boards"
