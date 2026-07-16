#!/usr/bin/env python3
"""
HyperX Pulsefire Saga Pro - NGENUITY feature capture helper

Records one USBPcap PCAP per NGENUITY action so protocol changes can be
diffed safely. Run from Windows PowerShell as Administrator.

This script does not send data to the mouse. It only starts/stops USBPcapCMD.
"""
from __future__ import annotations

import argparse
import csv
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
import zipfile


@dataclass(frozen=True)
class Step:
    step_id: str
    name: str
    filename: str
    instructions: str
    optional: bool = False
    group: str = "general"


STEPS: list[Step] = [
    Step("00", "enumeration_before_ngenuity", "00_enumeration_before_ngenuity.pcap", """Enumeration capture.\n\n1. Make sure NGENUITY is closed.\n2. Start this capture.\n3. Unplug/replug the mouse cable or 2.4 GHz dongle.\n4. Wait 10 seconds.\n5. Press Enter here to stop capture.\n\nThis captures descriptors and confirms the USBPcap hub/device ID.""", optional=True),
    Step("01", "ngenuity_startup_idle", "01_ngenuity_startup_idle.pcap", """Startup/idle capture.\n\n1. Start this capture.\n2. Open HyperX NGENUITY.\n3. Wait until it detects the mouse.\n4. Do not change settings.\n5. Wait 10 seconds.\n6. Press Enter here to stop capture.""", optional=True),

    Step("L10", "lighting_solid_static_ff00aa", "L10_lighting_solid_static_ff00aa.pcap", """Lighting: solid/static colour.\n\n1. Start this capture.\n2. In NGENUITY, set lighting mode to Solid/Static.\n3. Set colour to #ff00aa.\n4. Apply/save if NGENUITY requires it.\n5. Wait until it finishes.\n6. Press Enter here to stop capture.""", group="lighting"),
    Step("L11", "lighting_solid_static_00aaff", "L11_lighting_solid_static_00aaff.pcap", """Lighting: solid/static colour comparison.\n\nSet lighting mode to Solid/Static and colour to #00aaff. Capture only that action.""", group="lighting"),
    Step("L20", "lighting_breathing_ff00aa", "L20_lighting_breathing_ff00aa.pcap", """Lighting: breathing mode.\n\nSet lighting mode to Breathing/Pulse with colour #ff00aa. Capture only that one action.""", group="lighting"),
    Step("L21", "lighting_breathing_00aaff", "L21_lighting_breathing_00aaff.pcap", """Lighting: breathing colour comparison.\n\nKeep Breathing/Pulse mode, change colour to #00aaff, and capture only that one action.""", optional=True, group="lighting"),
    Step("L30", "lighting_cycle_rainbow", "L30_lighting_cycle_rainbow.pcap", """Lighting: cycle/rainbow mode.\n\nSet lighting mode to Cycle/Rainbow/Colour Cycle. Capture only that one action.""", group="lighting"),
    Step("L40", "lighting_speed_slow", "L40_lighting_speed_slow.pcap", """Lighting speed: slow.\n\nWith a mode that supports speed, set speed to Slow. Capture only that action.""", optional=True, group="lighting"),
    Step("L41", "lighting_speed_fast", "L41_lighting_speed_fast.pcap", """Lighting speed: fast.\n\nWith the same mode, set speed to Fast. Capture only that action.""", optional=True, group="lighting"),
    Step("L50", "lighting_brightness_100", "L50_lighting_brightness_100.pcap", """Lighting brightness: 100%.\n\nSet RGB brightness to 100%. Capture only that action.""", optional=True, group="lighting"),
    Step("L51", "lighting_brightness_050", "L51_lighting_brightness_050.pcap", """Lighting brightness: 50%.\n\nSet RGB brightness to 50%. Capture only that action.""", optional=True, group="lighting"),
    Step("L90", "lighting_explicit_save_to_device", "L90_lighting_explicit_save_to_device.pcap", """Lighting explicit save/apply-to-device.\n\nDo not change mode/colour here. Only click NGENUITY's save/apply/sync-to-device action. Capture only that action.""", group="lighting"),

    Step("B10", "button_side_back_to_keyboard_a", "B10_button_side_back_to_keyboard_a.pcap", """Button remap: side back -> keyboard A.\n\n1. Start capture.\n2. In NGENUITY, remap the side-back button to keyboard key A.\n3. Apply/save if required.\n4. Stop capture.""", group="buttons"),
    Step("B11", "button_side_forward_to_keyboard_b", "B11_button_side_forward_to_keyboard_b.pcap", """Button remap: side forward -> keyboard B.\n\nCapture only this assignment.""", group="buttons"),
    Step("B20", "button_dpi_cycle_disabled", "B20_button_dpi_cycle_disabled.pcap", """Button remap: DPI cycle -> disabled/no action, if NGENUITY offers it.\n\nCapture only this assignment.""", optional=True, group="buttons"),
    Step("B90", "button_restore_defaults", "B90_button_restore_defaults.pcap", """Button remap: restore defaults.\n\nRestore button mappings to defaults. Capture only that action.""", group="buttons"),
    Step("B91", "button_explicit_save_to_device", "B91_button_explicit_save_to_device.pcap", """Button explicit save/apply-to-device.\n\nDo not change mappings here. Only click save/apply/sync-to-device. Capture only that action.""", group="buttons"),

    Step("M10", "macro_create_a_b_50ms", "M10_macro_create_a_b_50ms.pcap", """Macro: create a simple known macro.\n\nCreate a macro that sends A then B with a known delay around 50 ms. Capture only macro creation/save in NGENUITY, not assignment.""", group="macros"),
    Step("M20", "macro_assign_to_side_back", "M20_macro_assign_to_side_back.pcap", """Macro assignment: assign the previously created A,B macro to side-back button.\n\nCapture only the assignment.""", group="macros"),
    Step("M30", "macro_remove_from_side_back", "M30_macro_remove_from_side_back.pcap", """Macro removal: remove macro from side-back button or restore that button to default.\n\nCapture only that action.""", group="macros"),
    Step("M90", "macro_explicit_save_to_device", "M90_macro_explicit_save_to_device.pcap", """Macro explicit save/apply-to-device.\n\nDo not edit macros here. Only click save/apply/sync-to-device. Capture only that action.""", group="macros"),
]


