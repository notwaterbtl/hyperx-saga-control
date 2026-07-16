#!/usr/bin/env bash
set -euo pipefail

APP_NAME="hyperx-saga-control"
DISPLAY_NAME="HyperX Saga Control"
DEFAULT_APP_DIR="$HOME/.local/share/$APP_NAME"
APP_DIR="${HYPERX_SAGA_CONTROL_APP_DIR:-$DEFAULT_APP_DIR}"
BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
AUTOSTART_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
INSTALL_AUTOSTART=1
INSTALL_UDEV=1
UPGRADE_PIP=1

usage() {
  cat <<USAGE
Install $DISPLAY_NAME for the current user.

Usage:
  ./install.sh [options]

Options:
  --target DIR        Install app files to DIR instead of $DEFAULT_APP_DIR
  --python PATH       Python interpreter to use instead of python3
  --no-autostart      Do not install the KDE/XDG autostart entry
  --skip-udev         Do not install hidraw udev permissions
  --no-pip-upgrade    Do not upgrade pip in the private venv
  -h, --help          Show this help

Environment variables still supported:
  HYPERX_SAGA_CONTROL_APP_DIR=/custom/path
  HYPERX_SAGA_NO_AUTOSTART=1
  PYTHON_BIN=/path/to/python3

Notes:
  This installer is distro-agnostic. It creates a private Python venv and
  installs Python dependencies into that venv. It does not require PySide6
  to be installed globally by apt/dnf/pacman/etc.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      APP_DIR="${2:-}"
      [[ -n "$APP_DIR" ]] || { echo "--target needs a directory" >&2; exit 2; }
      shift 2
      ;;
    --python)
      PYTHON_BIN="${2:-}"
      [[ -n "$PYTHON_BIN" ]] || { echo "--python needs a path" >&2; exit 2; }
      shift 2
      ;;
    --no-autostart)
      INSTALL_AUTOSTART=0
      shift
      ;;
    --skip-udev)
      INSTALL_UDEV=0
      shift
      ;;
    --no-pip-upgrade)
      UPGRADE_PIP=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "${HYPERX_SAGA_NO_AUTOSTART:-0}" == "1" ]]; then
  INSTALL_AUTOSTART=0
fi

have() { command -v "$1" >/dev/null 2>&1; }

check_python() {
  if ! have "$PYTHON_BIN"; then
    echo "Python interpreter not found: $PYTHON_BIN" >&2
    echo "Install Python 3.10+ first, or rerun with: ./install.sh --python /path/to/python3" >&2
    exit 1
  fi

  "$PYTHON_BIN" - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit(f"Python 3.10+ is required, found {sys.version.split()[0]}")
PY
}

copy_app() {
  local tmp_dir="${APP_DIR}.tmp"
  rm -rf "$tmp_dir"
  mkdir -p "$tmp_dir"

  if have rsync; then
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
  echo "Creating Python venv at: $APP_DIR/.venv"
  if ! "$PYTHON_BIN" -m venv "$APP_DIR/.venv"; then
    cat >&2 <<'MSG'

Failed to create the Python virtual environment.

On some distributions you may need an extra package:
  Debian/Ubuntu/Mint:   sudo apt install python3-venv python3-pip
  Fedora/Bazzite:      sudo dnf install python3 python3-pip
  Arch/Manjaro:        sudo pacman -S python python-pip
  openSUSE:            sudo zypper install python3 python3-pip python3-virtualenv
  Alpine:              sudo apk add python3 py3-pip py3-virtualenv

You can also run:
  ./scripts/install-linux-deps.sh

MSG
    exit 1
  fi

  if [[ "$UPGRADE_PIP" == "1" ]]; then
    "$APP_DIR/.venv/bin/python" -m pip install --upgrade pip
  fi

  if ! "$APP_DIR/.venv/bin/python" -m pip install -r "$APP_DIR/requirements.txt"; then
    cat >&2 <<'MSG'

Failed to install Python dependencies.

Most users only need internet access and pip. If PySide6 wheels are unavailable
for your distribution/CPU, install your distro's Qt/PySide6 package and run from
source, or see docs/INSTALL_LINUX.md for alternatives.

MSG
    exit 1
  fi
}

install_launchers() {
  mkdir -p "$BIN_DIR" "$DESKTOP_DIR" "$AUTOSTART_DIR" "$ICON_DIR"

  install -m 0755 "$APP_DIR/bin/hyperx-saga-control" "$BIN_DIR/hyperx-saga-control"
  install -m 0644 "$APP_DIR/share/icons/hyperx-saga-control.svg" "$ICON_DIR/hyperx-saga-control.svg"

  sed "s#__BIN__#$BIN_DIR/hyperx-saga-control#g" \
    "$APP_DIR/share/applications/io.github.hyperx_saga_control.desktop.in" \
    > "$DESKTOP_DIR/io.github.hyperx_saga_control.desktop"
  chmod 0644 "$DESKTOP_DIR/io.github.hyperx_saga_control.desktop"

  if [[ "$INSTALL_AUTOSTART" == "1" ]]; then
    sed "s#__BIN__#$BIN_DIR/hyperx-saga-control#g" \
      "$APP_DIR/share/autostart/io.github.hyperx_saga_control.desktop.in" \
      > "$AUTOSTART_DIR/io.github.hyperx_saga_control.desktop"
    chmod 0644 "$AUTOSTART_DIR/io.github.hyperx_saga_control.desktop"
  else
    rm -f "$AUTOSTART_DIR/io.github.hyperx_saga_control.desktop"
  fi

  if have update-desktop-database; then
    update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
  fi
  if have kbuildsycoca6; then
    kbuildsycoca6 >/dev/null 2>&1 || true
  elif have kbuildsycoca5; then
    kbuildsycoca5 >/dev/null 2>&1 || true
  fi
  if have gtk-update-icon-cache; then
    gtk-update-icon-cache "${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor" >/dev/null 2>&1 || true
  fi
}

install_hidraw_permissions() {
  if [[ "$INSTALL_UDEV" != "1" ]]; then
    echo "Skipping udev/hidraw permission install."
    return 0
  fi

  echo
  echo "Installing hidraw permission rule. sudo may prompt for your password."
  "$APP_DIR/scripts/install-hidraw-permissions.sh"
}

cat <<MSG
Installing $DISPLAY_NAME
  source: $SCRIPT_DIR
  target: $APP_DIR
  python: $PYTHON_BIN
MSG

check_python
copy_app
install_python_env
install_launchers
install_hidraw_permissions

cat <<MSG

Installed $DISPLAY_NAME.

Run it now:
  $BIN_DIR/hyperx-saga-control

It should also appear in your app launcher as:
  HyperX Saga Control

Options used:
  autostart: $INSTALL_AUTOSTART
  udev:      $INSTALL_UDEV

Important:
  - Unplug/replug the mouse cable or 2.4 GHz dongle after install.
  - If you were newly added to the hyperx group, log out and back in once.
  - For cross-distro help, see docs/INSTALL_LINUX.md.

MSG
