# items living mapping 

# project
from events import * 
from serialization import * 

# built-in
import random
import math
import json 
import os 
import tempfile
import shutil
from heapq import heappush, heappop

# third-party 
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtWidgets import QGraphicsPixmapItem
import noise  # Use python-perlin-noise instead of pynoise

# --- items

class Item(Serializable):
    __serialize_only__ = ["name","description","weight","sprite"]
    def __init__(self, name="", description="", weight=1, sprite="item"):
        super().__init__()
        self.name = name
        self.description = description
        self.weight = weight
        self.sprite = sprite

    def __str__(self):
        return f"{self.name} ({self.weight}kg): {self.description}"
        
    def use(self, character):
        pass  # Default: no effect    

class Container(Serializable):
    __serialize_only__ = ["items","current_char"]
    def __init__(self, current_char = None):
        super().__init__()
        self.items = []
        self.current_char = current_char

    def getItemIndex(self, item):
        for index, i in enumerate(self.items):
            if item is i:
                return index
        return -1

    def add_item(self, item):
        if isinstance(item, Item):
            index = self.getItemIndex(item)
            if index == -1: self.items.append(item)
            return True # either the item is already there or add the item 
        return False

    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item)
            return True
        return False

class Equippable(Item):
    __serialize_only__ = Item.__serialize_only__+["slot"]
    def __init__(self, name="", description="", weight=1, slot="primary_hand"):
        super().__init__(name, description, weight, sprite=name.lower())
        self.slot = slot
        
    def get_slot(self, char):
        if self == char.primary_hand:
            return "primary_hand"
        if self == char.secondary_hand:
            return "secondary_hand"
        if self == char.head: 
            return "head"
        if self == char.neck:
            return "neck"
        if self == char.torso:
            return "torso"
        if self == char.waist: 
            return "waist"
        if self == char.legs:
            return "legs"
        if self == char.foot:
            return "foot"
        return None
    
class Weapon(Equippable):
    __serialize_only__ = Equippable.__serialize_only__+["damage","stamina_consumption","max_damage"]
    def __init__(self, name="", damage=0 ,description="", weight=1, stamina_consumption=1):
        super().__init__(name, description, weight, slot="primary_hand")
        self.damage = damage # damages decrease when successfully hit and restored to max_damage using special item 
        self.stamina_consumption = stamina_consumption 
        self.max_damage = damage 

class Food(Item):
    __serialize_only__ = Item.__serialize_only__+["nutrition"]
    def __init__(self, name="", nutrition=0, description="", weight=1):
        super().__init__(name, description, weight, sprite=name.lower())
        self.nutrition = nutrition

    def use(self, character):
        if hasattr(character, 'hunger') and hasattr(character, 'max_hunger'):
            character.hunger = min(character.hunger + self.nutrition, character.max_hunger)
            character.hp = min(character.hp + self.nutrition/20.0, character.max_hp)
            character.stamina = min(character.stamina + self.nutrition/10.0, character.max_stamina)
            return True
        return False
        
class WeaponRepairTool(Item):
    __serialize_only__ = Item.__serialize_only__+["repairing_factor"]
    def __init__(self, name="", repairing_factor=1.05, description="", weight=1):
        super().__init__(name, description, weight, sprite=name.lower())
        self.repairing_factor = repairing_factor
    def use(self, character):
        if character.primary_hand:
            primary = character.primary_hand
            if primary.damage < 0.9*primary.max_damage:
                primary.damage = min( self.repairing_factor*primary.damage, primary.max_damage)
                return True
        return False
     
class Armor(Equippable):
    __serialize_only__ = Equippable.__serialize_only__+["armor"]
    def __init__(self, name="", armor=0, description="", weight=1, slot="torso"):
        super().__init__(name, description, weight, slot)
        self.armor = armor

# --- living

