import pystray
from PIL import Image, ImageDraw, ImageFont
from pyvda import VirtualDesktop, AppView, get_virtual_desktops
import tkinter as tk
from tkinter import simpledialog
import os
import time
import json
import threading
import subprocess

# Configuration file for desktop names
CONFIG_FILE_PATH = 'desktop_names.json'
# Configuration file for desktop colors
COLOR_CONFIG_FILE_PATH = 'desktop_colors.json'

# List to keep references to all icons
icons = []

# Default desktop names
default_desktop_names = ["Log", "Coding", "Music 1",
                         "Music 2", "Media", "Media 2", "Make"]

# Default color map with RGB values
default_desktop_colors = {
    "Default": (100, 100, 100),
    "Blue": (0, 120, 200),
    "Red": (200, 50, 50),
    "Green": (50, 180, 50),
    "Orange": (255, 140, 0),
    "Purple": (150, 50, 200),
    "Yellow": (220, 220, 0)
}

# Map to store each desktop's color (desktop_number -> color_name)
desktop_color_map = {}

# Flag to track if we need to restart icons
restart_needed = False

# Variable to track the current desktop in the polling thread
last_known_desktop = None

# Path to the Active-DesktopSwitcher.pyw file
DESKTOP_SWITCHER_SCRIPT = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "Active-DesktopSwitcher.pyw")

# Process handle for the desktop switcher window
desktop_switcher_process = None


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


