# AGENTS.md — macOS One‑Click GUI Roboflow Uploader (Codex/Cloud‑Ready)

> **Amaç:** Tek tıkla (macOS) kurulup çalışan, GUI’li, log + versiyon yönetimli; Roboflow workspace→project→version hiyerarşisini listeleyip **seçtiğin yerel model dosyasını** doğru hedefe **ilişkilendiren/yüklemeyi köprüleyen** bir uygulama. Codex/Cloud üzerinde de aynı komutla başlatılabilir.

> **Güvenlik:** API anahtarını **repo’ya koyma**. `.env.template` kullan; gerçek anahtarı yerelde `.env` olarak veya Codex/Cloud ortam değişkeni olarak tanımla.

---

## 1) Özellikler

- **GUI** (PySide6): Workspace/Project/Version ağaç görünümü + arama, **Model Dosyası Seç** (.pt/.onnx/.engine/…), ilerleme çubuğu, sonuç paneli.
- **Roboflow Entegrasyonu**:
  - **Listeleme:** Workspace, Project, Version’lar.
  - **A Modu — Dataset/Training (doğal):** Dataset upload → yeni version → (opsiyonel) training tetikleme → deploy bilgisi.
  - **B Modu — Dış Model Köprüsü:** Yerel modeli güvenli depoya/outputs’a kaydet, Roboflow version’a **metadata/not** olarak **link + checksum** ekle (audit trail & navigasyon).
- **Loglama:** `logs/app.log` (insan okunur) + `logs/events.jsonl` (yapısal).
- **Versiyonlama:** Uygulama **SemVer**; her işlem için `outputs/manifests/*.json` manifest.
- **Tek Tık Kurulum (macOS):** `scripts/bootstrap_macos.sh` ile tüm gereklilikleri yükler, venv kurar, çalıştırır.

---

## 2) Dizin Yapısı

```
app/
 ├─ ui/
 │   ├─ main_window.py
 │   └─ widgets/
 ├─ core/
 │   ├─ roboflow_client.py
 │   ├─ uploader.py
 │   ├─ versioning.py
 │   ├─ logging_util.py
 │   └─ config.py
 ├─ outputs/
 │   ├─ manifests/
 │   └─ artifacts/
 ├─ logs/
 │   ├─ app.log
 │   └─ events.jsonl
 ├─ scripts/
 │   ├─ bootstrap_macos.sh
 │   └─ run_app.sh
 ├─ .env.template
 ├─ pyproject.toml  (veya requirements.txt)
 └─ README.md
```

---

## 3) .env Yönetimi

**Repo’da şu dosyayı tut:**

```
# .env.template (commit edilecek)
ROBOFLOW_API_KEY=
APP_ENV=dev
```

**Yerelde gerçek dosya:**

```
# .env (commit ETME)
ROBOFLOW_API_KEY=PASTE_YOUR_KEY_HERE
APP_ENV=dev
```

> Codex/Cloud: Ortam değişkeni olarak **ROBOFLOW\_API\_KEY** ayarla (Settings → Environment). `.env` gerekmeyebilir.

> **Uyarı:** Kullanıcı talimatıyla paylaşılan anahtarlar **asla** depoya commit edilmemelidir.

---

## 4) Tek Tık Kurulum (macOS)

**Kullanım:**

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/<user>/<repo>/<branch>/scripts/bootstrap_macos.sh)"
```

``** (önerilen içerik):**

```bash
#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"

# 1) Xcode CLT (gerekirse)
if ! xcode-select -p >/dev/null 2>&1; then
  echo "[bootstrap] Installing Xcode Command Line Tools…"
  xcode-select --install || true
fi

# 2) Homebrew (gerekirse)
if ! command -v brew >/dev/null 2>&1; then
  echo "[bootstrap] Installing Homebrew…"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$HOME/.zprofile"
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# 3) Python ve bağımlılıklar
brew update
brew install python@3.11 git pkg-config || true

