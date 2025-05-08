# gui.py

# project
from reality import *
from globals_variables import *
from events import *

# built-in
import os
from datetime import datetime

# third-party
from PyQt5.QtWidgets import QWidget, QListWidget, QVBoxLayout, QPushButton, QHBoxLayout, QMenu, QDialog, QLabel, QTextEdit, QSizePolicy, QInputDialog
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QTextCursor, QColor

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

# -- helpers 
def item_text_color(game_item):
    if isinstance(game_item, Weapon):
        return QColor("white")
    if isinstance(game_item, Equippable): 
        return QColor("cyan")
    if isinstance(game_item, Food): 
        return QColor("yellow")
    if isinstance(game_item, Resource): 
        return QColor("magenta") 
    return QColor("white")
def info(game_item):
    return game_item.info(), item_text_color(game_item)
def color_to_css(foreground):
    if isinstance(foreground, QColor):
        return foreground.name(QColor.HexArgb) if foreground.alpha() < 255 else foreground.name()
    elif isinstance(foreground, str):
        return foreground  # assume it's a valid CSS color string
    return "white"  # default fallback

# -- constructors 
def new_text(foreground = "white", layout = None):
    color_css = color_to_css(foreground)
    text_edit = QTextEdit()
    text_edit.setStyleSheet(f"""
        QTextEdit {{
            background-color: rgba(0, 0, 0, 150);
            color: {color_css};
            border: 1px solid rgba(255, 255, 255, 50);
            border-radius: 5px;
            padding: 5px;
            font-size: 11px;
        }}
    """)
    text_edit.setFocusPolicy(Qt.StrongFocus)
    if layout is None: return text_edit
    layout.addWidget(text_edit)
    return text_edit
