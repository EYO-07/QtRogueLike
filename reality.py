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
from PyQt5.QtWidgets import QGraphicsPixmapItem, QInputDialog
import noise  # Use python-perlin-noise instead of pynoise

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

class Tool(Equippable):
    pass 
    
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
    __serialize_only__ = Equippable.__serialize_only__+["defense_factor"]
    def __init__(self, name="", defense_factor=0.02, description="", weight=1, slot="torso"):
        super().__init__(name, description, weight, slot)
        self.defense_factor = defense_factor

class Shield(Equippable):
    pass

# --- living

# SANITY COMMENTS:
# 1. b_generate_items must be False by default, otherwise the Serializable will generate initial items whenever they use Load_JSON 

class Character(Container, Entity2D):
    __serialize_only__ = ["name", "hp", "max_hp", "x", "y", "primary_hand", "secondary_hand", "head", "neck", "torso", "waist", "legs", "foot", "items", "sprite"]
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
        self.sprite = "player"
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
        
    def generate_initial_items(self):
        pass    

    def turn_update(self, game_turns_counter): # unused 
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
    
class Player(Character): # could be the actual player or a playable npc 
    __serialize_only__ = Character.__serialize_only__+[
        "stamina","max_stamina","hunger","max_hunger","rotation", "field_of_view", "current_map","days_survived", "party"
    ]
    def __init__(self, name="", hp=PLAYER_MAX_HP, x=MAP_WIDTH//2, y=MAP_HEIGHT//2, b_generate_items = False, sprite = "player", current_map = (0,0,0)):
        super().__init__(name, hp, x, y)
        self.rotation = 0
        self.field_of_view = 70
        self.name = name
        self.stamina = 100
        self.max_stamina = PLAYER_MAX_STAMINA
        self.hunger = 100
        self.max_hunger = PLAYER_MAX_HUNGER
        self.sprite = sprite
        self.current_map = current_map
        self.days_survived = 0
        self.party = False # {} # can put heroes or helping npcs 
        if b_generate_items: self.generate_initial_items()
    
    # -- 
    # def add_to_party(self, char, game_instance):
        # if len(char.party) > 0: 
            # print("Can't nest parties ...")
            # return 
        # game_instance.remove_player(char.name)
        # self.party.update({char.name : char})
        
    # def remove_from_party(self,key, game_instance):
        # char = self.party.get(key, None)
        # if char:
            # self.party.pop(key)
            # game_instance.players.update( {} )
    
    # def set_map_coords(self, coords):
        # self.current_map = coords
        # for k,v in iter(self.party.items()):
            # if v:
                # v.current_map = coords 
                
    # def release_party(self): # used to remove members for self.party, must be called whenever the player is close to death 
        # pass 
    
    # --
    def move(self, dx, dy, game_map):
        if self.stamina >= 10:
            moved = game_map.move_character(self, dx, dy)
            if moved:
                self.stamina -= 4
            return moved
        return False
        
    def npc_move(self, dx, dy, game_map):
        return super().move(dx, dy, game_map)
    
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

    def calculate_defense_factor(self):
        S = 0
        for df in EQUIPMENT_SLOTS:
            df_item = getattr(self, df, None)
            if df_item:
                if hasattr(df_item, "defense_factor"):
                    S += df_item.defense_factor
        return S 

    def is_rendered_on_map(self, game_map): 
        tile = game_map.get_tile(self.x, self.y)
        if not tile: return False 
        return tile.current_char is self 
        
    def is_placed_on_map(self, game_map):
        tile = game_map.get_tile(self.x, self.y)
        if not tile: return False 
        return (tile.current_char is self) and (self.current_tile is tile) 

    def update(self, game_instance): # on turn 
        self.regenerate_stamina()
        self.regenerate_health()
        self.hunger = max(0, self.hunger - 0.5)  # Hunger decreases each turn
        # Check for special events and set flags 
        if self.hp / self.max_hp < 0.2:
            game_instance.low_hp_triggered = True
        if self.hunger / self.max_hunger < 0.1:
            game_instance.low_hunger_triggered = True    
        if self.hunger <= 0: # starvation 
            self.hp = max(0, self.hp - 1)  # Starvation damage
            if self.hp <= 0:
                game_instance.add_message("Game Over: Starvation! Reloading last save...")
                game_instance.Event_PlayerDeath()
                return    

    def npc_update(self, game_instance):
        if self.current_map != game_instance.map.coords: return 
        self.regenerate_stamina()
        self.regenerate_health()
        # get closest enemy 
        enemy = None
        distance = None
        if len(game_instance.map.enemies)>0:
            enemy = game_instance.map.enemies[0]
            distance = abs(enemy.x - self.x) + abs(enemy.y - self.y)
            for v in game_instance.map.enemies:
                if not v.current_tile: continue
                tile = game_instance.map.get_tile(v.x,v.y)
                if not tile: continue
                if not tile.current_char is v: continue 
                new_distance = abs(self.x - v.x) + abs(self.y - v.y)
                if new_distance < distance:
                    enemy = v
                    distance = new_distance
        if enemy and distance and distance <= 2:
            path = game_instance.map.find_path(self.x, self.y, enemy.x, enemy.y)
            #print(path)
            if path:
                next_x, next_y = path[0]
                dx, dy = next_x - self.x, next_y - self.y
                tile = game_instance.map.get_tile(next_x, next_y)
                if tile:
                    if tile.walkable and not tile.current_char:
                        if self.move(dx, dy, game_instance.map):
                            pass #print(f"Enemy {self.name} moved to ({self.x}, {self.y}) via pathfinding")
                    elif tile.current_char is enemy:
                        game_instance.events.append(AttackEvent(self, enemy, self.calculate_damage_done()))
                        #print(f"NPC {self.name} attacking enemy")
        else:
            # Random movement
            if self.current_map != game_instance.current_map: 
                print(self, "not in the map")
                return 
            if random.random() < 0.05:
                dx, dy = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)])
                target_x, target_y = self.x + dx, self.y + dy
                tile = game_instance.map.get_tile(target_x, target_y)
                if tile:
                    #print(f"Random move to ({target_x}, {target_y}): walkable={tile.walkable}, occupied={tile.current_char is not None}")
                    if tile.walkable and not tile.current_char:
                        if self.npc_move(dx, dy, game_instance.map):
                            pass #print(f"Enemy {self.name} randomly moved to ({self.x}, {self.y})")
                        else:
                            pass #print(f"Enemy {self.name} failed to randomly move to ({target_x}, {target_y})")
                else:
                    pass #print(f"Invalid random move tile ({target_x}, {target_y})")

