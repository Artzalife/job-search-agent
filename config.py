"""
Configuration for the multi-ATS job collector.

Supported platforms
-------------------
- Greenhouse: https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs
- Lever:      https://api.lever.co/v0/postings/{site}?mode=json
- Ashby:      https://api.ashbyhq.com/posting-api/job-board/{job_board_name}
- Workable:   https://www.workable.com/api/accounts/{subdomain}?details=true
- Workday:    POST https://{tenant}.{wd_server}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs

Company boards are defined in data/companies.csv. Edit that file to add or
remove companies; this module loads enabled rows into the board dicts below.
"""

from __future__ import annotations

import csv
from pathlib import Path

COMPANIES_CSV = Path(__file__).resolve().parent / "data" / "companies.csv"

VALID_ATS = frozenset({"greenhouse", "lever", "ashby", "workable", "workday"})
VALID_CATEGORIES = frozenset({
    "Clinical AI",
    "EHR",
    "Provider Operations",
    "Population Health",
    "Healthcare Infrastructure",
    "Revenue Cycle",
    "Medical Devices",
    "Diagnostics",
    "Clinical Research",
    "Healthcare Analytics",
    "Healthcare CRM",
    "Veterinary",
    "Behavioral Health",
    "Employer Health",
    "General Tech",
    "Fintech",
    "HR Tech",
    "Cybersecurity",
    "Payer Operations",
    "Pharmacy",
})


def _is_enabled(value: str) -> bool:
    return value.strip().casefold() in {"yes", "y", "true", "1"}


def load_companies() -> list[dict[str, str]]:
    """Load all company rows from the operational registry CSV."""
    if not COMPANIES_CSV.exists():
        raise FileNotFoundError(f"Company registry not found: {COMPANIES_CSV}")

    with COMPANIES_CSV.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def load_boards() -> tuple[
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, dict],
]:
    """
    Build ATS board dicts from data/companies.csv.

    Returns GREENHOUSE_BOARDS, LEVER_BOARDS, ASHBY_BOARDS, WORKABLE_BOARDS,
    and WORKDAY_BOARDS in the shapes expected by job_scraper.py.
    """
    greenhouse: dict[str, str] = {}
    lever: dict[str, str] = {}
    ashby: dict[str, str] = {}
    workable: dict[str, str] = {}
    workday: dict[str, dict] = {}

    for row in load_companies():
        if not _is_enabled(row.get("enabled", "")):
            continue

        ats = row.get("ats", "").strip().casefold()
        slug = row.get("slug", "").strip()
        name = row.get("display_name", "").strip()
        if not ats or not slug or not name:
            continue

        if ats == "greenhouse":
            greenhouse[slug] = name
        elif ats == "lever":
            lever[slug] = name
        elif ats == "ashby":
            ashby[slug] = name
        elif ats == "workable":
            workable[slug] = name
        elif ats == "workday":
            workday[slug] = {
                "name": name,
                "wd_server": row.get("wd_server", "").strip(),
                "site": row.get("workday_site", "").strip(),
            }

    return greenhouse, lever, ashby, workable, workday


GREENHOUSE_BOARDS, LEVER_BOARDS, ASHBY_BOARDS, WORKABLE_BOARDS, WORKDAY_BOARDS = (
    load_boards()
)

# Job titles must contain at least one of these phrases (case-insensitive).
TITLE_INCLUDES = [
    "Product Designer",
    "Product Design",
    "UX Designer",
    "UI Designer",
    "UX/UI Designer",
    "UI/UX Designer",
    "Experience Designer",
    "Product Experience Designer",
    "Senior Experience Designer",
    "Service Designer",
    "Senior Service Designer",
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

# When True, jobs.csv only grows: existing rows are preserved across runs and new
# apply_urls are appended. Closed or stale postings are not auto-removed.
PRESERVE_EXISTING_JOBS = True

# Free-text filter passed to Workday job search API (searchText). Narrows large
# boards before title/location filtering. Set to "" to fetch all open postings.
WORKDAY_SEARCH_TEXT = "product designer"

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
