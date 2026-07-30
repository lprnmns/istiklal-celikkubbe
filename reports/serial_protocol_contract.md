# ISTIKLAL Serial Packet Protocol v1 Contract

Safety invariant: `no_physical_command_generated=true`

## Frame

| Field | Type |
| --- | --- |
| `sof_1` | `0xA5` |
| `sof_2` | `0x5A` |
| `version` | `uint8` |
| `msg_type` | `uint8` |
| `seq_id` | `uint16_le` |
| `timestamp_ms` | `uint32_le` |
| `flags` | `uint16_le` |
| `payload_len` | `uint16_le` |
| `payload` | bytes |
| `crc32` | `uint32_le`, computed over `version..payload` |

## Message Types

- `HELLO`
- `HEARTBEAT`
- `TELEMETRY`
- `DRIVER_STATE`
- `LIMIT_STATE`
- `FAULT`
- `ACK`
- `NACK`
- `CONFIG_REPORT`
- `UNKNOWN`

## Disabled in Phase 36

`SPD`, `LZR`, `STP`, motor movement, fire, trigger, servo actuation, GPIO, PWM, STEP/DIR, hardware enable, and serial write paths for physical control are disabled.

