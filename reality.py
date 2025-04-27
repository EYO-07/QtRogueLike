# items living mapping 

# project
from events import * 
from serialization import * 
from globals_variables import *

# built-in
import random
import math
import os 
from heapq import heappush, heappop
from itertools import product

# third-party 
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtWidgets import QGraphicsPixmapItem
import noise  # Use python-perlin-noise instead of pynoise

# --- Utilities
def GetRandomTile_Reservoir_Sampling(tile_container = None, foreach_tiles = None ):
    """
    Selects a uniformly random tile using reservoir sampling.

    Args:
        tile_container: Any object (not directly used here).
        foreach_tiles (Callable): A function like `map_obj.foreach_tiles`
            that takes a callback `(tile, i, j, state)` and state, and
            applies it to each tile.

    Returns:
        tuple: (tile, i, j) of the randomly selected tile, or None if no tiles were found.
    """
    if foreach_tiles == None: return None
    def random_selector(tile, i, j, state):
        state['count'] += 1
        if random.randint(1, state['count']) == 1:
            state['chosen'] = (tile, i, j)
    state = {'count': 0, 'chosen': None}
    foreach_tiles(tile_container, random_selector, state)
    return state['chosen']

def GetRandomTiles_Reservoir_Sampling(tile_container=None, foreach_tiles=None, k=1):
    """
    Selects `k` uniformly random tiles using reservoir sampling.

    Args:
        tile_container: Object passed to the foreach function as `self`.
        foreach_tiles (Callable): A method like `Map.foreach_tiles` or `Map.foreach_rooms_tiles`
            that accepts the form `foreach_tiles(self, callback, state)`.
        k (int): Number of tiles to sample.
        
    Returns:
        list[tuple]: A list of (tile, i, j) tuples randomly sampled without replacement.
    """
    if foreach_tiles is None or k <= 0: return []
    def sampler(tile, i, j, state):
        state['count'] += 1
        idx = state['count'] - 1
        if idx < state['k']:
            state['reservoir'].append((tile, i, j))
        else:
            s = random.randint(0, idx)
            if s < state['k']:
                state['reservoir'][s] = (tile, i, j)
    state = {'count': 0, 'k': k, 'reservoir': []}
    foreach_tiles(tile_container, sampler, state)
    return state['reservoir']
    
# --- Entity2D
class Entity2D:
    def __init__(self):
        self.sprite = None
    def get_sprite(self):
        if not self.sprite: 
            print(f"Warning: {self} sprite not found")
            return QPixmap()
        try:
            return Tile.SPRITES[self.sprite]
        except KeyError:
            print(f"Warning: {self} sprite not found")
            return QPixmap()  # Fallback    
    def paint_to(self, painter):
        painter.drawPixmap(0, 0, self.get_sprite())

# --- items

class Item(Serializable, Entity2D):
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

    def add_item_by_chance(self, item_name, chance = 0.1, *args, **kwargs):
        coin = random.random()
        if coin < chance:
            item_class = globals()[item_name]
            item_instance = item_class(*args, **kwargs)
            self.add_item(item_instance) 
            return item_instance
        return None

class Equippable(Item):
    __serialize_only__ = Item.__serialize_only__+["slot"]
    def __init__(self, name="", description="", weight=1, slot="primary_hand"):
        super().__init__(name, description, weight, sprite=name.lower())
        self.slot = slot
        
    def get_equipped_slot(self, char):
        current_slot = None
        for atrib in EQUIPMENT_SLOTS:
            if self == getattr(char, atrib):
                current_slot = atrib
                break
        return current_slot
    
class Weapon(Equippable):
    __serialize_only__ = Equippable.__serialize_only__+["damage","stamina_consumption","max_damage","durability_factor"]
    def __init__(self, name="", damage=0 ,description="", weight=1, stamina_consumption=1, durability_factor=0.995):
        super().__init__(name, description, weight, slot="primary_hand")
        self.damage = damage # damages decrease when successfully hit and restored to max_damage using special item 
        self.stamina_consumption = stamina_consumption 
        self.max_damage = damage 
        self.durability_factor = durability_factor
    
    def stats_update(self, player):
        if not player.primary_hand is self: return False
        # weapon stamina consumption
        player.stamina = max(0, player.stamina - self.stamina_consumption)
        # weapon durability consumption 
        self.damage = max(0,self.damage*self.durability_factor)
        if self.damage < 0.5: player.primary_hand = None
        return True
    
