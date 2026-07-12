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

Wireless 1000 Hz / 4000 Hz switching is not implemented yet.

The application intentionally does not send guessed polling packets.
