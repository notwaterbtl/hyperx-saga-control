# Future capture targets: RGB effects, button mappings, and macros

Current support covers:

- battery percentage / power state / temperature / voltage
- live RGB color and brightness
- persistent RGB profile color and brightness
- DPI table editing and persistence
- polling/report-rate selection through the native `0x32` table

The next feature areas are RGB effects and input remapping.

## RGB effects

The app currently implements static RGB color because the profile-save sequence for static color is confirmed.

The next captures needed are:

- Solid/static color baseline
- Breathing/pulse slow
- Breathing/pulse fast
- Color cycle/rainbow slow
- Color cycle/rainbow fast
- Lighting off
- Explicit save-to-device after each effect

These should identify which bytes in the native `0x44`/`0x40` profile records represent:

- effect mode
- speed
- direction
- brightness
- color slots

## Button mappings

Useful first captures:

- Reset buttons to defaults
- Map side Back button to keyboard `A`
- Map side Forward button to keyboard `B`
- Restore defaults

## Macros

Useful first captures:

- Create a simple `ABC` macro
- Assign it to side Back
- Remove the assignment
- Delete the macro

Macros may require a more complex storage format than simple button remaps, so they should be captured after basic button mapping is decoded.