def load_desktop_colors():
    try:
        with open(COLOR_CONFIG_FILE_PATH, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        # Initialize with default colors (all desktops use default active/inactive colors)
        colors = {}
        save_desktop_colors(colors)
        return colors


def save_desktop_colors(colors):
    with open(COLOR_CONFIG_FILE_PATH, 'w') as file:
        json.dump(colors, file)


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


def get_desktop_color(desktop_number, is_current=False):
    """Get the color for a desktop based on its color setting and active state"""
    color_name = desktop_color_map.get(str(desktop_number), "Default")

    # Always use the selected color (or default if not set)
    if color_name == "Default":
        # Blue for active, darker gray for inactive
        return (0, 120, 200) if is_current else (80, 80, 80)
    else:
        # Use the custom color with different brightness based on active state
        r, g, b = default_desktop_colors[color_name]
        if not is_current:
            # Darken the color for inactive desktops
            return (max(r - 70, 0), max(g - 70, 0), max(b - 70, 0))
        return (r, g, b)  # Use the full color for active desktops


def get_border_color(desktop_number, is_current=False):
    """Get a color for the icon border based on desktop settings"""
    color_name = desktop_color_map.get(str(desktop_number), "Default")

    # Only active desktops get a border
    if not is_current:
        # For inactive desktops, use the same color as the fill (no border effect)
        return get_desktop_color(desktop_number, is_current)

    # For active desktops, use a bright border of the same color family
    if color_name == "Default":
        return (0, 180, 255)  # Bright blue border
    else:
        # Get the base color and make it brighter for the border
        r, g, b = default_desktop_colors[color_name]
        # Brighten the color (with clamping to 255)
        return (min(r + 55, 255), min(g + 55, 255), min(b + 55, 255))


def create_numbered_icon(number, name, is_current=False):
    # Standard icon size
    width = 256
    height = 256

    # Create a higher resolution image and then resize down
    scale_factor = 4

    # Create a transparent background image
    img = Image.new('RGBA', (width*scale_factor,
                    height*scale_factor), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Get colors
    fill_color = get_desktop_color(number, is_current)
    border_color = get_border_color(number, is_current)

    # Calculate dimensions for shapes
    border_width = 20 * scale_factor  # Width of the border
    padding = 15 * scale_factor       # Padding from edge

    if is_current:
        # For active desktop, draw the border and inner rectangle
        # First draw the border (larger rectangle)
        d.rectangle(
            [padding, padding, width*scale_factor -
                padding, height*scale_factor-padding],
            fill=border_color,
            outline=None
        )

        # Then draw the inner rectangle (main background)
        d.rectangle(
            [padding + border_width, padding + border_width,
             width*scale_factor-padding-border_width, height*scale_factor-padding-border_width],
            fill=fill_color,
            outline=None
        )
    else:
        # For inactive desktop, just draw a single rectangle with the fill color
        d.rectangle(
            [padding, padding, width*scale_factor -
                padding, height*scale_factor-padding],
            fill=fill_color,
            outline=None
        )

    # Get text to display with up to 3 letters
    display_text = get_display_text(name, number)

    try:
        # Adjust font size based on length of text
        if len(display_text) <= 1:
            font_size = 320  # Very large for single characters
        elif len(display_text) == 2:
            font_size = 320   # Slightly smaller for 2 characters
        else:
            font_size = 320   # Even smaller for 3 characters

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
        # Draw shadow first (black with some transparency)
        d.text((position[0]+shadow_offset, position[1]+shadow_offset),
               display_text, fill=(0, 0, 0, 200), font=font)
        # Draw main text
        d.text(position, display_text, fill=(255, 255, 255, 255), font=font)

        # Resize down to target size with high quality
        img = img.resize((width, height), Image.LANCZOS)

    except Exception as e:
        print(f"Icon creation error: {e}")
        # Simple fallback if anything fails
        d.text((width*scale_factor//6, height*scale_factor//6),
               str(number), fill=(255, 255, 255, 255))
        img = img.resize((width, height), Image.NEAREST)

    # Convert RGBA to RGB for pystray (which doesn't support transparency well)
    rgb_img = Image.new("RGB", img.size, (0, 0, 0))
    rgb_img.paste(img, mask=img.split()[3])  # Use alpha channel as mask

    return rgb_img


def next_desktop():
    """Switch to the next desktop"""
    current_desktop = VirtualDesktop.current().number
    all_desktops = get_virtual_desktops()
    max_desktop = len(all_desktops)

    next_desktop_num = current_desktop + 1
    if next_desktop_num > max_desktop:
        next_desktop_num = 1  # Wrap around to first

    switch_to_desktop(next_desktop_num)


def prev_desktop():
    """Switch to the previous desktop"""
    current_desktop = VirtualDesktop.current().number
    all_desktops = get_virtual_desktops()
    max_desktop = len(all_desktops)

    prev_desktop_num = current_desktop - 1
    if prev_desktop_num < 1:
        prev_desktop_num = max_desktop  # Wrap around to last

    switch_to_desktop(prev_desktop_num)


def set_desktop_color(desktop_number, color_name):
    """Set the color for a specific desktop"""
    desktop_color_map[str(desktop_number)] = color_name
    save_desktop_colors(desktop_color_map)
    update_icons()  # Update all icons to reflect new color


def switch_to_desktop(desktop_number):
    print(f"Switching to desktop {desktop_number}")
    VirtualDesktop(desktop_number).go()
    update_icons()  # Update all icons to highlight current desktop
    show_desktop_switcher()  # Show the desktop switcher temporarily


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
        dialog_root.geometry(
            f'{window_width}x{window_height}+{center_x}+{center_y}')

        # Add label
        tk.Label(
            dialog_root, text=f"Enter new name for Desktop {desktop_number}:").pack(pady=5)

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
        tk.Button(button_frame, text="Save", command=save_name).pack(
            side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel",
                  command=cancel).pack(side=tk.LEFT, padx=5)

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
    icon = pystray.Icon(f"Desktop_{desktop_number:02d}",
                        icon_img, f"{name} (Desktop {desktop_number})")

    # Create a menu with the default item (clicked when left-clicking the icon)
    switch_item = pystray.MenuItem(f"Switch to {name}",
                                   lambda: switch_to_desktop(desktop_number),
                                   default=True)

    # Create color submenu
    color_menu = pystray.Menu(
        pystray.MenuItem("Default", lambda: set_desktop_color(
            desktop_number, "Default")),
        pystray.MenuItem("Red", lambda: set_desktop_color(
            desktop_number, "Red")),
        pystray.MenuItem("Green", lambda: set_desktop_color(
            desktop_number, "Green")),
        pystray.MenuItem("Blue", lambda: set_desktop_color(
            desktop_number, "Blue")),
        pystray.MenuItem("Orange", lambda: set_desktop_color(
            desktop_number, "Orange")),
        pystray.MenuItem("Purple", lambda: set_desktop_color(
            desktop_number, "Purple")),
        pystray.MenuItem("Yellow", lambda: set_desktop_color(
            desktop_number, "Yellow"))
    )

    # Create navigation submenu instead of using mouse scroll
    navigation_menu = pystray.Menu(
        pystray.MenuItem("Next Desktop", next_desktop),
        pystray.MenuItem("Previous Desktop", prev_desktop)
    )

    # Add organize/reorder option to the menu
    icon.menu = pystray.Menu(
        switch_item,
        pystray.MenuItem("Move current window here",
                         lambda: move_window_to_desktop(desktop_number)),
        pystray.MenuItem("Rename this desktop",
                         lambda: show_rename_dialog(desktop_number)),
        pystray.MenuItem("Set color", color_menu),
        pystray.MenuItem("Navigate", navigation_menu),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Reorder Desktops", reorder_desktops),  # New option
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

# Add this new function to poll for desktop changes


def monitor_desktop_changes():
    """Background thread that monitors for desktop changes from keyboard shortcuts or gestures"""
    global last_known_desktop

    # Initialize with the current desktop
    last_known_desktop = VirtualDesktop.current().number

    # Poll in a loop
    while True:
        try:
            # Sleep to avoid excessive CPU usage
            time.sleep(0.5)

            # Get the current desktop number
            current_desktop = VirtualDesktop.current().number

            # If it changed, update the icons and show the desktop switcher
            if current_desktop != last_known_desktop:
                print(
                    f"Desktop changed from {last_known_desktop} to {current_desktop} (external)")
                last_known_desktop = current_desktop
                update_icons()
                show_desktop_switcher()  # Show the desktop switcher temporarily
        except Exception as e:
            # In case of any error, just log and continue
            print(f"Error monitoring desktop changes: {e}")
            time.sleep(1)  # Longer sleep after error


def create_and_run_icons():
    global icons, last_known_desktop
    # Get all virtual desktops
    desktops = get_virtual_desktops()

    # Initialize last known desktop
    last_known_desktop = VirtualDesktop.current().number

    # Ensure we have enough names for all desktops
    while len(desktop_names) < len(desktops):
        desktop_names.append(f"Desktop {len(desktop_names)+1}")

    # Create icons in reverse order to achieve correct display order
    for i in range(len(desktops), 0, -1):
        name = desktop_names[i-1]
        icon = create_desktop_icon(i, name)
        # Insert at beginning to maintain correct order reference
        icons.insert(0, icon)

    # Launch the desktop switcher script initially
    launch_desktop_switcher()

    # Start the desktop monitoring thread
    monitor_thread = threading.Thread(target=monitor_desktop_changes)
    monitor_thread.daemon = True
    monitor_thread.start()

    # Run each icon in its own thread, launch in reverse order
    for i in range(len(icons)-1, 0, -1):
        icons[i].run_detached()
        time.sleep(0.1)  # Small delay to preserve order

    # Run the first icon in the main thread
    if icons:
        icons[0].run()


# Load desktop names from config
desktop_names = load_desktop_names()

# Load desktop colors from config
desktop_color_map = load_desktop_colors()

# Move these functions BEFORE create_and_run_icons()


def show_desktop_switcher():
    """Show the Active-DesktopSwitcher window temporarily"""
    try:
        # Send a command to the switcher window to show itself
        with open("desktop_switcher_command.txt", "w") as f:
            f.write("show")
    except Exception as e:
        print(f"Error showing desktop switcher: {e}")
        # If the command approach fails, try launching the script directly
        launch_desktop_switcher()


def launch_desktop_switcher():
    """Launch the Active-DesktopSwitcher script if it's not already running"""
    global desktop_switcher_process

    try:
        # Check if the process is still running
        if desktop_switcher_process is None or desktop_switcher_process.poll() is not None:
            # Start the process with a special command line argument for integration
            desktop_switcher_process = subprocess.Popen(
                ["pythonw", DESKTOP_SWITCHER_SCRIPT, "--integrate-with-systray"],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW  # Hide console window
            )
            print("Launched desktop switcher")

            # Give the window time to initialize before showing it
            time.sleep(0.2)
            show_desktop_switcher()
    except Exception as e:
        print(f"Error launching desktop switcher: {e}")


def reorder_desktops():
    """Shows a dialog to reorder desktop sequence"""
    def dialog_thread():
        dialog_root = tk.Tk()
        dialog_root.title("Reorder Desktops")

        # Center the dialog
        window_width = 400
        window_height = 120
        screen_width = dialog_root.winfo_screenwidth()
        screen_height = dialog_root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        dialog_root.geometry(
            f'{window_width}x{window_height}+{center_x}+{center_y}')

        # Add instructions
        tk.Label(dialog_root,
                 text="Enter desktop numbers in desired order (comma-separated):\nExample: 3,1,2").pack(pady=5)

        # Add entry field
        entry = tk.Entry(dialog_root, width=30)
        entry.insert(0, ",".join(map(str, range(1, len(desktop_names)+1))))
        entry.pack(pady=5)
        entry.select_range(0, tk.END)
        entry.focus()

        def save_order():
            try:
                global desktop_names
                new_order = [int(num.strip())
                             for num in entry.get().split(",")]
                if (sorted(new_order) != list(range(1, len(desktop_names)+1)) or
                        len(new_order) != len(desktop_names)):
                    raise ValueError("Invalid order")

                # Reorder desktop names based on new order
                desktop_names = [desktop_names[i-1] for i in new_order]
                save_desktop_names(desktop_names)

                # Recreate icons with new order
                recreate_icons()
                dialog_root.destroy()
            except Exception as e:
                print(f"Invalid order: {e}")
                tk.messagebox.showerror(
                    "Error", "Invalid desktop order entered")

        # Add buttons
        button_frame = tk.Frame(dialog_root)
        button_frame.pack(pady=5)
        tk.Button(button_frame, text="Apply", command=save_order).pack(
            side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel",
                  command=dialog_root.destroy).pack(side=tk.LEFT, padx=5)

        dialog_root.mainloop()

    threading.Thread(target=dialog_thread, daemon=True).start()


def recreate_icons():
    """Recreate all icons with current configuration"""
    global icons
    exit_all()  # Stop existing icons
    icons = []  # Clear icon references
    create_and_run_icons()  # Recreate with new order


# Start creating and running icons
create_and_run_icons()
