#!/usr/bin/env bash
set -euo pipefail

ASSUME_YES=0
DRY_RUN=0

usage() {
  cat <<'USAGE'
Install best-effort system prerequisites for HyperX Saga Control.

Usage:
  ./scripts/install-linux-deps.sh [--yes] [--dry-run]

This script only installs generic prerequisites such as Python, venv/pip, and
common Qt runtime libraries. The app itself still uses a private Python venv.

Supported package managers, best effort:
  apt, dnf, rpm-ostree, pacman, zypper, apk, xbps-install, eopkg
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --yes|-y) ASSUME_YES=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

have() { command -v "$1" >/dev/null 2>&1; }
run() {
  echo "+ $*"
  if [[ "$DRY_RUN" != "1" ]]; then
    "$@"
  fi
}

sudo_cmd() {
  if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

install_apt() {
  local y=()
  [[ "$ASSUME_YES" == "1" ]] && y=(-y)
  run sudo apt update
  run sudo apt install "${y[@]}" \
    python3 python3-venv python3-pip python3-setuptools python3-wheel \
    libgl1 libegl1 libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 \
    libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 \
    libxcb-xinerama0 libxcb-xinput0 desktop-file-utils
}

install_dnf() {
  local y=()
  [[ "$ASSUME_YES" == "1" ]] && y=(-y)
  run sudo dnf install "${y[@]}" \
    python3 python3-pip python3-virtualenv \
    libxkbcommon-x11 xcb-util-cursor qt6-qtwayland \
    desktop-file-utils hicolor-icon-theme acl
}

install_rpm_ostree() {
  echo "Detected rpm-ostree system. Layering minimal host packages."
  echo "A reboot is usually required after rpm-ostree install."
  run rpm-ostree install \
    python3 python3-pip python3-virtualenv \
    libxkbcommon-x11 xcb-util-cursor qt6-qtwayland \
    desktop-file-utils hicolor-icon-theme acl
}

install_pacman() {
  local y=()
  [[ "$ASSUME_YES" == "1" ]] && y=(--noconfirm)
  run sudo pacman -Syu "${y[@]}" \
    python python-pip python-virtualenv \
    libxkbcommon-x11 xcb-util-cursor qt6-wayland \
    desktop-file-utils hicolor-icon-theme acl
}

install_zypper() {
  local y=()
  [[ "$ASSUME_YES" == "1" ]] && y=(-y)
  run sudo zypper install "${y[@]}" \
    python3 python3-pip python3-virtualenv \
    libxkbcommon-x11-0 libxcb-cursor0 libQt6Gui6 \
    desktop-file-utils hicolor-icon-theme acl
}

install_apk() {
  run sudo apk add \
    python3 py3-pip py3-virtualenv \
    libxkbcommon-x11 xcb-util-cursor qt6-qtwayland \
    desktop-file-utils hicolor-icon-theme acl
}

install_xbps() {
  local y=()
  [[ "$ASSUME_YES" == "1" ]] && y=(-y)
  run sudo xbps-install -S "${y[@]}" \
    python3 python3-pip python3-virtualenv \
    libxkbcommon-x11 xcb-util-cursor qt6-wayland \
    desktop-file-utils hicolor-icon-theme acl
}

install_eopkg() {
  local y=()
  [[ "$ASSUME_YES" == "1" ]] && y=(-y)
  run sudo eopkg install "${y[@]}" \
    python3 pip virtualenv \
    libxkbcommon xcb-util-cursor \
    desktop-file-utils hicolor-icon-theme acl
}

if have apt; then
  install_apt
elif have dnf; then
  install_dnf
elif have rpm-ostree; then
  install_rpm_ostree
elif have pacman; then
  install_pacman
elif have zypper; then
  install_zypper
elif have apk; then
  install_apk
elif have xbps-install; then
  install_xbps
elif have eopkg; then
  install_eopkg
else
  cat <<'MSG'
Could not detect a supported package manager.

Install these prerequisites manually:
  - Python 3.10+
  - Python venv support
  - pip
  - Qt/PySide6 runtime dependencies, if your system needs them
  - acl, udev, desktop-file-utils, hicolor-icon-theme

Then run:
  ./install.sh
MSG
  exit 1
fi

cat <<'MSG'

System prerequisite step finished.
Now run:
  ./install.sh

If PySide6 cannot be installed from pip on your architecture, see:
  docs/INSTALL_LINUX.md
MSG
