from __future__ import annotations

import argparse
import os
import sys
import traceback
import time
from pathlib import Path

from .config import Profile, ProfileStore, load_settings, save_settings
from .protocol import (
    FORCE_CONFIG_ENV,
    HidDevice,
    SagaDevice,
    device_from_path,
    find_config_device,
    format_report,
    normalize_color,
    scan_devices,
    WIRED_POLLING_RATES,
    WIRELESS_POLLING_RATES,
    WIRELESS_ONLY_POLLING_RATES,
)

try:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QAction, QColor, QIcon
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QColorDialog,
        QComboBox,
        QFormLayout,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMenu,
        QMessageBox,
        QPushButton,
        QSpinBox,
        QSystemTrayIcon,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
except Exception as exc:  # pragma: no cover - shown to the user at runtime
    print('PySide6 is required for the GUI.', file=sys.stderr)
    print('Fedora: sudo dnf install python3-pyside6', file=sys.stderr)
    print('Bazzite/Fedora Atomic: rpm-ostree install python3-pyside6, then reboot', file=sys.stderr)
    raise

APP_NAME = 'HyperX Saga Control'
APP_ID = 'io.github.hyperx_saga_control'


def resource_icon() -> QIcon:
    local = Path(__file__).resolve().parent.parent / 'share' / 'icons' / 'hyperx-saga-control.svg'
    if local.exists():
        return QIcon(str(local))
    icon = QIcon.fromTheme('input-mouse')
    if not icon.isNull():
        return icon
    return QApplication.style().standardIcon(QApplication.style().StandardPixmap.SP_ComputerIcon)