class Enemy(Character):
    __serialize_only__ = Character.__serialize_only__+["type","stance","canSeeCharacter","patrol_direction"]
    def __init__(self, name="", hp=30, x=50, y=50, b_generate_items = False):
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
    def __init__(self, name="", hp=40, x=50, y=50, b_generate_items = False):
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
    def __init__(self, name="", hp=100 , x=50, y=50, b_generate_items = False):
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
    def __init__(self, name="", hp=130 , x=50, y=50, b_generate_items = False):
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
    def __init__(self, name="", hp=60 , x=50, y=50, b_generate_items = False, dbg_blind=False):
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

# --- tile
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
    
    def add_layer(self, sprite_key):
        self.cosmetic_layer_sprite_keys.append( sprite_key )
    def remove_layer(self, sprite_key = None):
        if not sprite_key: 
            self.cosmetic_layer_sprite_keys.clear()
            return 
        self.cosmetic_layer_sprite_keys.remove( sprite_key )
        
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

class ActionTile(Tile): # tile which the player can interact - interface class
    def __init__(self, front_sprite, walkable=True, sprite_key="grass"):
        super().__init__(walkable=walkable, sprite_key=sprite_key)
        self.add_layer( front_sprite )

class Stair(ActionTile): # not used yet 
    pass 
    