def new_button(label, callback, foreground = "white", layout = None):
    color_css = color_to_css(foreground)
    button = QPushButton(label)
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: rgba(0, 0, 0, 150);
            color: {color_css};
            border: 1px solid rgba(255, 255, 255, 50);
            border-radius: 5px;
            padding: 5px;
        }}
        QPushButton:hover {{
            background-color: rgba(255, 255, 255, 20);
        }}
    """)
    button.clicked.connect(callback)
    if layout is None: return button 
    layout.addWidget(button)
    return button

# -- set window properties

# 1. don't steals focus 
# 2. non modal 
# 3. small square size 
def set_properties_non_modal_popup(wdg, title):
    if not isinstance(wdg, QDialog): return 
    #self.setWindowFlags(Qt.FramelessWindowHint) # don't work 
    wdg.setAttribute(Qt.WA_TranslucentBackground)
    wdg.setWindowOpacity(POPUP_GUI_ALPHA) 
    wdg.setFocusPolicy(Qt.NoFocus) # Prevent stealing focus
    wdg.setModal(False) # Non-blocking
    wdg.setWindowTitle(title)
    wdg.setFixedSize(POPUP_WIDTH, POPUP_HEIGHT)  # Similar size to InventoryWindow 
def set_properties_layout(layout):
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(5)

# Classes 
class JournalWindow(Dialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        set_properties_non_modal_popup(self, "Journal")
        self.build_parts()
        self.assemble_parts()
        # -- 
        self.hide()  # Hidden by default
        self.update_position()
        if self.parent(): self.parent().setFocus()
    def build_parts(self):
        self.layout = VLayout() # vertical 
        self.text_edit = new_text(foreground = "yellow")
        self.save_button = new_button("Save", self.save_journal)
        self.log_button = new_button("Log Entry", self.log_diary_entry)
    def assemble_parts(self):
        set_properties_layout(self.layout)
        self/( self.layout/self.text_edit/( HLayout()/self.save_button/self.log_button ) )
    def whereAmI(self):
        player = self.parent().player
        if not player: return ""
        parent = self.parent()
        if not parent: return ""
        map = parent.map 
        if not map: return ""
        dx = map.width//3
        dy = map.height//3
        X_1 = dx 
        X_2 = 2*dx 
        Y_1 = dy 
        Y_2 = 2*dy
        x = player.x 
        y = player.y 
        if x<X_1: # west
            if y<Y_1: # northwest
                return "I'm on northwest part of this region, where should I go ? ..." 
            elif y<Y_2: # west
                return "I'm (going to/in) west, let's see what I find ..." 
            else: # southwest
                return "I'm on southwest part of this region, where should I go ? ..." 
        elif x<X_2: # middle x
            if y<Y_1: # north 
                return "I'm (going to/in) north, let's see what I find ..."
            elif y<Y_2: # middle 
                return "Feeling lost, I'm in the middle of nowhere, should walk for a while until I find something ..."
            else: # south
                return "I'm (going to/in) south, let's see what I find ..."
        else: # east
            if y<Y_1: # northeast
                return "I'm on northeast part of this region, where should I go ? ..." 
            elif y<Y_2: # east
                return "I'm (going to/in) east, let's see what I find ..."
            else: # southest
                return "I'm on southeast part of this region, where should I go ? ..."
        return ""
    def update_position(self):
        """Position the journal window to the right of the parent window, vertically centered."""
        if self.parent():
            parent_pos = self.parent().mapToGlobal(self.parent().rect().topLeft())
            parent_width = self.parent().width()
            parent_height = self.parent().height()
            journal_width = self.width()
            journal_height = self.height()
            x = parent_pos.x() + parent_width + 10  # 10px gap to the right
            y = parent_pos.y() + (parent_height - journal_height) // 2  # Vertical centering
            self.move(x, y)

    def save_journal(self):
        """Save journal contents to the current slot's journal file."""
        if not self.parent():
            return
        slot = self.parent().current_slot if hasattr(self.parent(), 'current_slot') else 1
        saves_dir = "./saves"
        journal_file = os.path.join(saves_dir, f"journal_{slot}.txt")
        try:
            os.makedirs(saves_dir, exist_ok=True)
            with open(journal_file, "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())
            self.parent().add_message("Journal saved")
        except Exception as e:
            self.parent().add_message(f"Failed to save journal: {e}")
            print(f"Error saving journal to {journal_file}: {e}")
            
    def log_diary_entry(self):
        """Create a formatted diary entry with day, map coordinates, and special event text."""
        if not self.parent():
            return
        # Calculate day (1 day = 1000 turns)
        day = self.parent().current_day
        map_coords = self.parent().current_map
        # Collect special event texts based on flags
        special_texts = []
        if getattr(self.parent(), 'low_hp_triggered', False):
            special_texts.append("I almost died, that enemy was tough, bastard.")
            self.parent().low_hp_triggered = False  # Reset flag
        if getattr(self.parent(), 'low_hunger_triggered', False):
            special_texts.append("I’m hungry, I need food right now, I could eat a horse.")
            self.parent().low_hunger_triggered = False  # Reset flag
        special_text = "\n".join(special_texts) if special_texts else "All is calm for now."
        # Format entry
        # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = (
            f"Day {day}, Map ({map_coords[0]},{-map_coords[1]},{map_coords[2]}), Position ({self.parent().player.x},{(self.parent().grid_height) - (self.parent().player.y)})\n"
            f"{special_text} {self.whereAmI()}\n"
        )
        self.append_text(entry)
        self.parent().add_message("Diary entry logged")
    
    def log_quick_diary_entry(self):
        """Create a formatted diary entry with day, map coordinates, and special event text."""
        if not self.parent():
            return
        # Calculate day (1 day = 1000 turns)
        day = self.parent().turn // 1000 + 1
        map_coords = self.parent().current_map
        # Collect special event texts based on flags
        special_texts = []
        if getattr(self.parent(), 'low_hp_triggered', False):
            special_texts.append("I almost died, that enemy was tough, bastard.")
            self.parent().low_hp_triggered = False  # Reset flag
        if getattr(self.parent(), 'low_hunger_triggered', False):
            special_texts.append("I’m hungry, I need food right now, I could eat a horse.")
            self.parent().low_hunger_triggered = False  # Reset flag
        if getattr(self.parent(),"last_encounter_description"):
            special_texts.append(self.parent().last_encounter_description)
            self.parent().last_encounter_description = ""
        special_text = "\n".join(special_texts) if special_texts else "All is calm for now."
        # Format entry
        # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = (
            f"Position ({map_coords[0]},{-map_coords[1]},{map_coords[2]}) {self.parent().player.x},{(self.parent().grid_height) - (self.parent().player.y)} {special_text} {self.whereAmI()}\n"
        )
        self.append_text(entry)
        self.parent().add_message("Diary entry logged")
    
    def showEvent(self, event):
        """Ensure the text is scrolled to the end when the journal is shown."""
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_edit.setTextCursor(cursor)
        self.text_edit.ensureCursorVisible()
        super().showEvent(event)
        if self.parent():
            self.parent().setFocus()
    
    def append_text(self, text):
        """Append text to the journal with a timestamp and scroll to end."""
        #timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_text = self.text_edit.toPlainText()
        new_text = f"{text}\n" if current_text else f"{text}"
        self.text_edit.setPlainText(current_text.rstrip("\n") +2*"\n" + new_text)
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_edit.setTextCursor(cursor)
        self.text_edit.ensureCursorVisible()
        self.save_journal()  # Autosave after appending
        
    def clear_text(self):
        self.text_edit.setPlainText("")

    def load_journal(self, slot=1):
        """Load journal contents from the current slot's journal file."""
        saves_dir = "./saves"
        journal_file = os.path.join(saves_dir, f"journal_{slot}.txt")
        try:
            with open(journal_file, "r", encoding="utf-8") as f:
                self.text_edit.setPlainText(f.read())
        except FileNotFoundError:
            self.text_edit.setPlainText("")  # Empty journal if file doesn't exist
        except Exception as e:
            self.parent().add_message(f"Failed to load journal: {e}")
            print(f"Error loading journal from {journal_file}: {e}")
            self.text_edit.setPlainText("")
        # Move cursor to end and scroll
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_edit.setTextCursor(cursor)
        self.text_edit.ensureCursorVisible()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape or key == Qt.Key_J: # set focus to parent 
            if self.parent():
                self.parent().setFocus()
        else:
            super().keyPressEvent(event)

class MessagePopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        #self.setWindowFlags(Qt.FramelessWindowHint)
        # Non-modal dialog with translucency
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # Show without taking focus
        self.setWindowOpacity(0.7)  # 70% opaque
        self.setModal(False)  # Non-blocking
        self.setFocusPolicy(Qt.NoFocus)  # Prevent keyboard focus
        # Layout
        self.layout = QVBoxLayout()
        self.label = QLabel(self) 
        self.label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 150);
            color: white;
            padding: 5px;
            border-radius: 5px;
            font-size: 10px;
            font-weight: bold;
        """)
        self.label.setWordWrap(True)
        self.label.setFocusPolicy(Qt.NoFocus)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        # Base size (updated in set_message)
        self.base_height = 31  # Height per message
        self.max_messages = 15  # Limit to prevent oversized pop-up
        self.setWindowTitle("Messages")
        self.hide()  # Hidden by default

    def set_message(self, messages):
        """Display a list of messages, newest at the top."""
        # If no messages, hide the pop-up
        if not messages:
            self.hide()
            return
                
        # Limit to max_messages
        messages = messages[-self.max_messages:]  # Take newest messages
        text = " | ".join(reversed(messages))  # Newest at top
        self.label.setText(text)
        
        # Position below the main window
        parent_height = 400
        parent_width = 400
        parent_geo = None
        target_x = 100
        target_y = 300
        if self.parent():
            parent_geo = self.parent().geometry()
            parent_width = parent_geo.width()
            parent_height = parent_geo.height()
        if parent_geo.x() == 0 and parent_geo.y() == 0 : 
            self.hide()
            return 
        # --
        target_x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
        target_y = parent_geo.y() + parent_geo.height() + 10
        # adjust size
        fixed_width = parent_width
        self.label.setFixedWidth(fixed_width)
        # self.setFixedSize(fixed_width + 20, self.label.height() + 20)
        self.label.adjustSize()
        self.adjustSize()
        self.move(target_x, target_y)        
        # Show and ensure main window retains focus
        self.show()
            
        if self.parent():
            self.parent().setFocus()

class SelectionBox(QWidget):
    def __init__(self, item_list = [f"Option {i}" for i in range(5)], action = lambda x, instance: instance.close(), parent=None, **kwargs):
        super().__init__(parent)
        self.action = action 
        self.kw = kwargs
        self.list_dictionary = { "main": item_list }
        self.current_key = "main"
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.7)  # 70% opaque, like MessagePopup
        self.setWindowModality(Qt.ApplicationModal)  # This is the trick!
        self.setFocusPolicy(Qt.StrongFocus)          # Accepts focus
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)
        self.list_widget_objects = []
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: rgba(0, 0, 0, 150);
                color: white;
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: rgba(255, 255, 255, 20);
                color: cyan; 
            }
        """)
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # self.list_widget.itemDoubleClicked.connect(self.action)
        self.list_widget.installEventFilter(self) # now the list_widget will use the keyPressEvent function 
        #self.list_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)        
        self.list_widget.setCurrentRow(len(self.list_widget)//2)
        self.layout.addWidget(self.list_widget)
        self.setLayout(self.layout)
        self.set_list()
        self.setFocus()
        self.list_widget.setFocus()
    def get_current_list(self):
        return self.current_key
    def add_list(self, key, item_list):
        self.list_dictionary.update({key:item_list})
    def set_list(self, key = "main", item_list = None):
        if not item_list is None: self.add_list(key, item_list)
        self.list_widget.clear()
        for it in self.list_dictionary[key]:
            self.list_widget.addItem(it)
        self.current_key = key
        self.list_widget.setCurrentRow(len(self.list_widget)//2)
        # Set fixed size to fit items exactly
        row_count = self.list_widget.count()
        row_height = self.list_widget.sizeHintForRow(0) if row_count > 0 else 20
        spacing = self.list_widget.spacing()
        frame = 2 * self.list_widget.frameWidth()
        total_height = row_height * row_count + spacing + frame
        #self.list_widget.setFixedHeight(total_height)
        # Get max width of all items
        max_width = max(self.list_widget.sizeHintForIndex(self.list_widget.model().index(i, 0)).width() for i in range(row_count)) if row_count > 0 else 100
        #self.list_widget.setFixedWidth(max_width + 100)
        self.list_widget.resize(max_width+100, total_height)
    def eventFilter(self, obj, event):
        if obj == self.list_widget and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                current_item = self.list_widget.currentItem()
                if current_item:
                    self.do_enter_action(current_item)
                    return True
            if event.key() == Qt.Key_Escape:
                self.close()
                return True
            if event.key() == Qt.Key_Up:
                if self.list_widget.currentRow() == 0:
                    return True
                else:
                    return super().eventFilter(obj, event)
            if event.key() == Qt.Key_Down:
                if self.list_widget.currentRow() == len(self.list_widget)-1:
                    return True
                else:
                    return super().eventFilter(obj, event)
            if event.key() in (Qt.Key_Left, Qt.Key_Right):
                return True 
        return super().eventFilter(obj, event)
    def do_enter_action(self, item=None):
        if not item: 
            item = self.list_widget.currentItem()
        self.action(self.current_key, item.text(),self, **self.kw)
        
class InventoryWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        #self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.8)  # 70% opaque, like MessagePopup
        self.setFocusPolicy(Qt.NoFocus)  # Prevent stealing focus
        self.setModal(False)  # Non-blocking
        # Layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)
        # Item list
        self.list_widget_objects = []
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: rgba(0, 0, 0, 150);
                color: white;
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: rgba(255, 255, 255, 20);
                color: cyan; 
            }
        """)
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.itemDoubleClicked.connect(self.item_double_click)  # Double-click to equip
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.list_widget.installEventFilter(self) # now the list_widget will use the keyPressEvent function 
        self.layout.addWidget(self.list_widget)
        self.list_widget_last_size = 0
        # Buttons
        button_layout = QHBoxLayout()
        self.equip_button = QPushButton("Equip/Use")
        self.equip_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 150);
                color: white;
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 20);
            }
        """)
        self.equip_button.clicked.connect(self.item_double_click)
        button_layout.addWidget(self.equip_button)
        self.drop_button = QPushButton("Drop")
        self.drop_button.setStyleSheet(self.equip_button.styleSheet())
        self.drop_button.clicked.connect(self.drop_item)
        button_layout.addWidget(self.drop_button)
        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)
        # Initial size
        self.setFixedSize(400, 400)
        self.setWindowTitle("Inventory")
        self.hide()  # Hidden by default
        self.parent().setFocus()

    def eventFilter(self, obj, event):
        if obj == self.list_widget and event.type() == QEvent.KeyPress:
            # self.current_list_widget_item_index = self.list_widget.currentRow()
            # print("Current Index:", self.current_list_widget_item_index)
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                current_item = self.list_widget.currentItem()
                if current_item:
                    self.item_double_click(current_item)
                    return True
            elif event.key() == Qt.Key_Delete:
                current_item = self.list_widget.currentItem()
                if current_item:
                    self.drop_item(current_item)
                    return True
        return super().eventFilter(obj, event)

    def get_quality(self, game_item):
        if not hasattr(game_item, "durability_factor"): return ""
        qlt = game_item.durability_factor
        if qlt>=0.998: 
            return "master-crafted"
        elif qlt>=0.95:
            return "durable"
        elif qlt>=0.90:
            return "bad-quality"
        else:
            return "junk"

    def label_for(self,game_item):
        return info(game_item)
    
    def update_inventory(self, player):
        """Update the list with the player's current items."""
        self.player = player  # Store player reference
        # --
        last_list_widget_size = len(self.list_widget_objects)
        last_list_widget_current_item_index = self.list_widget.currentRow()
        # -- 
        self.list_widget_objects.clear()
        self.list_widget.clear()
        wdg_index = 0
        for item in player.items:     
            label_text, qt_color = self.label_for(item)
            self.list_widget.addItem( label_text )
            item_widget = self.list_widget.item(wdg_index)
            item_widget.setForeground(qt_color)
            self.list_widget_objects.append(item)
            wdg_index += 1
        # equipped 
        b_equipped = False
        for slot in EQUIPMENT_SLOTS:
            equipped_item = getattr(player, slot)
            if equipped_item:
                b_equipped = True
                label_text, qt_color = self.label_for(equipped_item)
                self.list_widget.addItem( "* "+label_text )
                item_widget = self.list_widget.item(wdg_index)
                item_widget.setForeground(qt_color)
                self.list_widget_objects.append(equipped_item)
                wdg_index += 1
        
        if player.items or b_equipped:
            self.show()
            self.update_position()
            self.parent().setFocus()
        else:
            self.hide()
        if last_list_widget_size == len(self.list_widget_objects): # same size
            self.list_widget.setCurrentRow(last_list_widget_current_item_index)
        elif last_list_widget_size == len(self.list_widget_objects)-1: # size -1
            self.list_widget.setCurrentRow(last_list_widget_current_item_index-1)
        else:
            self.list_widget.setCurrentRow(0)
            
    def update_position(self):
        """Position the inventory window to the left of the parent window, vertically centered."""
        if self.parent():
            # Get top-left global position of the parent window
            parent_pos = self.parent().mapToGlobal(self.parent().rect().topLeft())
            parent_width = self.parent().width()
            parent_height = self.parent().height()

            # Inventory window size
            inv_width = self.width()
            inv_height = self.height()

            # New x and y positions
            x = parent_pos.x() - inv_width - 10  # 10 px gap to the left
            y = parent_pos.y() + (parent_height - inv_height) // 2  # Vertical centering

            self.move(x, y)
                
    def show_context_menu(self, pos):
        """Show a context menu for equip and drop actions."""
        item = self.list_widget.itemAt(pos)
        if item:
            menu = QMenu(self)
            equip_action = menu.addAction("Equip")
            drop_action = menu.addAction("Drop")
            action = menu.exec_(self.list_widget.mapToGlobal(pos))
            if action == equip_action:
                self.equip_item(item)
            elif action == drop_action:
                self.drop_item(item)

    def item_double_click(self, item=None):
        """Equip the selected or provided item."""
        # print("equip_item ()* || ",self.player.primary_hand, self.player.items)
        if not item: 
            item = self.list_widget.currentItem()
        if item:
            wdg_index = self.list_widget.row(item)
            game_item = self.list_widget_objects[wdg_index]
            ply_index = self.player.get_item_index(game_item)           
            # print("equip_item()* || ... |", ply_index, wdg_index)
            if ply_index == wdg_index: # not equipped 
                if isinstance(game_item, Equippable):
                    if self.player.equip_item(game_item, game_item.slot):
                        self.parent().add_message(f"Equipped {game_item.name}, {game_item.description}")
                        self.parent().draw_hud()  # Update HUD if needed
                    else:
                        self.parent().add_message(f"Cannot equip {game_item.name}")
                    self.update_inventory(self.player)  # Refresh list
                elif isinstance(game_item, Item):
                    if game_item in self.player.items:                    
                        self.parent().events.append(UseItemEvent(self.player, game_item))
                        #self.parent().add_message(f"{game_item.name} used")
                else:
                    self.parent().add_message(f"{game_item.name} is not equippable or usable")
            else: # equipped
                if isinstance(game_item, Equippable):
                    self.parent().add_message(f"Unequipped")
                    self.player.unequip_item(game_item.slot)
            self.parent().game_iteration() 
        self.update_inventory(self.player) # Refresh list            
        self.parent().setFocus()  # Return focus to game

    def drop_item(self, item=None):
        """Drop the selected or provided item to the current tile."""
        if not item:
            item = self.list_widget.currentItem()
        if item:            
            index = self.list_widget.row(item)
            if index>=len(self.player.items): 
                self.parent().add_message(f"Can't drop equipped item")
                return 
            game_item = self.player.items[index]
            if game_item == self.player.primary_hand: 
                self.parent().add_message(f"Can't drop equipped item: {game_item.name}")
                return 
            if game_item == self.player.torso: 
                self.parent().add_message(f"Can't drop equipped item: {game_item.name}")
                return
            tile = self.parent().map.get_tile(self.player.x, self.player.y)
            if tile:
                tile.add_item(game_item)
                self.player.remove_item(game_item)
                self.parent().add_message(f"Dropped {game_item.name}")
                self.update_inventory(self.player)  # Refresh list
                self.parent().dirty_tiles.add((self.player.x, self.player.y))  # Redraw tile
                self.parent().draw_grid()  # Update grid
            else:
                self.parent().add_message("Cannot drop item: invalid tile")
            self.parent().game_iteration() 
        self.parent().setFocus()  # Return focus to game    