class Character(Container):
    __serialize_only__ = ["name", "hp", "max_hp", "x", "y", "primary_hand", "secondary_hand", "head", "neck", "torso", "waist", "legs", "foot", "items"]
    def __init__(self, name="", hp=100, x=50, y=50):
        super().__init__()
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.x = x
        self.y = y
        self.current_tile = None
        self.primary_hand = None
        self.secondary_hand = None
        self.head = None
        self.neck = None
        self.torso = None
        self.waist = None
        self.legs = None
        self.foot = None
    
    def equip_item(self, item, slot): 
        if isinstance(item, Equippable) and item.slot == slot:
            if self.add_item(item): # add item to inventory or verify if its already there 
                if slot == "primary_hand":
                    if self.primary_hand: # removes any form primary hand 
                        self.items.append(self.primary_hand)
                        self.primary_hand = None
                    index = self.getItemIndex(item)
                    if index != -1: self.items.pop(index) # remove from inventory
                    self.primary_hand = item # put in the hand 
                    return True
        return False # not equipped

    def unequip_item(self, slot):
        if slot == "primary_hand" and self.primary_hand:
            index = self.getItemIndex(self.primary_hand)
            if index == -1: self.items.append(self.primary_hand)
            self.primary_hand = None
            return True
        return False
        
    def pickup_item(self, item):
        return self.add_item(item)

    def move(self, dx, dy, game_map):
        return game_map.move_character(self, dx, dy)

    def drop_on_death(self):
        # Drop items to the tile if any
        if self.current_tile:
            for item in self.items:
                self.current_tile.add_item(item)  # Use Tile.add_item
            if self.primary_hand and random.uniform(0,1)<0.2:
                self.current_tile.add_item(self.primary_hand)
            self.items.clear()

    def get_sprite(self):
        # This should be overridden in subclasses
        return QPixmap()

    def calculate_damage_done(self):
        damage = 1
        if self.primary_hand and hasattr(self.primary_hand, 'damage'):
            damage += self.primary_hand.damage
        return damage

    def calculate_damage_received(self, damage, attacker):
        # Placeholder for armor or mitigation
        return damage
        
    def regenerate_stamina(self):
        pass

    def generate_initial_items(self):
        pass    

class Player(Character):
    __serialize_only__ = Character.__serialize_only__+["stamina","max_stamina","hunger","max_hunger"]
    def __init__(self, name="", hp=100, x=50, y=50, b_generate_items = True):
        super().__init__(name, hp, x, y)
        self.name = name
        self.stamina = 100
        self.max_stamina = 100
        self.hunger = 100
        self.max_hunger = 1000
        if b_generate_items: self.generate_initial_items()
    
    def move(self, dx, dy, game_map):
        if self.stamina >= 10:
            moved = game_map.move_character(self, dx, dy)
            if moved:
                self.stamina -= 2
            return moved
        return False
    
    def get_sprite(self):
        try:
            return Tile.SPRITES["player"]
        except KeyError:
            print("Warning: Player sprite not found")
            return QPixmap()  # Fallback    

    def calculate_damage_done(self):
        damage = 1
        if self.primary_hand and hasattr(self.primary_hand, 'damage'):
            damage += random.uniform(self.primary_hand.damage/3.0, self.primary_hand.damage)
            #print(damage, self.primary_hand.damage)
        return max(1, damage)

    def regenerate_stamina(self):
        self.stamina = min(self.stamina + 1, self.max_stamina) 
        
    def regenerate_health(self):
        self.hp = min(self.hp + 1, self.max_hp) 
    
    def generate_initial_items(self):
        self.equip_item(Weapon("Long_Sword", damage=10), "primary_hand")
        #self.equip_item(Weapon("Long_Sword", damage=10), "primary_hand")
        self.add_item(Food("Apple", nutrition=50))
        self.add_item(Food("Apple", nutrition=50))
        self.add_item(Food("Apple", nutrition=50))
        self.add_item(Food("Bread", nutrition=100))

