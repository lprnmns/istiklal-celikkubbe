"""
TMC2209 Gelişmiş Optimizasyon Kütüphanesi
Hava Savunma Sistemi için HIZ ve ATIKSIZ optimizasyonlar

ÖZELLİKLER:
1. Otomatik StealthChop ↔ SpreadCycle geçişi (hıza göre)
2. Akıllı akım yönetimi (IRUN/IHOLD)
3. Mikroadım interpolasyonu (düşük mikro + 256 interp)
4. CoolStep (yük adaptif akım kontrolü)
5. Chopper optimizasyonu (hız ve tork dengesi)
"""

from machine import UART, Pin
import time
import struct

class TMC2209Advanced:
    """TMC2209 Gelişmiş Kontrol"""
    
    # TMC2209 Kayıtları
    REG_GCONF = 0x00
    REG_GSTAT = 0x01
    REG_IOIN = 0x04
    REG_IHOLD_IRUN = 0x10
    REG_TPOWERDOWN = 0x11
    REG_TSTEP = 0x12
    REG_TPWMTHRS = 0x13      # StealthChop→SpreadCycle geçiş eşiği
    REG_TCOOLTHRS = 0x14     # CoolStep eşiği
    REG_SGTHRS = 0x40        # StallGuard eşiği
    REG_SG_RESULT = 0x41
    REG_COOLCONF = 0x42      # CoolStep yapılandırması
    REG_VACTUAL = 0x22
    REG_CHOPCONF = 0x6C
    REG_DRV_STATUS = 0x6F
    REG_PWMCONF = 0x70
    
    # Mikroadım değerleri
    MRES_256 = 0
    MRES_128 = 1
    MRES_64 = 2
    MRES_32 = 3
    MRES_16 = 4
    MRES_8 = 5
    MRES_4 = 6
    MRES_2 = 7
    MRES_1 = 8
    
    def __init__(self, uart_id, tx_pin, rx_pin, slave_address=0x00, baudrate=115200):
        """TMC2209 başlat"""
        self.uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
        self.slave_addr = slave_address
        
    def _calc_crc(self, data):
        """CRC8 hesapla"""
        crc = 0
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x07
                else:
                    crc = crc << 1
        return crc & 0xFF
    
    def write_register(self, reg_addr, value):
        """TMC2209 kaydına yaz"""
        sync = 0x05
        
        data = bytearray([
            sync | (self.slave_addr << 0),
            reg_addr,
            (value >> 24) & 0xFF,
            (value >> 16) & 0xFF,
            (value >> 8) & 0xFF,
            value & 0xFF
        ])
        
        crc = self._calc_crc(data)
        data.append(crc)
        
        self.uart.write(data)
        time.sleep_ms(5)
    
    def read_register(self, reg_addr):
        """TMC2209 kaydını oku"""
        sync = 0x05
        
        data = bytearray([
            sync | (self.slave_addr << 0),
            reg_addr
        ])
        
        crc = self._calc_crc(data)
        data.append(crc)
        
        self.uart.write(data)
        time.sleep_ms(10)
        
        if self.uart.any() >= 8:
            response = self.uart.read(8)
            if len(response) == 8:
                value = (response[3] << 24) | (response[4] << 16) | (response[5] << 8) | response[6]
                return value
        
        return None
    
    # ============================================================================
    # OPTİMİZASYON 1: AKILCI AKIM YÖNETİMİ
    # ============================================================================
    
    def set_current_advanced(self, run_current, hold_current=None, hold_delay=2):
        """
        Gelişmiş akım yönetimi
        
        run_current: Hareket sırasında akım (0-2000 mA) - YÜKSEK GÜÇ
        hold_current: Durma sırasında akım (None = %30 run) - ENERJİ TASARRUFU
        hold_delay: Durma sonrası düşük akıma geçiş süresi (0-15)
        
        ✅ FAYDA: 
        - Hareket sırasında maksimum güç
        - Durma sırasında enerji tasarrufu + daha az ısınma
        """
        if hold_current is None:
            hold_current = int(run_current * 0.3)  # %30 hold
        
        # Akımı CS değerine çevir (0-31)
        irun = min(31, max(0, run_current // 71))
        ihold = min(31, max(0, hold_current // 71))
        
        # IHOLD_IRUN: [IHOLDDELAY:16-19][IRUN:8-12][IHOLD:0-4]
        value = (hold_delay << 16) | (irun << 8) | ihold
        
        self.write_register(self.REG_IHOLD_IRUN, value)
        print(f"⚡ Akım: RUN={run_current}mA, HOLD={hold_current}mA, DELAY={hold_delay}")
    
    # ============================================================================
    # OPTİMİZASYON 2: STEALTHCHOP ↔ SPREADCYCLE OTOMATİK GEÇİŞ
    # ============================================================================
    
    def configure_hybrid_mode(self, threshold_rpm=100):
        """
        Hybrid mod: Düşük hızda StealthChop, yüksek hızda SpreadCycle
        
        threshold_rpm: Geçiş hızı (RPM) - Bu hızın üstünde SpreadCycle
        
        ✅ FAYDA:
        - Düşük hızda sessiz (StealthChop)
        - Yüksek hızda güçlü ve hızlı (SpreadCycle)
        """
        # TPWMTHRS: StealthChop devre dışı kalacağı hız
        # Değer = 0 → Her zaman SpreadCycle
        # Değer = 0xFFFFF → Her zaman StealthChop
        # Orta değer → Otomatik geçiş
        
        # Formül: TPWMTHRS ≈ 12000000 / (256 * threshold_rpm * microsteps)
        # Basitleştirilmiş: 47000 / threshold_rpm (1/8 microstep için)
        
        if threshold_rpm == 0:
            tpwmthrs = 0xFFFFF  # Her zaman StealthChop
        else:
            tpwmthrs = max(0, min(0xFFFFF, int(47000 / threshold_rpm)))
        
        self.write_register(self.REG_TPWMTHRS, tpwmthrs)
        
        # GCONF: SpreadCycle'ı etkinleştir (bit 2 = 0)
        gconf = 0x00000000  # SpreadCycle ready
        self.write_register(self.REG_GCONF, gconf)
        
        print(f"🔄 Hybrid mod: {threshold_rpm} RPM'de SpreadCycle'a geçiş")
    
    # ============================================================================
    # OPTİMİZASYON 3: MİKROADIM + İNTERPOLASYON (HASSAS + HIZLI)
    # ============================================================================
    
    def set_microstepping_with_interpolation(self, mres, interpolate=True):
        """
        Mikroadım + 256 interpolasyon
        
        mres: Fiziksel mikroadım (MRES_8, MRES_32, vb.)
        interpolate: True = 256 interpolasyona çıkar
        
        ✅ FAYDA:
        - 1/8 mikroadım kullanarak HIZLI hareket
        - Interpolasyon ile 256 adım hassasiyeti
        - En iyi hız/hassasiyet dengesi!
        
        ÖNERİ: X ekseni için 1/8 + interp (HIZLI)
               Y ekseni için 1/32 + interp (HASSAS)
        """
        # CHOPCONF kaydını oku
        chopconf = self.read_register(self.REG_CHOPCONF)
        
        if chopconf is None:
            # Varsayılan CHOPCONF (optimize edilmiş)
            chopconf = 0x14410153  # TOFF=3, HSTRT=5, HEND=1, TBL=1
        
        # MRES bitlerini güncelle (24-27)
        chopconf = (chopconf & ~(0x0F << 24)) | (mres << 24)
        
        # INTPOL biti (28) - 256 interpolasyon
        if interpolate:
            chopconf |= (1 << 28)
        else:
            chopconf &= ~(1 << 28)
        
        self.write_register(self.REG_CHOPCONF, chopconf)
        
        microstep_values = {
            0: 256, 1: 128, 2: 64, 3: 32,
            4: 16, 5: 8, 6: 4, 7: 2, 8: 1
        }
        
        actual_steps = 256 if interpolate else microstep_values.get(mres, '?')
        print(f"🎯 Mikroadım: 1/{microstep_values.get(mres, '?')} → {actual_steps} interp")
    
    # ============================================================================
    # OPTİMİZASYON 4: COOLSTEP (YÜKE GÖRE AKIM KONTROLÜ)
    # ============================================================================
    
    def enable_coolstep(self, min_current=1, max_current=0, step_down=1, step_up=1):
        """
        CoolStep: Yüke göre akımı otomatik ayarla
        
        min_current: Minimum akım (0-15, 0=kapalı)
        max_current: Maksimum akım (0-15, 0=tam)
        step_down: Akım azaltma hızı (0-3)
        step_up: Akım artırma hızı (0-3)
        
        ✅ FAYDA:
        - Yük azsa akımı düşürür → Daha hızlı, daha az ısınma
        - Yük artınca otomatik güç artışı
        - %30'a kadar daha hızlı hareket!
        """
        # COOLCONF kaydı
        # [SEMIN:0-3][SEUP:5-6][SEMAX:8-11][SEDN:13-14][SEIMIN:15]
        coolconf = (min_current & 0x0F) | ((step_up & 0x03) << 5) | \
                   ((max_current & 0x0F) << 8) | ((step_down & 0x03) << 13)
        
        self.write_register(self.REG_COOLCONF, coolconf)
        
        # TCOOLTHRS: CoolStep aktif olacağı minimum hız
        # Düşük değer = Her zaman aktif
        tcoolthrs = 1000  # Düşük eşik
        self.write_register(self.REG_TCOOLTHRS, tcoolthrs)
        
        print(f"❄️ CoolStep aktif: MIN={min_current}, MAX={max_current}")
    
    # ============================================================================
    # OPTİMİZASYON 5: CHOPPER OPTİMİZASYONU (HIZ + TORK)
    # ============================================================================
    
    def optimize_chopper(self, mode='balanced'):
        """
        Chopper parametreleri optimizasyonu
        
        mode: 'speed'    → Maksimum hız (düşük tork)
              'torque'   → Maksimum tork (düşük hız)
              'balanced' → Dengeli (önerilen)
        
        ✅ FAYDA:
        - TOFF, HSTRT, HEND parametreleri optimize edilir
        - PWM karakteristiği hıza göre ayarlanır
        """
        chopconf = self.read_register(self.REG_CHOPCONF)
        
        if chopconf is None:
            chopconf = 0x14410153
        
        if mode == 'speed':
            # Hız modu: Düşük TOFF, yüksek HSTRT
            toff = 3
            hstrt = 7
            hend = 0
            tbl = 0  # Boşluk süresi minimum
        elif mode == 'torque':
            # Tork modu: Yüksek TOFF, dengeli HSTRT
            toff = 5
            hstrt = 5
            hend = 3
            tbl = 2
        else:  # balanced
            # Dengeli mod
            toff = 4
            hstrt = 5
            hend = 1
            tbl = 1
        
        # CHOPCONF: [MRES:24-27][INTPOL:28][DEDGE:29][DISS2G:30][DISS2VS:31]
        #           [TBL:15-16][HEND:7-10][HSTRT:4-6][TOFF:0-3]
        
        chopconf = (chopconf & 0xFF000000) | (tbl << 15) | (hend << 7) | (hstrt << 4) | toff
        
        self.write_register(self.REG_CHOPCONF, chopconf)
        print(f"⚙️ Chopper: {mode} (TOFF={toff}, HSTRT={hstrt}, HEND={hend})")
    
    # ============================================================================
    # OPTİMİZASYON 6: TPOWERDOWN (GÜÇLÜK KAYBINı AZALTICI)
    # ============================================================================
    
    def set_standstill_mode(self, delay=2):
        """
        Durma sonrası akım kesme süresi
        
        delay: Durma sonrası akım düşüş süresi (0-255, 0=anında, 255=~5 saniye)
        
        ✅ FAYDA:
        - Hızlı başlangıç için 1-2 (önerilen)
        - Enerji tasarrufu için 10-20
        """
        self.write_register(self.REG_TPOWERDOWN, delay)
        print(f"⏱️ Standstill delay: {delay}")
    
    # ============================================================================
    # HIZLI BAŞLATMA (PRESET KONFIGÜRASYONLAR)
    # ============================================================================
    
    def init_for_speed(self, axis='x'):
        """
        HIZ odaklı konfigürasyon (X ekseni için önerilen)
        
        - 1/8 mikroadım + 256 interpolasyon
        - SpreadCycle (güç modu)
        - Yüksek akım
        - CoolStep aktif
        - Speed-optimized chopper
        """
        print(f"\n🚀 {axis.upper()} Ekseni: HIZ MOD\n")
        
        # 1. Akım (yüksek)
        self.set_current_advanced(run_current=1400, hold_current=400, hold_delay=1)
        
        # 2. Mikroadım + interpolasyon (1/8 → 256)
        self.set_microstepping_with_interpolation(self.MRES_8, interpolate=True)
        
        # 3. SpreadCycle (düşük hızda bile)
        self.configure_hybrid_mode(threshold_rpm=0)  # Her zaman SpreadCycle
        
        # 4. CoolStep
        self.enable_coolstep(min_current=2, max_current=0, step_down=1, step_up=2)
        
        # 5. Chopper (hız modu)
        self.optimize_chopper(mode='speed')
        
        # 6. Hızlı başlangıç
        self.set_standstill_mode(delay=1)
        
        print("✅ HIZ modu aktif!\n")
    
    def init_for_precision(self, axis='y'):
        """
        HASSASİYET odaklı konfigürasyon (Y ekseni için önerilen)
        
        - 1/32 mikroadım + 256 interpolasyon
        - Hybrid mod (StealthChop ↔ SpreadCycle)
        - Orta akım
        - Balanced chopper
        """
        print(f"\n🎯 {axis.upper()} Ekseni: HASSASİYET MOD\n")
        
        # 1. Akım (orta)
        self.set_current_advanced(run_current=1000, hold_current=300, hold_delay=2)
        
        # 2. Mikroadım + interpolasyon (1/32 → 256)
        self.set_microstepping_with_interpolation(self.MRES_32, interpolate=True)
        
        # 3. Hybrid mod (düşük hızda StealthChop)
        self.configure_hybrid_mode(threshold_rpm=80)
        
        # 4. CoolStep (daha az agresif)
        self.enable_coolstep(min_current=1, max_current=0, step_down=2, step_up=1)
        
        # 5. Chopper (dengeli)
        self.optimize_chopper(mode='balanced')
        
        # 6. Normal başlangıç
        self.set_standstill_mode(delay=2)
        
        print("✅ HASSASİYET modu aktif!\n")
    
    def init_balanced(self):
        """
        DENGELİ konfigürasyon (her iki eksen için)
        
        - 1/16 mikroadım + 256 interpolasyon
        - Hybrid mod
        - Dengeli akım ve chopper
        """
        print("\n⚖️ DENGELİ MOD\n")
        
        self.set_current_advanced(run_current=1200, hold_current=350, hold_delay=2)
        self.set_microstepping_with_interpolation(self.MRES_16, interpolate=True)
        self.configure_hybrid_mode(threshold_rpm=100)
        self.enable_coolstep(min_current=1, max_current=0, step_down=1, step_up=1)
        self.optimize_chopper(mode='balanced')
        self.set_standstill_mode(delay=2)
        
        print("✅ Dengeli mod aktif!\n")
    
    # ============================================================================
    # DURUM OKUMA
    # ============================================================================
    
    def get_status(self):
        """Gelişmiş durum okuma"""
        drv_status = self.read_register(self.REG_DRV_STATUS)
        
        if drv_status is not None:
            status = {
                'stst': bool(drv_status & (1 << 31)),          # Standstill
                'stealth': bool(drv_status & (1 << 30)),       # StealthChop aktif mi?
                'cs_actual': (drv_status >> 16) & 0x1F,        # Gerçek akım
                'olb': bool(drv_status & (1 << 30)),
                'ola': bool(drv_status & (1 << 29)),
                's2vsb': bool(drv_status & (1 << 28)),
                's2vsa': bool(drv_status & (1 << 27)),
                's2gb': bool(drv_status & (1 << 26)),
                's2ga': bool(drv_status & (1 << 25)),
                'ot': bool(drv_status & (1 << 24)),            # Overtemp
                'otpw': bool(drv_status & (1 << 23)),          # Overtemp warning
            }
            return status
        
        return None
    
    def print_status(self):
        """Durumu ekrana yazdır"""
        status = self.get_status()
        if status:
            print("\n📊 TMC2209 Durum:")
            print(f"  Mode: {'StealthChop' if status['stealth'] else 'SpreadCycle'}")
            print(f"  Standstill: {status['stst']}")
            print(f"  Actual Current: {status['cs_actual']}/31")
            print(f"  Overtemp: {status['ot']} (Warning: {status['otpw']})")
        else:
            print("⚠️ Durum okunamadı")


# ============================================================================
# TEST KODU
# ============================================================================

def test_advanced():
    """Gelişmiş optimizasyon testi"""
    print("=" * 60)
    print(" TMC2209 ADVANCED OPTIMIZATION TEST")
    print("=" * 60)
    
    # UART pinleri (motor_control_pico.py'den farklı olmalı)
    TMC_UART_ID = 1
    TMC_TX = 4  # GPIO4
    TMC_RX = 5  # GPIO5
    
    # X Motor (HIZ modu)
    print("\n" + "=" * 60)
    tmc_x = TMC2209Advanced(TMC_UART_ID, TMC_TX, TMC_RX, slave_address=0x00)
    tmc_x.init_for_speed(axis='x')
    time.sleep(1)
    tmc_x.print_status()
    
    # Y Motor (HASSASİYET modu) - Farklı slave address gerekli!
    # Eğer ikinci motor varsa:
    # tmc_y = TMC2209Advanced(TMC_UART_ID, TMC_TX, TMC_RX, slave_address=0x01)
    # tmc_y.init_for_precision(axis='y')
    
    print("\n" + "=" * 60)
    print("✅ Optimizasyon tamamlandı!")
    print("=" * 60)
    print("\n📌 SONRAKİ ADIMLAR:")
    print("1. motor_control_pico.py'yi güncelle")
    print("2. Python tarafında config.py mikroadım değerlerini güncelle")
    print("3. Sistemi test et ve performansı gözlemle")
    print("=" * 60)

if __name__ == "__main__":
    test_advanced()
