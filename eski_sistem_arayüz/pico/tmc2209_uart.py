"""
TMC2209 UART Kontrol Kütüphanesi - Raspberry Pi Pico 2
İleride UART ile TMC2209'u kontrol etmek için

UART üzerinden TMC2209 kayıtlarına erişim sağlar:
- Akım ayarı (IRUN, IHOLD)
- Mikroadım ayarı (MRES)
- StealthChop/SpreadCycle geçişi
- Sürücü durumu okuma
"""

from machine import UART, Pin
import time
import struct

class TMC2209:
    """TMC2209 sürücü kontrolü (UART)"""
    
    # TMC2209 Yazma Kayıtları
    REG_GCONF = 0x00
    REG_GSTAT = 0x01
    REG_IOIN = 0x04
    REG_IHOLD_IRUN = 0x10
    REG_TPOWERDOWN = 0x11
    REG_TSTEP = 0x12
    REG_TPWMTHRS = 0x13
    REG_VACTUAL = 0x22
    REG_CHOPCONF = 0x6C
    REG_DRV_STATUS = 0x6F
    REG_PWMCONF = 0x70
    
    # Mikroadım değerleri
    MRES_256 = 0  # 1/256
    MRES_128 = 1  # 1/128
    MRES_64 = 2   # 1/64
    MRES_32 = 3   # 1/32
    MRES_16 = 4   # 1/16
    MRES_8 = 5    # 1/8
    MRES_4 = 6    # 1/4
    MRES_2 = 7    # 1/2
    MRES_1 = 8    # Full step
    
    def __init__(self, uart_id, tx_pin, rx_pin, slave_address=0x00, baudrate=115200):
        """
        TMC2209 başlat
        
        uart_id: UART numarası (0 veya 1)
        tx_pin: TX pin GPIO numarası
        rx_pin: RX pin GPIO numarası
        slave_address: TMC2209 slave adresi (MS1_AD0 ve MS2_AD1 pinleri ile ayarlanır)
        """
        self.uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
        self.slave_addr = slave_address
        
    def _calc_crc(self, data):
        """CRC8 hesapla (TMC protokolü)"""
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
        # Datagram: [sync + slave, reg, val3, val2, val1, val0, crc]
        sync = 0x05  # Write datagram
        
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
        time.sleep_ms(5)  # Yazma sonrası bekleme
    
    def read_register(self, reg_addr):
        """TMC2209 kaydını oku (okuma istemi gönder)"""
        # Read request: [sync + slave, reg, crc]
        sync = 0x05
        
        data = bytearray([
            sync | (self.slave_addr << 0),
            reg_addr
        ])
        
        crc = self._calc_crc(data)
        data.append(crc)
        
        self.uart.write(data)
        time.sleep_ms(10)
        
        # Yanıtı oku
        if self.uart.any() >= 8:
            response = self.uart.read(8)
            # Yanıt formatı: [sync, master_addr, reg, val3, val2, val1, val0, crc]
            if len(response) == 8:
                value = (response[3] << 24) | (response[4] << 16) | (response[5] << 8) | response[6]
                return value
        
        return None
    
    def set_current(self, run_current, hold_current=None):
        """
        Motor akımını ayarla (mA cinsinden)
        
        run_current: Hareket sırasında akım (0-2000 mA)
        hold_current: Durma sırasında akım (None ise run_current'in yarısı)
        
        Formül: CS = (I_RMS / 2.5A) * 32 - 1
        I_sense = 0.11 ohm için
        """
        if hold_current is None:
            hold_current = run_current // 2
        
        # Akımı CS değerine çevir (0-31 arası)
        # Basitleştirilmiş formül: CS ≈ current_mA / 71
        irun = min(31, max(0, run_current // 71))
        ihold = min(31, max(0, hold_current // 71))
        
        # IHOLD_IRUN kaydı: [IRUN:4-8][IHOLD:4-0][IHOLDDELAY:16-19]
        value = (irun << 8) | (ihold << 0) | (2 << 16)  # IHOLDDELAY = 2
        
        self.write_register(self.REG_IHOLD_IRUN, value)
        print(f"Akım ayarı: RUN={run_current}mA (CS={irun}), HOLD={hold_current}mA (CS={ihold})")
    
    def set_microstepping(self, mres):
        """
        Mikroadım ayarı
        
        mres: MRES_256, MRES_128, ..., MRES_1
        """
        # CHOPCONF kaydını oku
        chopconf = self.read_register(self.REG_CHOPCONF)
        
        if chopconf is None:
            # Varsayılan değer
            chopconf = 0x10000053
        
        # MRES bitlerini güncelle (24-27)
        chopconf = (chopconf & ~(0x0F << 24)) | (mres << 24)
        
        self.write_register(self.REG_CHOPCONF, chopconf)
        
        microstep_values = {
            0: 256, 1: 128, 2: 64, 3: 32,
            4: 16, 5: 8, 6: 4, 7: 2, 8: 1
        }
        print(f"Mikroadım: 1/{microstep_values.get(mres, '?')}")
    
    def enable_stealthchop(self, enable=True):
        """StealthChop modunu aktif/pasif et"""
        # GCONF kaydı
        gconf = 0x00000000
        
        if enable:
            gconf |= (1 << 2)  # en_spreadcycle = 0 (StealthChop aktif)
        else:
            gconf |= (1 << 2)  # en_spreadcycle = 1 (SpreadCycle aktif)
        
        self.write_register(self.REG_GCONF, gconf)
        print(f"{'StealthChop' if enable else 'SpreadCycle'} aktif")
    
    def get_status(self):
        """Sürücü durumunu oku"""
        drv_status = self.read_register(self.REG_DRV_STATUS)
        
        if drv_status is not None:
            status = {
                'stst': bool(drv_status & (1 << 31)),  # Standstill
                'olb': bool(drv_status & (1 << 30)),   # Open load B
                'ola': bool(drv_status & (1 << 29)),   # Open load A
                's2vsb': bool(drv_status & (1 << 28)), # Short to VS B
                's2vsa': bool(drv_status & (1 << 27)), # Short to VS A
                's2gb': bool(drv_status & (1 << 26)),  # Short to GND B
                's2ga': bool(drv_status & (1 << 25)),  # Short to GND A
                'ot': bool(drv_status & (1 << 24)),    # Overtemperature
                'otpw': bool(drv_status & (1 << 23)),  # Overtemperature prewarning
                'cs_actual': (drv_status >> 16) & 0x1F # Actual current
            }
            return status
        
        return None
    
    def init_driver(self, run_current=800, microstep='1/8', stealthchop=True):
        """
        Sürücüyü başlat (hızlı kurulum)
        
        run_current: Motor akımı (mA)
        microstep: '1/256', '1/128', ..., '1/1'
        stealthchop: True = sessiz mod, False = güç modu
        """
        print("\nTMC2209 başlatılıyor...")
        
        # Akım ayarı
        self.set_current(run_current)
        
        # Mikroadım ayarı
        mres_map = {
            '1/256': self.MRES_256,
            '1/128': self.MRES_128,
            '1/64': self.MRES_64,
            '1/32': self.MRES_32,
            '1/16': self.MRES_16,
            '1/8': self.MRES_8,
            '1/4': self.MRES_4,
            '1/2': self.MRES_2,
            '1/1': self.MRES_1,
        }
        
        mres = mres_map.get(microstep, self.MRES_8)
        self.set_microstepping(mres)
        
        # StealthChop
        self.enable_stealthchop(stealthchop)
        
        print("✅ TMC2209 hazır!\n")

# ============================================================================
# TEST KODU
# ============================================================================

def test_tmc2209():
    """TMC2209 UART test"""
    print("=" * 50)
    print("TMC2209 UART Test")
    print("=" * 50)
    
    # TMC UART pinleri (motor_control_pico.py'deki ana UART'tan farklı olmalı)
    TMC_UART_ID = 1
    TMC_TX = 4  # GPIO4
    TMC_RX = 5  # GPIO5
    
    # X motoru TMC2209 (slave address = 0)
    tmc_x = TMC2209(TMC_UART_ID, TMC_TX, TMC_RX, slave_address=0x00)
    
    # Sürücüyü başlat
    tmc_x.init_driver(
        run_current=1000,  # 1A
        microstep='1/16',
        stealthchop=True
    )
    
    # Durum kontrolü
    print("\nDurum kontrolü:")
    status = tmc_x.get_status()
    if status:
        print(f"  Standstill: {status['stst']}")
        print(f"  Actual current: {status['cs_actual']}")
        print(f"  Overtemp: {status['ot']}")
    else:
        print("  ⚠️ Durum okunamadı (bağlantı kontrol et)")
    
    print("\n✅ Test tamamlandı")

if __name__ == "__main__":
    test_tmc2209()