# Menus 
def main_menu(menu, item, instance, game_instance):
    if menu == "main":
        match item:
            case "Resume": instance.close()
            case "Start New Game": 
                new_name = QInputDialog.getText(instance, 'Input Dialog', 'Character Name :')
                if new_name[0]:
                    game_instance.start_new_game(new_name[0])
                    instance.close()
            case "Load Game >": instance.set_list("Load Game >")
            case "Save Game >": instance.set_list("Save Game >")
            case "Quit to Desktop": game_instance.close()
            case "Character Settings >": instance.set_list("Character Settings >")
    elif menu == "Character Settings >":
        match item:
            case "..": instance.set_list()
            case "Select Player Sprite >": 
                instance.set_list("Select Player Sprite >")
                instance.list_widget.setFixedHeight(MAP_HEIGHT*TILE_SIZE)
            case "Select Player Character >": instance.set_list("Select Player Character >")
            case "Change Current Character Name":
                new_name = QInputDialog.getText(instance, 'Input Dialog', 'New Character Name :')
                if new_name[0]:
                    if game_instance.set_player_name(game_instance.current_player, new_name[0]):
                        game_instance.current_player = new_name[0]
                        game_instance.save_current_game(slot = game_instance.current_slot)
                        instance.close()
    elif menu == "Load Game >":
        match item:
            case "Slot 1": 
                try:
                    game_instance.load_current_game(slot = 1)
                    instance.close()
                except:
                    pass
            case "Slot 2": 
                try:
                    game_instance.load_current_game(slot = 2)
                    instance.close()
                except:
                    pass 
            case "..":
                instance.set_list("main")
    elif menu == "Save Game >":
        match item:
            case "Slot 1":
                game_instance.save_current_game(slot = 1)
                instance.close()
            case "Slot 2":
                game_instance.save_current_game(slot = 2)
                instance.close()
            case "..":
                instance.set_list("main")
    elif menu == "Select Player Sprite >":
        if item == "..":
            instance.set_list()
        elif item != "[ Character Settings > Select Sprite ]":
            game_instance.player.sprite = item
            game_instance.draw()
            instance.close()
    elif menu == "Select Player Character >":
        if item == "..":
            instance.set_list()
        elif item != "[ Character Settings > Character Selection ]":
            game_instance.set_player(item) # will not load the actual position of the new character, that must be changed !!! 
            game_instance.draw()
            instance.close()
