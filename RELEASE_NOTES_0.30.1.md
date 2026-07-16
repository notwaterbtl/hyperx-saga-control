# SagaCtrl 0.30.1

Small usability release for tray process control.

## Changed

- Added **Exit SagaCtrl** to the system tray menu.
- The tray exit action now stops timers, hides the tray icon, closes the control window, and exits the Qt event loop.
- Added **Hide to Tray** to the tray menu.
- Closing the main window still keeps SagaCtrl running in the tray, but the tray menu now clearly exposes a full quit action.

## Notes

This package does not include `README.md`, so it will not overwrite your existing GitHub README.
