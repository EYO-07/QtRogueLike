# inventory_window.py
from PyQt5.QtWidgets import QWidget, QListWidget, QVBoxLayout
from PyQt5.QtCore import Qt

class InventoryWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.9)
        self.layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("background-color: rgba(0, 0, 0, 150); color: white;")
        self.layout.addWidget(self.list_widget)
        self.setLayout(self.layout)
        self.setFixedSize(200, 300)
        self.hide()

    def update_inventory(self, items):
        self.list_widget.clear()
        for item in items:
            self.list_widget.addItem(f"{item.name} ({item.weight}kg)")
        self.show()
        if self.parent():
            parent_geo = self.parent().geometry()
            self.move(parent_geo.x() + parent_geo.width() + 10, parent_geo.y())