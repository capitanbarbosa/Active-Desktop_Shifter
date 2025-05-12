from PyQt6.QtCore import QCoreApplication
import ctypes
from ctypes import wintypes
import win32gui
import win32con
import win32api
from constants import ABM_NEW, ABM_REMOVE, ABM_QUERYPOS, ABM_SETPOS, ABE_TOP

class APPBARDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uCallbackMessage", wintypes.UINT),
        ("uEdge", wintypes.UINT),
        ("rc", wintypes.RECT),
        ("lParam", wintypes.LPARAM),
    ]

class AppBarManager:
    def __init__(self, window, bar_height=40):
        self.window = window
        self.bar_height = bar_height
        self.appbar_data = APPBARDATA()
        self.appbar_data.cbSize = ctypes.sizeof(APPBARDATA)
        self.appbar_data.hWnd = self.window.winId().__int__()
        self.appbar_data.uEdge = ABE_TOP
        # self.appbar_data.uCallbackMessage = 0 # Optional: for callback messages

        self.original_wnd_proc = None
        self._register()

    def _register(self):
        """Registers the window as an appbar."""
        if not self.window.winId():
            print("AppBarManager Error: Window ID not available for appbar registration.")
            return
        
        # SHAppBarMessage returns BOOL (True/False for success/failure)
        if not ctypes.windll.shell32.SHAppBarMessage(ABM_NEW, ctypes.byref(self.appbar_data)):
            print(f"AppBarManager Error: SHAppBarMessage(ABM_NEW) failed. Error: {win32api.GetLastError()}")
            return # Don't proceed if registration fails
            
        self._set_pos() # Set initial position

        # Subclassing window procedure to handle WM_WINDOWPOSCHANGED
        # This is critical for the appbar to respond to screen resolution changes etc.
        # It's done after ABM_NEW and initial ABM_SETPOS
        try:
            self.original_wnd_proc = win32gui.SetWindowLong(
                self.appbar_data.hWnd,
                win32con.GWL_WNDPROC,
                self._wnd_proc_callback
            )
        except Exception as e:
            print(f"AppBarManager Error: Failed to set window procedure: {e}")
            # If setting wndproc fails, we should probably unregister the appbar
            self.unregister()


    def _set_pos(self):
        """Sets the position of the appbar."""
        # Use QCoreApplication.instance().primaryScreen() for screen geometry
        # This is more robust in PyQt if QApplication is already running.
        app_instance = QCoreApplication.instance()
        if not app_instance:
            print("AppBarManager Error: QApplication instance not found for screen geometry.")
            # Fallback or error handling if no QApplication instance (should not happen in normal flow)
            screen_width = win32api.GetSystemMetrics(0) 
        else:
            screen = app_instance.primaryScreen().geometry()
            screen_width = screen.width()

        self.appbar_data.rc.left = 0
        self.appbar_data.rc.top = 0
        self.appbar_data.rc.right = screen_width
        self.appbar_data.rc.bottom = self.bar_height
        
        # Query position (optional but good practice, shell might adjust rc)
        ctypes.windll.shell32.SHAppBarMessage(ABM_QUERYPOS, ctypes.byref(self.appbar_data))
        
        # Set position
        if not ctypes.windll.shell32.SHAppBarMessage(ABM_SETPOS, ctypes.byref(self.appbar_data)):
            print(f"AppBarManager Error: SHAppBarMessage(ABM_SETPOS) failed. Error: {win32api.GetLastError()}")

        self.window.setGeometry(
            self.appbar_data.rc.left,
            self.appbar_data.rc.top,
            self.appbar_data.rc.right - self.appbar_data.rc.left,
            self.appbar_data.rc.bottom - self.appbar_data.rc.top
        )
        # Force the window to be always on top after setting geometry
        # This helps ensure it behaves like a typical appbar/toolbar.
        win32gui.SetWindowPos(self.appbar_data.hWnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)


    def _wnd_proc_callback(self, hwnd, msg, wparam, lparam):
        """Custom window procedure callback."""
        if msg == win32con.WM_WINDOWPOSCHANGED:
            # This message is sent when the window position is about to change.
            # We need to tell the system our new desired position.
            # The system sends this message with a WINDOWPOS structure in lParam.
            # We don't strictly need to read it if we are recalculating everything,
            # but it's good to be aware.
            self._set_pos() 
            # Return 0 to indicate we've processed the message if the message
            # doesn't require a specific return value for WM_WINDOWPOSCHANGED
            # or if CallWindowProc is not going to be called for this specific message.
            # Typically, you'd call CallWindowProc for messages you don't handle.
            # For WM_WINDOWPOSCHANGED, after handling, further processing by default proc might not be needed or could interfere.
            # However, it's safer to call the original proc unless documentation says otherwise.
            # Let's call original and see if it causes issues.
            # return 0

        # Always call the original window procedure for other messages
        if self.original_wnd_proc:
             return win32gui.CallWindowProc(self.original_wnd_proc, hwnd, msg, wparam, lparam)
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)


    def unregister(self):
        """Unregisters the appbar."""
        if self.appbar_data.hWnd: # Ensure hWnd was set
            if not ctypes.windll.shell32.SHAppBarMessage(ABM_REMOVE, ctypes.byref(self.appbar_data)):
                 print(f"AppBarManager Error: SHAppBarMessage(ABM_REMOVE) failed. Error: {win32api.GetLastError()}")
            
            # Restore original window procedure if it was changed
            if self.original_wnd_proc:
                try:
                    win32gui.SetWindowLong(
                        self.appbar_data.hWnd,
                        win32con.GWL_WNDPROC,
                        self.original_wnd_proc
                    )
                    self.original_wnd_proc = None # Clear it after restoring
                except Exception as e:
                    print(f"AppBarManager Error: Failed to restore original window procedure: {e}")
            self.appbar_data.hWnd = 0 # Mark as unregistered 