def build_menu(menu, item, instance, game_instance):
    if item == "Exit": instance.close()
    if item != "[ Certificates ]":
        match item:
            case "Guard Tower":
                game_instance.certificates.remove("Guard Tower") 
                game_instance.map.set_tile(game_instance.player.x, game_instance.player.y, GuardTower())
                game_instance.map.update_buildings_list()
                game_instance.map.place_character(game_instance.player)
                game_instance.draw() 
                instance.close()
                return 
            case "Lumber Mill":
                game_instance.certificates.remove("Lumber Mill") 
                game_instance.map.set_tile(game_instance.player.x, game_instance.player.y, LumberMill(wood=0))
                game_instance.map.update_buildings_list()
                game_instance.map.place_character(game_instance.player)
                game_instance.draw() 
                instance.close()
                return 
            case "Farm":
                game_instance.certificates.remove("Farm") 
                game_instance.map.set_tile(game_instance.player.x, game_instance.player.y, Mill(food=0))
                game_instance.map.update_buildings_list()
                game_instance.map.place_character(game_instance.player)
                game_instance.draw()    
                instance.close()     
                return 
def primary_menu(menu, item, instance, game_instance, list_of_weapons):
    if item == "Exit": instance.close()
    for wp in list_of_weapons:
        if item == wp[1]:
            game_instance.player.equip_item(wp[0], wp[0].slot)
            game_instance.update_inv_window()
            instance.close()
