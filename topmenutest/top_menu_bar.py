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

# Windows API constants and structures
ABM_NEW = 0
ABM_REMOVE = 1
ABM_QUERYPOS = 2
ABM_SETPOS = 3
ABE_TOP = 1
ABE_BOTTOM = 3

# Desktop names from Active-DesktopSwitcher
DESKTOP_NAMES = {
    1: "Log",
    2: "dev",
    3: "miw1",
    4: "miw2",
    5: "media",
    6: "media 2",
    7: "make"
}


class APPBARDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uCallbackMessage", wintypes.UINT),
        ("uEdge", wintypes.UINT),
        ("rc", wintypes.RECT),
        ("lParam", wintypes.LPARAM),
    ]


class DesktopButton(QPushButton):
    def __init__(self, desktop_number, parent=None):
        super().__init__(parent)
        self.desktop_number = desktop_number
        self.setFixedSize(60, 30)
        self.setText(DESKTOP_NAMES.get(desktop_number, str(desktop_number)))
        self.setStyleSheet("""
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
        self.setCheckable(True)
        self.clicked.connect(self.switch_desktop)
        self.shift_clicked = False

    def switch_desktop(self):
        if self.shift_clicked:
            self.move_window_to_desktop()
        else:
            self.go_to_desktop()

    def go_to_desktop(self):
        try:
            VirtualDesktop(self.desktop_number).go()
        except Exception as e:
            print(f"Desktop switch error ({self.desktop_number}): {e}")

    def move_window_to_desktop(self):
        try:
            current_window = AppView.current()
            target_desktop = VirtualDesktop(self.desktop_number)
            current_window.move(target_desktop)
        except Exception as e:
            print(f"Error moving window to desktop {self.desktop_number}: {e}")


class TopMenuBar(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Top Menu Bar")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )

        # Get screen dimensions
        screen = QApplication.primaryScreen().geometry()
        self.bar_height = 40

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

        # Desktop switcher buttons
        self.desktop_buttons = []
        for i in range(1, 8):  # 7 desktops
            btn = DesktopButton(i)
            self.desktop_buttons.append(btn)
            layout.addWidget(btn)

        # System stats
        self.cpu_label = QLabel("CPU: 0%")
        self.mem_label = QLabel("MEM: 0%")
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.mem_label)

        # Update timer for stats and desktop highlighting
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

        # Set up shift key monitoring
        self.shift_pressed = False
        self.setup_shift_monitoring()

    def setup_shift_monitoring(self):
        # Create a timer to check shift key state
        self.shift_timer = QTimer()
        self.shift_timer.timeout.connect(self.check_shift_state)
        self.shift_timer.start(100)  # Check every 100ms

    def check_shift_state(self):
        shift_state = win32api.GetKeyState(win32con.VK_SHIFT)
        is_pressed = shift_state < 0

        if is_pressed != self.shift_pressed:
            self.shift_pressed = is_pressed
            for btn in self.desktop_buttons:
                btn.shift_clicked = is_pressed
                if is_pressed:
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #0077CC;
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
                else:
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

    def update_stats(self):
        # Update CPU and memory usage
        cpu_percent = psutil.cpu_percent()
        mem_percent = psutil.virtual_memory().percent
        self.cpu_label.setText(f"CPU: {cpu_percent}%")
        self.mem_label.setText(f"MEM: {mem_percent}%")

        # Update desktop button states
        try:
            current_desktop = VirtualDesktop.current()
            current_number = current_desktop.number
            for btn in self.desktop_buttons:
                btn.setChecked(btn.desktop_number == current_number)
        except Exception as e:
            print(f"Error updating desktop states: {e}")

    def register_appbar(self):
        self.appbar_data = APPBARDATA()
        self.appbar_data.cbSize = ctypes.sizeof(APPBARDATA)
        self.appbar_data.hWnd = self.winId().__int__()
        self.appbar_data.uEdge = ABE_TOP
        ctypes.windll.shell32.SHAppBarMessage(
            ABM_NEW, ctypes.byref(self.appbar_data))
        self.update_appbar_position()

    def update_appbar_position(self):
        screen = QApplication.primaryScreen().geometry()
        self.appbar_data.rc.left = 0
        self.appbar_data.rc.top = 0
        self.appbar_data.rc.right = screen.width()
        self.appbar_data.rc.bottom = self.bar_height
        ctypes.windll.shell32.SHAppBarMessage(
            ABM_QUERYPOS, ctypes.byref(self.appbar_data))
        ctypes.windll.shell32.SHAppBarMessage(
            ABM_SETPOS, ctypes.byref(self.appbar_data))
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
        ctypes.windll.shell32.SHAppBarMessage(
            ABM_REMOVE, ctypes.byref(self.appbar_data))
        super().closeEvent(event)

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
