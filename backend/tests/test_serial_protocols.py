import pytest

from app.protocols.crc16 import crc16_xmodem
from app.protocols.serial_binary import (
    BinaryMessageType,
    BinaryPacket,
    BinaryPacketError,
    decode_packet,
    encode_packet,
)
from app.protocols.serial_json import (
    AckRx,
    DisarmTx,
    SerialJsonError,
    decode_rx_json_line,
    decode_tx_json_line,
    encode_json_line,
)


def test_json_line_encode_decode_roundtrip() -> None:
    message = DisarmTx(seq=2, reason="operator_request")
    encoded = encode_json_line(message)

    assert encoded.endswith(b"\n")
    decoded = decode_tx_json_line(encoded)
    assert decoded.type == "disarm"
    assert decoded.seq == 2


def test_json_line_invalid_message_negative() -> None:
    with pytest.raises(SerialJsonError):
        decode_tx_json_line(b'{"type":"heartbeat"}\n')


def test_json_line_rx_ack_roundtrip() -> None:
    message = AckRx(seq=2, accepted=True)
    decoded = decode_rx_json_line(encode_json_line(message))

    assert decoded.type == "ack"
    assert decoded.seq == 2


def test_crc16_xmodem_vector() -> None:
    assert crc16_xmodem(b"123456789") == 0x31C3


def test_binary_packet_encode_decode_roundtrip() -> None:
    packet = BinaryPacket(message_type=BinaryMessageType.DISARM, seq=7, payload=b"safe")

    decoded = decode_packet(encode_packet(packet))

    assert decoded == packet


def test_binary_invalid_start_end_negative() -> None:
    packet = bytearray(encode_packet(BinaryPacket(BinaryMessageType.HEARTBEAT, 1, b"")))
    packet[0] = 0x00
    with pytest.raises(BinaryPacketError, match="START"):
        decode_packet(bytes(packet))

    packet = bytearray(encode_packet(BinaryPacket(BinaryMessageType.HEARTBEAT, 1, b"")))
    packet[-1] = 0x00
    with pytest.raises(BinaryPacketError, match="END"):
        decode_packet(bytes(packet))


def test_binary_len_mismatch_negative() -> None:
    packet = bytearray(encode_packet(BinaryPacket(BinaryMessageType.HEARTBEAT, 1, b"abc")))
    packet[3] = 2
    with pytest.raises(BinaryPacketError, match="LEN"):
        decode_packet(bytes(packet))


def test_binary_crc_invalid_negative() -> None:
    packet = bytearray(encode_packet(BinaryPacket(BinaryMessageType.HEARTBEAT, 1, b"abc")))
    packet[-3] ^= 0xFF
    with pytest.raises(BinaryPacketError, match="CRC"):
        decode_packet(bytes(packet))


def test_binary_unknown_type_negative() -> None:
    packet = bytearray(encode_packet(BinaryPacket(BinaryMessageType.HEARTBEAT, 1, b"")))
    packet[1] = 0xFE
    crc = crc16_xmodem(bytes(packet[1:4])).to_bytes(2, "big")
    packet[4:6] = crc
    with pytest.raises(BinaryPacketError, match="unknown TYPE"):
        decode_packet(bytes(packet))
