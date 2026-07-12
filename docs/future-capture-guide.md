# Future protocol capture guide

This project currently supports battery, charging/temperature/voltage, RGB colour/brightness, onboard RGB save, DPI profiles, local profiles, and polling/report-rate switching.

The next protocol targets are:

- RGB effects: solid/static, breathing, cycle/rainbow, speed, direction, brightness
- button remapping: left/right/middle, side buttons, DPI button, scroll click
- macros: macro creation, macro assignment, macro playback mode, macro removal

## Capture rule

Record exactly **one NGENUITY action per PCAP**.

Good captures:

```text
lighting_solid_ff00aa.pcap
lighting_breathing_ff00aa_slow.pcap
button_side_back_keyboard_a.pcap
macro_create_ab_50ms.pcap
```

Bad captures:

```text
changed_lighting_and_dpi_and_macro.pcap
```

The app can only implement a feature safely after the packet is decoded from a clean single-action capture.

## Recommended capture order

Lighting:

```text
solid/static colour
breathing colour
cycle/rainbow mode
brightness 100/50/10
speed slow/medium/fast
explicit save to device
```

Button mappings:

```text
side back -> keyboard A
side forward -> keyboard B
DPI button -> disabled/no action
restore defaults
explicit save to device
```

Macros:

```text
create simple macro A,B with known delays
assign macro to side back
remove macro from side back
explicit save to device
```

Always include a startup/idle capture for comparison.
