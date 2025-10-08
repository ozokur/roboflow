"""Dynamic ultralytics version management for different YOLO versions."""
from __future__ import annotations

import subprocess
import sys
import logging
from typing import Dict

logger = logging.getLogger("roboflow_uploader.version_manager")

# Version requirements from Roboflow documentation
ULTRALYTICS_REQUIREMENTS = {
    "v5": "8.0.196",
    "v7": "8.0.196", 
    "v8": "8.0.196",
    "v9": "custom",  # Requires custom repo
    "v10": "custom",  # Requires custom repo
    "v11": "8.3.40",
    "v12": "custom",  # Requires custom repo
}


def get_required_ultralytics_version(yolo_version: str) -> str:
    """Get the required ultralytics version for a YOLO model version."""
    return ULTRALYTICS_REQUIREMENTS.get(yolo_version, "8.0.196")


def switch_ultralytics_version(target_version: str, force: bool = False) -> bool:
    """
    Switch ultralytics to the required version.
    
    Args:
        target_version: Target ultralytics version (e.g., "8.3.40")
        force: Force reinstall even if version matches
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check current version
        import ultralytics
        current_version = ultralytics.__version__
        
        if current_version == target_version and not force:
            logger.info(f"ultralytics already at target version {target_version}")
            return True
        
        logger.info(f"Switching ultralytics from {current_version} to {target_version}")
        
        # Uninstall current
        subprocess.check_call(
            [sys.executable, "-m", "pip", "uninstall", "-y", "ultralytics"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Install target version
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", f"ultralytics=={target_version}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        logger.info(f"Successfully switched to ultralytics=={target_version}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to switch ultralytics version: {e}")
        return False


def ensure_compatible_ultralytics(yolo_version: str) -> bool:
    """
    Ensure ultralytics version is compatible with the YOLO model version.
    
    Args:
        yolo_version: YOLO version (v5, v8, v11, etc.)
        
    Returns:
        True if compatible version is installed
    """
    required = get_required_ultralytics_version(yolo_version)
    
    if required == "custom":
        logger.warning(f"YOLO {yolo_version} requires custom ultralytics repo")
        return False
    
    return switch_ultralytics_version(required)

