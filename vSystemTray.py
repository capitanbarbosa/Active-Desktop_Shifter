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
    
    # For multi-word names with numbers like "Music 1"
    words = name.split()
    if len(words) > 1 and any(w.isdigit() for w in words):
        # Find first letter and digit combination
        text = ""
        for w in words:
            if w.isalpha() and not text:
                text = w[:2].upper()  # Take up to 2 letters from first word
            elif w.isdigit():
                text += w  # Add the number
                break
        return text[:3]  # Limit to 3 chars total
    
    # For single words or multi-word without numbers
    if len(words) == 1:
        # For single words, show first 3 letters
        return name[:3].upper()
    else:
        # For multi-word names, use first letter of each word (up to 3)
        return ''.join(w[0].upper() for w in words[:3])

def create_numbered_icon(number, name, is_current=False):
    # Standard icon size
    width = 64
    height = 64
    
    # Create a higher resolution image and then resize down
    scale_factor = 4
    img = Image.new('RGB', (width*scale_factor, height*scale_factor), 
                   color=(0, 120, 200) if is_current else (100, 100, 100))
    d = ImageDraw.Draw(img)
    
    # Get text to display with up to 3 letters
    display_text = get_display_text(name, number)
    
    try:
        # Adjust font size based on length of text
        if len(display_text) <= 1:
            font_size = 120  # Very large for single characters
        elif len(display_text) == 2:
            font_size = 90   # Slightly smaller for 2 characters
        else:
            font_size = 120   # Even smaller for 3 characters
        
        try:
            # Bold font if available
            font = ImageFont.truetype("arialbd.ttf", font_size)  # Arial Bold
        except:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # Calculate position to center text
        try:
            text_width, text_height = d.textsize(display_text, font=font)
            position = ((width*scale_factor - text_width) // 2, 
                        (height*scale_factor - text_height) // 2)
        except:
            # Fallback position
            position = (width*scale_factor // 6, height*scale_factor // 6)
        
        # Draw text with a slight shadow for better visibility
        shadow_offset = 4
        # Draw shadow first (black)
        d.text((position[0]+shadow_offset, position[1]+shadow_offset), 
               display_text, fill=(0, 0, 0), font=font)
        # Draw main text
        d.text(position, display_text, fill=(255, 255, 255), font=font)
        
        # Resize down to target size with high quality
        img = img.resize((width, height), Image.LANCZOS)
        
    except Exception as e:
        print(f"Icon creation error: {e}")
        # Simple fallback if anything fails
        d.text((width*scale_factor//6, height*scale_factor//6), 
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
