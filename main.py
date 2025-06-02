import sys
import json
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QPushButton, QHBoxLayout, QProgressBar, QSpinBox, QLineEdit, QFrame
)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon

SAVE_FILE = "timers.json"

def get_running_path(relative_path):
    if '_internal' in os.listdir():
        return os.path.join('_internal', relative_path)
    else:
        return relative_path

class TimerWidget(QWidget):
    def __init__(self, name, duration_seconds, remove_callback, parent=None):
        super().__init__(parent)
        self.name = name
        self.duration = duration_seconds
        self.remaining = duration_seconds
        self.remove_callback = remove_callback
        self.is_paused = False

        self.layout = QVBoxLayout()
        self.name_label = QLabel(f"Timer: {self.name}")
        self.label = QLabel(f"Time remaining: {self.remaining}s")
        self.progress = QProgressBar()
        self.progress.setRange(0, self.duration)
        self.progress.setValue(self.duration)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_timer)

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_timer)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_timer)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_timer)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.delete_button)

        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.progress)
        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

        self.timer = QTimer()
        self.timer.setInterval(1000)  # 1 second
        self.timer.timeout.connect(self.update_timer)

        self.flash_timer = QTimer()
        self.flash_timer.setInterval(500)
        self.flash_timer.timeout.connect(self.flash_background)
        self.flash_state = False

    def start_timer(self):
        if self.remaining <= 0:
            self.remaining = self.duration
        self.progress.setValue(self.remaining)
        self.label.setText(f"Time remaining: {self.remaining}s")
        self.is_paused = False
        self.timer.start()
        self.stop_flash()

    def pause_timer(self):
        if self.timer.isActive():
            self.timer.stop()
            self.is_paused = True

    def reset_timer(self):
        self.timer.stop()
        self.remaining = self.duration
        self.progress.setValue(self.remaining)
        self.label.setText(f"Time remaining: {self.remaining}s")
        self.is_paused = False
        self.stop_flash()

    def update_timer(self):
        self.remaining -= 1
        self.progress.setValue(self.remaining)
        self.label.setText(f"Time remaining: {self.remaining}s")

        if self.remaining <= 0:
            self.timer.stop()
            self.label.setText("Time's up!")
            self.start_flash()

    def start_flash(self):
        self.flash_state = False
        self.flash_timer.start()

    def stop_flash(self):
        self.flash_timer.stop()
        self.setStyleSheet("")

    def flash_background(self):
        if self.flash_state:
            self.setStyleSheet("background-color: white;")
        else:
            self.setStyleSheet("background-color: red;")
        self.flash_state = not self.flash_state

    def delete_timer(self):
        self.timer.stop()
        self.stop_flash()
        self.setParent(None)
        self.remove_callback(self)

    def to_dict(self):
        return {"name": self.name, "duration": self.duration}


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("pyMulti-Timer v" + open(get_running_path('version.txt')).read())
        self.setWindowIcon(QIcon(get_running_path('icon.ico')))

        self.layout = QVBoxLayout()

        # Timer name input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter timer name")
        self.layout.addWidget(QLabel("Timer name:"))
        self.layout.addWidget(self.name_input)

        # Timer duration selection (H:M:S)
        self.layout.addWidget(QLabel("Select timer duration (H:M:S):"))
        self.time_layout = QHBoxLayout()

        self.hours_input = QSpinBox()
        self.hours_input.setRange(0, 23)
        self.hours_input.setPrefix("H: ")
        self.time_layout.addWidget(self.hours_input)

        self.minutes_input = QSpinBox()
        self.minutes_input.setRange(0, 59)
        self.minutes_input.setPrefix("M: ")
        self.time_layout.addWidget(self.minutes_input)

        self.seconds_input = QSpinBox()
        self.seconds_input.setRange(0, 59)
        self.seconds_input.setPrefix("S: ")
        self.time_layout.addWidget(self.seconds_input)

        self.layout.addLayout(self.time_layout)

        # Add timer button
        self.add_timer_button = QPushButton("Add Timer")
        self.add_timer_button.clicked.connect(self.add_timer)
        self.layout.addWidget(self.add_timer_button)

        # Add a horizontal line as delimiter
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(line)

        self.timers_layout = QVBoxLayout()
        self.layout.addLayout(self.timers_layout)

        self.setLayout(self.layout)

        self.timers = []
        self.load_timers()

    def add_timer(self):
        name = self.name_input.text().strip()
        if not name:
            name = f"Timer {len(self.timers) + 1}"

        hours = self.hours_input.value()
        minutes = self.minutes_input.value()
        seconds = self.seconds_input.value()
        duration = hours * 3600 + minutes * 60 + seconds

        if duration <= 0:
            return

        timer_widget = TimerWidget(name, duration, self.remove_timer)
        self.timers_layout.addWidget(timer_widget)
        self.timers.append(timer_widget)
        self.save_timers()

    def remove_timer(self, timer_widget):
        if timer_widget in self.timers:
            self.timers.remove(timer_widget)
            self.save_timers()

    def save_timers(self):
        data = [timer.to_dict() for timer in self.timers]
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f)

    def load_timers(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                try:
                    data = json.load(f)
                    for entry in data:
                        timer_widget = TimerWidget(entry["name"], entry["duration"], self.remove_timer)
                        self.timers_layout.addWidget(timer_widget)
                        self.timers.append(timer_widget)
                except json.JSONDecodeError:
                    pass

    def closeEvent(self, event):
        self.save_timers()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(300, 600)
    window.show()
    sys.exit(app.exec())
