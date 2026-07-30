# ISTIKLAL Windows Uzaktan Donanim Hazirlik Paketi

Bu paket Windows bilgisayarda guvenli uzaktan erisim, Pico seri port kesfi, USB kamera envanteri ve proje on kontrolu icindir. Paket kendi basina motor, servo, tetik, FIRE, LZR, STEP, DIR, PWM veya GPIO komutu uretmez.

## Sirali kullanim

1. ZIP dosyasini C:\ISTIKLAL_HIL gibi kisa bir yola cikartin. Betikleri ZIP icinden calistirmayin.
2. 01_YONETICI_KURULUM.ps1 dosyasina sag tiklayip PowerShell ile yonetici olarak calistirin.
3. Acilan Tailscale uygulamasinda cihaz basindaki arkadasiniz kendi hesabi ile oturum acsin. Sifre, kurtarma anahtari veya kalici erisim kodu paylasilmasin.
4. 02_BAGLANTI_VE_AYGIT_TANI.ps1 dosyasini normal PowerShell ile calistirin.
5. Pico ve USB kamerayi takin; ayni betigi tekrar calistirin. Once/sonra loglari aygit eslestirmesini gosterecektir.
6. Projeyi Windows bilgisayara kopyalayip 03_PROJE_ONKONTROL.ps1 -ProjectRoot C:\teknofest calistirin.
7. 04_LOGLARI_PAKETLE.ps1 ile tani ZIP'ini olusturup gelistiriciye gonderin.
8. Once kamera ve Pico salt-okunur kesfi tamamlanir. Fiziksel hareket testine ancak cihaz basindaki gorevli, fiziksel E-Stop, bos hazne ve guvenli alan ayri olarak dogrulandiktan sonra gecilir.

## Guvenlik kurallari

- Modem/router uzerinde 22, 3389 veya baska port acmayin.
- Windows Uzak Masaustu'nu internete acmayin.
- Ilk oturumda sarjor ve muhimmat takili olmayacak.
- Tetik/servo enerjisi ayrilacak; taret gucu kesik baslanacak.
- Cihaz basindaki kisi fiziksel E-Stop'un yaninda kalacak.
- Fiziksel testlerde ekran paylasimi gozlem amaclidir; hareket ve tetik eylemini cihaz basindaki yetkili uygular.

## Dosyalar

- 00_KURUCULARI_DOGRULA.ps1: Gomulu kurucularin SHA-256 ve Windows Authenticode imzalarini kontrol eder. Herhangi bir uyusmazlikta kurulumu durdurur.
- 01_YONETICI_KURULUM.ps1: Windows ve yonetici kontrolu, OpenSSH Server, Tailscale, daraltilmis firewall kurali.
- Ayni betik Python 3.12 ve uv eksikse resmi winget paketlerinden kurar. RustDesk yalniz ekran destegi icin istege bagli yardimci olarak kurulur.
- 02_BAGLANTI_VE_AYGIT_TANI.ps1: Tailscale/SSH, kamera, USB ve COM aygit envanteri. Seri porta yazmaz.
- 03_PROJE_ONKONTROL.ps1: Python, uv, Node, frontend build ve proje klasorlerini kontrol eder.
- 04_LOGLARI_PAKETLE.ps1: Loglari paylasilabilir ZIP haline getirir.
- 99_GERI_AL.ps1: Paketin firewall kuralini kaldirir ve SSH servisini durdurur.
- installers klasoru: Tailscale 1.98.9, Python 3.12.10, uv 0.11.32 ve RustDesk 1.4.9 resmi kurulum dosyalari.

## Uzaktan baglanti bilgisi

Tani betigi Tailscale IPv4 adresini ve Windows kullanici adini loga yazar. Baglanti bicimi ssh WINDOWS_KULLANICI_ADI@TAILSCALE_IP olur. Windows hesap parolasi sohbet veya log dosyasina yazilmaz. Mümkunse daha sonra parola yerine sinirli SSH anahtari kullanilir.

RustDesk kimligi ve tek kullanimlik parola yalniz aktif oturum icin paylasilir. Kalici/parolasiz erisim acilmaz. Oturum bittiginde RustDesk kapatilir; sonraki gun yeni kimlik bilgisiyle baslanir.
