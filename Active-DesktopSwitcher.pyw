import tkinter as tk
from tkinter import simpledialog
import keyboard
import pyautogui
import subprocess
from pyvda import VirtualDesktop, AppView
import time
import os
import sys
import threading
import win32gui
import win32con

# Integration mode check
INTEGRATION_MODE = "--integrate-with-systray" in sys.argv

desktop1_name = "Log"
desktop2_name = "dev"
desktop3_name = "miw1"
desktop4_name = "miw2"
desktop5_name = "media"
desktop6_name = "media 2"
desktop7_name = "make"

# Timer for auto-hiding
hide_timer = None
# Flag to track if mouse is inside the window
mouse_inside = False
# Flag to track window visibility state
window_visible = True

# Add these new variables at the top with the other global variables
last_mouse_check = 0
MOUSE_CHECK_INTERVAL = 100  # milliseconds

class ShortcutButtonRow(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.buttons = []
        self.shift_pressed = False
        self.create_widgets()
        self.create_shift_listener()
        self.configure(bg="#3f4652")  # Set the background color


    def create_shift_listener(self):
        keyboard.on_press_key("shift", self.on_shift_key_press)
        keyboard.on_release_key("shift", self.on_shift_key_release)

    def on_shift_key_press(self, event):
        self.shift_pressed = True
        for button in self.buttons:
            button.config(bg="#0077CC")
        self.highlight_current_desktop()

    def on_shift_key_release(self, event):
        self.shift_pressed = False
        for button in self.buttons:
            if button["text"] == "Log":
                button.config(bg="#3f4699")
            else:
                button.config(bg="#3f4652")
        if not self.shift_pressed:
            self.highlight_current_desktop()

    def create_widgets(self):
        self.button_frame = tk.Frame(self, bg="#3f4652")  # Set the background color
        self.button_frame.pack(side=tk.LEFT)

        self.create_default_buttons()

    def create_default_buttons(self):
        self.create_button(name=desktop1_name, bg="#3f4699")
        self.create_button(name=desktop2_name, bg="#3f4652")
        self.create_button(name=desktop3_name, bg="#3f4652")
        self.create_button(name=desktop4_name, bg="#3f4652")
        self.create_button(name=desktop5_name, bg="#3f4652")
        self.create_button(name=desktop6_name, bg="#3f4652")
        self.create_button(name=desktop7_name, bg="#3f4652")

        self.highlight_current_desktop()

    def highlight_current_desktop(self):
        if self.shift_pressed:
            return

        active_desktop = VirtualDesktop.current()
        active_desktop_index = active_desktop.number
        for index, button in enumerate(self.buttons, start=1):
            if str(index) == str(active_desktop_index):
                button.config(bg="#F40000")
            else:
                button.config(bg="#3f4652")
        
        # Only schedule next update if window is visible
        if window_visible:
            self.after(420, self.highlight_current_desktop)

    def create_button(self, name="", padx=5, bg="#3f4652"):
        index = len(self.buttons) + 1
        if (index in [1, 2, 3, 4, 5, 6, 7]) and name:
            text = name
        else:
            text = str(index)
        button = tk.Button(
            self.button_frame,
            text=(" " + text + " ").center(padx),
            relief=tk.FLAT,
            bg=bg,
            fg="white"
        )
        button.pack(side=tk.LEFT)
        button.bind("<Button-1>", lambda event, idx=index: self.execute_shortcut(idx))
        button.bind("<Button-3>", lambda event, btn=button: self.edit_button_text(btn))
        button.bind("<Shift-Button-1>", lambda event, idx=index: self.shortcut3(idx))
        button.bind("<Configure>", update_window_size)  # Bind the Configure event
        self.buttons.append(button)

    def edit_button_text(self, button):
        current_text = button.cget("text").strip()
        new_text = simpledialog.askstring("Edit Button", "Enter the new text for the button:", initialvalue=current_text)
        if new_text:
            button.config(text=(" " + new_text + " ").center(5))
            index = self.buttons.index(button)
            if isinstance(self, ShortcutButtonRow):
                row2.buttons[index].config(text=(" " + new_text + " ").center(5))
            elif isinstance(self, ShortcutButtonRow2):
                row.buttons[index].config(text=(" " + new_text + " ").center(5))

    def execute_shift(self, index):
        print("indexz: " + str(index))
        ahk_script = r'"C:\Program Files\AutoHotkey\UX\AutoHotkeyUX.exe"'
        script_path = r'"shift_window.ahk"'
        subprocess.run([ahk_script, script_path, str(index)])

    def execute_shortcut(self, index):
        index_str = str(index)
        for button in self.buttons:
            button.config(bg="#FF99" if button["text"] == index_str else "#3f4652")
        pyautogui.keyDown('win')
        pyautogui.keyDown('alt')
        pyautogui.keyDown('shift')
        pyautogui.press(index_str)
        pyautogui.keyUp('win')
        pyautogui.keyUp('alt')
        pyautogui.keyUp('shift')

    def execute_shortcut2(self, index):
        pyautogui.hotkey('win', 'tab')
        print('bruh')
        time.sleep(0.1)
        index_str = str(index)
        pyautogui.keyDown('win')
        pyautogui.keyDown('alt')
        pyautogui.keyDown('shift')
        pyautogui.keyDown('f' + index_str)
        pyautogui.keyUp('f' + index_str)
        pyautogui.keyUp('win')
        pyautogui.keyUp('alt')
        pyautogui.keyUp('shift')

    def shortcut3(self, index):
        if index < 1 or index > 7:
            print("Invalid index number. Please provide a number between 1 and 7.")
            return
        
        move_active_window_to_desktop(index)

class ShortcutButtonRow2(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.buttons = []
        self.shift_pressed = False
        self.create_widgets()
        self.configure(bg="#3f4699")  # Set the background color

    def create_widgets(self):
        self.button_frame = tk.Frame(self, bg="#3f4652")  # Set the background color
        self.button_frame.pack(side=tk.LEFT)

        self.create_default_buttons()

    def create_default_buttons(self):
        current_directory = os.path.dirname(os.path.abspath(__file__))
        file_directory = os.path.join(current_directory, "Notez")

        self.create_button(name="📄", bg="#1e2127", file_name=os.path.join(file_directory, "Log.txt"))
        self.create_button(name="📄", bg="#1e2127", file_name=os.path.join(file_directory, "dev.txt"))
        self.create_button(name="📄", bg="#1e2127", file_name=os.path.join(file_directory, "miw1.txt"))
        self.create_button(name="📄", bg="#1e2127", file_name=os.path.join(file_directory, "miw2.txt"))
        self.create_button(name="📄", bg="#1e2127", file_name=os.path.join(file_directory, "media.txt"))
        self.create_button(name="📄", bg="#1e2127", file_name=os.path.join(file_directory, "media2.txt"))
        self.create_button(name="📄", bg="#1e2127", file_name=os.path.join(file_directory, "make.txt"))


    def create_button(self, name="", padx=5, bg="#3f4652", file_name=""):
        index = len(self.buttons) + 1
        if (index in [1, 2, 3, 4, 5, 6, 7]) and name:
            text = name
        else:
            text = str(index)

        button = tk.Button(
            self.button_frame,
            text=(" " + text + " ").center(padx),
            relief=tk.FLAT,
            bg=bg,
            fg="white",
            height=2
        )
        button.pack(side=tk.LEFT)
        button.bind("<Button-1>", lambda event, file=file_name: self.open_file(file))
        button.bind("<Button-3>", lambda event, btn=button: self.edit_button_text(btn))
        button.bind("<Shift-Button-1>", lambda event, idx=index: self.shortcut3(idx))
        button.bind("<Configure>", update_window_size)  # Bind the Configure event
        self.buttons.append(button)

    def open_file(self, file_name):
        try:
            os.startfile(file_name)
        except FileNotFoundError:
            print(f"File not found: {file_name}")

    def edit_button_text(self, button):
        current_text = button.cget("text").strip()
        new_text = simpledialog.askstring("Edit Button", "Enter the new text for the button:", initialvalue=current_text)
        if new_text:
            button.config(text=(" " + new_text + " ").center(5))
            index = self.buttons.index(button)
            if isinstance(self, ShortcutButtonRow):
                row2.buttons[index].config(text=(" " + new_text + " ").center(5))
            elif isinstance(self, ShortcutButtonRow2):
                row.buttons[index].config(text=(" " + new_text + " ").center(5))

    def shortcut3(self, index):
        if index < 1 or index > 7:
            print("Invalid index number. Please provide a number between 1 and 7.")
            return
        
        move_active_window_to_desktop(index)

def on_shift_key_press(event):
    for button in row.buttons:
        button.config(bg="#31887A")

def on_shift_key_release(event):
    for button in row.buttons:
        button.config(bg="#3f4652")

def calculate_window_width():
    button_widths = [button.winfo_reqwidth() for button in button_row.buttons]
    total_width = sum(button_widths)
    return total_width + 10  # Add some extra padding

def position_window_above_taskbar():
    """Position the window just above the taskbar in the lower right corner"""
    # Get screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # Get window dimensions
    window_width = root.winfo_width()
    window_height = root.winfo_height()
    
    # Get taskbar height (approximate method)
    taskbar_height = 40  # Default Windows 10/11 taskbar height
    
    # Calculate position (right side of screen, just above taskbar)
    x_position = screen_width - window_width - 10  # 10px from right edge
    y_position = screen_height - window_height - taskbar_height - 30  # Increased gap to 30px
    
    # Set the window position
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

def update_window_size(event):
    new_width = calculate_window_width()
    root.geometry(f"{new_width}x59")  # Only set size, not position
    root.after(10, position_window_above_taskbar)  # Position after size is updated

# New functions for fade effects and hover detection

def on_enter(event):
    """Handle mouse entering the window"""
    global mouse_inside, hide_timer
    
    mouse_inside = True
    # Cancel any pending hide timer
    if hide_timer is not None:
        root.after_cancel(hide_timer)
        hide_timer = None
    
    # Make sure window is fully visible instantly
    if not window_visible:
        fade_in()

def on_leave(event):
    """Handle mouse leaving the window"""
    global mouse_inside, hide_timer
    
    mouse_inside = False
    # Start the hide timer - always wait 3 seconds
    if hide_timer is not None:
        root.after_cancel(hide_timer)
    hide_timer = root.after(3000, fade_out)  # 3 seconds before fading out

def fade_out():
    """Gradually fade out the window"""
    global window_visible
    
    # If mouse is back inside, don't fade out
    if mouse_inside:
        return
    
    # Fade out over 500ms (10 steps of 50ms)
    for alpha in range(10, -1, -1):
        if mouse_inside:  # Stop fading if mouse enters during fade
            return
        opacity = alpha / 10.0
        root.attributes('-alpha', opacity)
        root.update()
        time.sleep(0.05)
    
    window_visible = False
    # Make window invisible but still running
    root.withdraw()
    
    # Reset opacity for next time
    root.attributes('-alpha', 1.0)

def fade_in():
    """Instantly show the window"""
    global window_visible, hide_timer
    
    # Cancel any pending hide timer
    if hide_timer is not None:
        root.after_cancel(hide_timer)
        hide_timer = None
    
    # Make window visible immediately at full opacity
    root.deiconify()
    root.attributes('-alpha', 1.0)
    root.update()
    
    window_visible = True
    
    # Restart highlight animation
    button_row.highlight_current_desktop()

def check_command_file():
    """Check for command file from vSystemTray"""
    try:
        if os.path.exists("desktop_switcher_command.txt"):
            with open("desktop_switcher_command.txt", "r") as f:
                command = f.read().strip()
                
            # Delete the file after reading
            os.remove("desktop_switcher_command.txt")
            
            if command == "show":
                # Show the window if it's hidden
                if not window_visible:
                    fade_in()
                else:
                    # Reset the hide timer
                    if hide_timer is not None:
                        root.after_cancel(hide_timer)
                    hide_timer = root.after(3000, fade_out)
    except Exception as e:
        print(f"Error checking command file: {e}")
    
    # Check again after 0.5 seconds
    root.after(500, check_command_file)

def move_active_window_to_desktop(desktop_number):
    """Move the currently active window to the specified desktop and follow it"""
    try:
        # Get the current active window
        current_window = AppView.current()
        # Get the target desktop
        target_desktop = VirtualDesktop(desktop_number)
        # Move the window
        current_window.move(target_desktop)
        # Follow the window to the target desktop
        target_desktop.go()
    except Exception as e:
        print(f"Error moving window to desktop {desktop_number}: {e}")

# Add this new function
def check_mouse_position():
    """Check if mouse is in the window area and show if needed"""
    global window_visible, last_mouse_check
    
    current_time = time.time() * 1000  # Convert to milliseconds
    if current_time - last_mouse_check < MOUSE_CHECK_INTERVAL:
        # Check again after interval
        root.after(MOUSE_CHECK_INTERVAL, check_mouse_position)
        return
        
    last_mouse_check = current_time
    
    if not window_visible:
        # Get mouse position
        mouse_x = root.winfo_pointerx()
        mouse_y = root.winfo_pointery()
        
        # Get screen dimensions
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Calculate window area (same as in position_window_above_taskbar)
        window_width = button_row_width
        window_height = 59
        taskbar_height = 40
        
        # Calculate window position
        window_x = screen_width - window_width - 10
        window_y = screen_height - window_height - taskbar_height - 30
        
        # Check if mouse is in window area and show instantly if true
        if (window_x <= mouse_x <= window_x + window_width and 
            window_y <= mouse_y <= window_y + window_height):
            fade_in()  # This is now instant
    
    # Check again after interval
    root.after(MOUSE_CHECK_INTERVAL, check_mouse_position)

# Initialize the UI
root = tk.Tk()
root.overrideredirect(True)
root.wm_attributes("-topmost", True)
root.title("Active Window 🚀🌙⭐")
root.configure(bg="#3f4652")  # Set the background color

# Make window visible on all desktops
hwnd = win32gui.GetParent(root.winfo_id())
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                      win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_TOOLWINDOW)
root.after(10, lambda: win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                           win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE))

button_row = ShortcutButtonRow(root)
button_row.pack(side=tk.BOTTOM)

button_row2 = ShortcutButtonRow2(root)
button_row2.configure(bg="green")
button_row2.pack(side=tk.TOP)

root.bind_all("<Control-Key>", on_shift_key_press)
root.bind_all("<KeyRelease-Control_L>", on_shift_key_release)

# Add mouse enter/leave bindings for the entire window
root.bind("<Enter>", on_enter)
root.bind("<Leave>", on_leave)

button_row.update()  # Ensure that the frame has been updated with the button widths
button_row_width = button_row.winfo_reqwidth()

# Set the window size based on the button row width
# Don't specify position yet, just set the size
root.geometry(f"{button_row_width}x59")

# Position the window correctly
root.update_idletasks()  # Make sure window dimensions are updated
position_window_above_taskbar()

# If in integration mode, hide the window initially and start checking for commands
if INTEGRATION_MODE:
    window_visible = False
    root.withdraw()
    root.after(1000, check_command_file)
else:
    # Start the auto-hide timer
    hide_timer = root.after(3000, fade_out)

# Start updating desktop highlights
button_row.highlight_current_desktop()

# Start the mouse position checker
check_mouse_position()

root.mainloop()
