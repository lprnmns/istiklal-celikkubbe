import cv2

def main():
    print("Görüntü Testi Başlatılıyor...")
    print("Çıkış için 'Q' tuşuna basın.")
    
    # Daha önce çalışan ayar: Index 0, CAP_DSHOW
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    if not cap.isOpened():
        print("Kamera hiç açılamadı!")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Frame okunamadı (Veri yok)")
            break
            
        # Ortalama parlaklık değerini yazdır (0 ise tamamen siyah demektir)
        avg_brightness = frame.mean()
        print(f"\rParlaklık Değeri: {avg_brightness:.2f} (0=Siyah)", end="")
        
        cv2.imshow("Saf Goruntu Testi", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

