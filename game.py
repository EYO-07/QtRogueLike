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
import vector as vec 

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
from PyQt5.QtGui import QColor, QTransform, QFont, QBrush

# --
class Game_SOUNDMANAGER:
    def __init__(self):
        self.music_player = None
        self.is_music_muted = False
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
            self.music_player.setVolume(10)  # 0-100
            # Connect media status to start playback when loaded
            self.music_player.mediaStatusChanged.connect(self.handle_media_status)
            # Handle errors
            self.music_player.error.connect( lambda error: self.add_message(f"Music error: {self.music_player.errorString()}") )
            # Set looping
            # Fallback for older PyQt5
            # self.music_player.mediaStatusChanged.connect(
                # lambda status: self.music_player.play() if status == QMediaPlayer.EndOfMedia and not self.is_music_muted else None
            # )
        self.is_music_muted = False
        if os.path.exists(music_path):
            self.music_player.setMedia(QMediaContent(QUrl.fromLocalFile(music_path)))
        else:
            self.add_message(f"Music file {music_path} not found")
            print(f"Music file {music_path} not found")
    def load_random_music(self):
        if self.is_music_muted: return None
        return self.load_music( self.get_random_music_filename() )
    def handle_media_status(self, status):
        """Handle media status changes to start playback when loaded."""
        match status:
            case QMediaPlayer.LoadingMedia:
                # 1. Prevent Multiple Calls on loading 
                return 
            case QMediaPlayer.InvalidMedia:
                self.add_message("Music failed: Invalid media")
                print("Music failed: Invalid media")
                return 
            case QMediaPlayer.EndOfMedia:
                if not self.is_music_muted:
                    self.load_random_music()
                    print("Random Music Selected")
                    return 
            case QMediaPlayer.LoadedMedia:
                if not self.is_music_muted:
                    self.music_player.play()
                    print("Music started: Media loaded")
                    return 
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