class TileBuilding(ActionTile): # interface class
    __serialize_only__ = Tile.__serialize_only__ + ["villagers", "villagers_max", "food", "stone", "metal"]
    def __init__(self, front_sprite, walkable=True, sprite_key="grass"):
        super().__init__( front_sprite = front_sprite, walkable=walkable, sprite_key=sprite_key )
        self.villagers = 0 
        self.villagers_max = 100
        self.food = 0
        self.wood = 0
        self.stone = 0
        self.metal = 0
    def production(self):
        self.villagers = min( 1.05*self.villagers, self.villagers_max )
    def consumption(self):
        self.food = max( self.food - self.villagers, 0 )
        self.wood = max( self.wood - d(0,self.villagers), 0 )
        self.stone = max( self.stone - d(0,self.villagers), 0 )
        self.metal = max( self.metal - d(0,self.villagers), 0 )
    def update(self):
        self.production()
        self.consumption()
        
class Castle(TileBuilding):
    __serialize_only__ = TileBuilding.__serialize_only__ + ["name","heroes","num_heroes"]
    def __init__(self, name = "Home"):
        super().__init__(front_sprite = "castle", walkable=True, sprite_key="grass")
        self.name = name 
        self.heroes = {}
        self.num_heroes = 0
        self.menu_list = []
    def action(self):
        self.update_menu_list()
        def f(current_menu, current_item, menu_instance, game_instance):
            self.update_menu_list(menu_instance)
            menu_instance.add_list("Garrison-", self.heroes)
            foods = { f"{e.name} : {e.nutrition}" : e for e in game_instance.player.items if isinstance(e, Food) }
            menu_instance.add_list("Food+", list(foods.keys()) )
            if current_item == "Exit": menu_instance.close()
            if current_item == "New Hero (2000 Food)":
                if self.food >= 2000:
                    if self.new_npc(game_instance):
                        self.num_heroes += 1
                        self.food -= 2000 
                else:
                    game_instance.add_message("Can't afford to purchase new heroes ...")
                menu_instance.close()
            if current_item == "Garrison+":
                if len(game_instance.players) > 1: 
                    self.heroes.update({ game_instance.player.name : game_instance.player})
                    game_instance.remove_player()
                    game_instance.place_players()
                    game_instance.draw()
                    menu_instance.close()
            if current_item == "Garrison-":
                if len( list( self.heroes.keys()) )>0:
                    menu_instance.set_list("Garrison-")
            if current_menu == "Garrison-":
                if current_item:
                    hero = self.heroes.get(current_item)
                    if not hero: 
                        menu_instance.close()
                        return 
                    dx, dy = game_instance.player.get_forward_direction()
                    player = game_instance.player 
                    spawn_tile = game_instance.map.get_tile(player.x+dx, player.y + dy)
                    if not spawn_tile:
                        game_instance.add_message("Can't generate player at this position, please rotate the current character")
                        menu_instance.close()
                        return 
                    if spawn_tile.current_char:
                        game_instance.add_message("Can't generate player at this position, please rotate the current character")
                        menu_instance.close()
                        return 
                    hero.x = player.x+dx
                    hero.y = player.y + dy
                    game_instance.players.update({current_item: self.heroes.pop(current_item)})
                    # game_instance.set_player(current_item)
                    game_instance.place_players()
                    game_instance.draw()
                    menu_instance.close()
            if current_item == "Food+": 
                if len(foods) >0:
                    menu_instance.set_list("Food+")
            if current_item == "Food-":
                if self.food >= 100:
                    self.food -= 100
                    game_instance.player.add_item(Food(name = "bread", nutrition = 100))
                    game_instance.update_inv_window()
                    menu_instance.close()
            if current_menu == "Food+":
                self.food += foods[current_item].nutrition 
                game_instance.player.remove_item(foods[current_item])
                game_instance.update_inv_window()
                menu_instance.close()
        return f
    def update_menu_list(self, selection_box_instance = None):
        self.menu_list.clear()
        self.menu_list += [
            f"Castle [{self.name}]",
            f"-> heroes: {len(self.heroes)}",
            f"-> food: {self.food:.0f}",
            "New Hero (2000 Food)",
            "Garrison+",
            "Garrison-",
            "Food+",
            "Food-",
            "Exit"
        ]
    def new_npc(self, game_instance):
        dx, dy = game_instance.player.get_forward_direction()
        player = game_instance.player 
        spawn_tile = game_instance.map.get_tile(player.x+dx, player.y + dy)
        if not spawn_tile:
            game_instance.add_message("Can't generate player at this position, please rotate the current character")
            return False
        if spawn_tile.current_char:
            game_instance.add_message("Can't generate player at this position, please rotate the current character")
            return False
        new_name = QInputDialog.getText(game_instance, 'Input Dialog', 'Character Name :')
        if new_name:
            npc_name = new_name[0]
        if not npc_name:
            npc_name = "NPC_"+str(random.randint(0,9))+str(random.randint(0,9))+str(random.randint(0,9))+str(random.randint(0,9))+str(random.randint(0,9))
        game_instance.add_player(
            key = npc_name, 
            name = npc_name, 
            x = game_instance.player.x+dx, 
            y = game_instance.player.y+dy, 
            b_generate_items = False, 
            current_map = game_instance.current_map,
            sprite = random.choice(SPRITE_NAMES_PLAYABLES)
        )
        game_instance.place_players()
        game_instance.dirty_tiles.add((game_instance.player.x+dx, game_instance.player.y+dy))
        game_instance.draw()
        return True
    
    @classmethod
    def new(cls, game_instance, x = None,y = None):
        if not x: x = game_instance.player.x
        if not y: y = game_instance.player.y
        obj = Castle()
        obj.food = 2000 
        game_instance.map.set_tile(x, y, obj)
        game_instance.map.buildings.add(obj)
        game_instance.draw()
        
