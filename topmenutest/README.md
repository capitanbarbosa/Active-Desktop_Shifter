# Wiz Windows Active Top Menu

here i go again on my own,
going down the only road i've ever known.


We have successfully restructured your application into a more modular design:
- app.py: Contains the main TopMenuBar window, which now primarily acts as an assembler for various components. It also holds the application entry point (main function).

- constants.py: Centralizes shared constants like DESKTOP_NAMES and Windows API values.

- desktop_switcher.py: Manages the DesktopButton widgets and their logic for switching desktops and moving windows.

- system_stats.py: Handles the display and updating of CPU and Memory statistics.

- start_menu.py: Provides the StartButton component (functionality is a placeholder).

- search_bar.py: Provides the SearchButton component (functionality is a placeholder).

- appbar_manager.py: Encapsulates all the logic for registering the TopMenuBar as a Windows App Bar, managing its position, and handling related window events.

