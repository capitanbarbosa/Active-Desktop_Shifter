import tkinter as tk
from tkinter import ttk
import time
from tkinter import simpledialog, messagebox
import keyboard
import pyautogui
import subprocess
from pyvda import AppView, get_apps_by_z_order, VirtualDesktop, get_virtual_desktops


class ShortcutButtonRow(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.buttons = []
        self.shift_pressed = False  # Variable to track the state of the shift key
        self.create_widgets()
        self.create_shift_listener()  # Create the global shift key listener

    def create_shift_listener(self):
        # Create a global listener for the shift key
        keyboard.on_press_key("shift", self.on_shift_key_press)
        keyboard.on_release_key("shift", self.on_shift_key_release)

    def on_shift_key_press(self, event):
        # Change the background color of the frame and buttons when Shift key is pressed
        self.shift_pressed = True  # Set the shift_pressed flag to True
        for button in self.buttons:
            button.config(bg="#0077CC")  # Set the background color of buttons to red

    def on_shift_key_release(self, event):
        # Change the background color of the frame and buttons back to the default color when Shift key is released
        self.shift_pressed = False  # Set the shift_pressed flag to False
        for button in self.buttons:
            if button["text"] == "Log":
                button.config(bg="#3f4699")  # Set the background color of the "Log" button to a different color
            else:
                button.config(bg="#3f4652")  # Set the background color of other buttons to the default color

    def create_widgets(self):
        # Create a frame to hold the buttons
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(side=tk.LEFT)

        # Create the initial buttons
        self.create_default_buttons()

    def create_default_buttons(self):
        # Create the "Log" button
        self.create_button(name="Log", bg="#3f4699")  # Set the background color of the button to black
        self.create_button(name="dev", bg="#3f4652")  # Set the background color of the button to black
        self.create_button(name="1", bg="#3f4652")  # Set the background color of the button to black
        self.create_button(name="2", bg="#3f4652")  # Set the background color of the button to black
        self.create_button(name="3", bg="#3f4652")  # Set the background color of the button to black
        self.create_button(name="miw", bg="#3f4652")  # Set the background color of the button to black
        self.create_button(name="media", bg="#3f4652")  # Set the background color of the button to black

        # Highlight the current desktop index button
        self.highlight_current_desktop()

    def highlight_current_desktop(self):
        # Get the active virtual desktop
        active_desktop = VirtualDesktop.current()

        # Get the index of the active desktop
        active_desktop_index = active_desktop.number

        # Highlight the current desktop index button
        for index, button in enumerate(self.buttons, start=1):
            if str(index) == str(active_desktop_index):
                button.config(bg="#FF6904")  # Set the background color of the current desktop index button to pink
            else:
                button.config(bg="#3f4652")  # Set the background color of other buttons to the default color

        # Schedule the next update after 1 second (adjust the duration as desired)
        root.after(420, self.highlight_current_desktop)


    def create_button(self, name="", padx=5, bg="#3f4652"):
        # Determine the index of the button in the list
        index = len(self.buttons) + 1

        # Set the text based on the index and name
        if (index in [1, 2, 3, 4, 5, 6, 7]) and name:
            text = name
        else:
            text = str(index)

        # Create a new button and add it to the button frame
        button = tk.Button(
            self.button_frame,
            text=(" " + text + " ").center(padx),
            relief=tk.FLAT,  # Make the button flat
            bg=bg,  # Set the background color of the button
            fg="white"  # Set the text color to white
        )
        button.pack(side=tk.LEFT)

        # Bind left-click event to execute_shortcut method
        button.bind("<Button-1>", lambda event, idx=index: self.execute_shortcut(idx))

        # Bind right-click event to edit_button_text method
        button.bind("<Button-3>", lambda event, btn=button: self.edit_button_text(btn))

        # Bind shift + left-click event to execute_shift method
        button.bind("<Shift-Button-1>", lambda event, idx=index: self.execute_shift(idx))

        # Add the button to the list
        self.buttons.append(button)

    def edit_button_text(self, button):
        # Get the current text of the button
        current_text = button.cget("text").strip()

        # Prompt the user to enter the new text for the button
        new_text = simpledialog.askstring("Edit Button", "Enter the new text for the button:", initialvalue=current_text)

        # Update the button's text if the user provided new text
        if new_text:
            button.config(text=(" " + new_text + " ").center(5))

    def execute_shift(self, index):
        print("indexz: " + str(index))
        ahk_script = r'"C:\Program Files\AutoHotkey\UX\AutoHotkeyUX.exe"'
        script_path = r'"shift_window.ahk"'

        # Run AutoHotkey script with the index as an argument
        subprocess.run([ahk_script, script_path, str(index)])

    def execute_shortcut(self, index):
        # Convert the index to a string
        index_str = str(index)

        # Highlight the current desktop index button
        for button in self.buttons:
            button.config(bg="#FF99" if button["text"] == index_str else "#3f4652")

        pyautogui.keyDown('win')
        pyautogui.keyDown('alt')
        pyautogui.keyDown('shift')

        # Simulate pressing the index key (button number)
        pyautogui.press(index_str)

        # Simulate releasing the Win, Alt, Shift, and index keys
        pyautogui.keyUp('win')
        pyautogui.keyUp('alt')
        pyautogui.keyUp('shift')


def on_shift_key_press(event):
    # Change the background color of the frame and buttons when Shift key is pressed
    for button in row.buttons:
        button.config(bg="#31887A")  # Set the background color of buttons to red


def on_shift_key_release(event):
    # Change the background color of the frame and buttons back to the default color when Shift key is released
    for button in row.buttons:
        button.config(bg="#3f4652")  # Set the background color of buttons to the default color


# Create the root window
root = tk.Tk()

# Remove title bar
root.overrideredirect(True)

# Set the window to always be on top
root.wm_attributes("-topmost", True)

# Set the title of the window
root.title("Active Window 🚀🌙⭐")

# Calculate the required width of the button row
button_row = ShortcutButtonRow(root)
button_row.pack()
button_row.update()  # Ensure that the frame has been updated with the button widths
button_row_width = button_row.winfo_reqwidth()

# Set the window size based on the button row width
root.geometry(f"{button_row_width}x63+1055+1377")

root.bind_all("<Control-Key>", on_shift_key_press)
root.bind_all("<KeyRelease-Control_L>", on_shift_key_release)

root.mainloop()
