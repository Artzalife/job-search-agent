# Project Context

Engineering handoff document for the **job-search-agent** project. Read this before making architectural changes or starting expansion work.

---

## Product Philosophy

This project exists to increase the number of relevant **healthcare Product Design** opportunities discovered.

The goal is **not** to build the most sophisticated scraper.

The goal is **not** to automate job applications.

The goal is **not** to replace human judgment.

Automation should reduce repetitive work while leaving important career decisions to the user.

When deciding between adding new functionality or increasing healthcare company coverage, **prefer increasing coverage** unless a clear productivity benefit exists.

Every architectural decision should make the project easier to maintain and expand over the long term.

---

## Project Purpose

This is a **healthcare Product Design job search agent**.

It monitors public ATS (Applicant Tracking System) job boards for configured companies, filters postings to relevant design roles, and produces a curated CSV plus a Markdown archive of job descriptions.

**Primary goal:** maximize discovery of relevant jobs while minimizing maintenance effort.

The scraper does not apply to jobs, rank candidates, or make career recommendations. The user reviews output and applies manually.

---

## Current Architecture

### ATS platforms

The scraper supports five ATS platforms via their **public, unauthenticated JSON APIs**:

| Platform   | API pattern |
|-----------|-------------|
| Greenhouse | `GET boards-api.greenhouse.io/v1/boards/{slug}/jobs` |
| Lever      | `GET api.lever.co/v0/postings/{slug}?mode=json` |
| Ashby      | `GET api.ashbyhq.com/posting-api/job-board/{slug}` |
| Workable   | `GET www.workable.com/api/accounts/{slug}?details=true` |
| Workday    | `POST {tenant}.{wd_server}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs` |

There is **no public API to discover companies** on any platform. Coverage is limited to companies explicitly listed in the registry.

### Company registry

**File:** `data/companies.csv`

Each row is one scrapeable ATS board. Required columns: `company_id`, `category`, `display_name`, `ats`, `slug`, `enabled`. Workday rows also require `wd_server` and `workday_site`.

`config.py` loads enabled rows into in-memory board dicts consumed by the scraper. Adding a company means adding a CSV row — not editing Python board lists.

**Allowed categories:** Clinical AI, EHR, Provider Operations, Population Health, Healthcare Infrastructure, Revenue Cycle, Medical Devices, Diagnostics, Clinical Research, Healthcare Analytics, Healthcare CRM, Veterinary, Behavioral Health, Employer Health, General Tech.

### Validation

**Script:** `scripts/validate_companies.py`

Checks registry schema, required fields, valid ATS/category values, duplicate `(ats, slug)` pairs, and Workday field completeness. Optional flags:

- `--probe` — hits each enabled board's public API
- `--check-migration` — verifies loaded board dicts match `data/_migration_snapshot.json`

Run validation after every registry change and before scraping.

**Discovery helper:** `scripts/probe_all_ats.py` probes candidate slugs across all supported ATS APIs and prints suggested CSV rows. Use it when the ATS platform or slug is unknown.

### Scraper

**File:** `job_scraper.py`

Single script. Fetches all open jobs from configured boards (parallel within each ATS type), filters by title rules and location type, archives descriptions, deduplicates by `apply_url`, and writes to CSV.

**Filters** (in `config.py`):

- `TITLE_INCLUDES` — must match at least one phrase (Product Designer, UX Designer, etc.)
- `TITLE_EXCLUDES` — Staff, Principal, Lead, Director, Manager, Intern, Junior, etc.
- `LOCATION_TYPES_INCLUDED` — default: Remote only
- `WORKDAY_SEARCH_TEXT` — pre-filters large Workday boards (default: `"product designer"`)
- `PRESERVE_EXISTING_JOBS` — default `True`; append-only CSV, no auto-pruning

Dependencies: **Python 3.9+ standard library only** (no pip packages required for v1).

### Markdown archive

**Directory:** `job_descriptions/{year}/`

On first discovery of a job, the scraper saves its full description as Markdown:

```
{company}_{job-title}_{MM-DD-YY}.md
```

Each file includes title, company, location, URL, capture date, and description text. The relative path is stored in the `Description File` column of `jobs.csv`.

Archive rules:

- Created on first discovery only; never overwritten
- Never deleted, even if the job closes or is removed from CSV
- Duplicate `apply_url` values share one description file

The archive is intentionally preserved as a long-term dataset for future analysis.

### CSV output

**File:** `jobs.csv`

Columns: Company, Title, Apply URL, Experience, Category, Location, Location Type, Date Found, Description File.

Default behavior is **additive**: new jobs are appended; existing rows are not updated or removed. The user manually curates stale entries.

---

## Design Principles

