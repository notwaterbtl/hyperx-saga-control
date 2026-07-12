#!/usr/bin/env bash
set -euo pipefail

found=0
for dev in /dev/hidraw*; do
  [[ -e "$dev" ]] || continue
  props="$(udevadm info -q property -n "$dev" 2>/dev/null || true)"
  vendor="$(printf '%s\n' "$props" | awk -F= '/^ID_VENDOR_ID=/{print tolower($2); exit}')"
  model="$(printf '%s\n' "$props" | awk -F= '/^ID_MODEL_ID=/{print tolower($2); exit}')"
  if [[ "$vendor" == "03f0" && ( "$model" == "04bf" || "$model" == "06bf" ) ]]; then
    found=1
    echo "===== $dev ====="
    printf '%s\n' "$props" | grep -E 'ID_VENDOR_ID|ID_MODEL_ID|ID_MODEL|ID_VENDOR' || true
    ls -l "$dev"
    if command -v getfacl >/dev/null 2>&1; then
      getfacl "$dev" 2>/dev/null | sed -n '1,14p'
    fi
    echo
  fi
done

if [[ "$found" == "0" ]]; then
  echo "No HyperX Pulsefire Saga Pro hidraw nodes found."
  echo "Check that the wired mouse or 2.4 GHz dongle is connected."
fi
