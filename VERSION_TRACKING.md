# 📊 Versiyon Takibi ve Log Yönetimi

## Uygulama Versiyonu

**Mevcut Versiyon**: `v1.2.1` (Build: 2025-10-08)

### Yeni v1.2.1 Özellikleri:
- 🐛 **Düzeltme**: YOLOv11 modelleri artık doğru tespit ediliyor (C3k2 error analysis)
- 🛡️ Deploy öncesi uyumluluk kontrolü
- ⚠️ Kullanıcıya uyumsuz model için onay isteme

### v1.2.0 Özellikleri:
- 🔍 Otomatik model versiyonu tespiti (YOLOv5, YOLOv8, YOLOv11)
- ✅ Real-time uyumluluk kontrolü
- 🎨 Model bilgisi görsel gösterimi
- 📊 Model detay loglama

Uygulama [Semantic Versioning](https://semver.org/) kullanır:
- **MAJOR**: Geriye uyumsuz API değişiklikleri
- **MINOR**: Yeni özellikler (geriye uyumlu)
- **PATCH**: Hata düzeltmeleri (geriye uyumlu)

## Log Sistemi

### 📁 Log Dosyaları

Loglar tarih bazlı organize edilir:

```
app/logs/
├── app-2025-10-08.log          # Bugünün human-readable logu
├── events-2025-10-08.jsonl     # Bugünün yapısal event logu
├── app.log -> app-2025-10-08.log         # Symlink (en son)
└── events.jsonl -> events-2025-10-08.jsonl  # Symlink (en son)
```

### 📝 Log Formatları

#### 1. Human-Readable Log (`app-*.log`)
```
2025-10-08 17:59:28 [INFO] roboflow_uploader — Roboflow Uploader v1.1.0 (build: 2025-10-08) logger initialized
2025-10-08 17:59:29 [INFO] roboflow_uploader.client — event=rf_list_workspaces {"count": 1}
```

#### 2. Yapısal Event Log (`events-*.jsonl`)
```json
{"ts": "2025-10-08T14:59:28.123Z", "level": "INFO", "event": "rf_model_deployed", "workspace": "ozokur", "project": "a-xauau", "version": "12"}
```

### 📦 Manifest Dosyaları

Her işlem için ayrı manifest:

```
app/outputs/manifests/
├── ext-20251008-145906.json
├── ext-20251008-145928.json
└── ext-20251008-150425.json
```

**Manifest İçeriği:**
```json
{
  "op_id": "ext-20251008-150425",
  "app_version": "1.1.0",
  "mode": "external_model",
  "workspace": "ozokur",
  "project": "plastic-bottles-ip5yb-uziag-tmuqm",
  "target_version": "1",
  "artifact": {
    "filename": "yolov8n.pt",
    "sha256": "29bf4c988681711dfc40264682efbe188e74666aaada540d6e70f610eab08890",
    "size_bytes": 6242787,
    "storage_url": "file:///..."
  },
  "status": "success",
  "api_response": {...}
}
```

## 🔍 İşlem Geçmişini Görüntüleme

### GUI'den

GUI'de **"📊 İşlem Geçmişini Görüntüle"** butonuna tıklayın.

### Terminal'den

```bash
# Tüm geçmişi göster
python view_history.py

# Sadece manifests
python view_history.py --manifests

# Sadece events
python view_history.py --events

# İstatistikler
python view_history.py --stats

# İlk 100 event
python view_history.py --events --limit 100

# Belirli bir tarihin logları
python view_history.py --date 2025-10-08
```

### Çıktı Örneği

```
📊 İşlem Geçmişi (3 işlem)
================================================================================

✅ [2025-10-08 15:04:25] ext-20251008-150425
   Mode: external_model
   Target: ozokur/plastic-bottles-ip5yb-uziag-tmuqm/v1
   Status: success
   File: yolov8n.pt (5.95 MB)
   🚀 Deployed successfully!

⚠️ [2025-10-08 14:59:28] ext-20251008-145928
   Mode: external_model
   Target: ozokur/plastic-bottles-ip5yb-uziag-tmuqm/v1
   Status: partial_success
   File: yolov8n.pt (5.95 MB)
   ⚠️ Error: Model deployment failed: Can't get attribute 'C3k2'...
```

## 📈 İstatistikler

```bash
python view_history.py --stats
```

Çıktı:
```
📊 Statistics
================================================================================
Total operations: 5
  ✅ Successful: 2
  ⚠️ Partial: 2
  ❌ Failed: 1

Total events: 156

Top events:
  • rf_list_workspaces: 45
  • rf_list_projects: 42
  • rf_list_versions: 38
  • rf_model_deployed: 2
```

## 🗂️ Log Temizleme

Eski logları temizlemek için:

```bash
# 30 günden eski logları sil
find app/logs -name "*.log" -mtime +30 -delete
find app/logs -name "*.jsonl" -mtime +30 -delete

# Eski manifests'leri sil (dikkatli!)
find app/outputs/manifests -name "*.json" -mtime +90 -delete
```

## 🔐 Versiyon Bilgisi

Uygulama her başlatıldığında versiyonu loga kaydeder:

```
2025-10-08 17:59:28 [INFO] roboflow_uploader — Roboflow Uploader v1.1.0 (build: 2025-10-08) logger initialized
```

GUI'de sağ üstte versiyon görünür:
```
v1.1.0 (Build: 2025-10-08)
```

## 📝 Yeni Versiyon Oluşturma

1. `app/core/config.py` dosyasında `APP_VERSION` ve `APP_BUILD_DATE` güncelleyin
2. `CHANGELOG.md` dosyasına yeni versiyon notlarını ekleyin
3. Commit yapın:
   ```bash
   git commit -m "chore: bump version to 1.2.0"
   git tag v1.2.0
   git push && git push --tags
   ```

## 🎯 Best Practices

1. **Log Rotation**: Eski logları düzenli temizleyin
2. **Manifest Backup**: Önemli manifests'leri yedekleyin
3. **Version Tagging**: Her release için git tag kullanın
4. **Changelog**: Her değişikliği CHANGELOG.md'de dokümante edin
5. **Monitoring**: Hata oranlarını düzenli kontrol edin

---

**Son güncelleme**: 2025-10-08 | **Versiyon**: 1.2.1

