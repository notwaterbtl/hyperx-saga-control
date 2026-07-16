# Linux installation guide

SagaCtrl / HyperX Saga Control is designed to work on most modern Linux distributions.

The recommended installation method is the built-in **user-local venv installer**:

```bash
./install.sh
```

This avoids distro-specific Python packaging as much as possible. The app is copied to `~/.local/share/hyperx-saga-control`, a private Python virtual environment is created there, and a launcher is installed to `~/.local/bin/hyperx-saga-control`.

## Requirements

Minimum requirements:

- Linux
- Python 3.10 or newer
- Python `venv` support
- `pip`
- `udev`
- access to `/dev/hidraw*`
- a desktop environment that supports XDG `.desktop` launchers/tray icons

The app uses PySide6/Qt for the GUI. The installer installs PySide6 into the private venv with `pip`.

## Quick install

```bash
git clone https://github.com/YOUR_USERNAME/hyperx-saga-control.git
cd hyperx-saga-control
./install.sh
```

Then unplug/replug the mouse or 2.4 GHz dongle.

If the installer adds your user to the `hyperx` group, log out and back in once.

## Install system prerequisites

If your distro does not already have Python venv/pip support installed, run:

```bash
./scripts/install-linux-deps.sh
```

Or preview what it would run:

```bash
./scripts/install-linux-deps.sh --dry-run
```

Supported package managers, best effort:

- `apt` — Debian, Ubuntu, Linux Mint, Pop!_OS, elementary OS
- `dnf` — Fedora and related systems
- `rpm-ostree` — Fedora Atomic / Bazzite / Silverblue-style systems
- `pacman` — Arch, Manjaro, EndeavourOS
- `zypper` — openSUSE
- `apk` — Alpine
- `xbps-install` — Void Linux
- `eopkg` — Solus

Package names can vary by distro release. If the helper fails, install Python 3.10+, venv, pip, and Qt/PySide6 runtime dependencies manually, then run `./install.sh` again.

## Common distro commands

### Debian / Ubuntu / Mint

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip python3-setuptools python3-wheel \
  libgl1 libegl1 libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 \
  libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 \
  libxcb-xinerama0 libxcb-xinput0 desktop-file-utils acl
./install.sh
```

### Fedora

```bash
sudo dnf install python3 python3-pip python3-virtualenv \
  libxkbcommon-x11 xcb-util-cursor qt6-qtwayland \
  desktop-file-utils hicolor-icon-theme acl
./install.sh
```

### Bazzite / Fedora Atomic

```bash
rpm-ostree install python3 python3-pip python3-virtualenv \
  libxkbcommon-x11 xcb-util-cursor qt6-qtwayland \
  desktop-file-utils hicolor-icon-theme acl
systemctl reboot
./install.sh
```

### Arch / Manjaro / EndeavourOS

```bash
sudo pacman -Syu python python-pip python-virtualenv \
  libxkbcommon-x11 xcb-util-cursor qt6-wayland \
  desktop-file-utils hicolor-icon-theme acl
./install.sh
```

### openSUSE

```bash
sudo zypper install python3 python3-pip python3-virtualenv \
  libxkbcommon-x11-0 libxcb-cursor0 desktop-file-utils hicolor-icon-theme acl
./install.sh
```

## Install without autostart

```bash
./install.sh --no-autostart
```

or:

```bash
HYPERX_SAGA_NO_AUTOSTART=1 ./install.sh
```

## Install somewhere else

```bash
./install.sh --target "$HOME/Apps/hyperx-saga-control"
```

## Run without installing

For testing/development:

```bash
./run.sh
```

## Diagnose problems

```bash
./scripts/check-system.py
./scripts/diagnose-devices.py
./scripts/show-hidraw-permissions.sh
```

If the app detects the mouse but cannot open it:

```bash
./scripts/install-hidraw-permissions.sh
```

Then unplug/replug the mouse or dongle.

For the current session only:

```bash
./scripts/fix-current-permissions.sh
```

## AppImage / Flatpak status

A normal user-local venv install is currently the recommended universal method.

Flatpak/AppImage packaging is possible, but USB/HID access still requires host-side permissions for `/dev/hidraw*`. For that reason, even sandboxed builds will still need a udev rule or host permission helper.

Experimental packaging scaffolding lives in:

```text
packaging/
```
