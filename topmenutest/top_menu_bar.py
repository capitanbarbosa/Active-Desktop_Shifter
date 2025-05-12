import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QLabel, QPushButton, QSystemTrayIcon, QMenu)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QIcon, QFont
import psutil
import datetime
import win32gui
import win32con
import win32api
import ctypes
from ctypes import wintypes

# Windows API constants and structures
ABM_NEW = 0
ABM_REMOVE = 1
ABM_QUERYPOS = 2
ABM_SETPOS = 3
ABE_TOP = 1
ABE_BOTTOM = 3


class APPBARDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uCallbackMessage", wintypes.UINT),
        ("uEdge", wintypes.UINT),
        ("rc", wintypes.RECT),
        ("lParam", wintypes.LPARAM),
    ]


class TopMenuBar(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Top Menu Bar")

        # Remove window frame and taskbar entry, but keep it as a regular window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )

        # Get screen dimensions
        screen = QApplication.primaryScreen().geometry()
        self.bar_height = 40  # Height of our menu bar

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(10)

        # Start button
        start_btn = QPushButton("Start")
        start_btn.setFixedSize(60, 30)
        start_btn.clicked.connect(self.show_start_menu)
        layout.addWidget(start_btn)

        # Search bar
        search_btn = QPushButton("Search")
        search_btn.setFixedSize(200, 30)
        search_btn.clicked.connect(self.show_search)
        layout.addWidget(search_btn)

        # Active windows
        self.windows_label = QLabel("Active Windows")
        layout.addWidget(self.windows_label)

        # System stats
        self.cpu_label = QLabel("CPU: 0%")
        self.mem_label = QLabel("MEM: 0%")
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.mem_label)

        # Time and date
        self.time_label = QLabel()
        self.update_time()
        layout.addWidget(self.time_label)

        # Update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

        # Set stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2D2D2D;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 12px;
            }
            QPushButton {
                background-color: #3D3D3D;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4D4D4D;
            }
        """)

        # Register as appbar
        self.register_appbar()

        # Set up window event handling
        self.old_win_event = win32gui.SetWindowLong(
            self.winId().__int__(),
            win32con.GWL_WNDPROC,
            self.win_event_proc
        )

    def register_appbar(self):
        # Initialize APPBARDATA structure
        self.appbar_data = APPBARDATA()
        self.appbar_data.cbSize = ctypes.sizeof(APPBARDATA)
        self.appbar_data.hWnd = self.winId().__int__()
        self.appbar_data.uEdge = ABE_TOP

        # Register the appbar
        ctypes.windll.shell32.SHAppBarMessage(
            ABM_NEW, ctypes.byref(self.appbar_data))

        # Set the appbar position
        self.update_appbar_position()

    def update_appbar_position(self):
        # Get screen dimensions
        screen = QApplication.primaryScreen().geometry()

        # Update the appbar position
        self.appbar_data.rc.left = 0
        self.appbar_data.rc.top = 0
        self.appbar_data.rc.right = screen.width()
        self.appbar_data.rc.bottom = self.bar_height

        # Query and set the position
        ctypes.windll.shell32.SHAppBarMessage(
            ABM_QUERYPOS, ctypes.byref(self.appbar_data))
        ctypes.windll.shell32.SHAppBarMessage(
            ABM_SETPOS, ctypes.byref(self.appbar_data))

        # Move our window to the appbar position
        self.setGeometry(
            self.appbar_data.rc.left,
            self.appbar_data.rc.top,
            self.appbar_data.rc.right - self.appbar_data.rc.left,
            self.appbar_data.rc.bottom - self.appbar_data.rc.top
        )

    def win_event_proc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_WINDOWPOSCHANGED:
            self.update_appbar_position()
        return win32gui.CallWindowProc(self.old_win_event, hwnd, msg, wparam, lparam)

    def closeEvent(self, event):
        # Unregister the appbar when closing
        ctypes.windll.shell32.SHAppBarMessage(
            ABM_REMOVE, ctypes.byref(self.appbar_data))
        super().closeEvent(event)

    def update_time(self):
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.time_label.setText(f"{current_date} {current_time}")

    def update_stats(self):
        cpu_percent = psutil.cpu_percent()
        mem_percent = psutil.virtual_memory().percent
        self.cpu_label.setText(f"CPU: {cpu_percent}%")
        self.mem_label.setText(f"MEM: {mem_percent}%")
        self.update_time()

    def show_start_menu(self):
        # TODO: Implement start menu
        pass

    def show_search(self):
        # TODO: Implement search functionality
        pass


def main():
    app = QApplication(sys.argv)
    window = TopMenuBar()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
