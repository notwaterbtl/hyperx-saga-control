# SagaCtrl 0.30.0

This release focuses on making SagaCtrl easier to install and troubleshoot across Linux distributions, not just Fedora/Bazzite.

## Highlights

- Added a universal Linux installation flow.
- Added best-effort dependency helper for common package managers.
- Added system diagnostics for Python, PySide6, udev, hidraw, and Saga Pro device permissions.
- Improved installer options for custom install targets, autostart control, Python selection, and udev handling.
- Added generic Linux install documentation.
- Added early packaging scaffolding for Flatpak/AppImage experiments.

## Existing device support retained

- Battery percentage, charging/USB state, temperature, and voltage display.
- Wired and 2.4 GHz wireless detection.
- Persistent RGB color and brightness profiles.
- Persistent four-stage DPI profiles.
- Polling-rate controls:
  - Wired: 125, 250, 500, 1000 Hz
  - Wireless: 125, 250, 500, 1000, 2000, 4000 Hz

## Recommended install

```bash
./scripts/install-linux-deps.sh
./install.sh
```

After installation, unplug/replug the mouse or dongle. If the installer adds your user to the `hyperx` group, log out and back in once.
