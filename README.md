# SagaCtrl

> Native Linux control software for the **HyperX Pulsefire Saga Pro** (Wired + 2.4 GHz Wireless)

SagaCtrl is an open-source Linux application that provides native configuration for the HyperX Pulsefire Saga Pro without requiring HyperX NGENUITY or Windows.

This project was created through protocol analysis, HID inspection, and interoperability research to improve Linux compatibility for the Pulsefire Saga Pro.
With help of AI of course, this is a litle time-waster project that actually helped me lol.

---

## Features

### Supported

* Battery percentage
* Native RGB colour control
* RGB brightness control
* RGB profile saving to onboard memory
* Four-stage DPI profile editing
* DPI profile saving
* Local profile management
* Wired USB support
* Wireless (2.4 GHz) support
* KDE Plasma / Fedora / Bazzite compatible
* Background tray application

### Planned

* Wireless polling rate configuration (1000 Hz / 4000 Hz)
* Additional firmware information
* Automatic profile switching
* Improved UI polish
* Packaging for Flatpak

---

# Screenshots

## Main Window

![Main Window](/mainpage.png)

## RGB Profile Editor

![RGB Profile](/rgbprofile.png)

## DPI Profile Editor

![DPI Profile](/dpiprofile.png)

## Profiles

![Profiles](/profiles.png)

## Tray
![Tray](/tray.png)
---

## Project status

| Feature | Status |
| --- | --- |
| Battery percentage | Working |
| Live RGB | Working |
| RGB brightness | Working |
| RGB saved to onboard memory | Working |
| DPI stage editing | Working |
| DPI profile persistence | Working |
| Local app profiles | Working |
| Wired USB mode | Working |
| 2.4 GHz wireless mode | Working |
| KDE tray app | Working |
| Wireless 4 kHz polling switch | Not implemented yet |

Wireless 4 kHz polling is intentionally disabled until the required packet sequence is confirmed.

---

## Supported device

Currently supported:

| Device | Mode | USB ID |
| --- | --- | --- |
| HyperX Pulsefire Saga Pro | Wired USB | `03f0:04bf` |
| HyperX Pulsefire Saga Pro | 2.4 GHz wireless dongle | `03f0:06bf` |

Typical Linux config nodes:

| Mode | Typical config node |
| --- | --- |
| Wired USB | `/dev/hidraw2` |
| Wireless | `/dev/hidraw3` |

The app scans `/dev/hidraw*` automatically, so the exact node number does not have to stay fixed.

---

## Why this project exists

HyperX NGENUITY is Windows-only. Linux can use the mouse for normal pointer input, but Linux users do not get official access to configuration features such as RGB, DPI profiles, battery reporting, and onboard profile management.

This project exists to improve Linux interoperability for hardware that users already own.

---

## Install: Fedora, Bazzite, KDE Plasma

The recommended install uses a Python virtual environment. It does **not** require installing PySide6 globally with `dnf` or `rpm-ostree`.

Clone the repo:

```bash
git clone https://github.com/YOUR_USERNAME/hyperx-saga-control.git
cd hyperx-saga-control
```

Run the installer:

```bash
./install.sh
```

The installer will:

1. copy the app into `~/.local/share/hyperx-saga-control`
2. create a private Python venv
3. install Python dependencies into that venv
4. install a launcher into `~/.local/bin/hyperx-saga-control`
5. install a KDE `.desktop` file
6. install a KDE autostart entry
7. install a udev rule for Saga Pro hidraw access

After install, unplug and replug the mouse cable or 2.4 GHz dongle.

If your user was newly added to the `hyperx` group, log out and back in once.

Launch from the terminal:

```bash
hyperx-saga-control
```

Or search for:

```text
HyperX Saga Control
```

in the KDE application launcher.

---

## Install without autostart

```bash
HYPERX_SAGA_NO_AUTOSTART=1 ./install.sh
```

---

## Run directly from the source tree

For development or testing:

```bash
./run.sh
```

This creates `.venv/` in the project directory and launches the app without installing it.

---

## Permissions / udev

Linux exposes HID configuration endpoints as `/dev/hidraw*` devices. Normal users usually cannot write to them unless a udev rule grants access.

The installer creates a dedicated group:

```text
hyperx
```

and installs:

```text
/etc/udev/rules.d/60-hyperx-saga-pro.rules
```

