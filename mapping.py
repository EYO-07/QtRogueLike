# mapping.py
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtWidgets import QGraphicsPixmapItem
from items import *
import json 
import random
import noise  # Use python-perlin-noise instead of pynoise
from heapq import heappush, heappop
import math
import os 
import tempfile
import shutil
#from living import * 

# Tile : Container
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
        "rogue"
    ]
    
    def __init__(self, walkable=True, sprite_key="grass"):
        super().__init__()
        self._load_sprites()
        self.walkable = walkable
        self.blocks_sight = not walkable
        self.default_sprite = self.SPRITES.get(sprite_key, QPixmap())
        self.current_char = None
        self.items = []
        self.combined_sprite = None
        self.stair = None # used to store a tuple map cooord to connect between maps 
        
    # def __init__(self, type_of_tile="grass", walkable=True):
        # super().__init__()
        # self.type = type_of_tile
        # self.walkable = walkable
        # self.stair = None    
    
    def to_dict(self):
        """Serialize Tile to a dictionary."""
        data = super().to_dict()
        data.update({
            "type": self.type,
            "walkable": self.walkable,
            "stair": self.stair
        })
        return data
        
    @classmethod
    def from_dict(cls, data, characters=None):
        """Deserialize Tile from a dictionary."""
        tile = cls(type_of_tile=data["type"], walkable=data["walkable"])
        tile.items = Container.from_dict(data, characters).items
        tile.current_char = Container.from_dict(data, characters).current_char
        tile.stair = data.get("stair")
        return tile    
    
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
        # if not cls.SPRITES:
            # try:
                # cls.SPRITES["grass"] = QPixmap("./assets/grass")
                # cls.SPRITES["dirt"] = QPixmap("./assets/dirt")
                # cls.SPRITES["floor"] = QPixmap("./assets/floor")
                # cls.SPRITES["player"] = QPixmap("./assets/player")
                # cls.SPRITES["enemy"] = QPixmap("./assets/enemy")
                # cls.SPRITES["zombie"] = QPixmap("./assets/zombie")
                # cls.SPRITES["wall"] = QPixmap("./assets/wall")
                # cls.SPRITES["tree"] = QPixmap("./assets/tree")
                # cls.SPRITES["water"] = QPixmap("./assets/water")
                # cls.SPRITES["food"] = QPixmap("./assets/food")
                # cls.SPRITES["bread"] = QPixmap("./assets/bread")
                # cls.SPRITES["long_sword"] = QPixmap("./assets/long_sword")
                # cls.SPRITES["club"] = QPixmap("./assets/club")
                # cls.SPRITES["sack"] = QPixmap("./assets/sack")
                # cls.SPRITES["apple"] = QPixmap("./assets/apple")
                # cls.SPRITES["fish"] = QPixmap("./assets/fish")
            # except Exception as e:
                # print(f"Failed to load sprites: {e}")
                # for key in [
                        # "grass",
                        # "dirt",
                        # "floor", 
                        # "player", 
                        # "enemy", 
                        # "zombie", 
                        # "wall", 
                        # "tree", 
                        # "water",
                        # "food", 
                        # "long_sword", 
                        # "club", 
                        # "sack",
                        # "apple",
                        # "fish"
                    # ]:
                    # cls.SPRITES[key] = QPixmap()
    
    def get_default_pixmap(self):
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

