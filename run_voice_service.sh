#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Virtual environment not found at $PYTHON_BIN" >&2
  exit 1
fi

ROBOT_IP="${ROBOT_IP:-192.168.12.1}"
ROBOT_PASSWORD="${ROBOT_PASSWORD:-123}"
IDLE_INTERVAL="${IDLE_INTERVAL:-15}"

exec "$PYTHON_BIN" "$SCRIPT_DIR/example_integration.py" \
  --robot-ip "$ROBOT_IP" \
  --password "$ROBOT_PASSWORD" \
  --idle-interval "$IDLE_INTERVAL"
