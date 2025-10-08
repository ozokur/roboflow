"""Versioning and manifest helpers."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .config import APP_VERSION


def generate_operation_id(prefix: str = "upl") -> str:
    """Generate a sortable operation identifier."""

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{ts}"


def write_manifest(manifests_dir: Path, operation_id: str, payload: Dict[str, Any]) -> Path:
    """Persist a manifest describing an operation."""

    manifests_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifests_dir / f"{operation_id}.json"
    document = {
        "op_id": operation_id,
        "app_version": APP_VERSION,
        "written_at": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    manifest_path.write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest_path
