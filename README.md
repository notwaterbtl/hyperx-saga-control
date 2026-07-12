# SagaCtrl

> Native Linux control software for the **HyperX Pulsefire Saga Pro** (Wired + 2.4 GHz Wireless)

SagaCtrl is an open-source Linux application that provides native configuration for the HyperX Pulsefire Saga Pro without requiring HyperX NGENUITY or Windows.

This project was created through protocol analysis, HID inspection, and interoperability research to improve Linux compatibility for the Pulsefire Saga Pro.

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

# Why this project exists

HyperX NGENUITY is currently only available for Windows.

Linux users can use the mouse as a standard HID device, but many of the premium features—including RGB configuration, DPI editing, profile management, and battery reporting—are not officially available.

The goal of this project is to provide a native Linux implementation that allows users to fully configure their own hardware without requiring Windows.

---

# Current Status

| Feature                        | Status |
| ------------------------------ | ------ |
| Battery percentage             | ✅      |
| Live RGB                       | ✅      |
| RGB Brightness                 | ✅      |
| RGB saved to onboard memory    | ✅      |
| DPI editing                    | ✅      |
| DPI profile persistence        | ✅      |
| Wired mode                     | ✅      |
| Wireless mode                  | ✅      |
| Local profiles                 | ✅      |
| Wireless polling configuration | 🚧     |

---

# Supported Device

Currently supported:

```
HyperX Pulsefire Saga Pro

USB:
VID 03F0
PID 04BF

Wireless:
VID 03F0
PID 06BF
```

Support for additional HyperX devices may be added in the future.

---

# Installation

## Fedora / Bazzite

Clone the repository:

```bash
git clone https://github.com/notwaterbtl/hyperx-saga-control.git

cd hyperx-saga-control
```

Create a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -U pip
pip install PySide6
```

Install the udev rule:

```bash
sudo cp share/udev/rules.d/99-hyperx-saga-pro.rules \
    /etc/udev/rules.d/

sudo udevadm control --reload-rules
sudo udevadm trigger
```

Reconnect the mouse (or wireless dongle).

Run:

```bash
PYTHONPATH="$PWD" python -m hyperx_saga_control
```

---

# How it works

SagaCtrl communicates directly with the mouse using the Linux HID subsystem (`hidraw`).

No kernel driver is required.

The project automatically detects the correct configuration interface for both wired and wireless operation and communicates using the native vendor protocol discovered through protocol analysis.

---

# Reverse Engineering

This project was developed by observing and comparing USB HID traffic while configuring the mouse with HyperX NGENUITY.

Research included:

* HID descriptor analysis
* Linux `hidraw` packet inspection
* USBPcap captures
* Wireshark analysis
* Packet comparison
* Behaviour verification on Linux

The implementation is based on observed device behaviour and publicly documented HID interfaces.

---

# Disclaimer

This project is an independent community project.

It is **not affiliated with, endorsed by, sponsored by, or supported by HyperX or HP Inc.**

All trademarks are the property of their respective owners.

This software was created for the purposes of:

* improving Linux hardware compatibility
* interoperability
* education
* personal experimentation
* open-source research

This repository does **not** contain HyperX source code, proprietary firmware, or Windows software.

---

# Contributing

Bug reports, pull requests, protocol analysis, and testing are all welcome.

If you own a HyperX device that is not yet supported, USB captures and protocol documentation are greatly appreciated.

---

# License

MIT License

See the LICENSE file for details.

---

# Acknowledgements

Special thanks to:

* The Linux HID maintainers
* Wireshark
* USBPcap
* The OpenRGB project
* libratbag / Piper
* Everyone contributing to Linux hardware compatibility

---

# Project Goals

This project aims to provide Linux users with first-class support for HyperX peripherals while remaining open, transparent, and easy to understand.

The long-term goal is to create a reliable, native Linux configuration utility for HyperX devices that anyone can inspect, improve, and learn from.

If this project saves you from booting Windows just to change your mouse settings, then it has achieved its goal.
