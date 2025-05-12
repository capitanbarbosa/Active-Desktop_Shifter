from PyQt6.QtWidgets import QPushButton

class StartButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("Start", parent)
        self.setFixedSize(60, 30)
        self.clicked.connect(self.show_start_menu)
        self.setStyleSheet(""" # Basic styling, can be inherited or customized
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

    def show_start_menu(self):
        # TODO: Implement start menu functionality
        print("Start menu clicked (placeholder)")
        pass 