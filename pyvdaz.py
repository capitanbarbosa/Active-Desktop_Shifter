from pyvda import AppView, get_apps_by_z_order, VirtualDesktop, get_virtual_desktops

number_of_active_desktops = len(get_virtual_desktops())
print(f"There are {number_of_active_desktops} active desktops")

current_desktop = VirtualDesktop.current()
print(f"Current desktop is number {current_desktop}")

current_window = AppView.current()
target_desktop = VirtualDesktop(1)
current_window.move(target_desktop)
print(f"Moved window {current_window.hwnd} to {target_desktop.number}")

print("Going to desktop number" + str(target_desktop))
VirtualDesktop(1).go()

print("Pinning the current window")
AppView.current().pin()
# ...