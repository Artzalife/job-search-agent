#!/bin/bash
# Install the weekday launchd job for the job scraper.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_SOURCE="${PROJECT_DIR}/launchd/com.jobsearchagent.scraper.plist"
PLIST_DEST="${HOME}/Library/LaunchAgents/com.jobsearchagent.scraper.plist"
LABEL="com.jobsearchagent.scraper"

chmod +x "${PROJECT_DIR}/scripts/run_job_scraper.sh"
mkdir -p "${PROJECT_DIR}/logs"
cp "${PLIST_SOURCE}" "${PLIST_DEST}"

launchctl bootout "gui/${UID}" "${PLIST_DEST}" 2>/dev/null || true
launchctl bootstrap "gui/${UID}" "${PLIST_DEST}"
launchctl enable "gui/${UID}/${LABEL}"
launchctl kickstart -k "gui/${UID}/${LABEL}" 2>/dev/null || true

echo "Installed ${LABEL}"
echo "Schedule: Monday-Friday at 9:00 AM (local time)"
echo "Logs: ${PROJECT_DIR}/logs/job_scraper.log"
echo
echo "To run immediately:"
echo "  launchctl kickstart -k gui/${UID}/${LABEL}"
echo
echo "To uninstall:"
echo "  launchctl bootout gui/${UID} ${PLIST_DEST}"
