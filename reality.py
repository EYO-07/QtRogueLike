# reality.py 

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

# TRANSPARENT_IMAGE = 0 # QPixmap(TILE_SIZE,TILE_SIZE)

def is_enemy_of(char1, char2):
    if isinstance(char1, Player) and isinstance(char2, Player): return False 
    if isinstance(char1, Enemy) and isinstance(char2, Enemy): return False 
    if isinstance(char1, Player) and isinstance(char2, Enemy): return True 
    if isinstance(char1, Enemy) and isinstance(char2, Player): return True 
    return False 

# SANITY COMMENTS
# 1. Entity.get_tile don't means that the Entity is properly placed at 

# Entity.paint_to() || { Entity.get_sprite() } || {}
class Entity: # Interface : distance and painting on tile 
    """ Has a paint_to method which is used by the Tile.draw to paint the entity over the tile sprite. """
    __serialize_only__ = ["sprite", "x", "y"] # not a serializable yet 
    def __init__(self):
        self.sprite = None
        self.x = 0
        self.y = 0
        self.current_tile = None # don't serialize this, avoid infinite saving 
    def get_sprite(self):
        TRANSPARENT_IMAGE = QPixmap(TILE_SIZE,TILE_SIZE)
        TRANSPARENT_IMAGE.fill(Qt.transparent)
        if not self.sprite: 
            print(f"Warning: {self} sprite not found")
            return TRANSPARENT_IMAGE 
        try:
            return Tile.SPRITES[self.sprite]
        except KeyError:
            print(f"Warning: {self} sprite not found")
            return TRANSPARENT_IMAGE # Fallback    
    def paint_to(self, painter):
        painter.drawPixmap(0, 0, self.get_sprite())
    def distance(self, entity):
        return abs(entity.x - self.x) + abs(entity.y - self.y)
    def get_tile(self, map):
        return map.get_tile(x,y)
    def place(self, map):
        if map.can_place_character_at(self.x, self.y):
            map.place_character(self)
        else:
            return False
    
# Resource.store() || { Resource.get_value() | Resource.update_value() } || {}
class Resource: # Interface : store in buildings
    """ Interface for items that can be stored on buildings as a resources. """
    __serialize_only__ = ["value", "type"] # this class isn't Serializable, but the derived classes would be 
    def __init__(self):
        self.value = 0
        self.type = None 
    def get_value(self): # || { .update_value() }
        self.update_value()
        return self.value 
    def update_value(self):
        pass 
    def store(self, char, tile_building):
        old_val = getattr(tile_building,self.type, 0.0)
        setattr(tile_building, self.type, old_val + self.get_value())
        char.remove_item(self)
    def get_utility_info(self):
        return f"{self.get_value()} [value]"

# SpecialSkillWeapon.consumption() || { SpecialSkillWeapon.get_equipped_slot() } || {}
# SpecialSkillWeapon.special_attack() || { SpecialSkillWeapon.consumption() | SpecialSkillWeapon.damage() | Character.drop_on_death() } || { SpecialSkillWeapon.get_equipped_slot() }
# SpecialSkillWeapon.use_thrust_special() || { Character.get_forward_direction() } || {}
# SpecialSkillWeapon.use_knight_special() || { SpecialSkillWeapon.special_attack() | Character.get_forward_direction() } || { SpecialSkillWeapon.consumption(), SpecialSkillWeapon.damage(), Character.drop_on_death() }
# SpecialSkillWeapon.use_tower_special() || { SpecialSkillWeapon.special_attack() | Character.get_forward_direction() } || { SpecialSkillWeapon.consumption(), SpecialSkillWeapon.damage(), Character.drop_on_death() }
# SpecialSkillWeapon.use_special_F() || { SpecialSkillWeapon.use_knight_special() | SpecialSkillWeapon.use_tower_special() } || { SpecialSkillWeapon.special_attack(), Character.get_forward_direction() }
# SpecialSkillWeapon.use_special_End() || { SpecialSkillWeapon.use_thrust_special() } || { Character.get_forward_direction() } 
class SpecialSkillWeapon: # Interface : use special skills 
    def __init__(self):
        pass 
    def consumption(self, char, type): 
        """ return True if the special knight attack can proceed """
        if not isinstance(self, Equippable): return False 
        slot = self.get_equipped_slot(char)
        if not slot: return False 
        match type:
            case "knight":
                if char.stamina < char.max_stamina/3: return False
                char.stamina = char.stamina - char.max_stamina/3
                self.damage = max(0,self.damage*self.durability_factor*self.durability_factor)
                if self.damage < 0.5: char.set_equipment_by_slot(None, slot) # garbaging 
                return True 
            case "tower":
                if char.stamina < char.max_stamina/3: return False
                char.stamina = char.stamina - char.max_stamina/3
                self.damage = max(0,self.damage*self.durability_factor*self.durability_factor)
                if self.damage < 0.5: char.set_equipment_by_slot(None, slot) # garbaging 
                return True 
        return True
    def calc_damage(self, type):
        if type == "knight": return d(self.max_damage,3*self.max_damage)
        if type == "tower": return d(self.max_damage,3*self.max_damage)
        return self.damage 
    def special_attack(self, char, target_tile, game, type = "knight"):
        if not game: return False
        target = target_tile.current_char
        if not target: return False
        if not is_enemy_of(char, target): 
            game.add_message("watch out, he is not my enemy ...")
            return False
        if not char.can_see_character(target, game.map): return False
        if not self.consumption(char, type): return False
        dmg = self.calc_damage(type)
        if dmg > target.hp: # manual kill and move process 
            dx = target.x - char.x 
            dy = target.y - char.y 
            # death of target and removal from the map 
            target.drop_on_death()
            game.map.remove_character(target)
            # move the character 
            old_x, old_y = char.x, char.y
            if game.map.move_character(char, dx, dy):
                game.dirty_tiles.add((old_x, old_y))
                game.dirty_tiles.add((char.x, char.y))
                game.draw()
        else:
            match type:
                case "knight":
                    game.events.append( AttackEvent(char, target, dmg) )
                    game.add_message(f"Attack performed : {dmg:.1f}")
                case "tower":                    
                    game.events.append( AttackEvent(char, target, dmg) )
                    game.add_message(f"Attack performed : {dmg:.1f}")
                    # move the character 
                    dx, dy = char.get_forward_direction()
                    dx = -dx + target.x - char.x
                    dy = -dy + target.y - char.y 
                    old_x, old_y = char.x, char.y
                    if game.map.move_character(char, dx, dy):
                        game.dirty_tiles.add((old_x, old_y))
                        game.dirty_tiles.add((char.x, char.y))
                        game.draw()
                case _: 
                    game.events.append( AttackEvent(char, target, dmg) )
                    game.add_message(f"Attack performed : {dmg:.1f}")
        return True     
    def use_power_special(self, char, game): 
        pass     
    def use_thrust_special(self, char, game): # spear
        stamina_bound = 20
        tx, ty = char.get_forward_direction()
        tile0 = game.map.get_tile(char.x+tx, char.y+ty)
        if tile0:
            if not tile0.walkable:
                return False
            if tile0.current_char:
                return False
        tile1 = game.map.get_tile(char.x+2*tx, char.y+2*ty)
        if tile1:
            if tile1.current_char:
                if char.primary_hand:
                    if char.stamina<stamina_bound:
                        return False 
                    else:
                        game.events.append(
                            AttackEvent(
                                char, tile1.current_char, d(char.primary_hand.damage,3*char.primary_hand.damage) 
                            ) 
                        )
                        char.stamina -= stamina_bound
                        game.game_iteration()
                        return True 
        return False
    def use_knight_special(self, char, game): # sword 
        map = game.map 
        if not char: return False
        if not map: return False
        x = char.x
        y = char.y
        shuffled_list = random.sample(CHESS_KNIGHT_DIFF_MOVES, len(CHESS_KNIGHT_DIFF_MOVES))
        b_attack_performed = False
        for dx,dy in  shuffled_list:
            tile = map.get_tile(x+dx,y+dy)
            if tile:
                if self.special_attack(char, tile, game, "knight"):
                    b_attack_performed = True 
                    game.game_iteration()
                    break
        if not b_attack_performed:
            game.add_message("nevermind ...")
        return b_attack_performed
    def use_tower_special(self, char, game): # mace
        map = game.map 
        if not char: return False
        if not map: return False
        x = char.x
        y = char.y
        target = None 
        dx, dy = char.get_forward_direction()
        for i in range(1,7):
            tile = map.get_tile(x+i*dx, y+i*dy)
            if not tile: continue
            if not tile.walkable: continue 
            target = tile.current_char
            if target: 
                dx = dx*i 
                dy = dy*i
                break 
        if not target: return False 
        b_attack_performed = False
        tile = map.get_tile(x+dx,y+dy)
        if tile:
            if self.special_attack(char, tile, game, "tower"):
                b_attack_performed = True 
                # break
        return b_attack_performed
    def use_bishop_special(self, char, game):
        pass 
    def use_special_F(self, char, game): # F Key 
        if isinstance(self, Sword) and char.can_use_knight_skill:
            return self.use_knight_special(char, game)
        if isinstance(self, Mace) and char.can_use_tower_skill:
            print(self)
            return self.use_tower_special(char, game)
        game.add_message("this weapon don't have any special skill ...")
        return False 
    def use_special_End(self, char, game): # End Key
        if isinstance(self, Sword) and char.can_use_thrust_skill:
            return self.use_thrust_special(char, game)
        return False     

