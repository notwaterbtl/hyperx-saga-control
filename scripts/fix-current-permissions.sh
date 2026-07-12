#!/usr/bin/env bash
set -euo pipefail

TARGET_USER="${SUDO_USER:-${USER}}"

for dev in /dev/hidraw*; do
  [[ -e "$dev" ]] || continue
  props="$(udevadm info -q property -n "$dev" 2>/dev/null || true)"
  vendor="$(printf '%s\n' "$props" | awk -F= '/^ID_VENDOR_ID=/{print tolower($2); exit}')"
  model="$(printf '%s\n' "$props" | awk -F= '/^ID_MODEL_ID=/{print tolower($2); exit}')"
  if [[ "$vendor" == "03f0" && ( "$model" == "04bf" || "$model" == "06bf" ) ]]; then
    echo "Granting $TARGET_USER access to $dev ($vendor:$model)"
    sudo chgrp hyperx "$dev" 2>/dev/null || true
    sudo chmod 0660 "$dev" || true
    if command -v setfacl >/dev/null 2>&1; then
      sudo setfacl -m "u:${TARGET_USER}:rw" "$dev" || true
    fi
  fi
done
