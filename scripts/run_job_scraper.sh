#!/bin/bash
# Run the Greenhouse job collector and append output to a log file.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${PROJECT_DIR}/logs"
LOG_FILE="${LOG_DIR}/job_scraper.log"

mkdir -p "${LOG_DIR}"

{
  echo "===== $(date '+%Y-%m-%d %H:%M:%S %Z') ====="
  cd "${PROJECT_DIR}"
  /usr/bin/python3 job_scraper.py
  echo
} >> "${LOG_FILE}" 2>&1
