from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt

class MessagePopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Non-modal dialog with translucency
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # Show without taking focus
        self.setWindowOpacity(0.7)  # 70% opaque
        self.setModal(False)  # Non-blocking
        self.setFocusPolicy(Qt.NoFocus)  # Prevent keyboard focus

        # Layout
        self.layout = QVBoxLayout()
        # self.layout.setSpacing(2)  # Small gap between messages
        #self.layout.setContentsMargins(0, 0, 0, 0)  # Padding around messages
        self.labels = []  # List to store QLabel widgets for messages
        self.setLayout(self.layout)

        # Base size (updated in set_message)
        self.base_height = 31  # Height per message
        self.max_messages = 5  # Limit to prevent oversized pop-up
        self.hide()  # Hidden by default
        print("MessagePopup initialized, hidden by default")

    def set_message(self, messages):
        """Display a list of messages, newest at the top."""
        # Clear existing labels
        for label in self.labels:
            self.layout.removeWidget(label)
            label.deleteLater()
        self.labels.clear()

        # If no messages, hide the pop-up
        if not messages:
            self.hide()
            print("MessagePopup hidden, no messages")
            return

        # Limit to max_messages
        messages = messages[-self.max_messages:]  # Take newest messages
        print(f"MessagePopup displaying {len(messages)} messages: {messages}")

        # Create a QLabel for each message (newest first)
        for message in reversed(messages):  # Reverse to show newest at top
            label = QLabel(message, self)
            label.setStyleSheet("""
                background-color: rgba(0, 0, 0, 150);  /* Semi-transparent black */
                color: white;
                padding: 0px;
                border-radius: 0px;
                font-size: 10px;
                font-weight: bold;
            """)
            label.setWordWrap(True)
            label.setFocusPolicy(Qt.NoFocus)
            self.layout.addWidget(label)
            self.labels.append(label)

        # Resize pop-up based on number of messages
        height = len(messages) * self.base_height
        self.setFixedSize(500, height+3)

        # Position below the main window
        if self.parent():
            parent_geo = self.parent().geometry()
            target_x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            target_y = parent_geo.y() + parent_geo.height() + 10
            self.move(target_x, target_y)
            print(f"MessagePopup positioned at ({target_x}, {target_y}), parent at ({parent_geo.x()}, {parent_geo.y()}), size {parent_geo.width()}x{parent_geo.height()}, popup height={height}")
        else:
            self.move(100, 300)
            print(f"MessagePopup positioned at (100, 300), no parent")

        # Show and ensure main window retains focus
        self.show()
        if self.parent():
            self.parent().setFocus()
            print("Focus restored to main window")