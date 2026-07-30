import cv2
import time

def test_camera(index, backend_name, backend_val):
    print(f"\n--- Test Ediliyor: Index {index}, Backend: {backend_name} ---")
    try:
        if backend_val is None:
            cap = cv2.VideoCapture(index)
        else:
            cap = cv2.VideoCapture(index, backend_val)
        
        if not cap.isOpened():
            print("❌ Kamera açılamadı.")
            return False
        
        # Çözünürlük ayarla
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # 10 frame okumayı dene
        success_count = 0
        for i in range(10):
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                success_count += 1
                print(f"Frame {i+1}: OK ({frame.shape})")
            else:
                print(f"Frame {i+1}: Başarısız")
            time.sleep(0.1)
            
        cap.release()
        
        if success_count > 0:
            print(f"✅ BAŞARILI! ({success_count}/10 frame)")
            return True
        else:
            print("❌ Görüntü alınamadı.")
            return False
            
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
        return False

def main():
    print("Kamera Tanılama Aracı Başlatılıyor...")
    
    # Test edilecek kombinasyonlar
    configs = [
        (0, "CAP_DSHOW", cv2.CAP_DSHOW),
        (0, "CAP_MSMF", cv2.CAP_MSMF),
        (0, "OTOMATIK", None),
        (1, "CAP_DSHOW (Index 1)", cv2.CAP_DSHOW), # İkinci kamera ihtimali
        (1, "OTOMATIK (Index 1)", None)
    ]
    
    working_config = None
    
    for idx, name, val in configs:
        if test_camera(idx, name, val):
            working_config = (idx, name, val)
            break
    
    if working_config:
        print(f"\n✨ ÇALIŞAN AYAR BULUNDU: Index {working_config[0]}, Backend {working_config[1]}")
        print("Lütfen bu ayarı 'config.py' veya 'main.py' içine uygulayın.")
    else:
        print("\n⛔ Hiçbir kamera ayarı çalışmadı. Kameranın başka bir program tarafından kullanılmadığından emin olun.")

if __name__ == "__main__":
    main()