# (name, utility, info) ~ (alfa, beta, gama)
class Item(Serializable, Entity): # Primitive
    __serialize_only__ = Entity.__serialize_only__ + ["name","description","weight"]
    def __init__(self, name="", description="", weight=1, sprite="item"):
        Serializable.__init__(self)
        Entity.__init__(self)
        self.name = name
        self.description = description
        self.weight = weight # not used yet 
        self.sprite = sprite 
    def paint_to(self, painter, item_list=None):
        if not item_list: return super().paint_to(painter)
        if len(item_list)<=1: return super().paint_to(painter)
    def get_utility_info(self): # return a string with a formated value for the utility variable attributes 
        return ""
    def get_add_info(self): 
        return f"{self.weight:.1f} [kg] : {self.description}"
    def __str__(self):
        return f"{self.name} ; "+self.get_utility_info()
    def info(self):
        return self.__str__()
    def is_equipped(self, char):
        return False
    
# Usable.use() || { Character.remove_item() } || {}
class Usable(Item): # Interface : use item
    __serialize_only__ = Item.__serialize_only__+["uses"]
    def __init__(self, name="", description="", weight=1, sprite="item", uses = 1):
        Item.__init__(self, name = name, description = description, weight = weight, sprite = sprite)
        self.uses = uses 
    def use(self, char):
        self.uses -= 1
        if self.uses <= 0: char.remove_item(self)
        # do something on derived classes 
    def get_utility_info(self):
        return f"({self.uses:.0f})"

class Container(Serializable): # Primitive 
    __serialize_only__ = ["items"]
    def __init__(self, current_char = None):
        Serializable.__init__(self)
        self.items = []
        self.current_char = current_char # necessary ? 
    def get_item_index(self, item):
        for index, i in enumerate(self.items):
            if item is i:
                return index
        return -1
    def add_item(self, item):
        if isinstance(item, Item):
            index = self.get_item_index(item)
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
    def give(self, item, another):
        if not isinstance(another, Container): return False
        if self.get_item_index(item) == -1: return False
        self.remove_item( item )
        another.add_item( item ) 
        return True 
        
class Durable(Item): # interface : has durability_factor, quality
    __serialize_only__ = ["durability_factor"]
    def __init__(self, name="", description="", weight=1, durability_factor=0.995):
        Item.__init__(self, name = name, description = description, weight = weight, sprite=name.lower() )
        self.durability_factor = durability_factor
    def durability_consumption(self, char):
        pass 
    def get_quality(self):
        qlt = self.durability_factor
        if qlt>=0.998: 
            return "master-crafted"
        elif qlt>=0.95:
            return "durable"
        elif qlt>=0.90:
            return "bad-quality"
        else:
            return "junk"
    def set_quality(self, n_int = 2):
        match n_int:
            case 1: # master-crafted
                self.durability_factor = d(0.998, 0.999)
            case 2: # durable
                self.durability_factor = d(0.95, 0.998)
            case 3: # bad-quality
                self.durability_factor = d(0.9, 0.95)
            case 4: # junk 
                self.durability_factor = d(0.9)
    def get_utility_info(self):
        return f"({self.get_quality()})"
        
# Equippable.get_equipped_slot() || { Character.getattr() } || {}
class Equippable(Durable): # Interface : equipment
    __serialize_only__ = Durable.__serialize_only__+["slot"]
    def __init__(self, name="", description="", weight=1, slot="primary_hand", durability_factor=0.995):
        Durable.__init__(self, name = name, description = description, weight = weight, durability_factor = durability_factor)
        self.slot = slot
    def get_equipped_slot(self, char):
        current_slot = None
        for atrib in EQUIPMENT_SLOTS:
            if self == getattr(char, atrib):
                current_slot = atrib
                break
        return current_slot
    def is_equipped(self, char):
        return not (self.get_equipped_slot(char) is None)
    def is_properly_equipped(self, char):
        current_equipped_slot = self.get_equipped_slot(char)
        if self.slot == current_equipped_slot: return True 
        if self.slot in HAND_SLOTS and current_equipped_slot in HAND_SLOTS: return True 
        return False 
    def get_utility_info(self):
        return f"-{self.slot} "+super().get_utility_info()
    
# Weapon.durability_consumption() || { Character.set_equipment_by_slot() } || {}
# Weapon.stats_update() || { Weapon.stamina_consumption() | Weapon.durability_consumption() } || { Character.set_equipment_by_slot() }
class Weapon(Equippable): 
    __serialize_only__ = Equippable.__serialize_only__+["damage","stamina_consumption","max_damage"]
    def __init__(self, name="", damage=0 ,description="", weight=1, stamina_consumption=1, durability_factor=0.995):
        Equippable.__init__(self, name = name, description=description, weight=weight, slot="primary_hand", durability_factor=durability_factor)
        self.damage = damage # damages decrease when successfully hit and restored to max_damage using special item 
        self.stamina_consumption = stamina_consumption 
        self.max_damage = damage 
    def durability_consumption(self, char):
        if not self.is_properly_equipped(char): return 
        self.damage = max(0,self.damage*self.durability_factor)
        if self.damage < 0.5: char.primary_hand = None
    def do_stamina_consumption(self, char):
        char.stamina = max(0, char.stamina - self.stamina_consumption)
    def stats_update(self, player): # must differentiate between players and npcs 
        if not (self in {player.primary_hand, player.secondary_hand}): return False
        self.do_stamina_consumption(player)
        self.durability_consumption(player)
        return True
    def get_utility_info(self):
        return f"{self.damage:.1f} [dmg] "+Durable.get_utility_info(self)

class Parriable(Weapon): 
    """ Weapons that has probability to exchange hp damage for stamina consumption. """
    __serialize_only__ = Weapon.__serialize_only__
    def __init__(self, name="", damage=0 ,description="", weight=1, stamina_consumption=1, durability_factor=0.995):
        Weapon.__init__(self, name = name, damage = damage, description = description, weight= weight, stamina_consumption = stamina_consumption, durability_factor = durability_factor)
    def get_parry_chance(self, char, enemy, damage):
        """ To be used on derived classes, return False whenever the derived class should return 0.0 """
        if not (self in {char.primary_hand, char.secondary_hand}): return False # the derived class should return 0.0 chance 
        primary = enemy.primary_hand
        if not enemy: return False # the derived class should return 0.0 chance 
        if char.stamina <= damage: return False # the derived class should return 0.0 chance 
        return True # the derived class must do something else 
     
