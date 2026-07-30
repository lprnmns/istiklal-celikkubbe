# İSTİKLAL — TEKNOFEST Çelikkubbe

İSTİKLAL; USB kamera ve YOLO algılama, Pico 2 tabanlı taret kontrolü, CommandGateway güvenlik hattı, otomatik hedef takibi ve 3B dijital ikizi tek operatör arayüzünde birleştiren hava savunma sistemi yazılımıdır.

## Hızlı başlatma

Kurulum daha önce tamamlandıysa proje kökündeki tek-tık dosyasını kullanın:

- Windows: `ISTIKLAL_TEK_TIK.cmd`
- Linux: `ISTIKLAL_TEK_TIK.desktop` veya `./ISTIKLAL_TEK_TIK.sh`

Kısayol sistem kapalıysa başlatır, açıksa yalnız İSTİKLAL sürecini durdurur. `8000-8099` aralığındaki ilk boş port seçilir, sağlık kontrolünden sonra tarayıcı açılır ve adres `ISTIKLAL_URL.txt` dosyasına yazılır. Normal kurulumda adres `http://127.0.0.1:8000/` olur.

## Operatör modları

- **TEST:** Kamera, YOLO, hedef takibi ve fiziksel taret hareketi kullanılabilir. Pico `ARM,0` durumunda tutulur ve fiziksel FIRE engellenir.
- **CANLI SİSTEM:** Pico `ARM,1` durumuna alınabilir; CommandGateway preflight koşulları sağlandığında fiziksel hareket, takip ve FIRE yolu açıktır.

Mod seçimi arayüzden yapılır. Kaynak kod, `.env` veya gizli feature flag değiştirmek gerekmez. E-Stop, Pico heartbeat, kamera tazeliği, servo arm durumu ve hareket/atış sınırları CommandGateway tarafından fiziksel komut bazında denetlenir.

Varsayılan cihaz profili `windows-taret-hil` olarak gelir. Başka bilgisayarda kamera indeksi, USB kimliği veya COM portu değişebileceği için ilk çalıştırmada Kurulum Merkezi üzerinden cihazları yeniden bulup profili kaydedin.

## Windows kurulumu

Gerçek USB kamera, Pico/COM ve NVIDIA GPU ile yarışma kullanımı için önerilen ortam native Windows'tur.

### Gereksinimler

- Windows 10/11 64-bit
- Python 3.12
- Git
- Node.js LTS
- Pico firmware yüklemek için Arduino IDE veya uyumlu araç zinciri

PowerShell veya Komut İstemi:

```bat
git clone https://github.com/lprnmns/istiklal-celikkubbe.git
cd istiklal-celikkubbe
corepack enable
corepack prepare pnpm@11.0.8 --activate
```

Backend ortamını kurun:

```bat
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -e ".[dev]"
cd ..
```

Frontend'i üretin:

```bat
cd frontend
pnpm install --frozen-lockfile
pnpm build
cd ..
```

Ardından `ISTIKLAL_TEK_TIK.cmd` dosyasına çift tıklayın. Windows başlatıcısı varsa Görev Zamanlayıcıdaki `ISTIKLAL_UI_8000` görevini kullanır; yoksa projeye ait süreci doğrudan başlatır.

### Windows donanım hazırlığı

1. Pico ve taret enerjisini güvenli test düzeninde bağlayın; E-Stop'un fiziksel güç kesmesini doğrulayın.
2. Harici USB kamerayı bağlayın.
3. Arayüzde Kurulum Merkezi'ni açın, kamerayı `Ara` ile bulun ve önizlemede doğru cihaz olduğunu doğrulayın.
4. Pico'yu otomatik buldurun; port, handshake, heartbeat ve ACK durumlarını kontrol edin.
5. Balon modelini etkinleştirip güven eşiğini sahaya göre ayarlayın.
6. Profili yeni bir adla kaydedin ve ana ekranda bu profili seçin.
7. Önce **TEST**, fiziksel atış yalnız gerekli kontroller tamamlandıktan sonra **CANLI SİSTEM** ile çalıştırılmalıdır.

Repo, saha testinde kullanılan küçük balon modelini şu konumda içerir:

```text
models/incoming/legacy-balloon-yolo-0.1.0/model.pt
```

## Linux kurulumu

```bash
git clone https://github.com/lprnmns/istiklal-celikkubbe.git
cd istiklal-celikkubbe
curl -LsSf https://astral.sh/uv/install.sh | sh
cd backend
uv sync --extra dev
cd ../frontend
corepack enable
corepack prepare pnpm@11.0.8 --activate
pnpm install --frozen-lockfile
pnpm build
cd ..
chmod +x ISTIKLAL_TEK_TIK.sh ISTIKLAL_TEK_TIK.desktop
./ISTIKLAL_TEK_TIK.sh
```

Linux masaüstünde istenirse `ISTIKLAL_TEK_TIK.desktop` dosyasına çalıştırma izni verilip çift tıklanabilir.

## Manuel geliştirme

Backend:

```bash
cd backend
uv sync --extra dev
uv run python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Frontend:

```bash
cd frontend
pnpm install
pnpm dev --host 127.0.0.1 --port 5173
```

Testler:

```bash
cd backend
uv run pytest
cd ../frontend
pnpm build
```

## Docker

Docker akışı arayüz incelemesi, yazılım testi ve CI içindir:

- Windows: `release/one_click/docker/ISTIKLAL_DOCKER_TEK_TIK.cmd`
- Linux: `release/one_click/docker/ISTIKLAL_DOCKER_TEK_TIK.sh`

Gerçek Windows USB kamera, COM/Pico ve CUDA donanım yolu için native Windows başlatıcısını kullanın. Docker yarışma donanımı için varsayılan çalışma biçimi değildir.

## Firmware ve komut yolu

Güncel Arduino firmware:

```text
eski_sistem_arayüz/pico_arduino/motor_control_v2_optimized/motor_control_v2_optimized.ino
```

MicroPython uyumluluk kaynağı:

```text
firmware/pico2/main.py
```

Fiziksel komut zinciri özetle şöyledir:

```text
Operatör / Tracking -> CommandGateway -> PicoService / SerialService -> Pico firmware -> ACK
```

Tracking doğrudan seri porta yazmaz. Komut engellenirse arayüz CommandGateway reason code'unu gösterir; bütün uygulama yerine yalnız ilgili fiziksel komut engellenir.

## Proje yapısı

- `backend/`: FastAPI, cihaz servisleri, CommandGateway, tracking ve görev mantığı
- `frontend/`: Vue operatör arayüzü ve 3B dijital ikiz
- `firmware/`: Pico firmware kaynakları
- `config/`: varsayılan yapılandırmalar ve başlangıç profili seçimi
- `data/device_profiles/`: paylaşılabilir cihaz profilleri
- `models/incoming/`: doğrulanmış küçük model paketi
- `release/one_click/`: Windows, Linux ve Docker tek-tık başlatıcıları
- `backend/tests/`: sözleşme, güvenlik ve görev testleri
- `reports/`: yazılımsal kabul ve donanım test kayıtları

## Notlar

- Çalışma logları, runtime state, kullanıcıya özel profiller, sanal ortamlar ve build çıktıları repoya eklenmez.
- GitHub sınırını aşan ham CAD/STL ve eski alternatif model çıktıları yayın reposuna alınmamıştır. Aktif kinematik dijital ikiz GLB dosyası repoda mevcuttur.
- Başka bir makinede kaydedilmiş kamera indeksi veya COM portunu körlemesine kullanmayın; Kurulum Merkezi'nde gerçek cihaz kimliğini doğrulayın.
