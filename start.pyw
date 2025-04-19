# this is the entry point: start.pyw 
# other files: 
# items.py 
# living.py
# mapping.py 
# events.py 
# message_window.py 
# inventory_window.py

import os
import sys
import json
import random
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsRectItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor
from mapping import Map
from living import *
from events import *
import random  # Add for random enemy placement
from message_window import MessagePopup  # Import the new MessagePopup

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
        self.player.max_hunger = 400
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
        
        # Initialize message window
        self.message_popup = MessagePopup(self)  # Set Game as parent
        self.messages = []  # List of (message, turns_remaining) tuples
        
        # Attempt to load saved game
        try:
            self.load_current_game()
            self.add_message("Loaded saved game on startup") #print("Loaded saved game on startup")
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
            self.add_message("Game Being Saved ...")
            self.save_current_game()
            
        except Exception as e:
            print(f"Error saving game on exit: {e}")
        self.message_popup.close()  # Ensure message window closes
        event.accept()    
    
    def check_map_transition(self, x, y):
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
            # Save current map state
            self.map.save_state(self.player)
            
            # Clear current scene
            self.scene.clear()
            
            # Remove player and enemies from current map
            if not self.map.remove_character(self.player):
                print(f"Warning: Failed to remove player from {self.current_map}")
            for enemy in self.enemies.get(self.current_map, [])[:]:  # Use copy to avoid modifying while iterating
                if not self.map.remove_character(enemy):
                    print(f"Warning: Failed to remove enemy at ({enemy.x}, {enemy.y})")
            
            # Switch to new map
            if new_map_coord not in self.maps:
                print(f"Creating new map at {new_map_coord}")
                map_type = random.choice(["procedural_lake", "procedural_field", "procedural_road"])
                self.maps[new_map_coord] = Map(map_type)
                self.enemies[new_map_coord] = []  # Initialize empty enemy list
            else:
                print(f"Loading existing map at {new_map_coord}")
                self.maps[new_map_coord].load_state(self.player)  # Load saved state
            
            # Update map and player position
            self.current_map = new_map_coord
            #self.fill_enemies(100)  # Populate new map with enemies
            self.map = self.maps[self.current_map]
            self.player.x, self.player.y = new_x, new_y
            if not self.map.place_character(self.player):
                print(f"Error: Failed to place player at ({new_x}, {new_y}) on map {self.current_map}")
            if not self.enemies[self.current_map]:
                self.fill_enemies(100)  # Adjust max_enemies as needed
            elif len(self.enemies[self.current_map])<5: 
                self.fill_enemies(50)
            # Redraw everything
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
        
    def save_current_game(self):
        # state = {
            # "player": {
                # "x": self.player.x,
                # "y": self.player.y,
                # "hp": self.player.hp,
                # "stamina": self.player.stamina,
                # "hunger": self.player.hunger,
                # "items": [item.__dict__ for item in self.player.items]
            # },
            # "enemies": {
                # str(coord): [{"x": e.x, "y": e.y, "hp": e.hp, "type": e.type} for e in enemy_list]
                # for coord, enemy_list in self.enemies.items()
            # },
            # "current_map": self.current_map,
            # "maps": {str(coord): map.filename for coord, map in self.maps.items()}
        # }
        # with open("savegame.json", "w") as f:
            # json.dump(state, f, indent=2)
        # self.map.save_state(self.player)
        # Save all maps' states
        for coord, map_obj in self.maps.items():
            map_obj.save_state(self.player)

        state = {
            "player": {
                "x": self.player.x,
                "y": self.player.y,
                "hp": self.player.hp,
                "stamina": self.player.stamina,
                "hunger": self.player.hunger,
                "items": [
                    {
                        "name": item.name,
                        "nutrition": getattr(item, "nutrition", 0),
                        "weight": item.weight,
                        "description": item.description,
                        "sprite": item.sprite
                    } for item in self.player.items
                ],
                "equipped": {
                    "primary_hand": {
                        "name": self.player.primary_hand.name,
                        "damage": self.player.primary_hand.damage,
                        "weight": self.player.primary_hand.weight,
                        "description": self.player.primary_hand.description,
                        "sprite": self.player.primary_hand.sprite
                    } if self.player.primary_hand else None,
                    # Add other slots (e.g., torso) if Armor is implemented
                }
            },
            "current_map": list(self.current_map),  # Convert tuple to list for JSON
            "maps": {
                str(list(coord)): {  # Convert tuple to stringified list
                    "filename": map_obj.filename,
                    "saved_grid": map_obj.saved_grid
                } for coord, map_obj in self.maps.items()
            },
            "enemies": {
                str(list(self.current_map)): [  # Only save enemies for current map
                    {
                        "x": e.x,
                        "y": e.y,
                        "hp": e.hp,
                        "type": e.type,
                        "patrol_direction": list(e.patrol_direction),
                        "stance": e.stance,
                        "items": [
                            {
                                "name": item.name,
                                "nutrition": getattr(item, "nutrition", 0),
                                "weight": item.weight,
                                "description": item.description,
                                "sprite": item.sprite
                            } for item in e.items
                        ]
                    } for e in self.enemies.get(self.current_map, [])
                ]
            }
        }
        with open("savegame.json", "w") as f:
            json.dump(state, f, indent=2)

    def load_current_game(self):
        # try:
            # with open("savegame.json", "r") as f:
                # state = json.load(f)
            # self.player.x = state["player"]["x"]
            # self.player.y = state["player"]["y"]
            # self.player.hp = state["player"]["hp"]
            # self.player.stamina = state["player"]["stamina"]
            # self.player.hunger = state["player"]["hunger"]
            # self.player.items = [Food(item["name"], item.get("nutrition", 0)) for item in state["player"]["items"]]
            # self.current_map = tuple(map(int, state["current_map"].strip('()').split(',')))
            # self.maps = {tuple(map(int, k.strip('()').split(','))): Map(v) for k, v in state["maps"].items()}
            # self.map = self.maps[self.current_map]
            
            #Load enemies into dictionary
            # self.enemies = {}
            # for coord_str, enemy_list in state["enemies"].items():
                # coord = tuple(map(int, coord_str.strip('()').split(',')))
                # self.enemies[coord] = [Zombie("Zombie", e["hp"], e["x"], e["y"]) for e in enemy_list]
            
            #Place player and enemies on current map
            # self.map.load_state(self.player)
            # self.map.place_character(self.player)
            # for enemy in self.enemies.get(self.current_map, []):
                # self.map.place_character(enemy)
            
            # self.dirty_tiles.clear()
            # self.draw_grid()
            # self.draw_hud()
        # except FileNotFoundError:
            # print("No save file found")
        # except Exception as e:
            # print(f"Error loading game: {e}")
        try:
            with open("savegame.json", "r") as f:
                state = json.load(f)

            self.scene.clear()
            self.tile_items.clear()
            self.events = []
            # Load player
            self.player.x = state["player"]["x"]
            self.player.y = state["player"]["y"]
            self.player.hp = state["player"]["hp"]
            self.player.stamina = state["player"]["stamina"]
            self.player.hunger = state["player"]["hunger"]
            self.player.items = []
            for item_data in state["player"]["items"]:
                if item_data["nutrition"] > 0:
                    self.player.add_item(Food(
                        name=item_data["name"],
                        nutrition=item_data["nutrition"],
                        description=item_data.get("description", ""),
                        weight=item_data.get("weight", 1)
                    ))
            # Load equipped items
            equipped = state["player"]["equipped"]
            if equipped["primary_hand"]:
                self.player.equip_item(Weapon(
                    name=equipped["primary_hand"]["name"],
                    damage=equipped["primary_hand"]["damage"],
                    description=equipped["primary_hand"].get("description", ""),
                    weight=equipped["primary_hand"].get("weight", 1)
                ), "primary_hand")

            # Load maps
            self.current_map = tuple(state["current_map"])
            self.maps = {}
            for coord_str, map_data in state["maps"].items():
                coord = tuple(map(int, coord_str.strip('[]').split(',')))
                map_obj = Map(map_data["filename"])
                map_obj.saved_grid = map_data["saved_grid"]
                self.maps[coord] = map_obj

            # Load enemies for current map
            self.enemies = {}
            enemies_data = state["enemies"].get(str(list(self.current_map)), [])
            self.enemies[self.current_map] = []
            for e in enemies_data:
                enemy = Zombie("Zombie", e["hp"], e["x"], e["y"])
                enemy.type = e["type"]
                enemy.patrol_direction = tuple(e["patrol_direction"])
                enemy.stance = e["stance"]
                for item_data in e["items"]:
                    if item_data["nutrition"] > 0:
                        enemy.add_item(Food(
                            name=item_data["name"],
                            nutrition=item_data["nutrition"],
                            description=item_data.get("description", ""),
                            weight=item_data.get("weight", 1)
                        ))
                self.enemies[self.current_map].append(enemy)

            # Initialize empty enemy lists for other maps
            for coord in self.maps:
                if coord != self.current_map and coord not in self.enemies:
                    self.enemies[coord] = []

            # Set current map and restore state
            self.map = self.maps[self.current_map]
            self.map.load_state(self.enemies[self.current_map])
            self.map.place_character(self.player)
            for enemy in self.enemies[self.current_map]:
                self.map.place_character(enemy)

            #self.tile_items.clear()
            self.draw_grid()
            self.draw_hud()
        except FileNotFoundError:
            print("No save file found")
        except Exception as e:
            print(f"Error loading game: {e}")
    
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
        
    def fill_enemies(self, num_enemies):
        print(f"Filling enemies for map {self.current_map}")
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
                enemy = Zombie("Zombie", 20, x, y)
                if self.map.place_character(enemy):
                    self.enemies[self.current_map].append(enemy)  # Add to current map's list
                    
                    placed += 1
                    print(f"Placed enemy at ({x}, {y})")
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
            self.fill_enemies(max_enemies=50)
        self.update_messages()  # Critical: Update message window    
        self.draw_grid()
        self.draw_hud()

    def process_events(self):
        # Future: handle enemy logic, attacks, etc.
        for event in sorted(self.events, key=lambda e: getattr(e, 'priority', 0)):
            if isinstance(event, AttackEvent):
                self.resolve_attack(event)
            elif isinstance(event, MoveEvent):
                self.dirty_tiles.add((event.old_x, event.old_y))  # Redraw vacated tile    
            elif isinstance(event, PickupEvent):
                for item in event.tile.items[:]:
                    if event.character.pickup_item(item):
                        event.tile.remove_item(item)
                        self.add_message(f"{event.character.name} picked up {item.name}")
                        self.dirty_tiles.add((event.character.x, event.character.y))  # Redraw tile
            elif isinstance(event, UseItemEvent):
                if event.item.use(event.character):
                    event.character.remove_item(event.item)  # Remove used item
                    self.draw_hud()  # Update HUD to reflect hunger change            
            # Add other event types (e.g., MoveEvent, PickupEvent)
        self.events.clear()

    def resolve_attack(self, event):
        event.target.hp -= event.damage
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
            print(f"Updating {len(self.enemies[self.current_map])} enemies for map {self.current_map}")
            for enemy in self.enemies[self.current_map]:
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
        elif key == Qt.Key_F5:  # Save game
            self.save_current_game()
            print("Game saved")
            return
        elif key == Qt.Key_F8:  # Load game
            self.load_current_game()
            print("Game loaded")
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






























