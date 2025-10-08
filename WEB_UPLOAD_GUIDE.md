# 🌐 Roboflow Web UI'dan Model Upload Kılavuzu

## Sorun: SDK Versiyon Uyumsuzluğu

Roboflow SDK `ultralytics==8.0.196` gerektiriyor ama bu PyTorch 2.8 ile uyumlu değil. 

**En kolay çözüm**: Roboflow Web UI'dan manuel upload

## 📋 Adım Adım Kılavuz

### 1. Roboflow'da Dataset Version Oluştur

1. [Projenize gidin](https://app.roboflow.com/ozokur/a-xauau)
2. **"Versions"** sekmesine tıklayın
3. **"Generate New Version"** butonuna tıklayın
4. Preprocessing/Augmentation ayarlarını yapın
5. **"Generate"** tıklayın
6. ⚠️ **"Train Model"** butonuna TIKLAMAYIN!

### 2. Model Upload (Web UI)

#### Yöntem A: Roboflow Train İle (Önerilen)

Aslında Roboflow'un kendi train sistemi en güvenilir:

1. Dataset version'da **"Train Model"** butonuna tıklayın
2. Model türünü seçin (YOLOv8, YOLOv5, vb.)
3. Training ayarlarını yapın
4. **"Start Training"** tıklayın
5. Training tamamlandığında model otomatik deploy edilir

#### Yöntem B: Lokal Model İçin Alternatif

Eğer kendi modelinizi kullanmak istiyorsanız:

**UYARI**: Roboflow Web UI'da doğrudan custom model upload özelliği yok. 
Sadece Roboflow'da train edilen modeller destekleniyor.

### 3. Kendi Modelinizi Kullanma Yöntemleri

#### A) Local Inference (Uygulamamız) ✅

```bash
cd /Users/ozanokur/projeler/roboflow
source .venv/bin/activate

# Herhangi bir görüntü ile inference
python inference_model.py --source ~/Downloads/test_image.jpg
```

Model dosyanız ne olursa olsun (YOLOv8, YOLOv11, vb.) local inference çalışır!

#### B) Roboflow Inference API

Kendi modelinizi Roboflow'a yüklemeden Roboflow Inference API ile kullanabilirsiniz:

```python
from roboflow import Roboflow
from ultralytics import YOLO

# Kendi modeliniz
model = YOLO("/Users/ozanokur/Downloads/yolov8n.pt")

# Inference
results = model.predict("image.jpg")
```

#### C) Roboflow Universe'e Public Upload

Modelinizi toplulukla paylaşmak isterseniz:

1. [Roboflow Universe](https://universe.roboflow.com/upload) gidin
2. "Upload Model" tıklayın
3. Model dosyanızı yükleyin
4. Public olarak paylaşılır

## 🎯 Önerilen Workflow

### Senaryo 1: Roboflow'da Train Etmek İsterseniz
```
Dataset → Generate Version → Train Model → Auto Deploy ✅
```

### Senaryo 2: Kendi Modelinizi Kullanmak
```
Model → Local Inference (inference_model.py) ✅
Model → Roboflow Universe (Public sharing) ✅
Model → Roboflow SDK Deploy ❌ (Versiyon uyumsuzluğu)
```

## 💡 Neden SDK Çalışmıyor?

- **Roboflow SDK**: `ultralytics==8.0.196` gerektirir
- **Sisteminiz**: `PyTorch 2.8.0` kullanıyor
- **Sorun**: PyTorch 2.8'in güvenlik değişiklikleri eski ultralytics ile uyumsuz
- **Sonuç**: Model yükleme hatası

## 🔧 Teknik Detaylar

```
Can't get attribute 'C3k2' → YOLOv11 modülü
ultralytics 8.0.196 → YOLOv8 destekliyor, YOLOv11 değil
PyTorch 2.8 → weights_only=True (güvenlik)
ultralytics 8.0.196 → weights_only desteklemiyor
```

## ✅ Çözüm Özeti

| Yöntem | Çalışır mı? | Önerilen? |
|--------|-------------|-----------|
| Roboflow Web Train | ✅ | ⭐⭐⭐ En iyi |
| Local Inference | ✅ | ⭐⭐⭐ Hızlı |
| Roboflow Universe | ✅ | ⭐⭐ Public için |
| SDK Deploy | ❌ | ⚠️ Versiyon sorunu |

---

**Son Tavsiye**: Roboflow'da train edin veya local inference kullanın! 🚀

