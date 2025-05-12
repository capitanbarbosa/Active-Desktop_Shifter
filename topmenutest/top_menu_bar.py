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
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
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
        parent_menubar = self.window()  # Get the TopMenuBar instance

        if not hasattr(parent_menubar, 'last_active_app_hwnd'):
            print("Error: Parent menubar does not have 'last_active_app_hwnd' attribute.")
            return

        hwnd_to_move = parent_menubar.last_active_app_hwnd
        menubar_hwnd = parent_menubar.winId().__int__()

        if not hwnd_to_move:
            print(
                "No active application window recorded to move. Please focus an application window first.")
            # Optional: Attempt a fallback to AppView.current() but be wary
            try:
                print(
                    "Debug: No last_active_app_hwnd, attempting fallback to AppView.current()...")
                current_app_view = AppView.current()
                if current_app_view and current_app_view.hwnd and current_app_view.hwnd != menubar_hwnd:
                    hwnd_to_move = current_app_view.hwnd
                    print(
                        f"Debug: Fallback AppView.current() identified HWND: {hwnd_to_move} (Title: '{win32gui.GetWindowText(hwnd_to_move)}')")
                else:
                    current_title = win32gui.GetWindowText(
                        win32gui.GetForegroundWindow()) if win32gui.GetForegroundWindow() else "N/A"
                    print(
                        f"Debug: Fallback AppView.current() failed or identified the menubar (Current Foreground: '{current_title}'). Aborting move.")
                    return
            except Exception as e_fallback:
                print(
                    f"Debug: Fallback to AppView.current() failed: {e_fallback}")
                return

        if hwnd_to_move == menubar_hwnd:
            print("Error: The window to move is the menu bar itself (last_active_app_hwnd pointed to menubar). Aborting.")
            return

        try:
            window_title = win32gui.GetWindowText(hwnd_to_move)
            print(
                f"Attempting to move window HWND: {hwnd_to_move} (Title: '{window_title}') to desktop {self.desktop_number}")

            # Create AppView directly with the HWND
            app_to_move = AppView(hwnd=hwnd_to_move)
            target_desktop = VirtualDesktop(self.desktop_number)
            app_to_move.move(target_desktop)
            print(
                f"Successfully moved window (HWND: {hwnd_to_move}, Title: '{window_title}') to desktop {self.desktop_number}.")

        except Exception as e:
            title_on_error = "N/A"
            try:
                title_on_error = win32gui.GetWindowText(hwnd_to_move)
            except:
                pass
            print(
                f"Error moving window (HWND: {hwnd_to_move}, Title: '{title_on_error}') to desktop {self.desktop_number}: {e}")
            if "Element not found" in str(e):
                print(
                    "   This might mean the recorded HWND is no longer valid, not a top-level window, or not compatible with pyvda.")
            # HRESULT 0x800401E4 - MK_E_SYNTAX
            elif hasattr(e, 'args') and e.args and e.args[0] == -2147221020:
                print("   This specific error (MK_E_SYNTAX) can sometimes indicate the window is not suitable for virtual desktop operations (e.g., a child window or certain types of tool windows).")


class TopMenuBar(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Top Menu Bar")

        # self.setWindowFlags(...) should be called AFTER we have a HWND if we want to modify it with win32gui,
        # but for this strategy, we are removing the direct win32gui manipulation of WS_EX_NOACTIVATE here.

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )

        self.last_active_app_hwnd = None
        # Parent to self for auto-cleanup
        self.focus_check_timer = QTimer(self)
        self.focus_check_timer.timeout.connect(
            self.update_last_active_app_hwnd)
        self.focus_check_timer.start(250)  # Check every 250ms

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
            self.winId().__int__(),  # winId() should be valid here
            win32con.GWL_WNDPROC,
            self.win_event_proc
        )
        # It's possible that SetWindowLong for GWL_WNDPROC or register_appbar resets EX_STYLE.
        # If WS_EX_NOACTIVATE doesn't stick, we might need to re-apply it later, e.g., in a showEvent.

        # Set up shift key monitoring
        self.shift_pressed = False
        self.setup_shift_monitoring()

    def update_last_active_app_hwnd(self):
        try:
            current_fg_hwnd = win32gui.GetForegroundWindow()
            # Ensure self.winId() is valid before trying to get an int from it
            # It might not be fully initialized when the timer first fires.
            if not self.winId():
                return
            menubar_hwnd = self.winId().__int__()

            if current_fg_hwnd != 0 and current_fg_hwnd != menubar_hwnd:
                # Check if it's a visible, top-level, enabled window
                # This helps filter out some unsuitable windows (e.g., hidden helper windows)
                if win32gui.IsWindowVisible(current_fg_hwnd) and \
                   win32gui.IsWindowEnabled(current_fg_hwnd) and \
                   win32gui.GetParent(current_fg_hwnd) == 0:  # Check if it's a top-level window

                    if self.last_active_app_hwnd != current_fg_hwnd:
                        try:
                            # title = win32gui.GetWindowText(current_fg_hwnd)
                            # print(f"Debug: last_active_app_hwnd updated to {current_fg_hwnd} (Title: '{title}')")
                            pass  # Keep debug print commented for now to avoid noise
                        except Exception:  # If GetWindowText fails for some reason
                            # print(f"Debug: last_active_app_hwnd updated to {current_fg_hwnd} (Could not get title)")
                            pass
                        self.last_active_app_hwnd = current_fg_hwnd
        except Exception as e:
            # print(f"Minor error in update_last_active_app_hwnd: {e}")
            pass  # Keep it silent unless actively debugging this part

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
