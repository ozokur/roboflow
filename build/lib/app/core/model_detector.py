"""Model version and architecture detection."""
from __future__ import annotations

import torch
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger("roboflow_uploader.model_detector")


class ModelInfo:
    """Container for detected model information."""
    
    def __init__(
        self,
        model_type: str,
        version: str,
        architecture: str,
        compatible_ultralytics: str,
        file_path: Path,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.model_type = model_type  # e.g., "yolo"
        self.version = version  # e.g., "v8", "v11"
        self.architecture = architecture  # e.g., "yolov8n", "yolo11n"
        self.compatible_ultralytics = compatible_ultralytics  # e.g., "8.0.196", "8.3.0+"
        self.file_path = file_path
        self.metadata = metadata or {}
    
    @property
    def is_compatible_with_sdk(self) -> bool:
        """Check if model is compatible with current ultralytics version."""
        try:
            import ultralytics
            current_version = ultralytics.__version__
            
            # Parse version numbers for comparison
            current_parts = [int(x) for x in current_version.split('.')]
            
            # YOLOv5, v7, v8: require 8.0.196+
            if self.version in ["v5", "v7", "v8"]:
                return True  # These work with any 8.x version
            
            # YOLOv11: requires <=8.3.40
            if self.version == "v11":
                # Check if current version is <= 8.3.40
                if current_parts[0] == 8:
                    if current_parts[1] < 3:
                        return False  # Too old
                    elif current_parts[1] == 3 and current_parts[2] <= 40:
                        return True  # Perfect!
                    elif current_parts[1] > 3:
                        return True  # Might work with newer versions too
                return False
            
            # Other versions: assume compatible if ultralytics >= 8.0
            return current_parts[0] >= 8
            
        except Exception:
            # Fallback to old logic if version check fails
            return self.version in ["v8", "v5", "v7"]
    
    @property
    def display_name(self) -> str:
        """Human-readable model description."""
        return f"YOLO{self.version} ({self.architecture})"
    
    def __str__(self) -> str:
        compat = "✅ SDK Compatible" if self.is_compatible_with_sdk else "⚠️ SDK Incompatible"
        return (
            f"{self.display_name}\n"
            f"  Type: {self.model_type}\n"
            f"  Architecture: {self.architecture}\n"
            f"  Ultralytics: {self.compatible_ultralytics}\n"
            f"  {compat}"
        )


def detect_model_info(model_path: Path) -> ModelInfo:
    """
    Detect YOLO model version and architecture from model file.
    
    Args:
        model_path: Path to the model file (.pt, .onnx, etc.)
    
    Returns:
        ModelInfo object with detected information
    
    Raises:
        ValueError: If model cannot be analyzed
    """
    try:
        # Try to load checkpoint metadata
        checkpoint = torch.load(
            str(model_path), 
            map_location='cpu',
            weights_only=False  # Allow loading ultralytics objects
        )
        
        # Extract information from checkpoint
        metadata = {}
        
        # Check for version info
        if 'version' in checkpoint:
            metadata['train_ultralytics_version'] = checkpoint['version']
        
        # Check for model architecture
        model_arch = "unknown"
        yolo_version = "v8"  # Default assumption
        
        if 'model' in checkpoint:
            model_obj = checkpoint['model']
            
            # Check class name
            if hasattr(model_obj, '__class__'):
                class_name = model_obj.__class__.__name__
                metadata['model_class'] = class_name
            
            # Check for YAML configuration
            if hasattr(model_obj, 'yaml'):
                yaml_dict = model_obj.yaml
                if isinstance(yaml_dict, dict):
                    # Check for architecture indicators
                    yaml_str = str(yaml_dict)
                    
                    # Detect YOLOv11 (has C3k2, C2PSA modules)
                    if 'C3k2' in yaml_str or 'C2PSA' in yaml_str or 'SPPF' in yaml_str:
                        yolo_version = "v11"
                        model_arch = "yolo11"
                        compatible_ultralytics = "8.3.0+"
                    # Detect YOLOv8 (has C2f module)
                    elif 'C2f' in yaml_str:
                        yolo_version = "v8"
                        model_arch = "yolov8"
                        compatible_ultralytics = "8.0.196"
                    # Detect YOLOv5 (has C3 module)
                    elif 'C3' in yaml_str and 'C3k' not in yaml_str:
                        yolo_version = "v5"
                        model_arch = "yolov5"
                        compatible_ultralytics = "8.0.196"
                    
                    metadata['architecture_modules'] = [
                        m for m in ['C3k2', 'C2PSA', 'C2f', 'C3', 'SPPF', 'SPP']
                        if m in yaml_str
                    ]
        
        # Guess architecture size from filename
        filename = model_path.stem.lower()
        if 'n' in filename or 'nano' in filename:
            size = 'n'
        elif 'l' in filename or 'large' in filename:
            size = 'l'
        elif 'm' in filename or 'medium' in filename:
            size = 'm'
        elif 's' in filename or 'small' in filename:
            size = 's'
        elif 'x' in filename or 'xlarge' in filename:
            size = 'x'
        else:
            size = 'n'  # Default
        
        if model_arch == "unknown":
            model_arch = f"yolo{yolo_version}{size}"
        
        return ModelInfo(
            model_type="yolo",
            version=yolo_version,
            architecture=model_arch,
            compatible_ultralytics=compatible_ultralytics if 'compatible_ultralytics' in locals() else "8.0.196",
            file_path=model_path,
            metadata=metadata
        )
        
    except Exception as e:
        logger.warning(f"Could not fully analyze model {model_path}: {e}")
        
        # Smart fallback based on error message
        error_str = str(e)
        
        # If C3k2 error, it's definitely YOLOv11
        if "C3k2" in error_str or "C2PSA" in error_str:
            return ModelInfo(
                model_type="yolo",
                version="v11",
                architecture="yolo11n",
                compatible_ultralytics="8.3.0+",
                file_path=model_path,
                metadata={"detection_method": "error_analysis", "error": str(e)}
            )
        
        # Fallback: guess from filename
        filename = model_path.stem.lower()
        
        if 'yolo11' in filename or 'v11' in filename or '11' in filename:
            return ModelInfo(
                model_type="yolo",
                version="v11",
                architecture="yolo11n",
                compatible_ultralytics="8.3.0+",
                file_path=model_path,
                metadata={"detection_method": "filename", "error": str(e)}
            )
        else:
            # Default to YOLOv8
            return ModelInfo(
                model_type="yolo",
                version="v8",
                architecture="yolov8n",
                compatible_ultralytics="8.0.196",
                file_path=model_path,
                metadata={"detection_method": "filename_fallback", "error": str(e)}
            )


def check_compatibility(model_info: ModelInfo) -> tuple[bool, str]:
    """
    Check if model is compatible with current system.
    
    Returns:
        (is_compatible, message) tuple
    """
    if model_info.is_compatible_with_sdk:
        return True, f"✅ {model_info.display_name} is compatible with Roboflow SDK"
    else:
        return False, (
            f"⚠️ {model_info.display_name} requires ultralytics {model_info.compatible_ultralytics}\n"
            f"Roboflow SDK requires ultralytics 8.0.196\n"
            f"\n"
            f"🔧 Solutions:\n"
            f"• Use Roboflow Web UI to train models\n"
            f"• Use local inference (inference_model.py)\n"
            f"• Convert to YOLOv8 format"
        )

