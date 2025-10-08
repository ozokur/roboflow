"""PySide6 main window for the Roboflow Uploader."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from PySide6.QtCore import QRunnable, Qt, QThreadPool, Signal, QObject
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QFileDialog,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.config import APP_NAME, APP_VERSION, APP_BUILD_DATE, load_config, mask_secret
from app.core.logging_util import log_event, setup_logging
from app.core.model_detector import detect_model_info, check_compatibility
from app.core.roboflow_client import RoboflowAPIError, RoboflowClient
from app.core.uploader import UploadManager, validate_model_extension


class WorkerSignals(QObject):
    finished = Signal(object)
    error = Signal(Exception)


class FunctionWorker(QRunnable):
    """Run blocking functions on a background thread."""

    def __init__(self, fn: Callable, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self) -> None:  # noqa: D401 - QRunnable interface
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as exc:  # noqa: BLE001 - propagate via signal
            self.signals.error.emit(exc)
        else:
            self.signals.finished.emit(result)


class MainWindow(QMainWindow):
    """Main GUI for interacting with Roboflow."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.thread_pool = QThreadPool.globalInstance()

        self.config = load_config()
        self.logger = setup_logging(self.config.logs_dir)
        self.client = RoboflowClient(self.config.api_key)
        self.uploader = UploadManager(
            self.client,
            artifacts_dir=self.config.artifacts_dir,
            manifests_dir=self.config.manifests_dir,
            logger=self.logger,
        )

        self.selected_file: Optional[Path] = None
        self.selected_workspace: Optional[str] = None
        self.selected_project: Optional[str] = None
        self.selected_version: Optional[str] = None

        self.statusBar().showMessage("Ready")
        self._build_ui()
        self.refresh_hierarchy()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        container = QWidget()
        layout = QVBoxLayout(container)

        # Header with version info
        header_layout = QHBoxLayout()
        api_key_label = QLabel(
            f"API Key: {mask_secret(self.config.api_key)} — Env: {self.config.app_env}"
        )
        version_label = QLabel(
            f"v{APP_VERSION} (Build: {APP_BUILD_DATE})"
        )
        version_label.setStyleSheet("color: gray; font-size: 11px;")
        header_layout.addWidget(api_key_label)
        header_layout.addStretch()
        header_layout.addWidget(version_label)
        layout.addLayout(header_layout)

        # Action buttons row
        action_buttons_layout = QHBoxLayout()
        refresh_button = QPushButton("🔄 Workspace/Project/Version listesini yenile")
        refresh_button.clicked.connect(self.refresh_hierarchy)
        
        view_logs_button = QPushButton("📊 İşlem Geçmişini Görüntüle")
        view_logs_button.clicked.connect(self._view_operation_history)
        
        action_buttons_layout.addWidget(refresh_button)
        action_buttons_layout.addWidget(view_logs_button)
        layout.addLayout(action_buttons_layout)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Ad", "Tip", "Ek Bilgi"])
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.tree)

        file_group = QGroupBox("Dosya Seçimi")
        file_layout = QVBoxLayout()
        
        file_row = QHBoxLayout()
        self.file_label = QLabel("Hiçbir dosya seçilmedi")
        select_button = QPushButton("Model/Dataset Dosyası Seç")
        select_button.clicked.connect(self.pick_file)
        file_row.addWidget(self.file_label)
        file_row.addWidget(select_button)
        file_layout.addLayout(file_row)
        
        # Model info display
        self.model_info_label = QLabel("")
        self.model_info_label.setStyleSheet("color: blue; font-size: 11px; padding: 5px;")
        self.model_info_label.setWordWrap(True)
        self.model_info_label.hide()
        file_layout.addWidget(self.model_info_label)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Mode selection
        self.mode_group = QGroupBox("Çalışma Modu")
        mode_layout = QFormLayout()
        self.mode_dataset = QCheckBox("A Modu: Dataset yükle ve yeni versiyon oluştur")
        self.mode_external = QCheckBox("B Modu: Dış model artefaktını ilişkilendir")
        self.mode_external.setChecked(True)
        self.mode_dataset.stateChanged.connect(self._ensure_single_mode)
        self.mode_external.stateChanged.connect(self._ensure_single_mode)
        mode_layout.addRow(self.mode_dataset)
        mode_layout.addRow(self.mode_external)
        
        self.version_strategy_group = QGroupBox("Version Stratejisi")
        version_strategy_layout = QFormLayout()
        
        self.use_existing_version = QCheckBox("Mevcut versiyona deploy et (risky)")
        self.use_untrained_version = QCheckBox("Train edilmemiş versiyona deploy et")
        self.use_untrained_version.setChecked(True)
        
        version_strategy_layout.addRow(self.use_existing_version)
        version_strategy_layout.addRow(self.use_untrained_version)
        self.version_strategy_group.setLayout(version_strategy_layout)
        mode_layout.addRow(self.version_strategy_group)

        self.dataset_description = QLineEdit()
        self.dataset_description.setPlaceholderText("Dataset açıklaması (opsiyonel)")
        mode_layout.addRow("Dataset açıklaması", self.dataset_description)

        self.train_checkbox = QCheckBox("Yükleme sonrası training tetikle")
        mode_layout.addRow(self.train_checkbox)

        self.storage_note_input = QLineEdit()
        self.storage_note_input.setPlaceholderText("Artefakt depolama notu (örn. S3 URL)")
        mode_layout.addRow("Depolama notu", self.storage_note_input)

        self.mode_group.setLayout(mode_layout)
        layout.addWidget(self.mode_group)

        self.result_view = QTextEdit()
        self.result_view.setReadOnly(True)
        layout.addWidget(self.result_view)

        action_row = QHBoxLayout()
        self.execute_button = QPushButton("Seçili işlemi çalıştır")
        self.execute_button.clicked.connect(self.execute)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        action_row.addWidget(self.execute_button)
        action_row.addWidget(self.progress)
        layout.addLayout(action_row)

        container.setLayout(layout)
        self.setCentralWidget(container)

    # ------------------------------------------------------------------
    # Mode toggling
    # ------------------------------------------------------------------
    def _ensure_single_mode(self) -> None:
        sender = self.sender()
        if sender == self.mode_dataset and self.mode_dataset.isChecked():
            self.mode_external.setChecked(False)
        elif sender == self.mode_external and self.mode_external.isChecked():
            self.mode_dataset.setChecked(False)
        elif not self.mode_dataset.isChecked() and not self.mode_external.isChecked():
            self.mode_external.setChecked(True)

    # ------------------------------------------------------------------
    # Selection + file picking
    # ------------------------------------------------------------------
    def _on_selection_changed(self) -> None:
        selected = self.tree.selectedItems()
        if not selected:
            self.selected_workspace = None
            self.selected_project = None
            self.selected_version = None
            return

        item = selected[0]
        node_type = item.data(0, Qt.UserRole)
        if node_type == "workspace":
            self.selected_workspace = item.data(0, Qt.UserRole + 1)
            self.selected_project = None
            self.selected_version = None
        elif node_type == "project":
            self.selected_workspace = item.data(0, Qt.UserRole + 1)
            self.selected_project = item.data(0, Qt.UserRole + 2)
            self.selected_version = None
        elif node_type == "version":
            self.selected_workspace = item.data(0, Qt.UserRole + 1)
            self.selected_project = item.data(0, Qt.UserRole + 2)
            self.selected_version = item.data(0, Qt.UserRole + 3)

    def pick_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Model veya dataset dosyası seç",
            str(Path.home()),
            "Model/Dataset (*.pt *.onnx *.engine *.zip *.tflite *.pb)",
        )
        if not file_path:
            return
        self.selected_file = Path(file_path)
        self.file_label.setText(self.selected_file.name)
        
        # Auto-detect model info if it's a .pt file
        if self.selected_file.suffix.lower() == '.pt':
            try:
                model_info = detect_model_info(self.selected_file)
                is_compatible, message = check_compatibility(model_info)
                
                # Display model info
                info_text = f"🔍 Tespit Edilen: {model_info.display_name}\n"
                if is_compatible:
                    info_text += "✅ Roboflow SDK ile uyumlu"
                    self.model_info_label.setStyleSheet("color: green; font-size: 11px; padding: 5px; background-color: #e8f5e9;")
                else:
                    info_text += f"⚠️ SDK ile uyumlu değil\n"
                    info_text += f"Ultralytics gereksinimi: {model_info.compatible_ultralytics}"
                    self.model_info_label.setStyleSheet("color: orange; font-size: 11px; padding: 5px; background-color: #fff3e0;")
                
                self.model_info_label.setText(info_text)
                self.model_info_label.show()
                
                # Log the detection
                log_event(
                    self.logger,
                    "model_detected",
                    filename=self.selected_file.name,
                    model_type=model_info.model_type,
                    version=model_info.version,
                    architecture=model_info.architecture,
                    compatible=is_compatible
                )
                
            except Exception as e:
                self.model_info_label.setText(f"ℹ️ Model bilgisi tespit edilemedi: {str(e)[:50]}...")
                self.model_info_label.setStyleSheet("color: gray; font-size: 11px; padding: 5px;")
                self.model_info_label.show()
        else:
            self.model_info_label.hide()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def refresh_hierarchy(self) -> None:
        if not self.config.api_key:
            QMessageBox.warning(
                self,
                "API anahtarı yok",
                "ROBOFLOW_API_KEY ortam değişkeni veya .env dosyasında tanımlanmalı.",
            )
            return

        worker = FunctionWorker(self._load_hierarchy)
        worker.signals.finished.connect(self._populate_tree)
        worker.signals.error.connect(self._handle_refresh_error)
        self._start_worker(worker, busy_message="Projeler alınıyor…")

    def _load_hierarchy(self) -> dict[str, dict[str, list]]:
        hierarchy: dict[str, dict[str, list]] = {}
        for workspace in self.client.list_workspaces():
            workspace_slug = workspace.get("id") or workspace.get("slug")
            if not workspace_slug:
                continue
            hierarchy[workspace_slug] = {}
            for project in self.client.list_projects(workspace_slug):
                # Extract project slug from full ID (e.g., "ozokur/a-xauau" -> "a-xauau")
                project_id = project.get("id", "")
                if "/" in project_id:
                    project_slug = project_id.split("/", 1)[1]  # Take part after first /
                else:
                    project_slug = project.get("slug") or project.get("name") or project_id
                
                if not project_slug:
                    continue
                versions = self.client.list_versions(workspace_slug, project_slug)
                hierarchy[workspace_slug][project_slug] = versions
        return hierarchy

    def _populate_tree(self, data: Dict[str, Dict[str, list]]) -> None:
        self.progress.hide()
        self.tree.clear()
        for workspace, projects in data.items():
            workspace_item = QTreeWidgetItem([workspace, "Workspace", ""])
            workspace_item.setData(0, Qt.UserRole, "workspace")
            workspace_item.setData(0, Qt.UserRole + 1, workspace)
            self.tree.addTopLevelItem(workspace_item)
            for project, versions in projects.items():
                project_item = QTreeWidgetItem([project, "Project", ""])
                project_item.setData(0, Qt.UserRole, "project")
                project_item.setData(0, Qt.UserRole + 1, workspace)
                project_item.setData(0, Qt.UserRole + 2, project)
                workspace_item.addChild(project_item)
                for version in versions:
                    version_name = version.get("version") or version.get("id") or "unknown"
                    note = version.get("description") or ""
                    version_item = QTreeWidgetItem([version_name, "Version", note])
                    version_item.setData(0, Qt.UserRole, "version")
                    version_item.setData(0, Qt.UserRole + 1, workspace)
                    version_item.setData(0, Qt.UserRole + 2, project)
                    version_item.setData(0, Qt.UserRole + 3, str(version_name))
                    project_item.addChild(version_item)
        self.tree.expandAll()
        self.statusBar().showMessage("Liste güncellendi")

    def _handle_refresh_error(self, error: Exception) -> None:
        self.progress.hide()
        self.statusBar().showMessage("Listeleme başarısız")
        if isinstance(error, RoboflowAPIError):
            QMessageBox.critical(self, "Roboflow API hatası", str(error))
        else:
            QMessageBox.critical(self, "Hata", str(error))

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    def execute(self) -> None:
        if not self.selected_workspace or not self.selected_project:
            QMessageBox.warning(self, "Seçim yok", "Lütfen bir workspace ve proje seçin.")
            return

        if self.mode_external.isChecked():
            # Determine target version based on strategy
            target_version = None
            
            if self.use_untrained_version.isChecked():
                # Find a version without a trained model
                try:
                    versions = self.client.list_versions(
                        self.selected_workspace,
                        self.selected_project
                    )
                    if versions:
                        # Sort by version number (highest first)
                        sorted_versions = sorted(
                            versions, 
                            key=lambda v: int(v.get('version', 0)),
                            reverse=True
                        )
                        
                        # Look for a version without trained model
                        # Roboflow API doesn't always provide this info, so we'll try the latest
                        target_version = str(sorted_versions[0].get('version'))
                        
                        self.statusBar().showMessage(
                            f"Seçilen versiyon: {target_version} (Eğer hata alırsanız, yeni dataset version oluşturun)"
                        )
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Versiyon Bulunamadı",
                        f"Uygun versiyon bulunamadı: {e}\n\n"
                        "Lütfen Roboflow'da yeni bir dataset version oluşturun."
                    )
                    return
            else:
                # Use manually selected version
                target_version = self.selected_version
            
            if not target_version:
                QMessageBox.warning(
                    self,
                    "Versiyon Seçilmedi",
                    "Lütfen bir versiyon seçin veya otomatik seçimi aktif edin.",
                )
                return
                
            if not self.selected_file or not validate_model_extension(self.selected_file):
                QMessageBox.warning(
                    self,
                    "Dosya hatası",
                    "Lütfen .pt/.onnx/.engine/.tflite/.pb uzantılı bir model dosyası seçin.",
                )
                return
            
            # Check model compatibility before deployment
            if self.selected_file.suffix.lower() == '.pt':
                try:
                    model_info = detect_model_info(self.selected_file)
                    is_compatible, message = check_compatibility(model_info)
                    
                    if not is_compatible:
                        # YOLOv11 is actually supported by Roboflow, but needs different ultralytics version
                        if model_info.version == "v11":
                            reply = QMessageBox.warning(
                                self,
                                "YOLOv11 İçin Ultralytics Güncelleme Gerekli",
                                f"✅ YOLOv11 Roboflow tarafından destekleniyor!\n\n"
                                f"Ancak ultralytics versiyonu güncellenmeli:\n"
                                f"• Mevcut: 8.0.196\n"
                                f"• Gerekli: <=8.3.40\n\n"
                                f"🔧 Hızlı Çözüm:\n"
                                f"Terminal'de şu komutu çalıştırın:\n"
                                f"  bash setup_yolov11.sh\n\n"
                                f"🚀 Alternatif: Local Inference\n"
                                f"  python inference_model.py --source image.jpg --model {model_info.file_path.name}\n\n"
                                f"Şimdi setup scriptini çalıştırmak ister misiniz?",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.Yes
                            )
                            
                            if reply == QMessageBox.Yes:
                                QMessageBox.information(
                                    self,
                                    "Terminal'e Geçin",
                                    "Lütfen terminal'e gidin ve şu komutu çalıştırın:\n\n"
                                    "bash setup_yolov11.sh\n\n"
                                    "Kurulum tamamlandıktan sonra uygulamayı yeniden başlatın."
                                )
                            self.statusBar().showMessage("YOLOv11 için ultralytics güncelleme gerekli")
                            return
                        else:
                            reply = QMessageBox.warning(
                                self,
                                "Model Uyumsuzluğu Tespit Edildi",
                                f"⚠️ {model_info.display_name} şu anki kurulumla uyumlu değil!\n\n"
                                f"Ultralytics gereksinimi: {model_info.compatible_ultralytics}\n"
                                f"Mevcut versiyon: 8.0.196\n\n"
                                f"🔧 Önerilen Çözümler:\n"
                                f"1. Local Inference kullanın (inference_model.py)\n"
                                f"2. Roboflow Web UI'dan model train edin\n"
                                f"3. YOLOv8 formatında model kullanın\n\n"
                                f"Yine de devam etmek istiyor musunuz?\n"
                                f"(Başarısız olma ihtimali yüksek)",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No
                            )
                            
                            if reply == QMessageBox.No:
                                self.statusBar().showMessage("İşlem iptal edildi")
                                return
                        
                except Exception as e:
                    # If detection fails, continue anyway
                    pass
            
            worker = FunctionWorker(
                self.uploader.link_external_model,
                workspace=self.selected_workspace,
                project=self.selected_project,
                version=target_version,
                file_path=self.selected_file,
                storage_note=self.storage_note_input.text() or None,
            )
        else:
            if not self.selected_file or self.selected_file.suffix.lower() != ".zip":
                QMessageBox.warning(
                    self,
                    "Dataset arşivi gerekli",
                    "A Modu için sıkıştırılmış (.zip) dataset arşivi seçmelisiniz.",
                )
                return
            worker = FunctionWorker(
                self.uploader.upload_dataset,
                workspace=self.selected_workspace,
                project=self.selected_project,
                dataset_zip_path=self.selected_file,
                trigger_training=self.train_checkbox.isChecked(),
                description=self.dataset_description.text(),
            )

        worker.signals.finished.connect(self._handle_execution_success)
        worker.signals.error.connect(self._handle_execution_error)
        self._start_worker(worker, busy_message="İşlem çalışıyor…")

    def _handle_execution_success(self, result: Any) -> None:
        self.progress.hide()
        self.statusBar().showMessage("İşlem tamamlandı")
        
        # Format result in a user-friendly way
        if isinstance(result, dict):
            formatted_result = self._format_result(result)
        else:
            formatted_result = str(result)
        
        self.result_view.setPlainText(formatted_result)
        log_event(self.logger, "ui_operation_completed", result=str(result))

    def _handle_execution_error(self, error: Exception) -> None:
        self.progress.hide()
        self.statusBar().showMessage("İşlem başarısız")
        
        error_msg = str(error)
        
        # Check for specific error patterns
        if "already has a trained model" in error_msg:
            QMessageBox.critical(
                self, 
                "Version Zaten Trained Model İçeriyor", 
                "Bu version'da zaten Roboflow'da train edilmiş bir model var.\n\n"
                "🔧 Çözüm Seçenekleri:\n"
                "1. Roboflow'da yeni bir dataset version oluşturun\n"
                "2. Train edilmemiş başka bir version seçin\n"
                "3. Mevcut trained modeli silin (Roboflow web UI'dan)\n\n"
                f"Detay: {error_msg}"
            )
        elif "C3k2" in error_msg or "Weights only load failed" in error_msg:
            QMessageBox.critical(
                self,
                "Model Versiyon Uyumsuzluğu",
                "Model dosyası SDK ile uyumlu değil.\n\n"
                "🔧 Çözüm:\n"
                "• Roboflow Web UI'dan model train edin\n"
                "• VEYA local inference için inference_model.py kullanın\n"
                "• Detaylı kılavuz: WEB_UPLOAD_GUIDE.md\n\n"
                f"Teknik detay: {error_msg[:200]}..."
            )
        elif isinstance(error, RoboflowAPIError):
            QMessageBox.critical(self, "Roboflow API Hatası", error_msg)
        else:
            QMessageBox.critical(self, "Hata", error_msg)
            
        log_event(self.logger, "ui_operation_failed", error=error_msg)

    # ------------------------------------------------------------------
    # Result formatting
    # ------------------------------------------------------------------
    def _format_result(self, result: Dict[str, Any]) -> str:
        """Format operation result in a user-friendly way."""
        lines = []
        
        # Operation info
        op_id = result.get("operation_id", "N/A")
        lines.append(f"✅ İşlem Başarılı!")
        lines.append(f"─" * 60)
        lines.append(f"İşlem ID: {op_id}")
        
        # Artifact info
        artifact = result.get("artifact", {})
        if artifact:
            lines.append(f"\n📦 Model Bilgileri:")
            lines.append(f"   • Dosya: {artifact.get('filename', 'N/A')}")
            lines.append(f"   • Boyut: {artifact.get('size_bytes', 0) / (1024*1024):.2f} MB")
            lines.append(f"   • SHA256: {artifact.get('sha256', 'N/A')[:16]}...")
            lines.append(f"   • Konum: {artifact.get('storage_url', 'N/A')}")
        
        # Manifest info
        manifest = result.get("manifest")
        if manifest:
            lines.append(f"\n📄 Manifest: {manifest}")
        
        # Deployment status
        api_resp = result.get("api_response", {})
        if isinstance(api_resp, dict):
            if api_resp.get("status") == "deployed":
                lines.append(f"\n🚀 Roboflow'a yüklendi!")
                lines.append(f"   Workspace: {api_resp.get('workspace')}")
                lines.append(f"   Project: {api_resp.get('project')}")
                lines.append(f"   Version: {api_resp.get('version')}")
            elif "error" in api_resp:
                lines.append(f"\n⚠️  Roboflow'a yüklenemedi (local'de saklandı)")
                lines.append(f"   Hata: {api_resp.get('error', 'Unknown')}")
        
        lines.append(f"\n{'─' * 60}")
        lines.append(f"🎉 Model başarıyla işlendi!")
        
        return "\n".join(lines)
    
    # ------------------------------------------------------------------
    # Operation History Viewer
    # ------------------------------------------------------------------
    def _view_operation_history(self) -> None:
        """Show operation history in a dialog."""
        import json
        from pathlib import Path
        from datetime import datetime
        
        manifests_dir = self.config.manifests_dir
        if not manifests_dir.exists():
            QMessageBox.information(
                self,
                "İşlem Geçmişi",
                "Henüz hiç işlem yapılmamış."
            )
            return
        
        # Load manifests
        manifests = []
        for manifest_file in sorted(manifests_dir.glob("*.json"), reverse=True):
            try:
                with open(manifest_file) as f:
                    data = json.load(f)
                    manifests.append(data)
            except Exception:
                pass
        
        if not manifests:
            QMessageBox.information(
                self,
                "İşlem Geçmişi",
                "Henüz hiç işlem yapılmamış."
            )
            return
        
        # Build history text
        history_text = []
        history_text.append(f"📊 İşlem Geçmişi ({len(manifests)} işlem)\n")
        history_text.append("=" * 70 + "\n\n")
        
        for manifest in manifests[:20]:  # Show latest 20
            op_id = manifest.get('op_id', 'N/A')
            mode = manifest.get('mode', 'N/A')
            status = manifest.get('status', 'N/A')
            written_at = manifest.get('written_at', 'N/A')
            workspace = manifest.get('workspace', 'N/A')
            project = manifest.get('project', 'N/A')
            version = manifest.get('target_version', 'N/A')
            
            status_icon = "✅" if status == "success" else "⚠️" if status == "partial_success" else "❌"
            
            # Format timestamp
            try:
                dt = datetime.fromisoformat(written_at.replace('Z', '+00:00'))
                ts_formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                ts_formatted = written_at
            
            history_text.append(f"{status_icon} [{ts_formatted}] {op_id}\n")
            history_text.append(f"   Mode: {mode}\n")
            history_text.append(f"   Target: {workspace}/{project}/v{version}\n")
            history_text.append(f"   Status: {status}\n")
            
            if 'artifact' in manifest:
                artifact = manifest['artifact']
                size_mb = artifact.get('size_bytes', 0) / 1024 / 1024
                history_text.append(f"   File: {artifact.get('filename', 'N/A')} ({size_mb:.2f} MB)\n")
            
            if 'api_response' in manifest:
                api_resp = manifest['api_response']
                if isinstance(api_resp, dict):
                    if api_resp.get('status') == 'deployed':
                        history_text.append(f"   🚀 Roboflow'a deploy edildi!\n")
                    elif 'error' in api_resp:
                        error = api_resp.get('error', 'Unknown')[:80]
                        history_text.append(f"   ⚠️ Error: {error}...\n")
            
            history_text.append("\n")
        
        # Show in dialog
        dialog = QMessageBox(self)
        dialog.setWindowTitle("İşlem Geçmişi")
        dialog.setText("".join(history_text))
        dialog.setIcon(QMessageBox.Information)
        dialog.exec()
    
    # ------------------------------------------------------------------
    # Worker helper
    # ------------------------------------------------------------------
    def _start_worker(self, worker: FunctionWorker, *, busy_message: str) -> None:
        self.progress.show()
        self.statusBar().showMessage(busy_message)
        self.thread_pool.start(worker)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(960, 720)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
