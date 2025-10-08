"""Configuration utilities for the Roboflow Uploader application."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

APP_VERSION = "1.2.1"  # Updated: Fixed YOLOv11 detection (C3k2 error analysis)
APP_NAME = "Roboflow Uploader"
APP_BUILD_DATE = "2025-10-08"


def increment_version(version_type: str = "patch") -> str:
    """Increment app version (for auto-update feature)."""
    parts = APP_VERSION.split(".")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    
    if version_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif version_type == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    return f"{major}.{minor}.{patch}"


@dataclass
class AppConfig:
    """Simple container for runtime configuration."""

    api_key: Optional[str]
    app_env: str
    base_dir: Path
    logs_dir: Path
    manifests_dir: Path
    artifacts_dir: Path


def load_config() -> AppConfig:
    """Load configuration from environment variables and defaults."""

    base_dir = Path(__file__).resolve().parents[1]
    repo_root = base_dir.parent

    # Load environment variables in priority order: repo root first, app-specific
    load_dotenv(repo_root / ".env", override=False)
    load_dotenv(base_dir / ".env", override=False)

    api_key = os.getenv("ROBOFLOW_API_KEY")
    app_env = os.getenv("APP_ENV", "dev")

    logs_dir = base_dir / "logs"
    manifests_dir = base_dir / "outputs" / "manifests"
    artifacts_dir = base_dir / "outputs" / "artifacts"

    for path in (logs_dir, manifests_dir, artifacts_dir):
        path.mkdir(parents=True, exist_ok=True)

    return AppConfig(
        api_key=api_key,
        app_env=app_env,
        base_dir=base_dir,
        logs_dir=logs_dir,
        manifests_dir=manifests_dir,
        artifacts_dir=artifacts_dir,
    )


def mask_secret(secret: Optional[str]) -> str:
    """Return a masked representation of a secret for safe logging."""

    if not secret:
        return "<missing>"

    if len(secret) <= 4:
        return "*" * len(secret)

    return f"{secret[:2]}***{secret[-2:]}"
