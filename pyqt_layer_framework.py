# pyqt_layer_framework.py 

# third-party
from PyQt5.QtWidgets import QWidget, QListWidget, QVBoxLayout, QPushButton, QHBoxLayout, QMenu, QDialog, QLabel, QTextEdit, QSizePolicy, QInputDialog, QLayout
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QTextCursor, QColor

def color_to_css(foreground):
    if isinstance(foreground, QColor):
        return foreground.name(QColor.HexArgb) if foreground.alpha() < 255 else foreground.name()
    elif isinstance(foreground, str):
        return foreground  # assume it's a valid CSS color string
    return "white"  # default fallback
def set_relative_horizontal_position(widget, widget_reference, side = "right", gap = 10):
    if not widget or not widget_reference: return     
    # -- 
    ref_pos = widget_reference.mapToGlobal(widget_reference.rect().topLeft())
    ref_width = widget_reference.width()
    ref_height = widget_reference.height()
    _width = widget.width()
    _height = widget.height()
    # --
    x = 0
    match side:
        case "right":
            x = ref_pos.x() + ref_width + gap 
        case "left":
            x = ref_pos.x() - _width - gap
        case _:
            raise ValueError(f"Unsupported side: {side}")    
    y = ref_pos.y() + (ref_height - _height) // 2 # Vertical centering
    widget.move(x, y)
def set_relative_vertical_position(widget, widget_reference, side = "down", gap = 5):
    if not widget or not widget_reference: return     
    # -- 
    ref_pos = widget_reference.mapToGlobal(widget_reference.rect().topLeft())
    ref_width = widget_reference.width()
    ref_height = widget_reference.height()   
    _width = widget.width()
    _height = widget.height()
    # -- 
    x = ref_pos.x() + (ref_width - _width) // 2
    y = 0
    match side:
        case "down":
            y = ref_pos.y() + ref_height + gap 
        case "top":
            y = ref_pos.y() - _height - gap
        case _:
            raise ValueError(f"Unsupported side: {side}")
    widget.move(x, y)
def set_text_cursor_to(text_widget, position = QTextCursor.End):
    cursor = text_widget.textCursor()
    cursor.movePosition(position)
    text_widget.setTextCursor(cursor)
    text_widget.ensureCursorVisible()
def apply_filter_to_list_widget(list_widget, text):
    for index in range(list_widget.count()):
        item = list_widget.item(index)
        item.setHidden(text.lower() not in item.text().lower())

# -- helper classes
class VLayout(QVBoxLayout):
    def __truediv__(self, other):
        if isinstance(other, QWidget):
            self.addWidget(other)
        elif isinstance(other, QLayout):
            self.addLayout(other)
        else:
            raise TypeError(f"Cannot divide layout by object of type {type(other).__name__}")
        return self
class HLayout(QHBoxLayout):
    def __truediv__(self, other):
        if isinstance(other, QWidget):
            self.addWidget(other)
        elif isinstance(other, QLayout):
            self.addLayout(other)
        else:
            raise TypeError(f"Cannot divide layout by object of type {type(other).__name__}")
        return self
class Dialog(QDialog):
    def __truediv__(self, other):
        if isinstance(other, QLayout):
            self.setLayout(other)
        else:
            raise TypeError(f"Cannot divide layout by object of type {type(other).__name__}")
        return self
class Widget(QWidget):
    def __truediv__(self, other):
        if isinstance(other, QLayout):
            self.setLayout(other)
        else:
            raise TypeError(f"Cannot divide layout by object of type {type(other).__name__}")
        return self
    def __add__(self, other):
        if not isinstance(other, QWidget):
            raise TypeError(f"Cannot add object of type {type(other).__name__} to Widget")
        container = Widget()
        layout = VLayout()
        layout.addWidget(self)
        layout.addWidget(other)
        container.setLayout(layout)
        return container
    def __sub__(self, other):
        if not isinstance(other, QWidget):
            raise TypeError(f"Cannot subtract object of type {type(other).__name__} from Widget")
        container = Widget()
        layout = HLayout()
        layout.addWidget(self)
        layout.addWidget(other)
        container.setLayout(layout)
        return container

# -- END