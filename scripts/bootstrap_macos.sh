#!/usr/bin/env bash
# Bootstrap script for macOS one-click setup
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"

log() {
  printf '[bootstrap] %s\n' "$1"
}

log "Project directory: $APP_DIR"

if ! command -v xcode-select >/dev/null 2>&1; then
  log "Checking for Xcode Command Line Tools"
fi

if ! xcode-select -p >/dev/null 2>&1; then
  log "Installing Xcode Command Line Tools (this may require confirmation)…"
  xcode-select --install || true
fi

if ! command -v brew >/dev/null 2>&1; then
  log "Installing Homebrew…"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  if [ -d /opt/homebrew/bin ]; then
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$HOME/.zprofile"
    eval "$(/opt/homebrew/bin/brew shellenv)"
  else
    echo 'eval "$(/usr/local/bin/brew shellenv)"' >> "$HOME/.zprofile"
    eval "$(/usr/local/bin/brew shellenv)"
  fi
else
  eval "$(brew shellenv)"
fi

log "Updating Homebrew"
brew update
brew install python@3.11 git pkg-config || true

PY_BIN="python3.11"
if ! command -v "$PY_BIN" >/dev/null 2>&1; then
  PY_BIN="python3"
fi

log "Creating virtual environment"
"$PY_BIN" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel setuptools

if [ -f pyproject.toml ]; then
  log "Installing project dependencies via pip"
  pip install .
else
  log "Installing minimal runtime dependencies"
  pip install PySide6 requests python-dotenv rich
fi

log "Bootstrap complete. Launching application…"
./scripts/run_app.sh
