# Security and Safety

HyperX Saga Control talks directly to `/dev/hidraw*` devices and can write settings to mouse onboard memory.

The udev rule is intentionally limited to the HyperX Pulsefire Saga Pro wired and wireless USB IDs:

- `03f0:04bf`
- `03f0:06bf`

The project avoids unconfirmed or guessed commands. Wireless polling control is intentionally not implemented until confirmed.

If you discover a command that can brick, corrupt, or otherwise harm the device, please open an issue with clear reproduction details and mark it clearly as safety-sensitive.
