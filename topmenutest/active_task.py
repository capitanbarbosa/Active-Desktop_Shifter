from PyQt6.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSlot, QTimer
from pyvda import VirtualDesktop
import psutil
import win32gui
import win32process

class ActiveTaskWidget(QWidget):
    def __init__(self, parent_menubar, persistence_manager):
        super().__init__(parent_menubar)
        self.parent_menubar = parent_menubar
        self.persistence_manager = persistence_manager
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Create the text editor
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("Enter active task for this desktop...")
        self.text_edit.setMinimumWidth(300)  # Adjust as needed
        self.text_edit.editingFinished.connect(self.save_task)
        
        # Set styling
        self.text_edit.setStyleSheet("""
            QLineEdit {
                background-color: #3D3D3D;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #0077CC;
            }
        """)
        
        self.layout.addWidget(self.text_edit)
        
        # Dictionary to store tasks for each desktop (full titles)
        self.desktop_tasks = {}
        
        # Initial load:
        # Try to get current desktop immediately. If parent_menubar has it (and it's valid), use it.
        # Otherwise, on_desktop_changed (when called by parent) will handle loading later.
        initial_desktop_num_to_load = 0
        if self.parent_menubar:
            initial_desktop_num_to_load = self.parent_menubar.current_desktop_number

        if self.persistence_manager and initial_desktop_num_to_load != 0:
            self.load_persisted_task_for_desktop(initial_desktop_num_to_load)
        elif initial_desktop_num_to_load == 0 : # Still 0, means initial query in parent might have failed or not run
            self.text_edit.setText("Waiting for desktop info...") # Placeholder
        else: # No persistence_manager or other issue
             self.text_edit.setText("No active task")

        # Timer to periodically check and update the active task display
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_active_task_display_and_persist)
        self.update_timer.start(750) # Adjust interval as needed
    
    def save_task(self):
        """Save the current text from QLineEdit for the current desktop to persistence."""
        if not self.parent_menubar or not self.persistence_manager:
            return
        try:
            current_desktop_num = VirtualDesktop.current().number
            if current_desktop_num == 0: return

            user_text = self.text_edit.text()
            
            # Update in-memory cache
            self.desktop_tasks[current_desktop_num] = user_text
            
            # Persist this user-defined task.
            # Storing with an empty exe_path signifies it's user-set or the text itself is primary.
            task_to_persist = {"exe_path": "", "title": user_text} 
            
            self.persistence_manager.update_task_for_desktop(current_desktop_num, task_to_persist)
            
        except Exception as e:
            print(f"Error saving user task: {e}")
    
    def update_current_task(self):
        """Update the text field with the task for the current desktop from self.desktop_tasks."""
        try:
            current_desktop = VirtualDesktop.current().number
            if current_desktop == 0:
                self.text_edit.setText("Waiting for desktop info...") 
                return

            current_task_title = self.desktop_tasks.get(current_desktop, "")
            
            if current_task_title:
                max_len = 35 
                display_title = (current_task_title[:max_len] + '...') if len(current_task_title) > max_len else current_task_title
                self.text_edit.setText(display_title)
            else:
                # If cached title is empty, show placeholder text (which QLineEdit does if text is empty)
                # or explicitly set "No active task"
                self.text_edit.setText("") # Let placeholder show, or "No active task" if that's the placeholder
                                           # Or self.text_edit.setText("No active task") if you want it explicit
        except Exception as e:
            print(f"Error updating task display from cache: {e}")
            self.text_edit.setText("Error") # Indicate error
    
    @pyqtSlot()
    def on_desktop_changed(self):
        """
        Called by TopMenuBar when the virtual desktop changes.
        Loads the persisted task for the new desktop and then triggers an immediate update.
        """
        if not self.parent_menubar or not self.persistence_manager:
            return
        
        current_desktop_num = self.parent_menubar.current_desktop_number
        self.load_persisted_task_for_desktop(current_desktop_num)
        
        # The timer will handle the ongoing updates. 
        # A forced call here might be useful if the timer interval is long.
        self.update_active_task_display_and_persist()

    def get_current_active_window_info(self):
        """
        Tries to get information about the current true foreground application window.
        Returns a dictionary with {"exe_path": "...", "title": "...", "display_title": "..."} or None.
        This function needs to be robust in determining the actual top-level application window,
        potentially using self.parent_menubar.last_active_app_hwnd.
        """
        try:
            hwnd = win32gui.GetForegroundWindow()
            menubar_hwnd = self.parent_menubar.winId().__int__()
            
            target_hwnd = hwnd

            if hwnd == 0: return None

            # If menubar is focused or current window is not top-level, use last known app
            if hwnd == menubar_hwnd or win32gui.GetParent(hwnd) != 0:
                if self.parent_menubar.last_active_app_hwnd and \
                   win32gui.IsWindow(self.parent_menubar.last_active_app_hwnd) and \
                   win32gui.IsWindowVisible(self.parent_menubar.last_active_app_hwnd) and \
                   win32gui.GetParent(self.parent_menubar.last_active_app_hwnd) == 0:
                    target_hwnd = self.parent_menubar.last_active_app_hwnd
                else: # Try to find any other top-level window on the current desktop
                    # This part might need more sophisticated logic to find the "true" active app
                    # For now, if last_active_app_hwnd is not valid, we might not find a suitable window.
                    return None 


            if not win32gui.IsWindowVisible(target_hwnd) or not win32gui.IsWindowEnabled(target_hwnd):
                # Check if it's a UWP app which might be cloaked
                # Advanced UWP detection might be needed if this is a common issue
                is_cloaked = hasattr(win32gui, 'GetWindowLong') and win32gui.GetWindowLong(target_hwnd, win32gui.GWL_EXSTYLE) & 0x00000008 # WS_EX_TOPMOST might be misleading, DWM_CLOAKED is better but harder to get
                if not is_cloaked: # If not cloaked and not visible/enabled, then ignore
                     return None
            
            # Ensure it's a top-level window (no parent)
            if win32gui.GetParent(target_hwnd) != 0 : 
                return None


            title = win32gui.GetWindowText(target_hwnd)
            if not title: return None 

            # Filter out common non-app titles
            excluded_titles = ["Program Manager", "Windows Shell Experience Host"]
            if title in excluded_titles: return None
            # Filter out if the window is an "ApplicationFrameWindow" hosting a UWP app, get child UWP title
            class_name = win32gui.GetClassName(target_hwnd)
            if class_name == "ApplicationFrameWindow":
                # Try to find the actual UWP app window
                def callback(hwnd_child, hwnds):
                    if win32gui.IsWindowVisible(hwnd_child) and win32gui.GetClassName(hwnd_child) != "Windows.UI.Core.CoreWindow": # Heuristic
                        hwnds.append(hwnd_child)
                    return True
                child_windows = []
                win32gui.EnumChildWindows(target_hwnd, callback, child_windows)
                if child_windows:
                    # This logic might need refinement to pick the best child window
                    actual_app_hwnd = child_windows[0] 
                    actual_title = win32gui.GetWindowText(actual_app_hwnd)
                    if actual_title:
                        title = actual_title
                        target_hwnd = actual_app_hwnd # Update target_hwnd for process info

            pid = win32process.GetWindowThreadProcessId(target_hwnd)[1]
            process = psutil.Process(pid)
            exe_path = process.exe()
            
            # Exclude self
            if hasattr(self.parent_menubar, 'main_pid') and pid == self.parent_menubar.main_pid:
                return None

            max_len = 35
            display_title = (title[:max_len] + '...') if len(title) > max_len else title
            
            return {"exe_path": exe_path, "title": title, "display_title": display_title}
        except (psutil.NoSuchProcess, psutil.AccessDenied, win32gui.error, win32process.error):
            return None 
        except Exception as e:
            # print(f"Unexpected error in get_current_active_window_info: {e}")
            return None


    def update_active_task_display_and_persist(self):
        """
        Called by a timer.
        If a user-defined task (marked by empty exe_path) exists, displays its title.
        Otherwise, fetches current active window, updates label, and persists if changed.
        """
        if not self.parent_menubar or not self.persistence_manager:
            return

        # Skip updates when user is actively editing
        if self.text_edit.hasFocus():
            return

        current_desktop_num = self.parent_menubar.current_desktop_number
        if current_desktop_num == 0:
            # Desktop number not yet reliably known, display a waiting message or default.
            # Avoid overwriting user input if text_edit already has something from recent edit.
            if not self.text_edit.text() or self.text_edit.text() == self.text_edit.placeholderText() or self.text_edit.text() == "Waiting for desktop info...":
                 self.text_edit.setText("Waiting for desktop info...")
            return

        persisted_task_info = self.persistence_manager.get_task_for_desktop(current_desktop_num)

        # Check if the persisted task is explicitly user-set or an intentional empty state (exe_path == "")
        # This also covers cases where persisted_task_info might be None (e.g., read error).
        is_task_explicitly_set_or_empty = False
        current_title_from_persistence = "" # Default to empty

        if persisted_task_info and persisted_task_info.get("exe_path") == "":
            is_task_explicitly_set_or_empty = True
            current_title_from_persistence = persisted_task_info.get("title", "")

        if is_task_explicitly_set_or_empty:
            # Persisted task has exe_path: "". This is a user task or intentional empty.
            # Display its title and do not auto-detect.
            max_len = 35
            display_text = (current_title_from_persistence[:max_len] + '...') if len(current_title_from_persistence) > max_len else current_title_from_persistence
            
            if not current_title_from_persistence: # If the persisted title itself is empty
                effective_display_text = "" # Will show placeholder
            else:
                effective_display_text = display_text

            if self.text_edit.text() != effective_display_text:
                self.text_edit.setText(effective_display_text)
            
            if self.desktop_tasks.get(current_desktop_num) != current_title_from_persistence:
                 self.desktop_tasks[current_desktop_num] = current_title_from_persistence
            return # Crucial: Do not proceed to auto-detection

        # Fallthrough: Persisted task was either an auto-detected app (exe_path not empty),
        # or no valid persisted_task_info was found (e.g. None, or missing exe_path key).
        # In these cases, proceed with auto-detection.
        
        active_window_info = self.get_current_active_window_info()
        
        auto_task_to_persist = {"exe_path": "", "title": ""} 
        auto_display_text = "" # Default to empty, shows placeholder "No active task"

        if active_window_info:
            auto_task_to_persist = {
                "exe_path": active_window_info["exe_path"],
                "title": active_window_info["title"]
            }
            auto_display_text = active_window_info['display_title'] 
        
        if self.text_edit.text() != auto_display_text:
            self.text_edit.setText(auto_display_text) # Update QLineEdit
        
        full_auto_title = auto_task_to_persist["title"]
        if self.desktop_tasks.get(current_desktop_num) != full_auto_title: # Update cache
            if full_auto_title:
                self.desktop_tasks[current_desktop_num] = full_auto_title
            else: # Full auto title is empty string
                self.desktop_tasks[current_desktop_num] = ""


        # Persist this auto-detected task if it's different from what was persisted
        # (or if nothing valid was persisted before).
        if persisted_task_info != auto_task_to_persist:
            self.persistence_manager.update_task_for_desktop(current_desktop_num, auto_task_to_persist)

    def load_persisted_task_for_desktop(self, desktop_number):
        """
        Loads and displays the persisted task for the given desktop number.
        Also updates the internal self.desktop_tasks cache.
        """
        if not self.persistence_manager or desktop_number == 0:
            self.text_edit.setText("Waiting for desktop info...")
            self.desktop_tasks.pop(desktop_number, None) 
            return

        task_info = self.persistence_manager.get_task_for_desktop(desktop_number)
        actual_full_title = "" 
        display_text_for_load = "" # Default to empty, QLineEdit will show placeholder

        if task_info and "title" in task_info: 
            actual_full_title = task_info.get("title", "") # Ensure we get a string
            if actual_full_title: # If title is not an empty string
                max_len = 35 
                display_text_for_load = (actual_full_title[:max_len] + '...') if len(actual_full_title) > max_len else actual_full_title
            # else: actual_full_title is "", display_text_for_load remains "", shows placeholder
        
        self.text_edit.setText(display_text_for_load)
        
        # Update cache with the full title (can be empty string)
        self.desktop_tasks[desktop_number] = actual_full_title
