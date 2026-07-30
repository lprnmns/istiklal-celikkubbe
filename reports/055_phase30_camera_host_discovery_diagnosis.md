# Phase 30 - Camera Host Discovery and Blocker Diagnosis

## Karar

- Camera host discovery: partial
- Real camera frame evidence: partial
- Competition readiness: false
- Motor/hardware command readiness: not started

## Host Bulguları

- Host camera devices detected: True
- /dev/video entries: /dev/video0, /dev/video1, /dev/video2, /dev/video3
- v4l2 available: False
- Ubuntu camera app not seen note: True
- Blocker reason: camera device exists; frame capture not attempted yet

Bu fazda kamera için doğrudan `real camera acceptance passed` varsayımı yapılmadı. Kamera cihazları host seviyesinde görünüyor ancak `v4l2-ctl` eksik ve runtime camera profile halen mock olduğu için frame evidence `partial` sınıfında kaldı. Mock/surrogate evidence real camera evidence yerine geçmez.

## Üretilen Dosyalar

- `reports/camera_host_device_inventory.json`
- `reports/camera_host_diagnostic_commands.json`
- `reports/camera_host_blocker_report.md`
- `reports/real_camera_status.json`
- `reports/real_camera_capture_evidence.json`
- `reports/real_camera_acceptance_result.json`
- `reports/real_camera_safety_boundary.md`

## Manuel Host Kontrolleri

- `v4l-utils` / `v4l2-ctl` eksikse kullanıcı manuel kurulum durumunu değerlendirmeli.
- Kullanıcı `video` grubunda değilse permission durumu manuel incelenmeli; bu task otomatik `usermod`, `chmod` veya driver değişikliği yapmaz.
- BIOS/privacy switch, USB kablo, Snap/Flatpak camera permission ve `dmesg` uvcvideo/v4l2 çıktıları manuel kontrol edilmeli.

## Safety Boundary

No motor, servo, fire, GPIO, PWM, STEP/DIR, TMC write, serial TX/write or hardware enable path was added.

`DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false`

`no_physical_command_generated=true`

## Doğrulama

- `uv run pytest -q`: geçti
- `pnpm --dir frontend typecheck`: geçti
- `pnpm --dir frontend build`: geçti
- `python3 scripts/check_release.py`: geçti
- `bash -n release/linux/start_istiklal_c2.sh`: geçti
- `bash -n start_linux.sh`: geçti
- Manual smoke camera/data-lab/demo endpoints: HTTP 200

## Son Karar

- Camera host discovery: partial
- Real camera frame evidence: partial
- Motor/hardware command readiness: not started
- Competition readiness: false
- no_physical_command_generated=true
