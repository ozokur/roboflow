# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2025-10-08

### Added
- 🚀 Roboflow model deployment with SDK integration
- 📊 Automatic version detection (latest untrained version)
- 🔍 Workspace/Project/Version hierarchy browser
- 💾 Local model artifact storage with SHA256 checksum
- 📝 Comprehensive manifest generation for each operation
- 🎯 Smart error handling with solution suggestions
- 📚 Multiple deployment guides (DEPLOYMENT_GUIDE.md, WEB_UPLOAD_GUIDE.md, INFERENCE_GUIDE.md)
- 🧪 Local model inference script (inference_model.py)
- ⚙️ Version strategy options (auto/manual)

### Changed
- ♻️ Updated API client to handle Roboflow response formats
- 🔄 Improved project/version ID extraction from nested API responses
- 🎨 Enhanced result display with user-friendly formatting

### Fixed
- 🐛 Workspace listing (API returns single workspace, not list)
- 🐛 Project listing (nested in workspace object)
- 🐛 Version number extraction from full IDs
- 🐛 File path handling for model deployment
- 🐛 Interactive prompt handling (stdin mock for GUI)

### Known Issues
- ⚠️ SDK requires `ultralytics==8.0.196` which conflicts with PyTorch 2.8+
- ⚠️ YOLOv11 models (C3k2 module) incompatible with old ultralytics
- ⚠️ Trained versions cannot accept custom model uploads

### Workarounds
- ✅ Use Roboflow Web UI for training models
- ✅ Use local inference script for any YOLO model
- ✅ Generate new untrained dataset versions for deployment

## [1.0.0] - 2025-10-08

### Added
- 🎉 Initial release
- 📱 PySide6 GUI application
- 🔑 Roboflow API authentication
- 📁 Basic file selection and upload
- 📋 Two-mode operation (Dataset/External Model)
- 🔒 Secure API key management (.env)
- 📝 Logging system (app.log, events.jsonl)
- 🍎 macOS one-click bootstrap script

---

## Version History

| Version | Date | Key Features |
|---------|------|--------------|
| 1.1.0 | 2025-10-08 | Model deployment, smart versioning, inference |
| 1.0.0 | 2025-10-08 | Initial release, basic upload |

---

**Semantic Versioning**: MAJOR.MINOR.PATCH
- **MAJOR**: Incompatible API changes
- **MINOR**: New features (backwards-compatible)
- **PATCH**: Bug fixes (backwards-compatible)