# Sword.use_special () || ... Sword.special_attack()* || Append AttackEvent
# AttackEvent ~ Game.process_events() || 
class Sword(Weapon):
    __serialize_only__ = Weapon.__serialize_only__ 
    def __init__(self, name="long_sword", damage=8 ,description="", weight=1, stamina_consumption=1, durability_factor=0.995):
        super().__init__(name, damage, description, weight, stamina_consumption, durability_factor)
        self.days_to_unlock_special = 20
    
    def get_player_parry_chance(self, player, enemy, damage):
        # should be used on the context that self is the primary_hand of player 
        primary = enemy.primary_hand
        if not enemy: return 0.0
        if player.stamina <= damage: return 0.0 
        # Sword Fight Chance
        if isinstance(primary, Sword): 
            return 0.7
        elif isinstance(primary, Mace):
            return 0.5
        return 0.0 
    
    def use_special(self, player, map, game):
        # knight chess attack, sword swing 
        if game.current_day < self.days_to_unlock_special: 
            if game.journal_window:
                game.journal_window.append_text(
                    f"Survive more than {self.days_to_unlock_special} days to use this Sword Skill, that move will select an enemy in L position (like a chess knight) and do considerable damage."
                )
            game.add_message(f"I'm used to do this move, maybe with some practice ...")
            return False
        if not player: return False
        if not map: return False
        x = player.x
        y = player.y
        shuffled_list = random.sample(CHESS_KNIGHT_DIFF_MOVES, len(CHESS_KNIGHT_DIFF_MOVES))
        b_attack_performed = False
        for dx,dy in  shuffled_list:
            tile = map.get_tile(x+dx,y+dy)
            if tile:
                if self.special_attack(player, tile, game):
                    b_attack_performed = True 
                    break
        return b_attack_performed

    def special_attack(self, player, tile, game):
        if not game: return False
        char = tile.current_char
        if not char: return False
        if not isinstance(char, Enemy): return False
        if not player.can_see_character(char, game.map): 
            game.add_message(f"Where is the target? ...")
            return False
        # has char and the char is enemy 
        print(f"Enemy {char}")
        if player.stamina < player.max_stamina/3: return False
        damage = random.uniform(self.max_damage,3*self.max_damage)
        if damage > char.hp: # manual kill and move process 
            old_x = player.x 
            old_y = player.y
            dx = char.x - player.x 
            dy = char.y - player.y 
            # death of char and removal from the map 
            char.drop_on_death()
            char.current_tile.current_char = None
            tile = char.current_tile
            if game.current_map in game.enemies and char in game.enemies[game.current_map]:
                game.enemies[game.current_map].remove(char)
            # move the character 
            old_x, old_y = player.x, player.y
            if game.map.move_character(player, dx, dy):
                tile.current_char = player
                game.dirty_tiles.add((old_x, old_y))
                game.dirty_tiles.add((player.x, player.y))
                game.draw()
        else:
            game.events.append( AttackEvent(player, char, damage ) )
        # extra stats besides attack event
        player.stamina = player.stamina - player.max_stamina/3
        for i in range(2): self.damage = max(0,self.damage*self.durability_factor)
        if self.damage < 0.5: player.primary_hand = None
        return True 

class Mace(Weapon):
    __serialize_only__ = Weapon.__serialize_only__ 
    def __init__(self, name="mace", damage=10 ,description="", weight=1, stamina_consumption=2, durability_factor=0.995):
        super().__init__(name, damage, description, weight, stamina_consumption, durability_factor)
        self.days_to_unlock_special = 10
    def get_player_parry_chance(self, player, enemy, damage):
        primary = enemy.primary_hand
        if not enemy: return 0.0
        if player.stamina <= damage: return 0.0 
        # Sword Fight Chance
        if isinstance(primary, Sword): 
            return 0.5
        elif isinstance(primary, Mace):
            return 0.3
        return 0.0 

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
    __serialize_only__ = Item.__serialize_only__+["repairing_factor","uses"]
    def __init__(self, name="", repairing_factor=1.05, description="", weight=1, uses = 10):
        super().__init__(name, description, weight, sprite=name.lower())
        self.repairing_factor = repairing_factor
        self.uses = uses
    def use(self, character):
        if character.primary_hand:
            primary = character.primary_hand
            if primary.damage < 0.9*primary.max_damage:
                primary.damage = min( self.repairing_factor*primary.damage, primary.max_damage)
                self.uses -= 1
                return True
        return False
     
class Armor(Equippable):
    __serialize_only__ = Equippable.__serialize_only__+["armor"]
    def __init__(self, name="", armor=0, description="", weight=1, slot="torso"):
        super().__init__(name, description, weight, slot)
        self.armor = armor

class Shield(Equippable):
    pass

# --- living

class Character(Container, Entity2D):
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
        
        # used to slowdown a character by checking if turns % self.update_turn: return 
        self.update_turn = 1 
    
    def reset_stats(self):
        self.hp = self.max_hp
    
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
            for equip in EQUIPMENT_SLOTS:
                item = getattr(self, equip)
                if item and random.uniform(0,1)<0.2:
                    self.current_tile.add_item(item)
            self.items.clear()

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

    def turn_update(self, game_turns_counter):
        """
        Determines whether this entity should perform its update logic
        on the current game turn.

        This is useful in a turn-based system where not all entities 
        act on every game tick. For example, an entity with 
        `self.update_turn = 3` would act only every 3 turns.

        Usage:        
            On derived class use, 
            
            def turn_update(self, game_turns_counter):
                if not super().update(game_turns_counter): return False
                # return True if the entity should update, False otherwise.
        Args:
            game_turns_counter (int): The current global turn count of the game.

        Returns:
            bool: True if the entity should update this turn, False otherwise.
        """
        if game_turns_counter % self.update_turn: return False
        return True

    def can_see_character(self, another, game_map):
        if not isinstance(another, Character): return None
        distance = abs(self.x - another.x) + abs(self.y - another.y)
        if distance <= 7:
            return game_map.line_of_sight(self.x, self.y, another.x, another.y)
        return False

    def use_first_item_of(self, item_class_name, game_instance):
        for item in self.items:
            if isinstance(item, item_class_name):
                game_instance.events.append(UseItemEvent(self, item))
                game_instance.game_iteration()
                break
        game_instance.update_inv_window()
    
class Ally(Character):
    pass

