#!/usr/bin/env bash
set -euo pipefail

APP_NAME="hyperx-saga-control"
APP_DIR="${HYPERX_SAGA_CONTROL_APP_DIR:-$HOME/.local/share/$APP_NAME}"
BIN="$HOME/.local/bin/hyperx-saga-control"
DESKTOP="$HOME/.local/share/applications/io.github.hyperx_saga_control.desktop"
AUTOSTART="$HOME/.config/autostart/io.github.hyperx_saga_control.desktop"
ICON="$HOME/.local/share/icons/hicolor/scalable/apps/hyperx-saga-control.svg"

rm -rf "$APP_DIR"
rm -f "$BIN" "$DESKTOP" "$AUTOSTART" "$ICON"

if [[ "${1:-}" == "--remove-udev" ]]; then
  sudo rm -f /etc/udev/rules.d/60-hyperx-saga-pro.rules
  sudo udevadm control --reload-rules
  sudo udevadm trigger || true
  echo "Removed udev rule. The hyperx group was left in place."
fi

if command -v kbuildsycoca6 >/dev/null 2>&1; then
  kbuildsycoca6 >/dev/null 2>&1 || true
fi

echo "Uninstalled HyperX Saga Control."
echo "To remove the udev rule too, run: ./uninstall.sh --remove-udev"