# [ Game_VIEWPORT.draw ] { Game_VIEWPORT }
# -> Game_VIEWPORT.draw() || .draw_grid() | .draw_hud()
# -> Game_VIEWPORT.draw() || .draw_grid() || { .get_tiles_to_draw() | get_anchor() | .rotate_vector_for_camera() | .is_ingrid() | .is_inview() }
class Game_VIEWPORT:
    def __init__(self):
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.scene.setBackgroundBrush(QBrush(QColor(0, 0, 0)))
        # -- 
        self.rotation = 0  # degrees: 0, 90, 180, 270
        self.grid_width = MAP_WIDTH
        self.grid_height = MAP_HEIGHT
        self.view_width = VIEW_WIDTH_IN_TILES
        self.view_height = VIEW_HEIGHT_IN_TILES
        self.tile_size = TILE_SIZE 
        # -- 
        self.dirty_tiles = set()  # Track tiles that need redrawing
        self.tile_items = {}  # For optimized rendering
        # --
        self.flag_is_animating = False
        # -- 
        Tile._load_sprites()
    def draw(self):
        self.draw_grid()
        self.draw_hud()
    def get_tiles_to_draw(self):
        safety_draw_dy = 1
        # view range : controls the tiles to draw 
        # view measures : the size of viewport 
        if not self.dirty_tiles: return [(x, y) for y in range(self.grid_height) for x in range(self.grid_width)]
        # -- 
        tiles_to_draw = set(self.dirty_tiles)  # Start with dirty tiles (includes MoveEvent old positions)
        px, py = self.player.x, self.player.y
        view_range_x = range(-self.view_width // 2, self.view_width // 2 + 1)  # -3 to 3
        view_range_y = range(-self.view_height // 2 - 1 - safety_draw_dy , self.view_height // 2)  # -4 to 2, adjusted for anchor
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
                if self.is_ingrid(x,y): tiles_to_draw.add((x, y))
        return list(tiles_to_draw)
    def is_ingrid(self,x,y):
        return (0 <= x < self.grid_width and 0 <= y < self.grid_height)
    def is_inview(self,x,y):
        return (0 <= x < self.view_width * self.tile_size and 0 <= y < self.view_height * self.tile_size)
    def get_anchor(self):
        return (self.view_width // 2) * self.tile_size, (self.view_height - 2) * self.tile_size
    def draw_next_frame(self):
        if self.animation_index > len(self.animation_positions):
            self.animation_timer.stop()
            self.draw()
            self.flag_is_animating = False  # <<< UNBLOCK INPUT
            return
        ent_x, ent_y = None, None     
        if self.animation_index != len(self.animation_positions):
            ent_x, ent_y = self.animation_positions[self.animation_index]
        self.scene.clear()
        px, py = self.player.x, self.player.y
        anchor_screen_x, anchor_screen_y = self.get_anchor()
        tiles_to_draw = self.get_tiles_to_draw()
        for x, y in tiles_to_draw:
            dx, dy = x - px, y - py
            rx, ry = self.rotate_vector_for_camera(dx, dy)
            screen_x = anchor_screen_x + (rx) * self.tile_size
            screen_y = anchor_screen_y + (ry) * self.tile_size
            if self.is_ingrid(x, y) and self.is_inview(screen_x, screen_y):
                tile = self.map.get_tile(x, y)
                if tile:
                    if ent_x == x and ent_y == y:
                        tile.draw( self.scene, screen_x, screen_y, extra_pixmap = Tile.get_rotated_sprite(key = self.animation_sprite_key, rotation=self.animation_sprite_rotation), game_instance = self )
                    else:
                        tile.draw( self.scene, screen_x, screen_y, game_instance = self)
        self.scene.setSceneRect(0, 0, self.view_width * self.tile_size, self.view_height * self.tile_size)
        self.animation_index += 1
    def _get_diff(self, v2, v1): #  v2 - v1
        return (v2[0]-v1[0], v2[1]-v1[1])
    def draw_animation_on_grid(self, sprite_key, positions):
        if not positions: return
        self.flag_is_animating = True  # <<< BLOCK INPUT
        self.animation_index = 0
        self.animation_positions = positions
        self.animation_sprite_rotation = 0
        if len(positions)>1:
            self.animation_sprite_rotation = self.player._signed_angle( self._get_diff(positions[1], positions[0]), self.player.get_forward_direction() )
        self.animation_sprite_key = sprite_key
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.draw_next_frame)
        self.animation_timer.start(15)  # 1000ms = 1s per frame
    def draw_grid(self):
        self.scene.clear()
        tiles_to_draw = self.get_tiles_to_draw()
        # -- 
        px, py = self.player.x, self.player.y
        anchor_screen_x, anchor_screen_y = self.get_anchor()
        for x, y in tiles_to_draw:
            dx, dy = x - px, y - py
            rx, ry = self.rotate_vector_for_camera(dx, dy)
            screen_x = anchor_screen_x + (rx) * self.tile_size
            screen_y = anchor_screen_y + (ry) * self.tile_size
            if self.is_ingrid(x,y) and self.is_inview(screen_x, screen_y):
                tile = self.map.get_tile(x, y)
                if tile: tile.draw(self.scene, screen_x, screen_y, game_instance = self)
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
        # position label 
        pos_label = QGraphicsTextItem(f"{self.player.x}, {self.map.height - self.player.y}")
        pos_label.setDefaultTextColor(QColor("yellow"))  # White text
        pos_label_width = pos_label.boundingRect().width()
        pos_label.setPos(self.view_width*self.tile_size- pos_label_width - 10, 10)
        pos_label.setZValue(10) 
        self.scene.addItem(pos_label)
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
        # primary hand item 
        if self.player: 
            primary = self.player.primary_hand
            secondary = self.player.secondary_hand
            wp_img_scale = int(math.floor( TILE_SIZE/1.5 ))
            if primary:
                pr_graphics_pixmap = QGraphicsPixmapItem(primary.get_sprite().scaled(wp_img_scale, wp_img_scale, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                pr_graphics_pixmap.setPos( (self.view_width-1)*TILE_SIZE, (self.view_height-1)*TILE_SIZE )
                self.scene.addItem(pr_graphics_pixmap)
            if secondary:
                sc_graphics_pixmap = QGraphicsPixmapItem( secondary.get_sprite().scaled(wp_img_scale, wp_img_scale, Qt.KeepAspectRatio, Qt.SmoothTransformation) )
                sc_graphics_pixmap.setPos( TILE_SIZE-wp_img_scale, (self.view_height-1)*TILE_SIZE )
                self.scene.addItem(sc_graphics_pixmap)
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
class Game_PLAYERS:
    def __init__(self):
        self.turn = 0
        self.current_day = 0
        self.turns_per_day = 1000
        self.low_hp_triggered = False  # Flag for low HP event
        self.low_hunger_triggered = False  # Flag for low hunger event
        self.last_encounter_description = ""
        self.certificates = []
        self.player = None 
        self.current_player = None 
        self.players = {} 
        self.backup_players = [] 
        self.prior_next_index = 0
        self.prior_next_players = []
    def check_player_dict(self):
        for k in self.players:
            v = self.players.get(k,None)
            if not (v is None): continue 
            print("Character Vanished from Dictionary! Restoring from Emergency List")
            for char in self.backup_players: 
                if k == char.name: 
                    self.players.update({k:char}) 
                    break 
    def add_player(self, key, cls_constructor = Player,**kwargs): # add a player or ally in dictionary 
        obj = cls_constructor(**kwargs)
        self.players.update({ key : obj })
        self.backup_players.append(obj)
        self.update_prior_next_selection()
        return obj 
    def add_hero(self, key, **kwargs):
        obj = Hero(**kwargs)
        self.players.update({ key : obj })
        self.backup_players.append(obj)
        self.update_prior_next_selection()
        return obj 
    def set_player(self, name): # set the Game.player by dictionary name  
        """ return True if successfully set the current player, False otherwise """ 
        if not name in self.players: return False 
        new_player = self.players[name]
        self.player = new_player
        self.current_player = name 
        self.player.party = False
        self.update_inv_window()
        if self.behaviour_controller_window: self.behaviour_controller_window.update()
        if self.journal_window: 
            self.journal_window.load_journal()
            self.journal_window.update_char_button_images()
        self.player.rotation = self.rotation 
        return True 
    def set_player_name(self,key,new_name):
        player = self.players.get(key,None)
        if not player: return False
        self.players.pop(key)
        player.name = new_name 
        self.players.update({new_name:player})
        return True
    def place_players(self):
        for k,v in self.players.items():
            if v is self.player: continue
            if v.party: continue 
            if v.current_map != self.current_map: continue 
            self.map.place_character(v)
        return self.map.place_character(self.player)
    def remove_player(self, key = None):
        if not key: key = self.current_player
        if len(self.players) <= 1: 
            self.add_message("Must have at least one adventurer ...")
            return 
        def filter_candidates(k, v): # -- bug fix -- Fail to Garrison Player
            if k == key: return False 
            if v.party == True: return False 
            if v.current_map != self.current_map: return False 
            return True
        candidates = [ k for k,v in self.players.items() if filter_candidates(k,v) ]
        if len(candidates)==0: 
            self.add_message("Must have at least one adventurer ...")
            return 
        if not key in self.players:
            print(f"Warning : {key} not in game.players")
            return 
        char_to_remove = self.players[key]
        self.map.remove_character(char_to_remove)
        self.players.pop(key)
        self.backup_players.remove(char_to_remove) 
        if not char_to_remove is self.player: 
            self.update_prior_next_selection()
            return 
        new_key_name = random.choice(candidates)
        print("New Character Selection :", new_key_name)
        if not new_key_name: 
            self.update_prior_next_selection()
            return 
        self.set_player(new_key_name)
        self.update_prior_next_selection()
    def update_prior_next_selection(self):
        if self.journal_window: self.journal_window.update_journal()
        if self.player is None:
            print("Bad Timing to Call .update_prior_next_selection() the current player is None")
            self.prior_next_players = []
            return 
        def ply_filter(value):
            if value is None: return False 
            if not isinstance(value, Player): return False 
            if value.party: return False
            if value.current_map != self.current_map: return False
            if value is self.player: return False 
            if not value.is_placed_on_map(self.map): return False 
            if value.distance(self.player) > 20: return False 
            return True
        self.prior_next_index = 0
        try:
            self.prior_next_players = [self.player.name]+[ key for key,value in self.players.items() if ply_filter(value) ]
        except Exception as e:
            print(e)
            self.prior_next_players = []
    def move_party(self):
        for k,v in self.players.items():
            if v is self.player: 
                print(" - ",v.name, v.current_map)
                continue 
            if not v.party: 
                print(" - ",v.name, v.current_map)
                continue 
            v.current_map = self.current_map
            print(v.name, v.current_map) # debug 
        self.update_prior_next_selection() # -- bug fix -- Carring Players that isn't on current map using pageup and down
    def release_party(self, diff_moves = CROSS_DIFF_MOVES_1x1):
        print("releasing everyone from party")
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
    def release_hero_party(self):
        if not isinstance(self.player, Hero): return 
        self.player.release_party(self)
        self.update_prior_next_selection()
    def count_party(self):
        if isinstance(self.player, Hero):
            return self.player.count_party()
        S = 0
        for i in self.players:
            if self.players[i].party == True:
                S += 1
        return S
    def can_select_player(self, player_obj):
        return player_obj.current_map == self.player.current_map and not player_obj.party 
class Game_MAPTRANSITION:
    def __init__(self):
        self.current_map = (0,0,0) # Current map coordinates
        self.map = Map()
        self.maps = {(0,0,0):self.map}  # Store Map objects with coordinate keys
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
            going_up = up,
            b_generate = True
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
        if len(self.map.enemies) < 10: self.map.fill_enemies(num_enemies=50)
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
        self.place_players() # testing
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
        # -- 
        self.place_players() # testing
        # Update of Game Scene 
        self.scene.clear()
        self.dirty_tiles.clear()
        self.draw_grid()
        self.draw_hud()
        toc(T1,"Game.vertical_map_transition() ||")
class Game_DATA:
    def __init__(self):
        self.current_slot = 1  # Track current save slot
    def from_dict(self, dictionary):
        if not super().from_dict(dictionary):
            return False
        if self.current_map in self.maps and self.player:
            self.maps[self.current_map].place_character(self.player)
        return True
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
        self.add_hero(new_character_name, name = new_character_name, hp = 100, x=xy[0], y=xy[1], b_generate_items=True)
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
        # self.journal_window.clear_text()
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
        self.check_player_dict()
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
class Game_GUI:
    def __init__(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFocusPolicy(Qt.StrongFocus)  # Ensure Game accepts focus
        self.setWindowTitle("PyQt Rogue Like")
        self.setFixedSize(self.view_width * self.tile_size, self.view_height * self.tile_size)
        # --
        self.party_window = None 
        self.behaviour_controller_window = None 
        self.inventory_window = None  # Initialize later on demand
        # Initialize message window
        self.message_popup = MessagePopup(self)  # Set Game as parent
        self.messages = []  # List of (message, turns_remaining) tuples
        # Add journal window
        self.journal_window = None
        # Initialize music player
        self.music_player = None
        self.load_random_music()
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
    def update_all_gui(self):
        self.update_inv_window()
        self.update_journal_window()
        self.update_behav_window()
        self.update_party_window()
    def update_party_window(self):
        if self.party_window:
            if self.party_window.isVisible():
                self.party_window.update()
    def update_inv_window(self):
        if self.inventory_window: 
            if self.inventory_window.isVisible():
                self.inventory_window.update_inventory(self.player)
                self.setFocus()
    def update_journal_window(self):
        if self.journal_window:
            self.journal_window.save_journal()
            if self.journal_window.isVisible():
                self.journal_window.load_journal(self.current_slot)
                # self.journal_window.update_position() 
    def update_behav_window(self):
        if self.behaviour_controller_window:
            if self.behaviour_controller_window.isVisible():
                self.behaviour_controller_window.update()
    def take_note_on_diary(self):
        if not self.journal_window:
            self.journal_window = JournalWindow(self) 
        if self.journal_window.isVisible():
            self.journal_window.log_quick_diary_entry()
        else:
            self.journal_window.load_journal(self.current_slot)  # Refresh contents
            self.journal_window.log_quick_diary_entry()
            self.journal_window.show()
            # self.journal_window.update_position()
        self.journal_window.save_journal()
        self.setFocus()
class Game_ITERATION:
    def __init__(self):
        self.events = []  # Initialize events list
        # -- message flags || 100 turns 
        self.flag_near_to_village = False 
        self.flag_performance_players = False 
        self.flag_performance_enemies = False 
        self.flag_performance_buldings = False 
    def game_iteration_not_draw(self):
        prev_hp = self.player.hp 
        # -- 
        self.turn += 1
        
        largest_dt = 0
        culprit = ""
        t = 0
        
        t1 = tic()
        self.Event_NewTurn()
        dt1, txt1 = toc(t1, "Game.Event_NewTurn()")
        t += dt1
        
        if dt1 > largest_dt:
            largest_dt = dt1
            culprit = txt1
        
        t2 = tic()
        self.process_events() 
        dt2, txt2 = toc(t2, "Game.process_events()")
        t += dt2
        
        if dt2 > largest_dt:
            largest_dt = dt2
            culprit = txt2
        
        t3 = tic()
        self.update_players() # which include player and allies 
        dt3, txt3 = toc(t3, "Game.update_players()")
        t += dt3
        
        if dt3 > largest_dt:
            largest_dt = dt3
            culprit = txt3
        
        t4 = tic()
        self.update_enemies()
        dt4, txt4 = toc(t4, "Game.update_enemies()")
        t += dt4
        
        if dt4 > largest_dt:
            largest_dt = dt4
            culprit = txt4
        
        t5 = tic()
        self.update_buildings()
        dt5, txt5 = toc(t5, "Game.update_buildings()")
        t += dt5
        
        if dt5 > largest_dt:
            largest_dt = dt5
            culprit = txt5
        
        t6 = tic()
        self.update_messages() # Critical: Update message window 
        dt6, txt6 = toc(t6, "Game.update_messages()")
        t += dt6
        
        if dt6 > largest_dt:
            largest_dt = dt6
            culprit = txt6
        
        # print(f"{culprit} : {100.0*largest_dt/t:.1f} %")
        
        return ( self.player.hp < prev_hp )
    def game_iteration(self):
        """ return True if losing hp """
        prev_hp = self.player.hp 
        # -- 
        self.turn += 1
        self.Event_NewTurn()
        self.process_events() 
        self.update_players() # which include player and allies 
        self.update_enemies()
        self.update_buildings()
        self.update_messages() # Critical: Update message window 
        self.draw()
        return ( self.player.hp < prev_hp )
    def process_events(self): # delayed events 
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
            elif isinstance(event, UseItemEvent):
                if event.item.use(event.character):
                    if hasattr(event.item,"uses"):
                        self.add_message(f"{event.item.name} used")
                        if event.item.uses <= 0:
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
        t_1 = tic()
        T = 0
        t = t_1
        player = self.player 
        self.flag_performance_players = False 
        flag_performance = self.flag_performance_players or self.flag_performance_enemies or self.flag_performance_buldings
        for k,v in self.players.items():
            if T>PERFORMANCE_TIME or flag_performance: 
                if T>PERFORMANCE_TIME: self.flag_performance_players = True 
                if player.distance(v) > PERFORMANCE_DISTANCE: continue 
            if v is player: continue 
            if v.party:
                if v.is_placed_on_map(self.map):
                    self.map.remove_character(v)
                continue 
            v.behaviour_update(self)
            dt = toc(t)[0] 
            t += dt 
            T += dt 
        if self.flag_performance_players: print("performance mode: update_players()")     
        toc(t_1, "game.update_players() ||")
    def update_enemies(self): # maybe more maps could be updated, like maps with alive players 
        self.map.update_enemies(self)
    def update_buildings(self):
        t_1 = tic()
        T = 0
        t = t_1
        player = self.player 
        self.flag_performance_buldings = False 
        flag_performance = self.flag_performance_players or self.flag_performance_enemies or self.flag_performance_buldings
        for b in self.map.buildings:
            if T>PERFORMANCE_TIME or flag_performance: 
                if T>PERFORMANCE_TIME: self.flag_performance_buldings = True 
                if player.distance(b) > PERFORMANCE_DISTANCE: continue 
            b.update(self)
            dt = toc(t)[0] 
            t += dt 
            T += dt 
        if self.flag_performance_buldings: print("performance mode: update_buildings()") 
        toc(t_1, "game.update_buildings() ||")    
    def Event_NewTurn(self):
        if self.turn // self.turns_per_day + 1 > self.current_day:
            self.current_day += 1
            self.Event_NewDay()
        if self.turn % 5 == 0: # refresh some variables 
            self.last_encounter_description = ""
            if self.journal_window: self.journal_window.update_char_button_images()
        if self.turn % 100 == 0:
            self.Event_Every_100_Turns()
    def Event_Every_100_Turns(self):
        self.add_message(f"Day : {self.current_day} Turn : {self.turn}")
        if self.flag_near_to_village:
            self.add_message(f"I'm close to a village ... I should check it out")
            self.flag_near_to_village = False 
        self.player.update_available_skills()
    def Event_NewDay(self):
        print(f"Day {self.current_day}")
        if len(self.players)>7:
            if self.map.generate_raiders_spawn(self, probability = 1.0): self.add_message("beware, I feel a bad omen ...")
        else:
            if self.map.generate_raiders_spawn(self, probability = RAIDER_SPAWN_PROBABILITY): self.add_message("beware, I feel a bad omen ...")
        for k,v in self.players.items():
            if not v: continue 
            if not v.is_placed_on_map(self.map): continue 
            if not self.can_select_player(v): continue 
            v.days_survived += 1
        if self.current_day == 5:
            self.journal_window.append_text("(Skill - 5 days) I'm in full shape now, I'm feeling agile, use Ctrl to dodge and move two tiles backward ...") 
        if self.current_day == 20:
            self.journal_window.append_text("(Skill - 20 days) My body remembered how to use a sword properly, now I can perform deadly blows with F key. Whenever the enemy stay in L position like a knight chess I can swing my sword hit taking him off-guard ...") 
        if self.current_day == 30:
            self.journal_window.append_text("(Skill - 30 days) Now I'm proficient with many weapons, I can use special moves ...") 
    def Event_PlayerDeath(self):
        # SANITY COMMENTS
        # 1. If there is other characters on the map or on the party you still can load the save if you don't change the map. 
        # 2. Travelling Alone will result in losing the Character on Death, you can't load the game. 
        # 3. If you change the map before you load you will lose the character, because the game saves on map transition. 
        
        # DSL Logic 
        # 1. Player Death () || Release Party | Drop on Death | Remove the Character | % Has Other Characters on the Map | % else 
        # -> Player Death () || ... | % Has Other Characters on the Map || Take Control of Next Character on the Map 
        # -> Player Death () || ... | % Has Other Characters on the Map | % else || Start New Game and Saves  
        
        print("you died!")
        if isinstance(self.player, Hero): # only heroes can have a party 
            self.player.release_party(self)
        # self.release_party(SQUARE_DIFF_MOVES_5x5)
        self.player.drop_on_death()
        if self.player.name in self.players.keys():
            print("Removing :",self.player.name)
            self.players.pop(self.player.name)
        self.map.remove_character(self.player)
        # -- 
        b_new_char_set = False
        if len(self.players) > 0: # Has Other Characters on the Map
            for k,v in self.players.items():
                # take control of the first valid character 
                if k and v and isinstance(v, Player):
                    if self.set_player(v.name):
                        self.draw()
                        b_new_char_set = True
                        break 
        if not b_new_char_set:
            self.add_message("You died, starting new game")
            self.start_new_game(new_character_name = self.current_player, b_clear_players = False)
            self.save_current_game(slot = self.current_slot)
        self.update_prior_next_selection()
    def Event_DoAttack(self, event):
        if event.target.receive_damage(event.attacker, event.damage):
            if event.target is self.player: self.add_message("You parried the incoming attack.")
        else:
            if event.target is self.player: self.add_message("The enemy hits you ...")
        if hasattr(event.target, "description"): self.last_encounter_description = getattr(event.target,"description")
        if event.target is self.player: # player being attacked
            self.last_encounter_description = getattr(event.attacker,"description")
        elif self.player is event.attacker: # player attack            
            self.add_message(f"{event.attacker.name} deals {event.damage:.1f} damage to {event.target.name}")
            self.player.weapons_stats_update()
            self.update_inv_window()
        if event.target.hp <= 0: # in case of death 
            self.Event_CharacterDeath(event)
    def Event_CharacterDeath(self, event):
        if event.target is self.player:
            self.Event_PlayerDeath()
        else:
            event.target.drop_on_death()
            if event.target.name in self.players:
                print("Removing :",event.target.name)
                self.remove_player(event.target.name)
                return 
            self.map.remove_character(event.target)
    def Event_OnLeftMouseClickView(self, x, y):
        if x is None: return 
        if y is None: return 
        view_tile_x, view_tile_y = vec.to_integer_vector( vec.scalar_multiply(1.0/TILE_SIZE, (x,y)) )
        if view_tile_x is None or view_tile_y is None: return 
        view_diff = self.get_mouse_move_diff()
        if not view_diff: return 
        map_diff = self.rotated_direction( *view_diff )
        if not map_diff: return 
        player = self.player
        if not player: return
        map_tile_x = player.x + map_diff[0] 
        map_tile_y = player.y + map_diff[1] 
        # 1. x, y ; mouse coordinates in pixels relative to top-left corner of viewport 
        # 2. view_tile_ ; coordinates in tile size units relative to top-left corner of viewport 
        # 3. map_tile_ ; coordinate of respective tile in map grid  
        # 4. view_diff ; integer difference vector from player anchor point relative to viewport
        # 5. map_diff ; integer difference vector from player anchor point relative to map grid 
        map = self.map 
        if not map: return 
        tile = map.get_tile(map_tile_x, map_tile_y) 
        char = map.get_char(map_tile_x, map_tile_y) 
        
class DraggableView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_pos = None
        self.mouse_x = None 
        self.mouse_y = None
    def mousePressEvent(self, event):
        local_pos = event.pos() # QPoint
        self.mouse_x = local_pos.x()
        self.mouse_y = local_pos.y()
        # -- 
        if event.button() == Qt.RightButton:
            self._drag_pos = event.globalPos() - self.window().frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.RightButton:
            self.window().move(event.globalPos() - self._drag_pos)
            self.window_x = self.pos().x()
            self.window_y = self.pos().y()
            event.accept()
        else:
            super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)
            
# Main Window Class 
class Game(DraggableView, Serializable, Game_VIEWPORT, Game_SOUNDMANAGER, Game_PLAYERS, Game_MAPTRANSITION, Game_DATA, Game_GUI, Game_ITERATION):
    __serialize_only__ = [
        "version",
        "rotation",
        "players",
        "current_map", # map coords
        "turn",
        "current_slot",
        "current_day",
        "is_music_muted",
        "current_player",
        "certificates",
        "window_x",
        "window_y"
    ]
    def __init__(self):
        DraggableView.__init__(self)
        self.setFocusPolicy(Qt.StrongFocus) 
        #print(Game.__mro__)
        Serializable.__init__(self)
        Game_VIEWPORT.__init__(self)
        Game_SOUNDMANAGER.__init__(self)
        Game_PLAYERS.__init__(self)
        Game_MAPTRANSITION.__init__(self)
        Game_DATA.__init__(self)
        Game_GUI.__init__(self)
        Game_ITERATION.__init__(self)
        self.window_x = 0
        self.window_y = 0
        self.alt_pressed = False
        self.version = "1.0.0"
        self.load_current_game()
        if self.window_x and self.window_y: self.move(self.window_x, self.window_y)
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            x, y = self.mouse_map_pos()
            _tile = self.map.get_tile(x, y)
            if _tile: 
                _char = _tile.current_char 
                if _char and not _char is self.player:
                    key = _char.name
                    if key in self.players and self.can_select_player(_char):
                        self.set_player(key) # ?
                        self.draw()
                        self.update_all_gui()
                        return 
                if self.player and self.player.distance(_tile) < 1 and _tile.items:
                    self.events.append(PickupEvent(self.player, _tile))
                    self.dirty_tiles.add((self.player.x, self.player.y))  # Redraw tile
                    self.game_iteration()
                    self.update_inv_window()
        super().mouseDoubleClickEvent(event)  # optional: propagate the event if needed    
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
    def key_press_move_app_window(self, key):
        """ return True means that the keyPressEvent should return imediatly """
        if True: return False # disable for now 
        if key == Qt.Key_Alt and not self.alt_pressed: self.alt_pressed = True
        if self.alt_pressed:
            if key == Qt.Key_Left:
                self.move(self.x() - 10, self.y())
                return True
            elif key == Qt.Key_Right:
                self.move(self.x() + 10, self.y())
                return True
            elif key == Qt.Key_Up:
                self.move(self.x(), self.y() - 10)
                return True 
            elif key == Qt.Key_Down:
                self.move(self.x(), self.y() + 10)
                return True 
        return False 
    def key_press_cycle_between_playables(self, key):
        """ return True means that the keyPressEvent should return imediatly """
        if key == Qt.Key_PageUp: # cycle between playables
            # if self.count_party() > 0: 
                # self.add_message("Release Party to Change Character")
                # return True 
            if len(self.prior_next_players) <= 1:
                self.update_prior_next_selection()
            if len(self.prior_next_players) > 0:
                if self.prior_next_index>0:
                    self.prior_next_index -= 1 
                else:
                    self.prior_next_index = len(self.prior_next_players)-1
                self.set_player( self.prior_next_players[self.prior_next_index] )
                self.update_inv_window()
                self.draw()
            return True 
        elif key == Qt.Key_PageDown: # cycle between playables
            # if self.count_party() > 0: 
                # self.add_message("Release Party to Change Character")
                # return True 
            if len(self.prior_next_players) <= 1:
                self.update_prior_next_selection()
            if len(self.prior_next_players) > 0:
                if self.prior_next_index<len(self.prior_next_players)-1:
                    self.prior_next_index += 1 
                else:
                    self.prior_next_index = 0
                self.set_player( self.prior_next_players[self.prior_next_index] )
                self.update_inv_window()
                self.draw() 
            return True             
        return False 
    def key_press_choose_weapon_menu(self, key):
        """ return True means that the keyPressEvent should return imediatly """
        #list_of_weapons = [ [wp, f"{wp.name} {wp.damage:.1f} [dmg]"] for wp in self.player.items if isinstance(wp, Weapon) ]
        list_of_weapons = [ [wp, wp.info() ] for wp in self.player.items if isinstance(wp, Weapon) ]
        if key == Qt.Key_1:
            if self.player.primary_hand and hasattr(self.player.primary_hand, "info"):
                SB = SelectionBox( 
                    parent=self, 
                    item_list = ["[ Weapon Selection ]", f"-> primary: {self.player.primary_hand.info()}" ]+[ i[1] for i in list_of_weapons ]+["Exit"], 
                    action = primary_menu, 
                    game_instance = self, 
                    list_of_weapons = list_of_weapons,
                    slot = "primary_hand"
                )
            else:
                SB = SelectionBox( parent=self, item_list = ["[ Weapon Selection ]"]+[ i[1] for i in list_of_weapons ]+["Exit"], action = primary_menu, game_instance = self, list_of_weapons = list_of_weapons, slot = "primary_hand" )
            SB.show()
            return True 
        elif key == Qt.Key_2: # TODO : should include shields too 
            if self.player.secondary_hand and hasattr(self.player.secondary_hand, "info"):
                SB = SelectionBox( 
                    parent=self, 
                    item_list = ["[ Weapon Selection ]", f"-> secondary: {self.player.secondary_hand.info()}" ]+[ i[1] for i in list_of_weapons ]+["Exit"], 
                    action = primary_menu, 
                    game_instance = self, 
                    list_of_weapons = list_of_weapons,
                    slot = "secondary_hand"
                )
            else:
                SB = SelectionBox( parent=self, item_list = ["[ Weapon Selection ]"]+[ i[1] for i in list_of_weapons ]+["Exit"], action = primary_menu, game_instance = self, list_of_weapons = list_of_weapons, slot = "secondary_hand" )
            SB.show()   
            return True 
        return False 
    def key_press_gui(self, key):
        stamina_bound = 20 
        match key: # selection box menus 
            case Qt.Key_B: # build menu 
                SelectionBox(parent = self, item_list = [ "[ Certificates ]" ]+self.certificates+["Exit"], action = build_menu, game_instance = self ).show()
                return True 
            case Qt.Key_X: # skill menu            
                SelectionBox(parent = self, item_list = [
                    f"[ Available Skills ](days survived: {self.player.days_survived})",
                    f"-> Current Map: { self.player.current_map[0]}, {-self.player.current_map[1] }, {self.player.current_map[2] }",
                    f"-> Map Position: { self.player.x}, { self.map.height -self.player.y }",
                    f"Release Party: { self.player.count_party() if isinstance(self.player, Hero) else '...' }",
                    f"Dodge Skill: { self.player.can_use_dodge_skill }",
                    f"Thrust Skill: { self.player.can_use_thrust_skill }",
                    f"Knight Slash Skill: { self.player.can_use_knight_skill }",
                    f"Tower Smash Skill: { self.player.can_use_tower_skill }",
                    "Exit"
                ], action = skill_menu, game_instance = self, stamina_bound = stamina_bound).show()
                return True 
        match key: # journal and inventory
            case Qt.Key_N: # take a quick note in journal
                self.take_note_on_diary()
                return True 
            case Qt.Key_J:  # Toggle journal window
                if not self.journal_window:
                    self.journal_window = JournalWindow(self)
                if self.journal_window.isVisible():
                    self.journal_window.save_journal()  # Save on close
                    self.journal_window.hide()
                else:
                    self.journal_window.load_journal(self.current_slot)  # Refresh contents
                    self.journal_window.update_journal()
                    self.journal_window.show()
                self.setFocus()
                return True 
            case Qt.Key_I:  # Toggle inventory window
                if not self.inventory_window:
                    self.inventory_window = InventoryWindow(self)
                if self.inventory_window.isVisible():
                    self.inventory_window.update_inventory(self.player)
                    self.inventory_window.hide()
                else:
                    self.inventory_window.update_inventory(self.player)
                    self.inventory_window.show()
                return True     
            case Qt.Key_Z: # behaviour window
                if not self.behaviour_controller_window:
                    self.behaviour_controller_window = BehaviourController(self)
                if self.behaviour_controller_window.isVisible():
                    self.behaviour_controller_window.hide()
                else:
                    self.behaviour_controller_window.update()
                    self.behaviour_controller_window.show()
            case Qt.Key_P: # party window
                if not self.party_window:
                    self.party_window = PartyWindow(self)
                if self.party_window.isVisible():
                    self.party_window.hide()
                else:
                    self.party_window.update()
                    self.party_window.show()
        match key: # music 
            case Qt.Key_M:  # Toggle music
                self.toggle_music()
                return True
            case Qt.Key_Plus:
                volume = min(self.music_player.volume() + 10, 100)
                self.music_player.setVolume(volume)
                self.add_message(f"Music volume: {volume}%")
                return True 
            case Qt.Key_Minus:
                volume = max(self.music_player.volume() - 10, 0)
                self.music_player.setVolume(volume)
                self.add_message(f"Music volume: {volume}%")
                return True
        match key: # main menu options 
            case Qt.Key_F5:
                self.save_current_game(slot=1)
                return
            case Qt.Key_F7:
                self.load_current_game(slot=1)
                return True 
            case Qt.Key_F9:    
                self.start_new_game()
                return True 
        return False 
    def player_move_diff(self, dx, dy):
        """ return True if the key press should trigger game_iteration """
        b_isForwarding = vec.compare((dx,dy), self.player.get_forward_direction(), 0.01)
        target_x, target_y = self.player.x + dx, self.player.y + dy
        if not self.is_ingrid(target_x, target_y): # if target_x <0 or target_x > self.grid_width-1 or target_y<0 or target_y> self.grid_height-1:
            self.horizontal_map_transition(target_x, target_y)
            return False 
        tile = self.map.get_tile(target_x, target_y)
        if not tile: return False 
        if tile.walkable:
            target = tile.current_char
            if target:
                if b_isForwarding and is_enemy_of(self.player, target): #not isinstance(tile.current_char, Player):
                    self.events.append(AttackEvent(self.player, target, self.player.do_damage()))
            else:
                old_x, old_y = self.player.x, self.player.y
                if self.player.move(dx, dy, self.map):
                    self.events.append(MoveEvent(self.player, old_x, old_y))
                    self.dirty_tiles.add((old_x, old_y))
                    self.dirty_tiles.add((self.player.x, self.player.y))
            return True
        return False 
    def key_press_movement(self, key):
        """ return True if the key press should trigger game_iteration """
        dx, dy = 0, 0
        b_isForwarding = False
        match key: # use, interaction 
            case Qt.Key_R: # use item 
                self.player.use_first_item_of(WeaponRepairTool, self)
                return False 
            case Qt.Key_C: # Interact with stair or special tile 
                tile = self.map.get_tile(self.player.x, self.player.y)
                if tile:
                    if tile.stair:
                        if tile.default_sprite_key == "dungeon_entrance":
                            self.vertical_map_transition(tile.stair, False)
                        else:
                            self.vertical_map_transition(tile.stair, tile.default_sprite_key == "stair_up")
                        return False 
                    elif isinstance(tile, TileBuilding):
                        if tile.b_enemy: return False 
                        SB = SelectionBox( tile.menu_list, action = tile.action(), parent = self, game_instance = self )
                        tile.update_menu_list(SB)
                        SB.show()
                        return False 
                px, py = self.player.get_forward_direction()
                tile2 = self.map.get_tile(self.player.x+px, self.player.y+py)
                if tile2:
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
                        return False 
                return False 
            case Qt.Key_E: # Use first food item
                self.player.use_first_item_of(Food, self)
                return False 
            case Qt.Key_G: # Pickup items
                tile = self.map.get_tile(self.player.x, self.player.y)
                if tile and tile.items:
                    self.events.append(PickupEvent(self.player, tile))
                    self.dirty_tiles.add((self.player.x, self.player.y))  # Redraw tile
                    self.game_iteration()
                self.update_inv_window()
                return False 
        match key: # rotation
            case Qt.Key_Left:
                self.rotation = (self.rotation - 90) % 360
                self.player.rotation = self.rotation 
                return True
            case Qt.Key_Right:
                self.rotation = (self.rotation + 90) % 360
                self.player.rotation = self.rotation             
                return True   
        # -- $ dx, dy
        if key in (Qt.Key_Up, Qt.Key_W):
            dx, dy = self.rotated_direction(0, -1)
            b_isForwarding = True
        elif key in (Qt.Key_Down, Qt.Key_S):
            dx, dy = self.rotated_direction(0, 1)
        elif key == Qt.Key_A:
            dx, dy = self.rotated_direction(-1, 0)
        elif key == Qt.Key_D:
            dx, dy = self.rotated_direction(1, 0)
        elif key == Qt.Key_H:
            # self.save_current_game(slot=1)
            for i in range(H_REST_TURNS): 
                if self.game_iteration_not_draw(): 
                    self.add_message(f"Rested {i} turns, you've being interrupted !!!")
                    self.draw() 
                    return False 
            self.add_message(f"Rested {H_REST_TURNS} turns")        
            self.draw() 
            return False
        elif key == Qt.Key_Space:
            return True
        
        # -- $ dx, dy | process movement 
        if dx or dy: 
            if self.player_move_diff(dx,dy)==True: return True 
        return False 
    def mouse_map_pos(self):
        _diff = self.get_mouse_move_diff()
        dx, dy = self.rotated_direction( *_diff )
        x = self.player.x + dx 
        y = self.player.y + dy 
        return x, y 
    def mouse_press_interaction(self):
        """ return True if a action is selected in the conditional net, else if need further processing. """
        _diff = self.get_mouse_move_diff()
        dx, dy = self.rotated_direction( *_diff )
        _mag = vec.magnitude( (dx, dy) )
        if dx is None or dy is None: return False 
        x = self.player.x + dx 
        y = self.player.y + dy 
        _tile = self.map.get_tile(x, y)
        if not _tile: return False 
        _char = _tile.current_char 
        if _mag > 1: return False 
        # -- other playable character 
        if isinstance(_char, Player) and _mag > 0:
            SB = SelectionBox( [
                f"[ {_char.name} ]",
                "Add to Party",
                "items+",
                "items-",
                "Exit"
            ], action = player_menu, parent = self, game_instance = self, npc = _char )
            SB.show()
            return True 
        # -- tile building 
        if isinstance(_tile, TileBuilding) and _mag == 0:
            if _tile.b_enemy: return False 
            SB = SelectionBox( _tile.menu_list, action = _tile.action(), parent = self, game_instance = self )
            _tile.update_menu_list(SB)
            SB.show()
            return True 
        return False  
    def mouse_press_movement(self):
        if self.flag_is_animating: return False 
        _diff = self.get_mouse_move_diff()
        dx, dy = self.rotated_direction( *_diff )
        if vec.magnitude((dx,dy)) == 1: 
            if self.player_move_diff(dx,dy): return True 
        elif vec.compare( _diff, (-1,1), 0.01 ): # left rotation
            self.rotation = (self.rotation - 90) % 360
            self.player.rotation = self.rotation 
            return True
        elif vec.compare( _diff, (1,1), 0.01 ): # right rotation 
            self.rotation = (self.rotation + 90) % 360
            self.player.rotation = self.rotation             
            return True    
        return False
    def key_press_skills(self, key):
        primary = self.player.primary_hand
        match key:
            case Qt.Key_Control: # dodge
                if self.player.can_use_dodge_skill:
                    self.player.dodge_skill(self)
                else:
                    self.journal_window.append_text("With ctrl you activate de dodge skill and move 2 tiles backward, in order to use the dodge skill you must survive at least 5 days ...")
                    self.add_message("I don't feel well enough to exercise ... maybe tomorrow I'll feel better.")
                return True     
            case Qt.Key_End: # weapon special skill 
                if isinstance(primary, SpecialSkillWeapon):
                    primary.use_special_End(self.player, self)
                return True
            case Qt.Key_F: # weapon special skill 
                if isinstance(self.player, Healer):
                    dx, dy = self.player.get_forward_direction()
                    x = self.player.x + dx 
                    y = self.player.y + dy
                    target = self.map.get_char(x, y)
                    if target:
                        if self.player.heal_skill(target, self):
                            self.game_iteration()
                            return True 
                if isinstance(primary, SpecialSkillWeapon):
                    self.add_message("Using Special Weapon Skill ...")
                    primary.use_special_F(self.player, self)
                return True 
        return False 
    def keyPressEvent(self, event):
        if self.flag_is_animating: return 
        key = event.key()        
        match key:
            case Qt.Key_Escape: # main menu
                SelectionBox( parent=self, item_list = [
                    f"[ Main Menu ]", 
                    f"-> Current Save Slot: {self.current_slot}",
                    f"-> Character: {self.current_player}",
                    "Resume",
                    "Start New Game",
                    "Character Settings >",
                    "Load Game >", 
                    "Save Game >", 
                    "Quit to Desktop"
                ], action = main_menu, game_instance = self).show()
                return 
            case Qt.Key_F12: # debug menu
                SelectionBox(parent=self, item_list = [
                    "[ DEBUG MENU ]",
                    "Test Animation", 
                    "Display Players Info >",
                    "Set Day 100", 
                    "Add Item >", 
                    "Generate Enemies >", 
                    "Restore Status",
                    "Generate Dungeon Entrance", 
                    "Add a Cosmetic Layer >",
                    "Exit"
                ], action = debugging_menu, game_instance = self).show()
                return 
            case Qt.Key_F11:
                pass 
        if self.key_press_move_app_window(key): return 
        if self.key_press_cycle_between_playables(key): return 
        if self.key_press_choose_weapon_menu(key): return 
        if self.key_press_skills(key): return 
        if self.key_press_gui(key): return 
        if self.key_press_movement(key): # put that function always on the end 
            self.game_iteration()
            return 
    def get_mouse_move_diff(self):
        _diff = vec.subtract( (self.mouse_x, self.mouse_y) , self.get_anchor() )
        _diff = vec.scalar_multiply(1/TILE_SIZE, _diff)
        _diff = vec.to_integer_vector(_diff)
        return _diff 
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton: 
            self.Event_OnLeftMouseClickView(self.mouse_x, self.mouse_y)
            if self.mouse_press_movement():
                self.game_iteration()
                return 
        if self.mouse_press_interaction(): return 
        return super().mouseReleaseEvent(event)

# --- END 