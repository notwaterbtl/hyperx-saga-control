from __future__ import annotations

import array
import dataclasses
import errno
import fcntl
import glob
import os
import select
import struct
import time
from pathlib import Path
from typing import Iterable, Optional

VID_HP = 0x03F0
PID_WIRED = 0x04BF
PID_WIRELESS = 0x06BF
KNOWN_PIDS = {PID_WIRED, PID_WIRELESS}
FORCE_CONFIG_ENV = 'HYPERX_SAGA_CONFIG_DEV'

DEFAULT_DPI = [400, 800, 1600, 3200]

# Native Saga Pro polling/report-rate field inside report 0x32.
# Decoded from wireless NGENUITY captures and generalized from the
# interval-byte relationship:
#   rate_hz = 8000 / interval_code
# Confirmed / product-supported mapping:
#   1000 Hz -> interval byte 0x08
#   2000 Hz -> interval byte 0x04  (2.4 GHz wireless only)
#   4000 Hz -> interval byte 0x02  (2.4 GHz wireless only)
# Derived from the same interval formula:
#   500 Hz  -> 0x10
#   250 Hz  -> 0x20
#   125 Hz  -> 0x40
# Wired mode is limited in the UI to 1000 Hz and below.
# Wireless mode exposes the full set, including 2000 Hz and 4000 Hz.
POLLING_RATE_TO_CODE = {
    125: 0x40,
    250: 0x20,
    500: 0x10,
    1000: 0x08,
    2000: 0x04,
    4000: 0x02,
}
POLLING_CODE_TO_RATE = {v: k for k, v in POLLING_RATE_TO_CODE.items()}
WIRELESS_POLLING_RATES = [4000, 2000, 1000, 500, 250, 125]
WIRED_POLLING_RATES = [1000, 500, 250, 125]
WIRELESS_ONLY_POLLING_RATES = {2000, 4000}
DEFAULT_DPI_COLORS = [
    (0xFF, 0x00, 0x00),  # stage 0: red
    (0x00, 0x00, 0xFF),  # stage 1: blue
    (0xFF, 0xFF, 0x00),  # stage 2: yellow
    (0x00, 0xFF, 0x00),  # stage 3: green
]

# Linux ioctl helpers for hidraw.
# Kept local so the application does not need pyudev.
_IOC_NRBITS = 8
_IOC_TYPEBITS = 8
_IOC_SIZEBITS = 14
_IOC_DIRBITS = 2
_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
_IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
_IOC_DIRSHIFT = _IOC_SIZESHIFT + _IOC_SIZEBITS
_IOC_READ = 2


def _IOC(direction: int, type_: int, nr: int, size: int) -> int:
    return ((direction << _IOC_DIRSHIFT) |
            (type_ << _IOC_TYPESHIFT) |
            (nr << _IOC_NRSHIFT) |
            (size << _IOC_SIZESHIFT))


def _IOR(type_: int, nr: int, size: int) -> int:
    return _IOC(_IOC_READ, type_, nr, size)


HIDIOCGRAWINFO = _IOR(ord('H'), 0x03, struct.calcsize('IHH'))


def HIDIOCGRAWNAME(length: int) -> int:
    return _IOR(ord('H'), 0x04, length)


@dataclasses.dataclass(frozen=True)
class HidDevice:
    path: str
    bus: int
    vid: int
    pid: int
    name: str
    descriptor: bytes
    role: str
    mode: str

    @property
    def label(self) -> str:
        return f"{self.mode} {self.role}: {self.path} ({self.vid:04x}:{self.pid:04x})"


