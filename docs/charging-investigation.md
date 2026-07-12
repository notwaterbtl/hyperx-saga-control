# Charging Status Investigation

Battery percentage is confirmed through the Saga Pro status query:

```text
host -> mouse: 50 02
mouse -> host: 51 02 PP ...
```

`PP` behaves as the battery percentage.

Charging state still needs labelled captures. Current evidence suggests byte 3 in the `51 02` response may be a power-state field:

```text
51 02 PP 00 ... = on battery / not charging candidate
51 02 PP 02 ... = charging / USB power candidate
```

Bytes 6..7 also look like a little-endian voltage/millivolt candidate. Example:

```text
bc 10 = 0x10bc = 4284 mV candidate
```

These fields are intentionally labelled as candidates until multiple plugged/unplugged captures confirm them.

## How to collect data

Run the monitor:

```bash
cd ~/Applications/hyperx-saga-control
source .venv/bin/activate
PYTHONPATH="$PWD" python scripts/monitor-charging-status.py --csv charging-status.csv
```

Then perform this sequence while the script is running:

1. Wireless dongle only, mouse not connected by cable.
2. Plug the mouse into a USB power source or charging cable.
3. Wait 10-20 seconds.
4. Unplug the charging cable.
5. Wait 10-20 seconds.
6. Optionally repeat in wired USB mode.

Share the terminal output and `charging-status.csv`.

## App behaviour

The app displays:

- Battery percentage
- Power-state candidate
- Battery voltage
- Raw first bytes of the `51 02` report

The power-state byte is now mapped for on-battery, charging/USB power, and full/charge-complete states.
