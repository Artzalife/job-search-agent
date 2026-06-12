# job-search-agent

Automatically collects Product Design job postings from companies that use [Greenhouse](https://www.greenhouse.io/) as their applicant tracking system (ATS).

**Version 1** uses Greenhouse's public Job Board API (JSON, no authentication) to fetch open roles from configured company boards, filter for relevant design titles, and save results to `jobs.csv`.

## How it works

Each Greenhouse customer has a public job board identified by a **board token** (the slug in URLs like `https://boards.greenhouse.io/stripe`). The collector calls:

```
GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs
```

Jobs are filtered to titles containing Product Design / UX keywords and excluding intern, junior, or student roles. Duplicates are avoided by tracking each job's `apply_url`.

## Project structure

| File | Purpose |
|------|---------|
| `config.py` | Greenhouse board tokens, title filters, and output settings |
| `job_scraper.py` | Fetches jobs from the Greenhouse API and writes `jobs.csv` |
| `requirements.txt` | Dependencies (v1 uses stdlib only) |
| `jobs.csv` | Output file (created on first run) |

## Setup

Python 3.9+ is required. No extra packages are needed for v1.

```bash
pip install -r requirements.txt   # optional; no packages to install
```

## Configure boards

Edit `config.py` and add Greenhouse board tokens to `GREENHOUSE_BOARDS`. The token is the path segment from the company's Greenhouse careers URL:

```python
GREENHOUSE_BOARDS = {
    "stripe": "Stripe",
    "figma": "Figma",
    # ...
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
| `apply_url` | Direct link to the job posting |
| `date_found` | Date the job was collected (ISO format) |

Re-running the script merges new jobs into the existing CSV without duplicating `apply_url` values.
