#!/usr/bin/env python3
"""Monitor HyperX Pulsefire Saga Pro battery/charging status.

This tool repeatedly sends the confirmed Saga Pro status query:

    50 02

and logs the returned 51 02 report.  Battery percentage is confirmed as byte 2.
Charging state is still under investigation; byte 3 is printed as the main
candidate because current captures suggest:

    51 02 PP 00 ... = on battery / not externally powered candidate
    51 02 PP 01 ... = USB power / charging
    51 02 64 02 ... = full / 100% / charge complete

Run this while changing the power state, then share the CSV/log output.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hyperx_saga_control.protocol import SagaDevice, find_config_device, device_from_path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Monitor Saga Pro battery/charging status.')
    p.add_argument('--device', '-d', help='Explicit /dev/hidraw config node, e.g. /dev/hidraw3')
    p.add_argument('--interval', '-i', type=float, default=2.0, help='Seconds between queries, default: 2.0')
    p.add_argument('--count', '-n', type=int, default=0, help='Number of samples; 0 means until Ctrl+C')
    p.add_argument('--csv', default='', help='Optional CSV output path')
    p.add_argument('--prefer-wired', action='store_true', help='Prefer wired config device when auto-detecting')
    return p.parse_args()


def main() -> int:
    args = parse_args()

    if args.device:
        dev = device_from_path(args.device, force_role='config')
    else:
        dev = find_config_device(prefer_wireless=not args.prefer_wired)
        if dev is None:
            print('No Saga Pro config device found. Plug in the mouse/dongle or pass --device /dev/hidrawX.', file=sys.stderr)
            return 2

    print(f'Using {dev.label}')
    print('Press Ctrl+C to stop.')
    print()
    print('Suggested test sequence:')
    print('  1. wireless dongle only, mouse not plugged into cable')
    print('  2. plug mouse into USB power/charging cable')
    print('  3. unplug charging cable')
    print('  4. optionally repeat in wired USB mode')
    print()

    writer = None
    csv_f = None
    if args.csv:
        csv_f = open(args.csv, 'w', newline='')
        writer = csv.DictWriter(csv_f, fieldnames=[
            'time_iso', 'hidraw', 'mode', 'percent', 'state_hex', 'power_state',
            'temperature_c', 'voltage_mv', 'raw_16', 'raw_64'
        ])
        writer.writeheader()

    saga = SagaDevice(dev.path)
    last_key = None
    sample = 0
    try:
        while args.count <= 0 or sample < args.count:
            sample += 1
            now = time.strftime('%Y-%m-%dT%H:%M:%S%z')
            try:
                status, responses = saga.battery_status(seconds=1.0)
            except PermissionError:
                print(f'{now} ERROR permission denied opening {dev.path}. Check udev/ACL permissions.', file=sys.stderr)
                return 13
            except FileNotFoundError:
                print(f'{now} ERROR {dev.path} disappeared. Re-detect after replugging.', file=sys.stderr)
                return 2

            if status is None:
                print(f'{now} no 51 02 response; responses={len(responses)}')
            else:
                key = (status.percent, status.state_candidate, status.temperature_c, status.voltage_mv)
                changed = ' CHANGED' if last_key is not None and key != last_key else ''
                last_key = key
                charging = status.charging_candidate
                charging_str = 'yes' if charging is True else 'no' if charging is False else 'unknown'
                print(
                    f'{now} pct={status.percent}% state=0x{status.state_candidate:02x} '
                    f'charging_candidate={charging_str} field4={status.field4_le} '
                    f'voltage_candidate={status.voltage_mv_candidate}mV raw={status.raw_hex(16)}{changed}'
                )
                if writer:
                    writer.writerow({
                        'time_iso': now,
                        'hidraw': dev.path,
                        'mode': dev.mode,
                        'percent': status.percent,
                        'state_hex': f'0x{status.state_candidate:02x}' if status.state_candidate is not None else '',
                        'power_state': power_state,
                        'temperature_c': status.temperature_c,
                        'voltage_mv': status.voltage_mv,
                        'raw_16': status.raw_hex(16),
                        'raw_64': status.raw_hex(64),
                    })
                    csv_f.flush()

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print('\nStopped.')
    finally:
        if csv_f:
            csv_f.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
