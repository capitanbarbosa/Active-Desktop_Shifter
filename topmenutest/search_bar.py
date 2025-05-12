from PyQt6.QtWidgets import QPushButton, QWidget, QLineEdit, QVBoxLayout, QHBoxLayout, QListWidget, QDialog, QLabel, QFileDialog, QMenu
from PyQt6.QtCore import Qt, QDir, QThread, pyqtSignal, pyqtSlot
import os
import fnmatch
import time
import subprocess

class FileSearchWorker(QThread):
    # Custom signals to update the UI
    result_found = pyqtSignal(str)
    search_completed = pyqtSignal(int)
    progress_update = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.search_term = ""
        self.search_dir = ""
        self.cancel_flag = False
        self.max_results = 500
        
    def set_parameters(self, search_term, search_dir):
        self.search_term = search_term.lower()
        self.search_dir = search_dir
        self.cancel_flag = False
        
    def run(self):
        if not self.search_term or not self.search_dir:
            return
            
        count = 0
        dirs_searched = 0
        start_time = time.time()
        
        for root, dirs, files in os.walk(self.search_dir):
            if self.cancel_flag:
                break
                
            dirs_searched += 1
            if dirs_searched % 10 == 0:  # Update progress every 10 directories
                self.progress_update.emit(f"Searching directory {dirs_searched}: {root}")
            
            for file in files:
                if self.cancel_flag:
                    break
                    
                if self.search_term in file.lower():
                    full_path = os.path.join(root, file)
                    self.result_found.emit(full_path)
                    count += 1
                    
                    if count >= self.max_results:
                        self.progress_update.emit(f"Result limit reached ({self.max_results})")
                        self.search_completed.emit(count)
                        return
                        
        elapsed = time.time() - start_time
        self.search_completed.emit(count)

class FileSearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fast File Search")
        self.resize(700, 500)
        
        layout = QVBoxLayout(self)
        
        # Search input area
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter file name to search...")
        self.search_input.returnPressed.connect(self.perform_search)
        search_layout.addWidget(self.search_input)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_directory)
        search_layout.addWidget(self.browse_button)
        
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_search)
        self.cancel_button.setEnabled(False)
        search_layout.addWidget(self.cancel_button)
        
        layout.addLayout(search_layout)
        
        # Directory selection
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Search in:"))
        self.dir_input = QLineEdit()
        self.dir_input.setText(os.path.expanduser("~"))  # Default to user home
        dir_layout.addWidget(self.dir_input)
        layout.addLayout(dir_layout)
        
        # Results list with context menu
        self.results_list = QListWidget()
        self.results_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results_list.customContextMenuRequested.connect(self.show_context_menu)
        self.results_list.itemDoubleClicked.connect(self.open_file)
        layout.addWidget(self.results_list)
        
        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Set up the search worker thread
        self.search_worker = FileSearchWorker()
        self.search_worker.result_found.connect(self.add_result)
        self.search_worker.search_completed.connect(self.search_finished)
        self.search_worker.progress_update.connect(self.update_progress)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2D2D2D;
                color: #FFFFFF;
            }
            QLineEdit {
                background-color: #3D3D3D;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton {
                background-color: #3D3D3D;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4D4D4D;
            }
            QListWidget {
                background-color: #3D3D3D;
                color: #FFFFFF;
                border: 1px solid #555555;
            }
            QLabel {
                color: #FFFFFF;
            }
            QMenu {
                background-color: #3D3D3D;
                color: #FFFFFF;
                border: 1px solid #555555;
            }
            QMenu::item:selected {
                background-color: #4D4D4D;
            }
        """)
    
    def show_context_menu(self, position):
        if not self.results_list.selectedItems():
            return
            
        selected_item = self.results_list.selectedItems()[0]
        file_path = selected_item.text()
        
        context_menu = QMenu(self)
        
        # Add menu options
        open_action = context_menu.addAction("Open File")
        open_location_action = context_menu.addAction("Show in Explorer")
        copy_path_action = context_menu.addAction("Copy File Path")
        
        # Show the menu and get the selected action
        action = context_menu.exec(self.results_list.mapToGlobal(position))
        
        # Handle menu actions
        if action == open_action:
            self.open_file(selected_item)
        elif action == open_location_action:
            self.open_file_location(file_path)
        elif action == copy_path_action:
            # Copy path to clipboard
            from PyQt6.QtGui import QGuiApplication
            QGuiApplication.clipboard().setText(file_path)
            self.status_label.setText("File path copied to clipboard")
    
    def open_file_location(self, file_path):
        try:
            # This command opens Explorer and selects the specified file
            subprocess.run(['explorer', '/select,', os.path.normpath(file_path)])
            self.status_label.setText(f"Opened location of: {os.path.basename(file_path)}")
        except Exception as e:
            self.status_label.setText(f"Error showing file location: {e}")
    
    def browse_directory(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Directory to Search", self.dir_input.text())
        if dir_path:
            self.dir_input.setText(dir_path)
    
    def perform_search(self):
        # Don't start a new search if one is already running
        if self.search_worker.isRunning():
            return
            
        search_term = self.search_input.text()
        search_dir = self.dir_input.text()
        
        if not search_term:
            self.status_label.setText("Please enter a search term")
            return
            
        if not os.path.isdir(search_dir):
            self.status_label.setText("Invalid directory path")
            return
        
        # Clear previous results
        self.results_list.clear()
        self.status_label.setText("Searching...")
        
        # Update UI state
        self.search_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        
        # Start the search in a background thread
        self.search_worker.set_parameters(search_term, search_dir)
        self.search_worker.start()
    
    def cancel_search(self):
        if self.search_worker.isRunning():
            self.search_worker.cancel_flag = True
            self.status_label.setText("Cancelling search...")
    
    @pyqtSlot(str)
    def add_result(self, file_path):
        self.results_list.addItem(file_path)
    
    @pyqtSlot(int)
    def search_finished(self, count):
        # Re-enable UI elements
        self.search_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        
        if self.search_worker.cancel_flag:
            self.status_label.setText(f"Search cancelled. Found {count} files.")
        else:
            self.status_label.setText(f"Search completed. Found {count} files.")
    
    @pyqtSlot(str)
    def update_progress(self, message):
        self.status_label.setText(message)
    
    def open_file(self, item):
        file_path = item.text()
        try:
            # Use os.startfile on Windows to open with default application
            os.startfile(file_path)
        except Exception as e:
            self.status_label.setText(f"Error opening file: {e}")
    
    def closeEvent(self, event):
        # Make sure to stop the thread when closing the dialog
        if self.search_worker.isRunning():
            self.search_worker.cancel_flag = True
            self.search_worker.wait(500)  # Wait for thread to finish, with timeout
        event.accept()


class SearchButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("File Search", parent)
        self.setFixedSize(200, 30)
        self.clicked.connect(self.show_search_ui)
        self.setStyleSheet("""
            QPushButton {
                background-color: #3D3D3D;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4D4D4D;
            }
        """)
        
        self.search_dialog = None

    def show_search_ui(self):
        if not self.search_dialog:
            self.search_dialog = FileSearchDialog(self)
        self.search_dialog.show()
        self.search_dialog.raise_()
        self.search_dialog.activateWindow() 