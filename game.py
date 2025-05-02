# game.py
    # gui.py
    # mapping.py
        # reality.py
        # events.py 
        # globals_variables.py 
        # serialization.py 
        # performance.py 

# project
from performance import *
from serialization import *
from reality import *
from gui import *
from events import * 
from globals_variables import *
from mapping import * 

# built-in
import os
import sys
import math 
import random
import re 

# third-party
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem, QGraphicsOpacityEffect  
from PyQt5.QtCore import Qt, QRectF, QUrl, QPropertyAnimation, QTimer
from PyQt5.QtGui import QColor, QTransform, QFont

# Main Window Class 
class Game(QGraphicsView, Serializable):
    # -- class variables
    __serialize_only__ = [
        "version",
        "rotation",
        "players",
        "current_map", # map coords
        "turn",
        "current_slot",
        "low_hp_triggered",
        "low_hunger_triggered",
        "current_day",
        "is_music_muted",
        "current_player",
        "certificates"
    ]
    # -- inits
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.alt_pressed = False
        self.version = "1.0.0"
        # --
        self.turn = 0
        self.current_day = 0
        self.turns_per_day = 1000
        self.low_hp_triggered = False  # Flag for low HP event
        self.low_hunger_triggered = False  # Flag for low hunger event
        self.last_encounter_description = ""
        self.certificates = []
        # --
        self.is_music_muted = False
        self.init_viewport()
        self.init_gui()
        # -- 
        #xy = self.map.get_random_walkable_tile()
        #if not xy: xy = (50,50)
        self.player = None #Player() # 
        self.current_player = None # string key identifier
        self.players = {} # players storage 
        self.prior_next_index = 0
        self.prior_next_players = []
        self.current_map = (0,0,0) # Current map coordinates
        self.map = Map()
        self.maps = {(0,0,0):self.map}  # Store Map objects with coordinate keys
        # Create and place characters
        self.events = []  # Initialize events list
        # Initial render
        self.dirty_tiles = set()  # Track tiles that need redrawing
        self.tile_items = {}  # For optimized rendering
        self.current_slot = 1  # Track current save slot
        Tile._load_sprites()
        self.load_current_game()
    def init_viewport(self):
        self.grid_width = MAP_WIDTH
        self.grid_height = MAP_HEIGHT
        self.rotation = 0  # degrees: 0, 90, 180, 270
        self.view_width = VIEW_WIDTH_IN_TILES
        self.view_height = VIEW_HEIGHT_IN_TILES
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.tile_size = TILE_SIZE 
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
        self.music_player = None
        self.load_random_music()

    # -- music
    def get_random_music_filename(self,directory="music", pattern=""):
        # Compile the regex pattern
        regex = re.compile(pattern)

        # List all files in the directory
        all_files = os.listdir(directory)
        if len(all_files)==0: return None

        # Filter files that match the pattern
        matching_files = [ os.path.join(directory, f) for f in all_files if regex.match(f) ]

        # Return a random file or None if no matches
        return random.choice(matching_files) if matching_files else None
    def load_music(self, music_path):
        if not self.music_player:
            self.music_player = QMediaPlayer()
        self.is_music_muted = False
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
    def load_random_music(self):
        if self.is_music_muted: return None
        return self.load_music( self.get_random_music_filename() )
        
    # -- players - players and allies are the same 
    def add_player(self, key, **kwargs): # add a player or ally in dictionary 
        obj = Player(**kwargs)
        self.players.update({ key : obj })
        self.update_prior_next_selection()
        return obj 
    def set_player(self, name): # set the Game.player by dictionary name  
        self.player = self.players[name]
        self.current_player = name 
        self.player.party = False
    def set_player_name(self,key,new_name):
        player = self.players.get(key,None)
        if not player: return False
        self.players.pop(key)
        player.name = new_name 
        self.players.update({new_name:player})
        return True
    def place_players(self):
        for k,v in iter(self.players.items()):
            if v is self.player: continue
            if v.party: continue 
            if v.current_map != self.current_map: continue 
            self.map.place_character(v)
        return self.map.place_character(self.player)
    def remove_player(self, key = None):
        if len(list(self.players.keys())) <= 1: 
            self.add_message("Must have at least one adventurer ...")
            return 
        if not key: key = self.current_player
        self.map.remove_character(self.players[key])
        self.players.pop(key)
        new_key_name = random.choice( list(self.players.keys()) )
        if not new_key_name: return 
        self.set_player(new_key_name)
        self.update_prior_next_selection()
    def update_prior_next_selection(self):
        self.prior_next_index = 0
        try:
            self.prior_next_players = [self.player.name]+[ key for key,value in iter(self.players.items()) if (value.party == False and value.current_map == self.current_map and (not value is self.player)) ]
        except:
            self.prior_next_players = []
    
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
    def add_message(self, message, turns=15):
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
        self.map.fill_enemies()
        return self.map.starting_x, self.map.starting_y 
    def map_transition(
            self, 
            new_map_file, 
            new_map_coord, 
            map_type, 
            prv_coords = None, 
            going_up = False
        ):
        self.load_random_music()
        self.player.current_map = new_map_coord
        self.current_map = new_map_coord
        self.move_party()
        if new_map_coord not in self.maps: 
            self.maps[self.current_map] = Map(coords=self.current_map)
            self.map = self.maps[self.current_map]
            if not self.map.Load_JSON(new_map_file):
                if new_map_coord:
                    print(f"Creating new map at ({new_map_coord[0]}, {-new_map_coord[1]}, {new_map_coord[2]})")
                return self.new_map_from_current_coords(map_type, prev_coords = prv_coords, up = going_up)
            else:
                print(f"Loading Map from Saved File {self.current_map}")
                if self.current_map:
                    self.add_message(f"Loading Map from Saved File ({self.current_map[0]}, {-self.current_map[1]}, {self.current_map[2]})")
        else:
            print(f"Loading Map from Cache {self.current_map}")
            if self.current_map:
                self.add_message(f"Loading Map from Cache ({self.current_map[0]}, {-self.current_map[1]}, {self.current_map[2]})")
            self.map = self.maps[self.current_map]
        return None, None
    def safely_place_character_to_new_map(self,char=None):
        if not char: char = self.player 
        if not char: return 
        if not self.map.place_character(char):
            print(f"Error: Failed to place player at ({char.x}, {char.y})")
            old_x = char.x
            old_y = char.y
            b_placed = False
            for dx,dy in SQUARE_DIFF_MOVES_5x5:
                tile = self.map.get_tile(old_x+dx , old_y+dy)
                if not tile: continue
                if self.map.is_adjacent_walkable(tile, old_x+dx, old_y+dy):
                    char.x = old_x+dx 
                    char.y = old_y+dy
                    if self.map.place_character(char): 
                        b_placed = True
                        break 
            if not b_placed:
                char.x, char.y = self.map.width // 2, self.map.height // 2
                self.map.place_character(char)
    
    # -- map transitions 
    def horizontal_map_transition(self,x,y):
        T1 = tic()
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
        #map_type = "procedural_lake" # debug 
        
        self.map_transition(new_map_file, new_map_coord, map_type)
        # placing character to the new map 
        self.safely_place_character_to_new_map()
        # if not self.map.place_character(self.player):
            # print(f"Error: Failed to place player at ({self.player.x}, {self.player.y})")
            # old_x = self.player.x
            # old_y = self.player.y
            # b_placed = False
            # for dx,dy in SQUARE_DIFF_MOVES_5x5:
                # tile = self.map.get_tile(old_x+dx , old_y+dy)
                # if not tile: continue
                # if self.map.is_adjacent_walkable(tile, old_x+dx, old_y+dy):
                    # self.player.x = old_x+dx 
                    # self.player.y = old_y+dy
                    # if self.map.place_character(self.player): 
                        # b_placed = True 
                        # break 
            # if not b_placed:
                # self.player.x, self.player.y = self.map.width // 2, self.map.height // 2
                # self.map.place_character(self.player)
        self.scene.clear()
        self.dirty_tiles.clear()
        self.draw_grid()
        self.draw_hud()
        toc(T1,"Game.horizontal_map_transition() ||")
    def vertical_map_transition(self, target_map_coords, up):
        """Handle vertical map transition via stairs."""
        T1 = tic()
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
        toc(T1,"Game.vertical_map_transition() ||")
    
    # -- save and load from file - try to use the already created map    
    def start_new_game(self, new_character_name = "Main Character", b_clear_players = True):
        """Reset the game to a new state."""
        self.scene.clear()
        self.tile_items.clear()
        self.current_map = (0, 0, 0)
        if b_clear_players: self.players.clear()
        b_is_new = False
        if self.try_load_map_or_create_new():
            b_is_new = True
        xy = self.map.get_random_walkable_tile()
        if not xy: xy = (50,50)
        self.add_player(new_character_name, name = new_character_name, hp = 100, x=xy[0], y=xy[1], b_generate_items=True)
        self.set_player(new_character_name)
        if b_is_new: Castle.new(self)
        self.player.hunger = 200
        self.player.max_hunger = 1000
        self.events = []
        self.place_players()
        #self.map.place_character(self.player)
        self.turn = 0
        self.current_day = 0
        
        self.add_message("Starting new game") 
        if self.inventory_window: self.inventory_window.update_inventory(self.player)
        # Initialize and clear journal
        if not self.journal_window:
            self.journal_window = JournalWindow(self)
        if not self.journal_window.isVisible():
            self.journal_window.show()
            self.journal_window.update_position()
        self.journal_window.clear_text()
        self.journal_window.append_text("Day 0 - The world was affected by the plague, why? Maybe I should've prayed more instead of living with mercenaries and whores, God don't look to us now, and there is no church to pray anymore. Almost every one has transformed to walking deads, their flesh is putrid and their hunger insatiable, strange enough, before they lose their minds, they try desesperately to find food to satiate the hunger, so it's almost certain that I will find some with them, I'm starving. \n\nI should check myself, I'm almost losing my mind too. If I'm right, to move use A,W,S,D, Left, Right, to attack moves forward (only), to enter or use stairs press C, to open inventory press I, to open journal press J. I should take notes often, press N to write a quick note. \n\nI need to find food ...")
        self.setFocus()
        # Trigger music playback if not muted
        if not self.is_music_muted:
            if self.music_player.mediaStatus() in (QMediaPlayer.LoadedMedia, QMediaPlayer.BufferedMedia):
                self.music_player.play()
                print("Music started in start_new_game")
            else:
                print("Music not ready in start_new_game, waiting for LoadedMedia")
        
        self.update_prior_next_selection()
        self.dirty_tiles = set()
        self.draw_grid()
        self.draw_hud()
        self.dirty_tiles.clear()    
    def save_current_game(self, slot=1):
        """Save the current map to its JSON file and player state to a central file."""
        T1 = tic()
        # Delay the save operation slightly to allow fade-in
        try:
            # Ensure ./saves directory exists
            self.current_slot = slot  # Update current slot
            saves_dir = "./saves"
            if not os.path.exists(saves_dir): os.makedirs(saves_dir)
            # Save current map state
            map_file = os.path.join(saves_dir, f"map_{'_'.join(map(str, self.current_map))}_{slot}.json")
            #T2 = tic()
            self.map.Save_JSON(map_file)
            #toc(T2,"Game.save_current_game() || map.Save_JSON() ||")
            # save the player_file 
            player_file = os.path.join(saves_dir, f"player_state_{slot}.json")
            #T3 = tic()
            self.Save_JSON( player_file )
            #toc(T3,"Game.save_current_game() || Game.Save_JSON() ||")
            # Backup player state
            #T4 = tic()
            if os.path.exists(player_file): shutil.copy(player_file, os.path.join(saves_dir, f"player_state_{slot}.json.bak"))
            #toc(T4,"Game.save_current_game() || Backup Save ||")
            # Save journal
            #T5 = tic()
            if self.journal_window: self.journal_window.save_journal()
            #toc(T5,"Game.save_current_game() || Journal Save ||")
            self.add_message(f"Game saved to slot {slot}!")
        except Exception as e:
            self.add_message(f"Failed to save game: {e}")
            print(f"Error saving game: {e}")
            if os.path.exists(os.path.join(saves_dir, f"player_state_{slot}.json.bak")):
                shutil.copy(os.path.join(saves_dir, f"player_state_{slot}.json.bak"), player_file)  # Restore backup
        toc(T1, "Game.save_current_game() ||")
    def try_load_map_or_create_new(self):
        """ return True if create a new map, return False otherwise """
        b_result = False
        saves_dir = "./saves"
        map_file = os.path.join(saves_dir, f"map_{'_'.join(map(str, self.current_map))}_{self.current_slot}.json")
        self.map = Map("default", coords=self.current_map)
        if not self.map.Load_JSON(map_file):
            self.add_message(f"No map save file found for slot {self.current_slot}")
            print(f"No map save file found: {map_file}")
            self.new_map_from_current_coords()
            b_result = True
        self.maps[self.current_map] = self.map
        return b_result
    def load_current_game(self, slot=1):
        """Load player state and current map from their respective JSON files."""
        #T1 = tic()
        saves_dir = "./saves"
        player_file = os.path.join(saves_dir, f"player_state_{slot}.json")
        if not self.Load_JSON(player_file):
            print(f"Failed to Load or no File Found: {player_file}")
            self.start_new_game()
            return         
        print("Current Player :", self.current_player)
        if len(self.players) == 0:
            self.start_new_game()
            return 
        if (not self.current_player) or (not self.current_player in self.players.keys()):
            for k,v in iter(self.players.items()):
                if k and v:
                    self.current_player = k
                    break 
        self.set_player(self.current_player)
        # Clear current state
        self.scene.clear()
        self.tile_items.clear()
        self.events.clear()
        self.maps.clear()
        # Load current map
        self.try_load_map_or_create_new()
        # place current character
        if not self.map.place_character(self.player):
            self.add_message(f"Warning: Could not place player at ({self.player.x}, {self.player.y})")
            self.player.x, self.player.y = self.map.get_random_walkable_tile()
            self.map.place_character(self.player)
        # Place characters
        self.place_players()
        self.update_prior_next_selection()
        # Redraw
        self.draw_grid()
        self.draw_hud()
        self.add_message(f"Game loaded from slot {slot}!")
        # Initialize and load journal
        if not self.journal_window:
            self.journal_window = JournalWindow(self)
        self.journal_window.load_journal(slot)
        self.player.rotation = self.rotation 
        
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
        oppacity = 180
        hud_width = self.view_width * self.tile_size
        hud_height = 50
        hud_y = self.view_height * self.tile_size - hud_height
        bar_width = (hud_width - 20) // 3
        bar_height = 10
        padding = 5

        # HP Bar (Red)
        hp_ratio = self.player.hp / self.player.max_hp
        hp_bar = QGraphicsRectItem(10, hud_y + padding, bar_width * hp_ratio, bar_height)
        hp_bar.setBrush(QColor(255,0,0,oppacity))
        if hp_ratio<0.8: self.scene.addItem(hp_bar)

        # Stamina Bar (Blue)
        stamina_ratio = self.player.stamina / self.player.max_stamina
        stamina_bar = QGraphicsRectItem(10 + bar_width + padding, hud_y + padding, bar_width * stamina_ratio, bar_height)
        stamina_bar.setBrush(QColor(0,0,255,oppacity))
        if stamina_ratio<0.8: self.scene.addItem(stamina_bar)

        # Hunger Bar (Yellow)
        hunger_ratio = self.player.hunger / self.player.max_hunger
        hunger_bar = QGraphicsRectItem(10 + 2 * (bar_width + padding), hud_y + padding, bar_width * hunger_ratio, bar_height)
        hunger_bar.setBrush(QColor(255,255,0,oppacity))
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
    
    # --
    def move_party(self):
        for k,v in iter(self.players.items()):
            if v is self.player: continue 
            if not v.party: continue 
            v.current_map = self.current_map
    def release_party(self, diff_moves = CROSS_DIFF_MOVES_1x1):
        print("releasing from party")
        x = self.player.x 
        y = self.player.y 
        for dx,dy in diff_moves:
            if not self.map.can_place_character_at(x+dx,y+dy): continue 
            # if not self.map.is_adjacent_walkable_at(x+dx,y+dy): continue 
            if dx == 0 and dy == 0: continue
            for key,value in iter(self.players.items()):
                if value.party:
                    value.x = x+dx 
                    value.y = y+dy 
                    value.current_map = self.current_map # ? 
                    value.party = False 
                    self.map.place_character(value)
                    self.draw()
                    break 
        self.update_prior_next_selection()
    def count_party(self):
        S = 0
        for i in self.players:
            if self.players[i].party == True:
                S += 1
        return S
    
    # -- game iteration 
    def game_iteration(self):
        self.turn += 1
        self.Event_NewTurn()
        self.process_events() 
        self.update_players() # which include player and allies 
        self.update_enemies()
        self.update_buildings()
        self.update_messages() # Critical: Update message window 
        self.draw()
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
    def update_players(self):
        self.player.update(self)
        for k,v in iter(self.players.items()):
            if v is self.player: continue 
            if v.party:
                if v.is_placed_on_map(self.map):
                    self.map.remove_character(v)
                continue 
            v.npc_update(self)
    def update_enemies(self): # maybe more maps could be updated, like maps with alive players 
        self.map.update_enemies(self)
    def update_buildings(self):
        for b in self.map.buildings:
            b.update()
                          
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
    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Alt:
            self.alt_pressed = False
    def keyPressEvent(self, event):
        # window movement 
        if event.key() == Qt.Key_Alt:
            self.alt_pressed = True
        if self.alt_pressed:
            if event.key() == Qt.Key_Left:
                self.move(self.x() - 10, self.y())
                return 
            elif event.key() == Qt.Key_Right:
                self.move(self.x() + 10, self.y())
                return 
            elif event.key() == Qt.Key_Up:
                self.move(self.x(), self.y() - 10)
                return 
            elif event.key() == Qt.Key_Down:
                self.move(self.x(), self.y() + 10)
                return 
        # game key input 
        key = event.key()
        dx, dy = 0, 0
        b_isForwarding = False
        stamina_bound = 20
        if key == Qt.Key_PageUp:
            if self.count_party() > 0: 
                self.add_message("Release Party to Change Character")
                return 
            if len(self.prior_next_players) <= 1:
                self.update_prior_next_selection()
            if len(self.prior_next_players) > 0:
                if self.prior_next_index>0:
                    self.prior_next_index -= 1 
                else:
                    self.prior_next_index = len(self.prior_next_players)-1
                self.set_player( self.prior_next_players[self.prior_next_index] )
                self.draw()
                return 
        elif key == Qt.Key_PageDown:
            if self.count_party() > 0: 
                self.add_message("Release Party to Change Character")
                return 
            if len(self.prior_next_players) <= 1:
                self.update_prior_next_selection()
            if len(self.prior_next_players) > 0:
                if self.prior_next_index<len(self.prior_next_players)-1:
                    self.prior_next_index += 1 
                else:
                    self.prior_next_index = 0
                self.set_player( self.prior_next_players[self.prior_next_index] )
                self.draw()
                return 
        elif key == Qt.Key_1:
            list_of_weapons = [ [wp, f"{wp.name} {wp.damage:.1f} [dmg]"] for wp in self.player.items if isinstance(wp, Weapon) ]
            if self.player.primary_hand and hasattr(self.player.primary_hand, "damage"):
                SB = SelectionBox( 
                    parent=self, 
                    item_list = ["[ Weapon Selection ]", f"-> primary: {self.player.primary_hand.name} {self.player.primary_hand.damage:.1f} [dmg]"]+[ i[1] for i in list_of_weapons ]+["Exit"], 
                    action = primary_menu, 
                    game_instance = self, 
                    list_of_weapons = list_of_weapons 
                )
            else:
                SB = SelectionBox( parent=self, item_list = ["[ Weapon Selection ]"]+[ i[1] for i in list_of_weapons ]+["Exit"], action = primary_menu, game_instance = self, list_of_weapons = list_of_weapons )
            SB.show()
        elif key == Qt.Key_B: # build menu 
            SB = SelectionBox(parent = self, item_list = [ "[ Certificates ]" ]+self.certificates+["Exit"], action = build_menu, game_instance = self )
            SB.show()
        elif key == Qt.Key_X: # skill menu            
            SB = SelectionBox(parent = self, item_list = [
                f"[ Available Skills ](days survived: {self.player.days_survived})",
                f"-> Current Map: { self.player.current_map[0]}, {-self.player.current_map[1] }, {self.player.current_map[2] }",
                f"-> Map Position: { self.player.x}, { self.map.height -self.player.y }",
                f"Release Party: { self.count_party() }",
                f"Dodge: { self.player.days_survived>=5 }",
                f"Power Attack: { self.player.days_survived>=15 }",
                f"Weapon Special Attack: { self.player.days_survived>=20 }",
                "Exit"
            ], action = skill_menu, game_instance = self, stamina_bound = stamina_bound)
            SB.show()
        elif key == Qt.Key_R:
            self.player.use_first_item_of(WeaponRepairTool, self)
            return
        elif key == Qt.Key_End:
            if self.player.days_survived >= 15:
                tx, ty = self.player.get_forward_direction()
                tile0 = self.map.get_tile(self.player.x+tx, self.player.y+ty)
                if tile0:
                    if not tile0.walkable:
                        self.add_message("Can't find a target ...")
                        return 
                    if tile0.current_char:
                        self.add_message("The enemy is too close to perform this attack ...")
                        return 
                tile1 = self.map.get_tile(self.player.x+2*tx, self.player.y+2*ty)
                if tile1:
                    if tile1.current_char:
                        if self.player.primary_hand:
                            if self.player.stamina<stamina_bound:
                                self.add_message("I'm exhausted ... I need to take a breathe")
                            else:
                                self.add_message("Powerful Strike ...")
                                self.events.append(
                                    AttackEvent(
                                        self.player, tile1.current_char, d(self.player.primary_hand.damage,3*self.player.primary_hand.damage) 
                                    ) 
                                )
                                self.player.stamina -= stamina_bound
                                self.game_iteration()
                                return 
                    else:
                        self.add_message("Can't find a target ...")
            else:
                self.journal_window.append_text("With 'end' key you activate de power strike skill, you must be one tile of distance to the target, if the target is too close there is no much space to perform that skill, in order to use it you must survive at least 15 days ...")
                self.add_message("I don't feel well enough to exercise ... maybe tomorrow I'll feel better.")
        elif key == Qt.Key_Control: # dodge backward
            if self.player.days_survived >= 5:
                if self.player.stamina<stamina_bound:
                    self.add_message("I'm exhausted ... I need to take a breathe")
                x = self.player.x 
                y = self.player.y
                fx, fy = self.player.get_forward_direction()
                bx = -fx 
                by = -fy
                #print(bx,by)
                b_is_walkable = True 
                tile = self.map.get_tile(x+bx,y+by)
                if tile and self.player.stamina>stamina_bound:
                    if tile.walkable:
                        tile2 = self.map.get_tile(x+2*bx,y+2*by)
                        if tile2:
                            if tile2.walkable:
                                dx = 2*bx 
                                dy = 2*by
                                self.player.stamina -= stamina_bound
                            else:
                                b_is_walkable = False
                        else:
                            b_is_walkable = False
                    else:
                        b_is_walkable = False
                else:
                    b_is_walkable = False
                if not b_is_walkable:
                    self.game_iteration()
            else:
                self.journal_window.append_text("With ctrl you activate de dodge skill and move 2 tiles backward, in order to use the dodge skill you must survive at least 5 days ...")
                self.add_message("I don't feel well enough to exercise ... maybe tomorrow I'll feel better.")
        elif key == Qt.Key_F: # weapon special skill 
            primary = self.player.primary_hand
            if primary:
                if hasattr(primary,"use_special"):
                    if primary.use_special(self.player, self.map, self):
                        self.game_iteration()
                        return 
                    else:
                        self.add_message("Can't Use Special Skill Right Now ...")
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
        elif key == Qt.Key_C:  # Interact with stair or special tile 
            tile = self.map.get_tile(self.player.x, self.player.y)
            if tile:
                if tile.stair:
                    if tile.default_sprite_key == "dungeon_entrance":
                        self.vertical_map_transition(tile.stair, False)
                    else:
                        self.vertical_map_transition(tile.stair, tile.default_sprite_key == "stair_up")
                    return
                elif isinstance(tile, TileBuilding):
                    SB = SelectionBox( tile.menu_list, action = tile.action(), parent = self, game_instance = self )
                    tile.update_menu_list(SB)
                    SB.show()
                    return 
            px, py = self.player.get_forward_direction()
            tile2 = self.map.get_tile(self.player.x+px, self.player.y+py)
            if tile:
                char = tile2.current_char
                if char and isinstance(char, Player):
                    SB = SelectionBox( [
                        f"[ {char.name} ]",
                        "Add to Party",
                        "items+",
                        "items-",
                        "Exit"
                    ], action = player_menu, parent = self, game_instance = self, npc = char )
                    SB.show()
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
            self.player.rotation = self.rotation 
            self.game_iteration()
            return        
        elif key == Qt.Key_Right:
            self.rotation = (self.rotation + 90) % 360
            self.player.rotation = self.rotation 
            self.game_iteration()
            return
        elif key == Qt.Key_E:  # Use first food item
            self.player.use_first_item_of(Food, self)
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
        elif key == Qt.Key_Escape:  # Main Menu 
            SB = SelectionBox( parent=self, item_list = [
                f"[ Main Menu ]", 
                f"-> Current Save Slot: {self.current_slot}",
                f"-> Character: {self.current_player}",
                "Resume",
                "Start New Game",
                "Character Settings >",
                "Load Game >", 
                "Save Game >", 
                "Quit to Desktop"
            ], action = main_menu, game_instance = self)
            SB.add_list("Load Game >", ["[ Main Menu > Load Game ]","Slot 1", "Slot 2", ".."])
            SB.add_list("Save Game >", ["[ Main Menu > Save Game ]","Slot 1", "Slot 2", ".."])
            SB.add_list("Select Player Sprite >", ["[ Character Settings > Select Sprite ]"] + SPRITE_NAMES_PLAYABLES + [".."])
            SB.add_list("Select Player Character >", ["[ Character Settings > Character Selection ]"] + [ k for k,v in self.players.items() if v.current_map == self.player.current_map and not v.party ] + [".."])
            SB.add_list("Character Settings >", [
                "[ Main Menu > Character Settings ]",
                "Select Player Sprite >",
                "Select Player Character >",
                "Change Current Character Name",
                ".."
            ] )
            SB.show()
        elif key == Qt.Key_F12:  # F12 Debugging: 
            SB = SelectionBox(parent=self, item_list = [
                "[ DEBUG MENU ]",
                "Set Day 100", 
                "Add Item >", 
                "Generate Enemies >", 
                "Restore Status",
                "Generate Dungeon Entrance", 
                "Add a Cosmetic Layer >",
                "Exit"
            ], action = debugging_menu, game_instance = self)
            SB.add_list("Add Item >",[
                "Whetstone",
                "Mace",
                "Long Sword",
                "Food",
                ".."
            ])
            SB.add_list("Generate Enemies >",[
                "Zombie",
                "Bear",
                "Rogue",
                "Mercenary",
                "Player",
                ".."
            ])
            SB.add_list("Add a Cosmetic Layer >", [
                "House",
                "Castle",
                "Lumber Mill",
                "Clear", 
                "Mill",
                "Tower",
                ".."
            ])
            SB.show()        
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
                    if b_isForwarding and not isinstance(tile.current_char, Player):
                        damage = self.player.calculate_damage_done()
                        self.events.append(AttackEvent(self.player, tile.current_char, damage))
                else:
                    old_x, old_y = self.player.x, self.player.y
                    if self.player.move(dx, dy, self.map):
                        self.events.append(MoveEvent(self.player, old_x, old_y))
                        self.dirty_tiles.add((old_x, old_y))
                        self.dirty_tiles.add((self.player.x, self.player.y))    
            self.game_iteration()
    
    # -- Reactive Events Handlers
    def Event_NewTurn(self):
        # triggers the new day
        # print(f"Turn {self.turn}")
        if self.turn // self.turns_per_day + 1 > self.current_day:
            self.current_day += 1
            self.Event_NewDay()
        if self.turn % 5 == 0: # refresh some variables 
            self.last_encounter_description = ""
        if self.turn % 100 == 0:
            self.add_message(f"Day : {self.current_day} Turn : {self.turn}")
    def Event_NewDay(self):
        print(f"Day {self.current_day}")
        self.player.days_survived += 1
        if self.current_day == 5:
            self.journal_window.append_text("(Skill - 5 days) I'm in full shape now, I'm feeling agile, use Ctrl to dodge and move two tiles backward ...") 
        if self.current_day == 20:
            self.journal_window.append_text("(Skill - 20 days) My body remembered how to use a sword properly, now I can perform deadly blows with F key. Whenever the enemy stay in L position like a knight chess I can swing my sword hit taking him off-guard ...") 
    def Event_PlayerDeath(self):
        # SANITY COMMENTS
        # 1. You lose your character on death and drop all items
        # 2. The map keeps the same, you must delete the maps on saves folder to start a full fresh game.
        # 3. If there is no characters on self.players then the game will start a new game character
        # 4. If there is characters on self.players then the game will try to take control of that character (what would happen if the character is on other map?)
        # 5. ... The game will try to load with that character set 
        # 6. Garrisoned Characters will not be available on death, but will stay saved on building map. 
        print("Game Over!")
        self.player.drop_on_death()
        if self.player.name in self.players.keys():
            print("Removing :",self.player.name)
            self.players.pop(self.player.name)
        self.player.current_tile.current_char = None
        self.release_party(SQUARE_DIFF_MOVES_5x5)
        # -- 
        if len(self.players) <= 0:
            try:
                self.add_message("You died, starting new game")
                self.start_new_game()
            except FileNotFoundError:
                self.add_message("No Save File Found, Starting New Game")
                self.start_new_game()
            except Exception as e:
                self.add_message(f"Error Reloading Game: {e}, Starting New Game")
                self.start_new_game()
        else:
            for k,v in iter(self.players.items()):
                if isinstance(v, Player):
                    self.set_player(v.name)
                    self.load_current_game(slot = self.current_slot)
                    self.draw()
                    break 
    def Event_DoAttack(self, event):
        primary = self.player.primary_hand
        # swords have the parry property in the player perspective, they will try to consume the stamina first 
        if event.target is self.player: # player being attacked
            self.last_encounter_description = getattr(event.attacker,"description")
            primary_attacker = event.attacker.primary_hand 
            if primary and primary_attacker:
                if isinstance(primary, Sword):
                    print(f"Defense Factor : {self.player.calculate_defense_factor():.5f}")
                    if random.random() < primary.get_player_parry_chance(self.player, event.attacker, event.damage) + self.player.calculate_defense_factor():
                        self.add_message(f"You parry the incoming attack ...")
                        self.player.stamina -= event.damage
                    else:
                        self.add_message(f"You've being hit, your foe is skilled in sword combat ...")
                        self.player.hp -= event.damage
                else: 
                    self.player.hp -= event.damage
            else:
                self.player.hp -= event.damage            
        else: # player attack
            if hasattr(event.target, "description"): self.last_encounter_description = getattr(event.target,"description")
            event.target.hp -= event.damage
            if self.player is event.attacker:
                self.add_message(f"{event.attacker.name} deals {event.damage:.1f} damage to {event.target.name}")
            if primary:
                if isinstance(primary, Weapon):
                    primary.stats_update(self.player)
                    self.update_inv_window()
        # in case of death 
        if event.target.hp <= 0:
            self.Event_CharacterDeath(event)
    def Event_CharacterDeath(self, event):
        if event.target is self.player:
            self.Event_PlayerDeath()
            self.update_prior_next_selection()
        else:
            event.target.drop_on_death()
            if event.target in self.map.enemies:
                self.map.enemies.remove(event.target)
            if event.target.name in self.players.keys():
                print("Removing :",event.target.name)
                self.players.pop(event.target.name)
                self.update_prior_next_selection()
            event.target.current_tile.current_char = None
            
# --- END 