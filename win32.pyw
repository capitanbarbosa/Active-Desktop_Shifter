import tkinter as tk
from pyvda import VirtualDesktopAccessor

# Define colors
ACTIVE_DESKTOP_COLOR = "green"
INACTIVE_DESKTOP_COLOR = "gray"

# Get virtual desktop information
vda = VirtualDesktopAccessor()
desktops = vda.get_desktops()
current_desktop = vda.get_current_desktop()

# Initialize Tkinter window
root = tk.Tk()
root.title("Virtual Desktop Switcher")

# Define function to update button colors
def update_colors():
    for i, button in enumerate(buttons):
        if i == current_desktop:
            button.config(bg=ACTIVE_DESKTOP_COLOR)
        else:
            button.config(bg=INACTIVE_DESKTOP_COLOR)

# Create buttons
buttons = []
for i, desktop in enumerate(desktops):
    button = tk.Button(
        root, text=f"Desktop {i + 1}", command=lambda i=i: vda.goto_desktop_number(i)
    )
    buttons.append(button)
    button.pack(side="left", padx=5)

# Update button colors initially
update_colors()

# Bind event to listen for desktop switch
root.bind("<Win-Tab>", lambda event: update_colors())

# Start the main event loop
root.mainloop()
