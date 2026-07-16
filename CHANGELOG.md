# Changelog

## 0.30.1

- Added a tray menu `Exit SagaCtrl` action that fully terminates the background process.
- Added a `Hide to Tray` action so closing the main window can continue to minimize while the tray menu provides an explicit exit path.
- Improved the close-window notification to tell users how to quit completely.

## 0.30.0

- Added cross-distro installer improvements.
- Added `scripts/install-linux-deps.sh` for best-effort dependency setup across apt, dnf, rpm-ostree, pacman, zypper, apk, xbps, and eopkg systems.
- Added `scripts/check-system.py` for Python, PySide6, udev, and hidraw diagnostics.
- Added `docs/INSTALL_LINUX.md` with generic Linux installation instructions.
- Added experimental packaging scaffolding for Flatpak/AppImage and GitHub release archives.
- Improved `install.sh` with options for custom targets, Python selection, no-autostart, and skip-udev installs.

## 0.29.0

- Corrected polling availability: 2000 Hz is wireless-only, same as 4000 Hz.
- Wired mode exposes only 1000, 500, 250, and 125 Hz.
- Wireless mode exposes 4000, 2000, 1000, 500, 250, and 125 Hz.
- Updated Polling tab text, CLI guardrails, README, and protocol notes.

## 0.28.0

- Added full standard polling-rate list.
- Added future capture kit for lighting effects, button mappings, and macros.

## 0.27.0

- Added wireless polling/report-rate support using the native 0x32 profile table.

## 0.26.0

- Added low-battery desktop notifications.

## 0.25.0

- Added decoded battery power-state, temperature, and voltage labels.
