"""Roboflow API client abstractions."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from .config import mask_secret
from .logging_util import log_event

API_BASE_URL = "https://api.roboflow.com"
REQUEST_TIMEOUT = 30

logger = logging.getLogger("roboflow_uploader.client")


class RoboflowAPIError(RuntimeError):
    """Raised when the Roboflow API returns an error."""

    def __init__(self, status_code: int, message: str, *, payload: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(f"Roboflow API error {status_code}: {message}")
        self.status_code = status_code
        self.payload = payload or {}


class RoboflowClient:
    """Thin wrapper around the Roboflow REST API."""

    def __init__(self, api_key: Optional[str]) -> None:
        self.api_key = api_key

    # ------------------------------------------------------------------
    # Listing helpers
    # ------------------------------------------------------------------
    def list_workspaces(self) -> List[Dict[str, Any]]:
        """Return available workspaces for the authenticated user."""

        if not self.api_key:
            return []
        response = self._request("GET", "/")
        data = response.json()
        
        # Roboflow API returns a single workspace field, not a list
        workspace_slug = data.get("workspace")
        if workspace_slug:
            workspaces = [{
                "id": workspace_slug,
                "slug": workspace_slug,
                "name": workspace_slug
            }]
        else:
            # Fallback: try workspaces list if API changes
            workspaces_raw = data.get("workspaces", [])
            if isinstance(workspaces_raw, dict):
                workspaces = []
                for slug, info in workspaces_raw.items():
                    if isinstance(info, dict):
                        merged = {"slug": slug}
                        merged.update(info)
                        merged.setdefault("id", slug)
                    else:
                        merged = {"slug": slug, "id": slug, "name": str(info)}
                    workspaces.append(merged)
            else:
                workspaces = list(workspaces_raw)
        
        log_event(logger, "rf_list_workspaces", count=len(workspaces))
        return workspaces

    def list_projects(self, workspace: str) -> List[Dict[str, Any]]:
        """List projects for a given workspace."""

        if not self.api_key:
            return []
        response = self._request("GET", f"/{workspace}")
        data = response.json()
        
        # Roboflow API returns projects inside workspace object
        workspace_data = data.get("workspace", {})
        projects_raw = workspace_data.get("projects", [])
        
        # Also check top-level for backwards compatibility
        if not projects_raw:
            projects_raw = data.get("projects", [])
        
        if isinstance(projects_raw, dict):
            projects = []
            for slug, info in projects_raw.items():
                if isinstance(info, dict):
                    merged = {"slug": slug}
                    merged.update(info)
                    merged.setdefault("id", slug)
                else:
                    merged = {"slug": slug, "id": slug, "name": str(info)}
                projects.append(merged)
        else:
            projects = list(projects_raw)
        log_event(logger, "rf_list_projects", workspace=workspace, count=len(projects))
        return projects

    def list_versions(self, workspace: str, project: str) -> List[Dict[str, Any]]:
        """List versions for a specific project."""

        if not self.api_key:
            return []
        response = self._request("GET", f"/{workspace}/{project}")
        data = response.json()
        versions_raw = data.get("versions", [])
        
        if isinstance(versions_raw, dict):
            versions = []
            for version_id, info in versions_raw.items():
                if isinstance(info, dict):
                    merged = {"id": version_id, "version": version_id}
                    merged.update(info)
                else:
                    merged = {
                        "id": version_id,
                        "version": version_id,
                        "name": str(info),
                    }
                versions.append(merged)
        else:
            # API returns list of version objects
            versions = []
            for v in versions_raw:
                if isinstance(v, dict):
                    # Extract version number from ID (e.g., "ozokur/project/11" -> "11")
                    version_id = v.get("id", "")
                    version_number = version_id.split("/")[-1] if "/" in version_id else version_id
                    # Use name for display, version number for reference
                    v.setdefault("version", version_number)
                    versions.append(v)
        
        log_event(
            logger,
            "rf_list_versions",
            workspace=workspace,
            project=project,
            count=len(versions),
        )
        return versions

    # ------------------------------------------------------------------
    # Metadata helpers
    # ------------------------------------------------------------------
    def append_version_note(
        self,
        workspace: str,
        project: str,
        version: str,
        note: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Append a note/metadata blob to a version."""

        if not self.api_key:
            raise RoboflowAPIError(401, "Missing API key")

        payload = {"note": note, "metadata": metadata or {}}
        response = self._request(
            "POST",
            f"/{workspace}/{project}/{version}/notes",
            json=payload,
        )
        result = response.json()
        log_event(
            logger,
            "rf_append_note",
            workspace=workspace,
            project=project,
            version=version,
            metadata_keys=list(payload["metadata"].keys()),
        )
        return result

    # ------------------------------------------------------------------
    # Dataset upload / training stubs
    # ------------------------------------------------------------------
    def upload_dataset(
        self,
        workspace: str,
        project: str,
        dataset_zip_path: str,
        *,
        description: str = "",
    ) -> Dict[str, Any]:
        """Upload a dataset archive and create a new version.

        This method is intentionally kept lightweight to satisfy the spec without
        committing secrets. You may extend it to call the official Roboflow API.
        """

        raise NotImplementedError("Dataset upload requires project-specific implementation")

    def trigger_training(self, workspace: str, project: str, version: str) -> Dict[str, Any]:
        """Trigger a training job for a given dataset version."""

        raise NotImplementedError("Training trigger is not implemented in this template")
    
    def deploy_model(
        self,
        workspace: str,
        project: str,
        version: str,
        model_path: str,
        model_type: str = "yolov8"
    ) -> Dict[str, Any]:
        """Deploy a trained model to Roboflow using the SDK.
        
        Args:
            workspace: Workspace name
            project: Project name
            version: Version number
            model_path: Path to the model file
            model_type: Type of model (yolov8, yolov5, etc.)
        """
        try:
            from roboflow import Roboflow
            import sys
            from io import StringIO
            
            rf = Roboflow(api_key=self.api_key)
            ws = rf.workspace(workspace)
            proj = ws.project(project)
            ver = proj.version(int(version))
            
            # Mock stdin to automatically answer 'y' for any prompts
            old_stdin = sys.stdin
            sys.stdin = StringIO('y\n')
            
            try:
                # Deploy the model
                # Roboflow SDK expects model_path to be a directory and filename to be relative path
                model_file = Path(model_path)
                ver.deploy(
                    model_type=model_type,
                    model_path=str(model_file.parent),  # Directory containing the model
                    filename=model_file.name  # Just the filename
                )
            finally:
                # Restore stdin
                sys.stdin = old_stdin
            
            log_event(
                logger,
                "rf_model_deployed",
                workspace=workspace,
                project=project,
                version=version,
                model_type=model_type
            )
            
            return {
                "status": "deployed",
                "workspace": workspace,
                "project": project,
                "version": version,
                "model_path": model_path
            }
        except Exception as e:
            raise RoboflowAPIError(500, f"Model deployment failed: {str(e)}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        if not self.api_key:
            raise RoboflowAPIError(401, "Missing API key")

        params = kwargs.pop("params", {})
        params.setdefault("api_key", self.api_key)
        url = f"{API_BASE_URL}{path}"
        try:
            response = requests.request(
                method,
                url,
                params=params,
                timeout=REQUEST_TIMEOUT,
                **kwargs,
            )
        except requests.RequestException as exc:  # noqa: BLE001
            raise RoboflowAPIError(0, f"Network error: {exc}") from exc

        self._raise_for_status(response)
        return response

    def _raise_for_status(self, response: requests.Response) -> None:
        if response.ok:
            return

        status = response.status_code
        try:
            payload = response.json()
            message = payload.get("error") or payload.get("message") or response.text
        except ValueError:
            payload = None
            message = response.text

        if status in (401, 403):
            masked = mask_secret(self.api_key)
            message = f"Authentication failed for API key {masked}. {message}"
        elif status == 404:
            message = f"Resource not found. {message}"
        elif status >= 500:
            message = f"Roboflow service unavailable ({status}). {message}"

        raise RoboflowAPIError(status, message, payload=payload)
