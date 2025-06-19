import sys
import json
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QPushButton, QHBoxLayout, QProgressBar, QSpinBox,
    QLineEdit, QListWidget, QListWidgetItem, QFrame,
    QDialog, QFormLayout, QDialogButtonBox
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon
from ag95 import format_from_seconds

SAVE_FILE = "timers.json"

def get_running_path(relative_path):
    if '_internal' in os.listdir():
        return os.path.join('_internal', relative_path)
    else:
        return relative_path

class TimerWidget(QWidget):
    def __init__(self, name, duration_seconds, remove_callback, save_callback, parent=None):
        super().__init__(parent)
        self.name = name
        self.duration = duration_seconds
        self.remaining = duration_seconds
        self.remove_callback = remove_callback
        self.save_callback = save_callback
        self.is_paused = False

        self.layout = QVBoxLayout()
        self.name_label = QLabel(f"Timer: {self.name}")
        self.label = QLabel(f"Time remaining: {format_from_seconds(self.remaining)} || {format_from_seconds(self.duration)}")
        self.progress = QProgressBar()
        self.progress.setRange(0, self.duration)
        self.progress.setValue(self.duration)

        # Control buttons
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_timer)
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_timer)
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_timer)
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_timer)
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_timer)

        button_layout = QHBoxLayout()
        for btn in (self.start_button, self.pause_button, self.reset_button, self.edit_button, self.delete_button):
            button_layout.addWidget(btn)

        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.progress)
        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

        # timers
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_timer)
        self.flash_timer = QTimer()
        self.flash_timer.setInterval(500)
        self.flash_timer.timeout.connect(self.flash_background)
        self.flash_state = False
        self.update_button_styles()

    def start_timer(self):
        if self.remaining <= 0:
            self.remaining = self.duration
        self.progress.setValue(self.remaining)
        self.label.setText(f"Time remaining: {format_from_seconds(self.remaining)} || {format_from_seconds(self.duration)}")
        self.is_paused = False
        self.timer.start()
        self.update_button_styles()
        self.stop_flash()

    def pause_timer(self):
        if self.timer.isActive():
            self.timer.stop()
            self.is_paused = True
            self.update_button_styles()

    def reset_timer(self):
        self.timer.stop()
        self.remaining = self.duration
        self.progress.setRange(0, self.duration)
        self.progress.setValue(self.remaining)
        self.label.setText(f"Time remaining: {format_from_seconds(self.remaining)} || {format_from_seconds(self.duration)}")
        self.is_paused = False
        self.update_button_styles()
        self.stop_flash()

    def update_timer(self):
        self.remaining -= 1
        self.progress.setValue(self.remaining)
        self.label.setText(f"Time remaining: {format_from_seconds(self.remaining)} || {format_from_seconds(self.duration)}")
        if self.remaining <= 0:
            self.timer.stop()
            self.label.setText("Time's up!")
            self.start_flash()

    def update_button_styles(self):
        print('update called')
        if self.timer.isActive() and not self.is_paused:
            # Running: Start gray‑out, Pause green
            self.start_button.setEnabled(False)
            self.start_button.setStyleSheet("background-color: lightgreen;")
            self.pause_button.setEnabled(True)
            self.pause_button.setStyleSheet("background-color: lightgray;")
        elif self.is_paused:
            # Paused: Start green, Pause gray
            self.start_button.setEnabled(True)
            self.start_button.setStyleSheet("background-color: lightgray;")
            self.pause_button.setEnabled(False)
            self.pause_button.setStyleSheet("background-color: lightyellow;")
        else:
            # Stopped / reset: both neutral
            for btn in (self.start_button, self.pause_button):
                btn.setEnabled(True)
                btn.setStyleSheet("")

    def start_flash(self):
        self.flash_state = False
        self.flash_timer.start()

    def stop_flash(self):
        self.flash_timer.stop()
        self.setStyleSheet("")

    def flash_background(self):
        self.setStyleSheet("background-color: red;" if not self.flash_state else "background-color: white;")
        self.flash_state = not self.flash_state

    def delete_timer(self):
        self.timer.stop()
        self.stop_flash()
        self.setParent(None)
        self.remove_callback(self)

    def to_dict(self):
        return {"name": self.name, "duration": self.duration}

    def edit_timer(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Timer")
        form = QFormLayout(dialog)
        name_edit = QLineEdit(self.name)
        h_spin = QSpinBox(); h_spin.setRange(0, 23); h_spin.setValue(self.duration // 3600)
        m_spin = QSpinBox(); m_spin.setRange(0, 59); m_spin.setValue((self.duration % 3600) // 60)
        s_spin = QSpinBox(); s_spin.setRange(0, 59); s_spin.setValue(self.duration % 60)
        form.addRow("Name:", name_edit)
        form.addRow("Hours:", h_spin)
        form.addRow("Minutes:", m_spin)
        form.addRow("Seconds:", s_spin)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            # update timer
            self.name = name_edit.text().strip() or self.name
            self.duration = h_spin.value() * 3600 + m_spin.value() * 60 + s_spin.value()
            self.remaining = self.duration
            self.name_label.setText(f"Timer: {self.name}")
            self.progress.setRange(0, self.duration)
            self.progress.setValue(self.duration)
            self.label.setText(f"Time remaining: {format_from_seconds(self.remaining)} || {format_from_seconds(self.duration)}")
            self.save_callback()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("pyMulti-Timer v" + open(get_running_path('version.txt')).read())
        self.setWindowIcon(QIcon(get_running_path('icon.ico')))
        self.layout = QVBoxLayout(self)

        # input fields
        self.name_input = QLineEdit(); self.name_input.setPlaceholderText("Enter timer name")
        self.hours_input = QSpinBox(); self.hours_input.setRange(0,23); self.hours_input.setPrefix("H: ")
        self.minutes_input = QSpinBox(); self.minutes_input.setRange(0,59); self.minutes_input.setPrefix("M: ")
        self.seconds_input = QSpinBox(); self.seconds_input.setRange(0,59); self.seconds_input.setPrefix("S: ")
        self.add_button = QPushButton("Add Timer"); self.add_button.clicked.connect(self.add_timer)

        self.layout.addWidget(QLabel("Timer name:")); self.layout.addWidget(self.name_input)
        self.layout.addWidget(QLabel("Select timer duration (H:M:S):"))
        tlay = QHBoxLayout(); tlay.addWidget(self.hours_input); tlay.addWidget(self.minutes_input); tlay.addWidget(self.seconds_input)
        self.layout.addLayout(tlay); self.layout.addWidget(self.add_button)

        line = QFrame(); line.setFrameShape(QFrame.HLine); self.layout.addWidget(line)

        # use QListWidget for drag & drop
        self.list = QListWidget()
        self.list.setDragDropMode(QListWidget.InternalMove)
        self.list.model().rowsMoved.connect(self.save_timers)
        self.layout.addWidget(self.list)

        self.load_timers()

    def add_timer(self):
        name = self.name_input.text().strip() or f"Timer {self.list.count()+1}"
        secs = self.hours_input.value()*3600 + self.minutes_input.value()*60 + self.seconds_input.value()
        if secs <= 0:
            return
        widget = TimerWidget(name, secs, remove_callback=self.on_delete, save_callback=self.save_timers)
        item = QListWidgetItem(); item.setSizeHint(widget.sizeHint())
        self.list.addItem(item); self.list.setItemWidget(item, widget)
        self.save_timers()

    def on_delete(self, timer_widget):
        for i in range(self.list.count()):
            item = self.list.item(i)
            if self.list.itemWidget(item) is timer_widget:
                self.list.takeItem(i)
                break
        self.save_timers()

    def save_timers(self, *args):
        data = []
        for i in range(self.list.count()):
            w = self.list.itemWidget(self.list.item(i))
            data.append(w.to_dict())
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def load_timers(self):
        if not os.path.exists(SAVE_FILE):
            return
        try:
            with open(SAVE_FILE) as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return
        for entry in data:
            w = TimerWidget(entry['name'], entry['duration'], remove_callback=self.on_delete, save_callback=self.save_timers)
            item = QListWidgetItem(); item.setSizeHint(w.sizeHint())
            self.list.addItem(item); self.list.setItemWidget(item, w)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(500, 600)
    win.show()
    sys.exit(app.exec())
