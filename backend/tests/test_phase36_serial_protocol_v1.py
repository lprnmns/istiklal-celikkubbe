import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.protocols.istiklal_serial_v1 import MessageType, decode_packet, decode_stream, encode_packet, validate_crc


def test_serial_protocol_packet_roundtrip() -> None:
    payload = json.dumps({"pan_deg": 12.5, "tilt_deg": -3.0, "x_steps": 120, "y_steps": -30}).encode()
    frame = encode_packet(msg_type=MessageType.TELEMETRY, seq_id=7, timestamp_ms=123456, payload=payload)
    packet = decode_packet(frame)

    assert packet.version == 1
    assert packet.msg_type == MessageType.TELEMETRY
    assert packet.seq_id == 7
    assert packet.timestamp_ms == 123456
    assert packet.payload == payload
    assert packet.msg_type_name == "TELEMETRY"
    assert validate_crc(frame) is True


def test_serial_protocol_rejects_bad_crc() -> None:
    frame = bytearray(encode_packet(msg_type=MessageType.HEARTBEAT, seq_id=1, timestamp_ms=10, payload=b"{}"))
    frame[-1] ^= 0xFF

    result = decode_stream(bytes(frame))

    assert result.packets == []
    assert "crc_mismatch" in result.errors
    assert validate_crc(bytes(frame)) is False


def test_serial_protocol_handles_partial_frame_and_multiple_frames() -> None:
    first = encode_packet(msg_type=MessageType.HEARTBEAT, seq_id=1, timestamp_ms=10, payload=b"{}")
    second = encode_packet(msg_type=MessageType.ACK, seq_id=2, timestamp_ms=20, payload=b'{"ok":true}')
    partial = first + second[:8]

    result = decode_stream(partial)
    assert [packet.seq_id for packet in result.packets] == [1]
    assert result.remainder == second[:8]

    completed = decode_stream(result.remainder + second[8:])
    assert [packet.seq_id for packet in completed.packets] == [2]
    assert completed.remainder == b""


def test_serial_protocol_recovers_after_noise_bytes() -> None:
    frame = encode_packet(msg_type=MessageType.TELEMETRY, seq_id=42, timestamp_ms=99, payload=b"{}")
    result = decode_stream(b"noise" + frame)

    assert len(result.packets) == 1
    assert result.packets[0].seq_id == 42
    assert "noise_discarded" in result.errors


def test_serial_protocol_unknown_message_type_is_labelled_unknown() -> None:
    frame = encode_packet(msg_type=0x44, seq_id=9, timestamp_ms=100, payload=b"{}")
    packet = decode_packet(frame)

    assert packet.msg_type == 0x44
    assert packet.msg_type_name == "UNKNOWN"


def test_pico_protocol_sample_ingest_and_digital_twin_pose_mapping(client: TestClient) -> None:
    payload = json.dumps({
        "pan_deg": 6.25,
        "tilt_deg": -1.5,
        "x_steps": 625,
        "y_steps": -150,
        "driver_enabled": False,
        "limit_state": {"pan_left": False, "pan_right": False, "tilt_up": False, "tilt_down": False},
    }).encode()
    frame = encode_packet(msg_type=MessageType.TELEMETRY, seq_id=15, timestamp_ms=5000, payload=payload)

    response = client.post("/api/pico/protocol/read-sample", json={"sample_hex": frame.hex()})
    assert response.status_code == 200
    sample = response.json()
    assert sample["packets_parsed"] == 1
    assert sample["latest_telemetry"]["pose_source"] == "telemetry"
    assert sample["latest_telemetry"]["crc_status"] == "passed"
    assert sample["no_physical_command_generated"] is True

    state_response = client.get("/api/digital-twin/state")
    assert state_response.status_code == 200
    state = state_response.json()
    assert state["device_pose"]["pose_source"] == "telemetry"
    assert state["device_pose"]["pan_deg"] == 6.25
    assert state["telemetry_protocol"]["pose_source"] == "telemetry"
    assert state["telemetry_protocol"]["no_physical_command_generated"] is True


def test_digital_twin_fallback_when_protocol_telemetry_missing(client: TestClient) -> None:
    response = client.get("/api/digital-twin/state")
    assert response.status_code == 200
    payload = response.json()

    assert payload["telemetry_protocol"]["telemetry_missing"] is True
    assert payload["telemetry_protocol"]["pose_source"] in {"tracker_estimate", "fixture"}
    assert payload["device_pose"]["pose_source"] in {"tracker_estimate", "fixture"}
    assert payload["no_physical_command_generated"] is True


def test_pico_protocol_endpoints_are_read_only_by_default(client: TestClient) -> None:
    status = client.get("/api/pico/protocol/status").json()
    contract = client.get("/api/pico/protocol/contract").json()
    telemetry = client.get("/api/pico/protocol/latest-telemetry").json()

    assert status["serial_tx_enabled"] is False
    assert status["physical_tx_disabled"] is True
    assert status["physical_command_enabled"] is False
    assert status["no_physical_command_generated"] is True
    assert telemetry["no_physical_command_generated"] is True
    assert contract["serial_tx_enabled"] is False
    assert "SPD" in contract["explicitly_disabled_commands"]
    assert "LZR" in contract["explicitly_disabled_commands"]
    assert "STP" in contract["explicitly_disabled_commands"]


def test_phase36_no_legacy_physical_command_generation() -> None:
    root = Path(__file__).resolve().parents[2]
    files = [
        root / "backend" / "app" / "protocols" / "istiklal_serial_v1.py",
        root / "backend" / "app" / "api" / "routes_pico.py",
        root / "backend" / "app" / "services" / "pico_service.py",
        root / "frontend" / "src" / "api" / "pico.ts",
        root / "frontend" / "src" / "views" / "DebugCenterView.vue",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    forbidden = [
        "write(b\"SPD",
        "write(b\"LZR",
        "write(b\"STP",
        ".write(b'SPD",
        ".write(b'LZR",
        ".write(b'STP",
        "/api/serial/send-json",
        "send_speed_command(",
        "send_fire_command(",
        "set_servo_position(",
        "gpio_write(",
        "pwm_write(",
        "step_pulse(",
        "serial_tx_enabled: true",
    ]
    for item in forbidden:
        assert item not in combined