def skill_menu(menu, item, instance, game_instance, stamina_bound):
    if item == "Exit": instance.close()
    if "Release Party" in item:
        game_instance.release_party()
        instance.close()
        return 
    if "Dodge" in item: 
        if game_instance.player.days_survived >= 5:
            dx = 0
            dy = 0
            if game_instance.player.stamina<stamina_bound:
                game_instance.add_message("I'm exhausted ... I need to take a breathe")
            x = game_instance.player.x 
            y = game_instance.player.y
            fx, fy = game_instance.player.get_forward_direction()
            bx = -fx 
            by = -fy
            b_is_walkable = True 
            tile = game_instance.map.get_tile(x+bx,y+by)
            if tile and game_instance.player.stamina>stamina_bound:
                if tile.walkable:
                    tile2 = game_instance.map.get_tile(x+2*bx,y+2*by)
                    if tile2:
                        if tile2.walkable:
                            dx = 2*bx 
                            dy = 2*by
                            game_instance.player.stamina -= stamina_bound
                        else:
                            b_is_walkable = False
                    else:
                        b_is_walkable = False
                else:
                    b_is_walkable = False
            else:
                b_is_walkable = False
            if not b_is_walkable:
                game_instance.game_iteration()
            if dx or dy:
                target_x, target_y = game_instance.player.x + dx, game_instance.player.y + dy
                tile = game_instance.map.get_tile(target_x, target_y)
                if target_x <0 or target_x > game_instance.grid_width-1 or target_y<0 or target_y> game_instance.grid_height-1:
                    game_instance.horizontal_map_transition(target_x, target_y)  # Add this
                    instance.close()
                if tile and tile.walkable:
                    if tile.current_char:
                        if b_isForwarding:
                            damage = game_instance.player.calculate_damage_done()
                            game_instance.events.append(AttackEvent(game_instance.player, tile.current_char, damage))
                    else:
                        old_x, old_y = game_instance.player.x, game_instance.player.y
                        if game_instance.player.move(dx, dy, game_instance.map):
                            game_instance.events.append(MoveEvent(game_instance.player, old_x, old_y))
                            game_instance.dirty_tiles.add((old_x, old_y))
                            game_instance.dirty_tiles.add((game_instance.player.x, game_instance.player.y))
                game_instance.game_iteration()
            instance.close()
    if "Power Attack" in item: 
        if game_instance.player.days_survived >= 15:
            tx, ty = game_instance.player.get_forward_direction()
            tile0 = game_instance.map.get_tile(game_instance.player.x+tx, game_instance.player.y+ty)
            if tile0:
                if not tile0.walkable:
                    game_instance.add_message("Can't find a target ...")
                    instance.close()
                if tile0.current_char:
                    game_instance.add_message("The enemy is too close to perform this attack ...")
                    instance.close()
            tile1 = game_instance.map.get_tile(game_instance.player.x+2*tx, game_instance.player.y+2*ty)
            if tile1:
                if tile1.current_char:
                    if game_instance.player.primary_hand:
                        if game_instance.player.stamina<stamina_bound:
                            game_instance.add_message("I'm exhausted ... I need to take a breathe")
                        else:
                            game_instance.add_message("Powerful Strike ...")
                            game_instance.events.append(
                                AttackEvent(
                                    game_instance.player, tile1.current_char, d(game_instance.player.primary_hand.damage,3*game_instance.player.primary_hand.damage) 
                                ) 
                            )
                            game_instance.player.stamina -= stamina_bound
                            game_instance.game_iteration()
                            instance.close()
                else:
                    game_instance.add_message("Can't find a target ...")
            instance.close()
    if "Weapon Special Attack" in item: 
        primary = game_instance.player.primary_hand
        if primary:
            if hasattr(primary,"use_special"):
                if primary.use_special(game_instance.player, game_instance.map, game_instance):
                    game_instance.game_iteration()
                    instance.close() 
                else:
                    game_instance.add_message("Can't Use Special Skill Right Now ...")
            instance.close()            
