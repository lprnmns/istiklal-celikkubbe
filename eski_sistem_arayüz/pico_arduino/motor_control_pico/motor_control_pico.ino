/*
 * Hava Savunma Sistemi - Raspberry Pi Pico 2 Motor Kontrolü
 * Arduino IDE ile derlenecek
 * TMC2209 UART Kontrol Versiyon
 * 
 * ÖZELLIKLER:
 * - Çift eksen motor kontrolü (X/Y) - TMC2209 ile
 * - UART haberleşmesi üzerinden TMC konfigürasyonu
 * - Hızlanma/yavaşlama (ramping)
 * - Serial iletişim (⚡ 460800 baud - MAKSIMUM HİZ)
 * - Lazer kontrolü
 * - Acil durdur
 * 
 * KÜTÜPHANELER:
 * - TMCStepper: https://github.com/teemuatlut/TMCStepper
 * 
 * NOT:
 * - Ayrı UART hatları ile X ve Y motor kontrolü
 */

#include <TMCStepper.h>

// ============================================================================
// PIN TANIMLARI ve UART AYARLARI
// ============================================================================

// --- X MOTORU ---
#define STEP_X_PIN 14       // GPIO14
#define DIR_X_PIN 12        // GPIO12
#define X_SERIAL_TX 0       // UART0 TX
#define X_SERIAL_RX 1       // UART0 RX

// --- Y MOTORU ---
#define STEP_Y_PIN 15       // GPIO15
#define DIR_Y_PIN 13        // GPIO13
#define Y_SERIAL_TX 4       // UART1 TX
#define Y_SERIAL_RX 5       // UART1 RX

// --- DİĞER ---
#define ENABLE_PIN 10       // GPIO10
#define LASER_PIN 11        // GPIO11
#define EMERGENCY_STOP_PIN 18 // GPIO18

// --- TMC AYARLARI ---
#define R_SENSE 0.11f       // TwoTrees/MKS standart direnç
#define DRIVER_ADDRESS 0    // İki sürücü de ayrı UART hattında


// ============================================================================
// HIZ VE ZAMANLAMA AYARLARI
// ============================================================================

const unsigned long MIN_STEP_DELAY_US = 25;    // Minimum adım gecikmesi (maks hız)
const unsigned long MAX_STEP_DELAY_US = 2000;  // Maksimum adım gecikmesi (başlangıç)
// Eski sabit adım artışı çok yavaştı; üstel yaklaşım ile hızlı ve stabil ramping
const float ACCEL_ALPHA = 0.5;                 // Daha agresif ramping

// TMC2209 Ayarları
// --- TMC2209 AYARLARI (X MOTORU) ---
const uint16_t TMC_X_RMS_CURRENT_MA = 1000;    // 1000 mA (1 Amper)
const uint8_t TMC_X_MICROSTEPS = 32;           // 1/32 mikroadım
const uint8_t TMC_X_TOFF = 4;                  // Driver aktif
const uint8_t TMC_X_BLANK_TIME = 24;           // Blank time
const uint8_t TMC_X_SEMIN = 5;                 // Stallguard threshold

// --- TMC2209 AYARLARI (Y MOTORU) ---
const uint16_t TMC_Y_RMS_CURRENT_MA = 1000;    // 1000 mA (1 Amper)
const uint8_t TMC_Y_MICROSTEPS = 8;            // 1/8 mikroadım
const uint8_t TMC_Y_TOFF = 4;                  // Driver aktif
const uint8_t TMC_Y_BLANK_TIME = 24;           // Blank time
const uint8_t TMC_Y_SEMIN = 5;                 // Stallguard threshold

// ============================================================================
// GLOBAL DEĞİŞKENLER
// ============================================================================

// Hedef gecikme değerleri (0 = dur)
volatile long targetDelayX = 0;
volatile long targetDelayY = 0;

// Anlık gecikme değerleri
volatile double currentDelayX = 0.0;
volatile double currentDelayY = 0.0;

// Son adım zamanları (mikrosaniye)
volatile unsigned long lastStepTimeX = 0;
volatile unsigned long lastStepTimeY = 0;

// Komut buffer
String cmdBuffer = "";

// Durum raporu
unsigned long lastStatusTime = 0;

