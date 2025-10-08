# Roboflow Uploader

PySide6 tabanlı bu uygulama, Roboflow workspace → project → version hiyerarşisini listeler ve iki farklı modda yükleme/ilişkilendirme işlemleri sunar:

- **A Modu (Dataset Upload):** Yerel bir dataset arşivini (.zip) Roboflow projesine yeni versiyon olarak yükler ve opsiyonel olarak training tetikler.
- **B Modu (Dış Model Artefaktı):** Yerel model dosyasını (.pt/.onnx/.engine/…) güvenli depoya (varsayılan: `outputs/artifacts/`) kopyalar ve seçili versiyona checksum ile birlikte metadata/not ekler.

## Tek satır kurulum (macOS)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/<your-user>/<your-repo>/main/scripts/bootstrap_macos.sh)"
```

Yukarıdaki komut Homebrew, Python 3.11 ve sanal ortamı hazırlar, bağımlılıkları kurar ve GUI'yi başlatır. Kurulum tamamlandıktan
sonra macOS'ta Finder üzerinden çift tıklayarak çalıştırmak için `scripts/macos-launcher.command` dosyasını kullanabilirsiniz.

## Yerel geliştirme

1. `.env.template` dosyasını `.env` olarak kopyalayın ve `ROBOFLOW_API_KEY` değerini girin.
2. Sanal ortam kurun ve bağımlılıkları yükleyin:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

3. Uygulamayı başlatın:

   ```bash
   scripts/run_app.sh
   ```

## Dizin yapısı

```
app/
 ├─ core/
 │   ├─ config.py
 │   ├─ logging_util.py
 │   ├─ roboflow_client.py
 │   ├─ uploader.py
 │   └─ versioning.py
 ├─ ui/
 │   ├─ main_window.py
 │   └─ widgets/
outputs/
 ├─ artifacts/
 └─ manifests/
logs/
 ├─ app.log
 └─ events.jsonl
scripts/
 ├─ bootstrap_macos.sh
 └─ run_app.sh
.env.template
pyproject.toml
```

## Loglama & Manifestler

- `logs/app.log`: İnsan tarafından okunabilir günlükler.
- `logs/events.jsonl`: JSON satırları halinde yapısal olaylar.
- `outputs/manifests/*.json`: Her yükleme/ilişkilendirme işlemi için manifest.

## Güvenlik notları

- API anahtarları **asla** depoya eklenmemelidir. `.env` dosyanızı `.gitignore` ile koruyoruz.
- Uygulama, UI üzerinde maskelenmiş API anahtarını gösterir.

## Hata yönetimi

- 401/403: Yanlış/eksik API anahtarı → kullanıcıya uyarı.
- 404: Workspace/Project bulunamadı → GUI uyarısı.
- Timeout ve ağ hataları → kullanıcıya bilgi verilir; manifest `status` alanına hata düşer.
- Kullanıcı iptali (ör. dosya seçmeme) durumunda işlem başlatılmaz.

## Geliştirme notları

- `RoboflowClient.upload_dataset` ve `trigger_training` metotları şablon olarak bırakılmıştır. Roboflow REST API veya resmi SDK'ya göre genişletin.
- Yeni özelliklerde semantik versiyonlama için `app/core/config.py` içindeki `APP_VERSION` değerini güncelleyin.