def debugging_menu(menu,item, instance, game_instance):
    if item == "..": instance.set_list()
    # -- 
    if menu == "main":
        match item:
            case "Exit": 
                instance.close()
            case "Add Item >": 
                instance.set_list("Add Item >")
            case "Restore Status":
                game_instance.player.reset_stats()
                instance.close()
            case "Set Day 100":
                game_instance.player.days_survived = 100
                instance.close()
            case "Generate Enemies >":
                instance.set_list("Generate Enemies >")
            case "Generate Dungeon Entrance":
                if game_instance.map.add_dungeon_entrance_at(game_instance.player.x, game_instance.player.y):
                    game_instance.dirty_tiles.add((game_instance.player.x, game_instance.player.y)) 
                    game_instance.draw()
                instance.close()
            case "Add a Cosmetic Layer >":
                instance.set_list("Add a Cosmetic Layer >")
    # --
    if menu == "Add Item >":
        match item:
            case "Whetstone":
                game_instance.player.add_item(WeaponRepairTool("whetstone"))
                instance.close()
            case "Mace":
                game_instance.player.add_item(Mace())
                instance.close()    
            case "Long Sword":
                game_instance.player.add_item(Sword(name = "Long_Sword"))
                instance.close()    
            case "Food":
                game_instance.player.add_item(Food(name = "bread", nutrition = 150))
                instance.close()
    # -- 
    if menu == "Generate Enemies >":
        dx, dy = game_instance.player.get_forward_direction()
        dx = 2*dx 
        dy = 2*dy
        match item:                        
            case "Zombie":
                game_instance.map.generate_enemy_at(game_instance.player.x+dx, game_instance.player.y+dy, Zombie)
                game_instance.dirty_tiles.add((game_instance.player.x+dx, game_instance.player.y+dy)) 
                game_instance.draw()    
                instance.close()                            
            case "Bear":
                game_instance.map.generate_enemy_at(game_instance.player.x+dx, game_instance.player.y+dy, Bear)
                game_instance.dirty_tiles.add((game_instance.player.x+dx, game_instance.player.y+dy)) 
                game_instance.draw()
                instance.close()
            case "Rogue":
                game_instance.map.generate_enemy_at(game_instance.player.x+dx, game_instance.player.y+dy, Rogue)
                game_instance.dirty_tiles.add((game_instance.player.x+dx, game_instance.player.y+dy)) 
                game_instance.draw()    
                instance.close()                            
            case "Mercenary":
                game_instance.map.generate_enemy_at(game_instance.player.x+dx, game_instance.player.y+dy, Mercenary)
                game_instance.dirty_tiles.add((game_instance.player.x+dx, game_instance.player.y+dy)) 
                game_instance.draw()
                instance.close()
            case "Player":
                npc_name = "npc"+str(random.randint(0,9))+str(random.randint(0,9))+str(random.randint(0,9))+str(random.randint(0,9))+str(random.randint(0,9))
                game_instance.add_player(key = npc_name, name = npc_name, x = game_instance.player.x+dx, y = game_instance.player.y+dy)
                game_instance.dirty_tiles.add((game_instance.player.x+dx, game_instance.player.y+dy)) 
                game_instance.draw()
                instance.close()
    # --
    if menu == "Add a Cosmetic Layer >":
        tile = game_instance.player.current_tile
        match item:
            case "House":
                tile.add_layer("house")
                game_instance.draw()    
                instance.close()                            
            case "Castle":
                #tile.add_layer("castle")
                game_instance.map.set_tile(game_instance.player.x, game_instance.player.y, Castle())
                game_instance.draw()    
                instance.close()                            
            case "Lumber Mill":
                game_instance.map.set_tile(game_instance.player.x, game_instance.player.y, LumberMill())
                game_instance.draw()    
                instance.close()                            
            case "Mill":
                game_instance.map.set_tile(game_instance.player.x, game_instance.player.y, Mill())
                game_instance.draw()    
                instance.close()     
            case "Clear":
                tile.remove_layer()
                game_instance.draw()    
                instance.close()
            case "Tower":
                game_instance.map.set_tile(game_instance.player.x, game_instance.player.y, GuardTower())
                game_instance.draw()    
                instance.close()     
def player_menu(menu,item, instance, game_instance, npc):
    player_items = { info(it)[0] : it for it in game_instance.player.items }
    npc_items = { info(it)[0] : it for it in npc.items }
    instance.add_list("items+", list( player_items.keys() ) )
    instance.add_list("items-", list( npc_items.keys() ) )
    if item == "Exit": 
        instance.close()
        return 
    if item == "Add to Party":
        npc.party = True
        game_instance.map.remove_character(npc)
        game_instance.update_prior_next_selection()
        game_instance.draw()
        instance.close()
        return 
    if item == "items+": 
        if len( player_items ) > 0:
            instance.set_list("items+")
    if item == "items-": 
        if len( npc_items ) > 0:
            instance.set_list("items-")
    if menu == "items+":
        obj = player_items[item]
        npc.add_item( obj ) 
        game_instance.player.remove_item(obj)
        instance.close()
        return 
    if menu == "items-":
        obj = npc_items[item]
        npc.remove_item( obj ) 
        game_instance.player.add_item(obj)
        instance.close()
        return 
























        