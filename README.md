# SagaCtrl

> Native Linux control software for the **HyperX Pulsefire Saga Pro** (Wired + 2.4 GHz Wireless)

SagaCtrl is an open-source Linux application that provides native configuration for the HyperX Pulsefire Saga Pro without requiring HyperX NGENUITY or Windows.

This project was created through protocol analysis, HID inspection, and interoperability research to improve Linux compatibility for the Pulsefire Saga Pro. With the help of AI of course, this is a little time-waster project that actually helped me lol.

---

## Features

### Supported

* Battery percentage
* Battery power state: on battery, charging / USB power, and full / charge complete
* Battery temperature reporting
* Battery voltage reporting
* Configurable low-battery desktop warnings
* Native RGB colour control
* RGB brightness control
* RGB profile saving to onboard memory
* Four-stage DPI profile editing
* DPI profile saving
* Polling-rate configuration
  * Wired USB: 125 Hz, 250 Hz, 500 Hz, 1000 Hz
  * 2.4 GHz wireless: 125 Hz, 250 Hz, 500 Hz, 1000 Hz, 2000 Hz, 4000 Hz
* Local profile management
* Wired USB support
* Wireless (2.4 GHz) support
* KDE Plasma / Fedora / Bazzite compatible
* Background tray application

### Planned

* RGB lighting effects such as breathing and cycle/rainbow
* Button remapping
* Macro recording / assignment
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

## Polling

![Polling](/polling.png)

---

## Project status

| Feature | Status |
| --- | --- |
| Battery percentage | Working |
| Battery charging / power state | Working |
| Battery temperature | Working |
| Battery voltage | Working |
| Low-battery warnings | Working |
| Live RGB | Working |
| RGB brightness | Working |
| RGB saved to onboard memory | Working |
| DPI stage editing | Working |
| DPI profile persistence | Working |
| Polling-rate control, wired USB | Working |
| Polling-rate control, 2.4 GHz wireless | Working |
| Local app profiles | Working |
| Wired USB mode | Working |
| 2.4 GHz wireless mode | Working |
| KDE tray app | Working |
| RGB effects: breathing / cycle | Planned |
| Button remapping | Planned |
| Macros | Planned |

Polling support currently exposes:

```text
Wired USB:
  125 Hz, 250 Hz, 500 Hz, 1000 Hz

2.4 GHz wireless:
  125 Hz, 250 Hz, 500 Hz, 1000 Hz, 2000 Hz, 4000 Hz
```

2000 Hz and 4000 Hz are treated as wireless-only modes.

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

HyperX NGENUITY is Windows-only. Linux can use the mouse for normal pointer input, but Linux users do not get official access to configuration features such as RGB, DPI profiles, polling rates, battery reporting, charging status, and onboard profile management.

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
- power state: on battery, charging / USB power, or full / charge complete
- battery temperature
- battery voltage
- raw battery/status packet for debugging

The app also includes configurable low-battery notifications. You can choose the warning percentage, repeat interval, and whether warnings should only appear while the mouse is running on battery power.

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

### Polling

Allows you to configure the mouse polling/report rate.

Available wired USB polling options:

```text
125 Hz
250 Hz
500 Hz
1000 Hz
```

Available 2.4 GHz wireless polling options:

```text
125 Hz
250 Hz
500 Hz
1000 Hz
2000 Hz
4000 Hz
```

2000 Hz and 4000 Hz are wireless-only and are hidden or blocked while the mouse is in wired mode.

Polling and DPI share the same native Saga Pro profile table, so the app preserves the DPI values currently shown in the DPI tab when saving a polling-rate change.

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
- polling rate
- low-battery warning settings

---

## Protocol notes

The application uses native Saga Pro HID reports observed from the device.

High-level summary:

| Function | Native report family |
| --- | --- |
| Battery / power / temperature / voltage query | `50 02 -> 51 02` |
| DPI table | `0x32` |
| Polling-rate table | `0x32` |
| Live RGB | `0x44` |
| Brightness | `0x40` |
| Onboard RGB profile save | `0x44`, `0x40`, `0x50`, `0x36` profile sequence |

Battery/status packets decode as:

```text
51 02 PP SS TT 00 VV VV ...
```

Where:

```text
PP       = battery percentage
SS       = power state
TT       = temperature in °C
VV VV    = battery voltage in millivolts, little-endian
```

Observed power-state values:

```text
0x00 = on battery / not charging
0x01 = USB power present / charging
0x02 = full / 100% / charge complete
```

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

Polling uses the native `0x32` profile table as well. The observed/derived polling interval encoding is:

```text
rate_hz = 8000 / interval_code
```

Examples:

```text
4000 Hz -> 0x02  wireless only
2000 Hz -> 0x04  wireless only
1000 Hz -> 0x08
 500 Hz -> 0x10
 250 Hz -> 0x20
 125 Hz -> 0x40
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
- RGB lighting-effect captures for breathing/cycle modes
- button-remapping captures
- macro captures and testing

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