1. **Preserve backward compatibility.** Existing CSV rows, description files, and registry format should keep working across changes.
2. **Avoid unnecessary refactoring.** Match existing code style and conventions. Do not reorganize working code without a concrete benefit.
3. **Keep the scraper simple.** One script, stdlib-only, public APIs, no browser automation, no auth.
4. **Prefer expanding company coverage over adding new features.** More verified companies beats more scraper complexity.
5. **Do not automate human judgment.** Filtering is rule-based and conservative. Application decisions stay with the user.
6. **Keep dependencies minimal.** Resist adding libraries unless they solve a real, recurring problem.
7. **Make small, incremental improvements.** Focused diffs, one concern per change, validate after each registry update.

---

## Current Workflow

```
1. Expand company registry   →  Edit data/companies.csv
2. Validate registry         →  python3 scripts/validate_companies.py [--probe]
3. Run scraper               →  python3 job_scraper.py
4. Review CSV                →  jobs.csv (filter, dedupe manually if needed)
5. Read markdown descriptions →  job_descriptions/{year}/
6. Apply manually            →  User follows Apply URL links
```

Optional: weekday automation via macOS `launchd` (`scripts/install_schedule.sh`).

For registry expansion, probe unknown slugs first:

```bash
python3 scripts/probe_all_ats.py candidate-slug another-slug
```

---

## Expansion Philosophy

Expansion happens in **focused sprints**, not ad-hoc one-offs.

**Prioritize easily verifiable companies.** A company is added only when its ATS platform and board slug are confirmed via public API probe. If verification is uncertain, do not guess.

**Difficult companies go into a Manual Review Queue.** Examples: embedded Greenhouse boards (API 404 but `gh_jid` on careers page), custom career portals, unsupported ATS platforms (iCIMS, Oracle HCM, SmartRecruiters), or ambiguous slug matches.

**Organize expansion by healthcare sector.** Use registry categories (EHR, Clinical AI, Diagnostics, Revenue Cycle, etc.) to batch related companies and track coverage gaps.

**Maximize coverage instead of solving edge cases.** A verified board with a working slug is worth more than perfect handling of every ATS variant. Unsupported platforms wait until there is a clear, maintainable integration path.

**Do not modify scraper architecture during expansion sprints.** Sprint #1 added 21 companies to the registry with zero scraper changes. That is the expected pattern.

---

## Future Roadmap

Intended order of work. Do not skip ahead without explicit decision.

| Phase | Focus | Status |
|-------|-------|--------|
| **Phase 1** | Company registry — CSV-driven boards, validation, probe tooling | **Completed** |
| **Phase 2** | Expand healthcare coverage — sector sprints, manual review queue | **Current** |
| **Phase 3** | Analyze markdown archive for hiring trends | Planned |
| **Phase 4** | Dashboard | Planned |
| **Phase 5** | Optional AI analysis | Planned |

Phase 3+ depends on accumulated data in `job_descriptions/` and a stable, growing registry. Rushing to UI or AI before coverage is solid would violate the product philosophy.

---

## Things NOT To Do

- **Don't redesign the scraper.** The multi-ATS collector works. Extend via registry, not architecture rewrites.
- **Don't add unnecessary infrastructure.** No databases, queues, Docker, or cloud services unless a concrete need emerges.
- **Don't add AI features yet.** Phase 5 is optional and deferred.
- **Don't build dashboards yet.** Phase 4 is deferred.
- **Don't overengineer.** No abstractions for hypothetical future ATS platforms. No plugin systems. No ORMs.
- **Don't auto-apply to jobs.** Out of scope permanently.
- **Don't guess ATS slugs.** Unverified companies belong in the manual review report, not the registry.
- **Don't commit secrets.** No API keys, credentials, or `.env` files.

---

## Definition of Success

Success is measured by outcomes, not code complexity:

| Metric | What good looks like |
|--------|---------------------|
| **More verified companies** | Registry grows with confidently probed boards across healthcare sectors |
| **More relevant jobs discovered** | `jobs.csv` captures remote Product Design roles the user would not find manually |
| **Easier maintenance** | Adding a company is a CSV row + validation, not a code change |
| **Better long-term healthcare dataset** | `job_descriptions/` accumulates a searchable archive for trend analysis in Phase 3 |

A failed direction: a more sophisticated scraper that covers fewer companies and requires more upkeep.

---

## Key Files (Quick Reference)

| File | Role |
|------|------|
| `data/companies.csv` | Operational company registry |
| `config.py` | Loads boards from CSV; filter settings |
| `job_scraper.py` | Multi-ATS collector |
| `scripts/validate_companies.py` | Registry validation and probing |
| `scripts/probe_all_ats.py` | ATS slug discovery |
| `jobs.csv` | Curated job output |
| `job_descriptions/` | Markdown description archive |
| `README.md` | User-facing setup and usage docs |