class Map:
    def __init__(self, filename="default", width=100, height=100):
        self.width = width
        self.height = height
        self.filename = filename
        self.grid = []
        self.generate()
        self.enemy_type = "default" # used for fill_enemies to know which type of enemies should spawn. 
        self.path_cache = {}
        
    def save_state(self, enemies, filename):
        """Save the map's state to a JSON file."""
        from living import Character, Player, Enemy, Zombie, Rogue
        try:
            # Ensure ./saves directory exists
            saves_dir = "./saves"
            if not os.path.exists(saves_dir):
                os.makedirs(saves_dir)

            state = {
                "version": "1.0.0",
                "filename": self.filename,
                "width": self.width,
                "height": self.height,
                "grid": [
                    [
                        {
                            "walkable": tile.walkable,
                            "sprite_key": tile.default_sprite == Tile.SPRITES.get("grass") and "grass" or
                                         tile.default_sprite == Tile.SPRITES.get("tree") and "tree" or
                                         tile.default_sprite == Tile.SPRITES.get("water") and "water" or
                                         tile.default_sprite == Tile.SPRITES.get("wall") and "wall" or "grass",
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
                                } for item in tile.items
                            ],
                            "stair": tile.stair
                        } for tile in row
                    ] for row in self.grid
                ],
                "enemies": [
                    {
                        "type": enemy.type,
                        "x": enemy.x,
                        "y": enemy.y,
                        "hp": enemy.hp,
                        "max_hp": enemy.max_hp,
                        "patrol_direction": list(enemy.patrol_direction),
                        "stance": enemy.stance,
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
                            } for item in enemy.items
                        ],
                        "equipped": {
                            "primary_hand": {
                                "type": "weapon",
                                "name": enemy.primary_hand.name,
                                "damage": enemy.primary_hand.damage,
                                "max_damage": enemy.primary_hand.max_damage,
                                "weight": enemy.primary_hand.weight,
                                "description": enemy.primary_hand.description,
                                "sprite": enemy.primary_hand.sprite,
                                "stamina_consumption": enemy.primary_hand.stamina_consumption
                            } if enemy.primary_hand else None
                        }
                    } for enemy in enemies
                ]
            }

            # Backup existing map file
            if os.path.exists(filename):
                shutil.copy(filename, f"{filename}.bak")

            # Write to temporary file in ./saves
            temp_file_name = f"{filename}.tmp"
            with open(temp_file_name, 'w') as temp_file:
                json.dump(state, temp_file, indent=2)

            # Atomically rename
            os.replace(temp_file_name, filename)
            print(f"Saved map state to {filename}")

        except Exception as e:
            print(f"Error saving map state to {filename}: {e}")
            if os.path.exists(f"{filename}.bak"):
                shutil.copy(f"{filename}.bak", filename)

    def load_state(self, enemies, state):
        """Load the map's state from a JSON state dictionary."""
        from living import Character, Player, Enemy, Zombie, Rogue
        try:
            # Check version
            save_version = state.get("version", "0.0.0")
            if save_version != "1.0.0":
                print(f"Warning: Map save version {save_version} may not be compatible")

            # Initialize grid
            self.filename = state["filename"]
            self.width = state["width"]
            self.height = state["height"]
            self.grid = [
                [
                    Tile(
                        walkable=tile_data["walkable"],
                        sprite_key=tile_data["sprite_key"]
                    ) for tile_data in row
                ] for row in state["grid"]
            ]

            # Restore items
            for y, row in enumerate(state["grid"]):
                for x, tile_data in enumerate(row):
                    for item_data in tile_data["items"]:
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
                        self.grid[y][x].add_item(item)
                    self.grid[y][x].stair = tile_data["stair"]

            # Restore enemies
            enemies.clear()
            for enemy_data in state.get("enemies", []):
                try:
                    if not (0 <= enemy_data["x"] < self.width and 0 <= enemy_data["y"] < self.height):
                        print(f"Warning: Invalid enemy position ({enemy_data['x']}, {enemy_data['y']})")
                        continue
                    # Use type as name since name field is not saved
                    enemy_type = enemy_data.get("type", "Zombie")
                    enemy_name = enemy_type  # Default to type as name
                    if enemy_type == "Zombie":
                        enemy = Zombie(enemy_name, enemy_data["hp"], enemy_data["x"], enemy_data["y"])
                    elif enemy_type == "Rogue":
                        enemy = Rogue(enemy_name, enemy_data["hp"], enemy_data["x"], enemy_data["y"])
                    else:
                        enemy = Zombie(enemy_name, enemy_data["hp"], enemy_data["x"], enemy_data["y"])
                    enemy.max_hp = enemy_data.get("max_hp", enemy.hp)
                    enemy.patrol_direction = tuple(enemy_data.get("patrol_direction", [random.choice([-1, 1]), 0]))
                    enemy.stance = enemy_data.get("stance", "Aggressive")
                    for item_data in enemy_data.get("items", []):
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
                        enemy.add_item(item)
                    if enemy_data.get("equipped", {}).get("primary_hand"):
                        weapon_data = enemy_data["equipped"]["primary_hand"]
                        weapon = Weapon(
                            name=weapon_data["name"],
                            damage=weapon_data["damage"],
                            description=weapon_data.get("description", ""),
                            weight=weapon_data.get("weight", 1),
                            stamina_consumption=weapon_data["stamina_consumption"]
                        )
                        weapon.max_damage = weapon_data["max_damage"]
                        enemy.equip_item(weapon, "primary_hand")
                    enemies.append(enemy)
                except KeyError as ke:
                    print(f"Error processing enemy data: missing field {ke}")
                    continue
            return enemies
        except Exception as e:
            print(f"Error loading map state: {e}")
            raise  # Let caller handle the error instead of generating a new map    
    
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
        if self.filename == "procedural_field":
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
            
    def _generate_default(self):
        # inner floors, random trees
        self.grid = [ [Tile(walkable=True, sprite_key="grass") for j in range(100)] for i in range(100) ]
        for i in range(1, 99):
            for j in range(1, 99):
                if random.random() < 0.2:  # 10% chance of wall
                    self.grid[i][j] = Tile(walkable=False, sprite_key="tree") 

    def generate_procedural_field(self):
        self.grid = [[Tile(walkable=True, sprite_key="grass") for _ in range(100)] for _ in range(100)]
        for i in range(100):
            for j in range(100):
                n = noise.pnoise2(i * 0.1, j * 0.1, octaves=1, persistence=0.5, lacunarity=2.0)
                if n > 0.2:
                    self.grid[i][j] = Tile(walkable=False, sprite_key="tree")
                elif random.random() < 0.01:
                    self.grid[i][j].add_item(Food("Apple", nutrition=10))
                    
    def generate_procedural_road(self):
        self.grid = [[Tile(walkable=True, sprite_key="grass") for _ in range(100)] for _ in range(100)]
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
                    self.grid[i][j].add_item(Food("Fish", nutrition=20))
                    
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
            print(f"Invalid coordinates: start=({start_x}, {start_y}), goal=({goal_x}, {goal_y})")
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
                print(f"Path found from ({start_x}, {start_y}) to ({goal_x}, {goal_y}): {path}")
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

        print(f"No path found from ({start_x}, {start_y}) to ({goal_x}, {goal_y}): likely blocked by obstacles")
        return []  # No path found









# --- END 