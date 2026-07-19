"""
Fan control via the ChromeOS-EC host-command interface over LPC (ring0 ports).

SAFETY BY DESIGN: this module can only *raise* the fan target above whatever the
EC is already doing -- it never lowers it. So the worst case is "more cooling".
`auto()` hands full control back to the EC's thermal management.

The EC host-command (v3, non-MEC LPC) framing is implemented here; because it
writes to the EC it is EXPERIMENTAL and must be validated on the machine (Windows).
It is opt-in in the UI and off by default.
"""
from __future__ import annotations

import struct

# LPC host-command interface (standard, non-MEC)
ADDR_HOST_CMD = 0x204
ADDR_HOST_PACKET = 0x800
CMD_PROTOCOL_3 = 0xDA
STATUS_BUSY = 0x02

EC_CMD_PWM_SET_FAN_TARGET_RPM = 0x0025
EC_CMD_THERMAL_AUTO_FAN_CTRL = 0x0052


def _checksum(data: bytes) -> int:
    return (-sum(data)) & 0xFF


def _send(io, command: int, data: bytes = b"", cmd_version: int = 0):
    """Send one EC host command (protocol v3).

    Returns (result_code, response_payload) or (None, b"") on timeout.
    """
    hdr = bytearray(struct.pack("<BBHBBH", 3, 0, command, cmd_version, 0, len(data)))
    packet = bytes(hdr) + data
    packet = packet[:1] + bytes([_checksum(packet)]) + packet[2:]

    for i, b in enumerate(packet):
        io.write(ADDR_HOST_PACKET + i, b)
    io.write(ADDR_HOST_CMD, CMD_PROTOCOL_3)

    for _ in range(2000):
        if not (io.read(ADDR_HOST_CMD) & STATUS_BUSY):
            break
    else:
        return None, b""
    # response header: version, checksum, result(2), data_len(2), reserved(2)
    resp = bytes(io.read(ADDR_HOST_PACKET + i) for i in range(8))
    _ver, _csum, result, dlen, _res = struct.unpack("<BBHHH", resp)
    dlen = max(0, min(int(dlen), 64))
    payload = bytes(io.read(ADDR_HOST_PACKET + 8 + i) for i in range(dlen))
    return result, payload


def command(io, cmd: int, data: bytes = b"", cmd_version: int = 0):
    """Public helper: returns (result_code, response_payload)."""
    return _send(io, cmd, data, cmd_version)


def set_target_rpm(io, rpm: int) -> bool:
    """Set the EC fan target RPM (all EC fans). Returns True on EC success."""
    rpm = max(0, min(65534, int(rpm)))
    res, _ = _send(io, EC_CMD_PWM_SET_FAN_TARGET_RPM, struct.pack("<I", rpm), cmd_version=0)
    return res == 0


def auto(io) -> bool:
    """Return fans to the EC's automatic thermal control."""
    res, _ = _send(io, EC_CMD_THERMAL_AUTO_FAN_CTRL, b"", cmd_version=0)
    return res == 0


def boost_to(io, floor_rpm: int, measured_rpm: int) -> bool:
    """Up-only: enforce a minimum RPM. Never sets below what the fan is already doing."""
    target = max(int(floor_rpm), int(measured_rpm))
    return set_target_rpm(io, target)
