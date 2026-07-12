# Polling / report-rate findings

Polling/report rate was decoded from NGENUITY captures of the Pulsefire Saga Pro 2.4 GHz dongle mode.

The native `0x32` DPI/profile table contains a polling interval byte at offset `0x04`:

```text
1000 Hz: 32 01 .. .. 08 0f ...
4000 Hz: 32 01 .. .. 02 0f ...
```

Confirmed from captures:

```text
0x08 = 1000 Hz
0x02 = 4000 Hz
```

The field follows a clean interval formula:

```text
rate_hz = 8000 / interval_code
interval_code = 8000 / rate_hz
```

Supported mapping used by the app:

```text
0x40 = 125 Hz
0x20 = 250 Hz
0x10 = 500 Hz
0x08 = 1000 Hz
0x04 = 2000 Hz (wireless only)
0x02 = 4000 Hz (wireless only)
```

This looks like USB high-speed 125 microsecond microframe units:

```text
0x08 * 125 us = 1000 us = 1000 Hz
0x02 * 125 us = 250 us = 4000 Hz
```

`2000 Hz` and `4000 Hz` are treated as wireless-only. Wired mode should expose 1000 Hz, 500 Hz, 250 Hz, and 125 Hz only.

The app writes polling through the same `0x32` table used for DPI, so it preserves the current UI DPI values when changing the polling rate.