@dataclasses.dataclass(frozen=True)
class BatteryStatus:
    """Decoded HyperX Pulsefire Saga Pro battery/status response.

    Query:
        host -> mouse: 50 02 00 00 ...

    Response:
        mouse -> host: 51 02 PP SS TT 00 VV VV ...

    Confirmed fields:
        PP    battery percentage, 0-100
        SS    power/charge state
              0x00 = on battery
              0x01 = USB power present / charging
              0x02 = full / 100% / charge complete
        TT    temperature in degrees Celsius
        VV VV battery or charger voltage in millivolts, little endian
    """
    percent: int | None
    raw: bytes
    state_candidate: int | None = None
    field4_le: int | None = None
    voltage_mv_candidate: int | None = None

    @property
    def temperature_c(self) -> int | None:
        return self.field4_le

    @property
    def voltage_mv(self) -> int | None:
        return self.voltage_mv_candidate

    @property
    def charging_candidate(self) -> bool | None:
        if self.state_candidate is None:
            return None
        if self.state_candidate == 0x00:
            return False
        if self.state_candidate in (0x01, 0x02):
            return True
        return None

    @property
    def charging_text(self) -> str:
        if self.state_candidate is None:
            return 'Unknown'
        if self.state_candidate == 0x00:
            return 'On battery'
        if self.state_candidate == 0x01:
            return 'USB power / charging'
        if self.state_candidate == 0x02:
            return 'Full / 100% / charge complete'
        return f'Unknown power state 0x{self.state_candidate:02x}'

    def raw_hex(self, limit: int = 16) -> str:
        return ' '.join(f'{b:02x}' for b in self.raw[:limit])


def _sysfs_device_path(path: str) -> Path:
    return Path('/sys/class/hidraw') / os.path.basename(path) / 'device'


def _read_uevent(path: str) -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        data = (_sysfs_device_path(path) / 'uevent').read_text(errors='replace')
    except OSError:
        return out
    for line in data.splitlines():
        if '=' in line:
            k, v = line.split('=', 1)
            out[k] = v
    return out


def _read_raw_info_from_sysfs(path: str) -> tuple[int, int, int]:
    # Example HID_ID: 0003:000003F0:000006BF
    u = _read_uevent(path)
    hid_id = u.get('HID_ID', '')
    parts = hid_id.split(':')
    if len(parts) == 3:
        return int(parts[0], 16), int(parts[1], 16), int(parts[2], 16)
    raise OSError(f'cannot read HID_ID for {path}')


def _read_raw_info(path: str) -> tuple[int, int, int]:
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    except PermissionError:
        # Still allow detection; actual writes will show a permission error later.
        return _read_raw_info_from_sysfs(path)
    try:
        buf = array.array('B', [0] * struct.calcsize('IHH'))
        fcntl.ioctl(fd, HIDIOCGRAWINFO, buf, True)
        bus, vid, pid = struct.unpack('IHH', buf.tobytes())
        return bus, vid, pid
    finally:
        os.close(fd)


def _read_raw_name(path: str) -> str:
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    except PermissionError:
        return _read_uevent(path).get('HID_NAME', '')
    try:
        length = 256
        buf = array.array('B', [0] * length)
        fcntl.ioctl(fd, HIDIOCGRAWNAME(length), buf, True)
        raw = buf.tobytes().split(b'\0', 1)[0]
        return raw.decode('utf-8', 'replace')
    except OSError:
        return _read_uevent(path).get('HID_NAME', '')
    finally:
        os.close(fd)


def _read_descriptor(path: str) -> bytes:
    candidates = [
        _sysfs_device_path(path) / 'report_descriptor',
        Path('/sys') / 'class' / 'hidraw' / os.path.basename(path) / 'device' / 'report_descriptor',
    ]
    for p in candidates:
        try:
            return p.read_bytes()
        except OSError:
            continue
    return b''


def _resolved_sysfs_path(path: str) -> str:
    try:
        return str(_sysfs_device_path(path).resolve())
    except OSError:
        return ''


