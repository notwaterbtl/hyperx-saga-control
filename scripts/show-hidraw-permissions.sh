#!/usr/bin/env bash
set -euo pipefail
for dev in /dev/hidraw*; do
  [[ -e "$dev" ]] || continue
  props="$(udevadm info -q property -n "$dev" 2>/dev/null || true)"
  vendor="$(printf '%s\n' "$props" | awk -F= '/^ID_VENDOR_ID=/{print $2; exit}')"
  model="$(printf '%s\n' "$props" | awk -F= '/^ID_MODEL_ID=/{print $2; exit}')"
  if [[ "$vendor" == "03f0" && ( "$model" == "04bf" || "$model" == "06bf" ) ]]; then
    echo "===== $dev ($vendor:$model) ====="
    ls -l "$dev"
    if command -v getfacl >/dev/null 2>&1; then
      getfacl "$dev" | sed -n '1,16p'
    fi
    printf '%s\n' "$props" | grep -E 'ID_VENDOR_ID|ID_MODEL_ID|ID_MODEL|ID_VENDOR|TAGS' || true
  fi
done
