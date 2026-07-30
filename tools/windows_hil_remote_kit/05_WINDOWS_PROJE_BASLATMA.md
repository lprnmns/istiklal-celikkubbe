# Windows'ta proje baslatma

Donanim tani loglari incelenmeden projeyi LIVE moda almayin. Ilk yazilim acilisi asagidaki sirayla yapilir:

1. PowerShell acin ve proje kokune gecin.
2. python --version ciktisinin 3.12 veya ustu oldugunu dogrulayin.
3. uv --version komutunu dogrulayin. Yeni kurulumdan sonra komut bulunamazsa PowerShell'i kapatip yeniden acin.
4. frontend\dist\index.html dosyasinin varligini kontrol edin. Paket bunu runtime sirasinda yeniden build etmez.
5. start_windows.bat dosyasini calistirin.
6. Ilk acilista yalniz Test profiliyle kamera ve Pico kesfini yapin. Taret ve tetik enerjisi kapali kalir.
7. Kamera/Pico tani ZIP'i gelistirici tarafindan incelendikten sonra HIL listesinin siradaki maddesine gecilir.

Baslatici varsayilan olarak http://127.0.0.1:8000 adresini kullanir. Bu port internete veya Tailscale agina acilmaz. Uzaktan tarayici gerekiyorsa uzak bilgisayarda su SSH local forwarding komutu kullanilir:

    ssh -L 8000:127.0.0.1:8000 WINDOWS_KULLANICISI@TAILSCALE_IP

Uzak bilgisayarda tarayici http://127.0.0.1:8000 adresini acar.