def _classify_role(desc: bytes, pid: int | None = None, sysfs_path: str = '') -> str:
    # The native Saga config endpoints expose report IDs used by NGENUITY/profile writes.
    native_markers = [b'\x85\x32', b'\x85\x44', b'\x85\x50', b'\x85\x36']
    if any(m in desc for m in native_markers):
        return 'config'

    # Robust fallback by USB interface number.  Observed layouts:
    #   wired 03f0:04bf    interface 1.2 = native config (/dev/hidraw2 usually)
    #   wireless 03f0:06bf interface 1.3 = native config (/dev/hidraw3 usually)
    if pid == PID_WIRED and ':1.2/' in sysfs_path + '/':
        return 'config'
    if pid == PID_WIRELESS and ':1.3/' in sysfs_path + '/':
        return 'config'

    # HID LampArray page 0x59.  This is the live RGB interface.
    if b'\x05\x59' in desc or b'\x06\x59\x00' in desc:
        return 'lamparray'
    # Mouse movement endpoints usually include Generic Desktop Mouse.
    if b'\x05\x01\x09\x02' in desc:
        return 'movement'
    return 'other'


def scan_devices() -> list[HidDevice]:
    out: list[HidDevice] = []
    for path in sorted(glob.glob('/dev/hidraw*')):
        try:
            bus, vid, pid = _read_raw_info(path)
        except OSError:
            continue
        if vid != VID_HP or pid not in KNOWN_PIDS:
            continue
        desc = _read_descriptor(path)
        sysfs_path = _resolved_sysfs_path(path)
        role = _classify_role(desc, pid=pid, sysfs_path=sysfs_path)
        mode = 'wireless' if pid == PID_WIRELESS else 'wired'
        name = _read_raw_name(path) or 'HyperX Pulsefire Saga Pro'
        out.append(HidDevice(path=path, bus=bus, vid=vid, pid=pid, name=name, descriptor=desc, role=role, mode=mode))
    return out



def device_from_path(path: str, force_role: str | None = None) -> HidDevice:
    """Build a HidDevice object for a specific /dev/hidraw path.

    This is used for manual overrides when auto-detection fails but the user
    already knows the correct Saga Pro config endpoint, for example
    HYPERX_SAGA_CONFIG_DEV=/dev/hidraw3.
    """
    bus, vid, pid = _read_raw_info(path)
    if vid != VID_HP or pid not in KNOWN_PIDS:
        raise OSError(f'{path} is not a supported HyperX Saga Pro device: {vid:04x}:{pid:04x}')
    desc = _read_descriptor(path)
    sysfs_path = _resolved_sysfs_path(path)
    role = force_role or _classify_role(desc, pid=pid, sysfs_path=sysfs_path)
    mode = 'wireless' if pid == PID_WIRELESS else 'wired'
    name = _read_raw_name(path) or 'HyperX Pulsefire Saga Pro'
    return HidDevice(path=path, bus=bus, vid=vid, pid=pid, name=name, descriptor=desc, role=role, mode=mode)

def find_config_device(prefer_wireless: bool = True) -> Optional[HidDevice]:
    devices = scan_devices()
    configs = [d for d in devices if d.role == 'config']
    if not configs:
        return None
    if prefer_wireless:
        wireless = [d for d in configs if d.pid == PID_WIRELESS]
        if wireless:
            return sorted(wireless, key=lambda d: d.path)[-1]
    return sorted(configs, key=lambda d: d.path)[-1]


def report(prefix: Iterable[int]) -> bytes:
    p = list(prefix)
    if len(p) > 64:
        raise ValueError('HID report prefix longer than 64 bytes')
    return bytes(p + [0] * (64 - len(p)))


def parse_hex_color(color: str) -> tuple[int, int, int]:
    raw = color.strip()
    if raw.startswith('#'):
        raw = raw[1:]
    if len(raw) != 6:
        raise ValueError('color must be #rrggbb')
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def normalize_color(r: int, g: int, b: int) -> str:
    return f'#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}'


def percent_to_intensity(percent: int) -> int:
    pct = max(0, min(100, int(percent)))
    return round(pct * 255 / 100)


def dpi_to_code(dpi: int) -> int:
    if dpi < 50 or dpi > 26000 or dpi % 50 != 0:
        raise ValueError(f'DPI must be 50..26000 and divisible by 50, got {dpi}')
    return dpi // 50 - 1


def code_to_dpi(code: int) -> int:
    return (code + 1) * 50


