#!/usr/bin/env bash
set -uo pipefail

# Interval seconds (default 15)
INTERVAL="${1:-15}"

# Optional: log file for diagnostics (stderr and exit codes)
LOG_DIR="/data/salomonis-archive/FASTQs/NCI-R01/POSEIDON/Master_Project/logs"
LOG_FILE="$LOG_DIR/overall_status_watch.log"
mkdir -p "$LOG_DIR" 2>/dev/null || true

run_once() {
  # Prefer interactive bash so aliases like 'overall-status' are available
  # If you have a direct command path, set OVERALL_STATUS_CMD to override
  if [[ -n "${OVERALL_STATUS_CMD:-}" ]]; then
    eval "$OVERALL_STATUS_CMD"
  else
    bash -i -c "overall-status"
  fi
}

trap 'echo "$(date -Is) - received signal, exiting." >> "$LOG_FILE"; exit 0' INT TERM

while :; do
  TS=$(date -Is)
  if run_once >>"$LOG_FILE" 2>&1; then
    echo "$TS - overall-status OK" >>"$LOG_FILE"
  else
    RC=$?
    echo "$TS - overall-status FAILED (exit $RC)" >>"$LOG_FILE"
  fi
  sleep "$INTERVAL"
done
