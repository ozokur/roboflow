#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"

if [ ! -d .venv ]; then
  echo "[run_app] Virtual environment not found. Run scripts/bootstrap_macos.sh first." >&2
  exit 1
fi

source .venv/bin/activate

# Ensure PySide6 and other runtime dependencies are available. This covers
# scenarios where the repository was updated after the original bootstrap or the
# virtual environment was created manually without installing project deps.
if ! python -c "import PySide6" >/dev/null 2>&1; then
  echo "[run_app] PySide6 not found in the virtual environment. Installing project dependencies..."
  if [ -f pyproject.toml ]; then
    python -m pip install --quiet --upgrade pip wheel setuptools
    python -m pip install .
  else
    python -m pip install PySide6 requests python-dotenv rich
  fi
fi

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1090
  source .env
  set +a
fi

python -m app.ui.main_window