class Mill(TileBuilding):
    __serialize_only__ = TileBuilding.__serialize_only__ + ["name"]
    def __init__(self, name = "Farm"):
        super().__init__(front_sprite = "mill", walkable=True, sprite_key="grass")
        self.name = name 
        self.menu_list = []
        self.food = d(500,2000)
    def action(self):
        self.update_menu_list()
        def f(current_menu, current_item, menu_instance, game_instance):
            self.update_menu_list(menu_instance)
            if current_item == "Exit": menu_instance.close()
            if current_item == "Food-":
                if self.food >= 500:
                    self.food -= 500
                    game_instance.player.add_item(Food(name = "meat", nutrition = 500))
                    game_instance.update_inv_window()
                    menu_instance.close()
        return f
    def update_menu_list(self, selection_box_instance = None):
        self.menu_list.clear()
        self.menu_list += [
            f"Resource [{self.name}]",
            f"-> food: {self.food:.0f}",
            "Food-",
            "Exit"
        ]

class LumberMill(TileBuilding):
    __serialize_only__ = TileBuilding.__serialize_only__ + ["name"]
    def __init__(self, name = "Lumber Mill"):
        super().__init__(front_sprite = "lumber_mill", walkable=True, sprite_key="grass")
        self.name = name 
        self.menu_list = []
        self.wood = d(500,2000)
    def action(self):
        self.update_menu_list()
        def f(current_menu, current_item, menu_instance, game_instance):
            self.update_menu_list(menu_instance)
            if current_item == "Exit": menu_instance.close()
            if current_item == "Wood-":
                if self.wood >= 500:
                    #self.wood -= 500
                    #game_instance.player.add_item(Food(name = "meat", nutrition = 500))
                    #game_instance.update_inv_window()
                    menu_instance.close()
        return f
    def update_menu_list(self, selection_box_instance = None):
        self.menu_list.clear()
        self.menu_list += [
            f"Resource [{self.name}]",
            f"-> wood: {self.wood:.0f}",
            "Wood-",
            "Exit"
        ]

# --- END 