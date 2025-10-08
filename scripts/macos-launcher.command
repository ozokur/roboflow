#!/usr/bin/env bash
# macOS double-click launcher for the Roboflow Uploader
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$APP_DIR"

echo "[macos-launcher] Working directory: $APP_DIR"

if [ ! -f .env ]; then
  echo "[macos-launcher] .env not found."
  if [ -t 0 ]; then
    read -rsp "Enter your ROBOFLOW_API_KEY (input hidden): " ROBOFLOW_API_KEY
    echo
    if [ -z "${ROBOFLOW_API_KEY}" ]; then
      echo "[macos-launcher] No API key entered. Exiting."
      exit 1
    fi
    {
      echo "ROBOFLOW_API_KEY=${ROBOFLOW_API_KEY}"
      if [ -f .env.template ] && grep -q '^APP_ENV=' .env.template; then
        grep '^APP_ENV=' .env.template
      else
        echo "APP_ENV=dev"
      fi
    } > .env
    chmod 600 .env
    echo "[macos-launcher] .env created."
  else
    echo "[macos-launcher] .env missing and no interactive terminal available. Please create .env manually."
    exit 1
  fi
fi

if [ ! -d .venv ]; then
  echo "[macos-launcher] Virtual environment not found. Running bootstrap script..."
  exec "$APP_DIR/scripts/bootstrap_macos.sh"
fi

echo "[macos-launcher] Virtual environment detected. Launching application..."
exec "$APP_DIR/scripts/run_app.sh"
