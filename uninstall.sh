#!/usr/bin/env bash
set -euo pipefail
APP_NAME="hyperx-saga-control"
rm -rf "$HOME/.local/share/$APP_NAME"
rm -f "$HOME/.local/bin/hyperx-saga-control"
rm -f "$HOME/.local/share/applications/io.github.hyperx_saga_control.desktop"
rm -f "$HOME/.config/autostart/io.github.hyperx_saga_control.desktop"
rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/hyperx-saga-control.svg"
echo "Removed user app files. To remove the udev rule: sudo rm /etc/udev/rules.d/99-hyperx-saga-pro.rules && sudo udevadm control --reload-rules"
