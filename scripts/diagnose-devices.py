#!/usr/bin/env python3
from hyperx_saga_control.protocol import scan_devices, _resolved_sysfs_path, format_report

print('HyperX Saga Control device scan')
devices = scan_devices()
if not devices:
    print('No 03f0:04bf / 03f0:06bf hidraw devices were detected.')
    print('Check: lsusb | grep -Ei "03f0.*(04bf|06bf)"')
    raise SystemExit(1)
for d in devices:
    print(f'{d.path}: mode={d.mode} role={d.role} vidpid={d.vid:04x}:{d.pid:04x} name={d.name}')
    print(f'  sysfs={_resolved_sysfs_path(d.path)}')
    print(f'  descriptor_len={len(d.descriptor)}')
    print(f'  descriptor_head={format_report(d.descriptor, 32)}')