// ============================================================================
// TMC2209 UART OBJESI OLUŞTURMA
// ============================================================================
// TMCStepper(serial_address, R_SENSE, &serial_object)
// serial_address: 0 (ayrı hatlar kullanıyoruz)
// R_SENSE: 0.11 ohm (TwoTrees standart)

HardwareSerial &UART_X = Serial1;  // UART0 - X Motoru
HardwareSerial &UART_Y = Serial2;  // UART1 - Y Motoru

// TMC2209 sürücü nesneleri
TMC2209Stepper driverX(&UART_X, R_SENSE, DRIVER_ADDRESS);
TMC2209Stepper driverY(&UART_Y, R_SENSE, DRIVER_ADDRESS);

// ============================================================================
// MOTOR SÜRME FONKSİYONLARI
// ============================================================================

void motorTask() {
  /*
   * Ana motor sürme döngüsü
   * Her çağrıda her iki motoru da kontrol eder
   */
  
  unsigned long currentTime = micros();
  
  // Acil durdur kontrolü
  if (digitalRead(EMERGENCY_STOP_PIN) == LOW) {
    targetDelayX = 0;
    targetDelayY = 0;
    currentDelayX = 0.0;
    currentDelayY = 0.0;
    return;
  }
  
  // ========== X MOTORU ==========
  if (targetDelayX > 0) {
    // Hızlanma/yavaşlama
    if (currentDelayX == 0) {
      currentDelayX = MAX_STEP_DELAY_US;
    }
    // Üstel yaklaşım: hedefe hızlı, sarsıntısız yaklaş
    currentDelayX = currentDelayX + (targetDelayX - currentDelayX) * ACCEL_ALPHA;
    
    // Adım atma zamanı geldi mi?
    if (currentTime - lastStepTimeX >= (unsigned long)currentDelayX) {
      lastStepTimeX = currentTime;
      
      digitalWrite(STEP_X_PIN, HIGH);
      delayMicroseconds(2);  // TMC2209 için pulse genişliği
      digitalWrite(STEP_X_PIN, LOW);
    }
  } else {
    currentDelayX = 0.0;
  }
  
  // ========== Y MOTORU ==========
  if (targetDelayY > 0) {
    if (currentDelayY == 0) {
      currentDelayY = MAX_STEP_DELAY_US;
    }
    // Üstel yaklaşım: hedefe hızlı, sarsıntısız yaklaş
    currentDelayY = currentDelayY + (targetDelayY - currentDelayY) * ACCEL_ALPHA;
    
    if (currentTime - lastStepTimeY >= (unsigned long)currentDelayY) {
      lastStepTimeY = currentTime;
      
      digitalWrite(STEP_Y_PIN, HIGH);
      delayMicroseconds(2);
      digitalWrite(STEP_Y_PIN, LOW);
    }
  } else {
    currentDelayY = 0.0;
  }
}

// ============================================================================
// KOMUT İŞLEME
// ============================================================================

