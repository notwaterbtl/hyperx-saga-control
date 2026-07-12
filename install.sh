#!/usr/bin/env bash
set -euo pipefail

APP_NAME="hyperx-saga-control"
APP_DIR="$HOME/.local/share/$APP_NAME"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
AUTOSTART_DIR="$HOME/.config/autostart"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$APP_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$AUTOSTART_DIR" "$ICON_DIR"
TMP_DIR="$APP_DIR.tmp"
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"
cp -a "$SCRIPT_DIR"/. "$TMP_DIR"/
rm -rf "$APP_DIR"
mv "$TMP_DIR" "$APP_DIR"

install -m 0755 "$SCRIPT_DIR/bin/hyperx-saga-control" "$BIN_DIR/hyperx-saga-control"
install -m 0644 "$SCRIPT_DIR/share/icons/hyperx-saga-control.svg" "$ICON_DIR/hyperx-saga-control.svg"

sed "s#__BIN__#$BIN_DIR/hyperx-saga-control#g" \
  "$SCRIPT_DIR/share/applications/io.github.hyperx_saga_control.desktop.in" \
  > "$DESKTOP_DIR/io.github.hyperx_saga_control.desktop"
chmod 0644 "$DESKTOP_DIR/io.github.hyperx_saga_control.desktop"

sed "s#__BIN__#$BIN_DIR/hyperx-saga-control#g" \
  "$SCRIPT_DIR/share/autostart/io.github.hyperx_saga_control.desktop.in" \
  > "$AUTOSTART_DIR/io.github.hyperx_saga_control.desktop"
chmod 0644 "$AUTOSTART_DIR/io.github.hyperx_saga_control.desktop"

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q "$HOME/.local/share/icons/hicolor" || true
fi

if ! python3 - <<'PY' >/dev/null 2>&1
import PySide6
PY
then
  cat <<'MSG'

PySide6 was not found. Install the Qt Python bindings before launching the GUI.

Fedora Workstation / normal Fedora KDE:
  sudo dnf install python3-pyside6

Bazzite / Fedora Atomic Desktop:
  rpm-ostree install python3-pyside6
  systemctl reboot

MSG
fi

if [[ -f "$SCRIPT_DIR/share/udev/rules.d/99-hyperx-saga-pro.rules" ]]; then
  echo "Installing udev rule; sudo may prompt for your password."
  sudo install -m 0644 "$SCRIPT_DIR/share/udev/rules.d/99-hyperx-saga-pro.rules" /etc/udev/rules.d/99-hyperx-saga-pro.rules
  sudo udevadm control --reload-rules
  sudo udevadm trigger || true
fi

cat <<MSG

Installed HyperX Saga Control.

Run it now:
  $BIN_DIR/hyperx-saga-control

It also installs a KDE autostart entry, so it will start minimized in the tray on next login.
After udev rule installation, unplug/replug the mouse or dongle.

MSG
