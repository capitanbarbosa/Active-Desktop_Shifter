import tkinter as tk
from tkinter import simpledialog
import keyboard
import pyautogui
import subprocess
import time
import os

# Replace the desktop names with your own
desktop_names = ["Log", "dev", "3", "4", "5", "6", "7"]

last_pressed_button = None  # To keep track of the last pressed button


def get_active_desktop():
    return None


class ShortcutButtonRow(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.buttons = []
        self.shift_pressed = False
        self.create_widgets()
        self.configure(bg="#3f4652")

    def create_shift_listener(self):
        keyboard.on_press_key("shift", self.on_shift_key_press)
        keyboard.on_release_key("shift", self.on_shift_key_release)

    def on_shift_key_press(self, event):
        self.shift_pressed = True
        for button in self.buttons:
            button.config(bg="#0077cc")
        self.highlight_current_desktop()

    def on_shift_key_release(self, event):
        self.shift_pressed = False
        for button in self.buttons:
            # if button["text"] == "Log":
            # button.config(bg="#3f4699")
            # else:
            button.config(bg="#3f4652")
        if not self.shift_pressed:
            self.highlight_current_desktop()

    def create_widgets(self):
        self.button_frame = tk.Frame(self, bg="#3f4652")
        self.button_frame.pack(side=tk.LEFT)

        self.create_default_buttons()

    def create_default_buttons(self):
        # self.create_button(name=desktop_names[0], bg="#3f4699")
        for index in range(0, 7):
            self.create_button(name=desktop_names[index], bg="#3f4652")

        self.highlight_current_desktop()

    def highlight_current_desktop(self):
        if self.shift_pressed:
            return

        active_desktop_index = get_active_desktop()
        if active_desktop_index is not None:
            for index, button in enumerate(self.buttons, start=1):
                if index == active_desktop_index:
                    button.config(bg="#F40000")
                else:
                    button.config(bg="#3f4652")
        self.after(420, self.highlight_current_desktop)

    def create_button(self, name="", padx=5, bg="#3f4652"):
        index = len(self.buttons) + 1
        if (index in range(1, 8)) and name:
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
        button.bind("<Button-1>", lambda event,
                    idx=index: self.execute_shortcut(idx))
        button.bind("<Button-3>", lambda event,
                    btn=button: self.edit_button_text(btn))
        button.bind("<Shift-Button-1>", lambda event,
                    idx=index: self.shortcut3(idx))
        button.bind("<Configure>", update_window_size)
        self.buttons.append(button)

    def edit_button_text(self, button):
        current_text = button.cget("text").strip()
        new_text = simpledialog.askstring(
            "Edit Button", "Enter the new text for the button:", initialvalue=current_text)
        if new_text:
            button.config(text=(" " + new_text + " ").center(5))
            index = self.buttons.index(button)

    def execute_shortcut(self, index):
        global last_pressed_button
        if last_pressed_button:
            last_pressed_button.config(bg="#3f4652")
        last_pressed_button = self.buttons[index - 1]

        index_str = str(index)
        last_pressed_button.config(bg="#F40000")
        pyautogui.keyDown('win')
        pyautogui.keyDown('alt')
        pyautogui.keyDown('shift')
        pyautogui.press(index_str)
        pyautogui.keyUp('win')
        pyautogui.keyUp('alt')
        pyautogui.keyUp('shift')

    def shortcut3(self, index):
        if index < 1 or index > 7:
            print("Invalid index number. Please provide a number between 1 and 7.")
            return

        script_path = os.path.join(
            "DesktopSwitcher", f"DesktopSwitcher-d{index}.ahk")
        script_path = os.path.abspath(script_path)

        try:
            subprocess.run(
                ["C:\\Program Files\\AutoHotkey\\v2\\AutoHotkey64.exe", script_path], check=True)
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
    return total_width + 10


def update_window_size(event):
    new_width = calculate_window_width()
    root.geometry(f"{new_width}x59+2100-1081")
    # root.geometry(f"{new_width}x69+1200+1012")


root = tk.Tk()
root.overrideredirect(True)
root.wm_attributes("-topmost", True)
root.title("Active Window 🚀🌙⭐")
root.configure(bg="#3f4652")

button_row = ShortcutButtonRow(root)
button_row.pack(side=tk.BOTTOM)


class ShortcutButtonRow2(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.buttons = []
        self.shift_pressed = False
        self.create_widgets()
        self.configure(bg="#3f4699")

    def create_widgets(self):
        self.button_frame = tk.Frame(self, bg="#3f4652")
        self.button_frame.pack(side=tk.LEFT)

        self.create_default_buttons()

    def create_default_buttons(self):
        self.create_button(
            name="📄", bg="#1e2127", file_name=r"C:\Users\wiz\Coding\Active-Desktop_Shifter\Notez\Log.txt")
        self.create_button(
            name="📄", bg="#1e2127", file_name=r"C:\Users\wiz\Coding\Active-Desktop_Shifter\Notez\dev.txt")
        self.create_button(
            name="📄", bg="#1e2127", file_name=r"C:\Users\wiz\Coding\Active-Desktop_Shifter\Notez\1.txt")
        self.create_button(
            name="📄", bg="#1e2127", file_name=r"C:\Users\wiz\Coding\Active-Desktop_Shifter\Notez\2.txt")
        self.create_button(
            name="📄", bg="#1e2127", file_name=r"C:\Users\wiz\Coding\Active-Desktop_Shifter\Notez\3.txt")
        self.create_button(
            name="📄", bg="#1e2127", file_name=r"C:\Users\wiz\Coding\Active-Desktop_Shifter\Notez\media-biz.txt")
        self.create_button(
            name="📄", bg="#1e2127", file_name=r"C:\Users\wiz\Coding\Active-Desktop_Shifter\Notez\miw.txt")

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
        button.bind("<Button-1>", lambda event,
                    file=file_name: self.open_file(file))
        button.bind("<Button-3>", lambda event,
                    btn=button: self.edit_button_text(btn))
        button.bind("<Shift-Button-1>", lambda event,
                    idx=index: self.shortcut3(idx))
        button.bind("<Configure>", update_window_size)
        self.buttons.append(button)

    def open_file(self, file_name):
        try:
            os.startfile(file_name)
        except FileNotFoundError:
            print(f"File not found: {file_name}")


# Create an instance of ShortcutButtonRow2
button_row2 = ShortcutButtonRow2(root)
button_row2.configure(bg="green")
button_row2.pack(side=tk.TOP)

root.bind_all("<Control-Key>", on_shift_key_press)
root.bind_all("<KeyRelease-Control_L>", on_shift_key_release)

button_row.update()
button_row_width = button_row.winfo_reqwidth()
root.geometry(f"{button_row_width}x59+2100-1081")
# root.geometry(f"{button_row_width}x69+1200+1012")


root.mainloop()
