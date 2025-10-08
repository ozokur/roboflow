# 🚀 Model Inference Kullanım Kılavuzu

## Modelinizi Kullanma

Kaydedilmiş modelinizle görüntü, video veya webcam üzerinde tahmin yapabilirsiniz.

## 📋 Hızlı Başlangıç

### 1. Tek Görüntü Üzerinde Tahmin

```bash
cd /Users/ozanokur/projeler/roboflow
source .venv/bin/activate
python inference_model.py --source path/to/image.jpg
```

### 2. Klasördeki Tüm Görüntüler

```bash
python inference_model.py --source path/to/images/folder/
```

### 3. Video Dosyası Üzerinde

```bash
python inference_model.py --source path/to/video.mp4
```

### 4. Webcam ile Canlı Tahmin

```bash
python inference_model.py --source 0
```

### 5. Farklı Model Kullanma

```bash
python inference_model.py --model app/outputs/artifacts/your_model.pt --source image.jpg
```

## 🎛️ Parametreler

| Parametre | Açıklama | Varsayılan |
|-----------|----------|------------|
| `--model` | Model dosyası yolu (.pt) | `app/outputs/artifacts/yolov8n.pt` |
| `--source` | Görüntü/video/klasör/webcam (0) | **Zorunlu** |
| `--save-dir` | Sonuçların kaydedileceği klasör | `app/outputs/inference` |

## 📦 Kullanılabilir Modeller

Mevcut modellerinizi görmek için:

```bash
ls -lh app/outputs/artifacts/
```

## 📊 Sonuçlar

Inference sonuçları şuraya kaydedilir:
- **Klasör**: `app/outputs/inference/predict/`
- **Format**: Tespit edilen nesneler işaretlenmiş görüntüler

## 💡 Örnekler

### Örnek 1: Şişe Tespiti (Plastic Bottles Modeliniz)
```bash
python inference_model.py --source ~/Downloads/bottle_image.jpg
```

### Örnek 2: Toplu İşlem
```bash
python inference_model.py --source ~/Pictures/test_images/
```

### Örnek 3: Yüksek Güven Eşiği
Python scriptini düzenleyip `conf=0.5` yaparak daha yüksek güven eşiği kullanabilirsiniz.

## 🔧 İleri Seviye: Python'dan Kullanma

```python
from ultralytics import YOLO

# Model yükle
model = YOLO("app/outputs/artifacts/yolov8n.pt")

# Tahmin yap
results = model.predict(
    source="image.jpg",
    save=True,
    conf=0.25,
    iou=0.45
)

# Sonuçları işle
for result in results:
    boxes = result.boxes
    for box in boxes:
        print(f"Class: {result.names[int(box.cls)]}")
        print(f"Confidence: {float(box.conf):.2%}")
        print(f"Coordinates: {box.xyxy}")
```

## 📱 GUI Uygulaması İle Kullanma

Ana GUI uygulamasına inference özelliği eklemek isterseniz, lütfen belirtin!

## 🆘 Sorun Giderme

### Model Bulunamadı
```bash
# Mevcut modelleri kontrol edin
ls app/outputs/artifacts/*.pt
```

### GPU Kullanımı
```python
# GPU varsa otomatik kullanılır
# CPU'da zorlamak için:
model = YOLO("model.pt")
results = model.predict(source="image.jpg", device="cpu")
```

## 🎯 Performans İpuçları

1. **Batch İşlem**: Birden fazla görüntü için klasör kullanın
2. **GPU Hızlandırma**: CUDA yüklüyse otomatik kullanılır
3. **Confidence Threshold**: Çok fazla yanlış tespit varsa artırın
4. **Image Size**: Daha büyük görüntüler daha yavaş ama daha doğru

---

**🎉 Modeliniz hazır! İyi tahminler!**