# 4) Sanal ortam
PY=python3.11
if ! command -v $PY >/dev/null 2>&1; then PY=python3; fi
$PY -m venv .venv
source .venv/bin/activate
python -m pip install -U pip wheel setuptools

# 5) Bağımlılık kurulumu (pyproject varsa)
if [ -f pyproject.toml ]; then
  pip install .
elif [ -f requirements.txt ]; then
  pip install -r requirements.txt
else
  # Minimal bağımlılıklar
  pip install PySide6 requests python-dotenv rich
fi

# 6) Çalıştırma
scripts/run_app.sh
```

``** (önerilen içerik):**

```bash
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"
source .venv/bin/activate

# .env yükle
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

python - << 'PY'
import sys, os, json, hashlib, time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Basit bootstrap: log/outputs klasörleri
for p in ["logs", "outputs/manifests", "outputs/artifacts"]:
    Path(p).mkdir(parents=True, exist_ok=True)

# GUI veya hızlı smoke-test
try:
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
    app = QApplication(sys.argv)
    w = QWidget(); w.setWindowTitle("Roboflow Uploader (macOS)")
    layout = QVBoxLayout(w)
    layout.addWidget(QLabel("Workspace/Project/Version → Model Dosyası İlişkilendirici"))
    layout.addWidget(QLabel(f"ROBOFLOW_API_KEY set: {'YES' if os.getenv('ROBOFLOW_API_KEY') else 'NO'}"))
    w.resize(560, 180); w.show()
    sys.exit(app.exec())
except Exception as e:
    print("[run_app] GUI error:", e)
    sys.exit(1)
PY
```

---

## 5) Roboflow İstemcisi (taslak)

``** (özet arayüz):**

```python
class RoboflowClient:
    def __init__(self, api_key: str): ...
    def list_workspaces(self) -> list[dict]: ...
    def list_projects(self, workspace: str) -> list[dict]: ...
    def list_versions(self, project_id: str) -> list[dict]: ...
    def append_version_note(self, project_id: str, version: str, note: str, meta: dict): ...
```

> Uygulamada resmi SDK veya REST uç noktaları kullanılabilir. **A modu** (dataset) doğrudan SDK ile; **B modu** (dış model) not/metadata ile ilişkilendirme uygular.

---

## 6) Loglama & Manifest

- `logs/app.log` — kısa metin log
- `logs/events.jsonl` — her satır bir olay (JSON)
- `outputs/manifests/…json` — her yükleme/ilişkilendirme operasyonu için manifest

Örnek JSONL:

```json
{"ts":"2025-10-08T13:10:11.123Z","level":"INFO","event":"rf_list_projects","count":12}
```

Örnek manifest:

```json
{
  "op_id": "upl-20251008-131041-7f3",
  "app_version": "1.0.0",
  "mode": "external_model",
  "workspace": "example-ws",
  "project": "bottle-defect",
  "target_version": "v18",
  "artifact": {
    "filename": "yolov8.pt",
    "sha256": "…",
    "size_bytes": 73400320,
    "storage_url": "file:///.../outputs/artifacts/yolov8.pt"
  },
  "notes": "Uploaded local model; linked in Roboflow version notes.",
  "started_at": "2025-10-08T13:10:30Z",
  "ended_at": "2025-10-08T13:10:41Z",
  "status": "success"
}
```

---

## 7) Hata Yönetimi

- **401/403**: Anahtar yok/yanlış → GUI’de kırmızı banner, “Environment/.env kontrol” butonu
- **404**: Workspace/Project erişimi → izinleri doğrula
- **Timeout/Büyük dosya**: Otomatik **B Modu** öner (metadata link)
- **Kullanıcı iptali**: İşlemi atomik kes, manifest’e `"status":"cancelled"` yaz

---

## 8) Çalıştırma (Yerel & Codex/Cloud)

- **Yerel (tek satır):** bkz. §4 curl/b

# Short Answer

The assistant created a canvas document containing the requested **AGENTS.md** with a macOS one-click bootstrap script, directory layout, logging/versioning guidance, Roboflow integration notes, and run instructions suitable for GitHub/Codex.

