import tkinter as tk
from tkinter import simpledialog
import keyboard
import pyautogui
import subprocess
from pyvda import VirtualDesktop
import time
import os
import sys
import threading

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
        
        # Get the directory where this Python script is located
        current_directory = os.path.dirname(os.path.abspath(__file__))
        # Create absolute path to the AHK script in the DesktopSwitcher subfolder
        script_path = os.path.join(current_directory, "DesktopSwitcher", f"DesktopSwitcher-d{index}.ahk")
        
        try:
            subprocess.run(["C:\\Program Files\\AutoHotkey\\v2\\AutoHotkey64.exe", script_path], check=True)
        except subprocess.CalledProcessError:
            print(f"Failed to execute the AHK script: {script_path}")

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
        
        # Get the directory where this Python script is located
        current_directory = os.path.dirname(os.path.abspath(__file__))
        # Create absolute path to the AHK script in the DesktopSwitcher subfolder
        script_path = os.path.join(current_directory, "DesktopSwitcher", f"DesktopSwitcher-d{index}.ahk")
        
        try:
            subprocess.run(["C:\\Program Files\\AutoHotkey\\v2\\AutoHotkey64.exe", script_path], check=True)
        except subprocess.CalledProcessError:
            print(f"Failed to execute the AHK script: {script_path}")

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

def update_window_size(event):
    new_width = calculate_window_width()
    root.geometry(f"{new_width}x59+2900-0")  # Position near bottom right for 4K screen

# New functions for fade effects and hover detection

def on_enter(event):
    """Handle mouse entering the window"""
    global mouse_inside, hide_timer
    
    mouse_inside = True
    # Cancel any pending hide timer
    if hide_timer is not None:
        root.after_cancel(hide_timer)
        hide_timer = None

def on_leave(event):
    """Handle mouse leaving the window"""
    global mouse_inside, hide_timer
    
    mouse_inside = False
    # Start the hide timer
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
    """Gradually fade in the window"""
    global window_visible, hide_timer
    
    # Cancel any pending hide timer
    if hide_timer is not None:
        root.after_cancel(hide_timer)
    
    # Make window visible first
    root.deiconify()
    
    # Start with zero opacity
    root.attributes('-alpha', 0.0)
    root.update()
    
    # Fade in over 300ms (10 steps of 30ms)
    for alpha in range(1, 11):
        opacity = alpha / 10.0
        root.attributes('-alpha', opacity)
        root.update()
        time.sleep(0.03)
    
    window_visible = True
    
    # Start hide timer
    hide_timer = root.after(3000, fade_out)
    
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

# Initialize the UI
root = tk.Tk()
root.overrideredirect(True)
root.wm_attributes("-topmost", True)
root.title("Active Window 🚀🌙⭐")
root.configure(bg="#3f4652")  # Set the background color

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
root.geometry(f"{button_row_width}x59+2900-0")  # Position near bottom right for 4K screen

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

root.mainloop()
