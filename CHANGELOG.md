# Changelog

All notable changes to this project will be documented in this file.

## [1.2.1] - 2025-10-08

### Fixed
- 🐛 **Critical**: YOLOv11 detection now works correctly via C3k2 error analysis
- 🛡️ Added pre-deployment compatibility check with user confirmation
- ⚠️ Smart warning dialog for incompatible models before upload attempt

### Changed
- 🔍 Improved fallback detection: C3k2 error → YOLOv11, not YOLOv8
- 🎯 User can now choose to proceed or cancel when incompatible model detected

## [1.2.0] - 2025-10-08

### Added
- 🔍 **Auto Model Detection**: Automatically detect YOLO model version (v5, v8, v11)
- 🎯 **Smart Deployment**: Use detected model architecture for deployment
- ⚡ **Real-time Compatibility Check**: Show compatibility warnings before upload
- 📊 **Model Info Display**: Visual feedback showing detected model type and version
- 📝 **Enhanced Logging**: Log model detection events for audit trail

### Changed
- 🔄 Updated app version display to v1.2.0
- 🎨 Enhanced file selection UI with model info panel
- 🔧 Improved deployment with automatic model type detection

### Technical Details
- New `model_detector.py` module for YOLO version detection
- Detects YOLOv5 (C3), YOLOv8 (C2f), YOLOv11 (C3k2, C2PSA)
- Shows green badge for compatible models (YOLOv8)
- Shows orange badge for incompatible models (YOLOv11)
- Fallback to filename-based detection if torch load fails

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
| 1.2.1 | 2025-10-08 | Fixed YOLOv11 detection, pre-deployment checks |
| 1.2.0 | 2025-10-08 | Auto model detection, smart deployment |
| 1.1.0 | 2025-10-08 | Model deployment, smart versioning, inference |
| 1.0.0 | 2025-10-08 | Initial release, basic upload |

---

**Semantic Versioning**: MAJOR.MINOR.PATCH
- **MAJOR**: Incompatible API changes
- **MINOR**: New features (backwards-compatible)
- **PATCH**: Bug fixes (backwards-compatible)

