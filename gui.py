# gui.py

# project
from reality import *
from globals_variables import *
from events import *
from pyqt_layer_framework import *

# built-in
import os
from datetime import datetime

# third-party
from PyQt5.QtWidgets import QWidget, QListWidget, QVBoxLayout, QPushButton, QHBoxLayout, QMenu, QDialog, QLabel, QTextEdit, QSizePolicy, QInputDialog, QTabBar
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QTextCursor, QColor

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
def new_label(text = "", foreground = "white", parent = None):
    if not parent is None:
        label = QLabel(parent)
    else:
        label = QLabel()
    color_css = color_to_css(foreground)    
    label.setStyleSheet(f"""
        background-color: rgba(0, 0, 0, 150);
        color: {color_css};
        padding: 5px;
        border-radius: 5px;
        font-size: 10px;
        font-weight: bold;
    """)
    label.setWordWrap(True)
    label.setFocusPolicy(Qt.NoFocus)
    label.setText(text)
    return label 
def new_list_widget(callback = None, get_filtered_event_from = None):
    list_widget = QListWidget()
    list_widget.setStyleSheet("""
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
    list_widget.setSelectionMode(QListWidget.SingleSelection)
    list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
    list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    if callback: list_widget.itemDoubleClicked.connect(callback)
    if get_filtered_event_from: list_widget.installEventFilter(get_filtered_event_from) # now the list_widget will use the keyPressEvent function 
    return list_widget
def new_tab_bar(label="tab 1", callback = None):
    tab_ = QTabBar()
    tab_.addTab(label)
    # Styling (matches your dark semi-transparent style)
    tab_.setStyleSheet("""
        QTabBar::tab {
            background-color: rgba(0, 0, 0, 150);
            color: white;
            padding: 5px 10px;
            border: 1px solid rgba(255, 255, 255, 30);
            border-radius: 3px;
            margin: 2px;
            font-size: 10px;
        }
        QTabBar::tab:selected {
            background-color: rgba(255, 255, 255, 30);
            color: cyan;
        }
        QTabBar::tab:hover {
            background-color: rgba(255, 255, 255, 20);
        }
    """)
    # tab_widget.setFocusPolicy(Qt.StrongFocus)
    if callback: tab_.currentChanged.connect(callback)
    return tab_

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
def set_properties_layout(layout):
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(5)

# Classes 
class JournalWindow(Dialog):
    def __init__(self, parent=None):
        Dialog.__init__(self, parent)
        set_properties_non_modal_popup(self, "Journal")
        self.setFixedSize(POPUP_WIDTH, POPUP_HEIGHT)  # Similar size to InventoryWindow 
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
        set_relative_horizontal_position(self, self.parent(), side = "right")
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
    def save_journal(self):
        """Save journal contents to the current slot's journal file."""
        if not self.parent(): return
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
    def collect_special_text(self):
        if not self.parent(): return ""
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
        return "\n".join(special_texts) if special_texts else "All is calm for now."
    def generate_quick_entry(self):
        if not self.parent(): return ""
        return f"Position ({self.parent().player.x},{(self.parent().grid_height) - (self.parent().player.y)}) {self.collect_special_text()} {self.whereAmI()}"
    def log_quick_diary_entry(self):
        """Create a formatted diary entry with day, map coordinates, and special event text."""
        if not self.parent(): return 
        self.append_text( self.generate_quick_entry()+"\n" )
        self.parent().add_message("Diary entry logged")
    def log_diary_entry(self):
        """Create a formatted diary entry with day, map coordinates, and special event text."""
        if not self.parent(): return
        day = self.parent().current_day
        map_coords = self.parent().current_map
        # Format entry
        self.append_text(f"Day {day}, Map ({map_coords[0]},{-map_coords[1]},{map_coords[2]})"+self.generate_quick_entry()+"\n")
        self.parent().add_message("Diary entry logged")    
    def showEvent(self, event):
        """Ensure the text is scrolled to the end when the journal is shown."""
        set_text_cursor_to(self.text_edit)
        super().showEvent(event)
        if self.parent():
            self.parent().setFocus()
    def append_text(self, text):
        """Append text to the journal with a timestamp and scroll to end."""
        current_text = self.text_edit.toPlainText()
        new_text = f"{text}\n" if current_text else f"{text}"
        self.text_edit.setPlainText(current_text.rstrip("\n") +2*"\n" + new_text)
        set_text_cursor_to(self.text_edit)
        self.save_journal()  # Autosave after appending
    def clear_text(self):
        self.text_edit.setPlainText("")
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape or key == Qt.Key_J: # set focus to parent 
            if self.parent():
                self.parent().setFocus()
        else:
            super().keyPressEvent(event)
class MessagePopup(Dialog):
    def __init__(self, parent=None):
        Dialog.__init__(self, parent)
        # window settings
        set_properties_non_modal_popup(self, "Messages")
        self.setAttribute(Qt.WA_ShowWithoutActivating) # Show without taking focus
        # Layout
        self.layout = VLayout()
        self.label = new_label(parent = self)
        self / ( self.layout/self.label )
        self.base_height = 31 # Height per message
        self.max_messages = 15 # Limit to prevent oversized pop-up
        self.hide()
    def set_message(self, messages):
        """Display a list of messages, newest at the top."""
        if not messages:
            self.hide()
            return
        # Limit to max_messages
        messages = messages[-self.max_messages:] # Take newest messages
        text = " | ".join(reversed(messages)) # Newest at top
        self.label.setText(text)
        # adjust size
        self.label.setFixedWidth(500)
        # self.setFixedSize(fixed_width + 20, self.label.height() + 20)
        self.label.adjustSize()
        self.adjustSize()
        set_relative_vertical_position(self, self.parent(), 'down', 10)
        # Show and ensure main window retains focus
        self.show()
        if self.parent(): self.parent().setFocus()
class SelectionBox(Widget):
    def __init__(self, item_list = [f"Option {i}" for i in range(5)], action = lambda x, instance: instance.close(), parent=None, **kwargs):
        Widget.__init__(self, parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.7)  # 70% opaque, like MessagePopup
        self.setWindowModality(Qt.ApplicationModal) 
        self.setFocusPolicy(Qt.StrongFocus) 
        # -- 
        self.action = action 
        self.kw = kwargs
        self.list_dictionary = { "main": item_list }
        self.current_key = "main"
        self.list_widget_objects = []
        # -- 
        self.layout = VLayout()
        set_properties_layout(self.layout)
        self.list_widget = new_list_widget(get_filtered_event_from=self)
        self / (self.layout/self.list_widget)
        # -- 
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
        # Get max width of all items
        max_width = max(self.list_widget.sizeHintForIndex(self.list_widget.model().index(i, 0)).width() for i in range(row_count)) if row_count > 0 else 100
        self.list_widget.resize(max_width+100, total_height)
    def eventFilter(self, obj, event):
        if obj == self.list_widget and event.type() == QEvent.KeyPress:
            key = event.key() 
            if key in (Qt.Key_Return, Qt.Key_Enter):
                current_item = self.list_widget.currentItem()
                if current_item:
                    self.do_enter_action(current_item)
                    return True
            if key == Qt.Key_Escape:
                self.close()
                return True
            if key == Qt.Key_Up:
                if self.list_widget.currentRow() == 0:
                    return True
                else:
                    return super().eventFilter(obj, event)
            if key == Qt.Key_Down:
                if self.list_widget.currentRow() == len(self.list_widget)-1:
                    return True
                else:
                    return super().eventFilter(obj, event)
            if key in (Qt.Key_Left, Qt.Key_Right):
                return True 
        return super().eventFilter(obj, event)
    def do_enter_action(self, item=None):
        if not item: item = self.list_widget.currentItem()
        self.action(self.current_key, item.text(),self, **self.kw)
class InventoryWindow(Dialog):
    def __init__(self, parent=None):
        Dialog.__init__(self, parent)        
        set_properties_non_modal_popup(self, "Inventory")
        self.setFixedSize(POPUP_WIDTH, POPUP_HEIGHT)
        self.build_parts()
        self.assemble_parts()
        # --
        self.list_widget_objects = []
        self.list_widget_last_size = 0
        self.current_filter = ""
        # -- 
        self.hide()  # Hidden by default
        self.parent().setFocus()
    def build_parts(self):
        self.layout = VLayout()
        self.list_widget = new_list_widget(callback=self.item_double_click, get_filtered_event_from=self)
        self.tabs = new_tab_bar("*", self.tab_changed)
        self.tabs.addTab("Edible")
        self.tabs.addTab("Weapons")
        self.tabs.addTab("Resources")
        self.equip_button = new_button("Equip/Use", self.item_double_click)
        self.drop_button = new_button("Drop", self.drop_item)
    def assemble_parts(self):
        set_properties_layout(self.layout)        
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.tabs.currentChanged.connect(self.tab_changed)
        self / (self.layout/self.tabs/self.list_widget/ (HLayout()/self.equip_button/self.drop_button) )
    def tab_changed(self, index):
        self.current_filter = self.tabs.tabText(index)
        self.apply_filter()
    def apply_filter(self):
        match self.current_filter:
            case "*": 
                apply_filter_to_list_widget(self.list_widget,"")
            case "Edible": 
                apply_filter_to_list_widget(self.list_widget,"[ntr]")
            case "Weapons": 
                apply_filter_to_list_widget(self.list_widget,"[dmg]")
            case "Resources": 
                apply_filter_to_list_widget(self.list_widget,"[value]")
    def eventFilter(self, obj, event):
        if obj == self.list_widget and event.type() == QEvent.KeyPress:
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
        return game_item.get_quality()
    def label_for(self,game_item):
        return info(game_item)
    def update_position(self):
        set_relative_horizontal_position(self, self.parent(), 'left', 10)
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
        # --
        self.apply_filter()
        self.update_row_index(last_list_widget_size, last_list_widget_current_item_index)
        # show         
        self.show()
        set_relative_horizontal_position(self, self.parent(), 'left', 10)
        self.parent().setFocus()
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
        if not item: item = self.list_widget.currentItem()
        if item:
            wdg_index = self.list_widget.row(item)
            game_item = self.list_widget_objects[wdg_index]
            ply_index = self.player.get_item_index(game_item)           
            if ply_index == wdg_index: # not equipped 
                if isinstance(game_item, Equippable):
                    if self.player.equip_item(game_item, game_item.slot):
                        self.parent().add_message(f"Equipped {game_item.name}, {game_item.description}")
                        self.parent().draw_hud()  # Update HUD if needed
                    else:
                        self.parent().add_message(f"Cannot equip {game_item.name}")
                    self.update_inventory(self.player)  # Refresh list
                elif isinstance(game_item, Usable):
                    if game_item in self.player.items:                    
                        self.parent().events.append(UseItemEvent(self.player, game_item))
                else:
                    self.parent().add_message(f"{game_item.name} is not equippable or usable")
            else: # equipped
                if isinstance(game_item, Equippable):
                    self.parent().add_message(f"Unequipped")
                    c_slot = game_item.get_equipped_slot(self.player)
                    self.player.unequip_item(c_slot)
            self.parent().game_iteration() 
        self.update_inventory(self.player) # Refresh list            
        self.parent().setFocus()  # Return focus to game
    def drop_item(self, item=None):
        """Drop the selected or provided item to the current tile."""
        if not item: item = self.list_widget.currentItem()
        if item:            
            index = self.list_widget.row(item)
            if index>=len(self.player.items): 
                self.parent().add_message(f"Can't drop equipped item")
                return 
            game_item = self.player.items[index]
            if game_item.is_equipped(self.player):
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
    def update_row_index(self, last_size, last_index):
        if last_size == len(self.list_widget_objects): # same size
            #print("1", last_size, last_index)
            self.list_widget.setCurrentRow(last_index)
        elif last_size > len(self.list_widget_objects): # size -1
            #print("2", last_size, last_index)
            if last_index < len(self.list_widget) and last_index > 0:
                self.list_widget.setCurrentRow(last_index - 1)
            else:
                self.list_widget.setCurrentRow( len(self.list_widget)//2 )
        else:
            #print("3", last_size, last_index)
            self.list_widget.setCurrentRow( len(self.list_widget)//2 )
    
# menu components
def common_menu_parts(menu, item, instance, game_instance, previous_menu = None):
    """ return True means that the menu should close """
    if item == "..": 
        if previous_menu:
            instance.set_list(previous_menu)
        else:
            instance.set_list()
        return False 
    if menu == "main" and item.lower() == "exit": return True    
    if item.lower() == "resume": return True 
    return False 

# Menus 
def main_menu(menu, item, instance, game_instance):
    if common_menu_parts(menu, item, instance, game_instance): 
        instance.close()
        return 
    
    if menu == "main":
        match item:
            case "Start New Game": 
                new_name = QInputDialog.getText(instance, 'Input Dialog', 'Character Name :')
                if new_name[0]:
                    game_instance.start_new_game(new_name[0])
                    instance.close()
                    return 
            case "Load Game >": instance.set_list("Load Game >", ["[ Main Menu > Load Game ]","Slot 1", ".."])
            case "Save Game >": instance.set_list("Save Game >", ["[ Main Menu > Save Game ]","Slot 1", ".."])
            case "Quit to Desktop": 
                game_instance.close()
                return 
            case "Character Settings >": 
                instance.set_list("Character Settings >", [
                    "[ Main Menu > Character Settings ]",
                    "Select Player Sprite >",
                    "Select Player Character >",
                    "Change Current Character Name",
                    ".."
                ])
    elif menu == "Character Settings >":
        match item:
            case "Select Player Sprite >": 
                instance.set_list("Select Player Sprite >", ["[ Character Settings > Select Sprite ]"] + SPRITE_NAMES_PLAYABLES + [".."])
            case "Select Player Character >": 
                instance.set_list("Select Player Character >", ["[ Character Settings > Character Selection ]"] + [ k for k,v in game_instance.players.items() if v.current_map == game_instance.player.current_map and not v.party ] + [".."])
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
    elif menu == "Save Game >":
        match item:
            case "Slot 1":
                game_instance.save_current_game(slot = 1)
                instance.close()
            case "Slot 2":
                game_instance.save_current_game(slot = 2)
                instance.close()
    elif menu == "Select Player Sprite >":
        if item != "[ Character Settings > Select Sprite ]":
            game_instance.player.sprite = item
            game_instance.draw()
            instance.close()
    elif menu == "Select Player Character >":
        if item != "[ Character Settings > Character Selection ]":
            game_instance.set_player(item) # will not load the actual position of the new character, that must be changed !!! 
            game_instance.draw()
            instance.close()
def build_menu(menu, item, instance, game_instance):
    if common_menu_parts(menu, item, instance, game_instance): 
        instance.close()
        return 
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
def primary_menu(menu, item, instance, game_instance, list_of_weapons, slot):
    if common_menu_parts(menu, item, instance, game_instance): 
        instance.close()
        return 
    for wp in list_of_weapons:
        if item == wp[1]:
            game_instance.player.equip_item(wp[0], slot)
            game_instance.update_inv_window()
            instance.close()
def skill_menu(menu, item, instance, game_instance, stamina_bound):
    if common_menu_parts(menu, item, instance, game_instance): 
        instance.close()
        return 
    player = game_instance.player 
    if "Release Party" in item:
        if isinstance(player, Hero):
            player.release_party(game_instance)
            game_instance.update_prior_next_selection()
            instance.close()
            return 
def player_menu(menu,item, instance, game_instance, npc):
    player = game_instance.player 
    if not player: 
        instance.close()
        return 
    player_items = { info(it)[0] : it for it in player.items }
    npc_items = { info(it)[0] : it for it in npc.items }
    if common_menu_parts(menu, item, instance, game_instance): 
        instance.close()
        return 
    if item == "Add to Party":
        if isinstance(npc, Player) and isinstance(player, Hero):
            player.add_to_party(npc.name, game_instance)
            instance.close()
            return 
    if item == "items+": 
        if len( player_items ) > 0:
            instance.set_list("items+", list( player_items.keys() )+[".."] )
    if item == "items-": 
        if len( npc_items ) > 0:
            instance.set_list("items-", list( npc_items.keys() )+[".."] )
    if menu == "items+":        
        player.give( player_items[item] , npc)
        instance.close()
        return 
    if menu == "items-":
        npc.give( npc_items[item] , player)
        instance.close()
        return 
def debugging_menu(menu, item, instance, game_instance):
    if common_menu_parts(menu, item, instance, game_instance): 
        instance.close()
        return 
    # -- 
    player = game_instance.player 
    if menu == "main":
        match item:
            case "Display Players Info >":
                instance.set_list("Display Players Info >", [".."]+[ f"{k} {v.current_map} {v.party}" for k,v in game_instance.players.items() ])
            case "Add Item >": 
                instance.set_list("Add Item >", ["Resources","Whetstone","Mace","Long Sword","Food",".."])
            case "Restore Status":
                player.reset_stats()
                instance.close()
                return 
            case "All Skills":
                player.activate_all_skills()
                instance.close()
                return 
            case "Set Day 100":
                game_instance.player.days_survived = 100
                instance.close()
                return 
            case "Generate Enemies >":
                instance.set_list("Generate Enemies >", ["Zombie","Bear","Rogue","Mercenary","Player",".."])
            case "Generate Dungeon Entrance":
                if game_instance.map.add_dungeon_entrance_at(player.x, player.y):
                    game_instance.dirty_tiles.add((player.x, player.y)) 
                    game_instance.draw()
                instance.close()
                return 
            case "Add a Cosmetic Layer >":
                instance.set_list("Add a Cosmetic Layer >", ["House","Castle","Lumber Mill","Clear","Mill","Tower",".."])
    # --
    if menu == "Add Item >":
        match item:
            case "Resources":
                player.add_item(Wood(3000))
                player.add_item(Stone(3000))
                player.add_item(Metal(3000))
                player.add_item(Food(3000))
                instance.close()
                return 
            case "Whetstone":
                player.add_item(WeaponRepairTool("whetstone"))
                instance.close()
                return 
            case "Mace":
                player.add_item(Mace())
                instance.close()    
                return 
            case "Long Sword":
                player.add_item(Sword(name = "Long_Sword"))
                instance.close()    
                return 
            case "Food":
                player.add_item(Food(name = "Bread", nutrition = 150))
                instance.close()
                return 
    # --    
    if menu == "Generate Enemies >":
        dx, dy = player.get_forward_direction()
        dx = 2*dx 
        dy = 2*dy
        match item:                        
            case "Zombie":
                game_instance.map.generate_enemy_at(player.x+dx, player.y+dy, Zombie)
                game_instance.dirty_tiles.add((player.x+dx, player.y+dy)) 
                game_instance.draw()    
                instance.close()                            
                return 
            case "Bear":
                game_instance.map.generate_enemy_at(player.x+dx, player.y+dy, Bear)
                game_instance.dirty_tiles.add((player.x+dx, player.y+dy)) 
                game_instance.draw()
                instance.close()
                return 
            case "Rogue":
                game_instance.map.generate_enemy_at(player.x+dx, player.y+dy, Rogue)
                game_instance.dirty_tiles.add((player.x+dx, player.y+dy)) 
                game_instance.draw()    
                instance.close()                            
                return 
            case "Mercenary":
                game_instance.map.generate_enemy_at(player.x+dx, player.y+dy, Mercenary)
                game_instance.dirty_tiles.add((player.x+dx, player.y+dy)) 
                game_instance.draw()
                instance.close()
            case "Player":
                npc_name = "npc"+rn(7)
                game_instance.add_player(key = npc_name, name = npc_name, x = player.x+dx, y = player.y+dy)
                game_instance.dirty_tiles.add((player.x+dx, player.y+dy)) 
                game_instance.draw()
                instance.close()
                return 
    # --
    if menu == "Add a Cosmetic Layer >":
        tile = player.current_tile
        match item:
            case "House":
                tile.add_layer("house")
                game_instance.draw()    
                instance.close()                            
            case "Castle":
                game_instance.map.set_tile(player.x, player.y, Castle())
                game_instance.draw()    
                instance.close()                            
            case "Lumber Mill":
                game_instance.map.set_tile(player.x, player.y, LumberMill())
                game_instance.draw()    
                instance.close()                            
            case "Mill":
                game_instance.map.set_tile(player.x, player.y, Mill())
                game_instance.draw()    
                instance.close()     
            case "Clear":
                tile.remove_layer()
                game_instance.draw()    
                instance.close()
            case "Tower":
                game_instance.map.set_tile(player.x, player.y, GuardTower())
                game_instance.draw()    
                instance.close()     

# -- END       