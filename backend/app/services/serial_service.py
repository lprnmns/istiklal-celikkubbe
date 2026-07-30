import json
import time
import threading
from pathlib import Path
from typing import Any

from app.mocks.mock_serial_transport import MockSerialTransport
from app.protocols.serial_json import (
    PicoMessageType,
    SerialJsonError,
    decode_rx_json_line,
    decode_tx_json_line,
    encode_json_line,
)
from app.schemas.config import AppConfig
from app.schemas.log import LogLevel
from app.schemas.serial import (
    SerialCommandResult,
    SerialConnectionState,
    SerialDirection,
    SerialLogEntry,
    SerialLogKind,
    SerialSendJsonRequest,
    SerialSimulateRxRequest,
    SerialStatus,
)
from app.services.log_service import JsonlLogService

SAFE_TX_TYPES = {"heartbeat", "disarm", "self_test", "set_mode"}
MOTION_TX_TYPES = {"speed_command", "motor_stop", "driver_enable", "driver_disable", "home"}
FIRE_TX_TYPES = {"fire_request", "set_servo_position", "set_servo", "trigger"}
RISKY_TX_TYPES = {
    "fire_request",
    "jog_motor",
    "set_motor_target",
    "set_servo_position",
    "set_servo",
    "enable_driver",
    "set_pin",
    "pwm_write",
    "step_pulse",
}
ACK_TYPES = {PicoMessageType.ACK, PicoMessageType.NACK}


class _RealSerialTransport:
    """Gercek pyserial transport; raw firmware protokolune byte yazar/okur."""

    def __init__(self, port: str, baudrate: int) -> None:
        import serial
        self._ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=0.1,
            write_timeout=0.05,
        )

    def write(self, data: bytes) -> None:
        try:
            self._ser.write(data)
        except Exception:
            pass

    def readline(self) -> bytes:
        try:
            return bytes(self._ser.readline())
        except Exception:
            return b""

    def reset_input_buffer(self) -> None:
        try:
            self._ser.reset_input_buffer()
        except Exception:
            pass

    def reset_output_buffer(self) -> None:
        try:
            self._ser.reset_output_buffer()
        except Exception:
            pass

    def close(self) -> None:
        try:
            self._ser.close()
        except Exception:
            pass

    @property
    def is_open(self) -> bool:
        return self._ser.is_open