class Enemy(Character):
    __serialize_only__ = Character.__serialize_only__+["type","stance","canSeeCharacter","patrol_direction"]
    def __init__(self, name="", hp=30, x=50, y=50, b_generate_items = True):
        super().__init__(name, hp, x, y)
        self.type = "Generic"
        self.stance = "Aggressive"
        self.canSeeCharacter = False
        self.patrol_direction = (random.choice([-1, 1]), 0)
        if b_generate_items: self.generate_initial_items()
    
    def can_see_character(self, player, game_map):
        distance = abs(self.x - player.x) + abs(self.y - player.y)
        if distance <= 5:
            return game_map.line_of_sight(self.x, self.y, player.x, player.y)
        return False
    
    def calculate_damage_done(self):
        damage = random.randint(1, 10)
        if self.primary_hand and hasattr(self.primary_hand, 'damage'):
            damage += self.primary_hand.damage
        return damage
    
    def calculate_damage_received(self, damage, attacker):
        return damage
    
    def update(self, player, map, game):  # Add game parameter
        #print(f"Updating enemy {self.name} at ({self.x}, {self.y}), can_see={self.can_see_character(player, map)}")
        if self.can_see_character(player, map):
            path = map.find_path(self.x, self.y, player.x, player.y)
            #print(path)
            if path:
                next_x, next_y = path[0]
                dx, dy = next_x - self.x, next_y - self.y
                tile = map.get_tile(next_x, next_y)
                if tile:
                    if tile.walkable and not tile.current_char:
                        if self.move(dx, dy, map):
                            pass #print(f"Enemy {self.name} moved to ({self.x}, {self.y}) via pathfinding")
                    elif tile.current_char is player:
                        game.events.append(AttackEvent(self, player, self.calculate_damage_done()))
                        print(f"Enemy {self.name} attacking player")
            else:
                print(f"No path found to player from ({self.x}, {self.y})")            
        else:
            # Random movement
            if random.random() < 0.3:
                dx, dy = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)])
                target_x, target_y = self.x + dx, self.y + dy
                tile = map.get_tile(target_x, target_y)
                if tile:
                    #print(f"Random move to ({target_x}, {target_y}): walkable={tile.walkable}, occupied={tile.current_char is not None}")
                    if tile.walkable and not tile.current_char:
                        if self.move(dx, dy, map):
                            pass #print(f"Enemy {self.name} randomly moved to ({self.x}, {self.y})")
                        else:
                            pass #print(f"Enemy {self.name} failed to randomly move to ({target_x}, {target_y})")
                else:
                    pass #print(f"Invalid random move tile ({target_x}, {target_y})")

    def generate_initial_items(self):
        if random.random() < 0.2:
            self.equip_item(Weapon("Club", damage=1), "primary_hand")
    
    def get_sprite(self):
        try:
            return Tile.SPRITES["enemy"]
        except KeyError:
            print("Warning: Enemy sprite not found")
            return QPixmap()  # Fallback

class Zombie(Enemy):
    __serialize_only__ = Enemy.__serialize_only__
    def __init__(self, name="", hp=30, x=50, y=50, b_generate_items = True):
        super().__init__(name, hp, x, y, b_generate_items)
        self.type = "Zombie"
        
    def calculate_damage_done(self):
        return random.randint(0, 15)

    def generate_initial_items(self):
        if random.random() < 0.7:
            self.add_item(Food("bread", nutrition=random.randint(50, 100)))

    def get_sprite(self):
        try:
            return Tile.SPRITES.get("zombie", Tile.SPRITES["enemy"])
        except KeyError:
            print("Warning: Zombie sprite not found")
            return QPixmap()

class Rogue(Enemy):
    __serialize_only__ = Enemy.__serialize_only__
    def __init__(self, name="", hp=30 , x=50, y=50, b_generate_items = True):
        super().__init__(name, hp, x, y, b_generate_items)
        self.type = "Rogue"
        
    def calculate_damage_done(self):
        damage = random.randint(0, 8)
        if self.primary_hand and hasattr(self.primary_hand, 'damage'):
            damage += self.primary_hand.damage
        return damage    

    def generate_initial_items(self):
        self.equip_item(Weapon("Long_Sword", damage=10), "primary_hand")
        if random.random() < 0.3:
            self.add_item(Food("bread", nutrition=random.randint(50, 100)))

    def get_sprite(self):
        try:
            return Tile.SPRITES.get("rogue", Tile.SPRITES["rogue"])
        except KeyError:
            print("Warning: Rogue sprite not found")
            return QPixmap()

