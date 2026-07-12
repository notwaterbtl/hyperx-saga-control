# Polling rate support

Polling/report rate is stored in the native Saga `0x32` DPI/profile table at byte offset `0x04`.

```text
4000 Hz -> 0x02  wireless only
2000 Hz -> 0x04  wireless only
1000 Hz -> 0x08  wired + wireless
500 Hz  -> 0x10  wired + wireless
250 Hz  -> 0x20  wired + wireless
125 Hz  -> 0x40  wired + wireless
```

The 1000 Hz and 4000 Hz values were decoded from wireless NGENUITY USBPcap captures. The other values follow the same `rate_hz = 8000 / interval_code` relationship.

The Pulsefire Saga Pro treats 2000 Hz and 4000 Hz as 2.4 GHz wireless-only options. The GUI and CLI therefore block those rates on the wired USB endpoint unless explicitly forced from the CLI for research.