# Sword.get_parry_chance() || { Parriable.get_parry_chance() } || {}
class Sword(Parriable, SpecialSkillWeapon):
    __serialize_only__ = Parriable.__serialize_only__ 
    def __init__(self, name="long_sword", damage=8 ,description="", weight=1, stamina_consumption=1, durability_factor=0.995):
        Parriable.__init__(self, name = name, damage = damage, description = description, weight = weight, stamina_consumption = stamina_consumption, durability_factor = durability_factor)
        SpecialSkillWeapon.__init__(self)
        self.days_to_unlock_special = 20
    def get_parry_chance(self,player, enemy, damage):
        if not super().get_parry_chance(player, enemy, damage): return 0.0
        primary = enemy.primary_hand
        if isinstance(primary, Sword): 
            return 0.7
        elif isinstance(primary, Mace):
            return 0.5
        return 0.0 

# Mace.get_parry_chance() || { Parriable.get_parry_chance() } || {}
class Mace(Parriable, SpecialSkillWeapon):
    __serialize_only__ = Parriable.__serialize_only__ 
    def __init__(self, name="mace", damage=10 ,description="", weight=1, stamina_consumption=2, durability_factor=0.995):
        Parriable.__init__(self, name = name, damage = damage, description = description, weight = weight, stamina_consumption = stamina_consumption, durability_factor = durability_factor)
        SpecialSkillWeapon.__init__(self)
        self.days_to_unlock_special = 10
    def get_parry_chance(self, player, enemy, damage):
        if not super().get_parry_chance(player, enemy, damage): return 0.0
        primary = enemy.primary_hand
        if isinstance(primary, Sword): 
            return 0.5
        elif isinstance(primary, Mace):
            return 0.3
        return 0.0 

# Food.use() || { Food.update_value() | Usable.use() } || { Character.remove_item() }    
class Food(Usable, Resource):
    __serialize_only__ = Usable.__serialize_only__+Resource.__serialize_only__+["nutrition"]
    def __init__(self, nutrition=0, name="Meat", description="", weight=1):
        food_uses = 1
        if nutrition > 100: food_uses = nutrition//50
        Usable.__init__(self, name = name, description = description, weight = weight, sprite=name.lower(), uses = food_uses)
        Resource.__init__(self)
        self.nutrition = float(nutrition)/food_uses
        self.type = "food"
        self.update_value()
    def use(self, char):
        super().use(char)
        if hasattr(char, 'hunger') and hasattr(char, 'max_hunger'):
            char.hunger = min(char.hunger + self.nutrition, char.max_hunger)
            char.hp = min(char.hp + self.nutrition/20.0, char.max_hp)
            char.stamina = min(char.stamina + self.nutrition/10.0, char.max_stamina)
            self.update_value()
            return True
        return False
    def update_value(self):
        self.value = self.nutrition*self.uses 
    def get_utility_info(self):
        return f"{self.nutrition:.1f} [ntr] "+Usable.get_utility_info(self)

class Wood(Item, Resource):
    __serialize_only__ = Item.__serialize_only__+Resource.__serialize_only__
    def __init__(self, value = 100):
        Item.__init__(self, name="Wood", description="", weight=1, sprite="wood")
        Resource.__init__(self)
        self.value = value 
        self.type = "wood"
    def get_utility_info(self):
        return Resource.get_utility_info(self)

class Stone(Item, Resource):
    __serialize_only__ = Item.__serialize_only__+Resource.__serialize_only__
    def __init__(self, value = 100):
        Item.__init__(self, name="Stone", description="", weight=1, sprite="stone")        
        Resource.__init__(self)
        self.value = value 
        self.type = "stone"
    def get_utility_info(self):
        return Resource.get_utility_info(self)
        
class Metal(Item, Resource):
    __serialize_only__ = Item.__serialize_only__+Resource.__serialize_only__
    def __init__(self, value = 100):
        Item.__init__(self, name="Metal", description="", weight=1, sprite="metal")
        Resource.__init__(self)
        self.value = value 
        self.type = "metal"
    def get_utility_info(self):
        return Resource.get_utility_info(self)
        
# WeaponRepairTool.use() || { Usable.use() } || { Character.remove_item() }
class WeaponRepairTool(Usable):
    __serialize_only__ = Usable.__serialize_only__+["repairing_factor"]
    def __init__(self, name="", repairing_factor=1.05, description="", weight=1, uses = 10):
        Usable.__init__(self, name = name, description = description, weight = weight, sprite=name.lower(), uses = uses)
        self.repairing_factor = repairing_factor
    def use(self, char):
        if char.primary_hand:
            primary = char.primary_hand
            if primary.damage < 0.9*primary.max_damage:
                super().use(char)
                primary.damage = min( self.repairing_factor*primary.damage, primary.max_damage)
                return True
        return False
    
class Armor(Equippable): 
    __serialize_only__ = Equippable.__serialize_only__+["defense_factor"]
    def __init__(self, name="", defense_factor=0.02, description="", weight=1, slot="torso"):
        Equippable.__init__(self, name = name, description = description, weight = weight, slot = slot)
        self.defense_factor = defense_factor
    def durability_consumption(self, char):
        if not self.is_properly_equipped(): return 
        self.defense_factor = max(0,self.defense_factor*self.durability_factor)
        if self.defense_factor < 0.5: 
            if self.is_equipped():
                char.set_equipment_by_slot( value = None, slot = self.get_equipped_slot() )
    def get_utility_info(self):
        return f"{self.defense_factor*100:.0f} [def] "+super().get_utility_info()

# SANITY COMMENTS:
# 1. b_generate_items must be False by default, otherwise the Serializable will generate initial items whenever they use Load_JSON 
# 2. .receive_damage() use the do_damage() from enemy to perform de damage on character 

class Damageable:
    __serialize_only__ = ["hp", "max_hp"]
    def __init__(self):
        self.max_hp = 100
        self.hp = self.max_hp
    def receive_damage(self, attacker, damage): 
        self.hp -= damage
        
class OfensiveCharacter(Damageable):
    __serialize_only__ = Damageable.__serialize_only__ + ["base_damage"]
    def __init__(self):
        Damageable.__init__(self)
        self.base_damage = 0
    def do_damage(self):
        damage = self.base_damage
        if self.primary_hand and hasattr(self.primary_hand, 'damage'):
            damage += d(self.primary_hand.damage/2.0, 1.5*self.primary_hand.damage)
        if self.secondary_hand and hasattr(self.secondary_hand, 'damage'):
            damage += d(self.secondary_hand.damage/2.0, 1.5*self.secondary_hand.damage)/2.0
        return damage
    def weapons_stats_update(self):
        primary = self.primary_hand
        if primary and isinstance(primary, Weapon) and primary.is_properly_equipped(self):
            primary.stats_update(self)
        secondary = self.secondary_hand
        if secondary and isinstance(secondary, Weapon) and secondary.is_properly_equipped(self):
            secondary.stats_update(self)

# DefensiveCharacter.receive_damage() || { DefensiveCharacter.calculate_parry_factor() | DefensiveCharacter.calculate_defense_factor() } || {}
class DefensiveCharacter(OfensiveCharacter): # interface : characters that can parry and absorb damage 
    __serialize_only__ = OfensiveCharacter.__serialize_only__ + ["stamina", "max_stamina"]
    def __init__(self):
        OfensiveCharacter.__init__(self)
        self.max_stamina = 100
        self.stamina = self.max_stamina 
    def receive_damage(self, attacker, damage):
        if d() < self.calculate_parry_factor(attacker, damage) + self.calculate_defense_factor():
            self.stamina -= damage
        else:
            super().receive_damage(attacker, damage)
    def calculate_defense_factor(self):
        S = 0
        for df in EQUIPMENT_SLOTS:
            df_item = getattr(self, df, None)
            if df_item:
                if hasattr(df_item, "defense_factor"):
                    S += df_item.defense_factor
        return S 
    def calculate_parry_factor(self, attacker, damage):
        primary_parry = 0
        if isinstance(self.primary_hand, Parriable):
            primary_parry = self.primary_hand.get_parry_chance(self, attacker, damage)
        secondary_parry = 0    
        if isinstance(self.secondary_hand, Parriable):
            secondary_parry = self.secondary_hand.get_parry_chance(self, attacker, damage)
            if primary_parry:
                primary_parry = primary_parry/2.0
                secondary_parry = secondary_parry/2.5
        return primary_parry+secondary_parry

