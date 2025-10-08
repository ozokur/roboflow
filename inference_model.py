#!/usr/bin/env python3
"""Run inference using a trained YOLO model."""

import sys
from pathlib import Path
from ultralytics import YOLO
import cv2

def run_inference(model_path: str, source: str, save_dir: str = "outputs/inference"):
    """
    Run inference on images/video/webcam.
    
    Args:
        model_path: Path to the YOLO model (.pt file)
        source: Image file, video file, directory, or 0 for webcam
        save_dir: Directory to save results
    """
    print(f"🚀 Inference Başlıyor...")
    print(f"   Model: {model_path}")
    print(f"   Kaynak: {source}")
    print(f"   Çıktı: {save_dir}\n")
    
    # Load model
    model = YOLO(model_path)
    print(f"✅ Model yüklendi: {model_path}\n")
    
    # Run inference
    results = model.predict(
        source=source,
        save=True,
        save_dir=save_dir,
        conf=0.25,  # Confidence threshold
        show=False,  # Don't show in window (save instead)
        verbose=True
    )
    
    # Print results
    print(f"\n📊 Sonuçlar:")
    for i, result in enumerate(results):
        print(f"\n   Görüntü {i + 1}:")
        print(f"   • Tespit Sayısı: {len(result.boxes)}")
        
        if len(result.boxes) > 0:
            # Get detection details
            for box in result.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                class_name = result.names[cls]
                print(f"     - {class_name}: {conf:.2%} güven")
    
    print(f"\n✅ Inference tamamlandı!")
    print(f"📁 Sonuçlar kaydedildi: {save_dir}/predict/")
    return results


def main():
    """Main entry point for inference."""
    import argparse
    
    parser = argparse.ArgumentParser(description="YOLO Model Inference")
    parser.add_argument(
        "--model",
        type=str,
        default="app/outputs/artifacts/yolov8n.pt",
        help="Path to YOLO model (.pt file)"
    )
    parser.add_argument(
        "--source",
        type=str,
        required=True,
        help="Image file, video file, directory, or 0 for webcam"
    )
    parser.add_argument(
        "--save-dir",
        type=str,
        default="app/outputs/inference",
        help="Directory to save results"
    )
    
    args = parser.parse_args()
    
    # Check if model exists
    if not Path(args.model).exists():
        print(f"❌ Model bulunamadı: {args.model}")
        print(f"\n💡 Kullanılabilir modeller:")
        artifacts_dir = Path("app/outputs/artifacts")
        if artifacts_dir.exists():
            for model in artifacts_dir.glob("*.pt"):
                print(f"   - {model}")
        sys.exit(1)
    
    # Check if source exists (if not webcam)
    if args.source != "0" and not Path(args.source).exists():
        print(f"❌ Kaynak bulunamadı: {args.source}")
        sys.exit(1)
    
    # Run inference
    run_inference(args.model, args.source, args.save_dir)


if __name__ == "__main__":
    main()

