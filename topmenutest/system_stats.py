from PyQt6.QtWidgets import QLabel, QHBoxLayout, QWidget
from PyQt6.QtCore import QTimer
import psutil

class SystemStats(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)

        self.cpu_label = QLabel("CPU: 0%")
        self.mem_label = QLabel("MEM: 0%")

        self.layout.addWidget(self.cpu_label)
        self.layout.addWidget(self.mem_label)

        # Timer for stats updates
        self.stats_update_timer = QTimer(self)
        self.stats_update_timer.timeout.connect(self.update_labels)
        self.stats_update_timer.start(1000) # Update every second

        self.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 12px;
            }
        """)
        self.update_labels() # Initial update

    def update_labels(self):
        cpu_percent = psutil.cpu_percent()
        mem_percent = psutil.virtual_memory().percent
        self.cpu_label.setText(f"CPU: {cpu_percent}%")
        self.mem_label.setText(f"MEM: {mem_percent}%")

    def get_cpu_label(self):
        return self.cpu_label
    
    def get_mem_label(self):
        return self.mem_label 