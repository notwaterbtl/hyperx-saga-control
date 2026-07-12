#!/usr/bin/env bash
set -euo pipefail

RULE_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/share/udev/rules.d/99-hyperx-saga-pro.rules"
RULE_DST="/etc/udev/rules.d/99-hyperx-saga-pro.rules"

if [[ ! -f "$RULE_SRC" ]]; then
  echo "Could not find rule file: $RULE_SRC" >&2
  exit 1
fi

echo "Installing $RULE_DST"
sudo install -m 0644 "$RULE_SRC" "$RULE_DST"
sudo udevadm control --reload-rules
sudo udevadm trigger || true

TARGET_USER="${SUDO_USER:-${USER}}"
echo "Applying immediate ACL fallback to currently attached Saga Pro hidraw nodes for user: $TARGET_USER."
for dev in /dev/hidraw*; do
  [[ -e "$dev" ]] || continue
  props="$(udevadm info -q property -n "$dev" 2>/dev/null || true)"
  vendor="$(printf '%s\n' "$props" | awk -F= '/^ID_VENDOR_ID=/{print $2; exit}')"
  model="$(printf '%s\n' "$props" | awk -F= '/^ID_MODEL_ID=/{print $2; exit}')"
  if [[ "$vendor" == "03f0" && ( "$model" == "04bf" || "$model" == "06bf" ) ]]; then
    echo "  granting current user rw access to $dev ($vendor:$model)"
    sudo chmod a+rw "$dev" || true
    if command -v setfacl >/dev/null 2>&1; then
      sudo setfacl -m "u:${TARGET_USER}:rw" "$dev" || true
    fi
  fi
done

cat <<MSG

Done.
Now unplug/replug the wired mouse cable or the 2.4 GHz dongle.
Then verify with:
  ls -l /dev/hidraw*
  python scripts/diagnose-devices.py

For Saga Pro nodes, permissions should now be crw-rw-rw- or include your user in getfacl.
MSG
