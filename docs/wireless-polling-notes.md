# Wireless polling / report-rate notes

Wireless polling was decoded from user-captured NGENUITY USBPcap traces:

- `40_wireless_polling_1000hz.pcap`
- `41_wireless_polling_4000hz.pcap`
- `50_wireless_explicit_save_to_device.pcap`

The native Saga Pro profile table is report `0x32`:

```text
32 01 PP 00 RR 0f AA <DPI stage records...>
```

Where:

- `PP` is the immediate/profile selector:
  - `00` = immediate/live write
  - `01` = profile write
- `RR` is the polling/report interval byte:
  - `08` = 1000 Hz
  - `02` = 4000 Hz
- `AA` is the active DPI stage.

The `RR` value matches USB high-speed 125 microsecond interval units:

```text
1000 Hz = 1.000 ms = 8 * 125 us -> 0x08
4000 Hz = 0.250 ms = 2 * 125 us -> 0x02
```

The application exposes 4000 Hz and 2000 Hz only in 2.4 GHz wireless mode. Wired mode exposes 1000 Hz and below for the Pulsefire Saga Pro.

Polling and DPI live in the same native `0x32` table, so changing polling rewrites the current DPI table as well. The GUI preserves the values currently shown in the DPI tab when saving polling.
