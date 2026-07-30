// motor_control_high_performance.ino
// ACCELSTEPPER YOK - SAF HIZ
// Hedef: 80 mikrosaniye adım aralığına (Ultra Hız) ulaşmak

// --- PIN TANIMLARI ---
#define STEP_X_PIN 3  
#define DIR_X_PIN 6
#define ENABLE_PIN 8 

#define STEP_Y_PIN 2  
#define DIR_Y_PIN 5

#define LASER_PIN 12
#define EMERGENCY_STOP_PIN 9 

// --- AYARLAR ---
// Manuel koddaki o meşhur hız değeri:
const int MIN_STEP_DELAY = 50;   // EN YÜKSEK HIZ (80 mikrosaniye gecikme)
const int MAX_STEP_DELAY = 2000; // BAŞLANGIÇ HIZI (Yavaş)
const int ACCEL_STEP = 10;        // Hızlanma yumuşaklığı (Düşük sayı = Daha yumuşak)

// --- DEĞİŞKENLER ---
// Hedeflenen Gecikme (Serial'den gelen emre göre)
long targetDelayX = 0; // 0 = Dur
long targetDelayY = 0;

// Anlık Gecikme (Motorun şu anki hızı)
double currentDelayX = 0;
double currentDelayY = 0;

// Zamanlayıcılar
unsigned long lastStepTimeX = 0;
unsigned long lastStepTimeY = 0;

// Yön Durumu
bool dirX = true;
bool dirY = true;

void setup() {
  // Python kodunla uyumlu olsun diye 9600
  // Ama 115200 yaparsan veri akışı daha pürüzsüz olur.
  Serial.begin(115200); 

  pinMode(STEP_X_PIN, OUTPUT);
  pinMode(DIR_X_PIN, OUTPUT);
  pinMode(STEP_Y_PIN, OUTPUT);
  pinMode(DIR_Y_PIN, OUTPUT);
  
  pinMode(ENABLE_PIN, OUTPUT);
  pinMode(LASER_PIN, OUTPUT); digitalWrite(LASER_PIN, LOW);
  pinMode(EMERGENCY_STOP_PIN, INPUT_PULLUP);

  // Sürücüleri Aktif Et
  digitalWrite(ENABLE_PIN, LOW);

  // TMC Yön Düzeltmesi (Gerekirse false/true değiştir)
  // Bu kodda kütüphane olmadığı için yönü manual kontrol ediyoruz.
  // Aşağıda processCommand içinde yön mantığı var.
  
  Serial.println("OK,HIGH_PERFORMANCE_READY");
}

void loop() {
  // 1. Acil Durdurma
  if (digitalRead(EMERGENCY_STOP_PIN) == LOW) {
    targetDelayX = 0; targetDelayY = 0;
    currentDelayX = 0; currentDelayY = 0;
    return;
  }

  // 2. Serial Komut Okuma
  if (Serial.available()) {
    parseSerial();
  }

  // 3. X Motorunu Sür (RAMPING Algoritması)
  if (targetDelayX > 0) { // Eğer hareket emri varsa
    
    // Hızlanma / Yavaşlama Mantığı
    if (currentDelayX == 0) currentDelayX = MAX_STEP_DELAY; // İlk kalkış
    
    if (currentDelayX > targetDelayX) {
      currentDelayX -= 0.05; // Hızlan (Gecikmeyi azalt) -> Buradaki 0.05 ivmeyi belirler
    } else if (currentDelayX < targetDelayX) {
      currentDelayX += 0.05; // Yavaşla
    }

    // Adım Atma
    if (micros() - lastStepTimeX >= (unsigned long)currentDelayX) {
      lastStepTimeX = micros();
      digitalWrite(STEP_X_PIN, HIGH);
      delayMicroseconds(2); // TMC için kısa sinyal yeterli
      digitalWrite(STEP_X_PIN, LOW);
    }
  } else {
    currentDelayX = 0; // Dur
  }

  // 4. Y Motorunu Sür
  if (targetDelayY > 0) {
    
    if (currentDelayY == 0) currentDelayY = MAX_STEP_DELAY; 
    
    if (currentDelayY > targetDelayY) {
      currentDelayY -= 0.05; 
    } else if (currentDelayY < targetDelayY) {
      currentDelayY += 0.05;
    }

    if (micros() - lastStepTimeY >= (unsigned long)currentDelayY) {
      lastStepTimeY = micros();
      digitalWrite(STEP_Y_PIN, HIGH);
      delayMicroseconds(2);
      digitalWrite(STEP_Y_PIN, LOW);
    }
  } else {
    currentDelayY = 0;
  }

  // Durum Raporu (Sistemi yavaşlatmamak için çok seyrek gönder)
  static unsigned long lastStatus = 0;
  if (millis() - lastStatus > 500) {
    // Burada pozisyon saymıyoruz çünkü AccelStepper yok.
    // Sadece hareket durumunu bildiriyoruz.
    if (targetDelayX > 0 || targetDelayY > 0) Serial.println("STS,MOVING");
    else Serial.println("STS,READY");
    lastStatus = millis();
  }
}

// --- KOMUT İŞLEME ---
void parseSerial() {
  static String cmdBuffer = "";
  char c = Serial.read();
  
  if (c == '\n') {
    processCommand(cmdBuffer);
    cmdBuffer = "";
  } else {
    cmdBuffer += c;
  }
}

void processCommand(String cmd) {
  cmd.trim();
  int comma1 = cmd.indexOf(',');
  int comma2 = cmd.indexOf(',', comma1 + 1);

  if (cmd.startsWith("SPD")) {
    // FORMAT: SPD,HIZ_X,HIZ_Y (0-1000 arası değer gönder)
    // 0 = Dur
    // 1000 = Maksimum Hız (80us gecikme)
    // -1000 = Maksimum Hız (Ters Yön)
    
    if (comma1 > 0 && comma2 > comma1) {
      int valX = cmd.substring(comma1 + 1, comma2).toInt();
      int valY = cmd.substring(comma2 + 1).toInt();

      // --- X HESAPLAMA ---
      if (valX == 0) {
        targetDelayX = 0;
      } else {
        // Yön Belirle
        bool dir = (valX > 0); 
        digitalWrite(DIR_X_PIN, dir ? HIGH : LOW); // Yönü buradan tersine çevirebilirsin
        
        // Hızı Gecikmeye Çevir (Mapping)
        // Gelen 1 ile 1000 arasındaki hızı, 2000us ile 80us arasına çeviriyoruz.
        int speed = abs(valX);
        if (speed > 1000) speed = 1000; // Limit
        
        // map(değer, min_giriş, max_giriş, min_çıkış, max_çıkış)
        // Hız (1000) arttıkça gecikme (80) azalmalı.
        targetDelayX = map(speed, 1, 1000, MAX_STEP_DELAY, MIN_STEP_DELAY);
      }

      // --- Y HESAPLAMA ---
      if (valY == 0) {
        targetDelayY = 0;
      } else {
        bool dir = (valY > 0); 
        digitalWrite(DIR_Y_PIN, dir ? HIGH : LOW);
        
        int speed = abs(valY);
        if (speed > 1000) speed = 1000;
        targetDelayY = map(speed, 1, 1000, MAX_STEP_DELAY, MIN_STEP_DELAY);
      }
    }
  } 
  else if (cmd.startsWith("LZR,")) {
    bool on = (cmd.substring(4) == "1");
    digitalWrite(LASER_PIN, on ? HIGH : LOW);
  }
}
