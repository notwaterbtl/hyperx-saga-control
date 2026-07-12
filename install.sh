#!/usr/bin/env bash
set -euo pipefail

APP_NAME="hyperx-saga-control"
APP_DIR="${HYPERX_SAGA_CONTROL_APP_DIR:-$HOME/.local/share/$APP_NAME}"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
AUTOSTART_DIR="$HOME/.config/autostart"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

copy_app() {
  local tmp_dir="${APP_DIR}.tmp"
  rm -rf "$tmp_dir"
  mkdir -p "$tmp_dir"

  if command -v rsync >/dev/null 2>&1; then
    rsync -a \
      --exclude='.git' \
      --exclude='.venv' \
      --exclude='__pycache__' \
      --exclude='*.pyc' \
      "$SCRIPT_DIR"/ "$tmp_dir"/
  else
    cp -a "$SCRIPT_DIR"/. "$tmp_dir"/
    rm -rf "$tmp_dir/.git" "$tmp_dir/.venv"
    find "$tmp_dir" -type d -name '__pycache__' -prune -exec rm -rf {} +
    find "$tmp_dir" -type f -name '*.pyc' -delete
  fi

  rm -rf "$APP_DIR"
  mv "$tmp_dir" "$APP_DIR"
}

install_python_env() {
  "$PYTHON_BIN" -m venv "$APP_DIR/.venv"
  "$APP_DIR/.venv/bin/python" -m pip install --upgrade pip
  "$APP_DIR/.venv/bin/python" -m pip install -r "$APP_DIR/requirements.txt"
}

install_launchers() {
  mkdir -p "$BIN_DIR" "$DESKTOP_DIR" "$AUTOSTART_DIR" "$ICON_DIR"

  install -m 0755 "$APP_DIR/bin/hyperx-saga-control" "$BIN_DIR/hyperx-saga-control"
  install -m 0644 "$APP_DIR/share/icons/hyperx-saga-control.svg" "$ICON_DIR/hyperx-saga-control.svg"

  sed "s#__BIN__#$BIN_DIR/hyperx-saga-control#g" \
    "$APP_DIR/share/applications/io.github.hyperx_saga_control.desktop.in" \
    > "$DESKTOP_DIR/io.github.hyperx_saga_control.desktop"
  chmod 0644 "$DESKTOP_DIR/io.github.hyperx_saga_control.desktop"

  if [[ "${HYPERX_SAGA_NO_AUTOSTART:-0}" != "1" ]]; then
    sed "s#__BIN__#$BIN_DIR/hyperx-saga-control#g" \
      "$APP_DIR/share/autostart/io.github.hyperx_saga_control.desktop.in" \
      > "$AUTOSTART_DIR/io.github.hyperx_saga_control.desktop"
    chmod 0644 "$AUTOSTART_DIR/io.github.hyperx_saga_control.desktop"
  fi

  if command -v kbuildsycoca6 >/dev/null 2>&1; then
    kbuildsycoca6 >/dev/null 2>&1 || true
  fi
}

install_hidraw_permissions() {
  echo
  echo "Installing hidraw permission rule. sudo may prompt for your password."
  "$APP_DIR/scripts/install-hidraw-permissions.sh"
}

cat <<MSG
Installing HyperX Saga Control
  source: $SCRIPT_DIR
  target: $APP_DIR
MSG

copy_app
install_python_env
install_launchers
install_hidraw_permissions

cat <<MSG

Installed HyperX Saga Control.

Run it now:
  $BIN_DIR/hyperx-saga-control

It should also appear in your application launcher as:
  HyperX Saga Control

Autostart is enabled by default. To install without autostart, rerun with:
  HYPERX_SAGA_NO_AUTOSTART=1 ./install.sh

Important:
  - Unplug/replug the mouse cable or 2.4 GHz dongle after install.
  - If you were newly added to the hyperx group, log out and back in once.

MSG