# RegenerativeCharacter.regenerate() || { RegenerativeCharacter.regenerate_health() | RegenerativeCharacter.regenerate_stamina() } || {}
class RegenerativeCharacter(DefensiveCharacter): # interface : characters that can regenerate stats
    __serialize_only__ = DefensiveCharacter.__serialize_only__ 
    def __init__(self):
        DefensiveCharacter.__init__(self)
    def regenerate(self):
        self.regenerate_health()
        self.regenerate_stamina()
    def reset_stats(self):
        if hasattr(self, "stamina") and hasattr(self, "max_stamina"):
            self.stamina = self.max_stamina
        if hasattr(self, "hp") and hasattr(self, "max_hp"):
            self.hp = self.max_hp
        if hasattr(self, "hunger") and hasattr(self, "max_hunger"):
            self.hunger = self.max_hunger
    def regenerate_stamina(self):
        if hasattr(self, "stamina") and hasattr(self, "max_stamina"):
            self.stamina = min(self.stamina + 3, self.max_stamina) 
    def regenerate_health(self):
        if hasattr(self, "hp") and hasattr(self, "max_hp"):
            self.hp = min(self.hp + 1, self.max_hp) 

class BehaviourCharacter(Entity): # interface : artificially controlled characters 
    __serialize_only__ = Entity.__serialize_only__ + ["activity", "tolerance"] # not serializable yet 
    def __init__(self):
        Entity.__init__(self)
        self.activity = 0.05
        self.tolerance = 4
    def get_closest_visible(self, entities, game_instance, default_target = None):
        entity = None 
        distance = None 
        if default_target:
            entity = default_target
            distance = self.distance(entity)
        if len(entities) == 0: 
            return entity, distance 
        if type(entities) == list: 
            if not default_target:
                entity = entities[0]
                distance = self.distance(entity)
            if len(entities) == 1: 
                return entity, distance 
            for v in entities:
                if not v: continue # possibly unnecessary 
                # if not self.can_see_character(v, game_instance.map): continue 
                if not v.current_tile: continue 
                tile = game_instance.map.get_tile(v.x,v.y)
                if not tile: continue
                if not tile.current_char is v: continue 
                new_distance = self.distance(v)
                if new_distance < distance:
                    entity = v
                    distance = new_distance 
        elif type(entities) == dict:
            for k,v in entities.items():
                if not k or not v: continue # possibly unnecessary 
                if not self.can_see_character(v, game_instance.map): continue 
                if not v.current_tile: continue 
                tile = game_instance.map.get_tile(v.x,v.y)
                if not tile: continue
                if not tile.current_char is v: continue 
                new_distance = self.distance(v)
                if distance is None:
                    entity = v
                    distance = new_distance
                elif new_distance < distance:
                    entity = v
                    distance = new_distance 
        if entity and distance:
            if isinstance(self, Player):
                return entity, distance
            else:
                if self.can_see_character(entity, game_instance.map):
                    return entity, distance
                else:
                    return None, None 
        else:
            return None, None 
    def pursue_target(self, entities, game_instance, default_target = None):
        enemy, distance = self.get_closest_visible(entities, game_instance, default_target)
        map = game_instance.map 
        if enemy and distance and distance <= self.tolerance:
            path = map.find_path(self.x, self.y, enemy.x, enemy.y)
            if path:
                next_x, next_y = path[0]
                dx, dy = next_x - self.x, next_y - self.y
                tile = map.get_tile(next_x, next_y)
                if tile:
                    if tile.can_place_character():
                        self.move(dx, dy, map)
                        return True 
                    elif tile.current_char is enemy:
                        damage = self.do_damage()
                        game_instance.events.append(AttackEvent(self, enemy, damage))
                        if isinstance(self, Player):print(self, damage)
                        return True 
        return False
    def random_walk(self, game_instance):
        if random.random() < self.activity:
            dx, dy = random.choice(ADJACENT_DIFF_MOVES)
            target_x, target_y = self.x + dx, self.y + dy
            tile = game_instance.map.get_tile(target_x, target_y)
            if tile:
                if tile.walkable and not tile.current_char:
                    self.move(dx, dy, game_instance.map)
    def behaviour_update(self, entities, game_instance, default_target = None):
        if hasattr(self,"current_map"):
            if self.current_map != game_instance.map.coords: return False
            if self.current_map != game_instance.current_map: return False
        if self.pursue_target(entities, game_instance, default_target): return True 
        self.random_walk(game_instance) 
        return True 

class EquippedCharacter(Container): # interface : equip items
    __serialize_only__ = Container.__serialize_only__ + [ "primary_hand", "secondary_hand", "head", "neck", "torso", "waist", "legs", "foot" ]
    def __init__(self):
        Container.__init__(self) 
        self.primary_hand = None
        self.secondary_hand = None
        self.head = None
        self.neck = None
        self.torso = None
        self.waist = None
        self.legs = None
        self.foot = None
    def equip_item(self, item, slot): 
        if isinstance(item, Equippable):
            # removes any equipped 
            prev_equip = self.get_equipment_by_slot(slot)
            if prev_equip: 
                self.items.append(prev_equip) # put back the previous equipped to inventory
                self.set_equipment_by_slot(None, slot) # set slot free
            # remove the new item from inventory if its there 
            index = self.get_item_index(item)
            if index != -1: self.items.pop(index) 
            # equip item in the slot 
            self.set_equipment_by_slot(item, slot)
            return True 
        return False # not equipped, fail 
    def unequip_item(self, slot):
        prev_equip = self.get_equipment_by_slot(slot)
        if prev_equip:
            self.add_item(prev_equip)
            self.set_equipment_by_slot(None, slot)
            return True 
        return False
    def pickup_item(self, item):
        return self.add_item(item)
    def generate_initial_items(self):
        pass     
    def set_equipment_by_slot(self, value, slot = "primary_hand"):
        setattr(self, slot, value)
    def get_equipment_by_slot(self, slot = "primary_hand"):
        return getattr(self, slot, None)
    
class Character(EquippedCharacter, BehaviourCharacter):
    __serialize_only__ = EquippedCharacter.__serialize_only__ + BehaviourCharacter.__serialize_only__ +  ["name"]
    def __init__(self, name="", hp=100, x=50, y=50):
        EquippedCharacter.__init__(self)
        BehaviourCharacter.__init__(self)
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.x = x
        self.y = y
        self.sprite = "player"
        self.update_turn = 1 # not used yet # used to slowdown a character by checking if turns % self.update_turn: return 
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
    def can_see_character(self, another, game_map):
        if not isinstance(another, Character): return None
        distance = self.distance(another)
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
    def is_rendered_on_map(self, game_map): 
        tile = game_map.get_tile(self.x, self.y)
        if not tile: return False 
        return tile.current_char is self 
    def is_placed_on_map(self, game_map): 
        tile = game_map.get_tile(self.x, self.y)
        if not tile: return False 
        return (tile.current_char is self) and (self.current_tile is tile) 

