import pystray
from PIL import Image, ImageDraw
from pyvda import VirtualDesktop, AppView, get_virtual_desktops
import tkinter as tk
import os

# List to keep references to all icons
icons = []

def create_numbered_icon(number, is_current=False):
    # Create a simple colored square with a number
    img = Image.new('RGB', (64, 64), color=(0, 120, 200) if is_current else (100, 100, 100))
    d = ImageDraw.Draw(img)
    d.text((25, 20), str(number), fill=(255, 255, 255))
    return img

def switch_to_desktop(desktop_number):
    VirtualDesktop(desktop_number).go()
    update_icons()  # Update all icons to highlight current desktop

def move_window_to_desktop(desktop_number):
    current_window = AppView.current()
    target_desktop = VirtualDesktop(desktop_number)
    current_window.move(target_desktop)
    # Optionally follow the window
    target_desktop.go()
    update_icons()

def create_desktop_icon(desktop_number, name):
    current_desktop = VirtualDesktop.current().number
    is_current = (desktop_number == current_desktop)
    
    icon_img = create_numbered_icon(desktop_number, is_current)
    
    # Create icon with menu options
    icon = pystray.Icon(f"Desktop_{desktop_number}", icon_img, f"{name} (Desktop {desktop_number})")
    
    # Define menu for the icon
    icon.menu = pystray.Menu(
        pystray.MenuItem(f"Switch to {name}", lambda: switch_to_desktop(desktop_number)),
        pystray.MenuItem("Move current window here", lambda: move_window_to_desktop(desktop_number)),
        pystray.MenuItem("Exit All", exit_all)
    )
    
    return icon

def update_icons():
    current_desktop = VirtualDesktop.current().number
    for i, icon in enumerate(icons, 1):
        is_current = (i == current_desktop)
        icon.icon = create_numbered_icon(i, is_current)

def exit_all():
    for icon in icons:
        icon.stop()

# Get all virtual desktops
desktops = get_virtual_desktops()
desktop_names = ["Desktop " + str(i) for i in range(1, len(desktops) + 1)]

# Create an icon for each desktop
for i, name in enumerate(desktop_names, 1):
    icon = create_desktop_icon(i, name)
    icons.append(icon)

# Run each icon in its own thread
for icon in icons[:-1]:  # All but the last icon
    icon.run_detached()

# Run the last icon in the main thread
if icons:
    icons[-1].run()
