# job-search-agent

Automatically collects Product Design job postings from companies on [Greenhouse](https://www.greenhouse.io/), [Lever](https://www.lever.co/), [Ashby](https://www.ashbyhq.com/), [Workable](https://www.workable.com/), and [Workday](https://www.workday.com/).

Uses each platform's public Job Board API (JSON, no authentication) to fetch open roles from configured company boards, filter for relevant design titles, and save results to `jobs.csv`.

## How it works

Each ATS exposes a public API for published job postings:

```
GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs
GET https://api.lever.co/v0/postings/{site}?mode=json
GET https://api.ashbyhq.com/posting-api/job-board/{job_board_name}
GET https://www.workable.com/api/accounts/{subdomain}?details=true
POST https://{tenant}.{wd_server}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs
```

Jobs are filtered to product design / UX titles, excluding Staff, Principal, Lead, intern, junior, manager, and director roles. Only **remote** postings are kept — on-site and hybrid-only roles are excluded. Duplicates are avoided by tracking each job's `apply_url`.

By default (`PRESERVE_EXISTING_JOBS = True`), each run **adds** newly discovered jobs to `jobs.csv` without removing existing rows. Closed or stale postings stay in the CSV until you remove them manually. Set `PRESERVE_EXISTING_JOBS = False` in `config.py` to restore the previous sync-and-prune behavior.

Board fetches run in parallel within each ATS type. Workday boards use `WORKDAY_SEARCH_TEXT` (default `"product designer"`) to narrow API results before filtering.

**Coverage note:** None of these ATS platforms expose a public API to list every company board. The scraper only searches the board slugs configured in `config.py`. Add more slugs there to expand coverage.

## Project structure

| File | Purpose |
|------|---------|
| `config.py` | Board slugs for Greenhouse, Lever, Ashby, Workable, and Workday; title/location filters |
| `job_scraper.py` | Fetches jobs from all configured ATS platforms and writes `jobs.csv` |
| `requirements.txt` | Dependencies (v1 uses stdlib only) |
| `jobs.csv` | Output file (created on first run) |
| `job_descriptions/` | Archived Markdown job descriptions (organized by year) |

## Setup

Python 3.9+ is required. No extra packages are needed for v1.

```bash
pip install -r requirements.txt   # optional; no packages to install
```

## Configure boards

Edit `config.py` and add company slugs to `GREENHOUSE_BOARDS`, `LEVER_BOARDS`, `ASHBY_BOARDS`, `WORKABLE_BOARDS`, or `WORKDAY_BOARDS`. The slug is the path segment from the company's careers URL:

```python
GREENHOUSE_BOARDS = {"stripe": "Stripe", ...}
LEVER_BOARDS = {"ro": "Ro", ...}
ASHBY_BOARDS = {"headway": "Headway", ...}
WORKABLE_BOARDS = {"steadymd": "SteadyMD", ...}
WORKDAY_BOARDS = {
    "dexcom": {"name": "Dexcom", "wd_server": "wd1", "site": "Dexcom"},
    ...
}
```

## Run

```bash
python3 job_scraper.py
```

The script prints per-company stats, then writes matching jobs to `jobs.csv` with columns:

| Column | Description |
|--------|-------------|
| `company` | Company display name from config |
| `title` | Job title |
| `location` | Location string from Greenhouse |
| `location_type` | Location classification (`Remote`, `Office`, etc.) |
| `apply_url` | Direct link to the job posting |
| `date_found` | Date the job was collected (ISO format) |
| `description_file` | Relative path to the archived Markdown description |

### Job description archive

When a job is first discovered, the scraper saves its full description as a Markdown file under `job_descriptions/{year}/`.

**Filename format:** `{company}_{job-title}_{date}.md`

- Lowercase
- Spaces replaced with hyphens
- Date format: `MM-DD-YY`

**Example:**

```
job_descriptions/2026/vercel_senior-product-designer_06-15-26.md
```

Each file contains the job title, company, location, URL, capture date, and full description text. The relative path is stored in the `description_file` column of `jobs.csv`.

Archive rules:

- Description files are created only on first discovery
- Existing description files are never overwritten on later runs
- Archived descriptions are **never deleted**, even when a posting closes or is removed from `jobs.csv`
- Duplicate jobs (same `apply_url`) share a single description file

When `PRESERVE_EXISTING_JOBS` is `True` (default), rows are never auto-removed from `jobs.csv` — only new `apply_url` values are appended. Existing row metadata (`date_found`, title, location, etc.) is preserved from the first snapshot.

The archive uses only the Python standard library and relative paths, so it works in local runs, `launchd` schedules, and GitHub Actions.

### Filters (`config.py`)

| Setting | What it does |
|---------|--------------|
| `GREENHOUSE_BOARDS` | Greenhouse companies to search (slug → display name) |
| `LEVER_BOARDS` | Lever companies to search (slug → display name) |
| `ASHBY_BOARDS` | Ashby companies to search (slug → display name) |
| `WORKABLE_BOARDS` | Workable companies to search (subdomain → display name) |
| `WORKDAY_BOARDS` | Workday companies to search (tenant → name/wd_server/site) |
| `TITLE_INCLUDES` | Title must contain one of these phrases |
| `TITLE_EXCLUDES` | Title must not contain these phrases (manager, intern, etc.) |
| `LOCATION_TYPES_INCLUDED` | Only jobs with these location types are saved (default: `Remote` only) |
| `PRESERVE_EXISTING_JOBS` | When `True`, only append new jobs; never auto-remove existing rows (default: `True`) |
| `WORKDAY_SEARCH_TEXT` | Free-text filter for Workday job search API (default: `"product designer"`) |

Re-running the script merges new jobs into the existing CSV without duplicating `apply_url` values. With the default additive mode, existing rows are preserved across runs.

## Automatic weekday runs (macOS)

The project includes a `launchd` job that runs the scraper **Monday through Friday at 9:00 AM** local time.

Install or update the schedule:

```bash
./scripts/install_schedule.sh
```

Run the scraper immediately (without waiting for the schedule):

```bash
launchctl kickstart -k gui/$(id -u)/com.jobsearchagent.scraper
```

Logs are written to `logs/job_scraper.log`. To change the run time, edit the `Hour` and `Minute` values in `launchd/com.jobsearchagent.scraper.plist`, then rerun `install_schedule.sh`.

To remove the schedule:

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.jobsearchagent.scraper.plist
```
