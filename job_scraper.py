#!/usr/bin/env python3
"""
Multi-ATS job collector.

Collects Product Design job postings from configured Greenhouse, Lever, Ashby,
Workable, and Workday public job boards and writes matching results to jobs.csv.

Supported public APIs (no authentication required)
---------------------------------------------------
Greenhouse:
    GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs

Lever:
    GET https://api.lever.co/v0/postings/{site}?mode=json

Ashby:
    GET https://api.ashbyhq.com/posting-api/job-board/{job_board_name}

Workable:
    GET https://www.workable.com/api/accounts/{subdomain}?details=true

Workday:
    POST https://{tenant}.{wd_server}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs
    GET  https://{tenant}.{wd_server}.myworkdayjobs.com/wday/cxs/{tenant}/{site}{externalPath}

We fetch every open job from each configured board, filter titles against the
include/exclude rules in config.py, classify each location, keep only Remote
roles, archive first-time job descriptions as Markdown, deduplicate by
apply_url, and append new matches to jobs.csv (existing rows preserved by default).

Run:
    python3 job_scraper.py
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import socket
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

from config import (
    ASHBY_API_BASE,
    ASHBY_BOARDS,
    DESCRIPTIONS_DIR,
    GREENHOUSE_API_BASE,
    GREENHOUSE_BOARDS,
    LEVER_API_BASE,
    LEVER_BOARDS,
    LOCATION_TYPES_INCLUDED,
    OUTPUT_CSV,
    PRESERVE_EXISTING_JOBS,
    TITLE_EXCLUDES,
    TITLE_INCLUDES,
    WORKABLE_API_BASE,
    WORKABLE_BOARDS,
    WORKDAY_BOARDS,
    WORKDAY_SEARCH_TEXT,
)

CSV_COLUMNS = [
    "Company",
    "Title",
    "Apply URL",
    "Experience",
    "Category",
    "Location",
    "Location Type",
    "Date Found",
    "Description File",
]

MISSING_DESCRIPTION_PLACEHOLDER = "_No description available._"

_LEGACY_CSV_ALIASES = {
    "company": "Company",
    "title": "Title",
    "apply_url": "Apply URL",
    "experience": "Experience",
    "category": "Category",
    "location": "Location",
    "location_type": "Location Type",
    "date_found": "Date Found",
    "description_file": "Description File",
}


def normalize_csv_row(row: dict) -> dict:
    """Map legacy column names and ensure every output column is present."""
    normalized: dict[str, str] = {}
    for key, value in row.items():
        canonical = _LEGACY_CSV_ALIASES.get(key, key)
        if value is None:
            normalized[canonical] = ""
        else:
            normalized[canonical] = str(value)
    for column in CSV_COLUMNS:
        normalized.setdefault(column, "")
    return {column: normalized[column] for column in CSV_COLUMNS}

REMOTE_KEYWORDS = ("remote", "work from home")
NORTH_AMERICA_REMOTE_REGIONS = frozenset({
    "us / canada",
    "us/canada",
    "usa / canada",
    "united states / canada",
    "north america",
})
MULTI_ARRANGEMENT_MARKERS = ("•", " / ", " or ", ";", " & ", " and ")
INTERNATIONAL_MARKERS = (
    "ireland",
    "united kingdom",
    ", israel",
    ", uk",
    ", united kingdom",
    ", canada",
    ", germany",
    ", france",
    ", india",
    ", ireland",
    ", australia",
    ", singapore",
    ", japan",
    ", spain",
    ", netherlands",
    ", sweden",
    ", brazil",
    ", mexico",
    ", poland",
    ", portugal",
    ", switzerland",
    ", italy",
    ", china",
    ", korea",
    ", taiwan",
    "tel aviv",
    "london,",
    "dublin,",
    "berlin,",
    "paris,",
    "toronto,",
    "vancouver,",
    "montreal,",
    "emea",
    "apac",
    "latam",
    "europe",
)
US_STATE_ABBREVS = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC",
}
US_STATE_NAMES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york",
    "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington",
    "west virginia", "wisconsin", "wyoming", "district of columbia",
}
OFFICE_LOCATION_RE = re.compile(
    r"^[A-Za-z .'-]+,\s*([A-Z]{2}|[A-Za-z .'-]+)$"
)
GREENHOUSE_BOARD_JOB_RE = re.compile(
    r"https?://(?:boards|job-boards)\.greenhouse\.io/(?P<board>[^/]+)/jobs/(?P<job_id>\d+)",
    re.I,
)
GREENHOUSE_GH_JID_RE = re.compile(r"[?&]gh_jid=(?P<job_id>\d+)", re.I)
LEVER_POSTING_RE = re.compile(
    r"https?://jobs\.lever\.co/(?P<site>[^/]+)/(?P<posting_id>[0-9a-f-]{36})",
    re.I,
)
ASHBY_POSTING_RE = re.compile(
    r"https?://jobs\.ashbyhq\.com/(?P<board>[^/]+)/(?P<posting_id>[0-9a-f-]{36})",
    re.I,
)
WORKABLE_POSTING_RE = re.compile(
    r"https?://apply\.workable\.com/j/(?P<shortcode>[A-Z0-9]+)",
    re.I,
)
WORKDAY_POSTING_RE = re.compile(
    r"https?://(?P<tenant>[^.]+)\.(?P<wd>wd\d+)\.myworkdayjobs\.com/(?P<site>[^/]+)(?P<path>/job/.+)",
    re.I,
)


def title_matches(title: str) -> bool:
    """Return True if the title passes include and exclude filters."""
    normalized = title.casefold()
    if any(excluded.casefold() in normalized for excluded in TITLE_EXCLUDES):
        return False
    return any(included.casefold() in normalized for included in TITLE_INCLUDES)


def classify_location(location: str) -> str:
    """
    Classify a location string into Remote, Hybrid, Office, International, or Ambiguous.

    Rules (evaluated in order):
      Hybrid        — contains "hybrid" (checked before remote keywords)
      Remote        — contains "remote" or "work from home", or a North
                      America region label such as "US / Canada"
      Ambiguous     — contains "United States", US-based multi-location options,
                      empty/unclear text, or otherwise undetermined remote status
      International — clearly outside the United States
      Office        — US city/state location only
    """
    text = location.strip()
    normalized = text.casefold()

    if not text:
        return "Ambiguous"

    if "hybrid" in normalized:
        return "Hybrid"

    compact = re.sub(r"\s+", " ", normalized)
    if compact in NORTH_AMERICA_REMOTE_REGIONS:
        return "Remote"

    if any(keyword in normalized for keyword in REMOTE_KEYWORDS):
        return "Remote"

    if "united states" in normalized:
        return "Ambiguous"

    has_multi_arrangement = any(marker in text for marker in MULTI_ARRANGEMENT_MARKERS)
    if has_multi_arrangement and _has_us_reference(normalized):
        return "Ambiguous"

    if _is_international(normalized):
        return "International"

    if has_multi_arrangement:
        return "Ambiguous"

    if _is_us_city_state_only(text, normalized):
        return "Office"

    return "Ambiguous"


def _has_us_reference(normalized: str) -> bool:
    """Return True when a location string references the United States."""
    if "united states" in normalized:
        return True
    if re.search(r"\busa\b", normalized):
        return True
    if re.search(r"\bu\.s\.a?\.?\b", normalized):
        return True
    if re.search(r"(?<![a-z])us(?![a-z])", normalized):
        return True
    return False


def _is_international(normalized: str) -> bool:
    """Return True when the location clearly refers to a non-US work site."""
    if any(marker in normalized for marker in INTERNATIONAL_MARKERS):
        return True
    if re.search(r"\b(?!united states\b)(?:[a-z]+(?: [a-z]+)?),\s*[a-z]{2,}\b", normalized):
        # "City, Country" patterns such as "Paris, France" that are not US states.
        match = re.search(r",\s*([a-z][a-z .'-]+)$", normalized)
        if match:
            region = match.group(1).strip()
            if region not in US_STATE_NAMES and region not in {
                abbr.casefold() for abbr in US_STATE_ABBREVS
            }:
                if region not in {"usa", "u.s.", "u.s.a.", "us", "united states"}:
                    return True
    return False


def _is_us_city_state_only(text: str, normalized: str) -> bool:
    """Return True for a single US city and/or state with no broader country context."""
    if OFFICE_LOCATION_RE.match(text):
        suffix = text.split(",", 1)[1].strip()
        if suffix.upper() in US_STATE_ABBREVS:
            return True
        if suffix.casefold() in US_STATE_NAMES:
            return True

    # Single US city name with no country, remote, or multi-location markers.
    if "," not in text and normalized not in {"remote", "hybrid"}:
        return True

    # "City, State" repeated style such as "New York, New York".
    parts = [part.strip() for part in text.split(",")]
    if len(parts) == 2 and all(parts):
        second = parts[1]
        if second.upper() in US_STATE_ABBREVS or second.casefold() in US_STATE_NAMES:
            return True

    return False


def location_is_included(location_type: str) -> bool:
    """Return True when a classified location should be kept in the CSV."""
    return location_type in LOCATION_TYPES_INCLUDED


def empty_stats() -> dict[str, int]:
    """Return a fresh stats counter dict."""
    return {
        "retrieved": 0,
        "matching_title": 0,
        "excluded_by_title": 0,
        "excluded_by_location": 0,
    }


def merge_stats(total: dict[str, int], added: dict[str, int]) -> None:
    """Add source-specific stats into the running total."""
    for key in total:
        total[key] += added[key]


def fetch_json(url: str) -> object:
    """Fetch and parse JSON from a public job board API endpoint."""
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "job-search-agent/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except (TimeoutError, socket.timeout) as exc:
        raise urllib.error.URLError("timed out") from exc


def fetch_json_post(url: str, payload: dict) -> object:
    """POST JSON to a public job board API endpoint and parse the response."""
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "job-search-agent/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except (TimeoutError, socket.timeout) as exc:
        raise urllib.error.URLError("timed out") from exc


def fetch_json_allow_404(url: str) -> tuple[int, object | None]:
    """Fetch JSON and return (status_code, payload). Payload is None on HTTP errors."""
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "job-search-agent/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except urllib.error.URLError:
        return -1, None


def greenhouse_board_tokens() -> set[str]:
    """Return configured Greenhouse board tokens for posting verification."""
    return set(GREENHOUSE_BOARDS.keys())


def is_greenhouse_job_active(board_token: str, job_id: str) -> bool | None:
    """Return True when a Greenhouse job still exists on a board API."""
    url = f"{GREENHOUSE_API_BASE}/{board_token}/jobs/{job_id}"
    status, _payload = fetch_json_allow_404(url)
    if status == 200:
        return True
    if status == 404:
        return False
    return None


def is_lever_posting_active(site_slug: str, posting_id: str) -> bool | None:
    """Return True when a Lever posting is still published."""
    url = f"{LEVER_API_BASE}/{site_slug}?mode=json"
    status, payload = fetch_json_allow_404(url)
    if status != 200 or not isinstance(payload, list):
        return None
    return any(posting.get("id") == posting_id for posting in payload)


def is_ashby_posting_active(board_slug: str, posting_id: str) -> bool | None:
    """Return True when an Ashby posting is still published."""
    url = f"{ASHBY_API_BASE}/{board_slug}"
    status, payload = fetch_json_allow_404(url)
    if status != 200 or not isinstance(payload, dict):
        return None
    for job in payload.get("jobs", []):
        apply_url = (job.get("applyUrl") or job.get("jobUrl") or "").strip()
        if posting_id in apply_url:
            return True
    return False


def is_workable_posting_active(subdomain: str, shortcode: str) -> bool | None:
    """Return True when a Workable posting is still published."""
    url = f"{WORKABLE_API_BASE}/{subdomain}?details=true"
    status, payload = fetch_json_allow_404(url)
    if status != 200 or not isinstance(payload, dict):
        return None
    for job in payload.get("jobs", []):
        if (job.get("shortcode") or "").strip().upper() == shortcode.upper():
            return True
    return False


def is_workday_posting_active(tenant: str, wd_server: str, site: str, path: str) -> bool | None:
    """Return True when a Workday posting detail endpoint still responds."""
    detail_url = workday_job_detail_url(tenant, wd_server, site, path)
    status, payload = fetch_json_allow_404(detail_url)
    if status == 200 and isinstance(payload, dict):
        return bool(payload.get("jobPostingInfo"))
    if status == 404:
        return False
    return None


def is_posting_active(apply_url: str, company: str = "") -> bool | None:
    """
    Check whether a job posting is still open using ATS-specific public APIs.

    Returns True when active, False when closed, or None when the status
    cannot be determined (network/API errors).
    """
    match = GREENHOUSE_BOARD_JOB_RE.search(apply_url)
    if match:
        return is_greenhouse_job_active(match.group("board"), match.group("job_id"))

    gh_jid_match = GREENHOUSE_GH_JID_RE.search(apply_url)
    if gh_jid_match:
        job_id = gh_jid_match.group("job_id")
        boards_to_try: list[str] = []
        company_key = company.casefold().replace(" ", "")
        if company_key in greenhouse_board_tokens():
            boards_to_try.append(company_key)
        host = urllib.parse.urlparse(apply_url).netloc.casefold()
        if "pinterest" in host and "pinterest" not in boards_to_try:
            boards_to_try.append("pinterest")
        if not boards_to_try:
            return None
        for board_token in boards_to_try:
            active = is_greenhouse_job_active(board_token, job_id)
            if active is not None:
                return active
        return None

    match = LEVER_POSTING_RE.search(apply_url)
    if match:
        return is_lever_posting_active(match.group("site"), match.group("posting_id"))

    match = ASHBY_POSTING_RE.search(apply_url)
    if match:
        return is_ashby_posting_active(match.group("board"), match.group("posting_id"))

    match = WORKABLE_POSTING_RE.search(apply_url)
    if match:
        shortcode = match.group("shortcode")
        for subdomain in WORKABLE_BOARDS:
            active = is_workable_posting_active(subdomain, shortcode)
            if active is True:
                return True
        return False

    match = WORKDAY_POSTING_RE.search(apply_url)
    if match:
        return is_workday_posting_active(
            match.group("tenant"),
            match.group("wd"),
            match.group("site"),
            match.group("path"),
        )

    return None


def fetch_greenhouse_jobs(board_token: str) -> list[dict]:
    """Fetch all published jobs for a Greenhouse board, including descriptions."""
    url = f"{GREENHOUSE_API_BASE}/{board_token}/jobs?content=true"
    payload = fetch_json(url)
    return payload.get("jobs", [])


def fetch_lever_jobs(site_slug: str) -> list[dict]:
    """Fetch all published jobs for a Lever careers site."""
    url = f"{LEVER_API_BASE}/{site_slug}?mode=json"
    payload = fetch_json(url)
    return payload if isinstance(payload, list) else []


def fetch_ashby_jobs(board_slug: str) -> list[dict]:
    """Fetch all published jobs for an Ashby job board."""
    url = f"{ASHBY_API_BASE}/{board_slug}"
    payload = fetch_json(url)
    return payload.get("jobs", [])


def fetch_workable_jobs(subdomain: str) -> list[dict]:
    """Fetch all published jobs for a Workable account, including descriptions."""
    url = f"{WORKABLE_API_BASE}/{subdomain}?details=true"
    payload = fetch_json(url)
    return payload.get("jobs", [])


def workday_jobs_url(tenant: str, wd_server: str, site: str) -> str:
    """Build the Workday CXS job search endpoint for a career site."""
    host = f"{tenant}.{wd_server}.myworkdayjobs.com"
    return f"https://{host}/wday/cxs/{tenant}/{site}/jobs"


def workday_job_detail_url(tenant: str, wd_server: str, site: str, external_path: str) -> str:
    """Build the Workday CXS job detail endpoint for a posting."""
    host = f"{tenant}.{wd_server}.myworkdayjobs.com"
    return f"https://{host}/wday/cxs/{tenant}/{site}{external_path}"


def workday_apply_url(tenant: str, wd_server: str, site: str, external_path: str) -> str:
    """Build the public apply URL for a Workday posting summary."""
    host = f"{tenant}.{wd_server}.myworkdayjobs.com"
    return f"https://{host}/{site}{external_path}"


def fetch_workday_jobs(
    tenant: str,
    wd_server: str,
    site: str,
    search_text: str | None = None,
) -> list[dict]:
    """Fetch published job summaries for a Workday career site."""
    if search_text is None:
        search_text = WORKDAY_SEARCH_TEXT
    url = workday_jobs_url(tenant, wd_server, site)
    jobs: list[dict] = []
    offset = 0
    limit = 20
    total: int | None = None

    while True:
        payload = fetch_json_post(
            url,
            {
                "appliedFacets": {},
                "limit": limit,
                "offset": offset,
                "searchText": search_text,
            },
        )
        batch = payload.get("jobPostings", [])
        if not batch:
            break

        page_total = payload.get("total")
        if page_total and total is None:
            total = page_total

        jobs.extend(batch)
        offset += limit
        if total and offset >= total:
            break
        if len(batch) < limit:
            break

    return jobs


def fetch_workday_job_detail(
    tenant: str,
    wd_server: str,
    site: str,
    external_path: str,
) -> dict:
    """Fetch full posting details for a Workday job summary."""
    url = workday_job_detail_url(tenant, wd_server, site, external_path)
    payload = fetch_json(url)
    return payload.get("jobPostingInfo", {})


def extract_greenhouse_location(job: dict) -> str:
    """Pull a human-readable location string from a Greenhouse job object."""
    location = job.get("location") or {}
    return location.get("name", "").strip()


def extract_lever_location(job: dict) -> str:
    """Pull a human-readable location string from a Lever posting."""
    categories = job.get("categories") or {}
    location = categories.get("location", "").strip()
    if location:
        return location
    all_locations = categories.get("allLocations") or []
    return ", ".join(loc.strip() for loc in all_locations if loc.strip())


def extract_ashby_location(job: dict) -> str:
    """Pull a human-readable location string from an Ashby posting."""
    return job.get("location", "").strip()


def extract_workable_location(job: dict) -> str:
    """Pull a human-readable location string from a Workable posting."""
    location = (job.get("location") or "").strip()
    if location:
        return location

    parts: list[str] = []
    for entry in job.get("locations") or []:
        if entry.get("hidden"):
            continue
        city = (entry.get("city") or "").strip()
        region = (entry.get("region") or "").strip()
        country = (entry.get("country") or "").strip()
        if city and region:
            parts.append(f"{city}, {region}")
        elif city and country:
            parts.append(f"{city}, {country}")
        elif city:
            parts.append(city)

    if parts:
        return "; ".join(parts)

    city = (job.get("city") or "").strip()
    country = (job.get("country") or "").strip()
    if city and country:
        return f"{city}, {country}"
    return city or country


def extract_workday_location(job_summary: dict, job_detail: dict | None = None) -> str:
    """Pull a human-readable location string from Workday list/detail payloads."""
    if job_detail:
        detail_location = (job_detail.get("location") or "").strip()
        if detail_location:
            return detail_location

    return (job_summary.get("locationsText") or "").strip()


def html_to_text(value: str) -> str:
    """Convert HTML job descriptions to readable plain text."""
    text = html.unescape(value)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p>", "\n\n", text, flags=re.I)
    text = re.sub(r"</li>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_greenhouse_description(job: dict) -> str:
    """Extract plain-text description from a Greenhouse job object."""
    content = job.get("content", "")
    return html_to_text(content) if content else ""


def extract_lever_description(job: dict) -> str:
    """Extract plain-text description from a Lever posting."""
    for field in ("descriptionPlain", "description"):
        value = job.get(field, "")
        if value:
            if field == "description":
                return html_to_text(value)
            return value.strip()
    return ""


def extract_ashby_description(job: dict) -> str:
    """Extract plain-text description from an Ashby posting."""
    plain = job.get("descriptionPlain", "")
    if plain:
        return plain.strip()
    html_value = job.get("descriptionHtml", "")
    return html_to_text(html_value) if html_value else ""


def extract_workable_description(job: dict) -> str:
    """Extract plain-text description from a Workable posting."""
    description = job.get("description", "")
    return html_to_text(description) if description else ""


def extract_workday_description(job_detail: dict) -> str:
    """Extract plain-text description from a Workday job detail payload."""
    description = job_detail.get("jobDescription", "")
    return html_to_text(description) if description else ""


def slugify(value: str) -> str:
    """Lowercase a string and replace spaces with hyphens for filenames."""
    normalized = value.casefold()
    normalized = re.sub(r"[^\w\s-]", "", normalized)
    normalized = re.sub(r"[\s_]+", "-", normalized.strip())
    normalized = re.sub(r"-+", "-", normalized)
    return normalized


def description_filename(company: str, title: str, captured_on: date) -> str:
    """Build the Markdown filename for an archived job description."""
    date_slug = captured_on.strftime("%m-%d-%y")
    return f"{slugify(company)}_{slugify(title)}_{date_slug}.md"


def description_markdown(
    title: str,
    company: str,
    location: str,
    apply_url: str,
    captured_on: str,
    description: str,
) -> str:
    """Render the archived job description as Markdown."""
    body = description.strip() if description.strip() else MISSING_DESCRIPTION_PLACEHOLDER
    return (
        f"# {title}\n\n"
        f"Company: {company}\n"
        f"Location: {location}\n"
        f"URL: {apply_url}\n"
        f"Date Captured: {captured_on}\n\n"
        f"## Full Job Description\n\n"
        f"{body}\n"
    )


def archive_job_description(
    job: dict,
    descriptions_root: Path,
    existing_paths_by_url: dict[str, str],
) -> tuple[str, bool]:
    """
    Save a job description Markdown file when the job is first discovered.

    Returns the relative path and whether a new file was written. Existing
    files are never overwritten or deleted, including when a posting later
    closes and is removed from jobs.csv.
    """
    apply_url = job["Apply URL"]
    if apply_url in existing_paths_by_url:
        return existing_paths_by_url[apply_url], False

    captured_on = date.fromisoformat(job["Date Found"])
    year_dir = descriptions_root / str(captured_on.year)
    year_dir.mkdir(parents=True, exist_ok=True)

    filename = description_filename(job["Company"], job["Title"], captured_on)
    relative_path = Path(DESCRIPTIONS_DIR) / str(captured_on.year) / filename
    absolute_path = descriptions_root / str(captured_on.year) / filename

    if absolute_path.exists():
        url_hash = hashlib.sha256(apply_url.encode("utf-8")).hexdigest()[:8]
        stem = absolute_path.stem
        hashed_name = f"{stem}-{url_hash}{absolute_path.suffix}"
        absolute_path = absolute_path.with_name(hashed_name)
        relative_path = relative_path.with_name(hashed_name)

    if absolute_path.exists():
        return str(relative_path).replace("\\", "/"), False

    markdown = description_markdown(
        title=job["Title"],
        company=job["Company"],
        location=job["Location"],
        apply_url=apply_url,
        captured_on=job["Date Found"],
        description=job.get("description", ""),
    )
    absolute_path.write_text(markdown, encoding="utf-8")
    return str(relative_path).replace("\\", "/"), True


def classify_lever_location(job: dict, location: str) -> str:
    """Classify a Lever posting as Remote, Hybrid, or another location type."""
    workplace_type = (job.get("workplaceType") or "").strip().casefold()
    if workplace_type == "hybrid":
        return "Hybrid"
    if workplace_type == "remote":
        return "Remote"
    return classify_location(location)


def classify_ashby_location(job: dict, location: str) -> str:
    """Classify an Ashby posting as Remote, Hybrid, or another location type."""
    workplace_type = (job.get("workplaceType") or "").strip()
    if workplace_type == "Hybrid":
        return "Hybrid"
    if workplace_type == "Remote" or job.get("isRemote"):
        return "Remote"
    return classify_location(location)


def classify_workable_location(job: dict, location: str) -> str:
    """Classify a Workable posting as Remote, Hybrid, or another location type."""
    if job.get("telecommuting"):
        if "hybrid" in location.casefold():
            return "Hybrid"
        return "Remote"
    return classify_location(location)


def classify_workday_location(job_detail: dict, location: str) -> str:
    """Classify a Workday posting as Remote, Hybrid, or another location type."""
    remote_type = (job_detail.get("remoteType") or "").strip()
    if remote_type:
        normalized = remote_type.casefold()
        if "hybrid" in normalized:
            return "Hybrid"
        if "remote" in normalized:
            return "Remote"
        if "office" in normalized or "flexible" in normalized or "on-site" in normalized:
            return "Hybrid"
    return classify_location(location)


def ensure_remote_location_label(location: str, location_type: str) -> str:
    """Prefix location text with Remote when classified remote but string lacks it."""
    if location_type != "Remote":
        return location
    if any(keyword in location.casefold() for keyword in REMOTE_KEYWORDS):
        return location
    if location.strip():
        return f"Remote — {location.strip()}"
    return "Remote"


def make_job_row(
    company_name: str,
    title: str,
    location: str,
    location_type: str,
    apply_url: str,
    today: str,
    description: str = "",
) -> dict:
    """Build a normalized CSV row for a qualifying job posting."""
    return {
        "Company": company_name,
        "Title": title,
        "Apply URL": apply_url,
        "Experience": "",
        "Category": "",
        "Location": location,
        "Location Type": location_type,
        "Date Found": today,
        "description": description,
        "Description File": "",
    }


def filter_job_posting(
    title: str,
    location: str,
    location_type: str,
    stats: dict[str, int],
) -> bool:
    """Apply title/location filters and update stats. Returns True if job qualifies."""
    stats["retrieved"] += 1

    if not title_matches(title):
        stats["excluded_by_title"] += 1
        return False

    stats["matching_title"] += 1
    if not location_is_included(location_type):
        stats["excluded_by_location"] += 1
        return False

    return True


def _process_greenhouse_board(
    board_token: str,
    company_name: str,
    today: str,
) -> tuple[dict[str, int], dict[str, dict], set[str], str]:
    """Fetch and filter jobs for a single Greenhouse board."""
    stats = empty_stats()
    board_jobs: dict[str, dict] = {}
    board_live_urls: set[str] = set()

    try:
        jobs = fetch_greenhouse_jobs(board_token)
    except urllib.error.HTTPError as exc:
        print(
            f"Skipping {company_name} [Greenhouse/{board_token}]: HTTP {exc.code}",
            file=sys.stderr,
        )
        return stats, board_jobs, board_live_urls, ""
    except urllib.error.URLError as exc:
        print(
            f"Skipping {company_name} [Greenhouse/{board_token}]: {exc.reason}",
            file=sys.stderr,
        )
        return stats, board_jobs, board_live_urls, ""

    board_written = 0
    for job in jobs:
        title = job.get("title", "").strip()
        apply_url = job.get("absolute_url", "").strip()
        if not title or not apply_url:
            continue

        board_live_urls.add(apply_url)
        location = extract_greenhouse_location(job)
        location_type = classify_location(location)
        if not filter_job_posting(title, location, location_type, stats):
            continue

        board_jobs[apply_url] = make_job_row(
            company_name,
            title,
            location,
            location_type,
            apply_url,
            today,
            extract_greenhouse_description(job),
        )
        board_written += 1

    line = (
        f"[Greenhouse] {company_name}: {len(jobs)} open jobs, "
        f"{board_written} written after title/location filters"
    )
    return stats, board_jobs, board_live_urls, line


def collect_greenhouse_jobs(
    today: str,
    collected: dict[str, dict],
    live_apply_urls: set[str],
) -> dict[str, int]:
    """Fetch, filter, and normalize jobs from configured Greenhouse boards."""
    stats = empty_stats()
    lock = threading.Lock()

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(_process_greenhouse_board, board_token, company_name, today)
            for board_token, company_name in GREENHOUSE_BOARDS.items()
        ]
        for future in as_completed(futures):
            board_stats, board_jobs, board_urls, line = future.result()
            with lock:
                merge_stats(stats, board_stats)
                collected.update(board_jobs)
                live_apply_urls.update(board_urls)
            if line:
                print(line)

    return stats


def _process_lever_board(
    site_slug: str,
    company_name: str,
    today: str,
) -> tuple[dict[str, int], dict[str, dict], set[str], str]:
    """Fetch and filter jobs for a single Lever board."""
    stats = empty_stats()
    board_jobs: dict[str, dict] = {}
    board_live_urls: set[str] = set()

    try:
        jobs = fetch_lever_jobs(site_slug)
    except urllib.error.HTTPError as exc:
        print(
            f"Skipping {company_name} [Lever/{site_slug}]: HTTP {exc.code}",
            file=sys.stderr,
        )
        return stats, board_jobs, board_live_urls, ""
    except urllib.error.URLError as exc:
        print(
            f"Skipping {company_name} [Lever/{site_slug}]: {exc.reason}",
            file=sys.stderr,
        )
        return stats, board_jobs, board_live_urls, ""

    board_written = 0
    for job in jobs:
        title = job.get("text", "").strip()
        apply_url = (job.get("applyUrl") or job.get("hostedUrl") or "").strip()
        if not title or not apply_url:
            continue

        board_live_urls.add(apply_url)
        location = extract_lever_location(job)
        location_type = classify_lever_location(job, location)
        if not filter_job_posting(title, location, location_type, stats):
            continue

        board_jobs[apply_url] = make_job_row(
            company_name,
            title,
            location,
            location_type,
            apply_url,
            today,
            extract_lever_description(job),
        )
        board_written += 1

    line = (
        f"[Lever] {company_name}: {len(jobs)} open jobs, "
        f"{board_written} written after title/location filters"
    )
    return stats, board_jobs, board_live_urls, line


def collect_lever_jobs(
    today: str,
    collected: dict[str, dict],
    live_apply_urls: set[str],
) -> dict[str, int]:
    """Fetch, filter, and normalize jobs from configured Lever boards."""
    stats = empty_stats()
    lock = threading.Lock()

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(_process_lever_board, site_slug, company_name, today)
            for site_slug, company_name in LEVER_BOARDS.items()
        ]
        for future in as_completed(futures):
            board_stats, board_jobs, board_urls, line = future.result()
            with lock:
                merge_stats(stats, board_stats)
                collected.update(board_jobs)
                live_apply_urls.update(board_urls)
            if line:
                print(line)

    return stats


def _process_ashby_board(
    board_slug: str,
    company_name: str,
    today: str,
) -> tuple[dict[str, int], dict[str, dict], set[str], str]:
    """Fetch and filter jobs for a single Ashby board."""
    stats = empty_stats()
    board_jobs: dict[str, dict] = {}
    board_live_urls: set[str] = set()

    try:
        jobs = fetch_ashby_jobs(board_slug)
    except urllib.error.HTTPError as exc:
        print(
            f"Skipping {company_name} [Ashby/{board_slug}]: HTTP {exc.code}",
            file=sys.stderr,
        )
        return stats, board_jobs, board_live_urls, ""
    except urllib.error.URLError as exc:
        print(
            f"Skipping {company_name} [Ashby/{board_slug}]: {exc.reason}",
            file=sys.stderr,
        )
        return stats, board_jobs, board_live_urls, ""

    board_written = 0
    for job in jobs:
        title = job.get("title", "").strip()
        apply_url = (job.get("applyUrl") or job.get("jobUrl") or "").strip()
        if not title or not apply_url:
            continue

        board_live_urls.add(apply_url)
        location = extract_ashby_location(job)
        location_type = classify_ashby_location(job, location)
        if not filter_job_posting(title, location, location_type, stats):
            continue

        board_jobs[apply_url] = make_job_row(
            company_name,
            title,
            location,
            location_type,
            apply_url,
            today,
            extract_ashby_description(job),
        )
        board_written += 1

    line = (
        f"[Ashby] {company_name}: {len(jobs)} open jobs, "
        f"{board_written} written after title/location filters"
    )
    return stats, board_jobs, board_live_urls, line


def collect_ashby_jobs(
    today: str,
    collected: dict[str, dict],
    live_apply_urls: set[str],
) -> dict[str, int]:
    """Fetch, filter, and normalize jobs from configured Ashby boards."""
    stats = empty_stats()
    lock = threading.Lock()

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(_process_ashby_board, board_slug, company_name, today)
            for board_slug, company_name in ASHBY_BOARDS.items()
        ]
        for future in as_completed(futures):
            board_stats, board_jobs, board_urls, line = future.result()
            with lock:
                merge_stats(stats, board_stats)
                collected.update(board_jobs)
                live_apply_urls.update(board_urls)
            if line:
                print(line)

    return stats


def _process_workable_board(
    subdomain: str,
    company_name: str,
    today: str,
) -> tuple[dict[str, int], dict[str, dict], set[str], str]:
    """Fetch and filter jobs for a single Workable board."""
    stats = empty_stats()
    board_jobs: dict[str, dict] = {}
    board_live_urls: set[str] = set()

    try:
        jobs = fetch_workable_jobs(subdomain)
    except urllib.error.HTTPError as exc:
        print(
            f"Skipping {company_name} [Workable/{subdomain}]: HTTP {exc.code}",
            file=sys.stderr,
        )
        return stats, board_jobs, board_live_urls, ""
    except urllib.error.URLError as exc:
        print(
            f"Skipping {company_name} [Workable/{subdomain}]: {exc.reason}",
            file=sys.stderr,
        )
        return stats, board_jobs, board_live_urls, ""

    board_written = 0
    for job in jobs:
        title = job.get("title", "").strip()
        apply_url = (job.get("application_url") or job.get("url") or "").strip()
        if not title or not apply_url:
            continue

        board_live_urls.add(apply_url)
        location = extract_workable_location(job)
        location_type = classify_workable_location(job, location)
        location = ensure_remote_location_label(location, location_type)
        if not filter_job_posting(title, location, location_type, stats):
            continue

        board_jobs[apply_url] = make_job_row(
            company_name,
            title,
            location,
            location_type,
            apply_url,
            today,
            extract_workable_description(job),
        )
        board_written += 1

    line = (
        f"[Workable] {company_name}: {len(jobs)} open jobs, "
        f"{board_written} written after title/location filters"
    )
    return stats, board_jobs, board_live_urls, line


def collect_workable_jobs(
    today: str,
    collected: dict[str, dict],
    live_apply_urls: set[str],
) -> dict[str, int]:
    """Fetch, filter, and normalize jobs from configured Workable boards."""
    stats = empty_stats()
    lock = threading.Lock()

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(_process_workable_board, subdomain, company_name, today)
            for subdomain, company_name in WORKABLE_BOARDS.items()
        ]
        for future in as_completed(futures):
            board_stats, board_jobs, board_urls, line = future.result()
            with lock:
                merge_stats(stats, board_stats)
                collected.update(board_jobs)
                live_apply_urls.update(board_urls)
            if line:
                print(line)

    return stats


def _process_workday_board(
    tenant: str,
    board: dict,
    today: str,
) -> tuple[dict[str, int], dict[str, dict], set[str], str]:
    """Fetch and filter jobs for a single Workday career site."""
    stats = empty_stats()
    board_jobs: dict[str, dict] = {}
    board_live_urls: set[str] = set()
    company_name = board["name"]
    wd_server = board["wd_server"]
    site = board["site"]

    try:
        jobs = fetch_workday_jobs(tenant, wd_server, site)
    except urllib.error.HTTPError as exc:
        print(
            f"Skipping {company_name} [Workday/{tenant}/{site}]: HTTP {exc.code}",
            file=sys.stderr,
        )
        return stats, board_jobs, board_live_urls, ""
    except urllib.error.URLError as exc:
        print(
            f"Skipping {company_name} [Workday/{tenant}/{site}]: {exc.reason}",
            file=sys.stderr,
        )
        return stats, board_jobs, board_live_urls, ""

    board_written = 0
    for job in jobs:
        title = job.get("title", "").strip()
        external_path = (job.get("externalPath") or "").strip()
        if not title or not external_path:
            continue

        board_live_urls.add(workday_apply_url(tenant, wd_server, site, external_path))
        stats["retrieved"] += 1
        if not title_matches(title):
            stats["excluded_by_title"] += 1
            continue

        stats["matching_title"] += 1

        try:
            job_detail = fetch_workday_job_detail(tenant, wd_server, site, external_path)
        except urllib.error.HTTPError as exc:
            print(
                f"Skipping {company_name} job '{title}': detail HTTP {exc.code}",
                file=sys.stderr,
            )
            continue
        except urllib.error.URLError as exc:
            print(
                f"Skipping {company_name} job '{title}': detail {exc.reason}",
                file=sys.stderr,
            )
            continue

        apply_url = (job_detail.get("externalUrl") or "").strip()
        if not apply_url:
            continue

        board_live_urls.add(apply_url)
        location = extract_workday_location(job, job_detail)
        location_type = classify_workday_location(job_detail, location)
        location = ensure_remote_location_label(location, location_type)
        if not location_is_included(location_type):
            stats["excluded_by_location"] += 1
            continue

        board_jobs[apply_url] = make_job_row(
            company_name,
            title,
            location,
            location_type,
            apply_url,
            today,
            extract_workday_description(job_detail),
        )
        board_written += 1

    line = (
        f"[Workday] {company_name}: {len(jobs)} open jobs, "
        f"{board_written} written after title/location filters"
    )
    return stats, board_jobs, board_live_urls, line


def collect_workday_jobs(
    today: str,
    collected: dict[str, dict],
    live_apply_urls: set[str],
) -> dict[str, int]:
    """Fetch, filter, and normalize jobs from configured Workday career sites."""
    stats = empty_stats()
    lock = threading.Lock()

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(_process_workday_board, tenant, board, today)
            for tenant, board in WORKDAY_BOARDS.items()
        ]
        for future in as_completed(futures):
            board_stats, board_jobs, board_urls, line = future.result()
            with lock:
                merge_stats(stats, board_stats)
                collected.update(board_jobs)
                live_apply_urls.update(board_urls)
            if line:
                print(line)

    return stats


def collect_jobs() -> tuple[list[dict], dict[str, int], set[str]]:
    """Fetch, filter, and normalize jobs from all configured ATS boards."""
    today = date.today().isoformat()
    collected: dict[str, dict] = {}
    live_apply_urls: set[str] = set()
    stats = empty_stats()

    merge_stats(stats, collect_greenhouse_jobs(today, collected, live_apply_urls))
    print()
    merge_stats(stats, collect_lever_jobs(today, collected, live_apply_urls))
    print()
    merge_stats(stats, collect_ashby_jobs(today, collected, live_apply_urls))
    print()
    merge_stats(stats, collect_workable_jobs(today, collected, live_apply_urls))
    print()
    merge_stats(stats, collect_workday_jobs(today, collected, live_apply_urls))

    return list(collected.values()), stats, live_apply_urls


def load_existing_jobs(csv_path: Path) -> dict[str, dict]:
    """Load prior results keyed by apply_url to support deduplication across runs."""
    if not csv_path.exists():
        return {}

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        existing: dict[str, dict] = {}
        for row in reader:
            normalized = normalize_csv_row(row)
            apply_url = normalized["Apply URL"].strip()
            if apply_url:
                existing[apply_url] = normalized
        return existing


def job_qualifies(title: str, location: str) -> tuple[bool, str | None]:
    """
    Apply title and location filters.

    Returns (qualifies, location_type). location_type is None when the title fails.
    """
    if not title_matches(title):
        return False, None

    location_type = classify_location(location)
    return location_is_included(location_type), location_type


def _csv_sort_key(row: dict) -> tuple[str, str, str]:
    """Sort rows newest first by date_found, then company, then title."""
    return (
        row.get("Date Found", ""),
        row.get("Company", ""),
        row.get("Title", ""),
    )


def _save_jobs_additive(
    csv_path: Path,
    new_jobs: list[dict],
) -> tuple[int, int, int]:
    """
    Append-only merge: preserve all existing rows, add new apply_urls only.

    Returns (newly_added_count, total_rows_written, descriptions_archived).
    """
    existing = load_existing_jobs(csv_path)
    merged = dict(existing)
    descriptions_root = Path(DESCRIPTIONS_DIR)
    existing_paths_by_url = {
        apply_url: row.get("Description File", "").strip()
        for apply_url, row in existing.items()
        if row.get("Description File", "").strip()
    }
    archived = 0

    for job in new_jobs:
        apply_url = job["Apply URL"]
        if apply_url in merged:
            continue

        job_row = normalize_csv_row({
            "Company": job["Company"],
            "Title": job["Title"],
            "Apply URL": apply_url,
            "Experience": job.get("Experience", ""),
            "Category": job.get("Category", ""),
            "Location": job["Location"],
            "Location Type": job["Location Type"],
            "Date Found": job["Date Found"],
            "Description File": "",
            "description": job.get("description", ""),
        })

        description_file, created = archive_job_description(
            job_row,
            descriptions_root,
            existing_paths_by_url,
        )
        job_row["Description File"] = description_file
        existing_paths_by_url[apply_url] = description_file
        if created:
            archived += 1

        merged[apply_url] = {key: job_row[key] for key in CSV_COLUMNS}

    if not merged and existing:
        print(
            f"Safeguard: refusing to overwrite {csv_path} with an empty CSV "
            f"({len(existing)} existing row(s) preserved). "
            "This usually indicates a failed or incomplete scrape.",
            file=sys.stderr,
        )
        return 0, len(existing), 0

    added = sum(1 for apply_url in merged if apply_url not in existing)
    rows = sorted(merged.values(), key=_csv_sort_key, reverse=True)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    return added, len(rows), archived


def _save_jobs_sync(
    csv_path: Path,
    new_jobs: list[dict],
    live_apply_urls: set[str],
) -> tuple[int, int, int, int]:
    """
    Replace merge: keep only jobs from the latest scrape (legacy behavior).

    Returns (newly_added_count, total_rows_written, descriptions_archived, removed_count).
    """
    existing = load_existing_jobs(csv_path)
    pruned: dict[str, dict] = {}
    descriptions_root = Path(DESCRIPTIONS_DIR)
    existing_paths_by_url = {
        apply_url: row.get("Description File", "").strip()
        for apply_url, row in existing.items()
        if row.get("Description File", "").strip()
    }
    archived = 0

    for job in new_jobs:
        apply_url = job["Apply URL"]
        if apply_url not in live_apply_urls:
            active = is_posting_active(apply_url, job.get("Company", ""))
            if active is False:
                print(
                    f"Skipping closed posting: {job.get('Company', '')} — {job.get('Title', '')}",
                    file=sys.stderr,
                )
                continue

        merged = existing.get(apply_url, {})
        job_row = normalize_csv_row({
            "Company": job["Company"],
            "Title": job["Title"],
            "Apply URL": apply_url,
            "Experience": merged.get("Experience", job.get("Experience", "")),
            "Category": merged.get("Category", job.get("Category", "")),
            "Location": job["Location"],
            "Location Type": job["Location Type"],
            "Date Found": merged.get("Date Found", job["Date Found"]),
            "Description File": merged.get("Description File", "").strip(),
            "description": job.get("description", ""),
        })

        needs_archive = not job_row["Description File"]
        if needs_archive:
            description_file, created = archive_job_description(
                job_row,
                descriptions_root,
                existing_paths_by_url,
            )
            job_row["Description File"] = description_file
            existing_paths_by_url[apply_url] = description_file
            if created:
                archived += 1

        pruned[apply_url] = {key: job_row[key] for key in CSV_COLUMNS}

    if not pruned and existing:
        print(
            f"Safeguard: refusing to overwrite {csv_path} with an empty CSV "
            f"({len(existing)} existing row(s) preserved). "
            "This usually indicates a failed or incomplete scrape.",
            file=sys.stderr,
        )
        return 0, len(existing), 0, 0

    removed = 0
    for apply_url, row in existing.items():
        if apply_url in pruned:
            continue
        removed += 1
        if apply_url in live_apply_urls:
            reason = "no longer matches filters"
        elif is_posting_active(apply_url, row.get("Company", "")) is False:
            reason = "posting closed"
        else:
            reason = "not found on latest scrape"
        print(
            f"Removing ({reason}): {row.get('Company', '')} — {row.get('Title', '')}"
            f" (description archive kept)",
            file=sys.stderr,
        )

    added = sum(1 for apply_url in pruned if apply_url not in existing)
    rows = sorted(pruned.values(), key=lambda row: (row["Company"], row["Title"]))
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    return added, len(rows), archived, removed


def save_jobs(
    csv_path: Path,
    new_jobs: list[dict],
    live_apply_urls: set[str] | None = None,
) -> tuple[int, int, int, int]:
    """
    Merge new jobs into the CSV, deduplicating by apply_url.

    When PRESERVE_EXISTING_JOBS is True (default), existing rows are kept and
    only new apply_urls are appended. Archives Markdown descriptions for newly
    discovered jobs. Removing a row from jobs.csv never deletes its archived
    description file under job_descriptions/.

    Refuses to overwrite a non-empty CSV with zero rows, which usually
    indicates a failed or incomplete scrape.

    Returns (newly_added_count, total_rows_written, descriptions_archived, removed_count).
    """
    if PRESERVE_EXISTING_JOBS:
        added, total, archived = _save_jobs_additive(csv_path, new_jobs)
        return added, total, archived, 0

    return _save_jobs_sync(csv_path, new_jobs, live_apply_urls or set())


def print_summary(stats: dict[str, int], written_to_csv: int) -> None:
    """Print end-of-run filtering summary."""
    print("\nSummary")
    print(f"Jobs Retrieved:            {stats['retrieved']}")
    print(f"Jobs Matching Title:       {stats['matching_title']}")
    print(f"Jobs Excluded By Title:    {stats['excluded_by_title']}")
    print(f"Jobs Excluded By Location: {stats['excluded_by_location']}")
    print(f"Jobs Written To CSV:       {written_to_csv}")


def description_file_is_missing(relative_path: str) -> bool:
    """Return True when a description archive is absent or only a stub."""
    path_text = relative_path.strip()
    if not path_text:
        return True

    absolute_path = Path(path_text)
    if not absolute_path.is_file():
        return True

    try:
        content = absolute_path.read_text(encoding="utf-8")
    except OSError:
        return True

    return MISSING_DESCRIPTION_PLACEHOLDER in content


def find_jobs_missing_descriptions(csv_path: Path) -> list[dict]:
    """Return CSV rows whose archived description still needs a manual paste."""
    missing: list[dict] = []
    for row in load_existing_jobs(csv_path).values():
        if description_file_is_missing(row.get("Description File", "")):
            missing.append(row)
    missing.sort(key=_csv_sort_key, reverse=True)
    return missing


def print_missing_descriptions_report(missing: list[dict]) -> None:
    """Print jobs that need a manual description paste."""
    print(f"\nMissing descriptions (need manual paste): {len(missing)}")
    for row in missing:
        company = row.get("Company", "").strip() or "(unknown company)"
        title = row.get("Title", "").strip() or "(unknown title)"
        apply_url = row.get("Apply URL", "").strip()
        description_file = row.get("Description File", "").strip() or "(no description file)"
        print(f"  - {company} — {title}")
        if apply_url:
            print(f"    {apply_url}")
        print(f"    -> {description_file}")


def main() -> None:
    print(
        "Collecting Product Design jobs from Greenhouse, Lever, Ashby, "
        "Workable, and Workday boards...\n"
    )
    jobs, stats, live_apply_urls = collect_jobs()
    csv_path = Path(OUTPUT_CSV)
    existing_count = len(load_existing_jobs(csv_path))
    if stats["retrieved"] == 0 and existing_count:
        print(
            "Safeguard: scrape retrieved 0 jobs; keeping existing CSV unchanged.",
            file=sys.stderr,
        )
        print_summary(stats, 0)
        print(f"\nKept {existing_count} existing row(s) in {csv_path.resolve()}")
        print_missing_descriptions_report(find_jobs_missing_descriptions(csv_path))
        return

    added, total_written, archived, removed = save_jobs(csv_path, jobs, live_apply_urls)

    print_summary(stats, len(jobs))
    print(f"\nSaved to {csv_path.resolve()}")
    if PRESERVE_EXISTING_JOBS:
        print(
            f"Added {added} new row(s); preserved existing rows; "
            f"total rows in CSV: {total_written}"
        )
    else:
        print(
            f"Added {added} new row(s); removed {removed} inactive/stale row(s); "
            f"total rows in CSV: {total_written}"
        )
    print(f"Archived {archived} new job description(s) to {Path(DESCRIPTIONS_DIR).resolve()}")
    print_missing_descriptions_report(find_jobs_missing_descriptions(csv_path))


if __name__ == "__main__":
    main()
