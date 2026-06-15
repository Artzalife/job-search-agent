#!/usr/bin/env python3
"""
Multi-ATS job collector.

Collects Product Design job postings from configured Greenhouse, Lever, and Ashby
public job boards and writes matching results to jobs.csv.

Supported public APIs (no authentication required)
---------------------------------------------------
Greenhouse:
    GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs

Lever:
    GET https://api.lever.co/v0/postings/{site}?mode=json

Ashby:
    GET https://api.ashbyhq.com/posting-api/job-board/{job_board_name}

We fetch every open job from each configured board, filter titles against the
include/exclude rules in config.py, classify each location, keep only Remote
roles, deduplicate by apply_url, and write results to jobs.csv.

Run:
    python3 job_scraper.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

from config import (
    ASHBY_API_BASE,
    ASHBY_BOARDS,
    GREENHOUSE_API_BASE,
    GREENHOUSE_BOARDS,
    LEVER_API_BASE,
    LEVER_BOARDS,
    LOCATION_TYPES_INCLUDED,
    OUTPUT_CSV,
    TITLE_EXCLUDES,
    TITLE_INCLUDES,
)

CSV_COLUMNS = [
    "company",
    "title",
    "location",
    "location_type",
    "apply_url",
    "date_found",
]

REMOTE_KEYWORDS = ("remote", "work from home")
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
      Remote        — contains "remote" or "work from home"
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
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_greenhouse_jobs(board_token: str) -> list[dict]:
    """Fetch all published jobs for a Greenhouse board."""
    url = f"{GREENHOUSE_API_BASE}/{board_token}/jobs"
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


def make_job_row(
    company_name: str,
    title: str,
    location: str,
    location_type: str,
    apply_url: str,
    today: str,
) -> dict:
    """Build a normalized CSV row for a qualifying job posting."""
    return {
        "company": company_name,
        "title": title,
        "location": location,
        "location_type": location_type,
        "apply_url": apply_url,
        "date_found": today,
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


def collect_greenhouse_jobs(today: str, collected: dict[str, dict]) -> dict[str, int]:
    """Fetch, filter, and normalize jobs from configured Greenhouse boards."""
    stats = empty_stats()

    for board_token, company_name in GREENHOUSE_BOARDS.items():
        try:
            jobs = fetch_greenhouse_jobs(board_token)
        except urllib.error.HTTPError as exc:
            print(f"Skipping {company_name} [Greenhouse/{board_token}]: HTTP {exc.code}", file=sys.stderr)
            continue
        except urllib.error.URLError as exc:
            print(f"Skipping {company_name} [Greenhouse/{board_token}]: {exc.reason}", file=sys.stderr)
            continue

        board_written = 0
        for job in jobs:
            title = job.get("title", "").strip()
            apply_url = job.get("absolute_url", "").strip()
            if not title or not apply_url:
                continue

            location = extract_greenhouse_location(job)
            location_type = classify_location(location)
            if not filter_job_posting(title, location, location_type, stats):
                continue

            collected[apply_url] = make_job_row(
                company_name, title, location, location_type, apply_url, today
            )
            board_written += 1

        print(
            f"[Greenhouse] {company_name}: {len(jobs)} open jobs, "
            f"{board_written} written after title/location filters"
        )

    return stats


def collect_lever_jobs(today: str, collected: dict[str, dict]) -> dict[str, int]:
    """Fetch, filter, and normalize jobs from configured Lever boards."""
    stats = empty_stats()

    for site_slug, company_name in LEVER_BOARDS.items():
        try:
            jobs = fetch_lever_jobs(site_slug)
        except urllib.error.HTTPError as exc:
            print(f"Skipping {company_name} [Lever/{site_slug}]: HTTP {exc.code}", file=sys.stderr)
            continue
        except urllib.error.URLError as exc:
            print(f"Skipping {company_name} [Lever/{site_slug}]: {exc.reason}", file=sys.stderr)
            continue

        board_written = 0
        for job in jobs:
            title = job.get("text", "").strip()
            apply_url = (job.get("applyUrl") or job.get("hostedUrl") or "").strip()
            if not title or not apply_url:
                continue

            location = extract_lever_location(job)
            location_type = classify_lever_location(job, location)
            if not filter_job_posting(title, location, location_type, stats):
                continue

            collected[apply_url] = make_job_row(
                company_name, title, location, location_type, apply_url, today
            )
            board_written += 1

        print(
            f"[Lever] {company_name}: {len(jobs)} open jobs, "
            f"{board_written} written after title/location filters"
        )

    return stats


def collect_ashby_jobs(today: str, collected: dict[str, dict]) -> dict[str, int]:
    """Fetch, filter, and normalize jobs from configured Ashby boards."""
    stats = empty_stats()

    for board_slug, company_name in ASHBY_BOARDS.items():
        try:
            jobs = fetch_ashby_jobs(board_slug)
        except urllib.error.HTTPError as exc:
            print(f"Skipping {company_name} [Ashby/{board_slug}]: HTTP {exc.code}", file=sys.stderr)
            continue
        except urllib.error.URLError as exc:
            print(f"Skipping {company_name} [Ashby/{board_slug}]: {exc.reason}", file=sys.stderr)
            continue

        board_written = 0
        for job in jobs:
            title = job.get("title", "").strip()
            apply_url = (job.get("applyUrl") or job.get("jobUrl") or "").strip()
            if not title or not apply_url:
                continue

            location = extract_ashby_location(job)
            location_type = classify_ashby_location(job, location)
            if not filter_job_posting(title, location, location_type, stats):
                continue

            collected[apply_url] = make_job_row(
                company_name, title, location, location_type, apply_url, today
            )
            board_written += 1

        print(
            f"[Ashby] {company_name}: {len(jobs)} open jobs, "
            f"{board_written} written after title/location filters"
        )

    return stats


def collect_jobs() -> tuple[list[dict], dict[str, int]]:
    """Fetch, filter, and normalize jobs from all configured ATS boards."""
    today = date.today().isoformat()
    collected: dict[str, dict] = {}
    stats = empty_stats()

    merge_stats(stats, collect_greenhouse_jobs(today, collected))
    print()
    merge_stats(stats, collect_lever_jobs(today, collected))
    print()
    merge_stats(stats, collect_ashby_jobs(today, collected))

    return list(collected.values()), stats


def load_existing_jobs(csv_path: Path) -> dict[str, dict]:
    """Load prior results keyed by apply_url to support deduplication across runs."""
    if not csv_path.exists():
        return {}

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return {
            row["apply_url"]: row
            for row in reader
            if row.get("apply_url")
        }


def job_qualifies(title: str, location: str) -> tuple[bool, str | None]:
    """
    Apply title and location filters.

    Returns (qualifies, location_type). location_type is None when the title fails.
    """
    if not title_matches(title):
        return False, None

    location_type = classify_location(location)
    return location_is_included(location_type), location_type


def save_jobs(csv_path: Path, new_jobs: list[dict]) -> tuple[int, int]:
    """
    Merge new jobs into the CSV, deduplicating by apply_url.

    Existing rows that no longer pass filters are dropped. Returns
    (newly_added_count, total_rows_written).
    """
    existing = load_existing_jobs(csv_path)
    pruned: dict[str, dict] = {}

    for apply_url, row in existing.items():
        qualifies, location_type = job_qualifies(
            row.get("title", ""),
            row.get("location", ""),
        )
        if not qualifies:
            continue
        row["location_type"] = location_type
        pruned[apply_url] = row

    added = 0
    for job in new_jobs:
        if job["apply_url"] not in pruned:
            added += 1
        pruned[job["apply_url"]] = job

    rows = sorted(pruned.values(), key=lambda row: (row["company"], row["title"]))
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    return added, len(rows)


def print_summary(stats: dict[str, int], written_to_csv: int) -> None:
    """Print end-of-run filtering summary."""
    print("\nSummary")
    print(f"Jobs Retrieved:            {stats['retrieved']}")
    print(f"Jobs Matching Title:       {stats['matching_title']}")
    print(f"Jobs Excluded By Title:    {stats['excluded_by_title']}")
    print(f"Jobs Excluded By Location: {stats['excluded_by_location']}")
    print(f"Jobs Written To CSV:       {written_to_csv}")


def main() -> None:
    print("Collecting Product Design jobs from Greenhouse, Lever, and Ashby boards...\n")
    jobs, stats = collect_jobs()
    csv_path = Path(OUTPUT_CSV)
    added, total_written = save_jobs(csv_path, jobs)

    print_summary(stats, len(jobs))
    print(f"\nSaved to {csv_path.resolve()}")
    print(f"Added {added} new row(s); total rows in CSV: {total_written}")


if __name__ == "__main__":
    main()
