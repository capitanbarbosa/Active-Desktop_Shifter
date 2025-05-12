from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt
from pyvda import VirtualDesktop, AppView
import win32gui
import win32api # Added for GetKeyState
import win32con # Added for VK_SHIFT

# Import DESKTOP_NAMES from constants.py
from constants import DESKTOP_NAMES


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
        self.shift_clicked = False # This will be updated by TopMenuBar

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
        parent_menubar = self.window()

        if not hasattr(parent_menubar, 'last_active_app_hwnd'):
            print("Error: Parent menubar does not have 'last_active_app_hwnd' attribute.")
            return

        hwnd_to_move = parent_menubar.last_active_app_hwnd
        # Ensure parent_menubar.winId() is valid before calling __int__()
        if not parent_menubar.winId():
            print("Error: Parent menubar window ID is not valid yet.")
            return
        menubar_hwnd = parent_menubar.winId().__int__()


        if not hwnd_to_move:
            print(
                "No active application window recorded to move. Please focus an application window first.")
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

