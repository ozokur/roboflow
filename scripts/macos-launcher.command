#!/usr/bin/env bash
# macOS double-click launcher for the Roboflow Uploader
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$APP_DIR"

echo "[macos-launcher] Working directory: $APP_DIR"

if [ ! -d .venv ]; then
  echo "[macos-launcher] Virtual environment not found. Running bootstrap script..."
  exec "$APP_DIR/scripts/bootstrap_macos.sh"
fi

echo "[macos-launcher] Virtual environment detected. Launching application..."
exec "$APP_DIR/scripts/run_app.sh"