void processCommand(String cmd) {
  /*
   * Serial komutları işle
   * 
   * Komut formatları:
   * - SPD,x,y       : Hız ayarı (-1000 ~ 1000)
   * - LZR,0/1       : Lazer kontrol
   * - PING          : Bağlantı testi
   */
  
  cmd.trim();
  
  int comma1 = cmd.indexOf(',');
  int comma2 = cmd.indexOf(',', comma1 + 1);
  
  // ========== SPD KOMUTU ==========
  if (cmd.startsWith("SPD") && comma1 > 0 && comma2 > comma1) {
    int valX = cmd.substring(comma1 + 1, comma2).toInt();
    int valY = cmd.substring(comma2 + 1).toInt();
    
    Serial.print("DBG,SPD alındı: X="); Serial.print(valX); Serial.print(" Y="); Serial.println(valY);
    
    // X Motoru
    if (valX == 0) {
      targetDelayX = 0;
    } else {
      // Yön ayarla
      digitalWrite(DIR_X_PIN, (valX > 0) ? HIGH : LOW);
      
      // Hızı gecikmeye çevir
      int speed = min(abs(valX), 1000);
      targetDelayX = map(speed, 1, 1000, MAX_STEP_DELAY_US, MIN_STEP_DELAY_US);
      Serial.print("DBG,X: DIR="); Serial.print((valX > 0) ? "HIGH" : "LOW"); 
      Serial.print(" Delay="); Serial.println(targetDelayX);
    }
    
    // Y Motoru
    if (valY == 0) {
      targetDelayY = 0;
    } else {
      digitalWrite(DIR_Y_PIN, (valY > 0) ? HIGH : LOW);
      int speed = min(abs(valY), 1000);
      targetDelayY = map(speed, 1, 1000, MAX_STEP_DELAY_US, MIN_STEP_DELAY_US);
      Serial.print("DBG,Y: DIR="); Serial.print((valY > 0) ? "HIGH" : "LOW"); 
      Serial.print(" Delay="); Serial.println(targetDelayY);
    }
    Serial.println("OK,SPD");
  }
  
  // ========== LZR KOMUTU ==========
  else if (cmd.startsWith("LZR") && comma1 > 0) {
    int state = cmd.substring(comma1 + 1).toInt();
    digitalWrite(LASER_PIN, state ? HIGH : LOW);
    Serial.print("OK,LASER_");
    Serial.println(state);
  }
  
  // ========== PING KOMUTU ==========
  else if (cmd == "PING") {
    Serial.println("OK,PONG");
  }
  
  // ========== STP KOMUTU ==========
  else if (cmd == "STP") {
    targetDelayX = 0; targetDelayY = 0;
    currentDelayX = 0.0; currentDelayY = 0.0;
    Serial.println("OK,STOP");
  }
  
  // ========== HOM KOMUTU ==========
  else if (cmd == "HOM") {
    targetDelayX = 0; targetDelayY = 0;
    Serial.println("OK,HOME_DONE");
  }
  
  // ========== UNKNOWN KOMUTU ==========
  else {
    Serial.print("ERR,UNKNOWN_CMD: [");
    Serial.print(cmd);
    Serial.println("]");
  }
}

void parseSerial() {
  /*
   * Serial'den gelen karakterleri oku ve komut buffer'a ekle
   */
  while (Serial.available()) {
    char c = Serial.read();
    
    if (c == '\n' || c == '\r') {
      if (cmdBuffer.length() > 0) {
        processCommand(cmdBuffer);
        cmdBuffer = "";
      }
    } else {
      cmdBuffer += c;
    }
  }
}

// ============================================================================
// DURUM RAPORU
// ============================================================================

void sendStatus() {
  /*
   * Periyodik durum raporu gönder
   */
  unsigned long currentTime = millis();
  
  if (currentTime - lastStatusTime >= 500) {
    if (targetDelayX > 0 || targetDelayY > 0) {
      Serial.println("STS,MOVING");
    } else {
      Serial.println("STS,READY");
    }
    lastStatusTime = currentTime;
  }
}

// ============================================================================
// SETUP - BAŞLANGIÇ KURULUMU
// ============================================================================

