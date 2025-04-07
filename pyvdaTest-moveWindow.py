from pyvda import VirtualDesktop, AppView
# # Switch to desktop 1
# VirtualDesktop(4).go()
# Get current window
current_window = AppView.current()
# Move to target desktop (e.g., desktop 2)
target_desktop = VirtualDesktop(1)
current_window.move(target_desktop)