# Phase 29.1 Pico Permission Hotfix

## Decision

- Pico permission acceptance: partial
- Pico RX-only telemetry acceptance: partial
- Selected port: /dev/ttyACM0
- Blocker class: user_not_in_dialout
- Device exists: True
- Device mode: crw-rw----
- Device owner/group: root/dialout
- User in dialout: False
- Connected: False
- Telemetry frames: 0

## Host Evidence

- id output: `uid=1000(alperen) gid=1000(alperen) groups=1000(alperen),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),100(users),114(lpadmin),124(docker)`
- groups output: `alperen adm cdrom sudo dip plugdev users lpadmin docker`
- ls output: `crw-rw---- 1 root dialout 166, 0 May 15 12:48 /dev/ttyACM0`

## Manual Recommendation

If blocker is user_not_in_dialout or device_permission_denied, run manually outside the application:

```bash
sudo usermod -aG dialout $USER
```

Group change requires logout/login or reboot before it affects new sessions. For temporary manual testing only, not permanent:

```bash
sudo chmod a+rw /dev/ttyACM0
```

The application does not run sudo, usermod or chmod automatically.

## Safety

No motor, servo, fire, GPIO, PWM, STEP/DIR, TMC write, serial TX/write or hardware enable path was added.

- serial_write_enabled=false
- command_tx_enabled=false
- physical_command_enabled=false
- no_physical_command_generated=true

## Validation

- uv run pytest -q: passed
- pnpm --dir frontend typecheck: passed
- pnpm --dir frontend build: passed
- python3 scripts/check_release.py: passed
- bash -n release/linux/start_istiklal_c2.sh: passed
- bash -n start_linux.sh: passed
- Manual smoke: /pico and Pico read-only endpoints returned HTTP 200