class Player(Character):
    __serialize_only__ = Character.__serialize_only__+[
        "stamina","max_stamina","hunger","max_hunger","rotation", "field_of_view"
    ]
    def __init__(self, name="", hp=PLAYER_MAX_HP, x=MAP_WIDTH//2, y=MAP_HEIGHT//2, b_generate_items = True):
        super().__init__(name, hp, x, y)
        self.rotation = 0
        self.field_of_view = 70
        self.name = name
        self.stamina = 100
        self.max_stamina = PLAYER_MAX_STAMINA
        self.hunger = 100
        self.max_hunger = PLAYER_MAX_HUNGER
        self.sprite = "player"
        if b_generate_items: self.generate_initial_items()
    
    def move(self, dx, dy, game_map):
        if self.stamina >= 10:
            moved = game_map.move_character(self, dx, dy)
            if moved:
                self.stamina -= 4
            return moved
        return False
    
    def calculate_damage_done(self):
        damage = 1
        if self.primary_hand and hasattr(self.primary_hand, 'damage'):
            damage += random.uniform(self.primary_hand.damage/3.0, self.primary_hand.damage)
            #print(damage, self.primary_hand.damage)
        return max(1, damage)

    def regenerate_stamina(self):
        self.stamina = min(self.stamina + 3, self.max_stamina) 
        
    def regenerate_health(self):
        self.hp = min(self.hp + 1, self.max_hp) 
    
    def generate_initial_items(self):
        self.equip_item(Sword(name="Bastard_Sword", damage=8.5, durability_factor=0.9995, description="although with no name, this Bastard Sword was master-crafted and passed as heirloom in generations of my family, that swords reminds me of the values my father teach me ..."), "primary_hand")
        self.add_item(Food("Apple", nutrition=50))
        self.add_item(Food("Apple", nutrition=50))
        self.add_item(Food("Apple", nutrition=50))
        self.add_item(Food("Bread", nutrition=100))
    
    def get_forward_direction(self):
        dx = 0
        dy = -1
        rotation_degree = self.rotation
        if rotation_degree == 0:
            return dx, dy
        elif rotation_degree == 90:
            return -dy, dx
        elif rotation_degree == 180:
            return -dx, -dy
        elif rotation_degree == 270:
            return dy, -dx

    # Normalize both vectors
    def _normalize(self, v):
        length = math.hypot(v[0], v[1])
        return (v[0]/length, v[1]/length) if length != 0 else (0, 0)

    def is_in_cone_vision(self,observer, point, direction=(0,-1), fov_deg=180):
        """
        Determines if a point is visible from the observer through a cone of vision.

        Parameters:
        - observer: tuple (x, y) of observer's coordinates
        - point: tuple (x, y) of target point
        - direction: tuple (dx, dy), observer's frontal direction vector
        - fov_deg: field of view in degrees (centered on direction vector)

        Returns:
        - True if the point is within the field of view, False otherwise
        """

        # Compute vector from observer to point
        vec_to_point = (point[0] - observer[0], point[1] - observer[1])
        dir_norm = self._normalize(direction)
        vec_norm = self._normalize(vec_to_point)

        # Compute dot product and angle
        dot = dir_norm[0]*vec_norm[0] + dir_norm[1]*vec_norm[1]
        angle_rad = math.acos(max(min(dot, 1.0), -1.0))  # Clamp dot to avoid domain errors
        angle_deg = math.degrees(angle_rad)

        # Compare with half the field of view
        return angle_deg <= fov_deg / 2.0

    def can_see_character(self, another, game_map):
        if super().can_see_character(another, game_map):
            return self.is_in_cone_vision( (self.x,self.y), (another.x, another.y), self.get_forward_direction(), self.field_of_view )
        return False

    def reset_stats(self):
        super().reset_stats()
        self.stamina = self.max_stamina
        self.hunger = self.max_hunger 

class Enemy(Character):
    __serialize_only__ = Character.__serialize_only__+["type","stance","canSeeCharacter","patrol_direction"]
    def __init__(self, name="", hp=30, x=50, y=50, b_generate_items = True):
        super().__init__(name, hp, x, y)
        self.description = ""
        self.type = "Generic"
        self.stance = "Aggressive"
        self.canSeeCharacter = False
        self.patrol_direction = (random.choice([-1, 1]), 0)
        self.sprite = "enemy"
        if b_generate_items: self.generate_initial_items()
    
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
                        #print(f"Enemy {self.name} attacking player")
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
    
class Prey(Character):
    pass

class Zombie(Enemy):
    __serialize_only__ = Enemy.__serialize_only__
    def __init__(self, name="", hp=40, x=50, y=50, b_generate_items = True):
        super().__init__(name, hp, x, y, b_generate_items)
        self.type = "Zombie"
        self.description = "Zombies, people affected by the plague, they are still alive but because of this strange disease their bodies smells like rotten flesh. Before they lose their minds, they try to acummulate food to satiate hunger, it's almost certain to find food with them ..."
        self.sprite = "zombie"
        
    def calculate_damage_done(self):
        return random.randint(0, 15)

    def generate_initial_items(self):
        if random.random() < 0.7:
            self.add_item(Food("bread", nutrition=random.randint(50, 100)))
        if random.random() < 0.7:
            self.add_item(Food("apple", nutrition=random.randint(5, 15)))

class Rogue(Enemy):
    __serialize_only__ = Enemy.__serialize_only__
    def __init__(self, name="", hp=100 , x=50, y=50, b_generate_items = True):
        super().__init__(name, hp, x, y, b_generate_items)
        self.type = "Rogue"
        self.description = "Rogues and Bandits, they are just robbers, ambushing travellers on the road. Always carry a sword with you ..."
        self.sprite = "rogue"
        
    def calculate_damage_done(self):
        damage = random.randint(0, 8)
        if self.primary_hand and hasattr(self.primary_hand, 'damage'):
            damage += self.primary_hand.damage
        return damage    

    def generate_initial_items(self):
        self.equip_item(Sword("Long_Sword", damage=10), "primary_hand")
        if random.random() < 0.3:
            self.add_item(Food("bread", nutrition=random.randint(50, 100)))

class Mercenary(Rogue):
    __serialize_only__ = Enemy.__serialize_only__
    def __init__(self, name="", hp=130 , x=50, y=50, b_generate_items = True):
        super().__init__(name, hp, x, y, b_generate_items)
        self.type = "Mercenary"
        self.description = "More experienced in combat than rogues, but often doing the same kind of 'job', money before honor ..."
        self.sprite = "mercenary"
        
    def calculate_damage_done(self):
        damage = random.randint(0, 12)
        if self.primary_hand and hasattr(self.primary_hand, 'damage'):
            damage += self.primary_hand.damage
        return damage    

    def generate_initial_items(self):
        self.equip_item(Mace("mace", damage=10), "primary_hand")
        if random.random() < 0.3:
            self.add_item(Food("bread", nutrition=random.randint(50, 100)))
        else:
            self.add_item(Food("meat", nutrition=random.randint(150, 200)))
    
class Bear(Enemy):
    __serialize_only__ = Enemy.__serialize_only__
    def __init__(self, name="", hp=60 , x=50, y=50, b_generate_items = True, dbg_blind=False):
        super().__init__(name, hp, x, y, b_generate_items)
        self.description = "Bears, these woods are their home, stronger than any man, don't try to mess with them ..."
        self.dbg_blind = dbg_blind
        self.sprite = "bear"
    def calculate_damage_done(self):
        return random.randint(5, 30)
    def generate_initial_items(self):
        self.add_item(Food("meat", nutrition=250))
    def can_see_character(self, another, game_map):
        if self.dbg_blind: return False
        return super().can_see_character(another, game_map)
    
class Dear(Prey):
    pass 

# --- mapping
class Tile(Container):
    SPRITES = {}  # Class-level sprite cache
    list_sprites_names = list(SPRITE_NAMES)
    __serialize_only__ = ["items", "walkable", "blocks_sight", "default_sprite_key", "stair", "stair_x", "stair_y", "cosmetic_layer_sprite_keys"]
    def __init__(self, walkable=True, sprite_key="grass"):
        super().__init__()
        self._load_sprites()
        self.walkable = walkable
        self.blocks_sight = not walkable
        # --
        self.default_sprite_key = sprite_key # is the first and last layer sprite 
        self.cosmetic_layer_sprite_keys = [] # to be used as a modifier for default_sprite
        self.combined_sprite = None # is the final sprite rendered 
        # --
        self.current_char = None 
        # -- 
        self.stair = None # used to store a tuple map coord to connect between maps 
        self.stair_x = None # points to the stair tile from the map with coord self.stair
        self.stair_y = None # points to the stair tile from the map with coord self.stair 
        
    def draw(self, scene, x, y, tile_size = TILE_SIZE):
        # BEGIN Painter
        combined = QPixmap(tile_size, tile_size) # will be changed with QPainter 
        combined.fill(Qt.transparent)
        painter = QPainter(combined)
        # -- Base and Cosmetic Layers 
        base = self.get_default_pixmap()
        painter.drawPixmap(0, 0, base)
        for sprite_key in self.cosmetic_layer_sprite_keys:
            painter.drawPixmap(0, 0, Tile.SPRITES.get(sprite_key, base) )
        # -- Char Paint or Item Paint
        if self.current_char:
            self.current_char.paint_to(painter)
        elif self.items:
            if len(self.items) > 1:
                item_sprite = Tile.SPRITES.get("sack", base)
            else:
                item_sprite = Tile.SPRITES.get(self.items[0].sprite, base)
            if not item_sprite.isNull():
                painter.drawPixmap(0, 0, item_sprite)
        # END Painter 
        painter.end()
        self.combined_sprite = combined
        # -- Add to Scene
        item = QGraphicsPixmapItem(self.combined_sprite)
        item.setPos(x, y)
        scene.addItem(item)
        
    def can_place_character(self):
        return self.walkable and (not self.current_char )

    # sprites handling 
    @classmethod
    def _try_load(cls, key):
        # cls.SPRITES will store the sprites in memory 
        try: 
            qpx = QPixmap("./assets/"+key)
            cls.SPRITES[key] = qpx.scaled(TILE_SIZE, TILE_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        except Exception as e:
            print(f"Failed to load sprites: {e}")
            cls.SPRITES[key] = QPixmap()
    
    @classmethod
    def _load_sprites(cls):
        if not cls.SPRITES:
            for key in cls.list_sprites_names: cls._try_load(key)
        
    def get_default_pixmap(self):
        return self.SPRITES.get(self.default_sprite_key, QPixmap())

    def add_cosmetic_sprite(self, sprite_key = None):
        if not sprite_key: return 
        self.cosmetic_layer_sprite_keys.append(sprite_key)

class Room:
    def __init__(self):
        self.positions = [] # (x,y) tuples walkable or not
        self.boundaries = [] # (x,y) tuples non-interior and non-walkable positions
        self.entry = None # tuple 
        self.exit = None # tuple, could be the same .entry 
    def get_iterator(self):
        return self.positions
    def set_tiles_for_positions(self, map_instance, floor_sprite_key = "floor"):
        pass
    def set_tiles_for_boundaries(self, map_instance, wall_sprite_key = "wall"):
        pass 
    def add_random_loot(self, loot_table):
        pass 

class Map(Serializable):
    __serialize_only__ = ["width","height","filename","grid","enemy_type","coords","enemies"]
    def __init__(
            self, 
            filename="default", 
            coords=(0, 0, 0), 
            width=MAP_WIDTH, 
            height=MAP_HEIGHT, 
            b_generate = True, 
            previous_coords = (0,0,0), 
            prev_x = MAP_WIDTH//2, 
            prev_y = MAP_HEIGHT//2, 
            going_up = False
        ):
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
        self.rooms = None # could be tuple (x,y,w,h) of rectangular room of could be a Room instance 
        if b_generate: self.generate()
    
    def from_dict(self, dictionary):
        if not super().from_dict(dictionary):
            return False
        # Place characters after loading grid
        for enemy in self.enemies:
            self.place_character(enemy)
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
        elif self.filename == "procedural_forest":
            self.generate_procedural_forest()
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
    
    # -- fill enemies 
    def generate_enemy_by_chance_at(self, x,y, enemy = Enemy, chance = 1.0, extra_items = None, **kwargs):
        """
        Attempts to spawn an enemy at a given position with a certain probability.

        This method supports both direct class references and string-based enemy names,
        allowing for dynamic, data-driven enemy generation. It optionally equips the enemy
        with items by chance, if specified.

        Args:
            x (int | float): X-coordinate for the enemy spawn position.
            y (int | float): Y-coordinate for the enemy spawn position.
            enemy (type | str): The enemy class to instantiate (e.g., `Zombie` or "Zombie").
                                If a string is provided, the class is looked up in the global scope.
            chance (float): A value between 0.0 and 1.0 representing the spawn probability.
            extra_items (list[dict], optional): A list of item descriptors to attempt adding to
                                                the spawned enemy via `add_item_by_chance`.
                                                Defaults to an empty list.
            **kwargs: Additional keyword arguments passed to the enemy constructor.

        Returns:
            object | None: The created enemy instance if spawned; otherwise, `None`.

        Raises:
            ValueError: If `enemy` is a string that doesn't correspond to a known global class.

        Example:
            >>> self.generate_enemy_by_chance_at(50, 50, **{
            ...     "enemy": "Zombie",
            ...     "chance": 0.9,
            ...     "b_generate_items": True,
            ...     "extra_items": [
            ...         {"item": "WeaponRepairTool", "name": "Whetstone", "uses": 3}
            ...     ]
            ... })
        """
        if isinstance(enemy, str):
            enemy = globals().get(enemy)
            if enemy is None:                
                return None
        if extra_items is None:
            extra_items = [] 
        if d(0.0,1.0) < chance:
            enemy_instance = enemy(x=x, y=y, **kwargs)
            for kw in extra_items:
                enemy_instance.add_item_by_chance(**kw)
            return enemy_instance
        else:
            return None
            
    def generate_enemy_by_chance_by_list_at(self, x,y, enemy_list):
        """
        Attempts to spawn an enemy at a given position from a list of possible enemy configurations.

        This method iterates over a list of enemy definitions (dicts) and passes each to
        `generate_enemy_by_chance_at`. It returns the first successfully spawned enemy,
        or `None` if none were spawned.

        Args:
            x (int | float): X-coordinate for the enemy spawn position.
            y (int | float): Y-coordinate for the enemy spawn position.
            enemy_list (list[dict]): A list of keyword-argument dictionaries. Each dict is a
                                     configuration to pass to `generate_enemy_by_chance_at`.
                                     Must include at least the "enemy" key (class or string name).

        Returns:
            object | None: The first enemy instance successfully spawned based on chance;
                           otherwise, `None`.

        Example:
            >>> self.generate_enemy_by_chance_by_list_at(100, 200, [
            ...     {"enemy": "Skeleton", "chance": 0.3},
            ...     {"enemy": "Zombie", "chance": 0.5, "extra_items": [...]}
            ... ])
        """
        for config in enemy_list:  # Try all but if fails fallback to the last 
            enemy = self.generate_enemy_by_chance_at(x, y, **config)
            if enemy:
                return enemy

        # Fallback: guaranteed spawn
        fallback_config = enemy_list[-1].copy()
        fallback_config["chance"] = 1.0  # force spawn
        return self.generate_enemy_by_chance_at(x, y, **fallback_config)
    
    def generate_enemy_at(self, x,y, enemy_class=None, *args, **kwargs):
        if enemy_class:
            enemy = enemy_class(x=x,y=y,*args, **kwargs)
            self.enemies.append(enemy)
            return self.place_character(enemy)
        coin = random.uniform(0,1)
        enemy = None
        match self.enemy_type:    
            case "dungeon":
                enemy = self.generate_enemy_by_chance_by_list_at(x,y,DUNGEON_ENEMY_TABLE)
            case "deep_forest":
                enemy = self.generate_enemy_by_chance_by_list_at(x,y,FOREST_ENEMY_TABLE)
            case "field":
                enemy = self.generate_enemy_by_chance_by_list_at(x,y,FIELD_ENEMY_TABLE)
            case "default":
                enemy = self.generate_enemy_by_chance_by_list_at(x,y,DEFAULT_ENEMY_TABLE)
            case "road":
                enemy = self.generate_enemy_by_chance_by_list_at(x,y,ROAD_ENEMY_TABLE)
            case "lake":
                enemy = self.generate_enemy_by_chance_by_list_at(x,y,LAKE_ENEMY_TABLE)
            case _:
                enemy = Zombie("Zombie",x=x,y=y,b_generate_items=True)
        if not enemy: return False
        self.enemies.append(enemy)
        return self.place_character(enemy)
        
    def fill_enemies(self, num_enemies=100):
        #print(f"Filling enemies for map {self.current_map}")
        placed = 0
        attempts = 0
        max_attempts = num_enemies * 5
        while placed < num_enemies and attempts < max_attempts:
            x = random.randint(1, self.width - 1)
            y = random.randint(1, self.height - 1)
            tile = self.get_tile(x, y)
            if not tile:
                attempts += 1
                continue
            if tile.current_char or not tile.walkable: 
                attempts += 1
                continue
            if self.generate_enemy_at(x,y): placed += 1
            attempts += 1
        if placed < num_enemies:
            print(f"Warning: Only placed {placed} of {num_enemies} enemies due to limited valid tiles")
        print(f"Added {len(self.enemies)} enemies for map {self.coords}")
        return self.enemies 
    
    # -- procedural generators || generator helpers
    def grid_init_uniform(self, spriteKey = "grass", is_walkable = True, x1 = 0, x2 = None, y1 = 0, y2 = None):
        if not x2: x2 = self.width
        if not y2: y2 = self.height 
        if not self.grid:
            self.grid = [ 
            [ Tile(walkable=is_walkable, sprite_key=spriteKey) 
                for j in range(0,self.height)] 
            for i in range(0,self.width)]
        
        for i in range(x1,x2):
            for j in range(y1,y2):
                self.grid[i][j] = Tile(walkable=is_walkable, sprite_key=spriteKey)
    
    def add_rectangle(self, center_x, center_y, width, height, has_entry = True, sprite_border="wall", sprite_floor="floor"):
        """ Generate a room with one floor-tile entry only changing his limits """
        pass
    
    def add_L_shaped_connectors(self, sprite_corridor_floor = "dirt"):
        # Connect rooms with L-shaped corridors
        for i in range(len(self.rooms) - 1):
            x1, y1 = self.rooms[i][0] + self.rooms[i][2] // 2, self.rooms[i][1] + self.rooms[i][3] // 2
            x2, y2 = self.rooms[i + 1][0] + self.rooms[i + 1][2] // 2, self.rooms[i + 1][1] + self.rooms[i + 1][3] // 2
            if random.choice([True, False]):
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    self.grid[y1][x] = Tile(walkable=True, sprite_key=sprite_corridor_floor)
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    self.grid[y][x2] = Tile(walkable=True, sprite_key=sprite_corridor_floor)
            else:
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    self.grid[y][x1] = Tile(walkable=True, sprite_key=sprite_corridor_floor)
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    self.grid[y2][x] = Tile(walkable=True, sprite_key=sprite_corridor_floor)
    
    def add_rooms(self, num_rooms = random.randint(8, 15)):
        # Generate rooms () || & Generate Enough Rooms || $ (bool) Check if Overlaps | % not overlap || Add Room 
        # Generate rooms () || & Generate Enough Rooms || $ (bool) Check if Overlaps || Set overlap false | & x,y,w,h : over other rooms || % Overlaps || Set overlap true | break 
        self.rooms = []
        max_attempts = num_rooms * 10
        attempts = 0
        while len(self.rooms) < num_rooms and attempts < max_attempts:
            room_w = random.randint(5, 10)
            room_h = random.randint(5, 10)
            room_x = random.randint(1, self.width - room_w - 1)
            room_y = random.randint(1, self.height - room_h - 1)
            overlap = False
            for other_x, other_y, other_w, other_h in self.rooms:
                if (room_x < other_x + other_w + 2 and
                    room_x + room_w + 2 > other_x and
                    room_y < other_y + other_h + 2 and
                    room_y + room_h + 2 > other_y):
                    overlap = True
                    break
            if not overlap: self.rooms.append((room_x, room_y, room_w, room_h))
            attempts += 1
        if not self.rooms:
            raise RuntimeError("Failed to generate any rooms for dungeon")
    
    def add_rooms_with_connectors(self, sprite_floor = "floor", sprite_corridor_floor = "dirt"):
        self.add_rooms()
        self.add_L_shaped_connectors(sprite_corridor_floor = sprite_corridor_floor)            
        self.repaint_floor_rooms(sprite_floor)
        
    def foreach_rooms_tiles(self, f_lambda = lambda tile,i,j: print((i,j)), *args, **kwargs):
        """
        Applies a function to each tile within all defined rooms.

        Iterates through each room in `self.rooms`, treating the room as a rectangle
        defined by (x, y, w, h). For every tile (i, j) inside the room, the specified
        `f_lambda` function is called with the tile object and its coordinates.

        The iteration behavior can be altered based on the return value of `f_lambda`:
        - If `f_lambda` returns `None`, iteration continues.
        - If `f_lambda` returns `True`, the current room's tile loop breaks.
        - If `f_lambda` returns any other value, the method immediately returns that value.

        Args:
            f_lambda (Callable): A lambda or function that accepts the form `f(tile, i, j, *args, **kwargs)`.
                Defaults to printing the tile coordinates.
            *args: Additional positional arguments passed to `f_lambda`.
            **kwargs: Additional keyword arguments passed to `f_lambda`.

        Returns:
            Any: If `f_lambda` returns a non-None and non-True value, it is immediately returned.
            Otherwise, returns `None`.

        Example:
            def mark_tile(tile, i, j):
                tile.marked = True

            map.foreach_rooms_tiles(mark_tile)

        Note:
            Make sure `self.rooms` is a list of 4-tuples `(x, y, w, h)`.
            `self.get_tile(x, y)` must return a tile object.
        """
        if not self.rooms: return None 
        for x,y,w,h in self.rooms:
            for i,j in product(range(x,x+w), range(y,y+h)):            
                tile = self.get_tile(i,j)
                result = f_lambda(tile, i,j,*args, *kwargs)
                if result == None:
                    continue
                else:
                    if result == True:
                        break
                    else:
                        return result
        return None

    def repaint_floor_rooms(self, sprite = "floor"):
        def inner_function(tile,i,j):
            if not tile: return None
            if tile.stair: return None
            self.set_tile(i,j,Tile(walkable=True, sprite_key=sprite))
            return None
        self.foreach_rooms_tiles(inner_function)

    def get_random_tile_from_rooms(self):
        return GetRandomTile_Reservoir_Sampling( self, Map.foreach_rooms_tiles )

    def get_random_tiles_from_rooms(self, k=20):
        return GetRandomTiles_Reservoir_Sampling( self, Map.foreach_rooms_tiles, k=k )

    def add_patches(self, spriteKey = "dirt", is_walkable = True, scale = 0.1):
        # Generate dirt patches using Perlin noise or random clusters
        for i in range(self.width):
            for j in range(self.height):
                noise_value = noise.snoise2(i * scale, j * scale, octaves=1)  # Adjust scale (0.1) for patch size
                if noise_value > 0.2:  # Threshold for dirt
                    self.grid[i][j] = Tile(walkable=is_walkable, sprite_key=spriteKey)
                    
    def add_dungeon_loot(self, k=20):
        # -> add_dungeon_loot () || $ Sample | & (Tile) X : Sample || Random Choice in Loot Table || Add to X the Loot 
        Sampled_Tiles = self.get_random_tiles_from_rooms(k=k)
        for tile in Sampled_Tiles:
            LootKwargs = random.choice(LOOT_TABLE)
            tile[0].add_item_by_chance(**LootKwargs)
    
    def add_trees(self):
        # Add trees with slight clustering
        for i in range(1, self.width-1):
            for j in range(1, self.height-1):
                # Base chance for a tree
                tree_chance = 0.15
                # Increase chance if neighboring tiles have trees (clustering)
                for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    if 0 <= i + di < 100 and 0 <= j + dj < 100:
                        if self.grid[i + di][j + dj].default_sprite_key == "tree":
                            tree_chance += 0.1
                if random.random() < tree_chance:
                    self.grid[i][j] = Tile(walkable=False, sprite_key="tree")
    
    def add_rocks(self, spriteKey = "rock", is_walkable=False):
        for i in range(1, self.width-1):
            for j in range(1, self.height-1):
                if random.random() < 0.001:  # 2% chance for water
                    self.grid[i][j] = Tile(walkable=False, sprite_key="water")
                elif random.random() < 0.05:  # 5% chance for rocks
                    self.grid[i][j] = Tile(walkable=is_walkable, sprite_key=spriteKey)
                    
    def is_adjacent_walkable(self,tile, x,y):
        for dx,dy in CROSS_DIFF_MOVES:
            tile_2 = self.get_tile(x+dx,y+dy)
            if tile_2:
                if not tile_2.walkable: return False
        return True
    
    def get_random_walkable_tile(self, border_factor = 0.0):
        dx = int(border_factor*self.width)
        dy = int(border_factor*self.height)
        walkable_tiles = [(i, j) for j in range(dy,self.height-dy) for i in range(dx,self.width-dx) if self.is_adjacent_walkable(self.grid[i][j],i,j) ]
        if not walkable_tiles: return None
        return random.choice(walkable_tiles)
    
    def add_dungeon_entrance(self, probability = 1.0, border_factor = 0.0):
        coin = random.random()
        if coin > probability: return False
        xy = self.get_random_walkable_tile(border_factor = border_factor)
        if not xy: return False
        entrance_x = xy[0]
        entrance_y = xy[1]
        target_map = (self.coords[0], self.coords[1], -1)
        self.grid[entrance_y][entrance_x] = Tile(walkable=True, sprite_key="dungeon_entrance")
        self.grid[entrance_y][entrance_x].stair = target_map
        self.grid[entrance_y][entrance_x].stair_x = entrance_x
        self.grid[entrance_y][entrance_x].stair_y = entrance_y
        print(f"Placed dungeon_entrance at ({entrance_x}, {entrance_y}) linking to {target_map}")
        return True

    def add_dungeon_entrance_at(self,x,y):
        current_x, current_y, current_z = self.coords
        target_map = (current_x, current_y, current_z - 1)
        tile = self.get_tile(x, y)
        if tile:
            # Remove any existing character or items to simplify
            char_ = tile.current_char
            tile.current_char = None  # Temporarily remove
            tile.items.clear()
            # Set stair properties
            tile.walkable = True
            tile.default_sprite_key = "dungeon_entrance"
            tile.get_default_pixmap()
            tile.stair = target_map
            # Place player back
            if char_:
                tile.current_char = char_
                char_.current_tile = tile
            # Save the map to persist the stair
            saves_dir = "./saves"
            map_file = os.path.join(saves_dir, f"map_{'_'.join(map(str, self.coords))}_1.json")
            self.Save_JSON(map_file)
            return True
        return False

    def carve_corridor(self, x1, y1, x2, y2, sprite_key="dirt"):
        if random.choice([True, False]):
            for x in range(min(x1, x2), max(x1, x2) + 1):
                self.grid[y1][x] = Tile(walkable=True, sprite_key=sprite_key)
            for y in range(min(y1, y2), max(y1, y2) + 1):
                self.grid[y][x2] = Tile(walkable=True, sprite_key=sprite_key)
        else:
            for y in range(min(y1, y2), max(y1, y2) + 1):
                self.grid[y][x1] = Tile(walkable=True, sprite_key=sprite_key)
            for x in range(min(x1, x2), max(x1, x2) + 1):
                self.grid[y2][x] = Tile(walkable=True, sprite_key=sprite_key)
                
    def ensure_connection(self, target_points = None):
        if not self.rooms:
            print("No rooms to connect entrance.")
            return
        if not target_points:
            target_points = [
                (x, 0) for x in range(self.width) if self.grid[0][x].walkable  # Top edge
            ] + [
                (x, self.height - 1) for x in range(self.width) if self.grid[self.height - 1][x].walkable  # Bottom edge
            ] + [
                (0, y) for y in range(self.height) if self.grid[y][0].walkable  # Left edge
            ] + [
                (self.width - 1, y) for y in range(self.height) if self.grid[y][self.width - 1].walkable  # Right edge
            ]

        def distance(p1, p2):
            return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

        # Pick the center of the room closest to the map edge
        room_centers = [(rx + rw // 2, ry + rh // 2) for (rx, ry, rw, rh) in self.rooms]
        closest_pair = None
        min_dist = float("inf")
        for center in room_centers:
            for edge in target_points:
                d = distance(center, edge)
                if d < min_dist:
                    min_dist = d
                    closest_pair = (center, edge)

        if closest_pair:
            (cx, cy), (ex, ey) = closest_pair
            self.carve_corridor(cx, cy, ex, ey, sprite_key="dirt")
            
    # -- procedural generators || full map generator
    def _generate_default(self):
        # inner floors, random trees
        self.enemy_type = "default"
        self.grid_init_uniform()
        self.add_patches()
        self.add_trees()
        self.add_rocks()

    def generate_procedural_forest(self):
        self.enemy_type = "deep_forest"
        # initialize grid
        self.grid_init_uniform("grass",True)
        self.grid_init_uniform("tree", False,x1 = 1, x2 = self.width-1, y1 = 1, y2=self.height-1)
        self.add_rooms_with_connectors("grass","dirt")
        self.add_patches(scale = 0.4)
        self.ensure_connection()  # <--- Here!
        self.add_dungeon_loot(k=10)

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

        # initialize grid
        self.grid_init_uniform("wall",False)
        self.add_rooms_with_connectors("floor","dirt")
        
        # Choose starting point (stair_up or stair_down to previous map)
        start_room = random.choice(self.rooms)
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
            available_rooms = [(rx, ry, rw, rh) for rx, ry, rw, rh in self.rooms
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
        #self.ensure_connection([(new_x,new_y)])
        self.add_dungeon_loot()
        return new_x, new_y, new_z
    
    def generate_procedural_field(self):
        self.enemy_type = "field"
        self.grid_init_uniform("grass",True)
        self.add_patches()
        self.add_rocks()
        for i in range(self.width-1):
            for j in range(self.height-1):
                n = noise.pnoise2(i * 0.1, j * 0.1, octaves=1, persistence=0.5, lacunarity=2.0)
                if n > 0.2:
                    self.grid[i][j] = Tile(walkable=False, sprite_key="tree")
                elif random.random() < 0.01:
                    self.grid[i][j].add_item(Food("Apple", nutrition=10))
                    
    def generate_procedural_road(self):
        self.enemy_type = "road"
        self.grid_init_uniform("grass",True)
        self.add_patches()
        # Vertical road with noise
        road_x = self.width//2
        for y in range(self.width):
            offset = int(noise.pnoise1(y * 0.1, octaves=1, persistence=0.5, lacunarity=2.0) * 10)
            road_x += offset
            road_x = max(1, min(self.width-2, road_x))
            self.grid[y][road_x] = Tile(walkable=True, sprite_key="grass")
            if random.random() < 0.05:
                self.grid[y][road_x].add_item(Food("Bread", nutrition=15))
        for i in range(self.height):
            for j in range(self.height):
                if random.random() < 0.1 and abs(j - road_x) > 2:
                    self.grid[i][j] = Tile(walkable=False, sprite_key="tree")
    
    def generate_procedural_lake(self):
        self.enemy_type = "lake"
        self.grid_init_uniform("grass", True)
        self.add_patches()
        center_x, center_y = self.width//2, self.height//2
        for i in range(self.width-1):
            for j in range(self.height-1):
                n = noise.pnoise2(i * 0.05, j * 0.05, octaves=1, persistence=0.5, lacunarity=2.0)
                dist = ((i - center_x) ** 2 + (j - center_y) ** 2) ** 0.5
                if n > -0.1 and dist < 30:
                    self.grid[i][j] = Tile(walkable=False, sprite_key="water")
                elif random.random() < 0.1:
                    self.grid[i][j] = Tile(walkable=False, sprite_key="tree")
                elif random.random() < 0.001:
                    self.grid[i][j].add_item(Food("Fish", nutrition=80))
                elif random.random() < 0.0005:
                    self.grid[i][j].add_item(WeaponRepairTool("Whetstone", uses=10))
        self.add_dungeon_entrance()
                    
    # -- methods 
    def get_tile(self, x, y):
        try:
            if 0 <= y < len(self.grid) and 0 <= x < len(self.grid[0]):
                return self.grid[y][x]
            return None
        except Exception as e:
            print(f"Error accessing tile ({x}, {y}): {e}")
            return None

    def set_tile(self, x, y, tile):
        self.grid[y][x] = tile

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
        if not (0 <= start_x < self.width and 0 <= start_y < self.height and 0 <= goal_x < self.width and 0 <= goal_y < self.height):
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
                if not (0 <= next_x < self.width and 0 <= next_y < self.height):
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

    def _get_sprite_key(self, tile):
        """Return the sprite key for a tile's default_sprite."""
        for key, sprite in Tile.SPRITES.items():
            if tile.default_sprite == sprite:
                return key
        return "grass"  # Fallback if no match found    

    def line_of_sight(self, x1, y1, x2, y2):
        """
        Determines whether there is a clear line of sight between two points on a grid.

        This method uses Bresenham's Line Algorithm to trace a line from the start point
        (x1, y1) to the end point (x2, y2). It checks each tile along the line to determine 
        if any of them block sight. If a tile that blocks sight is encountered, the function 
        returns False, indicating the line of sight is blocked. If the entire path is clear, 
        it returns True.

        Parameters
        ----------
        x1 : int
            X-coordinate of the starting point.
        y1 : int
            Y-coordinate of the starting point.
        x2 : int
            X-coordinate of the ending point.
        y2 : int
            Y-coordinate of the ending point.

        Returns
        -------
        bool
            True if the line of sight is clear, False if it is blocked by any tile.

        Notes
        -----
        - Assumes that `self.get_tile(x, y)` returns a tile object with a `blocks_sight` attribute.
        - Diagonal movement and horizontal/vertical lines are supported.
        - This method does not check the visibility rules related to field of view or distance,
          only direct line obstruction.
        """
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

# Town Management 
class Town:
    def __init__(self, coords):
        self.coords = coords 
        self.food = 0
        self.wood = 0
        self.stone = 0
        self.metal = 0
        self.raid_interval = 30 # 30 days 
        self.villagers = 0 

# --- END 