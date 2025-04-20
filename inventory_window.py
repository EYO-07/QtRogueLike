# inventory_window.py
# from PyQt5.QtWidgets import QWidget, QListWidget, QVBoxLayout
# from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QListWidget, QVBoxLayout, QPushButton, QHBoxLayout, QMenu
from PyQt5.QtCore import Qt
from items import Equippable

class InventoryWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        #self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setWindowOpacity(0.7)
        # self.layout = QVBoxLayout()
        # self.list_widget = QListWidget()
        # self.list_widget.setStyleSheet("background-color: rgba(0, 0, 0, 150); color: white;")
        # self.layout.addWidget(self.list_widget)
        # self.setLayout(self.layout)
        # self.setFixedSize(200, 300)
        # self.hide()
        
        # Set window properties to match MessagePopup
        #self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.7)  # 70% opaque, like MessagePopup
        self.setFocusPolicy(Qt.NoFocus)  # Prevent stealing focus

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
            }
        """)
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.itemDoubleClicked.connect(self.equip_item)  # Double-click to equip
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.layout.addWidget(self.list_widget)

        # Buttons
        button_layout = QHBoxLayout()
        self.equip_button = QPushButton("Equip")
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
        self.equip_button.clicked.connect(self.equip_item)
        button_layout.addWidget(self.equip_button)

        self.drop_button = QPushButton("Drop")
        self.drop_button.setStyleSheet(self.equip_button.styleSheet())
        self.drop_button.clicked.connect(self.drop_item)
        button_layout.addWidget(self.drop_button)

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

        # Initial size
        self.setFixedSize(250, 300)
        self.hide()  # Hidden by default

    def update_inventory(self, player):
        # self.list_widget.clear()
        # for item in items:
            # self.list_widget.addItem(f"{item.name} ({item.weight}kg)")
        # self.show()
        # if self.parent():
            # parent_geo = self.parent().geometry()
            # self.move(parent_geo.x() + parent_geo.width() + 10, parent_geo.y())
        """Update the list with the player's current items."""
        self.player = player  # Store player reference
        self.list_widget_objects.clear()
        self.list_widget.clear()
        for item in player.items:
            self.list_widget.addItem(f"{item.name} ({item.weight}kg)")
            self.list_widget_objects.append(item)
        # equipped 
        b_equipped = False
        if player.primary_hand:
            self.list_widget.addItem(f"* {player.primary_hand.name} ({player.primary_hand.weight}kg)")  
            self.list_widget_objects.append(player.primary_hand)
            b_equipped = True
        if player.secondary_hand:
            self.list_widget.addItem(f"* {player.secondary_hand.name} ({player.secondary_hand.weight}kg)")  
            self.list_widget_objects.append(player.secondary_hand)
            b_equipped = True
        if player.head:
            self.list_widget.addItem(f"* {player.head.name} ({player.head.weight}kg)")  
            self.list_widget_objects.append(player.head)
            b_equipped = True
        if player.neck:
            self.list_widget.addItem(f"* {player.neck.name} ({player.neck.weight}kg)")  
            self.list_widget_objects.append(player.neck)
            b_equipped = True
        if player.torso:
            self.list_widget.addItem(f"* {player.torso.name} ({player.torso.weight}kg)")  
            self.list_widget_objects.append(player.torso)
            b_equipped = True
        if player.waist:
            self.list_widget.addItem(f"* {player.waist.name} ({player.waist.weight}kg)")  
            self.list_widget_objects.append(player.waist)
            b_equipped = True
        if player.legs:
            self.list_widget.addItem(f"* {player.legs.name} ({player.legs.weight}kg)")  
            self.list_widget_objects.append(player.legs)
            b_equipped = True
        if player.foot:
            self.list_widget.addItem(f"* {player.foot.name} ({player.foot.weight}kg)")  
            self.list_widget_objects.append(player.foot)
            b_equipped = True
        
        if player.items or b_equipped:
            self.show()
            self.update_position()
        else:
            self.hide()
            
    def update_position(self):
        """Position the window to the left of the parent window."""
        pass
        # if self.parent():
            # parent_geo = self.parent().geometry()
            # target_x = parent_geo.x() - self.width() - 10  # 10px gap to the left
            # target_y = parent_geo.y() + (parent_geo.height() - self.height()) // 2  # Vertically centered
            # self.move(target_x, target_y)
            # print(f"InventoryWindow positioned at ({target_x}, {target_y})")
        # else:
            # self.move(50, 100)  # Fallback position
            
    # def update_position(self):
        # """Position the window at the center of the parent window."""
        # if self.parent():
            # parent_geo = self.parent().geometry()
            #Calculate center of parent window
            # parent_center_x = parent_geo.x() + parent_geo.width() / 2
            # parent_center_y = parent_geo.y() + parent_geo.height() / 2
            #Position inventory window so its center aligns with parent's center
            # target_x = parent_center_x - self.width() / 2
            # target_y = parent_center_y - self.height() / 2
            # self.move(int(target_x), int(target_y))  # Convert to integers for move()
            # print(f"InventoryWindow positioned at ({target_x}, {target_y}), parent center at ({parent_center_x}, {parent_center_y})")
        # else:
            #Fallback position (center of screen or arbitrary point)
            # self.move(100, 100)
            # print(f"InventoryWindow positioned at (100, 100), no parent")        

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

    def equip_item(self, item=None):
        """Equip the selected or provided item."""
        if not item:
            item = self.list_widget.currentItem()
        if item:
            index = self.list_widget.row(item)
            if index>=len(self.player.items): 
                self.parent().add_message(f"Unequipped")
                self.list_widget_objects[index].unequip(self.player)
                self.update_inventory(self.player)  # Refresh list
                self.parent().setFocus()  # Return focus to game
                return 
            game_item = self.player.items[index]
            if isinstance(game_item, Equippable):
                if self.player.equip_item(game_item, game_item.slot):
                    self.player.items.remove(game_item)
                    self.parent().add_message(f"Equipped {game_item.name}")
                    self.update_inventory(self.player)  # Refresh list
                    self.parent().draw_hud()  # Update HUD if needed
                else:
                    self.parent().add_message(f"Cannot equip {game_item.name}")
            else:
                self.parent().add_message(f"{game_item.name} is not equippable")
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
        self.parent().setFocus()  # Return focus to game    


























        