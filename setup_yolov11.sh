#!/usr/bin/env bash
# Setup script for YOLOv11 model deployment
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

echo "🔧 YOLOv11 Model Deployment için Kurulum"
echo "=========================================="
echo ""

# Activate venv
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
else
    echo "❌ Virtual environment bulunamadı!"
    echo "Önce: ./scripts/bootstrap_macos.sh"
    exit 1
fi

# Check current ultralytics version
CURRENT_VERSION=$(python -c "import ultralytics; print(ultralytics.__version__)" 2>/dev/null || echo "not installed")
echo "Mevcut ultralytics: $CURRENT_VERSION"
echo "YOLOv11 gereksinimi: 8.3.40"
echo ""

# Confirm
read -p "ultralytics'i 8.3.40 versiyonuna güncellemek istiyor musunuz? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "İşlem iptal edildi."
    exit 0
fi

echo ""
echo "📦 ultralytics güncelleniyor..."

# Upgrade ultralytics for YOLOv11
pip uninstall -y ultralytics
pip install "ultralytics==8.3.40"

# Also need to upgrade roboflow if needed
pip install --upgrade roboflow

echo ""
echo "✅ Kurulum tamamlandı!"
echo ""
echo "🎯 Şimdi ne yapmalı:"
echo "1. Uygulamayı başlatın: python -m app.ui.main_window"
echo "2. YOLOv11 modelinizi seçin (sise.pt)"
echo "3. Deploy butonuna tıklayın"
echo ""
echo "⚠️ NOT: YOLOv8 modelleri için tekrar:"
echo "   pip install ultralytics==8.0.196"
echo ""

