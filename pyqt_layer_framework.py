# pyqt_layer_framework.py 

# project
from serialization import * 

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
def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        # If the item is a layout, clear it recursively
        if item.layout(): clear_layout(item.layout())
        # If it's a widget, delete it
        elif item.widget():
            widget = item.widget()
            widget.setParent(None)
def is_widget_in_list(list_widget: QListWidget, widget: QWidget) -> bool:
    for i in range(list_widget.count()):
        item = list_widget.item(i)
        if list_widget.itemWidget(item) == widget:
            return True
    return False

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
class Dialog(QDialog, Serializable):
    __serialize_only__ = ["window_width", "window_height", "window_x", "window_y"]
    def __init__(self, parent=None):
        QDialog.__init__(self, parent=parent)
        Serializable.__init__(self)
        self.window_name = "Default"
        self.window_x = 0
        self.window_y = 0 
        self.window_width = 400
        self.window_height = 400 
    def restore_state(self): # should be called on init or else in derived classes.    
        if self.Load_JSON(self.window_name+".ini"):
            self.setGeometry(self.window_x, self.window_y, self.window_width, self.window_height)
    def closeEvent(self, event):
        """Save the game state when the window is closed."""
        rect = self.geometry()
        self.window_x = rect.x()
        self.window_y = rect.y()
        self.window_width = rect.width()
        self.window_height = rect.height()
        try:
            self.Save_JSON(self.window_name+".ini")
        except Exception as e:
            print(f"Error saving game on exit: {e}")
        event.accept()    
    def resizeEvent(self, event):
        # This method is called whenever the window is resized
        rect = self.geometry()
        self.window_x = rect.x()
        self.window_y = rect.y()
        self.window_width = rect.width()
        self.window_height = rect.height()
        super().resizeEvent(event)  # Make sure to call the base class implementation       
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

class DraggableWidget(Widget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_pos = None
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.window().frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.window().move(event.globalPos() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

# -- END

# Wizardry Paradigm : Guides de Creation of Functions by analogy 
# 1. Function as a Spell : Is a short name for something someone desire to be as easy as casting a spell.
# 2. 