class SkilledCharacter(Character):
    __serialize_only__ = Character.__serialize_only__ + [ 
        "can_use_bishop_skill",
        "can_use_knight_skill", 
        "can_use_power_skill", 
        "can_use_thrust_skill", 
        "can_use_tower_skill",
        "can_use_dodge_skill" 
    ]
    def __init__(self, name="", hp=100, x=50, y=50):
        Character.__init__(self, name = name, hp = hp, x = x, y = y)
        self.deactivate_all_skills()
        self.stamina_bound = 20
    def dodge_skill(self, game_instance): 
        if not self.can_use_dodge_skill: return False 
        if self.stamina<self.stamina_bound:
            game_instance.add_message("I'm exhausted ... I need to take a breathe")
        x = self.x 
        y = self.y
        fx, fy = self.get_forward_direction()
        bx = -fx 
        by = -fy
        b_is_walkable = True 
        map = game_instance.map 
        tile = map.get_tile(x+bx,y+by)
        if tile and self.stamina>self.stamina_bound:
            if tile.walkable:
                tile2 = map.get_tile(x+2*bx,y+2*by)
                if tile2:
                    if tile2.walkable:
                        dx = 2*bx 
                        dy = 2*by
                        self.stamina -= self.stamina_bound
                    else:
                        b_is_walkable = False
                else:
                    b_is_walkable = False
            else:
                b_is_walkable = False
        else:
            b_is_walkable = False
        if not b_is_walkable:
            return False 
        old_x, old_y = self.x, self.y
        if self.move(dx, dy, game_instance.map):
            game_instance.events.append(MoveEvent(self, old_x, old_y))
            game_instance.dirty_tiles.add((old_x, old_y))
            game_instance.dirty_tiles.add((self.x, self.y))    
            game_instance.game_iteration()
            return True 
        return False 
    def activate_all_skills(self):
        self.can_use_power_skill = True
        self.can_use_thrust_skill = True
        self.can_use_knight_skill = True
        self.can_use_tower_skill = True
        self.can_use_bishop_skill = True
        self.can_use_dodge_skill = True
    def deactivate_all_skills(self):
        self.can_use_power_skill = False 
        self.can_use_thrust_skill = False 
        self.can_use_knight_skill = False 
        self.can_use_tower_skill = False 
        self.can_use_bishop_skill = False 
        self.can_use_dodge_skill = False 

