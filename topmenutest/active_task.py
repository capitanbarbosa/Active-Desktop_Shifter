from PyQt6.QtWidgets import QWidget, QLineEdit, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSlot
from pyvda import VirtualDesktop

class ActiveTaskWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
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
        
        # Dictionary to store tasks for each desktop
        self.desktop_tasks = {}
        
        # Update the text for the current desktop
        self.update_current_task()
    
    def save_task(self):
        """Save the current text for the current desktop"""
        try:
            current_desktop = VirtualDesktop.current().number
            self.desktop_tasks[current_desktop] = self.text_edit.text()
        except Exception as e:
            print(f"Error saving task: {e}")
    
    def update_current_task(self):
        """Update the text field with the task for the current desktop"""
        try:
            current_desktop = VirtualDesktop.current().number
            current_task = self.desktop_tasks.get(current_desktop, "")
            self.text_edit.setText(current_task)
        except Exception as e:
            print(f"Error updating task display: {e}")
    
    @pyqtSlot()
    def on_desktop_changed(self):
        """Call this when the desktop changes to update the displayed task"""
        self.update_current_task()
