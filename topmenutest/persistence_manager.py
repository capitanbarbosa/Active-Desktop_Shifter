# persistence_manager.py
import json
import os

# Store the persistence file in the same directory as the script
# For a production app, consider using a user-specific config directory (e.g., via appdirs library)
CONFIG_FILE_NAME = "active_tasks_persistence.json"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE_NAME)

class PersistenceManager:
    def __init__(self, file_path=CONFIG_PATH):
        self.file_path = file_path
        # Ensure the directory exists (though for local path it usually does)
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)


    def save_active_tasks(self, tasks_data):
        """
        Saves the active tasks data to a JSON file.
        tasks_data should be a dictionary like: {desktop_number: {"exe_path": "...", "title": "..."}}
        """
        try:
            with open(self.file_path, 'w') as f:
                json.dump(tasks_data, f, indent=4)
        except IOError as e:
            print(f"Error saving active tasks to {self.file_path}: {e}")

    def load_active_tasks(self):
        """
        Loads the active tasks data from a JSON file.
        Returns a dictionary or an empty dictionary if the file doesn't exist or is invalid.
        """
        if not os.path.exists(self.file_path):
            return {}
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                # Ensure desktop numbers (keys) are integers
                return {int(k): v for k, v in data.items()}
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading active tasks from {self.file_path} or file is corrupted: {e}")
            return {}

    def get_task_for_desktop(self, desktop_number):
        """
        Retrieves the persisted task information for a specific desktop.
        """
        tasks = self.load_active_tasks()
        return tasks.get(desktop_number)

    def update_task_for_desktop(self, desktop_number, task_info):
        """
        Updates task info for a specific desktop and saves all tasks.
        task_info should be a dictionary like {"exe_path": "...", "title": "..."}
        An empty title or exe_path can signify no specific task or clearing a task.
        """
        if desktop_number is None or int(desktop_number) == 0: # Avoid saving for invalid desktop numbers
             # print(f"Attempted to update task for invalid desktop number: {desktop_number}")
             return
        tasks = self.load_active_tasks()
        tasks[str(desktop_number)] = task_info # JSON keys are strings
        self.save_active_tasks(tasks)
