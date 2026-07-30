# ISTIKLAL Docker profili

Bu profil yalnız **TEST/CI ve arayüz inceleme** içindir. Güvenli varsayılan
`DRY_RUN`, mock seri yol ve fiziksel komutlar kapalı biçimde başlar.

Windows üzerinde USB kamera, Pico COM portu, CUDA/DirectShow ve gerçek taret için
Docker kullanılmaz. Bunun yerine `release/one_click/windows/ISTIKLAL_TEK_TIK.cmd`
kullanılır. Linux donanım geçişi ayrıca cihaz izinleriyle saha kabulü yapılmadan
Docker profiline eklenmemelidir.

Docker TEST image'ı hızlı ve taşınabilir kalması için Torch, Ultralytics ve CUDA
paketlerini içermez. Bu nedenle gerçek YOLO/GPU kabulü native kurulumda yapılır;
Docker'ın amacı arayüz, API, mock akış ve CI kontrolüdür.

Compose hostta boş bir portu otomatik seçer. Teknik kullanım:

```text
docker compose -f release/one_click/docker/compose.yaml up -d --build
docker compose -f release/one_click/docker/compose.yaml port istiklal 8000
```
