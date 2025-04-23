# this is the entry point: start.pyw 
# other files: 
# start.pyw 
# -> gui.py
# -----> reality.py
# ---------> events.py 
# ---------> config.py 
# ---------> serialization.py 

# project
from serialization import *
from reality import *
from gui import *
from events import * 
from config import *

# built-in
import shutil
import tempfile
import json
import os
import sys
import math 
import random

# third-party
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem, QGraphicsOpacityEffect  
from PyQt5.QtCore import Qt, QRectF, QUrl, QPropertyAnimation, QTimer
from PyQt5.QtGui import QColor, QTransform, QFont

# Set working directory to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class Game_Component__React:
    def __init__(self):
        self._current_day = 0  # Track current day for flag reset 
        self._turn = 0  # Track turns
    # .turn
    @property
    def turn(self):
        return self._turn
    @turn.setter
    def turn(self, value):
        self._turn = value
        self.Event_NewTurn()
    
    # .current_day
    @property
    def current_day(self):
        return self._current_day
    @current_day.setter
    def current_day(self, value):
        self._current_day = value
        self.Event_NewDay()
    
    # Event Handlers 
    def Event_NewTurn(self):
        pass
            
    def Event_NewDay(self):
        pass

class Game(QGraphicsView, Serializable, Game_Component__React):
    # -- class variables
    __serialize_only__ = [
        "version",
        "rotation",
        "player",
        "current_map", # map coords
        "_turn",
        "current_slot",
        "low_hp_triggered",
        "low_hunger_triggered",
        "_current_day",
        "is_music_muted",
    ]
    
    # -- inits
    def __init__(self):
        super().__init__()
        self.version = "1.0.0"
        # --
        self.turns_per_day = 2000
        self.low_hp_triggered = False  # Flag for low HP event
        self.low_hunger_triggered = False  # Flag for low hunger event
        # --
        self.init_viewport()
        self.init_gui()
        # -- 
        self.player = Player()
        self.current_map = (0,0,0) # Current map coordinates
        self.map = Map()
        self.maps = {(0,0,0):self.map}  # Store Map objects with coordinate keys
        # Create and place characters
        self.events = []  # Initialize events list
        self.enemies = {(0, 0, 0): []}  # Dictionary with map coords as keys, enemy lists as values
        # Initial render
        self.dirty_tiles = set()  # Track tiles that need redrawing
        self.tile_items = {}  # For optimized rendering
        self.current_slot = 1  # Track current save slot
        self.load_current_game()
    def init_viewport(self):
        self.grid_width = MAP_WIDTH
        self.grid_height = MAP_HEIGHT
        self.rotation = 0  # degrees: 0, 90, 180, 270
        self.view_width = 7
        self.view_height = 7
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.tile_size = 70 
    def init_gui(self):
        # init_view_port() | init_gui() 
        self.setFocusPolicy(Qt.StrongFocus)  # Ensure Game accepts focus
        self.setWindowTitle("PyQt Rogue Like")
        self.setFixedSize(self.view_width * self.tile_size, self.view_height * self.tile_size)
        # --
        self.inventory_window = None  # Initialize later on demand
        # Initialize message window
        self.message_popup = MessagePopup(self)  # Set Game as parent
        self.messages = []  # List of (message, turns_remaining) tuples
        # Add journal window
        self.journal_window = None
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
        
    # -- overrides
    def from_dict(self, dictionary):
        if not super().from_dict(dictionary):
            return False
        if self.current_map in self.maps and self.player:
            self.maps[self.current_map].place_character(self.player)
        return True
    
    # -- gui helpers
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
    def update_inv_window(self):
        if self.inventory_window: 
            if self.inventory_window.isVisible():
                self.inventory_window.update_inventory(self.player)
                self.setFocus()
    def take_note_on_diary(self):
        if not self.journal_window:
            self.journal_window = JournalWindow(self) 
        if self.journal_window.isVisible():
            self.journal_window.log_quick_diary_entry()
        else:
            self.journal_window.load_journal(self.current_slot)  # Refresh contents
            self.journal_window.log_quick_diary_entry()
            self.journal_window.show()
            self.journal_window.update_position()
        self.journal_window.save_journal()
        self.setFocus()
    
    # -- map transition helpers
    def player_new_x_y_horizontal(self, out_of_bounds_x, out_of_bounds_y):
        new_map_coord = None
        new_x = out_of_bounds_x
        new_y = out_of_bounds_y
        if out_of_bounds_x < 0:
            new_map_coord = (self.current_map[0] - 1, self.current_map[1], self.current_map[2])
            new_x = self.grid_width - 1
        elif out_of_bounds_x >= self.grid_width:
            new_map_coord = (self.current_map[0] + 1, self.current_map[1], self.current_map[2])
            new_x = 0
        elif out_of_bounds_y < 0:
            new_map_coord = (self.current_map[0], self.current_map[1] - 1, self.current_map[2])
            new_y = self.grid_height - 1
        elif out_of_bounds_y >= self.grid_height:
            new_map_coord = (self.current_map[0], self.current_map[1] + 1, self.current_map[2])
            new_y = 0
        return new_x, new_y, new_map_coord

    def find_stair_tile(self, map_obj, target_stair_coords):
        """Find a tile in map_obj with a stair attribute matching target_stair_coords."""
        for y in range(map_obj.height):
            for x in range(map_obj.width):
                tile = map_obj.get_tile(x, y)
                if tile and tile.stair == target_stair_coords:
                    return (tile.stair_x or x, tile.stair_y or y)
        return None
    
    def new_map_from_current_coords(
            self, 
            filename = "default", 
            prev_coords = None, 
            up = False
        ):
        self.scene.clear()
        self.tile_items.clear()
        self.events = []
        self.map = Map(
            filename, 
            coords=self.current_map, 
            previous_coords = prev_coords, 
            going_up = up
        )
        self.maps[self.current_map] = self.map # update the cached maps 
        self.fill_enemies()
        return self.map.starting_x, self.map.starting_y 
    
    # -- map transitions 
    def map_transition(
            self, 
            new_map_file, 
            new_map_coord, 
            map_type, 
            prv_coords = None, 
            going_up = False
        ):
        self.current_map = new_map_coord
        if new_map_coord not in self.maps: 
            self.maps[self.current_map] = Map(coords=self.current_map)
            self.map = self.maps[self.current_map]
            if not self.map.Load_JSON(new_map_file):
                print(f"Creating new map at {new_map_coord}")
                return self.new_map_from_current_coords(map_type, prev_coords = prv_coords, up = going_up)
            else:
                print(f"Loading Map from Saved File {self.current_map}")
                self.add_message(f"Loading Map {self.current_map}")
                # if self.player.current_tile.stair_x:
                    # return self.player.current_tile.stair_x, self.player.current_tile.stair_y
        else:
            print(f"Loading Map from Cache {self.current_map}")
            self.add_message(f"Loading Map {self.current_map}")
            self.map = self.maps[self.current_map]
            # if self.player.current_tile.stair_x:
                # return self.player.current_tile.stair_x, self.player.current_tile.stair_y
        self.enemies[self.current_map] = self.map.enemies 
        return None, None
    
    def horizontal_map_transition(self,x,y):
        self.events.clear()
        self.save_current_game(slot=self.current_slot)
        # print(">>> ", self.map, self.current_map)
        new_x, new_y, new_map_coord = self.player_new_x_y_horizontal(x,y)
        if not new_map_coord: return 
        saves_dir = "./saves"
        previous_map_file = os.path.join(saves_dir, f"map_{'_'.join(map(str, self.current_map))}_1.json")
        new_map_file = os.path.join(saves_dir, f"map_{'_'.join(map(str, new_map_coord))}_1.json")
        # removes the character from previous map
        self.map.remove_character(self.player)
        # save the previous map 
        self.map.Save_JSON(previous_map_file)
        # update player
        self.player.x = new_x
        self.player.y = new_y
        # check if the map already in self.maps
        map_type = random.choice(["procedural_lake", "procedural_field", "procedural_road", "procedural_forest"])
        self.map_transition(new_map_file, new_map_coord, map_type)
        # placing character to the new map 
        if not self.map.place_character(self.player):
            print(f"Error: Failed to place player at ({self.player.x}, {self.player.y})")
            self.player.x, self.player.y = self.map.width // 2, self.map.height // 2
            self.map.place_character(self.player)
        self.scene.clear()
        self.dirty_tiles.clear()
        self.draw_grid()
        self.draw_hud()
    
    def vertical_map_transition(self, target_map_coords, up):
        """Handle vertical map transition via stairs."""
        self.events.clear()
        self.save_current_game(slot=self.current_slot)
        if not self.player.current_tile:
            print("please update the current_tile on char")
        # Variables
        saves_dir = "./saves"
        new_map_coord = target_map_coords
        previous_map_file = os.path.join(saves_dir, f"map_{'_'.join(map(str, self.current_map))}_1.json")
        new_map_file = os.path.join(saves_dir, f"map_{'_'.join(map(str, new_map_coord))}_1.json")
        prev_x = self.player.x 
        prev_y = self.player.y 
        new_x = self.player.current_tile.stair_x
        new_y = self.player.current_tile.stair_y 
        prev_map_coord = self.map.coords
        prev_tile = self.player.current_tile 
        # Remove the Player and Save the Current Map 
        self.map.remove_character(self.player)
        self.map.Save_JSON(previous_map_file)
        # update player position from the stair 
        self.player.x = new_x
        self.player.y = new_y
        
        # do map transition || ?
        # do map transition || % old map | % new map || make the stairs from each map points to each other | transitioning
        # do map transition || % old map || % cached | % loaded || load and use the info on the stair to do the transition
        # do map transition || % old map || % cached || use the info on the stair to do the transition 
        
        # if a new map was created the test_x and test_y must be used to update the player position and the previous tile must be updated and the map saved again
        test_x, test_y = self.map_transition(new_map_file, new_map_coord, "procedural_dungeon", prev_map_coord, up) 
        if test_x:
            self.player.x = test_x
            self.player.y = test_y
            prev_tile.stair_x = test_x 
            prev_tile.stair_y = test_y 
            if self.map.place_character(self.player):
                new_tile = self.player.current_tile
                new_tile.stair_x = prev_x
                new_tile.stair_y = prev_y
            self.maps[prev_map_coord].Save_JSON(previous_map_file) # save with the updated tile 
            self.maps[new_map_coord].Save_JSON(new_map_file) 
        else: # old map
            if not self.map.place_character(self.player):
                print(">>> Failed to Place Character")
        # Update of Game Scene 
        self.scene.clear()
        self.dirty_tiles.clear()
        self.draw_grid()
        self.draw_hud()
        
    # -- save and load from file    
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
        self.fill_enemies()
        self.turn = 0
        
        self.add_message("Starting new game") 
        if self.inventory_window: self.inventory_window.update_inventory(self.player)
        # Initialize and clear journal
        if not self.journal_window:
            self.journal_window = JournalWindow(self)
            self.journal_window.append_text("Day 0 - The world was affected by the plague, why? Maybe I should've prayed more instead of living with mercenaries and whores, God don't look to us now, and there is no church to pray anymore. Almost every one has transformed to walking deads, their flesh is putrid and their hunger insatiable, strange enough, before they lose their minds, they try desesperately to find food to satiate the hunger, so it's almost certain that I will find some with them, I'm starving. \n\nI should check myself, I'm almost losing my mind too. If I'm right, to move use A,W,S,D, Left, Right, to attack moves forward (only), to enter or use stairs press C, to open inventory press I, to open journal press J. I should take notes often, press N to write a quick note. \n\nI need to find food ...")
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
        
        self.dirty_tiles = set()
        self.draw_grid()
        self.draw_hud()
        self.dirty_tiles.clear()    
    def save_current_game(self, slot=1):
        """Save the current map to its JSON file and player state to a central file."""
        # Delay the save operation slightly to allow fade-in
        try:
            # Ensure ./saves directory exists
            self.current_slot = slot  # Update current slot
            saves_dir = "./saves"
            if not os.path.exists(saves_dir): os.makedirs(saves_dir)
            # Save current map state
            map_file = os.path.join(saves_dir, f"map_{'_'.join(map(str, self.current_map))}_{slot}.json")
            self.map.Save_JSON(map_file)
            # save the player_file 
            player_file = os.path.join(saves_dir, f"player_state_{slot}.json")
            self.Save_JSON( player_file )
            # Backup player state
            if os.path.exists(player_file): shutil.copy(player_file, os.path.join(saves_dir, f"player_state_{slot}.json.bak"))
            # Save journal
            if self.journal_window: self.journal_window.save_journal()
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
        if not self.Load_JSON(player_file):
            print("here")
            print(f"Failed to Load or no File Found: {player_file}")
            self.start_new_game()
            return 
        # Clear current state
        self.scene.clear()
        self.tile_items.clear()
        self.events.clear()
        self.enemies.clear()
        self.maps.clear()
        # Load current map and update enemies
        map_file = os.path.join(saves_dir, f"map_{'_'.join(map(str, self.current_map))}_{slot}.json")
        self.map = Map("default", coords=self.current_map)
        if not self.map.Load_JSON(map_file):
            self.add_message(f"No map save file found for slot {slot}")
            print(f"No map save file found: {map_file}")
            self.new_map_from_current_coords()
        else:
            self.enemies[self.current_map] = self.map.enemies
        self.maps[self.current_map] = self.map
        
        # Place characters
        if not self.map.place_character(self.player):
            self.add_message(f"Warning: Could not place player at ({self.player.x}, {self.player.y})")
            self.player.x, self.player.y = self.grid_width // 2, self.grid_height // 2
            self.map.place_character(self.player)
        # Redraw
        self.draw_grid()
        self.draw_hud()
        self.add_message(f"Game loaded from slot {slot}!")
        # Initialize and load journal
        if not self.journal_window:
            self.journal_window = JournalWindow(self)
        self.journal_window.load_journal(slot)
    
    # -- viewport draws 
    def draw(self):
        self.draw_grid()
        self.draw_hud()
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
        else:
            print("Warning: Arrow sprite not found")
    def rotate_vector_for_camera(self, dx, dy):
        """ Rotation for drawing (camera)"""
        if self.rotation == 0:
            return dx, dy
        elif self.rotation == 90:
            return dy, -dx
        elif self.rotation == 180:
            return -dx, -dy
        elif self.rotation == 270:
            return -dy, dx    
    def rotate_vector_for_movement(self, dx, dy):
        """ Rotation for movement (world coordinates) """
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
    
    # -- game iteration 
    def game_iteration(self):
        self.update_player()
        self.turn += 1
        self.process_events()
        self.update_enemies()
        self.update_messages()  # Critical: Update message window 
        self.draw()
    
    def update_player(self):
        self.player.regenerate_stamina()
        self.player.regenerate_health()
        self.player.hunger = max(0, self.player.hunger - 1)  # Hunger decreases each turn
        # Check for special events and set flags
        if self.player.hp / self.player.max_hp < 0.2:
            self.low_hp_triggered = True
        if self.player.hunger / self.player.max_hunger < 0.1:
            self.low_hunger_triggered = True    
        if self.player.hunger <= 0:
            self.player.hp = max(0, self.player.hp - 1)  # Starvation damage
            if self.player.hp <= 0:
                self.add_message("Game Over: Starvation! Reloading last save...")
                self.Event_PlayerDeath()
                return
        
    def process_events(self):
        """Process events and trigger autosave for significant changes."""
        for event in sorted(self.events, key=lambda e: getattr(e, 'priority', 0)):
            if isinstance(event, AttackEvent):
                self.Event_DoAttack(event)
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
                    if hasattr(event.item,"uses"):
                        self.add_message(f"{event.item.name} used")
                        if event.item.uses <0:
                            event.character.remove_item(event.item)
                    else:
                        event.character.remove_item(event.item)
                        self.add_message(f"{event.item.name} used")
                    self.draw_hud()
                else:
                    self.add_message("Nevermind ...")
        self.events.clear()
    
    def fill_enemies(self, num_enemies=70):
        self.enemies[self.current_map] = self.map.fill_enemies(num_enemies)
                
    def update_enemies(self):
        if self.current_map in self.enemies:  # Check if map has enemies
            for enemy in self.enemies[self.current_map]:
                distance = abs(enemy.x - self.player.x) + abs(enemy.y - self.player.y)
                if distance >= 25: continue                
                old_x, old_y = enemy.x, enemy.y
                enemy.update(self.player, self.map, self)
                if (enemy.x, enemy.y) != (old_x, old_y):
                    self.events.append(MoveEvent(enemy, old_x, old_y))
                    self.dirty_tiles.add((old_x, old_y))
                    self.dirty_tiles.add((enemy.x, enemy.y))
            if len(self.enemies[self.current_map]) < 5:
                self.fill_enemies()
                
    # -- Qt Events
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
    def resizeEvent(self, event):
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        
    def keyPressEvent(self, event):
        key = event.key()
        dx, dy = 0, 0
        b_isForwarding = False
        if key == Qt.Key_F: # weapon skill  
            pass
        elif key == Qt.Key_N:
            self.take_note_on_diary()
            return 
        elif key == Qt.Key_J:  # Toggle journal window
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
                if tile.default_sprite == Tile.SPRITES.get("dungeon_entrance"):
                    self.vertical_map_transition(tile.stair, False)
                else:
                    self.vertical_map_transition(tile.stair, tile.default_sprite == Tile.SPRITES.get("stair_up"))
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
            #from items import Food  # Import here to avoid circular import
            for item in self.player.items:
                if isinstance(item, Food):
                    self.events.append(UseItemEvent(self.player, item))
                    self.game_iteration()
                    break
            self.update_inv_window()
            return    
        elif key == Qt.Key_G:  # Pickup items
            tile = self.map.get_tile(self.player.x, self.player.y)
            if tile and tile.items:
                self.events.append(PickupEvent(self.player, tile))
                self.dirty_tiles.add((self.player.x, self.player.y))  # Redraw tile
                self.game_iteration()
            self.update_inv_window()
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
            #self.player.add_item(WeaponRepairTool("whetstone"))
            if self.map.add_dungeon_entrance_at(self.player.x, self.player.y):
                self.dirty_tiles.add((self.player.x, self.player.y))  # Redraw tile
                self.draw_grid()
                self.draw_hud()
        else:
            self.game_iteration()
            return 

        if dx or dy:
            target_x, target_y = self.player.x + dx, self.player.y + dy
            tile = self.map.get_tile(target_x, target_y)
            if target_x <0 or target_x > self.grid_width-1 or target_y<0 or target_y> self.grid_height-1:
                self.horizontal_map_transition(target_x, target_y)  # Add this
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
    
    # -- Reactive Events Handlers
    def Event_NewTurn(self):
        # triggers the new day
        if self.turn // self.turns_per_day + 1 > self.current_day:
            self.current_day += 1
        
    def Event_NewDay(self):
        self.low_hp_triggered = False
        self.low_hunger_triggered = False
        self.current_day = new_day
        self.add_message(f"Day {self.current_day} begins")
        
    def Event_PlayerDeath(self):
        print("Game Over!")
        try:
            self.load_current_game()
            self.add_message("Last Save Reloaded")
        except FileNotFoundError:
            self.add_message("No Save File Found, Starting New Game")
            self.start_new_game()
        except Exception as e:
            self.add_message(f"Error Reloading Game: {e}, Starting New Game")
            self.start_new_game()
    
    def Event_DoAttack(self, event):
        event.target.hp -= event.damage
        if not event.target is self.player:
            self.add_message(f"{event.attacker.name} deals {event.damage} damage to {event.target.name}")
            if self.player.primary_hand:
                # weapon stamina consumption
                self.player.stamina = max(0, self.player.stamina - self.player.primary_hand.stamina_consumption)
                # weaopn durability consumption 
                self.player.primary_hand.decrease_durability()
                if self.player.primary_hand.damage < 0.5: self.player.primary_hand = None
                self.update_inv_window()
        if event.target.hp <= 0:
            self.Event_CharacterDeath(event)
    
    def Event_CharacterDeath(self, event):
        if event.target is self.player:
            self.Event_PlayerDeath()
        else:
            event.target.drop_on_death()
            if self.current_map in self.enemies and event.target in self.enemies[self.current_map]:
                self.enemies[self.current_map].remove(event.target)
            event.target.current_tile.current_char = None
            
if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = Game()
    game.show()
    sys.exit(app.exec_())

# --- END 






























