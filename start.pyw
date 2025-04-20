# this is the entry point: start.pyw 
# other files: 
# items.py 
# living.py
# mapping.py 
# events.py 
# message_window.py 
# inventory_window.py

import shutil
import tempfile
import os
import sys
import json
import random
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsRectItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QTransform
from mapping import *
from living import *
from items import *
from events import *
import random  # Add for random enemy placement
from message_window import MessagePopup  # Import the new MessagePopup
from inventory_window import InventoryWindow
import math 

# Set working directory to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"Working directory set to: {os.getcwd()}")

class Game(QGraphicsView):
    instance = None  # Temporary singleton for Enemy access
    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.StrongFocus)  # Ensure Game accepts focus
        self.rotation = 0  # degrees: 0, 90, 180, 270
        self.view_width = 7
        self.view_height = 7
        # gV := Member Variables
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.tile_size = 70
        self.grid_width = 100
        self.grid_height = 100
        self.maps = {(0, 0, 0): Map("default")}  # Store Map objects with coordinate keys
        self.current_map = (0, 0, 0)  # Current map coordinates
        self.map = self.maps[self.current_map]
        # Create and place characters
        self.player = Player("Hero", 100, 50, 50)  # Start near center
        self.player.hunger = 200
        self.player.max_hunger = 1000
        self.events = []  # Initialize events list
        self.enemies = {(0, 0, 0): []}  # Dictionary with map coords as keys, enemy lists as values
        self.map.place_character(self.player)
        self.fill_enemies(100) # place zombies 
        self.turn = 0  # Track turns
        
        # Initial render
        self.dirty_tiles = set()  # Track tiles that need redrawing
        self.tile_items = {}  # For optimized rendering
        self.draw_grid()
        self.draw_hud()
        self.dirty_tiles.clear()  # Clear after full draw
        self.setWindowTitle("PyQt Rogue Like")
        #self.setFixedSize(self.grid_width * self.tile_size, self.grid_height * self.tile_size)
        self.setFixedSize(self.view_width * self.tile_size, self.view_height * self.tile_size)
        Game.instance = self
        
        self.inventory_window = None  # Initialize later on demand
        # Initialize message window
        self.message_popup = MessagePopup(self)  # Set Game as parent
        self.messages = []  # List of (message, turns_remaining) tuples
        
        # Attempt to load saved game
        try:
            self.load_current_game()
            #self.add_message("Loaded saved game on startup") #print("Loaded saved game on startup")
        except FileNotFoundError:
            self.add_message("No save file found, starting new game") #print("No save file found, starting new game")
        except Exception as e:
            self.add_message(f"Error loading game on startup: {e}, starting new game") #print(f"Error loading game on startup: {e}, starting new game")
    
    def add_message(self, message, turns=5):
        """Add a message to the queue."""
        self.messages.append((message, turns))
        # Update pop-up with all active messages
        active_messages = [msg for msg, _ in self.messages]
        self.message_popup.set_message(active_messages)
        print(f"Added message: '{message}' for {turns} turns, queue: {self.messages}")
        
    def update_messages(self):
        """Update message queue and refresh pop-up."""
        print(f"Updating messages, current queue: {self.messages}")
        if not self.messages:
            self.message_popup.set_message([])
            return
        # Decrease turn counters and remove expired messages
        self.messages = [(msg, turns - 1) for msg, turns in self.messages if turns > 1]
        # Update pop-up with active messages
        active_messages = [msg for msg, _ in self.messages]
        self.message_popup.set_message(active_messages)
        print(f"Active messages: {active_messages}")  
    
    def closeEvent(self, event):
        """Save the game state when the window is closed."""
        try:
            self.add_message("Saving game before exit...")
            self.save_current_game(slot=1)
        except Exception as e:
            self.add_message(f"Error saving game on exit: {e}")
            print(f"Error saving game on exit: {e}")
        self.message_popup.close()
        if self.inventory_window:
            self.inventory_window.close()
        event.accept()  
    
    def check_map_transition(self, x, y):
        """Handle map transitions by saving the current map and loading the new one."""
        current_x, current_y, current_z = self.current_map
        new_map_coord = None
        new_x, new_y = x, y
        if x < 0:
            new_map_coord = (current_x - 1, current_y, current_z)
            new_x = self.grid_width - 1
        elif x > self.grid_width - 1:
            new_map_coord = (current_x + 1, current_y, current_z)
            new_x = 0
        elif y < 0:
            new_map_coord = (current_x, current_y - 1, current_z)
            new_y = self.grid_height - 1
        elif y > self.grid_height - 1:
            new_map_coord = (current_x, current_y + 1, current_z)
            new_y = 0

        if new_map_coord:
            self.add_message(f"Transitioning from {self.current_map} to {new_map_coord}, player to ({new_x}, {new_y})")
            
            # Save current map
            saves_dir = "./saves"
            map_file = os.path.join(saves_dir, f"map_{'_'.join(map(str, self.current_map))}_1.json")
            # Clear enemies to ensure only saved state is used
            current_enemies = self.enemies.get(self.current_map, [])
            self.enemies[self.current_map] = []
            self.map.save_state(current_enemies, map_file)
            
            # Remove player from current map
            if not self.map.remove_character(self.player):
                print(f"Warning: Failed to remove player from {self.current_map}")
            
            # Update player state
            self.player.x, self.player.y = new_x, new_y
            self.save_current_game(slot=1)  # Updates player_state.json with new map and position

            # Clear current scene
            self.scene.clear()           
            
            # Switch to new map
            self.current_map = new_map_coord
            self.enemies[new_map_coord] = []
            if new_map_coord not in self.maps:
                print(f"Creating new map at {new_map_coord}")
                map_type = random.choice(["procedural_lake", "procedural_field", "procedural_road"])
                self.maps[new_map_coord] = Map(map_type)
            self.map = self.maps[self.current_map]
            
            # Load new map state
            map_file = os.path.join(saves_dir, f"map_{'_'.join(map(str, self.current_map))}_1.json")
            try:
                with open(map_file, "r") as f:
                    #print("(1) HERE")
                    map_state = json.load(f)
                    fill_list = []
                    self.map.load_state(fill_list, map_state)
                    self.enemies[self.current_map] = fill_list
                    print(self.enemies[self.current_map])
            except FileNotFoundError:
                self.add_message(f"No map file found for {self.current_map}, generating new map")
                self.map.generate()
            except Exception as e:
                self.add_message(f"Failed to load map for {self.current_map}: {e}")
                print(f"Error loading map {map_file}: {e}")
                self.map.generate()
            
            # Place player
            if not self.map.place_character(self.player):
                print(f"Error: Failed to place player at ({new_x}, {new_y}) on map {self.current_map}")
                self.player.x, self.player.y = self.map.width // 2, self.map.height // 2
                self.map.place_character(self.player)
            
            # Place enemies
            for enemy in self.enemies.get(self.current_map, []):
                
                if not self.map.place_character(enemy):
                    print(f"Warning: Failed to place enemy {enemy.name} at ({enemy.x}, {enemy.y})")
                else:
                    print(f"placed enemy {enemy.name} at ({enemy.x}, {enemy.y})")
            
            # Populate enemies if needed
            if not self.enemies[self.current_map]:
                self.fill_enemies(100)
            elif len(self.enemies[self.current_map]) < 5:
                self.fill_enemies(50)

            # Redraw
            self.dirty_tiles.clear()
            self.draw_grid()
            self.draw_hud()

    def start_new_game(self):
        """Reset the game to a new state."""
        self.scene.clear()
        self.tile_items.clear()
        self.tile_items.clear()
        self.maps = {(0, 0, 0): Map("default")}
        self.current_map = (0, 0, 0)
        self.map = self.maps[self.current_map]
        self.player = Player("Hero", 100, 50, 50)
        self.player.hunger = 200
        self.player.max_hunger = 400
        self.events = []
        self.enemies = {(0, 0, 0): []}
        self.map.place_character(self.player)
        self.fill_enemies(20)
        self.turn = 0
        self.dirty_tiles = set()
        self.draw_grid()
        self.draw_hud()
        self.dirty_tiles.clear()    
        
    def save_current_game(self, slot=1):
        """Save the current map to its JSON file and player state to a central file."""
        try:
            # Ensure ./saves directory exists
            saves_dir = "./saves"
            if not os.path.exists(saves_dir):
                os.makedirs(saves_dir)

            # Save current map state
            map_file = os.path.join(saves_dir, f"map_{'_'.join(map(str, self.current_map))}_{slot}.json")
            self.map.save_state(self.enemies.get(self.current_map, []), map_file)

            # Save player state
            player_state = {
                "version": "1.0.0",
                "slot": slot,
                "turn": self.turn,
                "current_map": list(self.current_map),
                "player": {
                    "x": self.player.x,
                    "y": self.player.y,
                    "hp": self.player.hp,
                    "max_hp": self.player.max_hp,
                    "stamina": self.player.stamina,
                    "max_stamina": self.player.max_stamina,
                    "hunger": self.player.hunger,
                    "max_hunger": self.player.max_hunger,
                    "items": [
                        {
                            "type": "food" if isinstance(item, Food) else "weapon" if isinstance(item, Weapon) else "repair_tool" if isinstance(item, WeaponRepairTool) else "armor",
                            "name": item.name,
                            "nutrition": getattr(item, "nutrition", 0),
                            "weight": item.weight,
                            "description": item.description,
                            "sprite": item.sprite,
                            "damage": getattr(item, "damage", 0),
                            "max_damage": getattr(item, "max_damage", 0),
                            "stamina_consumption": getattr(item, "stamina_consumption", 0),
                            "repairing_factor": getattr(item, "repairing_factor", 0),
                            "armor": getattr(item, "armor", 0),
                            "slot": getattr(item, "slot", None)
                        } for item in self.player.items
                    ],
                    "equipped": {
                        "primary_hand": {
                            "type": "weapon",
                            "name": self.player.primary_hand.name,
                            "damage": self.player.primary_hand.damage,
                            "max_damage": self.player.primary_hand.max_damage,
                            "weight": self.player.primary_hand.weight,
                            "description": self.player.primary_hand.description,
                            "sprite": self.player.primary_hand.sprite,
                            "stamina_consumption": self.player.primary_hand.stamina_consumption
                        } if self.player.primary_hand else None,
                        "torso": {
                            "type": "armor",
                            "name": self.player.torso.name,
                            "armor": self.player.torso.armor,
                            "weight": self.player.torso.weight,
                            "description": self.player.torso.description,
                            "sprite": self.player.torso.sprite
                        } if self.player.torso else None
                        # Add other slots (secondary_hand, head, etc.) as needed
                    }
                }
            }

            # Backup player state
            player_file = os.path.join(saves_dir, f"player_state_{slot}.json")
            if os.path.exists(player_file):
                shutil.copy(player_file, os.path.join(saves_dir, f"player_state_{slot}.json.bak"))

            # Write player state to temporary file in ./saves
            temp_file_name = os.path.join(saves_dir, f"player_state_{slot}.tmp")
            with open(temp_file_name, 'w') as temp_file:
                json.dump(player_state, temp_file, indent=2)

            # Atomically rename temporary file
            os.replace(temp_file_name, player_file)
            self.add_message(f"Game saved to slot {slot}!")

        except Exception as e:
            self.add_message(f"Failed to save game: {e}")
            print(f"Error saving game: {e}")
            if os.path.exists(os.path.join(saves_dir, f"player_state_{slot}.json.bak")):
                shutil.copy(os.path.join(saves_dir, f"player_state_{slot}.json.bak"), player_file)  # Restore backup
            
    def load_current_game(self, slot=1):
        """Load player state and current map from their respective JSON files."""
        saves_dir = "./saves"
        player_file = os.path.join(saves_dir, f"player_state_{slot}.json")
        try:
            # Load player state
            with open(player_file, "r") as f:
                state = json.load(f)

            # Check version
            save_version = state.get("version", "0.0.0")
            if save_version != "1.0.0":
                self.add_message(f"Warning: Save version {save_version} may not be compatible")

            # Clear current state
            self.scene.clear()
            self.tile_items.clear()
            self.events.clear()
            self.enemies.clear()
            self.maps.clear()

            # Load player
            player_data = state["player"]
            self.player.x = player_data["x"]
            self.player.y = player_data["y"]
            self.player.hp = player_data["hp"]
            self.player.max_hp = player_data["max_hp"]
            self.player.stamina = player_data["stamina"]
            self.player.max_stamina = player_data["max_stamina"]
            self.player.hunger = player_data["hunger"]
            self.player.max_hunger = player_data["max_hunger"]
            self.player.items = []
            for item_data in player_data["items"]:
                if item_data["type"] == "food":
                    item = Food(
                        name=item_data["name"],
                        nutrition=item_data["nutrition"],
                        description=item_data.get("description", ""),
                        weight=item_data.get("weight", 1)
                    )
                elif item_data["type"] == "weapon":
                    item = Weapon(
                        name=item_data["name"],
                        damage=item_data["damage"],
                        description=item_data.get("description", ""),
                        weight=item_data.get("weight", 1),
                        stamina_consumption=item_data["stamina_consumption"]
                    )
                    item.max_damage = item_data["max_damage"]
                elif item_data["type"] == "repair_tool":
                    item = WeaponRepairTool(
                        name=item_data["name"],
                        repairing_factor=item_data["repairing_factor"],
                        description=item_data.get("description", ""),
                        weight=item_data.get("weight", 1)
                    )
                elif item_data["type"] == "armor":
                    item = Armor(
                        name=item_data["name"],
                        armor=item_data["armor"],
                        description=item_data.get("description", ""),
                        weight=item_data.get("weight", 1),
                        slot=item_data["slot"]
                    )
                self.player.add_item(item)
            equipped = player_data["equipped"]
            if equipped["primary_hand"]:
                weapon = Weapon(
                    name=equipped["primary_hand"]["name"],
                    damage=equipped["primary_hand"]["damage"],
                    description=equipped["primary_hand"].get("description", ""),
                    weight=equipped["primary_hand"].get("weight", 1),
                    stamina_consumption=equipped["primary_hand"]["stamina_consumption"]
                )
                weapon.max_damage = equipped["primary_hand"]["max_damage"]
                self.player.equip_item(weapon, "primary_hand") 
                #self.player.items.remove(weapon) 
            if equipped["torso"]:
                self.player.equip_item(Armor(
                    name=equipped["torso"]["name"],
                    armor=equipped["torso"]["armor"],
                    description=equipped["torso"].get("description", ""),
                    weight=equipped["torso"].get("weight", 1),
                    slot="torso"
                ), "torso")

            # Load current map
            self.current_map = tuple(state["current_map"])
            map_file = os.path.join(saves_dir, f"map_{'_'.join(map(str, self.current_map))}_{slot}.json")
            self.maps[self.current_map] = Map(state.get("filename", "default"))
            self.map = self.maps[self.current_map]
            self.enemies[self.current_map] = []
            try:
                with open(map_file, "r") as f:
                    map_state = json.load(f)
                    self.map.load_state(self.enemies[self.current_map], map_state)
                    print("Load from Load Current State:", len(self.enemies[self.current_map]) )
            except FileNotFoundError:
                self.add_message(f"No map file found for {self.current_map}, generating new map")
                self.map.generate()
            except Exception as e:
                self.add_message(f"Failed to load map for {self.current_map}: {e}")
                print(f"Error loading map {map_file}: {e}")
                self.map.generate()

            # Place characters
            if not self.map.place_character(self.player):
                self.add_message(f"Warning: Could not place player at ({self.player.x}, {self.player.y})")
                self.player.x, self.player.y = self.grid_width // 2, self.grid_height // 2
                self.map.place_character(self.player)
            for enemy in self.enemies[self.current_map]:
                if not self.map.place_character(enemy):
                    print(f"Warning: Could not place enemy at ({enemy.x}, {enemy.y})")

            # Load turn
            self.turn = state.get("turn", 0)

            # Redraw
            self.draw_grid()
            self.draw_hud()
            self.add_message(f"Game loaded from slot {slot}!")

        except FileNotFoundError:
            self.add_message(f"No save file found for slot {slot}")
            print(f"No save file found: {player_file}")
            self.start_new_game()
        except Exception as e:
            self.add_message(f"Failed to load game from slot {slot}: {e}")
            print(f"Error loading game: {e}")
            self.start_new_game()

    def draw_hud(self):
        hud_width = self.view_width * self.tile_size
        hud_height = 50
        hud_y = self.view_height * self.tile_size - hud_height
        bar_width = (hud_width - 20) // 3
        bar_height = 10
        padding = 5

        # HP Bar (Red)
        hp_ratio = self.player.hp / self.player.max_hp
        hp_bar = QGraphicsRectItem(10, hud_y + padding, bar_width * hp_ratio, bar_height)
        hp_bar.setBrush(QColor("red"))
        if hp_ratio<0.8: self.scene.addItem(hp_bar)

        # Stamina Bar (Blue)
        stamina_ratio = self.player.stamina / self.player.max_stamina
        stamina_bar = QGraphicsRectItem(10 + bar_width + padding, hud_y + padding, bar_width * stamina_ratio, bar_height)
        stamina_bar.setBrush(QColor("blue"))
        if stamina_ratio<0.8: self.scene.addItem(stamina_bar)

        # Hunger Bar (Yellow)
        hunger_ratio = self.player.hunger / self.player.max_hunger
        hunger_bar = QGraphicsRectItem(10 + 2 * (bar_width + padding), hud_y + padding, bar_width * hunger_ratio, bar_height)
        hunger_bar.setBrush(QColor("yellow"))
        if hunger_ratio<0.8: self.scene.addItem(hunger_bar)

        #North Arrow
        # arrow_size = 40  # Size of the arrow in pixels
        # arrow_x = (hud_width - arrow_size) / 2  # Desired center x-coordinate
        # arrow_y = 30  # Desired center y-coordinate
        # arrow_sprite = Tile.SPRITES.get("HUD_arrow", QPixmap())  # Get arrow sprite
        # if not arrow_sprite.isNull():
            # arrow_scaled = arrow_sprite.scaled(arrow_size, arrow_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            # arrow_item = QGraphicsPixmapItem(arrow_scaled)
            #Rotate to point north (opposite of player rotation)
            # rotation_angle = -self.rotation  # Negative to counter player's rotation
            # transform = QTransform().rotate(rotation_angle)
            # arrow_item.setTransform(transform)
            #Calculate the center of the pixmap
            # center_x = arrow_scaled.width() / 2
            # center_y = arrow_scaled.height() / 2
            #Convert rotation angle to radians for math.cos and math.sin
            # theta = math.radians(rotation_angle)
            #Calculate the offset of the center after rotation
            # offset_x = center_x * math.cos(theta) - center_y * math.sin(theta)
            # offset_y = center_x * math.sin(theta) + center_y * math.cos(theta)
            #Adjust position so the center of the pixmap is at (arrow_x, arrow_y)
            # adjusted_x = arrow_x - offset_x
            # adjusted_y = arrow_y - offset_y
            # arrow_item.setPos(adjusted_x, adjusted_y)
            # self.scene.addItem(arrow_item)
        # else:
            # print("Warning: Arrow sprite not found")
        # North Arrow
        arrow_size = 50  # Target size for scaling
        arrow_x = hud_width / 2  # Desired center x-coordinate (middle of HUD)
        arrow_y = 30  # Desired center y-coordinate
        arrow_sprite = Tile.SPRITES.get("HUD_arrow", QPixmap())  # Get arrow sprite
        if not arrow_sprite.isNull():
            arrow_scaled = arrow_sprite.scaled(arrow_size, arrow_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            arrow_item = QGraphicsPixmapItem(arrow_scaled)
            # Rotate to point north (opposite of player rotation)
            rotation_angle = -self.rotation
            transform = QTransform().rotate(rotation_angle)
            arrow_item.setTransform(transform)
            # Calculate the center of the pixmap
            center_x = arrow_scaled.width() / 2
            center_y = arrow_scaled.height() / 2
            # Convert rotation angle to radians
            theta = math.radians(rotation_angle)
            # Calculate the offset of the center after rotation
            offset_x = center_x * math.cos(theta) - center_y * math.sin(theta)
            offset_y = center_x * math.sin(theta) + center_y * math.cos(theta)
            # Adjust position so the center of the pixmap is at (arrow_x, arrow_y)
            adjusted_x = arrow_x - center_x - (center_x * (math.cos(theta) - 1) - center_y * math.sin(theta))
            adjusted_y = arrow_y - center_y - (center_x * math.sin(theta) + center_y * (math.cos(theta) - 1))
            arrow_item.setPos(adjusted_x, adjusted_y)
            self.scene.addItem(arrow_item)
            # Debug output
            # print(f"Arrow scaled size: {arrow_scaled.width()}x{arrow_scaled.height()}")
            # print(f"Arrow center: ({center_x}, {center_y})")
            # print(f"Rotation angle: {rotation_angle} degrees")
            # print(f"Offset: ({offset_x}, {offset_y})")
            # print(f"Adjusted position: ({adjusted_x}, {adjusted_y})")
            # print(f"Desired center: ({arrow_x}, {arrow_y})")
        else:
            print("Warning: Arrow sprite not found")    
        
    def fill_enemies(self, num_enemies):
        #print(f"Filling enemies for map {self.current_map}")
        if self.current_map not in self.enemies:
            self.enemies[self.current_map] = []
        placed = 0
        attempts = 0
        max_attempts = num_enemies * 10
        while placed < num_enemies and attempts < max_attempts:
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            if (x, y) == (self.player.x, self.player.y):
                attempts += 1
                continue
            tile = self.map.get_tile(x, y)
            if tile and tile.walkable and not tile.current_char:
                enemy = None
                coin = random.uniform(0,1)
                if self.map.filename == 'default':
                    if coin < 0.8:
                        enemy = Zombie("Zombie", 20, x, y)
                    else:
                        enemy = Rogue("Rogue",30,x,y)
                elif self.map.filename == 'procedural_field':
                    if coin < 0.8:
                        enemy = Zombie("Zombie", 20, x, y)
                    else:
                        enemy = Rogue("Rogue",20,x,y)
                elif self.map.filename == 'procedural_lake':
                    if coin < 0.7:
                        enemy = Zombie("Zombie", 20, x, y)
                    else:
                        enemy = Rogue("Rogue",30,x,y)
                elif self.map.filename == 'procedural_road':
                    if coin < 0.6:
                        enemy = Zombie("Zombie",20, x, y)
                    else:
                        enemy = Rogue("Rogue",30,x,y)
                else:
                    enemy = Zombie("Zombie", 20, x, y)
                if self.map.place_character(enemy):
                    self.enemies[self.current_map].append(enemy)  # Add to current map's list
                    
                    placed += 1
                    #print(f"Placed enemy at ({x}, {y})")
                else:
                    print(f"Failed to place enemy at ({x}, {y})")
            attempts += 1
        if placed < num_enemies:
            print(f"Warning: Only placed {placed} of {num_enemies} enemies due to limited valid tiles")
        print(f"Added {len(self.enemies[self.current_map])} enemies for map {self.current_map}")
            
    # gM := Member Methods
    def draw_grid(self):        
        if not self.dirty_tiles:  # Full redraw
            self.scene.clear()
            tiles_to_draw = [(x, y) for y in range(self.grid_height) for x in range(self.grid_width)]
            #print("Full redraw: all tiles")
        else:
            self.scene.clear()  # Clear scene to remove stale sprites
            tiles_to_draw = set(self.dirty_tiles)  # Start with dirty tiles (includes MoveEvent old positions)
            # Add all tiles in the 7x7 viewport
            px, py = self.player.x, self.player.y
            view_range_x = range(-self.view_width // 2, self.view_width // 2 + 1)  # -3 to 3
            view_range_y = range(-self.view_height // 2 - 1, self.view_height // 2)  # -4 to 2, adjusted for anchor
            for dy in view_range_y:
                for dx in view_range_x:
                    # Reverse rotation to get world coordinates
                    if self.rotation == 0:
                        wx, wy = dx, dy
                    elif self.rotation == 90:
                        wx, wy = -dy, dx
                    elif self.rotation == 180:
                        wx, wy = -dx, -dy
                    elif self.rotation == 270:
                        wx, wy = dy, -dx
                    x, y = px + wx, py + wy
                    if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                        tiles_to_draw.add((x, y))
            tiles_to_draw = list(tiles_to_draw)
            #print(f"Partial redraw: tiles_to_draw={tiles_to_draw}")

        px, py = self.player.x, self.player.y
        anchor_screen_x = (self.view_width // 2) * self.tile_size  # Center x
        anchor_screen_y = (self.view_height - 2) * self.tile_size  # Player at y=5

        player_rendered = False
        for x, y in tiles_to_draw:
            dx, dy = x - px, y - py
            rx, ry = self.rotate_vector_for_camera(dx, dy)
            screen_x = anchor_screen_x + rx * self.tile_size
            screen_y = anchor_screen_y + ry * self.tile_size
            # Relax bounds to include edge tiles
            if (0 <= x < self.grid_width and 0 <= y < self.grid_height and 0 <= screen_x < self.view_width * self.tile_size and 0 <= screen_y < self.view_height * self.tile_size):
                tile = self.map.get_tile(x, y)
                if tile:
                    if tile.current_char == self.player:
                        if player_rendered:
                            print(f"Warning: Multiple player renderings detected at ({x}, {y})")
                        player_rendered = True
                    tile.draw(self.scene, screen_x, screen_y, self.tile_size)
        self.scene.setSceneRect(0, 0, self.view_width * self.tile_size, self.view_height * self.tile_size)
        self.dirty_tiles.clear()

    def game_iteration(self):
        self.player.regenerate_stamina()
        self.player.regenerate_health()
        self.player.hunger = max(0, self.player.hunger - 1)  # Hunger decreases each turn
        if self.player.hunger <= 0:
            self.player.hp = max(0, self.player.hp - 5)  # Starvation damage
            if self.player.hp <= 0:
                self.add_message("Game Over: Starvation! Reloading last save...") #print("Game Over: Starvation!")
                try:
                    self.load_current_game()
                    self.add_message("Last save reloaded")
                except FileNotFoundError:
                    self.add_message("No save file found, starting new game")
                    self.start_new_game()
                except Exception as e:
                    self.add_message(f"Error reloading game: {e}, starting new game")
                    self.start_new_game()
                return
        self.turn += 1
        self.process_events()
        self.update_enemies()
        if self.current_map in self.enemies and len(self.enemies[self.current_map]) < 5:
            self.fill_enemies(50)
        self.update_messages()  # Critical: Update message window    
        self.draw_grid()
        self.draw_hud()

    def process_events(self):
        """Process events and trigger autosave for significant changes."""
        for event in sorted(self.events, key=lambda e: getattr(e, 'priority', 0)):
            if isinstance(event, AttackEvent):
                self.resolve_attack(event)
                if event.target.hp <= 0 and event.target != self.player:
                    pass #self.save_current_game(slot=1)  # Autosave on enemy death
            elif isinstance(event, MoveEvent):
                self.dirty_tiles.add((event.old_x, event.old_y))
            elif isinstance(event, PickupEvent):
                for item in event.tile.items[:]:
                    if event.character.pickup_item(item):
                        event.tile.remove_item(item)
                        self.add_message(f"{event.character.name} picked up {item.name}")
                        self.dirty_tiles.add((event.character.x, event.character.y))
                        #self.save_current_game(slot=1)  # Autosave on pickup
            elif isinstance(event, UseItemEvent):
                if event.item.use(event.character):
                    event.character.remove_item(event.item)
                    self.draw_hud()
                    #self.save_current_game(slot=1)  # Autosave on item use
        self.events.clear()
    
    def resolve_attack(self, event):
        event.target.hp -= event.damage
        if not event.target is self.player:
            if self.player.primary_hand:
                self.player.stamina = max(0, self.player.stamina - self.player.primary_hand.stamina_consumption)
        if event.target.hp <= 0:
            if event.target is self.player:
                # print("Game Over!")
                self.add_message("Game Over: Killed by enemy! Reloading last save...")
                try:
                    self.load_current_game()
                    self.add_message("Last save reloaded")
                except FileNotFoundError:
                    self.add_message("No save file found, starting new game")
                    self.start_new_game()
                except Exception as e:
                    self.add_message(f"Error reloading game: {e}, starting new game")
                    self.start_new_game()
            else:
                event.target.drop_on_death()
                if self.current_map in self.enemies and event.target in self.enemies[self.current_map]:
                    self.enemies[self.current_map].remove(event.target)
                event.target.current_tile.current_char = None
            self.add_message(f"{event.attacker.name} deals {event.damage} damage to {event.target.name}") #print(f"{event.attacker.name} deals {event.damage} damage to {event.target.name}")
        
    # Rotation for drawing (camera)
    def rotate_vector_for_camera(self, dx, dy):
        if self.rotation == 0:
            return dx, dy
        elif self.rotation == 90:
            return dy, -dx
        elif self.rotation == 180:
            return -dx, -dy
        elif self.rotation == 270:
            return -dy, dx    

    # Rotation for movement (world coordinates)
    def rotate_vector_for_movement(self, dx, dy):
        if self.rotation == 0:
            return dx, dy
        elif self.rotation == 90:
            return -dy, dx
        elif self.rotation == 180:
            return -dx, -dy
        elif self.rotation == 270:
            return dy, -dx            

    def rotated_direction(self, dx, dy):
        return self.rotate_vector_for_movement(dx, dy)
    
    def update_enemies(self):
        print(self.current_map)
        if self.current_map in self.enemies:  # Check if map has enemies
            #print(f"Updating {len(self.enemies[self.current_map])} enemies for map {self.current_map}")
            for enemy in self.enemies[self.current_map]:
                distance = abs(enemy.x - self.player.x) + abs(enemy.y - self.player.y)
                if distance < 25:
                    old_x, old_y = enemy.x, enemy.y
                    enemy.update(self.player, self.map, self)
                    if (enemy.x, enemy.y) != (old_x, old_y):
                        self.events.append(MoveEvent(enemy, old_x, old_y))
                        self.dirty_tiles.add((old_x, old_y))
                        self.dirty_tiles.add((enemy.x, enemy.y))
        else:
            print(f"No enemies found for map {self.current_map}")
                    
    # gE := Event Handlers
    def resizeEvent(self, event):
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        
    def keyPressEvent(self, event):
        key = event.key()
        dx, dy = 0, 0
        b_isForwarding = False
        if key in (Qt.Key_Up, Qt.Key_W):
            dx, dy = self.rotated_direction(0, -1)
            b_isForwarding = True
        elif key in (Qt.Key_Down, Qt.Key_S):
            dx, dy = self.rotated_direction(0, 1)
        elif key == Qt.Key_A:
            dx, dy = self.rotated_direction(-1, 0)
        elif key == Qt.Key_D:
            dx, dy = self.rotated_direction(1, 0)
        elif key == Qt.Key_Left:
            self.rotation = (self.rotation - 90) % 360
            direction = {0: "North", 90: "East", 180: "South", 270: "West"}[self.rotation]
            self.add_message(f"Facing {direction}")
            self.game_iteration()
            return        
        elif key == Qt.Key_Right:
            self.rotation = (self.rotation + 90) % 360
            direction = {0: "North", 90: "East", 180: "South", 270: "West"}[self.rotation]
            self.add_message(f"Facing {direction}")
            self.game_iteration()
            return
        elif key == Qt.Key_E:  # Use first food item
            print(self.player.items)
            from items import Food  # Import here to avoid circular import
            for item in self.player.items:
                if isinstance(item, Food):
                    self.events.append(UseItemEvent(self.player, item))
                    self.game_iteration()
                    break
            return    
        elif key == Qt.Key_G:  # Pickup items
            tile = self.map.get_tile(self.player.x, self.player.y)
            if tile and tile.items:
                self.events.append(PickupEvent(self.player, tile))
                self.dirty_tiles.add((self.player.x, self.player.y))  # Redraw tile
                self.game_iteration()
            return
        elif key == Qt.Key_F5:
            self.save_current_game(slot=1)
            return
        elif key == Qt.Key_F6:
            self.save_current_game(slot=2)
            return
        elif key == Qt.Key_F7:
            self.load_current_game(slot=1)
            return
        elif key == Qt.Key_F8:
            self.load_current_game(slot=2)
            return
        elif key == Qt.Key_F9:    
            self.start_new_game()
            return 
        elif key == Qt.Key_I:  # Toggle inventory window
            print(self.player.items)
            print(self.player.primary_hand)
            if not self.inventory_window:
                self.inventory_window = InventoryWindow(self)
            if self.inventory_window.isVisible():
                self.inventory_window.update_inventory(self.player)
                self.inventory_window.hide()
            else:
                self.inventory_window.update_inventory(self.player)
            return
        elif key == Qt.Key_Escape:  # Close inventory window
            if self.inventory_window and self.inventory_window.isVisible():
                self.inventory_window.hide()
                return
        else:
            self.game_iteration()
            return 

        if dx or dy:
            target_x, target_y = self.player.x + dx, self.player.y + dy
            tile = self.map.get_tile(target_x, target_y)
            if target_x <0 or target_x > self.grid_width-1 or target_y<0 or target_y> self.grid_height-1:
                self.check_map_transition(target_x, target_y)  # Add this
                return
            if tile and tile.walkable:
                if tile.current_char:
                    if b_isForwarding:
                        damage = self.player.calculate_damage_done()
                        self.events.append(AttackEvent(self.player, tile.current_char, damage))
                else:
                    old_x, old_y = self.player.x, self.player.y
                    if self.player.move(dx, dy, self.map):
                        self.events.append(MoveEvent(self.player, old_x, old_y))
                        #if tile.items:
                        #    for item in tile.items[:]:
                        #        if self.player.pickup_item(item):
                        #            tile.remove_item(item)
                        self.dirty_tiles.add((old_x, old_y))
                        self.dirty_tiles.add((self.player.x, self.player.y))
            
                
            self.game_iteration()
      
if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = Game()
    game.show()
    sys.exit(app.exec_())

# --- END 






























