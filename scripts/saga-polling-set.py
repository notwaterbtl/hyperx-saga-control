#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from repository checkout without installation.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hyperx_saga_control.protocol import SagaDevice, device_from_path


def main() -> int:
    ap = argparse.ArgumentParser(
        description='Set HyperX Pulsefire Saga Pro polling rate using the native 0x32 table. 2000/4000 Hz are wireless-only.'
    )
    ap.add_argument('hidraw', help='native config node, usually /dev/hidraw3 wireless or /dev/hidraw2 wired')
    ap.add_argument('--rate', type=int, choices=[125, 250, 500, 1000, 2000, 4000], required=True, help='polling/report rate')
    ap.add_argument('--dpi', type=int, nargs=4, default=[400, 800, 1600, 3200], metavar=('DPI0','DPI1','DPI2','DPI3'), help='DPI stages to preserve/write')
    ap.add_argument('--active-stage', type=int, default=0, choices=[0,1,2,3])
    ap.add_argument('--force', action='store_true', help='allow wireless-only rates on a wired node for protocol testing; not recommended')
    ap.add_argument('--send', action='store_true', help='actually write to the mouse')
    args = ap.parse_args()

    try:
        info = device_from_path(args.hidraw)
    except Exception:
        info = None

    if args.rate > 1000 and info is not None and info.mode != 'wireless' and not args.force:
        print(
            'Refusing: 2000 Hz and 4000 Hz are wireless-only on the Saga Pro. '
            'Use the 2.4 GHz config node, usually /dev/hidraw3, or add --force to override for testing.',
            file=sys.stderr,
        )
        return 2

    dev = SagaDevice(args.hidraw)
    pkt = dev.build_dpi_packet(args.dpi, active_stage=args.active_stage, polling_hz=args.rate, profile=True)
    if info is not None:
        print(f'Device mode: {info.mode} ({info.vid:04x}:{info.pid:04x})')
    else:
        print('Device mode: unknown')
    print(f'Polling rate: {args.rate} Hz')
    print(f'DPI table: {args.dpi}, active_stage={args.active_stage}')
    print('Profile 0x32 packet:')
    print(pkt.hex(' '))
    if not args.send:
        print('\nDry run only. Add --send to write the immediate/profile polling sequence.')
        return 0
    responses = dev.save_polling_profile(dpis=args.dpi, active_stage=args.active_stage, polling_hz=args.rate)
    print(f'Wrote polling profile. Responses={len(responses)}')
    for i, rep in enumerate(responses, 1):
        print(f'response {i}: {rep.hex(" ")}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