class SerialService:
    def __init__(self, config: AppConfig, logger: JsonlLogService, magazine_state_path: Path | None = None) -> None:
        self.config = config
        self.logger = logger
        self._real_transport: _RealSerialTransport | None = None
        self._write_lock = threading.Lock()
        self._gateway_exchange_lock = threading.RLock()

        # Gerçek serial bağlantısı aç (real_write modu ve port tanımlıysa)
        if (
            config.serial.transport_mode == "real_write"
            and config.serial.port
            and config.serial.real_serial_enabled
        ):
            try:
                self._real_transport = _RealSerialTransport(
                    port=config.serial.port,
                    baudrate=config.serial.baudrate,
                )
                self.transport = self._real_transport
                self.connection_state = SerialConnectionState.PORT_OPEN_NO_TELEMETRY
                logger.emit(LogLevel.INFO, "SERIAL", f"Real serial opened: {config.serial.port} @ {config.serial.baudrate}")
            except Exception as exc:
                self.transport = MockSerialTransport()
                self.connection_state = SerialConnectionState.DISCONNECTED
                logger.emit(LogLevel.WARN, "SERIAL", f"Real serial FAILED, falling back to mock: {exc}")
        else:
            self.transport = MockSerialTransport()
            self.connection_state = SerialConnectionState.MOCK_CONNECTED

        self.seq_counter = 0
        self.pending: dict[int, dict[str, Any]] = {}
        self.logs: list[SerialLogEntry] = []
        self.last_tx: dict[str, Any] | None = None
        self.last_rx: dict[str, Any] | None = None
        self.last_command_sent_at: float | None = None
        self.last_command_completed_at: float | None = None
        self.last_command_kind: str | None = None
        self.last_command_raw: str | None = None
        self.last_command_ack_state = "unknown"
        self.last_command_rtt_ms: int | None = None
        self.last_command_error: str | None = None
        self.magazine_capacity = 8
        self.magazine_remaining = 8
        self.acknowledged_shot_count = 0
        self.magazine_reload_count = 0
        self.magazine_updated_at: float | None = None
        self.magazine_state_path = magazine_state_path
        self.last_heartbeat_at: float | None = None
        self.last_error: str | None = None
        self._log_id = 0
        self.readonly_connected = False
        self.readonly_transport_source = "mock"
        self.readonly_telemetry_received = False
        self.readonly_pico_verified = False
        self.raw_pico_verified = False
        self.gateway_last_heartbeat_at: float | None = None
        self._mock_estop_active = False
        self._mock_trigger_armed = False
        self._mock_driver_enabled = False
        self._load_magazine_state()

        if self._real_transport is not None and self.config.serial.protocol_mode == "raw":
            self._probe_raw_pico()


    def status(self) -> SerialStatus:
        self.check_timeouts()
        heartbeat_age_ms = None
        if self.last_heartbeat_at is not None:
            heartbeat_age_ms = int((time.time() - self.last_heartbeat_at) * 1000)
            if heartbeat_age_ms > self.config.serial.heartbeat_timeout_ms:
                self.last_error = "HEARTBEAT_TIMEOUT"
                self.connection_state = SerialConnectionState.FAULT
        return SerialStatus(
            connection_state=self.connection_state,
            transport_mode="real_readonly" if self.readonly_connected else self.config.serial.transport_mode,
            transport_source=self.readonly_transport_source if self.readonly_connected else "real_serial" if self._real_transport is not None else "mock",
            protocol_mode=self.config.serial.protocol_mode,
            real_serial_enabled=self.config.serial.real_serial_enabled,
            real_serial_readonly=self.config.serial.real_serial_readonly,
            readonly=self.readonly_connected,
            telemetry_received=self.readonly_telemetry_received,
            pico_verified=self.readonly_pico_verified or self.raw_pico_verified,
            physical_command_enabled=self.config.hardware.physical_command_enabled,
            last_tx=self.last_tx,
            last_rx=self.last_rx,
            pending_ack_count=len(self.pending),
            command_queue_depth=len(self.pending),
            last_command_age_ms=self._last_command_age_ms(),
            last_command_kind=self.last_command_kind,
            last_command_raw=self.last_command_raw,
            last_command_ack_state=self.last_command_ack_state,
            last_command_rtt_ms=self.last_command_rtt_ms,
            last_command_error=self.last_command_error,
            magazine_capacity=self.magazine_capacity,
            magazine_remaining=self.magazine_remaining,
            magazine_empty=self.magazine_remaining <= 0,
            acknowledged_shot_count=self.acknowledged_shot_count,
            magazine_reload_count=self.magazine_reload_count,
            magazine_updated_at=self.magazine_updated_at,
            heartbeat_age_ms=heartbeat_age_ms,
            ack_timeout_ms=self.config.serial.ack_timeout_ms,
            heartbeat_timeout_ms=self.config.serial.heartbeat_timeout_ms,
            last_error=self.last_error,
        )

    def recent_logs(self) -> list[SerialLogEntry]:
        return self.logs[-200:]

    def clear_logs(self) -> SerialCommandResult:
        self.logs.clear()
        self.pending.clear()
        self.last_error = None
        entry = self._append_log(SerialDirection.SYSTEM, SerialLogKind.STATUS, {"action": "clear_logs"})
        return SerialCommandResult(accepted=True, reason="Serial logs cleared.", status=self.status(), log_entry=entry)

    def reset_magazine(self, capacity: int | None = None) -> SerialCommandResult:
        if capacity is not None:
            self.magazine_capacity = max(0, int(capacity))
        self.magazine_remaining = self.magazine_capacity
        self.magazine_reload_count += 1
        self.magazine_updated_at = time.time()
        self._persist_magazine_state()
        entry = self._append_log(
            SerialDirection.SYSTEM,
            SerialLogKind.STATUS,
            {
                "action": "reset_magazine",
                "magazine_capacity": self.magazine_capacity,
                "magazine_reload_count": self.magazine_reload_count,
            },
        )
        return SerialCommandResult(accepted=True, reason="Magazine counter reset.", status=self.status(), log_entry=entry)

    def send_json(self, request: SerialSendJsonRequest) -> SerialCommandResult:
        message = dict(request.message)
        message_type = str(message.get("type", ""))

        if self.readonly_connected or self.config.serial.transport_mode == "real_readonly":
            reason = "physical_commands_disabled_in_phase12_readonly"
            return self._reject(message, reason)

        if message_type in RISKY_TX_TYPES:
            return self._reject(message, "Risky serial command is disabled in phase 12.")
        if message_type not in SAFE_TX_TYPES:
            return self._reject(message, f"Message type '{message_type}' is not allowlisted.")

        if "seq" not in message:
            message["seq"] = self.next_seq()

        try:
            decoded = decode_tx_json_line(encode_json_line(message))
        except SerialJsonError as exc:
            return self._reject(message, f"Invalid JSON-line TX message: {exc}")

        payload = decoded.model_dump(mode="json")
        raw = encode_json_line(decoded)
        self.transport.write(raw)
        self.last_tx = payload
        if message_type != "heartbeat":
            self.pending[int(payload["seq"])] = {"message": payload, "sent_at": time.time()}
        entry = self._append_log(SerialDirection.TX, SerialLogKind.TX, payload, raw.decode("utf-8").strip())
        self.logger.emit(LogLevel.INFO, "SERIAL", "Mock serial TX", payload)
        return SerialCommandResult(accepted=True, reason="Message sent to mock transport.", status=self.status(), log_entry=entry)

    def simulate_rx(self, request: SerialSimulateRxRequest) -> SerialCommandResult:
        try:
            decoded = decode_rx_json_line(encode_json_line(request.message))
        except SerialJsonError as exc:
            self.last_error = "SERIAL_RX_DECODE_ERROR"
            entry = self._append_log(
                SerialDirection.RX,
                SerialLogKind.ERROR,
                request.message,
                error=str(exc),
            )
            return SerialCommandResult(accepted=False, reason=f"Invalid RX message: {exc}", status=self.status(), log_entry=entry)

        payload = decoded.model_dump(mode="json")
        self.last_rx = payload
        kind = self._kind_for_rx(payload)
        if payload["type"] == "heartbeat":
            self.last_heartbeat_at = time.time()
            if self.connection_state == SerialConnectionState.FAULT and self.last_error == "HEARTBEAT_TIMEOUT":
                self.connection_state = SerialConnectionState.MOCK_CONNECTED
                self.last_error = None
        if payload["type"] == "ack":
            self.pending.pop(int(payload["seq"]), None)
        if payload["type"] == "nack":
            self.pending.pop(int(payload["seq"]), None)
            self.last_error = f"NACK:{payload.get('reason', 'unknown')}"
        if payload["type"] == "error":
            self.last_error = f"{payload.get('code', 'SERIAL_ERROR')}:{payload.get('message', '')}"
        entry = self._append_log(SerialDirection.RX, kind, payload)
        self.logger.emit(LogLevel.INFO if kind in {SerialLogKind.RX, SerialLogKind.ACK} else LogLevel.WARN, "SERIAL", "Mock serial RX", payload)
        return SerialCommandResult(accepted=True, reason="RX message accepted into mock transport.", status=self.status(), log_entry=entry)

    def check_timeouts(self) -> list[SerialLogEntry]:
        now = time.time()
        timed_out: list[int] = []
        entries: list[SerialLogEntry] = []
        for seq, pending in self.pending.items():
            if (now - float(pending["sent_at"])) * 1000 > self.config.serial.ack_timeout_ms:
                timed_out.append(seq)
        for seq in timed_out:
            message = self.pending.pop(seq)["message"]
            self.last_error = f"ACK_TIMEOUT:{seq}"
            self.last_command_ack_state = "timeout"
            self.last_command_error = self.last_error
            self.connection_state = SerialConnectionState.FAULT
            entry = self._append_log(
                SerialDirection.SYSTEM,
                SerialLogKind.TIMEOUT,
                {"seq": seq, "message": message, "fault": "ACK_TIMEOUT"},
            )
            entries.append(entry)
            self.logger.emit(LogLevel.ERROR, "SAFETY", "Serial ACK timeout", entry.model_dump(mode="json"))

        if self.last_heartbeat_at is not None:
            heartbeat_age_ms = int((now - self.last_heartbeat_at) * 1000)
            if heartbeat_age_ms > self.config.serial.heartbeat_timeout_ms and self.last_error != "HEARTBEAT_TIMEOUT":
                self.last_error = "HEARTBEAT_TIMEOUT"
                self.connection_state = SerialConnectionState.FAULT
                entry = self._append_log(
                    SerialDirection.SYSTEM,
                    SerialLogKind.TIMEOUT,
                    {"fault": "HEARTBEAT_TIMEOUT", "heartbeat_age_ms": heartbeat_age_ms},
                )
                entries.append(entry)
                self.logger.emit(LogLevel.ERROR, "SAFETY", "Serial heartbeat timeout", entry.model_dump(mode="json"))
        return entries

    def next_seq(self) -> int:
        self.seq_counter = (self.seq_counter + 1) % 256
        if self.seq_counter == 0:
            self.seq_counter = 1
        return self.seq_counter

    def mark_real_readonly_connected(self, hardware_connection_state: str = "PORT_OPEN_NO_TELEMETRY") -> None:
        self.readonly_connected = True
        self.readonly_transport_source = "mock" if hardware_connection_state == "MOCK_READONLY_CONNECTED" else "real_serial"
        self.readonly_telemetry_received = hardware_connection_state in {"READONLY_CONNECTED_UNVERIFIED", "PICO_READONLY_VERIFIED"}
        self.readonly_pico_verified = hardware_connection_state == "PICO_READONLY_VERIFIED"
        try:
            self.connection_state = SerialConnectionState(hardware_connection_state)
        except ValueError:
            self.connection_state = SerialConnectionState.PORT_OPEN_NO_TELEMETRY
        self._append_log(
            SerialDirection.SYSTEM,
            SerialLogKind.STATUS,
            {
                "transport_mode": "real_readonly",
                "transport_source": self.readonly_transport_source,
                "connection_state": self.connection_state,
                "no_physical_command_generated": True,
            },
        )

    def mark_real_readonly_disconnected(self) -> None:
        self.readonly_connected = False
        self.readonly_transport_source = "mock"
        self.readonly_telemetry_received = False
        self.readonly_pico_verified = False
        if self.connection_state in {
            SerialConnectionState.PORT_OPEN_NO_TELEMETRY,
            SerialConnectionState.READONLY_CONNECTED_UNVERIFIED,
            SerialConnectionState.PICO_READONLY_VERIFIED,
            SerialConnectionState.MOCK_READONLY_CONNECTED,
        }:
            self.connection_state = SerialConnectionState.DISCONNECTED
        self._append_log(
            SerialDirection.SYSTEM,
            SerialLogKind.STATUS,
            {"transport_mode": "mock", "no_physical_command_generated": True},
        )

    def _reject(self, message: dict[str, Any], reason: str) -> SerialCommandResult:
        self.last_error = reason
        entry = self._append_log(SerialDirection.SYSTEM, SerialLogKind.ERROR, message, error=reason)
        self.logger.emit(LogLevel.WARN, "SERIAL", "Serial command rejected", {"reason": reason, "message": message})
        return SerialCommandResult(accepted=False, reason=reason, status=self.status(), log_entry=entry)

    def _append_log(
        self,
        direction: SerialDirection,
        kind: SerialLogKind,
        message: dict[str, Any],
        raw: str | None = None,
        error: str | None = None,
    ) -> SerialLogEntry:
        self._log_id += 1
        entry = SerialLogEntry(
            id=self._log_id,
            ts=time.time(),
            direction=direction,
            kind=kind,
            message=message,
            raw=raw,
            error=error,
        )
        self.logs.append(entry)
        self.logs = self.logs[-500:]
        return entry

    def _write_raw(self, raw: str, *, clear_output_buffer: bool = False) -> None:
        data = raw.encode("utf-8")
        with self._write_lock:
            if clear_output_buffer and hasattr(self.transport, "reset_output_buffer"):
                self.transport.reset_output_buffer()
            self.transport.write(data)

    def _mark_command_sent(self, kind: str, raw: str, *, ack_state: str = "sent") -> None:
        self.last_command_sent_at = time.time()
        self.last_command_completed_at = None
        self.last_command_kind = kind
        self.last_command_raw = raw.strip()
        self.last_command_ack_state = ack_state
        self.last_command_rtt_ms = None
        self.last_command_error = None

    def _mark_command_done(self, state: str = "sent") -> None:
        now = time.time()
        if self.last_command_sent_at is not None:
            self.last_command_rtt_ms = int((now - self.last_command_sent_at) * 1000)
        self.last_command_completed_at = now
        self.last_command_ack_state = state

    def _last_command_age_ms(self) -> int | None:
        if self.last_command_sent_at is None:
            return None
        return int((time.time() - self.last_command_sent_at) * 1000)

    def _probe_raw_pico(self) -> None:
        if self._real_transport is None:
            return

        deadline = time.time() + 1.5
        try:
            with self._write_lock:
                self._real_transport.reset_input_buffer()
                self._real_transport.write(b"PING\n")
                self.last_tx = {"type": "raw_probe", "raw": "PING"}
                while time.time() < deadline:
                    line = self._real_transport.readline().decode("utf-8", errors="replace").strip()
                    if not line:
                        continue
                    self.last_rx = {"type": "raw_probe_response", "raw": line}
                    self._append_log(SerialDirection.RX, SerialLogKind.RX, self.last_rx, line)
                    if line == "OK,PONG":
                        self.raw_pico_verified = True
                        self.logger.emit(LogLevel.INFO, "SERIAL", "Raw Pico verified with PING/OK,PONG")
                        return
            self.logger.emit(LogLevel.WARN, "SERIAL", "Raw Pico probe timed out")
        except Exception as exc:
            self.last_error = f"RAW_PICO_PROBE_FAILED:{exc}"
            self.logger.emit(LogLevel.WARN, "SERIAL", "Raw Pico probe failed", {"error": str(exc)})

    # ------------------------------------------------------------------
    # Motor komut yolu (SPD, DRV, STP, HOM — ateş HER ZAMAN kapalı)
    # ------------------------------------------------------------------

    def motion_allowed(self) -> bool:
        """Legacy raw motion write için fail-closed izin kontrolü."""
        return (
            self.config.system.hardware_enabled
            and not self.config.system.dry_run
            and self.config.hardware.physical_command_enabled
            and self.config.hardware.allow_physical_motion
            and self.config.motion.real_motion_enabled
        )

    def send_speed_command(self, speed_x: int, speed_y: int) -> SerialCommandResult:
        """
        SPD,{speed_x},{speed_y}\n — Pico'ya motor hız komutu gönderir.
        Ateş/trigger komutları BU FONKSIYON ÜZERINDEN GÖNDERİLEMEZ.
        """
        if not self.motion_allowed():
            return self._reject(
                {"type": "speed_command", "speed_x": speed_x, "speed_y": speed_y},
                "Motion not allowed: tracking.enabled, motion.real_motion_enabled, or hardware.allow_physical_motion must be true."
            )
        raw = f"SPD,{int(speed_x)},{int(speed_y)}\n"
        self._mark_command_sent("speed_command", raw)
        self._write_raw(raw)
        self._mark_command_done("sent")
        payload = {"type": "speed_command", "speed_x": speed_x, "speed_y": speed_y, "raw": raw.strip()}
        self.last_tx = payload
        entry = self._append_log(SerialDirection.TX, SerialLogKind.TX, payload, raw.strip())
        return SerialCommandResult(accepted=True, reason="SPD command sent.", status=self.status(), log_entry=entry)

    def send_motor_command(self, command: str) -> SerialCommandResult:
        """
        Genel motor komutları: DRV,1 | DRV,0 | STP | HOM
        Fire/trigger komutları ASLA gönderilmez.
        """
        cmd_type = command.split(",")[0].upper()
        if not self.motion_allowed():
            return self._reject({"type": "motor_command", "raw": command}, "Motion not allowed.")
        raw = f"{command}\n"
        self._mark_command_sent("motor_command", raw)
        self._write_raw(raw)
        self._mark_command_done("sent")
        payload = {"type": "motor_command", "raw": command}
        self.last_tx = payload
        entry = self._append_log(SerialDirection.TX, SerialLogKind.TX, payload, raw.strip())
        return SerialCommandResult(accepted=True, reason=f"{cmd_type} command sent.", status=self.status(), log_entry=entry)

    def send_fire_command(self, state: int) -> SerialCommandResult:
        """
        Legacy LZR safety release helper.

        state=1 fiziksel ateş isteği CommandGateway uygulanana kadar her
        durumda reddedilir. state=0 yalnız mevcut/legacy bir tetik durumunu
        güvenli konuma bırakmak için korunur.
        """
        if int(state) == 1:
            return self._reject(
                {"type": "blocked_fire", "state": state},
                "Direct physical fire is disabled; CommandGateway authorization is required.",
            )
        if not self.config.hardware.allow_physical_fire:
            return self._reject(
                {"type": "blocked_fire", "state": state},
                "Fire permanently blocked in hardware config (allow_physical_fire=False)."
            )
        if int(state) == 1 and self.magazine_remaining <= 0:
            return self._reject(
                {"type": "blocked_fire", "state": state, "magazine_remaining": self.magazine_remaining},
                "Magazine empty: fire command blocked."
            )
        raw = f"LZR,{int(state)}\n"
        self._mark_command_sent("fire_command", raw)
        if int(state) == 1:
            with self._write_lock:
                if hasattr(self.transport, "reset_output_buffer"):
                    self.transport.reset_output_buffer()
                self.transport.write(b"SPD,0,0\n")
                self.transport.write(raw.encode("utf-8"))
            self.magazine_remaining = max(0, self.magazine_remaining - 1)
        else:
            self._write_raw(raw)
        self._mark_command_done("sent")
        payload = {"type": "fire_command", "state": state, "raw": raw.strip()}
        self.last_tx = payload
        entry = self._append_log(SerialDirection.TX, SerialLogKind.TX, payload, raw.strip())
        return SerialCommandResult(accepted=True, reason=f"LZR,{state} command sent.", status=self.status(), log_entry=entry)

    # ------------------------------------------------------------------
    # CommandGateway raw protocol path
    # ------------------------------------------------------------------

    def gateway_exchange(
        self,
        command: str,
        expected_ack: tuple[str, ...] = (),
        *,
        count_physical_shot: bool = True,
    ) -> SerialCommandResult:
        # A heartbeat monitor, trigger-release timer and operator command may
        # all run on different threads. Keep write + matching ACK atomic so a
        # PING response can never be consumed as an SPD/LZR response.
        with self._gateway_exchange_lock:
            return self._gateway_exchange_unlocked(
                command,
                expected_ack,
                count_physical_shot=count_physical_shot,
            )

    def _gateway_exchange_unlocked(
        self,
        command: str,
        expected_ack: tuple[str, ...] = (),
        *,
        count_physical_shot: bool = True,
    ) -> SerialCommandResult:
        """Gateway-only raw command exchange for the Pico command contract.

        Direct callers remain blocked from LZR,1. CommandGateway is the only
        service that uses this method after visible preflight has passed.
        """
        if self.readonly_connected or self.config.serial.transport_mode == "real_readonly":
            return self._reject({"type": "gateway_raw", "command": command}, "PICO_READONLY")

        if command.strip() == "LZR,1" and self.magazine_remaining <= 0:
            return self._reject(
                {"type": "gateway_raw", "command": command, "magazine_remaining": self.magazine_remaining},
                "MAGAZINE_EMPTY",
            )

        raw = f"{command.strip()}\n"
        self._mark_command_sent("gateway_raw", raw, ack_state="pending" if expected_ack else "sent")
        try:
            self._write_raw(raw)
        except Exception as exc:
            self.connection_state = SerialConnectionState.FAULT
            return self._reject({"type": "gateway_raw", "command": command}, f"PICO_WRITE_FAILED:{exc}")

        payload = {"type": "gateway_raw", "command": command.strip(), "raw": raw.strip()}
        self.last_tx = payload
        tx_entry = self._append_log(SerialDirection.TX, SerialLogKind.TX, payload, raw.strip())
        if not expected_ack:
            self._mark_command_done("sent")
            return SerialCommandResult(
                accepted=True,
                reason=f"Gateway command sent: {command.strip()}",
                status=self.status(),
                log_entry=tx_entry,
                no_physical_command_generated=self._real_transport is None,
            )

        response = self._gateway_response_for(command.strip())
        if response is None:
            self.connection_state = SerialConnectionState.FAULT
            self.last_error = f"PICO_ACK_TIMEOUT:{command.strip()}"
            self.last_command_ack_state = "timeout"
            self.last_command_error = self.last_error
            return self._reject(payload, self.last_error)

        self.last_rx = {"type": "gateway_raw_response", "raw": response}
        matched = self._gateway_ack_matches(response, expected_ack)
        self._append_log(
            SerialDirection.RX,
            SerialLogKind.ACK if matched else SerialLogKind.NACK,
            self.last_rx,
            response,
            None if matched else "unexpected_gateway_ack",
        )
        if not matched:
            self.connection_state = SerialConnectionState.FAULT
            self.last_error = f"PICO_UNEXPECTED_ACK:{response}"
            self.last_command_ack_state = "nack"
            self.last_command_error = self.last_error
            return self._reject(payload, self.last_error)

        self._mark_command_done("ack")
        if command.strip() == "LZR,1" and count_physical_shot:
            # Count only a Pico ACK, never an operator click, a candidate or
            # an unacknowledged serial write. This is the physical-shot ledger
            # used by mission/CO₂ acceptance runs.
            self.magazine_remaining = max(0, self.magazine_remaining - 1)
            self.acknowledged_shot_count += 1
            self.magazine_updated_at = time.time()
            self._persist_magazine_state()
        if command.strip() == "PING":
            self.raw_pico_verified = True
            self.gateway_last_heartbeat_at = time.time()
            # A matched PONG is direct proof that the transport and firmware
            # command parser are healthy again. A previous command-specific
            # NACK/timeout remains visible in the serial log, but must not keep
            # a successfully re-preflighted Pico permanently FAULT-locked.
            self.connection_state = SerialConnectionState.MOCK_CONNECTED if self._real_transport is None else SerialConnectionState.PORT_OPEN_NO_TELEMETRY
            if self.last_error and self.last_error.startswith(("PICO_ACK_TIMEOUT:", "PICO_UNEXPECTED_ACK:", "HEARTBEAT_TIMEOUT")):
                self.last_error = None
        return SerialCommandResult(
            accepted=True,
            reason=f"Pico ACK: {response}",
            status=self.status(),
            log_entry=tx_entry,
            no_physical_command_generated=self._real_transport is None,
        )

    def gateway_connect_real(self, port: str, baudrate: int) -> tuple[bool, str]:
        """Select a Pico from the operator UI for a live Gateway profile.

        This is deliberately runtime-only: a technician does not edit source,
        environment variables, or hidden flags to return from mock to a
        connected Pico.  It opens no output by itself; `PING`/preflight still
        gates every later output command.
        """
        if not port.strip():
            return False, "PICO_PORT_REQUIRED"
        try:
            if self._real_transport is not None:
                self._real_transport.close()
            self._real_transport = _RealSerialTransport(port=port.strip(), baudrate=int(baudrate))
            self.transport = self._real_transport
            self.config.serial.port = port.strip()
            self.config.serial.baudrate = int(baudrate)
            self.config.serial.transport_mode = "real_write"
            self.config.serial.real_serial_enabled = True
            self.connection_state = SerialConnectionState.PORT_OPEN_NO_TELEMETRY
            self.last_error = None
            return True, "PICO_PORT_OPEN"
        except Exception as exc:
            self._real_transport = None
            self.transport = MockSerialTransport()
            self.connection_state = SerialConnectionState.FAULT
            self.last_error = f"PICO_CONNECT_FAILED:{exc}"
            return False, "PICO_CONNECT_FAILED"

    def gateway_disconnect(self) -> None:
        """End a setup session without retaining a physical serial handle."""
        self.gateway_safe_stop()
        if self._real_transport is not None:
            try:
                self._real_transport.close()
            except Exception:
                pass
        self._real_transport = None
        self.transport = MockSerialTransport()
        self.connection_state = SerialConnectionState.DISCONNECTED
        self.raw_pico_verified = False
        self.gateway_last_heartbeat_at = None

    def discover_gateway_pico(self, timeout_s: float = 5.0, baudrate: int = 460800) -> tuple[str | None, str, int | None]:
        """Probe eligible USB CDC ports with harmless PING only.

        This deliberately does not alter the current gateway transport or emit
        any actuator command. The chosen port is still connected by the
        operator through the normal visible connect + preflight flow.
        """
        deadline = time.time() + max(0.1, min(float(timeout_s), 5.0))
        candidates: list[tuple[str, bool]] = []
        try:
            from serial.tools import list_ports  # type: ignore[import-not-found]
            for item in list_ports.comports():
                if not (item.device.startswith(("/dev/ttyACM", "/dev/ttyUSB", "/dev/serial/")) or item.device.upper().startswith("COM")):
                    continue
                is_pico = item.vid == 0x2E8A or "2E8A" in str(item.hwid).upper() or "PICO" in str(item.description).upper()
                candidates.append((item.device, is_pico))
            candidates.sort(key=lambda item: (not item[1], item[0]))
        except Exception:
            pass
        if not candidates:
            # Keep the UI contract deterministic: the operator sees a full
            # 5-second discovery window, even if the OS currently exposes no
            # eligible USB CDC port at all.
            remaining = deadline - time.time()
            if remaining > 0:
                time.sleep(remaining)
            return None, "PICO_NOT_FOUND", None
        baud_candidates = list(dict.fromkeys([int(baudrate), 115200, 460800]))
        for port, _is_pico in candidates:
            for candidate_baud in baud_candidates:
                if time.time() >= deadline:
                    break
                probe = None
                try:
                    probe = _RealSerialTransport(port=port, baudrate=candidate_baud)
                    probe.reset_input_buffer()
                    probe.write(b"PING\n")
                    probe_deadline = min(deadline, time.time() + 0.45)
                    while time.time() < probe_deadline:
                        response = probe.readline().decode("utf-8", errors="replace").strip()
                        if not response:
                            continue
                        if "OK,PONG" in response or response == "PONG" or '"message":"PONG"' in response:
                            return port, "PICO_FOUND", candidate_baud
                        break
                except Exception:
                    continue
                finally:
                    if probe is not None:
                        try:
                            probe.close()
                        except Exception:
                            pass
        remaining = deadline - time.time()
        if remaining > 0:
            time.sleep(remaining)
        return None, "PICO_NOT_FOUND", None

    def gateway_safe_stop(self) -> None:
        """Best-effort safing path used on E-stop, heartbeat loss or disconnect."""
        for command, expected in (
            ("LZR,0", ("OK,LASER_0", "FIRE_SERVO_RELEASED")),
            ("STP", ("OK,STOP", "EMERGENCY_STOP")),
            ("DRV,0", ("OK,DRIVER_DISABLED",)),
        ):
            try:
                self.gateway_exchange(command, expected)
            except Exception:
                continue

    def _load_magazine_state(self) -> None:
        if self.magazine_state_path is None or not self.magazine_state_path.exists():
            return
        try:
            raw = json.loads(self.magazine_state_path.read_text(encoding="utf-8"))
            self.magazine_capacity = max(0, int(raw["magazine_capacity"]))
            self.magazine_remaining = min(self.magazine_capacity, max(0, int(raw["magazine_remaining"])))
            self.acknowledged_shot_count = max(0, int(raw.get("acknowledged_shot_count", 0)))
            self.magazine_reload_count = max(0, int(raw.get("magazine_reload_count", 0)))
            updated = raw.get("magazine_updated_at")
            self.magazine_updated_at = float(updated) if updated is not None else None
        except (OSError, ValueError, TypeError, KeyError):
            # A corrupted ledger must not silently restore fire authority.
            self.magazine_remaining = 0
            self.magazine_updated_at = time.time()
            self.last_error = "SHOT_BUDGET_STATE_INVALID"

    def _persist_magazine_state(self) -> None:
        if self.magazine_state_path is None:
            return
        self.magazine_state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "magazine_capacity": self.magazine_capacity,
            "magazine_remaining": self.magazine_remaining,
            "acknowledged_shot_count": self.acknowledged_shot_count,
            "magazine_reload_count": self.magazine_reload_count,
            "magazine_updated_at": self.magazine_updated_at,
        }
        self.magazine_state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def set_mock_estop(self, active: bool) -> None:
        """Contract-test hook; never used as a real hardware E-stop source."""
        self._mock_estop_active = bool(active)

    def _gateway_response_for(self, command: str) -> str | None:
        if self._real_transport is None:
            return self._mock_gateway_response(command)
        deadline = time.time() + (self.config.serial.ack_timeout_ms / 1000.0)
        while time.time() < deadline:
            line = self._real_transport.readline().decode("utf-8", errors="replace").strip()
            if line:
                return line
        return None

    def _mock_gateway_response(self, command: str) -> str:
        if command == "PING":
            return "OK,PONG"
        if command == "STAT":
            return f"OK,STAT,ESTOP={1 if self._mock_estop_active else 0},DRV={1 if self._mock_driver_enabled else 0},ARM={1 if self._mock_trigger_armed else 0}"
        if command.startswith("DRV,"):
            self._mock_driver_enabled = command.split(",", 1)[1] != "0"
            return "OK,DRIVER_ENABLED" if self._mock_driver_enabled else "OK,DRIVER_DISABLED"
        if command == "STP":
            return "OK,STOP"
        if command.startswith("ARM,"):
            requested = command.split(",", 1)[1] != "0"
            if requested and self._mock_estop_active:
                return "ERR,ESTOP_ACTIVE"
            self._mock_trigger_armed = requested
            return "OK,ARM_1" if requested else "OK,ARM_0"
        if command.startswith("SRV,CFG,"):
            return "OK,SERVO_CONFIGURED"
        if command.startswith("CFG_SERVO,"):
            values = command.split(",")
            return f"OK,SERVO_CFG,{values[1]},{values[2]}" if len(values) == 3 else "ERR,INVALID_SERVO_CFG"
        if command == "SRV,TEST":
            if self._mock_estop_active:
                return "ERR,ESTOP_ACTIVE"
            if not self._mock_trigger_armed:
                return "ERR,TRIGGER_NOT_ARMED"
            return "OK,SERVO_TEST"
        if command.startswith("LZR,"):
            requested = command.split(",", 1)[1] != "0"
            if requested and self._mock_estop_active:
                return "ERR,ESTOP_ACTIVE"
            if requested and not self._mock_trigger_armed:
                return "ERR,TRIGGER_NOT_ARMED"
            return "OK,LASER_1" if requested else "OK,LASER_0"
        if command.startswith("SPD,"):
            return "OK,SPD"
        return "ERR,UNKNOWN_CMD"

    @staticmethod
    def _gateway_ack_matches(response: str, expected_ack: tuple[str, ...]) -> bool:
        if response.startswith("{"):
            try:
                payload = json.loads(response)
            except json.JSONDecodeError:
                payload = {}
            if payload.get("type") == "ack" and payload.get("accepted") is True:
                message = str(payload.get("message", ""))
                return any(token in message for token in expected_ack)
            return False
        return any(token in response for token in expected_ack)

    @staticmethod
    def _kind_for_rx(payload: dict[str, Any]) -> SerialLogKind:
        if payload["type"] == "ack":
            return SerialLogKind.ACK
        if payload["type"] == "nack":
            return SerialLogKind.NACK
        if payload["type"] == "error":
            return SerialLogKind.ERROR
        return SerialLogKind.RX
