import pystray
from PIL import Image, ImageDraw, ImageFont
from pyvda import VirtualDesktop, AppView, get_virtual_desktops
import tkinter as tk
import os
import time

# List to keep references to all icons
icons = []

def create_numbered_icon(number, is_current=False):
    # Create a simple colored square with a number
    img = Image.new('RGB', (64, 64), color=(0, 120, 200) if is_current else (100, 100, 100))
    d = ImageDraw.Draw(img)
    # Try to use a font that's likely to be available
    try:
        font = ImageFont.truetype("arial.ttf", 24)
        d.text((25, 20), str(number), fill=(255, 255, 255), font=font)
    except:
        d.text((25, 20), str(number), fill=(255, 255, 255))
    return img

def switch_to_desktop(desktop_number):
    print(f"Switching to desktop {desktop_number}")
    VirtualDesktop(desktop_number).go()
    update_icons()  # Update all icons to highlight current desktop

def move_window_to_desktop(desktop_number):
    current_window = AppView.current()
    target_desktop = VirtualDesktop(desktop_number)
    current_window.move(target_desktop)
    # Optionally follow the window
    target_desktop.go()
    update_icons()

def action_handler(icon, item):
    if hasattr(item, 'desktop_number'):
        switch_to_desktop(item.desktop_number)

def create_desktop_icon(desktop_number, name):
    current_desktop = VirtualDesktop.current().number
    is_current = (desktop_number == current_desktop)
    
    icon_img = create_numbered_icon(desktop_number, is_current)
    
    # Create icon with only click-to-switch functionality
    icon = pystray.Icon(f"Desktop_{desktop_number:02d}", icon_img, f"{name} (Desktop {desktop_number})")
    
    # Create a menu with the default item (clicked when left-clicking the icon)
    switch_item = pystray.MenuItem(f"Switch to Desktop {desktop_number}", 
                                  lambda: switch_to_desktop(desktop_number),
                                  default=True)
    # Store desktop number for direct access
    switch_item.desktop_number = desktop_number
    
    icon.menu = pystray.Menu(
        switch_item,  # This is the default item that's triggered on left-click
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

# Create icons in reverse order to achieve correct display order
for i in range(len(desktop_names), 0, -1):
    name = desktop_names[i-1]
    icon = create_desktop_icon(i, name)
    icons.insert(0, icon)  # Insert at beginning to maintain correct order reference

# Run each icon in its own thread, launch in reverse order
# This helps ensure the system tray displays them in sequential order
for i in range(len(icons)-1, 0, -1):
    icons[i].run_detached()
    time.sleep(0.1)  # Small delay to preserve order

# Run the first icon in the main thread
if icons:
    icons[0].run()