class MainWindow(QMainWindow):
    def __init__(self, tray: QSystemTrayIcon | None = None):
        super().__init__()
        self.tray = tray
        self.store = ProfileStore()
        self.settings = load_settings()
        self.devices: list[HidDevice] = []
        self.selected_device: HidDevice | None = None
        self.current_color = QColor('#00aaff')
        self.last_battery: int | None = None
        self.last_low_battery_notify_mono = 0.0
        self.low_battery_active = False

        self.setWindowTitle(APP_NAME)
        self.resize(820, 620)
        self.setWindowIcon(resource_icon())

        self._build_ui()
        self._wire_events()
        self.refresh_profiles()
        self.refresh_devices()
        self.load_profile_to_ui(self.profile_combo.currentText() or 'Default')

        self.battery_timer = QTimer(self)
        self.battery_timer.setInterval(60_000)
        self.battery_timer.timeout.connect(self.refresh_battery)
        self.battery_timer.start()

        self.device_timer = QTimer(self)
        self.device_timer.setInterval(10_000)
        self.device_timer.timeout.connect(self.refresh_devices_silent)
        self.device_timer.start()

    def _build_ui(self) -> None:
        root = QWidget(self)
        outer = QVBoxLayout(root)
        self.setCentralWidget(root)

        header = QGroupBox('Device')
        header_layout = QGridLayout(header)
        self.device_combo = QComboBox()
        self.refresh_button = QPushButton('Refresh devices')
        self.device_status = QLabel('No device selected')
        self.device_status.setTextInteractionFlags(Qt.TextSelectableByMouse)
        header_layout.addWidget(QLabel('Native config node:'), 0, 0)
        header_layout.addWidget(self.device_combo, 0, 1)
        header_layout.addWidget(self.refresh_button, 0, 2)
        header_layout.addWidget(self.device_status, 1, 0, 1, 3)
        outer.addWidget(header)

        tabs = QTabWidget()
        tabs.addTab(self._build_status_tab(), 'Status')
        tabs.addTab(self._build_rgb_tab(), 'RGB Profile')
        tabs.addTab(self._build_dpi_tab(), 'DPI Profile')
        tabs.addTab(self._build_polling_tab(), 'Polling')
        tabs.addTab(self._build_profiles_tab(), 'Local Profiles')
        tabs.addTab(self._build_log_tab(), 'Log')
        outer.addWidget(tabs, 1)

    def _build_status_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        box = QGroupBox('Battery and mode')
        form = QFormLayout(box)
        self.battery_label = QLabel('Unknown')
        self.power_label = QLabel('Unknown')
        self.temperature_label = QLabel('Unknown')
        self.voltage_label = QLabel('Unknown')
        self.raw_battery_label = QLabel('Unknown')
        self.raw_battery_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.mode_label = QLabel('Unknown')
        self.refresh_battery_button = QPushButton('Refresh battery now')
        self.auto_battery_check = QCheckBox('Refresh battery in the tray every 60 seconds')
        self.auto_battery_check.setChecked(True)
        form.addRow('Battery:', self.battery_label)
        form.addRow('Power state:', self.power_label)
        form.addRow('Temperature:', self.temperature_label)
        form.addRow('Battery voltage:', self.voltage_label)
        form.addRow('Raw 51 02:', self.raw_battery_label)
        form.addRow('Mode:', self.mode_label)
        form.addRow('', self.refresh_battery_button)
        form.addRow('', self.auto_battery_check)
        layout.addWidget(box)

        warn_box = QGroupBox('Low battery warning')
        warn_form = QFormLayout(warn_box)
        self.low_battery_enabled_check = QCheckBox('Show a desktop notification when battery falls below the selected level')
        self.low_battery_enabled_check.setChecked(bool(self.settings.get('low_battery_enabled', True)))

        self.low_battery_threshold_spin = QSpinBox()
        self.low_battery_threshold_spin.setRange(1, 99)
        self.low_battery_threshold_spin.setSuffix('%')
        self.low_battery_threshold_spin.setValue(int(self.settings.get('low_battery_threshold', 20)))

        self.low_battery_repeat_spin = QSpinBox()
        self.low_battery_repeat_spin.setRange(1, 1440)
        self.low_battery_repeat_spin.setSuffix(' min')
        self.low_battery_repeat_spin.setValue(int(self.settings.get('low_battery_repeat_minutes', 30)))

        self.low_battery_only_on_battery_check = QCheckBox('Only warn when the mouse is on battery power')
        self.low_battery_only_on_battery_check.setChecked(bool(self.settings.get('low_battery_only_on_battery', True)))

        self.test_low_battery_button = QPushButton('Test low-battery notification')

        warn_form.addRow('', self.low_battery_enabled_check)
        warn_form.addRow('Warn at or below:', self.low_battery_threshold_spin)
        warn_form.addRow('Repeat warning every:', self.low_battery_repeat_spin)
        warn_form.addRow('', self.low_battery_only_on_battery_check)
        warn_form.addRow('', self.test_low_battery_button)
        layout.addWidget(warn_box)

        note = QLabel('Low-battery warnings are handled by this Linux app. The mouse firmware may have its own NGENUITY-controlled warning, but that packet is not implemented yet.')
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch(1)
        return w

    def _build_rgb_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        box = QGroupBox('RGB and brightness')
        form = QFormLayout(box)
        color_row = QHBoxLayout()
        self.color_button = QPushButton('#00aaff')
        self.color_button.setMinimumWidth(130)
        self.pick_color_button = QPushButton('Open color wheel')
        color_row.addWidget(self.color_button)
        color_row.addWidget(self.pick_color_button)
        color_row.addStretch(1)
        self.brightness_spin = QSpinBox()
        self.brightness_spin.setRange(0, 100)
        self.brightness_spin.setSuffix('%')
        self.brightness_spin.setValue(100)
        self.live_rgb_button = QPushButton('Apply live RGB now')
        self.save_rgb_button = QPushButton('Save RGB profile to mouse memory')
        form.addRow('Color:', color_row)
        form.addRow('Brightness:', self.brightness_spin)
        form.addRow('', self.live_rgb_button)
        form.addRow('', self.save_rgb_button)
        layout.addWidget(box)
        note = QLabel('Live RGB changes immediately. “Save RGB profile” writes the confirmed onboard RGB sequence that survived power cycles in testing.')
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch(1)
        return w

    def _build_dpi_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        box = QGroupBox('Four-stage DPI table')
        grid = QGridLayout(box)
        self.dpi_spins: list[QSpinBox] = []
        defaults = [400, 800, 1600, 3200]
        for i in range(4):
            spin = QSpinBox()
            spin.setRange(50, 26000)
            spin.setSingleStep(50)
            spin.setValue(defaults[i])
            spin.setSuffix(' DPI')
            self.dpi_spins.append(spin)
            grid.addWidget(QLabel(f'Stage {i}:'), i, 0)
            grid.addWidget(spin, i, 1)
        self.active_stage_combo = QComboBox()
        for i in range(4):
            self.active_stage_combo.addItem(f'Stage {i}', i)
        self.save_dpi_button = QPushButton('Save DPI profile to mouse')
        grid.addWidget(QLabel('Active stage:'), 4, 0)
        grid.addWidget(self.active_stage_combo, 4, 1)
        grid.addWidget(self.save_dpi_button, 5, 0, 1, 2)
        layout.addWidget(box)
        note = QLabel('The DPI packet is the native Saga Pro 0x32 table discovered from the NGENUITY capture. On your mouse, sending it persisted the DPI profile.')
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch(1)
        return w

    def _build_polling_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        box = QGroupBox('Polling / report rate')
        form = QFormLayout(box)
        self.polling_combo = QComboBox()
        self.polling_status_label = QLabel('Polling is stored in the native 0x32 DPI/profile table. Wireless exposes 4000/2000 Hz plus lower rates; wired exposes 1000 Hz and below.')
        self.polling_status_label.setWordWrap(True)
        self.save_polling_button = QPushButton('Apply / save polling rate to mouse')
        self.update_polling_options()
        form.addRow('Polling rate:', self.polling_combo)
        form.addRow('', self.save_polling_button)
        form.addRow('Status:', self.polling_status_label)
        layout.addWidget(box)
        note = QLabel('Known mapping: 4000=0x02, 2000=0x04, 1000=0x08, 500=0x10, 250=0x20, 125=0x40. 4000 Hz and 2000 Hz are treated as wireless-only for the Saga Pro; wired mode is limited to 1000 Hz and below. Saving polling rewrites the current DPI table from the DPI tab so your stages are preserved.')
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch(1)
        return w

    def _build_profiles_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        box = QGroupBox('Local app profiles')
        grid = QGridLayout(box)
        self.profile_combo = QComboBox()
        self.profile_name = QLineEdit('Default')
        self.save_local_profile_button = QPushButton('Save current UI as local profile')
        self.load_local_profile_button = QPushButton('Load selected local profile')
        self.delete_local_profile_button = QPushButton('Delete selected local profile')
        self.apply_all_button = QPushButton('Apply all to mouse: save RGB + DPI + polling')
        grid.addWidget(QLabel('Selected profile:'), 0, 0)
        grid.addWidget(self.profile_combo, 0, 1)
        grid.addWidget(QLabel('Profile name:'), 1, 0)
        grid.addWidget(self.profile_name, 1, 1)
        grid.addWidget(self.load_local_profile_button, 2, 0, 1, 2)
        grid.addWidget(self.save_local_profile_button, 3, 0, 1, 2)
        grid.addWidget(self.delete_local_profile_button, 4, 0, 1, 2)
        grid.addWidget(self.apply_all_button, 5, 0, 1, 2)
        layout.addWidget(box)
        layout.addStretch(1)
        return w

    def _build_log_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.clear_log_button = QPushButton('Clear log')
        layout.addWidget(self.log_text, 1)
        layout.addWidget(self.clear_log_button)
        return w

    def _wire_events(self) -> None:
        self.refresh_button.clicked.connect(self.refresh_devices)
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        self.refresh_battery_button.clicked.connect(self.refresh_battery)
        self.auto_battery_check.toggled.connect(self.on_auto_battery_toggled)
        self.low_battery_enabled_check.toggled.connect(self.save_low_battery_settings)
        self.low_battery_threshold_spin.valueChanged.connect(self.save_low_battery_settings)
        self.low_battery_repeat_spin.valueChanged.connect(self.save_low_battery_settings)
        self.low_battery_only_on_battery_check.toggled.connect(self.save_low_battery_settings)
        self.test_low_battery_button.clicked.connect(self.test_low_battery_notification)
        self.color_button.clicked.connect(self.pick_color)
        self.pick_color_button.clicked.connect(self.pick_color)
        self.live_rgb_button.clicked.connect(self.apply_live_rgb)
        self.save_rgb_button.clicked.connect(self.save_rgb_profile)
        self.save_dpi_button.clicked.connect(self.save_dpi_profile)
        self.save_polling_button.clicked.connect(self.save_polling_profile)
        self.polling_combo.currentIndexChanged.connect(self.save_default_polling_setting)
        self.profile_combo.currentTextChanged.connect(lambda name: self.profile_name.setText(name))
        self.load_local_profile_button.clicked.connect(lambda: self.load_profile_to_ui(self.profile_combo.currentText()))
        self.save_local_profile_button.clicked.connect(self.save_profile_from_ui)
        self.delete_local_profile_button.clicked.connect(self.delete_selected_profile)
        self.apply_all_button.clicked.connect(self.apply_all_to_mouse)
        self.clear_log_button.clicked.connect(self.log_text.clear)

    def log(self, msg: str) -> None:
        self.log_text.append(msg)
        print(msg)

    def show_error(self, title: str, exc: Exception | str) -> None:
        text = str(exc)
        self.log(f'ERROR: {title}: {text}')
        if isinstance(exc, Exception):
            self.log(traceback.format_exc())
        QMessageBox.critical(self, title, text)

    def refresh_profiles(self) -> None:
        current = self.profile_combo.currentText()
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItems(self.store.names())
        if current:
            idx = self.profile_combo.findText(current)
            if idx >= 0:
                self.profile_combo.setCurrentIndex(idx)
        self.profile_combo.blockSignals(False)

    def profile_from_ui(self) -> Profile:
        return Profile(
            name=self.profile_name.text().strip() or 'Default',
            color=self.current_color.name(),
            brightness=self.brightness_spin.value(),
            dpi=[s.value() for s in self.dpi_spins],
            active_stage=self.active_stage_combo.currentData(),
            polling_hz=int(self.polling_combo.currentData()) if hasattr(self, 'polling_combo') else 1000,
        )

    def load_profile_to_ui(self, name: str) -> None:
        if not name:
            return
        p = self.store.get(name)
        self.profile_name.setText(p.name)
        self.set_color(QColor(p.color))
        self.brightness_spin.setValue(max(0, min(100, int(p.brightness))))
        for spin, dpi in zip(self.dpi_spins, p.dpi):
            spin.setValue(int(dpi))
        idx = self.active_stage_combo.findData(int(p.active_stage))
        if idx >= 0:
            self.active_stage_combo.setCurrentIndex(idx)
        if hasattr(self, 'polling_combo'):
            pidx = self.polling_combo.findData(int(getattr(p, 'polling_hz', 1000)))
            if pidx >= 0:
                self.polling_combo.setCurrentIndex(pidx)
        self.log(f'Loaded local profile: {p.name}')

    def save_profile_from_ui(self) -> None:
        p = self.profile_from_ui()
        self.store.put(p)
        self.refresh_profiles()
        idx = self.profile_combo.findText(p.name)
        if idx >= 0:
            self.profile_combo.setCurrentIndex(idx)
        self.log(f'Saved local profile: {p.name}')

    def delete_selected_profile(self) -> None:
        name = self.profile_combo.currentText()
        self.store.delete(name)
        self.refresh_profiles()
        self.log(f'Deleted local profile: {name}')

    def refresh_devices_silent(self) -> None:
        # Keep current list fresh without flooding the log.
        old = [(d.path, d.pid, d.role) for d in self.devices]
        new = scan_devices()
        new_key = [(d.path, d.pid, d.role) for d in new]
        if new_key != old:
            self.refresh_devices()

    def refresh_devices(self) -> None:
        previous = self.selected_device.path if self.selected_device else self.settings.get('last_device')
        override = os.environ.get(FORCE_CONFIG_ENV, '').strip()
        try:
            all_devices = scan_devices()
            if override:
                try:
                    manual = device_from_path(override, force_role='config')
                    all_devices = [manual] + [d for d in all_devices if d.path != manual.path]
                    previous = manual.path
                    self.log(f'Using manual config device from {FORCE_CONFIG_ENV}: {manual.label}')
                except Exception as exc:
                    self.log(f'WARNING: {FORCE_CONFIG_ENV}={override!r} could not be used: {exc}')
        except Exception as exc:
            self.show_error('Device scan failed', exc)
            return
        self.devices = [d for d in all_devices if d.role == 'config']
        self.device_combo.blockSignals(True)
        self.device_combo.clear()
        for d in self.devices:
            self.device_combo.addItem(d.label, d.path)
        self.device_combo.blockSignals(False)

        index = 0
        if previous:
            for i, d in enumerate(self.devices):
                if d.path == previous:
                    index = i
                    break
        elif self.devices:
            # Prefer wireless if present.
            for i, d in enumerate(self.devices):
                if d.mode == 'wireless':
                    index = i
                    break
        if self.devices:
            self.device_combo.setCurrentIndex(index)
            self.selected_device = self.devices[index]
            self.update_device_status()
            self.update_polling_options()
            self.log(f'Found {len(self.devices)} Saga config device(s). Selected {self.selected_device.label}')
            if self.auto_battery_check.isChecked():
                self.refresh_battery()
        else:
            self.selected_device = None
            self.device_status.setText('No Saga Pro config device found. Check mode, udev permissions, and dongle/cable.')
            self.battery_label.setText('Unknown')
            self.mode_label.setText('Unknown')
            self.update_tray_text()

    def on_device_changed(self, index: int) -> None:
        if 0 <= index < len(self.devices):
            self.selected_device = self.devices[index]
            self.settings['last_device'] = self.selected_device.path
            save_settings(self.settings)
            self.update_device_status()
            self.update_polling_options()
            if self.auto_battery_check.isChecked():
                self.refresh_battery()

    def update_device_status(self) -> None:
        d = self.selected_device
        if not d:
            self.device_status.setText('No device selected')
            return
        self.mode_label.setText(d.mode)
        self.device_status.setText(f'{d.name}\n{d.label}')
        self.update_tray_text()

    def device(self) -> SagaDevice:
        if not self.selected_device:
            raise RuntimeError('No Saga Pro native config device selected')
        return SagaDevice(self.selected_device.path)

    def refresh_battery(self) -> None:
        if not self.selected_device:
            return
        try:
            status, responses = self.device().battery_status(seconds=1.0)
            if status is None or status.percent is None:
                self.battery_label.setText('Unknown')
                self.power_label.setText('Unknown')
                self.temperature_label.setText('Unknown')
                self.voltage_label.setText('Unknown')
                self.raw_battery_label.setText('No 51 02 response')
                self.log('Battery query returned no 51 02 battery response.')
                for r in responses:
                    self.log(f'  response: {format_report(r, 24)}')
            else:
                self.last_battery = status.percent
                self.battery_label.setText(f'{status.percent}%')
                self.power_label.setText(status.charging_text)
                if status.temperature_c is not None:
                    self.temperature_label.setText(f'{status.temperature_c} °C')
                else:
                    self.temperature_label.setText('Unknown')
                if status.voltage_mv is not None:
                    self.voltage_label.setText(f'{status.voltage_mv} mV')
                else:
                    self.voltage_label.setText('Unknown')
                self.raw_battery_label.setText(status.raw_hex(16))
                self.log(
                    'Battery: ' +
                    f'{status.percent}% | {status.charging_text} | ' +
                    f'state=0x{status.state_candidate:02x} ' +
                    f'temperature={status.temperature_c}C ' +
                    f'voltage={status.voltage_mv}mV | ' +
                    f'raw={status.raw_hex(16)}'
                )
            if status is not None:
                self.check_low_battery_warning(status)
            self.update_tray_text()
        except PermissionError as exc:
            self.show_error('Permission denied', 'Cannot open hidraw device. Install the udev rule, then unplug/replug the mouse or dongle.')
        except Exception as exc:
            self.show_error('Battery refresh failed', exc)


    def save_low_battery_settings(self) -> None:
        self.settings['low_battery_enabled'] = bool(self.low_battery_enabled_check.isChecked())
        self.settings['low_battery_threshold'] = int(self.low_battery_threshold_spin.value())
        self.settings['low_battery_repeat_minutes'] = int(self.low_battery_repeat_spin.value())
        self.settings['low_battery_only_on_battery'] = bool(self.low_battery_only_on_battery_check.isChecked())
        save_settings(self.settings)

    def test_low_battery_notification(self) -> None:
        threshold = int(self.low_battery_threshold_spin.value())
        battery = self.last_battery if self.last_battery is not None else threshold
        self.show_low_battery_notification(battery, threshold, test=True)

    def show_low_battery_notification(self, percent: int, threshold: int, test: bool = False) -> None:
        title = 'HyperX Saga battery low' if not test else 'HyperX Saga battery notification test'
        msg = f'Mouse battery is at {percent}%. Warning threshold: {threshold}%.'
        if self.selected_device:
            msg += f'\nMode: {self.selected_device.mode}'
        if self.tray and self.tray.isVisible():
            self.tray.showMessage(title, msg, QSystemTrayIcon.MessageIcon.Warning, 8000)
        else:
            QMessageBox.warning(self, title, msg)
        self.log(f'{title}: {msg.replace(chr(10), " | ")}')

    def check_low_battery_warning(self, status) -> None:
        if status is None or status.percent is None:
            return
        if not self.low_battery_enabled_check.isChecked():
            self.low_battery_active = False
            return

        threshold = int(self.low_battery_threshold_spin.value())
        repeat_seconds = int(self.low_battery_repeat_spin.value()) * 60
        only_on_battery = self.low_battery_only_on_battery_check.isChecked()

        on_battery = status.state_candidate == 0x00
        if only_on_battery and not on_battery:
            # Do not warn while charging or full. Reset so a future unplugged low state can notify.
            self.low_battery_active = False
            return

        if status.percent > threshold:
            self.low_battery_active = False
            return

        now = time.monotonic()
        should_notify = (not self.low_battery_active) or (now - self.last_low_battery_notify_mono >= repeat_seconds)
        if should_notify:
            self.show_low_battery_notification(status.percent, threshold)
            self.last_low_battery_notify_mono = now
            self.low_battery_active = True

    def on_auto_battery_toggled(self, checked: bool) -> None:
        if checked:
            self.battery_timer.start()
            self.refresh_battery()
        else:
            self.battery_timer.stop()

    def update_tray_text(self) -> None:
        if not self.tray:
            return
        mode = self.selected_device.mode if self.selected_device else 'no device'
        batt = f'{self.last_battery}%' if self.last_battery is not None else 'battery unknown'
        power = getattr(self, 'power_label', None)
        power_text = power.text() if power is not None else ''
        self.tray.setToolTip(f'{APP_NAME}\n{mode}\n{batt}\n{power_text}')
        action = getattr(self, 'battery_menu_action', None)
        if action is not None:
            action.setText(f'Battery: {batt} ({mode})')

    def set_color(self, color: QColor) -> None:
        if not color.isValid():
            return
        self.current_color = color
        name = color.name().lower()
        self.color_button.setText(name)
        self.color_button.setStyleSheet(f'QPushButton {{ background-color: {name}; color: {self._text_color_for(color)}; font-weight: bold; }}')

    @staticmethod
    def _text_color_for(color: QColor) -> str:
        luminance = (0.2126 * color.red() + 0.7152 * color.green() + 0.0722 * color.blue())
        return '#000000' if luminance > 140 else '#ffffff'

    def pick_color(self) -> None:
        color = QColorDialog.getColor(self.current_color, self, 'Choose HyperX RGB color', QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if color.isValid():
            self.set_color(color)

    def apply_live_rgb(self) -> None:
        try:
            color = self.current_color.name().lower()
            brightness = self.brightness_spin.value()
            responses = self.device().set_live_rgb(color, brightness)
            self.log(f'Applied live RGB {color} brightness={brightness}%. Responses={len(responses)}')
        except Exception as exc:
            self.show_error('Live RGB failed', exc)

    def save_rgb_profile(self) -> None:
        try:
            color = self.current_color.name().lower()
            brightness = self.brightness_spin.value()
            responses = self.device().save_rgb_profile(color, brightness)
            self.log(f'Saved onboard RGB profile {color} brightness={brightness}%. Responses={len(responses)}')
        except Exception as exc:
            self.show_error('RGB profile save failed', exc)

    def update_polling_options(self) -> None:
        if not hasattr(self, 'polling_combo'):
            return
        current = int(self.polling_combo.currentData() or self.settings.get('default_polling_rate', 1000)) if self.polling_combo.count() else int(self.settings.get('default_polling_rate', 1000))
        mode = self.selected_device.mode if self.selected_device else 'unknown'
        rates = WIRELESS_POLLING_RATES if mode == 'wireless' else WIRED_POLLING_RATES
        self.polling_combo.blockSignals(True)
        self.polling_combo.clear()
        for rate in rates:
            suffix = ''
            if rate == 4000:
                suffix = ' (2.4 GHz wireless)'
            elif rate == 2000:
                suffix = ' (2.4 GHz wireless only)'
            self.polling_combo.addItem(f'{rate} Hz{suffix}', rate)
        idx = self.polling_combo.findData(current)
        if idx < 0:
            idx = self.polling_combo.findData(1000)
        if idx >= 0:
            self.polling_combo.setCurrentIndex(idx)
        self.polling_combo.blockSignals(False)
        if hasattr(self, 'polling_status_label'):
            if mode == 'wireless':
                self.polling_status_label.setText('Wireless mode: 4000, 2000, 1000, 500, 250, and 125 Hz are available. 4000 Hz and 2000 Hz are wireless-only; 500/250/125 use the same interval-code formula.')
            elif mode == 'wired':
                self.polling_status_label.setText('Wired mode: 1000, 500, 250, and 125 Hz are available. 2000 Hz and 4000 Hz are hidden because they are wireless-only on the Saga Pro.')
            else:
                self.polling_status_label.setText('Select or connect a Saga Pro config device to choose valid polling rates.')

    def selected_polling_rate(self) -> int:
        return int(self.polling_combo.currentData() or 1000)

    def validate_polling_mode(self, polling: int) -> None:
        if self.selected_device is not None and self.selected_device.mode != 'wireless' and polling in WIRELESS_ONLY_POLLING_RATES:
            raise RuntimeError('2000 Hz and 4000 Hz are wireless-only on the Saga Pro. Switch to 2.4 GHz wireless mode, or choose 1000 Hz or lower.')

    def save_default_polling_setting(self) -> None:
        self.settings['default_polling_rate'] = self.selected_polling_rate()
        save_settings(self.settings)

    def save_dpi_profile(self) -> None:
        try:
            dpis = [s.value() for s in self.dpi_spins]
            active = int(self.active_stage_combo.currentData())
            polling = self.selected_polling_rate()
            self.validate_polling_mode(polling)
            responses = self.device().save_dpi_profile(dpis, active_stage=active, polling_hz=polling)
            self.log(f'Saved DPI profile dpis={dpis} active_stage={active} polling={polling}Hz. Responses={len(responses)}')
        except Exception as exc:
            self.show_error('DPI profile save failed', exc)

    def save_polling_profile(self) -> None:
        try:
            dpis = [s.value() for s in self.dpi_spins]
            active = int(self.active_stage_combo.currentData())
            polling = self.selected_polling_rate()
            self.validate_polling_mode(polling)
            color = self.current_color.name().lower()
            brightness = self.brightness_spin.value()
            responses = self.device().save_polling_profile(
                dpis=dpis,
                active_stage=active,
                polling_hz=polling,
                color=color,
                brightness_percent=brightness,
            )
            self.settings['polling_hz'] = polling
            save_settings(self.settings)
            self.log(f'Saved polling profile polling={polling}Hz with RGB={color} brightness={brightness}% dpis={dpis} active_stage={active}. Responses={len(responses)}')
            if polling in (2000, 4000):
                self.polling_status_label.setText(f'Saved {polling} Hz wireless polling. Reconnect/measure to verify if needed.')
            else:
                self.polling_status_label.setText(f'Saved {polling} Hz polling.')
        except Exception as exc:
            self.show_error('Polling profile save failed', exc)

    def apply_all_to_mouse(self) -> None:
        self.save_profile_from_ui()
        self.save_dpi_profile()
        self.save_rgb_profile()

    def apply_last_profile_from_tray(self) -> None:
        try:
            name = self.profile_combo.currentText() or 'Default'
            self.load_profile_to_ui(name)
            self.apply_all_to_mouse()
        except Exception as exc:
            self.show_error('Apply profile failed', exc)

    def closeEvent(self, event):  # type: ignore[override]
        if self.tray and self.tray.isVisible():
            event.ignore()
            self.hide()
            self.tray.showMessage(APP_NAME, 'Still running in the system tray.', QSystemTrayIcon.MessageIcon.Information, 2500)
        else:
            super().closeEvent(event)


class SagaApplication:
    def __init__(self, argv: list[str]):
        self.app = QApplication(argv)
        self.app.setApplicationName(APP_NAME)
        self.app.setDesktopFileName(APP_ID)
        self.app.setQuitOnLastWindowClosed(False)
        self.icon = resource_icon()
        self.tray = QSystemTrayIcon(self.icon)
        self.window = MainWindow(tray=self.tray)
        self._build_tray()

    def _build_tray(self) -> None:
        menu = QMenu()
        battery_status_action = QAction('Battery: unknown')
        battery_status_action.setEnabled(False)
        self.window.battery_menu_action = battery_status_action
        open_action = QAction('Open Control Panel')
        open_action.triggered.connect(self.show_window)
        battery_action = QAction('Refresh Battery')
        battery_action.triggered.connect(self.window.refresh_battery)
        apply_action = QAction('Apply Selected Profile to Mouse')
        apply_action.triggered.connect(self.window.apply_last_profile_from_tray)
        quit_action = QAction('Quit')
        quit_action.triggered.connect(self.app.quit)
        menu.addAction(battery_status_action)
        menu.addSeparator()
        menu.addAction(open_action)
        menu.addAction(battery_action)
        menu.addAction(apply_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()
        self.window.update_tray_text()

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.show_window()

    def show_window(self) -> None:
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def run(self, start_minimized: bool) -> int:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.window.show()
        elif not start_minimized:
            self.window.show()
        return self.app.exec()


def parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description='HyperX Pulsefire Saga Pro control tray application')
    ap.add_argument('--start-minimized', action='store_true', help='start directly in the tray')
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    args = parse_args(argv)
    qt_argv = [sys.argv[0]]
    app = SagaApplication(qt_argv)
    return app.run(start_minimized=args.start_minimized)


if __name__ == '__main__':
    raise SystemExit(main())
