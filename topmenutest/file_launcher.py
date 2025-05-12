# file_launcher.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFileDialog, QMenu
from PyQt6.QtCore import Qt, pyqtSignal, QProcess
from PyQt6.QtGui import QIcon
import os
import json

# File to store launcher shortcuts
LAUNCHER_CONFIG_FILE = "launcher_shortcuts.json"

class FileLauncherButton(QPushButton):
    def __init__(self, file_path="", parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setText(self._get_display_name())
        self.setToolTip(file_path)
        self.setFixedSize(40, 30)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet("""
            QPushButton {
                background-color: #3f4652;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4D4D4D;
            }
        """)
        self.clicked.connect(self.launch_file)
    
    def _get_display_name(self):
        if not self.file_path:
            return "+"
        return os.path.basename(self.file_path)[:1].upper()
    
    def launch_file(self):
        if not self.file_path:
            # If no file path, open file dialog
            self.parent().open_file_dialog()
            return
            
        try:
            # Use os.startfile on Windows to open with default application
            os.startfile(self.file_path)
        except Exception as e:
            print(f"Error launching file {self.file_path}: {e}")
    
    def set_file_path(self, file_path):
        self.file_path = file_path
        self.setText(self._get_display_name())
        self.setToolTip(file_path)

class FileLauncherWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        
        # Set of launcher buttons
        self.launcher_buttons = []
        
        # Load saved shortcuts
        self.shortcuts = self.load_shortcuts()
        
        # Initialize the UI
        self.init_ui()
    
    def init_ui(self):
        # Create launcher buttons for each saved shortcut
        for path in self.shortcuts:
            self.add_launcher_button(path)
        
        # Add button to add more shortcuts
        self.add_launcher_button()
    
    def add_launcher_button(self, file_path=""):
        button = FileLauncherButton(file_path, self)
        self.launcher_buttons.append(button)
        self.layout.addWidget(button)
        
        # Context menu for removing shortcuts
        if file_path:
            button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda pos, btn=button: self.show_context_menu(pos, btn))
    
    def show_context_menu(self, pos, button):
        context_menu = QMenu(self)
        remove_action = context_menu.addAction("Remove Shortcut")
        action = context_menu.exec(button.mapToGlobal(pos))
        
        if action == remove_action:
            self.remove_launcher_button(button)
    
    def remove_launcher_button(self, button):
        if button in self.launcher_buttons:
            self.shortcuts.remove(button.file_path)
            self.launcher_buttons.remove(button)
            button.deleteLater()
            self.save_shortcuts()
    
    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File or Application", "",
            "All Files (*);;Applications (*.exe);;Documents (*.pdf *.docx *.txt)")
        
        if file_path:
            # If this was triggered from an empty button, update it
            # Otherwise, add a new button
            empty_button = None
            for btn in self.launcher_buttons:
                if not btn.file_path:
                    empty_button = btn
                    break
            
            if empty_button:
                empty_button.set_file_path(file_path)
            else:
                self.add_launcher_button(file_path)
            
            # Add to shortcuts and save
            if file_path not in self.shortcuts:
                self.shortcuts.append(file_path)
                self.save_shortcuts()
            
            # Always ensure we have an empty "add" button
            if all(btn.file_path for btn in self.launcher_buttons):
                self.add_launcher_button()
    
    def load_shortcuts(self):
        try:
            if os.path.exists(LAUNCHER_CONFIG_FILE):
                with open(LAUNCHER_CONFIG_FILE, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading shortcuts: {e}")
            return []
    
    def save_shortcuts(self):
        try:
            with open(LAUNCHER_CONFIG_FILE, 'w') as f:
                json.dump(self.shortcuts, f, indent=4)
        except Exception as e:
            print(f"Error saving shortcuts: {e}")