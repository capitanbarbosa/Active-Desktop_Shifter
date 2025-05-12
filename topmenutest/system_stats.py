from PyQt6.QtWidgets import QLabel, QHBoxLayout, QWidget
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFontMetrics
import psutil

class SystemStats(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)

        # Create labels with fixed width to prevent layout wobbling
        self.cpu_label = QLabel("CPU: 00%")
        self.mem_label = QLabel("MEM: 00%")
        
        # Calculate minimum width based on text with maximum expected value
        font_metrics = QFontMetrics(self.cpu_label.font())
        cpu_width = font_metrics.horizontalAdvance("CPU: 100%")
        mem_width = font_metrics.horizontalAdvance("MEM: 100%")
        
        # Set fixed width to prevent wobbling
        self.cpu_label.setFixedWidth(cpu_width)
        self.mem_label.setFixedWidth(mem_width)

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
        
        # Use right-aligned text with fixed width to prevent wobbling
        self.cpu_label.setText(f"CPU: {cpu_percent:2.0f}%")
        self.mem_label.setText(f"MEM: {mem_percent:2.0f}%")

    def get_cpu_label(self):
        return self.cpu_label
    
    def get_mem_label(self):
        return self.mem_label 