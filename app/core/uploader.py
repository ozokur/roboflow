"""High level upload orchestration."""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Dict, Optional

from .config import APP_VERSION
from .logging_util import log_event
from .roboflow_client import RoboflowClient, RoboflowAPIError
from .versioning import generate_operation_id, write_manifest


class UploadManager:
    """Coordinate uploads for both dataset and external model modes."""

    def __init__(
        self,
        client: RoboflowClient,
        *,
        artifacts_dir: Path,
        manifests_dir: Path,
        logger,
    ) -> None:
        self.client = client
        self.artifacts_dir = artifacts_dir
        self.manifests_dir = manifests_dir
        self.logger = logger

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def _copy_artifact(self, file_path: Path) -> Dict[str, str]:
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        destination = self.artifacts_dir / file_path.name
        shutil.copy2(file_path, destination)
        sha256 = hashlib.sha256(destination.read_bytes()).hexdigest()
        return {
            "filename": destination.name,
            "sha256": sha256,
            "size_bytes": destination.stat().st_size,
            "storage_url": destination.resolve().as_uri(),
        }

    def _persist_manifest(self, operation_id: str, payload: Dict[str, object]) -> Path:
        manifest_path = write_manifest(self.manifests_dir, operation_id, payload)
        self.logger.info("Manifest written to %s", manifest_path)
        return manifest_path

    # ------------------------------------------------------------------
    # External model workflow (Mode B)
    # ------------------------------------------------------------------
    def link_external_model(
        self,
        *,
        workspace: str,
        project: str,
        version: str,
        file_path: Path,
        storage_note: Optional[str] = None,
    ) -> Dict[str, object]:
        operation_id = generate_operation_id("ext")
        log_event(
            self.logger,
            "external_model_link_started",
            operation_id=operation_id,
            workspace=workspace,
            project=project,
            version=version,
            filename=file_path.name,
        )

        artifact = self._copy_artifact(file_path)
        metadata = {
            "artifact": artifact,
            "storage_note": storage_note or "stored locally",
            "app_version": APP_VERSION,
        }
        note = (
            f"External model artifact {artifact['filename']} stored at {artifact['storage_url']}\n"
            f"Checksum (sha256): {artifact['sha256']}"
        )

        # Deploy model to Roboflow
        # Try to detect model type
        from .model_detector import detect_model_info
        
        try:
            model_info = detect_model_info(file_path)
            model_type = model_info.architecture  # e.g., "yolov8n", "yolo11n"
            log_event(
                self.logger,
                "model_info_detected",
                operation_id=operation_id,
                model_type=model_type,
                version=model_info.version,
                compatible=model_info.is_compatible_with_sdk
            )
        except Exception as e:
            model_type = "yolov8"  # Fallback
            log_event(
                self.logger,
                "model_info_detection_failed",
                operation_id=operation_id,
                error=str(e)
            )
        
        try:
            response = self.client.deploy_model(
                workspace=workspace,
                project=project,
                version=version,
                model_path=str(file_path),
                model_type=model_type
            )
            api_response = response
            status = "success"
        except RoboflowAPIError as exc:
            # If deployment fails, store locally only
            api_response = {
                "status": "stored_locally",
                "error": str(exc),
                "metadata": metadata,
            }
            status = "partial_success"
            log_event(
                self.logger,
                "model_deployment_failed",
                operation_id=operation_id,
                error=str(exc),
            )

        manifest_payload = {
            "mode": "external_model",
            "workspace": workspace,
            "project": project,
            "target_version": version,
            "artifact": artifact,
            "storage_note": storage_note,
            "note_content": note,
            "status": status,
            "api_response": api_response,
        }
        manifest = self._persist_manifest(operation_id, manifest_payload)
        log_event(
            self.logger,
            "external_model_link_completed",
            operation_id=operation_id,
            manifest=str(manifest),
        )
        return {
            "operation_id": operation_id,
            "manifest": manifest,
            "artifact": artifact,
            "api_response": api_response,
        }

    # ------------------------------------------------------------------
    # Dataset workflow (Mode A)
    # ------------------------------------------------------------------
    def upload_dataset(
        self,
        *,
        workspace: str,
        project: str,
        dataset_zip_path: Path,
        trigger_training: bool = False,
        description: str = "",
    ) -> Dict[str, object]:
        operation_id = generate_operation_id("ds")
        log_event(
            self.logger,
            "dataset_upload_started",
            operation_id=operation_id,
            workspace=workspace,
            project=project,
            archive=str(dataset_zip_path),
        )

        try:
            response = self.client.upload_dataset(
                workspace=workspace,
                project=project,
                dataset_zip_path=str(dataset_zip_path),
                description=description,
            )
            version = response.get("version")
        except NotImplementedError as exc:
            log_event(
                self.logger,
                "dataset_upload_not_implemented",
                operation_id=operation_id,
                reason=str(exc),
            )
            manifest = self._persist_manifest(
                operation_id,
                {
                    "mode": "dataset",
                    "workspace": workspace,
                    "project": project,
                    "dataset_archive": str(dataset_zip_path),
                    "status": "pending",
                    "notes": str(exc),
                },
            )
            return {
                "operation_id": operation_id,
                "manifest": manifest,
                "status": "pending",
                "message": str(exc),
            }
        except RoboflowAPIError as exc:
            manifest = self._persist_manifest(
                operation_id,
                {
                    "mode": "dataset",
                    "workspace": workspace,
                    "project": project,
                    "dataset_archive": str(dataset_zip_path),
                    "status": "error",
                    "error": str(exc),
                    "payload": getattr(exc, "payload", {}),
                },
            )
            raise

        training_response = None
        if trigger_training and version:
            try:
                training_response = self.client.trigger_training(
                    workspace=workspace,
                    project=project,
                    version=version,
                )
            except NotImplementedError as exc:
                training_response = {"status": "pending", "message": str(exc)}
            except RoboflowAPIError as exc:
                training_response = {"status": "error", "message": str(exc)}

        manifest = self._persist_manifest(
            operation_id,
            {
                "mode": "dataset",
                "workspace": workspace,
                "project": project,
                "dataset_archive": str(dataset_zip_path),
                "status": "success",
                "api_response": response,
                "training_response": training_response,
            },
        )
        log_event(
            self.logger,
            "dataset_upload_completed",
            operation_id=operation_id,
            manifest=str(manifest),
        )
        return {
            "operation_id": operation_id,
            "manifest": manifest,
            "api_response": response,
            "training_response": training_response,
        }


def validate_model_extension(path: Path) -> bool:
    """Return True if file extension matches accepted model artifacts."""

    return path.suffix.lower() in {".pt", ".onnx", ".engine", ".tflite", ".pb"}
