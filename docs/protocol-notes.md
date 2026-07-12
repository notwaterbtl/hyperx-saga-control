# Protocol Notes

These notes document the parts of the HyperX Pulsefire Saga Pro protocol currently implemented by HyperX Saga Control.

This is not official documentation. It is based on observed HID traffic and behaviour testing.

## Device IDs

| Mode | VID:PID |
| --- | --- |
| Wired USB | `03f0:04bf` |
| 2.4 GHz wireless | `03f0:06bf` |

## Known Linux endpoints

Typical nodes observed during development:

| Mode | Movement | RGB / LampArray | Native config |
| --- | --- | --- | --- |
| Wired | `/dev/hidraw0` | `/dev/hidraw1` | `/dev/hidraw2` |
| Wireless | `/dev/hidraw1` | `/dev/hidraw2` | `/dev/hidraw3` |

The app does not rely on fixed node numbers.

## Battery

Request:

```text
50 02 00 00 ...
```

Response:

```text
51 02 PP ...
```

`PP` appears to be the battery percentage.

Example:

```text
51 02 63 ...
```

`0x63` is decimal `99`, interpreted as 99%.

## DPI

DPI profiles are written using native report family `0x32`.

Observed encoding:

```text
dpi_code = (DPI / 50) - 1
```

Examples:

| DPI | Code |
| --- | --- |
| 400 | `07` |
| 800 | `0f` |
| 1600 | `1f` |
| 3200 | `3f` |

DPI stage events from the device look like:

```text
fb 08 00 07  # stage 0
fb 08 01 0f  # stage 1
fb 08 02 1f  # stage 2
fb 08 03 3f  # stage 3
```

## RGB and brightness

Live RGB uses native RGB reports around `0x44`.

Brightness uses native report family `0x40`.

Persistent onboard RGB profile saving uses a profile sequence involving:

```text
44
40
50
36
```

The minimal `rgb-only` profile sequence has been tested across power cycles.

## Polling

Polling is stored in the native `0x32` DPI/profile table at byte offset `0x04`.

Polling code mapping:

```text
0x40 = 125 Hz
0x20 = 250 Hz
0x10 = 500 Hz
0x08 = 1000 Hz
0x04 = 2000 Hz (wireless only)
0x02 = 4000 Hz (wireless only)
```

4000 Hz and 2000 Hz are treated as wireless-only. Wired mode should use 1000 Hz or lower.


## Battery and charging status

The confirmed status query is:

```text
host -> device: 50 02
device -> host: 51 02 PP ...
```

`PP` is confirmed as the battery percentage.

Current evidence confirms byte 3 of the `51 02` response indicates the power/charge state:

```text
51 02 PP 00 TT 00 VV VV ... = on battery
51 02 PP 01 TT 00 VV VV ... = USB power / charging
51 02 64 02 TT 00 VV VV ... = full / 100% / charge complete
```

Bytes 6..7 appear to be a little-endian voltage/millivolt candidate, for example:

```text
bc 10 = 0x10bc = 4284 mV candidate
```

Byte 4 is temperature in °C, and bytes 6..7 are battery/charger voltage in millivolts, little-endian.


## Low-battery notifications

The application implements low-battery warnings in userspace. It periodically sends the confirmed battery/status query:

```text
50 02 -> 51 02 PP SS TT 00 VV VV ...
```

The warning trigger currently uses `PP` (battery percentage) and optionally requires `SS == 0x00` so notifications only appear when the mouse is on battery power. The firmware-level NGENUITY low-battery-warning packet is not implemented yet.


## Wireless polling

Wireless polling was decoded from NGENUITY captures. The native `0x32` profile table uses offset `0x04` as a polling interval code: `0x08` for 1000 Hz and `0x02` for 4000 Hz. The app exposes this in the Polling tab. 2000 Hz and 4000 Hz are intended for the 2.4 GHz wireless dongle.


## Wireless polling / report rate

Wireless polling was decoded from NGENUITY captures comparing 1000 Hz and 4000 Hz. Polling is stored in the native Saga `0x32` profile/DPI table.

```text
32 01 PP 00 RR 0f AA ...
```

Fields:

```text
PP = 0x00 for immediate/live write, 0x01 for profile write
RR = polling/report interval code
AA = active DPI stage
```

Observed `RR` values:

```text
0x08 = 1000 Hz
0x02 = 4000 Hz
```

The same `0x32` report also contains the four DPI stage records, so polling changes must preserve the current DPI table when writing.


## Polling / report-rate interval codes

Polling is stored inside the native `0x32` DPI/profile table at byte offset `0x04`.

Confirmed from wireless captures:

```text
1000 Hz -> 0x08
4000 Hz -> 0x02
```

The remaining standard rates follow the same interval relationship:

```text
rate_hz = 8000 / interval_code

4000 Hz -> 0x02  wireless only
2000 Hz -> 0x04  wireless only
1000 Hz -> 0x08
 500 Hz -> 0x10
 250 Hz -> 0x20
 125 Hz -> 0x40
```

The UI exposes `4000` and `2000` only in wireless mode. Wired mode exposes `1000`, `500`, `250`, and `125`.