def windows_desktop() -> Path:
    return Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"


def default_output_root(mode: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return windows_desktop() / "SagaPro-NGENUITY-Captures" / f"saga-pro-{mode}-features-{stamp}"


def find_usbpcapcmd() -> Path | None:
    candidates = [
        Path(r"C:\Program Files\USBPcap\USBPcapCMD.exe"),
        Path(r"C:\Program Files\Wireshark\extcap\USBPcapCMD.exe"),
        Path(r"C:\Program Files\Wireshark\extcap\wireshark\USBPcapCMD.exe"),
        Path(r"C:\Program Files (x86)\USBPcap\USBPcapCMD.exe"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def parse_list(value: str | None) -> set[str] | None:
    if not value:
        return None
    out: set[str] = set()
    for part in value.replace(";", ",").split(","):
        part = part.strip()
        if part:
            out.add(part)
    return out


def select_steps(only: set[str] | None, groups: set[str] | None, skip_optional: bool) -> list[Step]:
    selected: list[Step] = []
    for s in STEPS:
        if only is not None and s.step_id not in only and s.name not in only:
            continue
        if groups is not None and s.group not in groups and s.step_id not in ("00", "01"):
            continue
        if skip_optional and s.optional and only is None:
            continue
        selected.append(s)
    return selected


def stop_process(proc: subprocess.Popen, log) -> None:
    if proc.poll() is not None:
        return
    try:
        if os.name == "nt":
            proc.send_signal(signal.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
        else:
            proc.send_signal(signal.SIGINT)
        proc.wait(timeout=10)
        return
    except Exception as e:
        print(f"Graceful stop failed: {e}", file=log)
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception as e:
        print(f"Terminate failed: {e}; killing", file=log)
        try:
            proc.kill()
            proc.wait(timeout=5)
        except Exception:
            pass


def capture_step(usbpcapcmd: Path, usbpcap: str, output_dir: Path, step: Step, manifest_writer: csv.writer) -> None:
    output_pcap = output_dir / step.filename
    output_log = output_dir / f"{Path(step.filename).stem}.log.txt"

    print("\n" + "=" * 78)
    print(f"Step {step.step_id}: {step.name}")
    print("=" * 78)
    print(step.instructions)
    print()
    print(f"USBPcap: {usbpcap}")
    print(f"Output:  {output_pcap}")
    print()
    input("Press Enter to START this capture...")

    cmd = [str(usbpcapcmd), "-d", usbpcap, "-A", "-o", str(output_pcap)]
    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    start = datetime.now()
    with output_log.open("w", encoding="utf-8", newline="") as log:
        print(f"Command: {cmd}", file=log)
        print(f"Started: {start.isoformat(timespec='seconds')}", file=log)
        log.flush()
        proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, creationflags=creationflags)
        time.sleep(1.0)
        if proc.poll() is not None:
            print(f"USBPcapCMD exited early with code {proc.returncode}", file=log)
            print("USBPcapCMD exited early. See log file:", output_log)
        else:
            print("\nCapture is running now.")
            print("Perform ONLY the action described above in NGENUITY.")
            input("When done, return here and press Enter to STOP this capture...")
            stop_process(proc, log)
        end = datetime.now()
        print(f"Stopped: {end.isoformat(timespec='seconds')}", file=log)

    size = output_pcap.stat().st_size if output_pcap.exists() else 0
    status = "ok" if size > 4096 else "small_or_missing"
    manifest_writer.writerow([step.step_id, step.group, step.name, str(output_pcap), str(output_log), start.isoformat(timespec="seconds"), datetime.now().isoformat(timespec="seconds"), size, status])
    print(f"Capture file size: {size} bytes ({status})")
    if size <= 4096:
        print("WARNING: Capture file is missing or very small. Check USBPcap root hub and try again.")


def zip_output(output_dir: Path) -> Path:
    zip_path = output_dir.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in output_dir.rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(output_dir.parent))
    return zip_path


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture HyperX Pulsefire Saga Pro NGENUITY feature changes with USBPcap.")
    parser.add_argument("--mode", choices=["wired", "wireless"], default="wireless", help="Capture mode. Used for folder names and instructions only.")
    parser.add_argument("--usbpcap", help=r'USBPcap root hub, e.g. "\\.\USBPcap2"')
    parser.add_argument("--usbpcap-cmd", help="Path to USBPcapCMD.exe")
    parser.add_argument("--output-dir", help="Output directory. Defaults to Desktop\\SagaPro-NGENUITY-Captures\\...")
    parser.add_argument("--only", help="Comma-separated step IDs or names, e.g. L10,L20,L30,L90")
    parser.add_argument("--groups", help="Comma-separated groups: lighting,buttons,macros,general")
    parser.add_argument("--skip-optional", action="store_true", help="Skip optional steps unless --only includes them")
    parser.add_argument("--zip", action="store_true", help="Create a zip of the capture folder at the end")
    parser.add_argument("--list-steps", action="store_true", help="List available capture steps and exit")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.list_steps:
        for s in STEPS:
            opt = " optional" if s.optional else ""
            print(f"{s.step_id}: {s.group}: {s.name}{opt}")
        return 0

    usbpcapcmd = Path(args.usbpcap_cmd) if args.usbpcap_cmd else find_usbpcapcmd()
    if not usbpcapcmd or not usbpcapcmd.exists():
        print("Could not find USBPcapCMD.exe.")
        print(r"Try: --usbpcap-cmd 'C:\Program Files\USBPcap\USBPcapCMD.exe'")
        return 2

    usbpcap = args.usbpcap
    if not usbpcap:
        target = "03F0:06BF wireless dongle" if args.mode == "wireless" else "03F0:04BF wired mouse"
        print(f"Enter the USBPcap root hub that contains the {target}.")
        print(r"Example: \\.\USBPcap2")
        usbpcap = input("USBPcap device: ").strip()
    if not usbpcap:
        print("No USBPcap device provided.")
        return 2

    output_dir = Path(args.output_dir) if args.output_dir else default_output_root(args.mode)
    output_dir.mkdir(parents=True, exist_ok=True)

    selected = select_steps(parse_list(args.only), parse_list(args.groups), args.skip_optional)
    if not selected:
        print("No steps selected.")
        return 2

    readme_path = output_dir / "README_CAPTURE_SESSION.txt"
    readme_path.write_text(
        "HyperX Pulsefire Saga Pro feature capture session\n"
        f"Created: {datetime.now().isoformat(timespec='seconds')}\n"
        f"Mode: {args.mode}\n"
        f"USBPcap: {usbpcap}\n"
        "Rule: one NGENUITY action per PCAP. Upload the whole folder when finished.\n",
        encoding="utf-8",
    )

    manifest_path = output_dir / "manifest.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["step_id", "group", "name", "pcap", "log", "started", "stopped", "pcap_bytes", "status"])
        print("Output directory:", output_dir)
        print("Manifest:", manifest_path)
        print("USBPcapCMD:", usbpcapcmd)
        print("USBPcap:", usbpcap)
        print()
        if args.mode == "wireless":
            print("Before continuing: use 2.4 GHz wireless mode and target VID:PID 03F0:06BF.")
        else:
            print("Before continuing: use wired USB mode and target VID:PID 03F0:04BF.")
        print("Open NGENUITY only when a step asks you to, and change exactly one setting per capture.")
        input("Press Enter when ready...")
        for step in selected:
            capture_step(usbpcapcmd, usbpcap, output_dir, step, writer)
            f.flush()

    print("\nDone.")
    print("Output directory:", output_dir)
    if args.zip:
        zp = zip_output(output_dir)
        print("Created zip:", zp)
    print("Upload the whole output folder/zip plus manifest.csv.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
