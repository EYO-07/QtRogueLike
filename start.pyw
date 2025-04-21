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
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsRectItem
from PyQt5.QtCore import Qt, QRectF, QUrl
from PyQt5.QtGui import QColor, QTransform
from mapping import *
from living import *
from items import *
from events import *
import random  # Add for random enemy placement
from message_window import MessagePopup  # Import the new MessagePopup
from inventory_window import InventoryWindow
from journal_window import JournalWindow
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
        self.player = None
        #self.player = Player("Adventurer", 100, 50, 50, False)
        self.maps = {(0,0,0):None}  # Store Map objects with coordinate keys
        self.current_map = (0,0,0) # Current map coordinates
        self.map = self.maps[self.current_map]
        # Create and place characters
        self.events = []  # Initialize events list
        self.enemies = {(0, 0, 0): []}  # Dictionary with map coords as keys, enemy lists as values
        self.turn = 0  # Track turns
        
        # Initial render
        self.dirty_tiles = set()  # Track tiles that need redrawing
        self.tile_items = {}  # For optimized rendering
        self.setWindowTitle("PyQt Rogue Like")
        self.setFixedSize(self.view_width * self.tile_size, self.view_height * self.tile_size)
        Game.instance = self
        
        self.inventory_window = None  # Initialize later on demand
        # Initialize message window
        self.message_popup = MessagePopup(self)  # Set Game as parent
        self.messages = []  # List of (message, turns_remaining) tuples
        
        # Add journal window
        self.journal_window = None
        self.current_slot = 1  # Track current save slot
        self.low_hp_triggered = False  # Flag for low HP event
        self.low_hunger_triggered = False  # Flag for low hunger event
        self.current_day = 1  # Track current day for flag reset
        self.turns_per_day = 1000  # 1 day = 1000 turns
        
        # Initialize music player
        self.music_player = QMediaPlayer()
        self.is_music_muted = False
        music_path = "./music/dark_fantasy.mp3"
        if os.path.exists(music_path):
            self.music_player.setMedia(QMediaContent(QUrl.fromLocalFile(music_path)))
            self.music_player.setVolume(10)  # 0-100
            # Connect media status to start playback when loaded
            self.music_player.mediaStatusChanged.connect(self.handle_media_status)
            # Handle errors
            self.music_player.error.connect(
                lambda error: self.add_message(f"Music error: {self.music_player.errorString()}")
            )
            # Set looping
            try:
                self.music_player.setLoops(QMediaPlayer.Infinite)  # PyQt5 5.15+
            except AttributeError:
                # Fallback for older PyQt5
                self.music_player.mediaStatusChanged.connect(
                    lambda status: self.music_player.play() if status == QMediaPlayer.EndOfMedia and not self.is_music_muted else None
                )
        else:
            self.add_message(f"Music file {music_path} not found")
            print(f"Music file {music_path} not found")
        
        # Attempt to load saved game
        try:
            self.load_current_game()
        except FileNotFoundError:
            self.start_new_game()
            self.add_message("No save file found, starting new game") 
        except Exception as e:
            self.add_message(f"Error loading game on startup: {e}, starting new game") 
            print(f"Error loading game on startup: {e}, starting new game")
    
    def handle_media_status(self, status):
        """Handle media status changes to start playback when loaded."""
        if status == QMediaPlayer.LoadedMedia and not self.is_music_muted:
            self.music_player.play()
            print("Music started: Media loaded")
        elif status == QMediaPlayer.InvalidMedia:
            self.add_message("Music failed: Invalid media")
            print("Music failed: Invalid media")
    
    def toggle_music(self):
        """Toggle music mute state."""
        self.is_music_muted = not self.is_music_muted
        if self.is_music_muted:
            self.music_player.stop()
            self.add_message("Music muted")
        else:
            # Check if media is loaded before playing
            if self.music_player.mediaStatus() in (QMediaPlayer.LoadedMedia, QMediaPlayer.BufferedMedia):
                self.music_player.play()
                self.add_message("Music unmuted")
            else:
                self.add_message("Music not ready, will play when loaded")
                print("Music not ready, waiting for LoadedMedia state")
    
    def add_message(self, message, turns=5):
        """Add a message to the queue."""
        self.messages.append((message, turns))
        # Update pop-up with all active messages
        active_messages = [msg for msg, _ in self.messages]
        self.message_popup.set_message(active_messages)
        # print(f"Added message: '{message}' for {turns} turns, queue: {self.messages}")
        
    def update_messages(self):
        """Update message queue and refresh pop-up."""
        #print(f"Updating messages, current queue: {self.messages}")
        if not self.messages:
            self.message_popup.set_message([])
            return
        # Decrease turn counters and remove expired messages
        self.messages = [(msg, turns - 1) for msg, turns in self.messages if turns > 1]
        # Update pop-up with active messages
        active_messages = [msg for msg, _ in self.messages]
        self.message_popup.set_message(active_messages)
        #print(f"Active messages: {active_messages}")  
    
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

    def check_map_transition(self,x,y):
        new_map_coord = None
        new_x = self.player.x 
        new_y = self.player.y 
        if x < 0:
            new_map_coord = (self.current_map[0] - 1, self.current_map[1], self.current_map[2])
            new_x = self.grid_width - 1
        elif x >= self.grid_width:
            new_map_coord = (self.current_map[0] + 1, self.current_map[1], self.current_map[2])
            new_x = 0
        elif y < 0:
            new_map_coord = (self.current_map[0], self.current_map[1] - 1, self.current_map[2])
            new_y = self.grid_height - 1
        elif y >= self.grid_height:
            new_map_coord = (self.current_map[0], self.current_map[1] + 1, self.current_map[2])
            new_y = 0

        if new_map_coord:
            saves_dir = "./saves"
            map_file = os.path.join(saves_dir, f"map_{'_'.join(map(str, self.current_map))}_1.json")
            current_enemies = list(self.enemies.get(self.current_map, []))
            self.enemies[self.current_map] = []
            self.map.save_state(current_enemies, map_file)
            self.map.remove_character(self.player)
            self.player.x = new_x
            self.player.y = new_y
            if new_map_coord not in self.maps:
                print(f"Creating new map at {new_map_coord}")
                map_type = random.choice(["procedural_lake", "procedural_field", "procedural_road"])
                self.maps[new_map_coord] = Map(map_type, coords=new_map_coord)
            self.current_map = new_map_coord
            self.map = self.maps[self.current_map]
            map_file = os.path.join(saves_dir, f"map_{'_'.join(map(str, self.current_map))}_1.json")
            try:
                with open(map_file, "r") as f:
                    map_state = json.load(f)
                    fill_list = []
                    self.map.load_state(fill_list, map_state)
                    self.enemies[self.current_map] = fill_list
            except FileNotFoundError:
                self.add_message(f"No map file found for {self.current_map}, using generated map")
            except Exception as e:
                self.add_message(f"Failed to load map for {self.current_map}: {e}")
                print(f"Error loading map {map_file}: {e}")
            if not self.map.place_character(self.player):
                print(f"Error: Failed to place player at ({self.player.x}, {self.player.y})")
                self.player.x, self.player.y = self.map.width // 2, self.map.height // 2
                self.map.place_character(self.player)
            for enemy in self.enemies.get(self.current_map, []):
                if not self.map.place_character(enemy):
                    print(f"Warning: Failed to place enemy {enemy.name} at ({enemy.x}, {enemy.y})")
            if not self.enemies.get(self.current_map):
                self.enemies[self.current_map] = []
                self.fill_enemies(100)
            elif len(self.enemies[self.current_map]) < 5:
                self.fill_enemies(50)
            self.save_current_game(slot=1)
            self.scene.clear()
            self.dirty_tiles.clear()
            self.draw_grid()
            self.draw_hud()
    
    def find_stair_tile(self, map_obj, target_stair_coords):
        """Find a tile in map_obj with a stair attribute matching target_stair_coords."""
        for y in range(map_obj.height):
            for x in range(map_obj.width):
                tile = map_obj.get_tile(x, y)
                if tile and tile.stair == target_stair_coords:
                    return (tile.stair_x or x, tile.stair_y or y)
        return None
    
    def handle_stair_transition(self, target_map, up):
        """Handle vertical map transition via stairs."""
        if not isinstance(target_map, tuple):
            print(f"Error: target_map {target_map} is not a tuple")
            self.add_message("Cannot use stair: Invalid map coordinates")
            return

        self.add_message(f"Using stairs to map {target_map}")
        saves_dir = "./saves"
        current_tile = self.map.get_tile(self.player.x, self.player.y)
        prev_x, prev_y = self.player.x, self.player.y

        # Save current map
        map_file = os.path.join(saves_dir, f"map_{'_'.join(map(str, self.current_map))}_1.json")
        current_enemies = list(self.enemies.get(self.current_map, []))
        self.enemies[self.current_map] = []
        self.map.save_state(current_enemies, map_file)
        self.map.remove_character(self.player)

        previous_map = self.current_map
        self.current_map = target_map
        self.enemies[target_map] = []
        if target_map not in self.maps:
            self.maps[target_map] = Map("procedural_dungeon", coords=target_map, b_generate=False)
        self.map = self.maps[self.current_map]

        map_file = os.path.join(saves_dir, f"map_{'_'.join(map(str, self.current_map))}_1.json")
        try:
            with open(map_file, "r") as f:
                map_state = json.load(f)
                fill_list = []
                self.map.load_state(fill_list, map_state)
                self.enemies[self.current_map] = fill_list
                stair_pos = self.find_stair_tile(self.map, previous_map)
                if stair_pos:
                    self.player.x, self.player.y = stair_pos
                else:
                    print(f"Warning: No stair tile found on map {self.current_map} linking to {previous_map}")
                    self.player.x, self.player.y = self.map.width // 2, self.map.height // 2
        except FileNotFoundError:
            self.add_message(f"No map file found for {self.current_map}, generating new dungeon")
            new_coords = self.map.generate_procedural_dungeon(previous_map, prev_x, prev_y, up)
            self.player.x, self.player.y = new_coords[0], new_coords[1]
            prev_map = self.maps.get(previous_map)
            if prev_map and current_tile:
                current_tile.stair_x = self.player.x
                current_tile.stair_y = self.player.y
                prev_map_file = os.path.join(saves_dir, f"map_{'_'.join(map(str, previous_map))}_1.json")
                prev_map.save_state(current_enemies, prev_map_file)
                print(f"Updated previous map {previous_map} stair at ({prev_x}, {prev_y}) to point to ({self.player.x}, {self.player.y})")
        except Exception as e:
            self.add_message(f"Failed to load map for {self.current_map}: {e}")
            print(f"Error loading map {map_file}: {e}")
            new_coords = self.map.generate_procedural_dungeon(previous_map, prev_x, prev_y, up)
            self.player.x, self.player.y = new_coords[0], new_coords[1]
            prev_map = self.maps.get(previous_map)
            if prev_map and current_tile:
                current_tile.stair_x = self.player.x
                current_tile.stair_y = self.player.y
                prev_map_file = os.path.join(saves_dir, f"map_{'_'.join(map(str, previous_map))}_1.json")
                prev_map.save_state(current_enemies, prev_map_file)
                print(f"Updated previous map {previous_map} stair at ({prev_x}, {prev_y}) to point to ({self.player.x}, {self.player.y})")

        if not self.map.place_character(self.player):
            print(f"Error: Failed to place player at ({self.player.x}, {self.player.y}) on map {self.current_map}")
            self.player.x, self.player.y = self.map.width // 2, self.map.height // 2
            self.map.place_character(self.player)

        for enemy in self.enemies.get(self.current_map, []):
            if not self.map.place_character(enemy):
                print(f"Warning: Failed to place enemy {enemy.name} at ({enemy.x}, {enemy.y})")

        if not self.enemies[self.current_map]:
            self.fill_enemies(100)
        elif len(self.enemies[self.current_map]) < 5:
            self.fill_enemies(50)

        self.save_current_game(slot=1)
        print(f"handle_stair_transition(): Current Map Coords: {self.current_map}")
        self.scene.clear()
        self.dirty_tiles.clear()
        self.draw_grid()
        self.draw_hud()

    def start_new_game(self):
        """Reset the game to a new state."""
        self.scene.clear()
        self.tile_items.clear()
        self.maps = {(0, 0, 0): Map("default", coords=self.current_map)}
        self.current_map = (0, 0, 0)
        self.map = self.maps[self.current_map]
        self.player = Player("Adventurer", 100, 50, 50)
        self.player.hunger = 200
        self.player.max_hunger = 1000
        self.events = []
        self.enemies = {(0, 0, 0): []}
        self.map.place_character(self.player)
        self.fill_enemies(20)
        self.turn = 0
        self.dirty_tiles = set()
        self.draw_grid()
        self.draw_hud()
        self.dirty_tiles.clear()    
        self.add_message("Starting new game") 
        if self.inventory_window: self.inventory_window.update_inventory(self.player)
        # Initialize and clear journal
        if not self.journal_window:
            self.journal_window = JournalWindow(self)
            self.journal_window.append_text("Day 0 - The world was affected by the plague, why? Maybe I should've prayed more instead of living with mercenaries and whores, God don't look to us now, and there is no church to pray anymore. Almost every one has transformed to walking deads, their flesh is putrid and their hunger insatiable, strange enough, before they lose their minds, they try desesperately to find food to satiate the hunger, so it's almost certain that I will find some with them, I'm starving. \n\nI should check myself, I'm almost losing my mind too. If I'm right, to move use A,W,S,D, Left, Right, to attack moves forward (only), to enter or use stairs press C, to open inventory press I, to open journal press J. \n\nI need to find food ...")
        if not self.journal_window.isVisible():
            self.journal_window.show()
            self.journal_window.update_position()
        self.journal_window.load_journal(self.current_slot)
        self.setFocus()
        # Trigger music playback if not muted
        if not self.is_music_muted:
            if self.music_player.mediaStatus() in (QMediaPlayer.LoadedMedia, QMediaPlayer.BufferedMedia):
                self.music_player.play()
                print("Music started in start_new_game")
            else:
                print("Music not ready in start_new_game, waiting for LoadedMedia")
        
    def save_current_game(self, slot=1):
        """Save the current map to its JSON file and player state to a central file."""
        try:
            # Ensure ./saves directory exists
            self.current_slot = slot  # Update current slot
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
                },
                "music_muted": self.is_music_muted,
                "low_hp_triggered": self.low_hp_triggered,
                "low_hunger_triggered": self.low_hunger_triggered,
                "current_day": self.current_day
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
            
            # Save journal
            if self.journal_window:
                self.journal_window.save_journal()
            self.add_message(f"Game saved to slot {slot}!")
            
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
        self.player = Player("Adventurer",100,50,50, False) # testing if solves the issue 
        try:
            # Load player state
            with open(player_file, "r") as f:
                state = json.load(f)

            self.current_slot = slot  # Update current slot
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
            self.low_hp_triggered = state.get("low_hp_triggered", False)
            self.low_hunger_triggered = state.get("low_hunger_triggered", False)
            self.current_day = state.get("current_day", 1)

            # Redraw
            self.draw_grid()
            self.draw_hud()
            self.add_message(f"Game loaded from slot {slot}!")

            # Initialize and load journal
            if not self.journal_window:
                self.journal_window = JournalWindow(self)
            self.journal_window.load_journal(slot)

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
                if self.map.enemy_type == "dungeon":
                    if coin < 0.7:
                        enemy = Zombie("Zombie", 25, x, y)
                    else:
                        enemy = Rogue("Rogue", 35, x, y)
                elif self.map.filename == 'default':
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
        # Check for special events and log to journal
        # if self.player.hp / self.player.max_hp < 0.2 and self.journal_window:
            # self.journal_window.append_text("I almost died, that enemy was tough, bastard.")
        # if self.player.hunger / self.player.max_hunger < 0.1 and self.journal_window:
            # self.journal_window.append_text("I’m hungry, I need food right now, I could eat a horse.")
        new_day = self.turn // self.turns_per_day + 1
        if new_day > self.current_day:
            self.low_hp_triggered = False
            self.low_hunger_triggered = False
            self.current_day = new_day
            self.add_message(f"Day {self.current_day} begins")
        # Check for special events and set flags
        if self.player.hp / self.player.max_hp < 0.2:
            self.low_hp_triggered = True
        if self.player.hunger / self.player.max_hunger < 0.1:
            self.low_hunger_triggered = True    
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
        self.add_message(f"{event.attacker.name} deals {event.damage} damage to {event.target.name}")
        
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
        #print(self.current_map)
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
            pass 
            #print(f"No enemies found for map {self.current_map}")
                    
    # gE := Event Handlers
    def resizeEvent(self, event):
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        
    def keyPressEvent(self, event):
        key = event.key()
        dx, dy = 0, 0
        b_isForwarding = False
        if key == Qt.Key_J:  # Toggle journal window
            if not self.journal_window:
                self.journal_window = JournalWindow(self)
            if self.journal_window.isVisible():
                self.journal_window.save_journal()  # Save on close
                self.journal_window.hide()
            else:
                self.journal_window.load_journal(self.current_slot)  # Refresh contents
                self.journal_window.show()
                self.journal_window.update_position()
            self.setFocus()
            return
        elif key == Qt.Key_M:  # Toggle music
            self.toggle_music()
            return
        elif key == Qt.Key_Plus:
            volume = min(self.music_player.volume() + 10, 100)
            self.music_player.setVolume(volume)
            self.add_message(f"Music volume: {volume}%")
            return
        elif key == Qt.Key_Minus:
            volume = max(self.music_player.volume() - 10, 0)
            self.music_player.setVolume(volume)
            self.add_message(f"Music volume: {volume}%")
            return    
        elif key == Qt.Key_C:  # Interact with stair
            tile = self.map.get_tile(self.player.x, self.player.y)
            if tile and tile.stair:
                self.handle_stair_transition(tile.stair, tile.default_sprite == Tile.SPRITES.get("stair_up"))
                return
        elif key in (Qt.Key_Up, Qt.Key_W):
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
            #print(self.player.items)
            from items import Food  # Import here to avoid circular import
            for item in self.player.items:
                if isinstance(item, Food):
                    self.events.append(UseItemEvent(self.player, item))
                    self.game_iteration()
                    break
            if self.inventory_window: 
                if self.inventory_window.isVisible():
                    self.inventory_window.update_inventory(self.player)
                    self.setFocus()
            return    
        elif key == Qt.Key_G:  # Pickup items
            tile = self.map.get_tile(self.player.x, self.player.y)
            if tile and tile.items:
                self.events.append(PickupEvent(self.player, tile))
                self.dirty_tiles.add((self.player.x, self.player.y))  # Redraw tile
                self.game_iteration()
            if self.inventory_window: 
                if self.inventory_window.isVisible():
                    self.inventory_window.update_inventory(self.player)
                    self.setFocus()
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
            #print("Pressing I: ",self.player.primary_hand, self.player.items)
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
        
        elif key == Qt.Key_F1:  # Debugging: Place a stair_down at player's position
            current_x, current_y, current_z = self.current_map
            target_map = (current_x, current_y, current_z - 1)
            tile = self.map.get_tile(self.player.x, self.player.y)
            if tile:
                # Remove any existing character or items to simplify
                tile.current_char = None  # Temporarily remove player
                tile.items.clear()
                # Set stair properties
                tile.walkable = True
                tile.default_sprite = Tile.SPRITES.get("dungeon_entrance", Tile.SPRITES.get("floor"))
                tile.stair = target_map
                # Place player back
                tile.current_char = self.player
                self.player.current_tile = tile
                # Mark tile for redraw
                self.dirty_tiles.add((self.player.x, self.player.y))
                self.scene.clear()
                self.draw_grid()
                self.draw_hud()
                # Save the map to persist the stair
                saves_dir = "./saves"
                map_file = os.path.join(saves_dir, f"map_{'_'.join(map(str, self.current_map))}_1.json")
                self.map.save_state(self.enemies.get(self.current_map, []), map_file)
                self.add_message(f"Placed stair_down at ({self.player.x}, {self.player.y}) leading to {target_map}")
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






























