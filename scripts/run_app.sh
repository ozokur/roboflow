#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"

if [ ! -d .venv ]; then
  echo "[run_app] Virtual environment not found. Run scripts/bootstrap_macos.sh first." >&2
  exit 1
fi

source .venv/bin/activate

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1090
  source .env
  set +a
fi

python -m app.ui.main_window