The rule is limited to the Saga Pro wired and wireless USB IDs:

```text
03f0:04bf
03f0:06bf
```

To manually install or repair permissions:

```bash
./scripts/install-hidraw-permissions.sh
```

To inspect detected devices and permissions:

```bash
./scripts/diagnose-devices.py
./scripts/show-hidraw-permissions.sh
```

If the app detects the mouse but says `Permission denied`, run:

```bash
./scripts/fix-current-permissions.sh
```

Then unplug/replug the mouse or dongle.

---

## Usage

### Status

Shows:

- detected device
- wired/wireless mode
- battery percentage

### RGB Profile

Allows you to:

- choose an RGB colour
- adjust brightness
- apply live RGB
- save RGB and brightness to onboard memory

### DPI Profile

Allows you to configure four DPI stages.

DPI values must be divisible by 50.

Example:

```text
Stage 0: 400
Stage 1: 800
Stage 2: 1600
Stage 3: 3200
```

### Local Profiles

Stores local presets in:

```text
~/.config/hyperx-saga-control/profiles.json
```

Local profiles can include:

- RGB colour
- brightness
- DPI stages
- active stage

---

## Protocol notes

The application uses native Saga Pro HID reports observed from the device.

High-level summary:

| Function | Native report family |
| --- | --- |
| Battery query | `50 02 -> 51 02` |
| DPI table | `0x32` |
| Live RGB | `0x44` |
| Brightness | `0x40` |
| Onboard RGB profile save | `0x44`, `0x40`, `0x50`, `0x36` profile sequence |

DPI uses this observed encoding:

```text
dpi_code = (DPI / 50) - 1
```

Examples:

```text
400 DPI  -> 0x07
800 DPI  -> 0x0f
1600 DPI -> 0x1f
3200 DPI -> 0x3f
```

See [`docs/protocol-notes.md`](docs/protocol-notes.md) for more information.

---

## What this project does not include

This repository does **not** include:

- HyperX source code
- HyperX firmware
- HyperX NGENUITY files
- proprietary Windows software
- raw USB captures by default
- any kernel module

It is a clean-room/community userspace implementation based on observed HID behaviour and interoperability research.

---

## Disclaimer

This is an independent community project.

It is **not affiliated with, endorsed by, sponsored by, or supported by HyperX or HP Inc.**

All product names, trademarks, and registered trademarks belong to their respective owners.

This software is provided for:

- personal use
- educational use
- Linux interoperability
- hardware compatibility research
- open-source experimentation

Use it at your own risk. Some features write settings to onboard mouse memory. The project tries to avoid unknown or unconfirmed commands, but there is always some risk when working with reverse-engineered device protocols.

---

## Contributing

Contributions are welcome.

Useful contributions include:

- testing on other Fedora/Bazzite/KDE systems
- UI improvements
- packaging work
- protocol documentation
- additional HyperX device research
- wireless polling captures for 1000 Hz / 4000 Hz support

Please do not submit proprietary HyperX files or copyrighted NGENUITY assets.

---

## Troubleshooting

### App starts but cannot control the mouse

Run:

```bash
./scripts/show-hidraw-permissions.sh
```

If Saga Pro nodes are owned by `root root` with no user ACL, run:

```bash
./scripts/install-hidraw-permissions.sh
```

Then unplug/replug the mouse or dongle.

### Device is not detected

Check USB IDs:

```bash
lsusb | grep -Ei '03f0.*04bf|03f0.*06bf'
```

Check hidraw devices:

```bash
./scripts/diagnose-devices.py
```

### Force a config device manually

Wireless usually:

```bash
HYPERX_SAGA_CONFIG_DEV=/dev/hidraw3 hyperx-saga-control
```

Wired usually:

```bash
HYPERX_SAGA_CONFIG_DEV=/dev/hidraw2 hyperx-saga-control
```

---

## Uninstall

```bash
./uninstall.sh
```

Remove udev rule too:

```bash
./uninstall.sh --remove-udev
```

---

## License

MIT License. See [`LICENSE`](LICENSE).

---

## Acknowledgements

Thanks to the maintainers and communities around:

- Linux HID
- Wireshark
- USBPcap
- OpenRGB
- libratbag / Piper
- the wider Linux hardware compatibility community

This project exists because Linux users should be able to configure the hardware they own.