class Player(SkilledCharacter, RegenerativeCharacter): # player or playable npc 
    __serialize_only__ = SkilledCharacter.__serialize_only__+ RegenerativeCharacter.__serialize_only__ + [ 
        "hunger",
        "max_hunger",
        "rotation", 
        "field_of_view", 
        "current_map",
        "days_survived",
        "party"
    ]
    def __init__(self, name="", hp=PLAYER_MAX_HP, x=MAP_WIDTH//2, y=MAP_HEIGHT//2, b_generate_items = False, sprite = "player", current_map = (0,0,0)):
        SkilledCharacter.__init__(self, name = name, hp = hp, x = x, y = y)
        RegenerativeCharacter.__init__(self)
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
        self.party = False # marker if the player belongs to a character 
        self.activity = 0.05
        self.tolerance = 4
        if b_generate_items: self.generate_initial_items()
    def move(self, dx, dy, game_map):
        if self.stamina >= 10:
            moved = super().move(dx, dy, game_map)
            if moved: self.stamina -= self.current_tile.get_stamina_consumption()
            return moved
        return False
    def generate_initial_items(self):
        self.equip_item(Sword(name="Bastard_Sword", damage=8.5, durability_factor=0.9995, description="although with no name, this Bastard Sword was master-crafted and passed as heirloom in generations of my family, that swords reminds me of the values my father teach me ..."), "primary_hand")
        self.add_item(Food(name="Apple", nutrition=50))
        self.add_item(Food(name="Apple", nutrition=50))
        self.add_item(Food(name="Apple", nutrition=50))
        self.add_item(Food(name="Bread", nutrition=100))
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
    def behaviour_update(self, game_instance): # on turn for npcs 
        if super().behaviour_update(game_instance.map.enemies, game_instance):
            self.regenerate_stamina()
            self.regenerate_health()
    def update_available_skills(self):
        if self.days_survived >= 5: 
            self.can_use_dodge_skill = True 
        if self.days_survived >= 20: 
            self.can_use_thrust_skill = True
        if self.days_survived >= 30:
            self.can_use_knight_skill = True 
            self.can_use_tower_skill = True 
            self.can_use_bishop_skill = True 
            self.can_use_power_skill = True

# Hero.add_to_party() || { Hero.remove_character() | Hero.place_character() } || {}
# Hero.release_party() || { Hero.place_character() | Hero.draw() } || {}
class Hero(Player): # playable character that can "carry" a party 
    __serialize_only__ = Player.__serialize_only__ + ["party_members"]
    def __init__(self, name="", hp=PLAYER_MAX_HP, x=MAP_WIDTH//2, y=MAP_HEIGHT//2, b_generate_items = False, sprite = "player", current_map = (0,0,0)):
        Player.__init__(self, name = name, hp = hp, x = x, y = y, b_generate_items = b_generate_items, sprite = sprite, current_map = current_map)
        self.party_members = set() # names of players that belongs to Hero party 
    def add_to_party(self, key, game_instance):
        if not key in game_instance.players: return 
        npc = game_instance.players[key]
        if not isinstance(npc, Player): return 
        if npc.party == True: return 
        if isinstance(npc, Hero):
            if len(npc.party_members) > 0: return 
        if len(self.party_members) >= 4: return 
        # -- 
        self.party_members.add(key)
        npc.party = True
        game_instance.map.remove_character(npc)
        game_instance.update_prior_next_selection()
        game_instance.draw()
    def release_party(self, game_instance):
        x = self.x 
        y = self.y 
        for dx,dy in CROSS_DIFF_MOVES_1x1:
            if not game_instance.map.can_place_character_at(x+dx,y+dy): continue 
            if dx == 0 and dy == 0: continue
            for key in self.party_members:
                value = game_instance.players.get(key, None)
                if value and value.party:
                    value.x = x+dx 
                    value.y = y+dy 
                    value.party = False 
                    self.party_members.remove(key)
                    game_instance.map.place_character(value)
                    game_instance.draw()
                    break 
    def count_party(self):
        return len(self.party_members)
                    
class Enemy(Character, OfensiveCharacter):
    __serialize_only__ = Character.__serialize_only__ + OfensiveCharacter.__serialize_only__ +["type","stance","canSeeCharacter","patrol_direction"]
    def __init__(self, name="", hp=30, x=50, y=50, b_generate_items = False):
        Character.__init__(self, name = name, hp = hp, x = x, y = y)
        OfensiveCharacter.__init__(self)
        self.description = ""
        self.type = "Generic"
        self.stance = "Aggressive"
        self.canSeeCharacter = False
        self.patrol_direction = (random.choice([-1, 1]), 0)
        self.sprite = "enemy"
        self.activity = 0.3 
        self.tolerance = 15 
        if b_generate_items: self.generate_initial_items()
    def behaviour_update(self, game_instance):  # Add game parameter
        super().behaviour_update(game_instance.players, game_instance, game_instance.player)
    
class Zombie(Enemy):
    __serialize_only__ = Enemy.__serialize_only__
    def __init__(self, name="", hp=40, x=50, y=50, b_generate_items = False):
        Enemy.__init__(self, name = name, hp = hp, x = x, y = y, b_generate_items = b_generate_items)
        self.type = "Zombie"
        self.description = "Zombies, people affected by the plague, they are still alive but because of this strange disease their bodies smells like rotten flesh. Before they lose their minds, they try to acummulate food to satiate hunger, it's almost certain to find food with them ..."
        self.sprite = "zombie"
    def do_damage(self):
        return d(0, 10)
    def generate_initial_items(self):
        if random.random() < 0.7:
            self.add_item(Food(name="bread", nutrition=random.randint(50, 100)))
        if random.random() < 0.7:
            self.add_item(Food(name="apple", nutrition=random.randint(5, 15)))

class Rogue(Enemy):
    __serialize_only__ = Enemy.__serialize_only__
    def __init__(self, name="", hp=100 , x=50, y=50, b_generate_items = False):
        Enemy.__init__(self, name = name, hp = hp, x = x, y = y, b_generate_items = b_generate_items)
        self.type = "Rogue"
        self.description = "Rogues and Bandits, they are just robbers, ambushing travellers on the road. Always carry a sword with you ..."
        self.sprite = "rogue"
        self.activity = 0.2 
        self.tolerance = 7 
    def generate_initial_items(self):
        self.equip_item(Sword("Long_Sword", damage=10), "primary_hand")
        if random.random() < 0.3:
            self.add_item(Food(name="bread", nutrition=random.randint(50, 100)))

class Mercenary(Rogue):
    __serialize_only__ = Enemy.__serialize_only__
    def __init__(self, name="", hp=130 , x=50, y=50, b_generate_items = False):
        Rogue.__init__(self, name = name, hp = hp, x = x, y = y, b_generate_items = b_generate_items)
        self.type = "Mercenary"
        self.description = "More experienced in combat than rogues, but often doing the same kind of 'job', money before honor ..."
        self.sprite = "mercenary"
        self.activity = 0.1 
        self.tolerance = 10 
    def generate_initial_items(self):
        self.equip_item(Mace("mace", damage=10), "primary_hand")
        if random.random() < 0.3:
            self.add_item(Food(name="bread", nutrition=random.randint(50, 100)))
        else:
            self.add_item(Food(name="meat", nutrition=random.randint(150, 200)))
    
class Bear(Enemy):
    __serialize_only__ = Enemy.__serialize_only__
    def __init__(self, name="", hp=60 , x=50, y=50, b_generate_items = False):
        Enemy.__init__(self, name = name, hp = hp, x = x, y = y, b_generate_items = b_generate_items)
        self.description = "Bears, these woods are their home, stronger than any man, don't try to mess with them ..."
        self.sprite = "bear"
        self.activity = 0.1
        self.tolerance = 10 
    def generate_initial_items(self):
        self.add_item(Food(name="meat", nutrition=250))
    
# Tile.draw() || { Tile.get_default_pixmap() | Entity.paint_to() } || { Entity.get_sprite() }
class Tile(Container):
    SPRITES = {}  # Class-level sprite cache
    list_sprites_names = list(SPRITE_NAMES)
    __serialize_only__ = Container.__serialize_only__ + ["x", "y", "walkable", "blocks_sight", "default_sprite_key", "stair", "stair_x", "stair_y", "cosmetic_layer_sprite_keys", "stamina_consumption"]
    def __init__(self, x = 0, y = 0, walkable=True, sprite_key="grass"):
        Container.__init__(self)
        self._load_sprites()
        self.walkable = walkable
        self.blocks_sight = not walkable
        self.x = x 
        self.y = y 
        # --
        self.default_sprite_key = sprite_key # is the first and last layer sprite 
        self.cosmetic_layer_sprite_keys = [] # to be used as a modifier for default_sprite
        self.combined_sprite = None # is the final sprite rendered 
        # --
        self.current_char = None 
        self.stamina_consumption = 4.0 
        # -- 
        self.stair = None # used to store a tuple map coord to connect between maps 
        self.stair_x = None # points to the stair tile from the map with coord self.stair
        self.stair_y = None # points to the stair tile from the map with coord self.stair 
    def add_layer(self, sprite_key):
        self.cosmetic_layer_sprite_keys.append( sprite_key )
    # def remove_layer(self, sprite_key = None):
        # if not sprite_key: 
            # self.cosmetic_layer_sprite_keys.clear()
            # return 
        # self.cosmetic_layer_sprite_keys.remove( sprite_key )
    def get_transparent_image(self):
        # todo 
        return 
    def paint_items(self, painter):
        if len(self.items) == 0: return 
        if len(self.items) == 1: self.items[0].paint_to(painter)
        if len(self.items) > 1:
            painter.drawPixmap(0, 0, Tile.SPRITES.get("sack", self.get_default_pixmap() ))
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
        # -- paint items 
        self.paint_items(painter) 
        # -- Char Paint 
        if self.current_char: self.current_char.paint_to(painter) 
        # END Painter 
        painter.end()
        self.combined_sprite = combined
        # -- Add to Scene
        item = QGraphicsPixmapItem(self.combined_sprite)
        item.setPos(x, y)
        scene.addItem(item)
    def can_place_character(self):
        return self.walkable and (not self.current_char )
    def get_default_pixmap(self):
        return self.SPRITES.get(self.default_sprite_key, QPixmap())
    def add_cosmetic_sprite(self, sprite_key = None):
        if not sprite_key: return 
        self.cosmetic_layer_sprite_keys.append(sprite_key)
    def get_stamina_consumption(self):
        return self.stamina_consumption
    def get_layer_index(self, sprite_name):
        """ return index or None """
        result = None 
        if len(self.cosmetic_layer_sprite_keys)>0:
            idx = 0 
            for it in self.cosmetic_layer_sprite_keys:
                if sprite_name == it: 
                    result = idx 
                    break 
                idx += 1
        return result 
    def add_layer_if_not_already(self, sprite_name):
        idx = self.get_layer_index(sprite_name)
        if idx is None:
            self.add_layer( sprite_name )
    def remove_layer(self, sprite_name):
        idx = self.get_layer_index(sprite_name)
        if idx is None: return 
        self.cosmetic_layer_sprite_keys.pop(idx)

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
        
class ActionTile(Tile): # tile which the player can interact - interface class
    def __init__(self, x =0,y=0,front_sprite = "stair_up", walkable=True, sprite_key="grass"):
        Tile.__init__(self, x=x, y=y, walkable=walkable, sprite_key=sprite_key)
        self.add_layer( front_sprite )
    
class Stair(ActionTile): # not used yet 
    def __init__(self, x=0, y = 0,front_sprite = "stair_up", walkable=True, sprite_key="grass"):
        ActionTile.__init__(self, x=x, y = y, front_sprite = front_sprite, walkable = walkable, sprite_key = sprite_key)
        self.stair = None # used to store a tuple map coord to connect between maps 
        self.stair_x = None # points to the stair tile from the map with coord self.stair
        self.stair_y = None # points to the stair tile from the map with coord self.stair 
    
# TileBuilding.production() || { TileBuilding.villagers() } || {}
# TileBuilding.update() || { TileBuilding.production() } || { TileBuilding.villagers() }
# TileBuilding.retrieve_food() || { Character.add_item() | TileBuilding.update_inv_window() } || {}
# TileBuilding.retrieve_wood() || { Character.add_item() | TileBuilding.update_inv_window() } || {}
# TileBuilding.store_resource() || { Character.remove_item() } || {}
class TileBuilding(ActionTile): # interface class
    __serialize_only__ = Tile.__serialize_only__ + ["villagers", "villagers_max", "food", "stone", "metal", "wood", "b_enemy"]
    def __init__(self, x=0,y=0,front_sprite = "Castle", walkable=True, sprite_key="grass", b_enemy = False):
        ActionTile.__init__(self, x = x, y = y, front_sprite = front_sprite, walkable=walkable, sprite_key=sprite_key )
        self.villagers = 5
        self.villagers_max = 20
        self.food = 0
        self.wood = 0
        self.stone = 0
        self.metal = 0
        self.b_enemy = b_enemy
    def bonus_resources(self):
        self.food = d(0,2000)
        self.wood = d(0,2000)
        self.stone = d(0,2000)
        self.metal = d(0,2000)
    def production(self):
        self.villagers = min( 1.005*self.villagers, self.villagers_max )
        self.food += d(0,self.villagers/PROD_INV_FACTOR)
        self.wood += d(0,self.villagers/PROD_INV_FACTOR)
        self.stone += d(0,self.villagers/PROD_INV_FACTOR)
        self.metal += d(0,self.villagers/PROD_INV_FACTOR)
    def update(self, game_instance = None):
        self.production()
        # % .b_enemy || add red flag cosmetic layer 
        # % .b_enemy | % else || remove red flag cosmetic layer 
        if self.b_enemy:
            self.add_layer_if_not_already("red_flag")
            # % Player Distance to Building is Less than 5 || % has villagers || spawn rogue and mercenaries | reduze .villagers count 
            # % Player Distance to Building is Less than 5 || % has villagers || spawn rogue and mercenaries || spawn on free walkable and adjacent walkable adjacent tiles 
            # % Player Distance to Building is Less than 5 || % has villagers | % else || .b_enemy = False | add one villager 
            if not game_instance: return 
            map = game_instance.map
            if self.b_enemy: print( "TileBuilding.update() || ", self.villagers )
            if game_instance.player.distance(self) < 4: 
                if self.villagers > 0:
                    enemy = map.generate_enemy_by_chance_by_list_at(self.x, self.y, TILE_BUILDING_ENEMY_TABLE)
                    if enemy:
                        self.villagers -= 5
                        map.enemies.append(enemy)
                        map.place_character(enemy)
                        game_instance.draw()
                else:
                    self.b_enemy = False 
                    self.villagers = 1
                    self.bonus_resources()
        else:
            self.remove_layer("red_flag")
            
    def retrieve_food(self, game_instance, quantity = 500):
        if self.food >= quantity:
            self.food -= quantity
            game_instance.player.add_item(Food(name = "Meat", nutrition = quantity))
            game_instance.update_inv_window()
            return True 
        return False
    def retrieve_wood(self, game_instance, quantity = 500):
        if self.wood >= quantity:
            self.wood -= quantity
            game_instance.player.add_item(Wood(value = quantity))
            game_instance.update_inv_window()
            return True 
        return False
    def retrieve_metal(self, game, quantity = 500):
        pass 
    def retrieve_stone(self, game, quantity = 500):
        pass 
    def store_resource(self, res, char):
        if isinstance(res, Resource): res.store(char, self)
    def menu_garrison(self, current_menu, current_item, menu_instance, game_instance):
        """ return True means that the menu should close """
        if not hasattr( self,"heroes" ): return False # not meant to be used without that attribute 
        # -- select and build the menu garrison on runtime
        if current_item == "Garrison >": 
            menu_instance.set_list("Garrison >", [ "Garrison+", "Garrison-", ".." ])
            return False # necessary ? 
        # --
        if current_menu == "Garrison >":
            if current_item == "..":
                menu_instance.set_list()
                return False
            if current_item == "Garrison+":
                if len(game_instance.players) > 1: 
                    self.heroes.update({ game_instance.player.name : game_instance.player})
                    game_instance.remove_player() 
                    game_instance.place_players() # maybe not necessary 
                    game_instance.draw() 
                    return True 
            if current_item == "Garrison-":
                if len( list( self.heroes.keys()) )>0:
                    menu_instance.set_list("Garrison-", self.heroes)
                    return False
        if current_menu == "Garrison-":
            if current_item:
                hero = self.heroes.get(current_item)
                if not hero: 
                    menu_instance.close()
                    return True
                dx, dy = game_instance.player.get_forward_direction()
                player = game_instance.player 
                spawn_tile = game_instance.map.get_tile(player.x+dx, player.y + dy)
                if not spawn_tile:
                    game_instance.add_message("Can't generate player at this position, please rotate the current character")
                    menu_instance.close()
                    return True
                if spawn_tile.current_char:
                    game_instance.add_message("Can't generate player at this position, please rotate the current character")
                    menu_instance.close()
                    return True 
                hero.x = player.x+dx
                hero.y = player.y + dy
                self.heroes.pop(current_item)
                game_instance.players.update({current_item: hero})
                print( hero.name, hero.party, hero.current_map )
                game_instance.place_players()
                game_instance.draw()
                return True
        return False
    def menu_resources(self, current_menu, current_item, menu_instance, game_instance):
        """ return True means that the menu should close """
        from gui import info 
        counter = [0]
        def resource_counter(obj, counter):
            if isinstance(obj, Food) or isinstance(obj, Resource):
                counter[0] += 1
                return True
            else:
                return False
        resources = { f"{counter[0]}. {info(e)[0]}" : e for e in game_instance.player.items if resource_counter(e, counter) }
        # -- 
        if current_item == "Resources >":
            menu_instance.set_list("Resources >",[ f"-> food: {self.food:.0f}", f"-> wood: {self.wood:.0f}", "Resources+", "Resources++", "Food-", "Wood-", ".." ])
            return False 
        # -- 
        if current_menu == "Resources >":
            match current_item:
                case "..":
                    menu_instance.set_list()
                    return False
                case "Resources+":
                    if len(resources) > 0:
                        menu_instance.set_list("Resources+", list(resources.keys()))
                        return False # necessary ? 
                case "Resources++":
                    if len(resources) > 0:
                        for k,v in iter(resources.items()):
                            self.store_resource(v, game_instance.player)
                        game_instance.update_inv_window()
                        return True 
                case "Food-":
                    if self.retrieve_food(game_instance):
                        return True 
                case "Wood-":
                    if self.retrieve_wood(game_instance):
                        return True 
        if current_menu == "Resources+":
            res_obj = resources[current_item]
            self.store_resource(res_obj, game_instance.player)
            game_instance.update_inv_window()
            return True 
        return False 
    def set_population_menu(self, menu_instance):
         menu_instance.set_list( "Overview >" ,
            [f"Population : {self.villagers:.1f}/{self.villagers_max}",f"Mean Production : {self.villagers/PROD_INV_FACTOR/2.0:.1f}/turn"]+[f"Food : {self.food:.1f}" if self.food else None ]+[f"Wood : {self.wood:.1f}" if self.wood else None ]+[f"Stone : {self.stone:.1f}" if self.stone else None ]+[f"Metal : {self.metal:.1f}" if self.metal else None ]+[".."]
         )

# Castle.action() || { Castle.update_menu_list() | Castle.new_npc() | TileBuilding.menu_garrison() | TileBuilding.menu_resources() } || { Character.add_item(), TileBuilding.update_inv_window(), Character.remove_item() }
class Castle(TileBuilding):
    __serialize_only__ = TileBuilding.__serialize_only__ + ["name","heroes","num_heroes"]
    def __init__(self, x=0, y =0, name = "Home", b_enemy=False):
        TileBuilding.__init__(self, x=x,y=y, front_sprite = "castle", walkable=True, sprite_key="grass", b_enemy=b_enemy)
        self.name = name 
        self.heroes = {}
        self.num_heroes = 0
        self.menu_list = []    
    def production(self):
        self.villagers = min( 1.005*self.villagers, self.villagers_max )
        self.food += d(0,self.villagers/PROD_INV_FACTOR)
    def action(self):
        from gui import info 
        self.update_menu_list()
        def f(current_menu, current_item, menu_instance, game_instance):
            self.update_menu_list(menu_instance)
            if current_item == "..": menu_instance.set_list()
            if current_item == "Overview >": self.set_population_menu(menu_instance)
            if current_item == "Exit": menu_instance.close()
            if "Guard Tower" in current_item:
                if self.wood >= 2000 and self.food >= 2500:
                    self.wood -= 2000 
                    self.food -= 2500
                    game_instance.certificates.append("Guard Tower")
                    menu_instance.close()
                    return 
            if "Lumber Mill" in current_item:
                if self.wood >= 500 and self.food >= 250:
                    self.wood -= 500 
                    self.food -= 250
                    game_instance.certificates.append("Lumber Mill")
                    menu_instance.close()
                    return 
            if "Farm" in current_item:
                if self.wood >= 500 and self.food >= 500:
                    self.wood -= 500 
                    self.food -= 500
                    game_instance.certificates.append("Farm")
                    menu_instance.close()
                    return 
            if "New Hero" in current_item:
                if self.food >= 2000:
                    if self.new_hero(game_instance):
                        self.num_heroes += 1
                        self.food -= 2000 
                else:
                    game_instance.add_message("Can't afford to purchase new heroes ...")
                menu_instance.close()
            if self.menu_garrison(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
            if self.menu_resources(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
        return f
    def update_menu_list(self, selection_box_instance = None):
        self.menu_list.clear()
        self.menu_list += [
            f"Castle [{self.name}]",
            f"-> heroes: {len(self.heroes)}",
            f"-> food: {self.food:.0f}",
            f"-> wood: {self.wood:.0f}",
            "Overview >",
            "New Hero (2000 Food)",
            "Garrison >",
            "Resources >",
            "Lumber Mill (500 Wood, 250 Food)",
            "Farm (500 Wood, 500 Food)",
            "Guard Tower (2000 Wood, 2500 Food)",
            "Exit"
        ]
    def new_hero(self, game_instance):
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
            npc_name = "Hero_"+rn(7)
        game_instance.add_hero(
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
        game_instance.map.buildings.append(obj)
        game_instance.draw()
        
# Mill.action() || { Mill.update_menu_list() | TileBuilding.menu_resources() } || { Character.add_item(), TileBuilding.update_inv_window(), Character.remove_item() }
class Mill(TileBuilding):
    __serialize_only__ = TileBuilding.__serialize_only__ + ["name"]
    def __init__(self, x=0, y =0, name = "Farm", food = d(500,2000), b_enemy=False):
        TileBuilding.__init__(self, x=x, y=y, front_sprite = "mill", walkable=True, sprite_key="grass", b_enemy=b_enemy)
        self.name = name 
        self.menu_list = []
        self.food = food 
    def action(self):
        self.update_menu_list()
        def f(current_menu, current_item, menu_instance, game_instance):
            self.update_menu_list(menu_instance)
            if current_item == "..": menu_instance.set_list()
            if current_item == "Overview >": self.set_population_menu(menu_instance)
            if current_item == "Exit": menu_instance.close()
            if self.menu_resources(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
        return f
    def update_menu_list(self, selection_box_instance = None):
        self.menu_list.clear()
        self.menu_list += [
            f"Resource [{self.name}]",
            f"-> food: {self.food:.0f}",
            "Overview >",
            "Resources >",
            "Exit"
        ]
    def production(self):
        self.villagers = min( 1.005*self.villagers, self.villagers_max )
        self.food += d(0,2*self.villagers/PROD_INV_FACTOR)

# LumberMill.action() || { LumberMill.update_menu_list() | TileBuilding.menu_resources() } || { Character.add_item(), TileBuilding.update_inv_window(), Character.remove_item() }
class LumberMill(TileBuilding):
    __serialize_only__ = TileBuilding.__serialize_only__ + ["name"]
    def __init__(self, x=0, y =0, name = "Lumber Mill", wood = d(500,2000), b_enemy=False):
        TileBuilding.__init__(self, x=x,y=y,front_sprite = "lumber_mill", walkable=True, sprite_key="grass", b_enemy=b_enemy)
        self.name = name 
        self.menu_list = []
        self.wood = wood
    def action(self):
        self.update_menu_list()
        def f(current_menu, current_item, menu_instance, game_instance):
            self.update_menu_list(menu_instance)
            if current_item == "..": menu_instance.set_list()
            if current_item == "Overview >": self.set_population_menu(menu_instance)
            if current_item == "Exit": menu_instance.close()
            if self.menu_resources(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
        return f
    def update_menu_list(self, selection_box_instance = None):
        self.menu_list.clear()
        self.menu_list += [
            f"Resource [{self.name}]",
            f"-> wood: {self.wood:.0f}",
            "Overview >",
            "Resources >",
            "Exit"
        ]
    def production(self):
        self.villagers = min( 1.005*self.villagers, self.villagers_max )
        self.wood += d(0,2*self.villagers/PROD_INV_FACTOR)

# GuardTower.action() || { GuardTower.update_menu_list() | GuardTower.new_swordman() | GuardTower.new_mounted_knight() | TileBuilding.menu_garrison() | TileBuilding.menu_resources() } || { Character.add_item(), TileBuilding.update_inv_window(), Character.remove_item() }
class GuardTower(TileBuilding):
    __serialize_only__ = TileBuilding.__serialize_only__ + ["name","heroes","num_heroes"]
    def __init__(self, x=0, y =0,name = "Guard Tower", b_enemy=False):
        TileBuilding.__init__(self, x=x, y=y, front_sprite = "tower", walkable=True, sprite_key="grass", b_enemy=b_enemy)
        self.name = name 
        self.heroes = {}
        self.num_heroes = 0
        self.menu_list = []
    def action(self):
        from gui import info 
        self.update_menu_list()
        def f(current_menu, current_item, menu_instance, game_instance):
            self.update_menu_list(menu_instance)
            if current_item == "..": menu_instance.set_list()
            if current_item == "Overview >": self.set_population_menu(menu_instance)
            if current_item == "Exit": menu_instance.close()
            if "Recruit Swordman" in current_item:
                if self.food >= 500:
                    if self.new_swordman(game_instance):
                        self.num_heroes += 1
                        self.food -= 500 
                else:
                    game_instance.add_message("Can't afford to purchase Swordman ...")
                menu_instance.close()
            if "Recruit Mounted Knight" in current_item:
                if self.food >= 700 and self.wood >= 1200:
                    if self.new_mounted_knight(game_instance):
                        self.num_heroes += 1
                        self.food -= 700 
                        self.wood -= 1200 
                else:
                    game_instance.add_message("Can't afford to purchase Mounted Knight ...")
                menu_instance.close()
            if self.menu_garrison(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
            if self.menu_resources(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
        return f
    def update_menu_list(self, selection_box_instance = None):
        self.menu_list.clear()
        self.menu_list += [
            f"Building [{self.name}]",
            f"-> garrison: {len(self.heroes)}",
            f"-> food: {self.food:.0f}",
            f"-> wood: {self.wood:.0f}",
            "Overview >",
            "Recruit Swordman (500 Food)",
            "Recruit Mounted Knight (700 Food 1200 Wood)",
            "Garrison >",
            "Resources >",
            "Exit"
        ]
    def new_swordman(self, game_instance):
        dx, dy = game_instance.player.get_forward_direction()
        player = game_instance.player 
        spawn_tile = game_instance.map.get_tile(player.x+dx, player.y + dy)
        if not spawn_tile:
            game_instance.add_message("Can't generate player at this position, please rotate the current character")
            return False
        if spawn_tile.current_char:
            game_instance.add_message("Can't generate player at this position, please rotate the current character")
            return False
        npc_name = "Swordman_"+rn(7)
        npc_obj = game_instance.add_player(
            key = npc_name, 
            name = npc_name, 
            hp = 45,
            x = game_instance.player.x+dx, 
            y = game_instance.player.y+dy, 
            b_generate_items = False, 
            current_map = game_instance.current_map,
            sprite = "swordman"
        )
        npc_obj.equip_item( Sword(name="Long_Sword", damage=7, durability_factor=0.9995), "primary_hand" )
        npc_obj.hunger = npc_obj.max_hunger
        npc_obj.can_use_thrust_skill = True 
        game_instance.place_players()
        game_instance.dirty_tiles.add((game_instance.player.x+dx, game_instance.player.y+dy))
        game_instance.draw()
        return True
    def new_mounted_knight(self, game_instance): # not used yet 
        dx, dy = game_instance.player.get_forward_direction()
        player = game_instance.player 
        spawn_tile = game_instance.map.get_tile(player.x+dx, player.y + dy)
        if not spawn_tile:
            game_instance.add_message("Can't generate player at this position, please rotate the current character")
            return False
        if spawn_tile.current_char:
            game_instance.add_message("Can't generate player at this position, please rotate the current character")
            return False
        npc_name = "Knight_"+rn(7)
        npc_obj = game_instance.add_player(
            key = npc_name, 
            name = npc_name, 
            hp = 80,
            x = game_instance.player.x+dx, 
            y = game_instance.player.y+dy, 
            b_generate_items = False, 
            current_map = game_instance.current_map,
            sprite = "mounted_knight"
        )
        npc_obj.equip_item( Sword(name="Long_Sword", damage=8.5, durability_factor=0.9995), "primary_hand" )
        npc_obj.hunger = npc_obj.max_hunger
        npc_obj.can_use_thrust_skill = True 
        npc_obj.can_use_knight_skill = True 
        game_instance.place_players()
        game_instance.dirty_tiles.add((game_instance.player.x+dx, game_instance.player.y+dy))
        game_instance.draw()
        return True    
    def production(self):
        self.villagers = min( 1.005*self.villagers, self.villagers_max )

# --- END 