void setup() {
  // 1. USB Serial (Python Haberleşmesi)
  Serial.begin(460800);
  while (!Serial && millis() < 3000);  // 3 saniye bekle
  
  // 2. UART Serial Kurulumu
  // Serial1 (UART0): X Motoru - GP0 (TX) / GP1 (RX) - Varsayılan
  Serial1.begin(115200);
  delay(50);
  
  // Serial2 (UART1): Y Motoru - GP4 (TX) / GP5 (RX) - Varsayılan
  Serial2.begin(115200);
  delay(50);

  // 3. Pin Modları
  pinMode(STEP_X_PIN, OUTPUT); 
  pinMode(DIR_X_PIN, OUTPUT);
  pinMode(STEP_Y_PIN, OUTPUT); 
  pinMode(DIR_Y_PIN, OUTPUT);
  pinMode(ENABLE_PIN, OUTPUT);
  pinMode(LASER_PIN, OUTPUT);
  pinMode(EMERGENCY_STOP_PIN, INPUT_PULLUP);

  digitalWrite(LASER_PIN, LOW);
  digitalWrite(DIR_X_PIN, LOW);
  digitalWrite(DIR_Y_PIN, LOW);
  digitalWrite(STEP_X_PIN, LOW);
  digitalWrite(STEP_Y_PIN, LOW);
  // NOT: ENABLE_PIN CNC Shield'de kısa devre - kontrol edilmiyor

  delay(100);

  // 4. Sürücü Konfigürasyonu (X EKSENİ)
  driverX.begin();
  driverX.toff(TMC_X_TOFF);                    // Sürücüyü aktifleştir
  driverX.blank_time(TMC_X_BLANK_TIME);
  driverX.rms_current(TMC_X_RMS_CURRENT_MA);  // RMS akımı ayarla
  driverX.microsteps(TMC_X_MICROSTEPS);       // Mikroadım ayarı
  driverX.pwm_autoscale(true);
  driverX.en_spreadCycle(false);               // StealthChop modu
  driverX.semin(TMC_X_SEMIN);                  // Stallguard threshold
  Serial.println("✓ X Motor TMC başlatıldı");
  
  delay(50);
  
  // 5. Sürücü Konfigürasyonu (Y EKSENİ)
  driverY.begin();
  driverY.toff(TMC_Y_TOFF);
  driverY.blank_time(TMC_Y_BLANK_TIME);
  driverY.rms_current(TMC_Y_RMS_CURRENT_MA);
  driverY.microsteps(TMC_Y_MICROSTEPS);
  driverY.pwm_autoscale(true);
  driverY.en_spreadCycle(false);
  driverY.semin(TMC_Y_SEMIN);
  Serial.println("✓ Y Motor TMC başlatıldı");

  delay(100);
  
  Serial.println("✓ Motor kontrolü hazır");
  
  // Başlangıç mesajı
  Serial.println("============================================");
  Serial.println("Hava Savunma - Pico 2 Motor Kontrol");
  Serial.println("TMC2209 UART Kontrol Versiyon");
  Serial.println("Baud Rate: 460800 (⚡ Maksimum Hız)");
  Serial.println("============================================");
  Serial.println("Pin Konfigürasyonu:");
  Serial.print("  X Motor: STEP="); Serial.print(STEP_X_PIN);
  Serial.print(", DIR="); Serial.print(DIR_X_PIN);
  Serial.print(", UART="); Serial.print(X_SERIAL_TX);
  Serial.print("/"); Serial.println(X_SERIAL_RX);
  
  Serial.print("  Y Motor: STEP="); Serial.print(STEP_Y_PIN);
  Serial.print(", DIR="); Serial.print(DIR_Y_PIN);
  Serial.print(", UART="); Serial.print(Y_SERIAL_TX);
  Serial.print("/"); Serial.println(Y_SERIAL_RX);
  
  Serial.print("  Kontrol: ENABLE="); Serial.print(ENABLE_PIN);
  Serial.print(", LASER="); Serial.print(LASER_PIN);
  Serial.print(", E-STOP="); Serial.println(EMERGENCY_STOP_PIN);
  
  Serial.println("--------------------------------------------");
  Serial.println("TMC2209 Ayarları (X Motoru):");
  Serial.print("  RMS Current: "); Serial.print(TMC_X_RMS_CURRENT_MA); Serial.println(" mA");
  Serial.print("  Microsteps: 1/"); Serial.println(TMC_X_MICROSTEPS);
  Serial.print("  toff: "); Serial.println(TMC_X_TOFF);
  Serial.println("TMC2209 Ayarları (Y Motoru):");
  Serial.print("  RMS Current: "); Serial.print(TMC_Y_RMS_CURRENT_MA); Serial.println(" mA");
  Serial.print("  Microsteps: 1/"); Serial.println(TMC_Y_MICROSTEPS);
  Serial.print("  toff: "); Serial.println(TMC_Y_TOFF);
  Serial.println("--------------------------------------------");
  Serial.println("OK,PICO_READY");
  Serial.println("============================================");
  
  delay(100);
}

// ============================================================================
// LOOP - ANA DÖNGÜ
// ============================================================================

void loop() {
  // 1. Serial komut okuma
  parseSerial();
  
  // 2. Motor kontrolü
  motorTask();
  
  // 3. Durum raporu
  sendStatus();
  
  // CPU'ya nefes aldır (opsiyonel)
  // delayMicroseconds(1);
}
