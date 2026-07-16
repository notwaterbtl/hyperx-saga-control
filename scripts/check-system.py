#!/usr/bin/env python3
"""Cross-distro environment checker for HyperX Saga Control."""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

SAGA_IDS = {("03f0", "04bf"): "wired", ("03f0", "06bf"): "wireless"}


def run(cmd: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return p.returncode, p.stdout.strip()
    except FileNotFoundError:
        return 127, "not found"


def ok(flag: bool) -> str:
    return "OK" if flag else "WARN"


def section(name: str) -> None:
    print(f"\n== {name} ==")


def check_python() -> None:
    section("Python")
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    print(f"Python >= 3.10: {ok(sys.version_info >= (3, 10))}")
    try:
        import venv  # noqa: F401
        print("venv module: OK")
    except Exception as exc:  # pragma: no cover
        print(f"venv module: WARN ({exc})")
    try:
        import PySide6  # type: ignore
        print(f"PySide6 import: OK ({getattr(PySide6, '__version__', 'unknown')})")
    except Exception as exc:
        print(f"PySide6 import: WARN ({exc})")


def check_tools() -> None:
    section("Tools")
    for tool in ["udevadm", "lsusb", "setfacl", "kbuildsycoca6", "update-desktop-database"]:
        path = shutil.which(tool)
        print(f"{tool}: {path or 'not found'}")


def udev_props(dev: Path) -> dict[str, str]:
    rc, out = run(["udevadm", "info", "-q", "property", "-n", str(dev)])
    props: dict[str, str] = {}
    if rc != 0:
        return props
    for line in out.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            props[k] = v
    return props


def check_devices() -> None:
    section("Saga Pro hidraw devices")
    hidraws = sorted(Path("/dev").glob("hidraw*"))
    if not hidraws:
        print("No /dev/hidraw* devices found.")
        return
    found = False
    for dev in hidraws:
        props = udev_props(dev)
        vid = props.get("ID_VENDOR_ID", "").lower()
        pid = props.get("ID_MODEL_ID", "").lower()
        if (vid, pid) not in SAGA_IDS:
            continue
        found = True
        mode = SAGA_IDS[(vid, pid)]
        model = props.get("ID_MODEL", "unknown")
        can_rw = os.access(dev, os.R_OK | os.W_OK)
        try:
            stat = dev.stat()
            mode_bits = oct(stat.st_mode & 0o777)
        except OSError:
            mode_bits = "?"
        print(f"{dev}: {mode} {vid}:{pid} {model} perms={mode_bits} current-user-rw={ok(can_rw)}")
        rc, acl = run(["getfacl", "-p", str(dev)])
        if rc == 0:
            interesting = [line for line in acl.splitlines() if line.startswith(("# owner", "# group", "user:", "group:", "other:"))]
            for line in interesting[:8]:
                print(f"  {line}")
    if not found:
        print("No HyperX Pulsefire Saga Pro hidraw nodes found.")
        print("Expected USB IDs: 03f0:04bf wired, 03f0:06bf wireless.")


def check_rule() -> None:
    section("udev rule")
    rule = Path("/etc/udev/rules.d/60-hyperx-saga-pro.rules")
    print(f"{rule}: {'present' if rule.exists() else 'missing'}")
    if rule.exists():
        text = rule.read_text(errors="replace")
        print(f"contains 04bf: {ok('04bf' in text.lower())}")
        print(f"contains 06bf: {ok('06bf' in text.lower())}")


def main() -> int:
    print("HyperX Saga Control system check")
    print(f"Platform: {platform.platform()}")
    check_python()
    check_tools()
    check_rule()
    check_devices()
    print("\nIf device access is WARN, run: ./scripts/install-hidraw-permissions.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
