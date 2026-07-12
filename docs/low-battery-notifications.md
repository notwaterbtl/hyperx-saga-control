# Low-battery notifications

HyperX Saga Control can warn the user when the mouse battery drops below a configurable percentage.

This warning is handled by the Linux tray application. It does not currently program the mouse firmware's own low-battery warning threshold.

## User settings

The Status tab contains a **Low battery warning** section:

- Enable or disable warnings
- Choose the warning percentage
- Choose the repeat interval
- Choose whether warnings should only appear when the mouse is running on battery power
- Send a test notification

Settings are stored in:

```text
~/.config/hyperx-saga-control/settings.json
```

## Protocol basis

The warning logic uses the confirmed battery/status report:

```text
Host -> mouse:
50 02

Mouse -> host:
51 02 PP SS TT 00 VV VV ...
```

Known fields:

```text
PP       battery percentage
SS       power/charge state
TT       temperature in Celsius
VV VV    battery voltage in millivolts, little-endian
```

Observed power states:

```text
0x00 = on battery
0x01 = USB power / charging
0x02 = full / charge complete
```

