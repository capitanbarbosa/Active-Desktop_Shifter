import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QLabel, QPushButton, QSystemTrayIcon, QMenu)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QIcon, QFont
import psutil
import win32gui
import win32con
import win32api
import ctypes
from ctypes import wintypes
from pyvda import VirtualDesktop, AppView
import time

# Import components
from desktop_switcher import DesktopButton
from system_stats import SystemStats
from start_menu import StartButton
from search_bar import SearchButton
from appbar_manager import AppBarManager
from active_task import ActiveTaskWidget
from persistence_manager import PersistenceManager
from file_launcher import FileLauncherWidget

# Import constants
from constants import DESKTOP_NAMES, ABM_NEW, ABM_REMOVE, ABM_QUERYPOS, ABM_SETPOS, ABE_TOP # ABE_BOTTOM is not used in app.py

# Windows API constants and structures are now in constants.py
# DESKTOP_NAMES is now in constants.py

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
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )

        self.last_active_app_hwnd = None
        self.focus_check_timer = QTimer(self)
        self.focus_check_timer.timeout.connect(
            self.update_last_active_app_hwnd)
        self.focus_check_timer.start(250)

        # Attempt to set current_desktop_number reliably before ActiveTaskWidget init
        try:
            self.current_desktop_number = VirtualDesktop.current().number
        except Exception:
            # print("Initial desktop query failed in TopMenuBar, defaulting to 0") # Optional: for debugging
            self.current_desktop_number = 0 

        screen = QApplication.primaryScreen().geometry()
        self.bar_height = 40

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(10)

        # Start button component
        self.start_button_widget = StartButton(self)
        layout.addWidget(self.start_button_widget)

        # Search button component
        self.search_button_widget = SearchButton(self)
        layout.addWidget(self.search_button_widget)

        self.desktop_buttons = []
        for i in range(1, 8):  # 7 desktops
            btn = DesktopButton(i, self)
            self.desktop_buttons.append(btn)
            layout.addWidget(btn)

        # Initialize PersistenceManager
        self.persistence_manager = PersistenceManager()

        # Add the Active Task widget here
        self.active_task_widget = ActiveTaskWidget(self, self.persistence_manager)
        layout.addWidget(self.active_task_widget)

        # Add a stretching space to push right-side widgets to the right
        layout.addStretch(1)

        # Add the File Launcher widget (now on the right)
        self.file_launcher_widget = FileLauncherWidget(self)
        layout.addWidget(self.file_launcher_widget)

        # System stats widget (on the far right)
        self.stats_widget = SystemStats(self)
        layout.addWidget(self.stats_widget)

        # Update timer for desktop highlighting (stats timer is in SystemStats)
        self.desktop_highlight_timer = QTimer(self)
        self.desktop_highlight_timer.timeout.connect(self.update_desktop_button_states)
        self.desktop_highlight_timer.start(1000)

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

        # Initialize AppBarManager
        self.app_bar_manager = AppBarManager(self, self.bar_height)

        self.shift_pressed = False
        self.setup_shift_monitoring()

    def update_last_active_app_hwnd(self):
        try:
            current_fg_hwnd = win32gui.GetForegroundWindow()
            if not self.winId():
                return
            menubar_hwnd = self.winId().__int__()

            if current_fg_hwnd != 0 and current_fg_hwnd != menubar_hwnd:
                if win32gui.IsWindowVisible(current_fg_hwnd) and \
                   win32gui.IsWindowEnabled(current_fg_hwnd) and \
                   win32gui.GetParent(current_fg_hwnd) == 0:
                    if self.last_active_app_hwnd != current_fg_hwnd:
                        self.last_active_app_hwnd = current_fg_hwnd
        except Exception as e:
            pass

    def setup_shift_monitoring(self):
        self.shift_timer = QTimer()
        self.shift_timer.timeout.connect(self.check_shift_state)
        self.shift_timer.start(100)

    def check_shift_state(self):
        shift_state = win32api.GetKeyState(win32con.VK_SHIFT)
        is_pressed = shift_state < 0

        if is_pressed != self.shift_pressed:
            self.shift_pressed = is_pressed
            for btn in self.desktop_buttons:
                btn.shift_clicked = is_pressed
                # Update button style based on shift state
                if is_pressed:
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #0077CC; /* Blue when shift is pressed */
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 5px;
                        }
                        QPushButton:hover {
                            background-color: #005fa3; /* Darker blue on hover */
                        }
                        QPushButton:checked {
                            background-color: #F40000; /* Keep checked color */
                        }
                    """)
                else:
                    # Reset to default style (ensure this matches DesktopButton's default)
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #3f4652;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 5px;
                        }
                        QPushButton:hover {
                            background-color: #4D4D4D;
                        }
                        QPushButton:checked {
                            background-color: #F40000;
                        }
                    """)

    def update_desktop_button_states(self):
        # Update desktop button states
        try:
            current_desktop = VirtualDesktop.current()
            current_number = current_desktop.number
            
            # Check if desktop has changed
            if current_number != self.current_desktop_number:
                self.current_desktop_number = current_number
                # Update the active task when desktop changes
                self.active_task_widget.on_desktop_changed()
            
            # Update button highlighting
            for btn in self.desktop_buttons:
                btn.setChecked(btn.desktop_number == current_number)
        except Exception as e:
            print(f"Error updating desktop states: {e}")

    def closeEvent(self, event):
        # Unregister app bar
        if hasattr(self, 'app_bar_manager') and self.app_bar_manager:
            self.app_bar_manager.unregister()

        if self.focus_check_timer:
            self.focus_check_timer.stop()
        if self.shift_timer: # Stop shift_timer
            self.shift_timer.stop()
        if self.desktop_highlight_timer: # Ensure this new timer is stopped
            self.desktop_highlight_timer.stop()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = TopMenuBar()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 