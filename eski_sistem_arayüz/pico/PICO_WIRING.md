# 🔌 Raspberry Pi Pico 2 - TMC2209 Bağlantı Şeması

## 📋 İçindekiler
1. [Pin Konfigürasyonu](#pin-konfigürasyonu)
2. [TMC2209 Bağlantıları](#tmc2209-bağlantıları)
3. [Manuel Mikroadım Ayarı](#manuel-mikroadım-ayarı)
4. [UART Bağlantısı (İlerleyen Aşama)](#uart-bağlantısı)
5. [Güç Kaynağı](#güç-kaynağı)

---

## Pin Konfigürasyonu

### Raspberry Pi Pico 2 Pin Atamaları

```
┌─────────────────────────────────────┐
│     Raspberry Pi Pico 2             │
├─────────────────────────────────────┤
│ GPIO0  (TX)  ──► Python ile UART    │
│ GPIO1  (RX)  ──► Python ile UART    │
├─────────────────────────────────────┤
│ GPIO2  ──────► X Motor STEP         │
│ GPIO3  ──────► X Motor DIR          │
│ GPIO4  ──────► X Motor MS1          │
│ GPIO5  ──────► X Motor MS2          │
├─────────────────────────────────────┤
│ GPIO6  ──────► Y Motor STEP         │
│ GPIO7  ──────► Y Motor DIR          │
│ GPIO8  ──────► Y Motor MS1          │
│ GPIO9  ──────► Y Motor MS2          │
├─────────────────────────────────────┤
│ GPIO10 ──────► ENABLE (Her iki TMC) │
│ GPIO11 ──────► Lazer Kontrol        │
│ GPIO12 ──────► Acil Durdur (Buton)  │
├─────────────────────────────────────┤
│ GND    ──────► Ortak Toprak         │
│ 3.3V   ──────► TMC2209 VCC_IO       │
└─────────────────────────────────────┘
```

---

## TMC2209 Bağlantıları

### X Motoru TMC2209 Sürücü

```
TMC2209 #1 (X Motor)
┌─────────────────────────────────────┐
│ VCC_IO    ──► 3.3V (Pico)           │
│ GND       ──► GND (Pico + Güç)      │
│ VM        ──► +12V / +24V (Motor)   │
├─────────────────────────────────────┤
│ STEP      ──► GPIO2                 │
│ DIR       ──► GPIO3                 │
│ EN        ──► GPIO10 (ortak)        │
├─────────────────────────────────────┤
│ MS1 (CFG1)──► GPIO4                 │
│ MS2 (CFG2)──► GPIO5                 │
│ MS3 (CFG3)──► GND (sabit)           │
├─────────────────────────────────────┤
│ 1A        ──► Motor Bobin 1+        │
│ 1B        ──► Motor Bobin 1-        │
│ 2A        ──► Motor Bobin 2+        │
│ 2B        ──► Motor Bobin 2-        │
├─────────────────────────────────────┤
│ PDN_UART  ──► VCC_IO (3.3V) (şimdilik) │
│ CLK       ──► Bağlantısız (NC)      │
│ DIAG      ──► Bağlantısız (NC)      │
│ INDEX     ──► Bağlantısız (NC)      │
└─────────────────────────────────────┘
```

### Y Motoru TMC2209 Sürücü

```
TMC2209 #2 (Y Motor)
┌─────────────────────────────────────┐
│ VCC_IO    ──► 3.3V (Pico)           │
│ GND       ──► GND (Pico + Güç)      │
│ VM        ──► +12V / +24V (Motor)   │
├─────────────────────────────────────┤
│ STEP      ──► GPIO6                 │
│ DIR       ──► GPIO7                 │
│ EN        ──► GPIO10 (ortak)        │
├─────────────────────────────────────┤
│ MS1 (CFG1)──► GPIO8                 │
│ MS2 (CFG2)──► GPIO9                 │
│ MS3 (CFG3)──► GND (sabit)           │
├─────────────────────────────────────┤
│ 1A        ──► Motor Bobin 1+        │
│ 1B        ──► Motor Bobin 1-        │
│ 2A        ──► Motor Bobin 2+        │
│ 2B        ──► Motor Bobin 2-        │
├─────────────────────────────────────┤
│ PDN_UART  ──► VCC_IO (3.3V) (şimdilik) │
│ CLK       ──► Bağlantısız (NC)      │
│ DIAG      ──► Bağlantısız (NC)      │
│ INDEX     ──► Bağlantısız (NC)      │
└─────────────────────────────────────┘
```

---

## Manuel Mikroadım Ayarı

### MS1 ve MS2 Pinleri ile Ayar (UART kullanmadan)

```
┌─────┬─────┬──────────────┐
│ MS1 │ MS2 │ Mikroadım    │
├─────┼─────┼──────────────┤
│ LOW │ LOW │ 1/8  ✅ ÖNE. │
│ HIGH│ HIGH│ 1/16         │
│ HIGH│ LOW │ 1/32         │
│ LOW │ HIGH│ 1/64         │
└─────┴─────┴──────────────┘

NOT: MS3 (CFG3) her zaman GND'ye bağlı
```

### Başlangıç için Önerilen Ayar

```python
# motor_control_pico.py içinde:
set_microstepping('both', '1/8')  # ✅ Dengeli performans
```

**1/8 mikroadım avantajları:**
- İyi hassasiyet
- Orta düzey titreşim azaltma
- Hızlı hareket desteği
- Stabil performans

---

## UART Bağlantısı (İlerleyen Aşama)

### UART ile Gelişmiş Kontrol

TMC2209'un UART pinini kullanarak akım, mikroadım ve mod ayarlarını yazılımdan değiştirebilirsiniz.

```
┌─────────────────────────────────────┐
│ İLERİ SEVİYE - UART MOD             │
├─────────────────────────────────────┤
│ Pico GPIO4 (TX) ──► TMC RX (X)      │
│ Pico GPIO5 (RX) ──► TMC TX (X)      │
│                                     │
│ PDN_UART ──► 1kΩ ──► VCC_IO (3.3V)  │
│                                     │
│ * Her TMC için slave address ayarı  │
│   gerekir (MS1_AD0, MS2_AD1)        │
└─────────────────────────────────────┘
```

**UART ile yapabilecekleriniz:**
- Akım ayarı (0-2A arası hassas kontrol)
- Mikroadım ayarı (1/1'den 1/256'ya)
- StealthChop/SpreadCycle geçişi
- Stallguard (takılma algılama)
- Sürücü durumu okuma (sıcaklık, akım vb.)

**Kullanım:**
```python
from tmc2209_uart import TMC2209

tmc = TMC2209(uart_id=1, tx_pin=4, rx_pin=5, slave_address=0x00)
tmc.init_driver(run_current=1000, microstep='1/16', stealthchop=True)
```

---

## Güç Kaynağı

### Gereksinimler

```
┌─────────────────────────────────────────┐
│ 1. Pico Güç Kaynağı                     │
│    └─► USB (5V) veya VIN (1.8-5.5V)     │
│                                         │
│ 2. Motor Güç Kaynağı (VM)               │
│    └─► 12V-24V DC (Önerilen: 24V)      │
│    └─► Akım: En az 2A per motor        │
│                                         │
│ 3. Ortak Toprak (GND)                   │
│    └─► Pico GND + Motor Güç GND        │
│        (Mutlaka birleştirilmeli!)       │
└─────────────────────────────────────────┘
```

### Bağlantı Şeması

```
              ┌─────────────┐
              │  Güç Kaynağı │
              │   (12-24V)   │
              └──────┬───────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼────┐            ┌────▼────┐
    │ TMC2209 │            │ TMC2209 │
    │  (X)    │            │  (Y)    │
    └────┬────┘            └────┬────┘
         │                       │
         └───────────┬───────────┘
                     │
              ┌──────▼──────┐
              │  Pico GND   │
              └─────────────┘

⚠️ UYARI: Motor güç GND ile Pico GND mutlaka birleştirilmeli!
```

### Güç Koruma Önerileri

1. **Kondansatör:** VM ve GND arasına 100µF elektrolitik + 100nF seramik
2. **Sigorta:** Motor güç hattına 2A sigorta
3. **Diyot:** Güç kaynağına ters polarite koruma diyotu (1N4007)

---

## Ek Bağlantılar

### Lazer Modülü

```
┌──────────────────────────────────┐
│ Pico GPIO11 ──► Transistor Base  │
│                 (BC547 veya 2N2222) │
│                                  │
│ Transistor Collector ──► Lazer + │
│ Transistor Emitter ──► GND       │
│                                  │
│ Lazer - ──► GND                  │
│                                  │
│ * 5V lazer için direkt Pico'dan │
│   veya harici 5V kaynaktan       │
└──────────────────────────────────┘
```

### Acil Durdur Butonu

```
┌──────────────────────────────────┐
│ Pico GPIO12 (Pull-up aktif)      │
│     │                            │
│     ├──── Buton ──── GND         │
│     │                            │
│     └──── 10kΩ ──── 3.3V (iç)   │
│                                  │
│ Basıldığında: LOW (Dur komutu)   │
│ Normal durum: HIGH               │
└──────────────────────────────────┘
```

---

## Test Prosedürü

### 1. İlk Güç Açma

```bash
1. Güç bağlantılarını kontrol et
2. Motor bağlantılarını kontrol et
3. Önce Pico'yu USB ile güçlendir
4. Sonra motor güç kaynağını aç
5. LED'lerin yanıp yanmadığını kontrol et
```

### 2. Basit Test

```bash
# Pico'ya simple_test.py yükle
# Thonny veya mpremote ile:

mpremote fs cp simple_test.py :
mpremote run simple_test.py
```

### 3. Ana Program

```bash
# motor_control_pico.py'yi main.py olarak kaydet
mpremote fs cp motor_control_pico.py :main.py
mpremote reset
```

---

## Sorun Giderme

### Motor Hareket Etmiyor

- [ ] ENABLE pini LOW mu? (Aktif seviye)
- [ ] VM güç geliyor mu? (12-24V)
- [ ] GND ortak mı?
- [ ] Motor kabloları doğru mu? (multimetre ile test et)

### Motorlar Titriyor

- [ ] Mikroadım ayarını kontrol et (1/8 önerilen)
- [ ] Akım çok düşük olabilir (UART ile artır)
- [ ] Adım frekansı çok yüksek (hızı düşür)

### UART Çalışmıyor

- [ ] TX/RX pinleri ters bağlanmış olabilir (takas et)
- [ ] PDN_UART 1kΩ ile VCC_IO'ya bağlı mı?
- [ ] Baudrate doğru mu? (115200)
- [ ] Slave address doğru mu? (MS1_AD0, MS2_AD1)

---

## İleri Seviye: UART Geçiş Adımları

### Adım 1: Donanım Hazırlığı

```
1. PDN_UART pinini 1kΩ ile VCC_IO'ya bağla
2. TMC RX ──► Pico TX (GPIO4)
3. TMC TX ──► Pico RX (GPIO5)
4. Slave address pinlerini ayarla (MS1_AD0, MS2_AD1)
```

### Adım 2: Yazılım Güncellemesi

```python
# motor_control_pico.py'ye ekle:
from tmc2209_uart import TMC2209

# Setup içinde:
tmc_x = TMC2209(1, 4, 5, slave_address=0x00)
tmc_x.init_driver(run_current=1000, microstep='1/16')
```

### Adım 3: Test

```python
# Durum kontrolü
status = tmc_x.get_status()
print(status)
```

---

## Özet Checklist

- [x] Pico pin atamaları yapıldı
- [x] TMC2209 bağlantıları tanımlandı
- [x] Manuel mikroadım ayarı açıklandı
- [x] UART geçiş yolu hazırlandı
- [x] Güç kaynağı gereksinimleri belirlendi
- [x] Test prosedürü oluşturuldu

**Başarılar! 🚀**
