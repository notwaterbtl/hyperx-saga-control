#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RULE_SRC="$ROOT_DIR/share/udev/rules.d/60-hyperx-saga-pro.rules"
RULE_DST="/etc/udev/rules.d/60-hyperx-saga-pro.rules"
TARGET_USER="${SUDO_USER:-${USER}}"

if [[ ! -f "$RULE_SRC" ]]; then
  echo "Could not find rule file: $RULE_SRC" >&2
  exit 1
fi

echo "Creating group: hyperx"
sudo groupadd -f hyperx

echo "Adding user '$TARGET_USER' to group: hyperx"
sudo usermod -aG hyperx "$TARGET_USER"

echo "Installing udev rule: $RULE_DST"
sudo install -m 0644 "$RULE_SRC" "$RULE_DST"
sudo udevadm control --reload-rules
sudo udevadm trigger || true

echo "Applying immediate ACL fallback to currently attached Saga Pro hidraw nodes."
for dev in /dev/hidraw*; do
  [[ -e "$dev" ]] || continue
  props="$(udevadm info -q property -n "$dev" 2>/dev/null || true)"
  vendor="$(printf '%s\n' "$props" | awk -F= '/^ID_VENDOR_ID=/{print tolower($2); exit}')"
  model="$(printf '%s\n' "$props" | awk -F= '/^ID_MODEL_ID=/{print tolower($2); exit}')"
  if [[ "$vendor" == "03f0" && ( "$model" == "04bf" || "$model" == "06bf" ) ]]; then
    echo "  granting rw access to $dev ($vendor:$model) for $TARGET_USER"
    sudo chgrp hyperx "$dev" || true
    sudo chmod 0660 "$dev" || true
    if command -v setfacl >/dev/null 2>&1; then
      sudo setfacl -m "u:${TARGET_USER}:rw" "$dev" || true
    fi
  fi
done

cat <<MSG

Done.

Now unplug/replug the wired mouse cable or the 2.4 GHz dongle.
If this is the first time '$TARGET_USER' was added to the hyperx group,
log out and back in once so the new group membership applies everywhere.

Verify with:
  scripts/show-hidraw-permissions.sh

MSG