# --- END 

# --- mapping
class Tile(Container):
    SPRITES = {}  # Class-level sprite cache
    list_sprites_names = [
        "grass",
        "dirt",
        "floor", 
        "player", 
        "enemy", 
        "zombie", 
        "wall", 
        "tree", 
        "water",
        "food", 
        "long_sword", 
        "club", 
        "sack",
        "apple",
        "fish",
        "bread",
        "HUD_arrow",
        "rogue",
        "stair_up",
        "stair_down",
        "dungeon_entrance",
        "rock"
    ]
    __serialize_only__ = ["items", "walkable", "blocks_sight", "default_sprite_key", "stair", "stair_x", "stair_y"]
    def __init__(self, walkable=True, sprite_key="grass"):
        super().__init__()
        self._load_sprites()
        self.walkable = walkable
        self.blocks_sight = not walkable
        self.default_sprite_key = sprite_key
        self.default_sprite = None # maybe isn't necessary anymore
        self.cosmetic_layer_sprite = None # to be used as a modifier for default_sprite
        self.current_char = None
        self.combined_sprite = None
        self.stair = None # used to store a tuple map cooord to connect between maps 
        self.stair_x = None # points to the stair tile from the map with coord self.stair
        self.stair_y = None # points to the stair tile from the map with coord self.stair 
        
    @classmethod
    def _try_load(cls, key):
        try: 
            cls.SPRITES[key] = QPixmap("./assets/"+key)
        except Exception as e:
            print(f"Failed to load sprites: {e}")
            cls.SPRITES[key] = QPixmap()
    
    @classmethod
    def _load_sprites(cls):
        if not cls.SPRITES:
            for key in cls.list_sprites_names: cls._try_load(key)
        
    def get_default_pixmap(self):
        self.default_sprite = self.SPRITES.get(self.default_sprite_key, QPixmap())
        return self.default_sprite

    def draw(self, scene, x, y, tile_size):
        base = self.get_default_pixmap()
        base_scaled = base.scaled(tile_size, tile_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        if self.current_char:
            char_sprite = self.current_char.get_sprite()
            char_scaled = char_sprite.scaled(tile_size, tile_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            combined = QPixmap(tile_size, tile_size)
            combined.fill(Qt.transparent)
            painter = QPainter(combined)
            painter.drawPixmap(0, 0, base_scaled)
            painter.drawPixmap(0, 0, char_scaled)
            painter.end()
            self.combined_sprite = combined
            #print(f"Tile ({x}, {y}) drawn with character {self.current_char.name}")
        elif self.items:
            if len(self.items) > 1:
                item_sprite = Tile.SPRITES.get("sack", base_scaled)
            else:
                item_sprite = Tile.SPRITES.get(self.items[0].sprite, base_scaled)
            item_scaled = item_sprite.scaled(tile_size, tile_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            combined = QPixmap(tile_size, tile_size)
            combined.fill(Qt.transparent)
            painter = QPainter(combined)
            painter.drawPixmap(0, 0, base_scaled)
            if not item_sprite.isNull():
                painter.drawPixmap(0, 0, item_scaled)
            painter.end()
            self.combined_sprite = combined
        else:
            self.combined_sprite = base_scaled
            #print(f"Tile ({x}, {y}) drawn as empty floor")
        item = QGraphicsPixmapItem(self.combined_sprite)
        item.setPos(x, y)
        scene.addItem(item)
        
    def add_item(self, item):
        self.items.append(item)
        return True  # No weight limit for tiles (adjust as needed)

    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item)
            return True
        return False

class Map(Serializable):
    __serialize_only__ = ["width","height","filename","grid","enemy_type","coords","enemies"]
    def __init__(self, filename="default", coords=(0, 0, 0), width=100, height=100, b_generate = True, previous_coords = (0,0,0), prev_x = 50, prev_y = 50, going_up = False):
        super().__init__()
        self.width = width
        self.height = height
        self.filename = filename
        self.grid = []
        self.enemy_type = "default" # used for fill_enemies to know which type of enemies should spawn. 
        self.path_cache = {}
        self.coords = coords # maybe would be necessary 
        self.previous_coords = previous_coords 
        self.prev_x = prev_x
        self.prev_y = prev_y
        self.going_up = going_up
        self.enemies = []
        self.starting_x = None
        self.starting_y = None
        if b_generate: self.generate()
    
    def from_dict(self, dictionary):
        if not super().from_dict(dictionary):
            return False
        # Place characters after loading grid
        for enemy in self.enemies:
            self.place_character(enemy)
        return True
    
    def _get_sprite_key(self, tile):
        """Return the sprite key for a tile's default_sprite."""
        for key, sprite in Tile.SPRITES.items():
            if tile.default_sprite == sprite:
                return key
        return "grass"  # Fallback if no match found    
        
    def line_of_sight(self, x1, y1, x2, y2):
        # Bresenham's line algorithm
        points = []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        while True:
            points.append((x1, y1))
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
        for x, y in points:
            tile = self.get_tile(x, y)
            if tile and tile.blocks_sight:
                return False
        return True    

    def generate(self):
        if self.filename == "procedural_dungeon":
            # Default to descending from (0, 0, 0) if no previous coords provided
            return self.generate_procedural_dungeon(self.previous_coords, self.prev_x, self.prev_y, self.going_up)
        elif self.filename == "procedural_field":
            self.generate_procedural_field()
        elif self.filename == "procedural_road":
            self.generate_procedural_road()
        elif self.filename == "procedural_lake":
            self.generate_procedural_lake()
        elif self.filename == "default":
            self._generate_default()
        else:
            if self.filename:
                try:
                    with open(f"maps/{self.filename}.txt", 'r') as f:
                        lines = f.readlines()
                        self.grid = [
                            [Tile(walkable=c != '#', sprite_key="wall" if c == '#' else "grass") for c in line.strip()]
                            for line in lines
                        ]
                except FileNotFoundError:
                    print(f"Map file {self.filename}.txt not found, using default map")
                    self._generate_default()
            
    def add_dirt_patches(self):
        # Generate dirt patches using Perlin noise or random clusters
        for i in range(100):
            for j in range(100):
                # Option 1: Perlin noise for smooth, natural dirt patches
                noise_value = noise.snoise2(i * 0.1, j * 0.1, octaves=1)  # Adjust scale (0.1) for patch size
                if noise_value > 0.2:  # Threshold for dirt
                    self.grid[i][j] = Tile(walkable=True, sprite_key="dirt")
                    
    def add_trees(self):
        # Add trees with slight clustering
        for i in range(1, 99):
            for j in range(1, 99):
                # Base chance for a tree
                tree_chance = 0.15
                # Increase chance if neighboring tiles have trees (clustering)
                for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    if 0 <= i + di < 100 and 0 <= j + dj < 100:
                        if self.grid[i + di][j + dj].default_sprite_key == "tree":
                            tree_chance += 0.1
                if random.random() < tree_chance:
                    self.grid[i][j] = Tile(walkable=False, sprite_key="tree")
    
    def add_rocks(self):
        for i in range(1, 99):
            for j in range(1, 99):
                if random.random() < 0.001:  # 2% chance for water
                    self.grid[i][j] = Tile(walkable=False, sprite_key="water")
                elif random.random() < 0.05:  # 5% chance for rocks
                    self.grid[i][j] = Tile(walkable=False, sprite_key="rock")
            
    def _generate_default(self):
        # inner floors, random trees
        self.grid = [ [Tile(walkable=True, sprite_key="grass") for j in range(100)] for i in range(100) ]
        
        self.add_dirt_patches()
        self.add_trees()
        self.add_rocks()

    def generate_procedural_dungeon(self, previous_map_coords, prev_x, prev_y, up=False):
        """
        Generate a multi-level RogueLike dungeon with rooms, corridors, and a stair_down.
        
        Args:
            previous_map_coords (tuple): (x, y, z) coordinates from the previous map.
            prev_x (int): x-coordinate of the stair/entrance on the previous map.
            prev_y (int): y-coordinate of the stair/entrance on the previous map.
            up (bool): True if ascending, False if descending.
        
        Returns:
            tuple: (x, y, z) of the starting point (stair_up or stair_down position).
        """
        prev_x_map, prev_y_map, prev_z = previous_map_coords
        new_z = prev_z + 1 if up else prev_z - 1
        self.coords = (prev_x_map, prev_y_map, new_z)  # Update map coords, it's necessary? 
        self.enemy_type = "dungeon"

        # Initialize grid with walls
        self.grid = [
            [Tile(walkable=False, sprite_key="wall") for _ in range(self.width)]
            for _ in range(self.height)
        ]

        # Generate rooms
        rooms = []
        num_rooms = random.randint(8, 15)
        max_attempts = num_rooms * 10
        attempts = 0
        while len(rooms) < num_rooms and attempts < max_attempts:
            room_w = random.randint(5, 10)
            room_h = random.randint(5, 10)
            room_x = random.randint(1, self.width - room_w - 1)
            room_y = random.randint(1, self.height - room_h - 1)
            overlap = False
            for other_x, other_y, other_w, other_h in rooms:
                if (room_x < other_x + other_w + 2 and
                    room_x + room_w + 2 > other_x and
                    room_y < other_y + other_h + 2 and
                    room_y + room_h + 2 > other_y):
                    overlap = True
                    break
            if not overlap:
                rooms.append((room_x, room_y, room_w, room_h))
                for y in range(room_y, room_y + room_h):
                    for x in range(room_x, room_x + room_w):
                        self.grid[y][x] = Tile(walkable=True, sprite_key="floor")
            attempts += 1

        if not rooms:
            raise RuntimeError("Failed to generate any rooms for dungeon")

        # Connect rooms with L-shaped corridors
        for i in range(len(rooms) - 1):
            x1, y1 = rooms[i][0] + rooms[i][2] // 2, rooms[i][1] + rooms[i][3] // 2
            x2, y2 = rooms[i + 1][0] + rooms[i + 1][2] // 2, rooms[i + 1][1] + rooms[i + 1][3] // 2
            if random.choice([True, False]):
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    self.grid[y1][x] = Tile(walkable=True, sprite_key="floor")
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    self.grid[y][x2] = Tile(walkable=True, sprite_key="floor")
            else:
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    self.grid[y][x1] = Tile(walkable=True, sprite_key="floor")
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    self.grid[y2][x] = Tile(walkable=True, sprite_key="floor")

        # Choose starting point (stair_up or stair_down to previous map)
        start_room = random.choice(rooms)
        room_x, room_y, room_w, room_h = start_room
        new_x = room_x + room_w // 2
        new_y = room_y + room_h // 2
        stair_sprite = "stair_down" if up else "stair_up"
        self.grid[new_y][new_x] = Tile(walkable=True, sprite_key=stair_sprite)
        self.grid[new_y][new_x].stair = previous_map_coords
        self.grid[new_y][new_x].stair_x = prev_x  # Point to the stair/entrance on previous map
        self.grid[new_y][new_x].stair_y = prev_y
        new_coords = (new_x, new_y, new_z)

        # Add stair_down to deeper level with 50% probability (not on topmost level if up=True)
        if not up and random.random() < 0.5:
            available_rooms = [(rx, ry, rw, rh) for rx, ry, rw, rh in rooms
                              if (rx + rw // 2, ry + rh // 2) != (new_x, new_y)]
            if available_rooms:
                down_room = random.choice(available_rooms)
                down_x = down_room[0] + down_room[2] // 2
                down_y = down_room[1] + down_room[3] // 2
                target_map = (prev_x_map, prev_y_map, new_z - 1)
                self.grid[down_y][down_x] = Tile(walkable=True, sprite_key="stair_down")
                self.grid[down_y][down_x].stair = target_map
                self.grid[down_y][down_x].stair_x = down_x  # Point to stair_up on next level
                self.grid[down_y][down_x].stair_y = down_y
                print(f"Placed stair_down at ({down_x}, {down_y}) linking to {target_map}")

        print(f"generate_procedural_dungeon(): from {previous_map_coords} to ({prev_x_map}, {prev_y_map}, {new_z}), entry at ({new_x}, {new_y})")
        self.starting_x = new_x
        self.starting_y = new_y
        return new_coords
    
    def generate_procedural_field(self):
        self.grid = [[Tile(walkable=True, sprite_key="grass") for _ in range(100)] for _ in range(100)]
        self.add_dirt_patches()
        self.add_rocks()
        for i in range(100):
            for j in range(100):
                n = noise.pnoise2(i * 0.1, j * 0.1, octaves=1, persistence=0.5, lacunarity=2.0)
                if n > 0.2:
                    self.grid[i][j] = Tile(walkable=False, sprite_key="tree")
                elif random.random() < 0.01:
                    self.grid[i][j].add_item(Food("Apple", nutrition=10))
                    
    def generate_procedural_road(self):
        self.grid = [[Tile(walkable=True, sprite_key="grass") for _ in range(100)] for _ in range(100)]
        self.add_dirt_patches()
        # Vertical road with noise
        road_x = 50
        for y in range(100):
            offset = int(noise.pnoise1(y * 0.1, octaves=1, persistence=0.5, lacunarity=2.0) * 10)
            road_x += offset
            road_x = max(1, min(98, road_x))
            self.grid[y][road_x] = Tile(walkable=True, sprite_key="grass")
            if random.random() < 0.05:
                self.grid[y][road_x].add_item(Food("Bread", nutrition=15))
        for i in range(100):
            for j in range(100):
                if random.random() < 0.1 and abs(j - road_x) > 2:
                    self.grid[i][j] = Tile(walkable=False, sprite_key="tree")
    
    def generate_procedural_lake(self):
        self.grid = [[Tile(walkable=True, sprite_key="grass") for _ in range(100)] for _ in range(100)]
        self.add_dirt_patches()
        center_x, center_y = 50, 50
        for i in range(100):
            for j in range(100):
                n = noise.pnoise2(i * 0.05, j * 0.05, octaves=1, persistence=0.5, lacunarity=2.0)
                dist = ((i - center_x) ** 2 + (j - center_y) ** 2) ** 0.5
                if n > -0.1 and dist < 30:
                    self.grid[i][j] = Tile(walkable=False, sprite_key="water")
                elif random.random() < 0.1:
                    self.grid[i][j] = Tile(walkable=False, sprite_key="tree")
                elif random.random() < 0.01:
                    self.grid[i][j].add_item(Food("Fish", nutrition=80))

        # Add dungeon entrance with 70% probability
        if random.random() < 0.7:
            walkable_tiles = [(i, j) for i in range(100) for j in range(100)
                             if self.grid[i][j].walkable and self.grid[i][j].default_sprite == Tile.SPRITES["grass"]]
            if walkable_tiles:
                entrance_x, entrance_y = random.choice(walkable_tiles)
                target_map = (self.coords[0], self.coords[1], -1)
                self.grid[entrance_y][entrance_x] = Tile(walkable=True, sprite_key="dungeon_entrance")
                self.grid[entrance_y][entrance_x].stair = target_map
                self.grid[entrance_y][entrance_x].stair_x = entrance_x
                self.grid[entrance_y][entrance_x].stair_y = entrance_y
                print(f"Placed dungeon_entrance at ({entrance_x}, {entrance_y}) linking to {target_map}")
                    
    def get_tile(self, x, y):
        try:
            if 0 <= y < len(self.grid) and 0 <= x < len(self.grid[0]):
                return self.grid[y][x]
            return None
        except Exception as e:
            print(f"Error accessing tile ({x}, {y}): {e}")
            return None

    def place_character(self, char):
        try:
            tile = self.get_tile(char.x, char.y)
            if tile and tile.walkable and not tile.current_char:
                tile.current_char = char
                char.current_tile = tile
                #print(f"Placed {char.name} at ({char.x}, {char.y}), tile walkable={tile.walkable}")
                return True
            #print(f"Cannot place {char.name} at ({char.x}, {char.y}): Invalid or occupied tile")
            return False
        except Exception as e:
            print(f"Error placing character {char.name}: {e}")
            return False
            
    def remove_character(self, char):
        try:
            tile = self.get_tile(char.x, char.y)
            if tile and tile.current_char == char:
                tile.current_char = None
                char.current_tile = None
                print(f"Removed {char.name} from ({char.x}, {char.y})")
                return True
            print(f"Failed to remove {char.name} at ({char.x}, {char.y}): Tile not found or not occupied by character")
            return False
        except Exception as e:
            print(f"Error removing character {char.name}: {e}")
            return False

    def move_character(self, char, dx, dy):
        try:
            new_x = char.x + dx
            new_y = char.y + dy
            target_tile = self.get_tile(new_x, new_y)
            if target_tile and target_tile.walkable and target_tile.current_char is None:
                if char.current_tile:
                    char.current_tile.current_char = None
                char.x = new_x
                char.y = new_y
                self.place_character(char)
                return True
            return False
        except Exception as e:
            print(f"Error moving character {char.name}: {e}")
            return False

    def find_path(self, start_x: int, start_y: int, goal_x: int, goal_y: int) -> list[tuple[int, int]]:
        """A* pathfinding to find shortest path from (start_x, start_y) to (goal_x, goal_y)."""
        # Validate coordinates
        if not (0 <= start_x < 100 and 0 <= start_y < 100 and 0 <= goal_x < 100 and 0 <= goal_y < 100):
            #print(f"Invalid coordinates: start=({start_x}, {start_y}), goal=({goal_x}, {goal_y})")
            return []

        open_set = []
        heappush(open_set, (0, (start_x, start_y)))
        came_from = {}
        g_score = {(start_x, start_y): 0}
        f_score = {(start_x, start_y): abs(goal_x - start_x) + abs(goal_y - start_y)}  # Manhattan distance

        while open_set:
            _, current = heappop(open_set)
            x, y = current

            # Reached the goal
            if (x, y) == (goal_x, goal_y):
                path = []
                while (x, y) in came_from:
                    path.append((x, y))
                    x, y = came_from[(x, y)]
                #print(f"Path found from ({start_x}, {start_y}) to ({goal_x}, {goal_y}): {path}")
                return path[::-1]  # Reverse path

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                next_x, next_y = x + dx, y + dy
                if not (0 <= next_x < 100 and 0 <= next_y < 100):
                    continue  # Skip out-of-bounds tiles
                tile = self.get_tile(next_x, next_y)
                if tile:
                    # Allow the goal tile (player's position) even if occupied
                    is_goal = (next_x == goal_x and next_y == goal_y)
                    if tile.walkable and (is_goal or not tile.current_char):
                        tentative_g_score = g_score[(x, y)] + 1
                        if (next_x, next_y) not in g_score or tentative_g_score < g_score[(next_x, next_y)]:
                            came_from[(next_x, next_y)] = (x, y)
                            g_score[(next_x, next_y)] = tentative_g_score
                            f_score[(next_x, next_y)] = tentative_g_score + abs(goal_x - next_x) + abs(goal_y - next_y)
                            heappush(open_set, (f_score[(next_x, next_y)], (next_x, next_y)))
                else:
                    print(f"Invalid tile at ({next_x}, {next_y})")

        #print(f"No path found from ({start_x}, {start_y}) to ({goal_x}, {goal_y}): likely blocked by obstacles")
        return []  # No path found

# --- END 