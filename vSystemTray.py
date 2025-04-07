import pystray
from PIL import Image, ImageDraw, ImageFont
from pyvda import VirtualDesktop, AppView, get_virtual_desktops
import tkinter as tk
from tkinter import simpledialog
import os
import time
import json
import threading

# Configuration file for desktop names
CONFIG_FILE_PATH = 'desktop_names.json'

# List to keep references to all icons
icons = []

# Default desktop names
default_desktop_names = ["Log", "Coding", "Music 1", "Music 2", "Media", "Media 2", "Make"]

# Flag to track if we need to restart icons
restart_needed = False

def load_desktop_names():
    try:
        with open(CONFIG_FILE_PATH, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        # Initialize with default names and save them
        save_desktop_names(default_desktop_names)
        return default_desktop_names

def save_desktop_names(names):
    with open(CONFIG_FILE_PATH, 'w') as file:
        json.dump(names, file)

def get_display_text(name, number):
    """Get text to display in the icon based on the name"""
    # If name is empty or just a number, use the number
    if not name or name.isdigit():
        return str(number)
    
    # For standard square icons, we need to be concise
    words = name.split()
    if len(words) > 1:
        # For multi-word names, use initials (e.g., "Music 1" -> "M1")
        text = ''.join([w[0] for w in words if w and w[0].isalpha()])
        # If there are numbers in the name, append them
        numbers = ''.join([w for w in words if w.isdigit()])
        if numbers:
            text += numbers
        return text[:2]  # Keep it short for clarity
    else:
        # For single words, first 1-2 letters are usually enough
        # and appear clearer in the system tray
        return name[:2].upper()  # Uppercase looks better at small sizes

def create_numbered_icon(number, name, is_current=False):
    # System tray icons have size limitations, so let's optimize
    width = 64  # More standard icon size
    height = 64  # Use square icons which distort less
    
    # Create a higher resolution image and then resize down
    # This helps with clarity when Windows scales the icon
    scale_factor = 4
    img = Image.new('RGB', (width*scale_factor, height*scale_factor), 
                   color=(0, 120, 200) if is_current else (100, 100, 100))
    d = ImageDraw.Draw(img)
    
    # Get text to display (number or abbreviation of name)
    display_text = get_display_text(name, number)
    
    try:
        # Use larger font size for the high-res version
        font_size = 36 * scale_factor // 2
        try:
            # Try to load a high-quality font
            font = ImageFont.truetype("segoeui.ttf", font_size)  # Windows UI font
        except:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                # If all else fails, use default
                font = ImageFont.load_default()
        
        # Calculate text position to center it
        try:
            text_width, text_height = d.textsize(display_text, font=font)
            position = ((width*scale_factor - text_width) // 2, 
                        (height*scale_factor - text_height) // 2)
        except:
            # Fallback position if textsize fails
            position = (width*scale_factor // 4, height*scale_factor // 3)
        
        # Draw on the high-res image
        d.text(position, display_text, fill=(255, 255, 255), font=font)
        
        # Add a subtle border around the text for better visibility
        if is_current:
            # Draw a small indicator to show this is active
            border = 10 * scale_factor
            d.rectangle([(border, border), 
                        (width*scale_factor-border, height*scale_factor-border)], 
                        outline=(255, 255, 255), width=scale_factor)
        
        # Resize down to the target size with high quality
        img = img.resize((width, height), Image.LANCZOS)
        
    except Exception as e:
        print(f"Icon creation error: {e}")
        # Simple fallback if anything fails
        d.text((width*scale_factor//4, height*scale_factor//3), 
               str(number), fill=(255, 255, 255))
        img = img.resize((width, height), Image.NEAREST)
    
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

def show_rename_dialog(desktop_number):
    """Shows a simple rename dialog in a separate process to avoid blocking the main thread"""
    # Since we're only renaming our representation, not the actual desktop,
    # we'll use a simple approach that won't block the system tray
    
    def dialog_thread():
        dialog_root = tk.Tk()
        dialog_root.title(f"Rename Desktop {desktop_number}")
        
        # Center the dialog
        window_width = 300
        window_height = 100
        screen_width = dialog_root.winfo_screenwidth()
        screen_height = dialog_root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        dialog_root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Add label
        tk.Label(dialog_root, text=f"Enter new name for Desktop {desktop_number}:").pack(pady=5)
        
        # Add entry field
        entry = tk.Entry(dialog_root, width=30)
        entry.insert(0, desktop_names[desktop_number-1])
        entry.pack(pady=5)
        entry.select_range(0, tk.END)
        entry.focus()
        
        def save_name():
            new_name = entry.get()
            if new_name:
                desktop_names[desktop_number-1] = new_name
                save_desktop_names(desktop_names)
                # Update icon tooltips and menus
                update_icon_labels()
                dialog_root.destroy()
        
        def cancel():
            dialog_root.destroy()
        
        # Add buttons
        button_frame = tk.Frame(dialog_root)
        button_frame.pack(pady=5)
        tk.Button(button_frame, text="Save", command=save_name).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)
        
        # Handle Enter key
        dialog_root.bind('<Return>', lambda event: save_name())
        dialog_root.bind('<Escape>', lambda event: cancel())
        
        dialog_root.mainloop()
    
    # Run the dialog in a separate thread
    dialog = threading.Thread(target=dialog_thread)
    dialog.daemon = True
    dialog.start()

def update_icon_labels():
    """Updates icon tooltips and menu labels without recreating them"""
    for i, icon in enumerate(icons, 1):
        name = desktop_names[i-1]
        # Update the icon title (tooltip)
        icon.title = f"{name} (Desktop {i})"
        
        # Update menu items
        if hasattr(icon, '_menu_items') and len(icon._menu_items) > 0:
            # Update the first menu item (the switch item)
            try:
                icon._menu_items[0].text = f"Switch to {name}"
            except:
                pass  # Ignore if menu item update fails
    
    # Update the icons themselves with the new display text
    update_icons()

def create_desktop_icon(desktop_number, name):
    current_desktop = VirtualDesktop.current().number
    is_current = (desktop_number == current_desktop)
    
    icon_img = create_numbered_icon(desktop_number, name, is_current)
    
    # Create icon with only click-to-switch functionality
    icon = pystray.Icon(f"Desktop_{desktop_number:02d}", icon_img, f"{name} (Desktop {desktop_number})")
    
    # Create a menu with the default item (clicked when left-clicking the icon)
    switch_item = pystray.MenuItem(f"Switch to {name}", 
                                  lambda: switch_to_desktop(desktop_number),
                                  default=True)
    
    icon.menu = pystray.Menu(
        switch_item,  # This is the default item that's triggered on left-click
        pystray.MenuItem("Move current window here", lambda: move_window_to_desktop(desktop_number)),
        pystray.MenuItem("Rename this desktop", lambda: show_rename_dialog(desktop_number)),
        pystray.MenuItem("Exit All", exit_all)
    )
    
    return icon

def update_icons():
    current_desktop = VirtualDesktop.current().number
    
    # Just update the icon images without recreating everything
    for i, icon in enumerate(icons, 1):
        is_current = (i == current_desktop)
        icon.icon = create_numbered_icon(i, desktop_names[i-1], is_current)

def exit_all():
    for icon in icons:
        try:
            icon.stop()
        except:
            pass

def create_and_run_icons():
    global icons
    # Get all virtual desktops
    desktops = get_virtual_desktops()
    
    # Ensure we have enough names for all desktops
    while len(desktop_names) < len(desktops):
        desktop_names.append(f"Desktop {len(desktop_names)+1}")
    
    # Create icons in reverse order to achieve correct display order
    for i in range(len(desktops), 0, -1):
        name = desktop_names[i-1]
        icon = create_desktop_icon(i, name)
        icons.insert(0, icon)  # Insert at beginning to maintain correct order reference

    # Run each icon in its own thread, launch in reverse order
    for i in range(len(icons)-1, 0, -1):
        icons[i].run_detached()
        time.sleep(0.1)  # Small delay to preserve order

    # Run the first icon in the main thread
    if icons:
        icons[0].run()

# Load desktop names from config
desktop_names = load_desktop_names()

# Start creating and running icons
create_and_run_icons()