def polling_rate_to_code(rate_hz: int) -> int:
    try:
        return POLLING_RATE_TO_CODE[int(rate_hz)]
    except KeyError as exc:
        supported = ', '.join(str(x) for x in sorted(POLLING_RATE_TO_CODE))
        raise ValueError(f'supported polling rates are: {supported} Hz') from exc


def polling_code_to_rate(code: int) -> int | None:
    return POLLING_CODE_TO_RATE.get(int(code))


class SagaDevice:
    def __init__(self, hidraw: str):
        self.hidraw = hidraw

    def _open(self) -> int:
        return os.open(self.hidraw, os.O_RDWR | os.O_NONBLOCK)

    @staticmethod
    def _drain(fd: int) -> None:
        while True:
            r, _, _ = select.select([fd], [], [], 0)
            if not r:
                return
            try:
                os.read(fd, 4096)
            except (BlockingIOError, OSError):
                return

    @staticmethod
    def _read_reports(fd: int, seconds: float = 0.5) -> list[bytes]:
        end = time.monotonic() + seconds
        reports: list[bytes] = []
        while time.monotonic() < end:
            timeout = min(0.1, max(0.0, end - time.monotonic()))
            r, _, _ = select.select([fd], [], [], timeout)
            if not r:
                continue
            try:
                data = os.read(fd, 4096)
            except BlockingIOError:
                continue
            if not data:
                continue
            if len(data) > 64 and len(data) % 64 == 0:
                reports.extend(data[i:i + 64] for i in range(0, len(data), 64))
            else:
                reports.append(data)
        return reports

    def write_reports(self, packets: list[bytes], delay: float = 0.04, read_after: float = 0.08) -> list[bytes]:
        fd = self._open()
        responses: list[bytes] = []
        try:
            self._drain(fd)
            for pkt in packets:
                os.write(fd, pkt)
                time.sleep(delay)
                responses.extend(self._read_reports(fd, read_after))
            return responses
        finally:
            os.close(fd)

    def battery_status(self, seconds: float = 1.0) -> tuple[Optional[BatteryStatus], list[bytes]]:
        # Confirmed Saga query: 50 02 -> 51 02 <battery percent> ...
        fd = self._open()
        try:
            self._drain(fd)
            os.write(fd, report([0x50, 0x02]))
            responses = self._read_reports(fd, seconds)
        finally:
            os.close(fd)
        for rep in responses:
            if len(rep) >= 3 and rep[0] == 0x51 and rep[1] == 0x02:
                percent = int(rep[2]) if rep[2] <= 100 else None
                state = int(rep[3]) if len(rep) > 3 else None
                field4 = int.from_bytes(rep[4:6], 'little') if len(rep) >= 6 else None
                voltage = int.from_bytes(rep[6:8], 'little') if len(rep) >= 8 else None
                return BatteryStatus(
                    percent=percent,
                    raw=bytes(rep),
                    state_candidate=state,
                    field4_le=field4,
                    voltage_mv_candidate=voltage,
                ), responses
        return None, responses

    def battery_percent(self, seconds: float = 1.0) -> tuple[Optional[int], list[bytes]]:
        status, responses = self.battery_status(seconds=seconds)
        return (status.percent if status else None), responses

    def set_live_rgb(self, color: str, brightness_percent: int) -> list[bytes]:
        r, g, b = parse_hex_color(color)
        intensity = percent_to_intensity(brightness_percent)
        packets = [
            report([0x44, 0x01, 0x01, 0x00]),
            report([0x44, 0x02, 0x00, 0x00, r, g, b]),
            report([0x40, 0x01, 0x00, 0x00, intensity]),
        ]
        return self.write_reports(packets)

    def save_rgb_profile(self, color: str, brightness_percent: int) -> list[bytes]:
        # Confirmed by user: this rgb-only sequence persists across power cycles.
        r, g, b = parse_hex_color(color)
        intensity = percent_to_intensity(brightness_percent)
        packets = [
            report([0x44, 0x01, 0x01, 0x00]),
            report([0x44, 0x02, 0x00, 0x00, r, g, b]),
            report([0x40, 0x01, 0x00, 0x00, intensity]),
            report([0x44, 0x03, 0x01, 0x01, 0x00, 0x01]),
            report([0x44, 0x04, 0x00, 0x00, r, g, b]),
            report([0x40, 0x01, 0x01, 0x00, intensity]),
            report([0x50, 0x01, 0x14, 0x01]),
            report([0x36, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02]),
        ]
        return self.write_reports(packets)

    @staticmethod
    def build_dpi_packet(dpis: list[int], active_stage: int = 0, colors: Optional[list[tuple[int, int, int]]] = None, polling_hz: int = 1000, profile: bool = True) -> bytes:
        if len(dpis) != 4:
            raise ValueError('DPI table must have exactly four stages')
        if not 0 <= active_stage <= 3:
            raise ValueError('active_stage must be 0..3')
        colors = colors or DEFAULT_DPI_COLORS
        polling_code = polling_rate_to_code(polling_hz)
        # Native Saga Pro 0x32 profile table:
        #   32 01 PP 00 RR 0f AA <4x DPI/color records>
        # PP = 0x00 for immediate/live write, 0x01 for profile write.
        # RR = polling/report-rate interval byte. Confirmed 1000/4000 and
        # generalized using rate_hz = 8000 / interval_code.
        # AA = active DPI stage.
        prefix = [0x32, 0x01, 0x01 if profile else 0x00, 0x00, polling_code, 0x0F, active_stage & 0xFF]
        for dpi, (r, g, b) in zip(dpis, colors):
            code = dpi_to_code(int(dpi))
            prefix += [code & 0xFF, (code >> 8) & 0xFF, r & 0xFF, g & 0xFF, b & 0xFF]
        return report(prefix)

    def save_dpi_profile(self, dpis: list[int], active_stage: int = 0, polling_hz: int = 1000) -> list[bytes]:
        pkt = self.build_dpi_packet(dpis, active_stage=active_stage, polling_hz=polling_hz, profile=True)
        return self.write_reports([pkt], read_after=0.25)

    def save_polling_profile(
        self,
        dpis: list[int],
        active_stage: int = 0,
        polling_hz: int = 1000,
        color: str | None = None,
        brightness_percent: int = 100,
    ) -> list[bytes]:
        # NGENUITY first sends an immediate 0x32 write (profile byte 0x00),
        # then saves the same table with profile byte 0x01. Polling and DPI
        # share this table, so pass current UI DPI stages to preserve them.
        # Observed polling codes inside report 0x32:
        #   1000 Hz -> byte 4 = 0x08
        #   4000 Hz -> byte 4 = 0x02
        # 2000 Hz is derived from the same interval-code formula and
        # treated as wireless-only for the Saga Pro. Other standard rates
        # are derived from rate_hz = 8000 / code.
        live = self.build_dpi_packet(dpis, active_stage=active_stage, polling_hz=polling_hz, profile=False)
        profile_pkt = self.build_dpi_packet(dpis, active_stage=active_stage, polling_hz=polling_hz, profile=True)
        packets = [live]
        if color is not None:
            r, g, b = parse_hex_color(color)
            intensity = percent_to_intensity(brightness_percent)
            packets += [
                report([0x44, 0x03, 0x01, 0x01, 0x00, 0x01]),
                report([0x44, 0x04, 0x00, 0x00, r, g, b]),
                report([0x42, 0x02, 0x01, 0x00, 0x06, 0x32]),
                report([0x40, 0x01, 0x01, 0x00, intensity]),
            ]
        else:
            packets += [report([0x42, 0x02, 0x01, 0x00, 0x06, 0x32])]
        packets += [
            profile_pkt,
            report([0x20, 0x05, 0x01, 0x00, 0x01]),
            report([0x22, 0x07, 0x01, 0x00, 0x01]),
            report([0x50, 0x01, 0x14, 0x01]),
            report([0x36, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02]),
        ]
        return self.write_reports(packets, read_after=0.25)


def format_report(rep: bytes, limit: int = 16) -> str:
    return ' '.join(f'{b:02x}' for b in rep[:limit])
