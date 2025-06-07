# reality.py 

# project
from events import * 
from serialization import * 
from globals_variables import *
from artificial_behavior import *

# built-in
import random
import math
import os 
from heapq import heappush, heappop
from itertools import product

# third-party 
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QTransform, QColor
from PyQt5.QtWidgets import QGraphicsPixmapItem, QInputDialog
import noise  # Use python-perlin-noise instead of pynoise

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
        self._transparent_image = None
    def get_transparent_image(self):
        if not self._transparent_image:
            self._transparent_image = QPixmap(TILE_SIZE,TILE_SIZE)
            self._transparent_image.fill(Qt.transparent)
        return self._transparent_image
    def get_sprite(self, rotation = 0):
        if not self.sprite: 
            print(f"Warning: {self} sprite not found")
            return self.get_transparent_image()
        try:
            if rotation == 0:
                return Tile.SPRITES[self.sprite]
            else:                
                transform = QTransform().rotate(-rotation)
                return Tile.SPRITES[self.sprite].transformed( transform , mode = 1 )
        except KeyError:
            print(f"Warning: {self} sprite not found")
            return self.get_transparent_image()
    def paint_to(self, painter, game_instance = None):
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
        return f"{self.get_value():.1f} [value]"

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
        if not description: description = "inventory item"
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
        if not description: description = "usable item"
        Item.__init__(self, name = name, description = description, weight = weight, sprite = sprite)
        self.uses = uses 
    def use(self, char):
        self.uses -= 1
        if self.uses <= 0: char.remove_item(self)
        # do something on derived classes 
    def get_utility_info(self):
        return f"({self.uses:.0f})"

class Ammo(Usable):
    __serialize_only__ = Usable.__serialize_only__
    def __init__(self, name="bolt", description="", weight=1, uses = 100):
        if not description: description = "Ammo for Crossbows. Use it to reload."
        Usable.__init__(self, name = name, description = description, weight = weight, sprite=name.lower(), uses = uses )
    def use(self, char):
        primary = char.primary_hand
        if not isinstance(primary, Fireweapon): return 
        if primary.ammo_type != self.name: return 
        d_ammo = min(30, self.uses)
        self.uses -= d_ammo
        if self.uses <= 0: char.remove_item(self)
        primary.ammo += d_ammo

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
    __serialize_only__ = Item.__serialize_only__ + ["durability_factor"]
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
        if not description: description = "equippable item"
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
        if not description: description = "equippable item"
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

class Fireweapon(Weapon, SpecialSkillWeapon): # interface class 
    __serialize_only__ = Weapon.__serialize_only__ + ["ammo", "range", "projectile_sprite","ammo_type"]
    def __init__(self, 
            name="Crossbow", 
            damage=5,
            description="", 
            weight=1, 
            stamina_consumption=1, 
            durability_factor=0.995, 
            ammo = 0, 
            range = 12, 
            projectile_sprite = "bolt",
            ammo_type = "bolt"
        ):
        Weapon.__init__(self, name=name, damage=damage ,description=description, weight=weight, stamina_consumption=stamina_consumption, durability_factor=durability_factor)
        SpecialSkillWeapon.__init__(self)
        if not description: self.description = f"It's a {self.get_quality()} {self.name}. Pressing F you can attack targets at distance."
        self.ammo = ammo 
        self.range = range
        self.projectile_sprite = projectile_sprite
        self.ammo_type = ammo_type
    def perform_attack(self, char, target, positions, game):
        if self.ammo <=0: 
            return False 
        if char is game.player:
            if not char.can_see_character(target, game.map, self.range): 
                return False
        else:
            if not Character.can_see_character(char, target, game.map, self.range):
                return False
        if not target or not positions:
            return False
        game.draw_animation_on_grid(sprite_key = self.projectile_sprite, positions = positions)
        game.events.append( AttackEvent(char, target, d(self.damage/1.5, 2.0*self.damage)) )
        return True 
    def use_special_F(self, char, game):
        # print("Fireweapon.use_special_F() || ...")
        if self.ammo <=0: 
            game.add_message("Not enough ammo")
            return 
        if not char is game.player: return 
        target, positions = self.find_target(char, game)
        if not self.perform_attack(char, target, positions, game):
            game.add_message("Can't find a target")
        game.game_iteration()
    def do_ammo_consumption(self):
        if self.ammo > 0: self.ammo -= 1
    def stats_update(self, player):
        if Weapon.stats_update(self, player):
            self.do_ammo_consumption()
    def find_target(self, char, game):
        # -> find_target() || % player || & find a valid target on range in forward direction | % if a valid target is found return 
        # -> find_target() || % player | % else || & direction : north, south, east, west || & search through direction || % if a valid target is found return 
        map = game.map 
        player = game.player
        x = char.x 
        y = char.y 
        path = []
        if char is player:
            dx, dy = player.get_forward_direction()
            for i in range(self.range):
                if i!=self.range-1: path.append( (x+dx*i,y+dy*i) )
                target = map.get_char(x+dx*i,y+dy*i)
                if isinstance(target, Character) and is_enemy_of(char, target):
                    return target, path 
        else:
            for dx,dy in CARDINAL_DIFF_MOVES:
                path.clear()
                for i in range(self.range):
                    path.append( (x+dx*i,y+dy*i) )
                    target = map.get_char(x+dx*i,y+dy*i)
                    if isinstance(target, Character) and is_enemy_of(char, target):
                        return target, path  
        return None, None
    def get_utility_info(self):
        return f"{self.damage:.1f} [dmg] {self.range} [range] ({self.ammo}) "+Durable.get_utility_info(self)

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
        if not description: self.description = f"It's a {self.get_quality()} {name}. Swords can parry other swords and weapons exchanging hp for stamina consumption, useful against humanoid creatures. You can repair the swords with whetstones."
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
        if not description: self.description = f"It's a {self.get_quality()} mace. A Mace can parry other swords and weapons exchanging hp for stamina consumption, useful against humanoid creatures. You can repair the Maces with whetstones."
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
        if not description: self.description = f"It's an edible, you can store as resource or eat to satiate hunger."
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
        self.description = f"It's a resource, you can store in a building pressing C. Used to buy creatures or building certificates."
    def get_utility_info(self):
        return Resource.get_utility_info(self)

class Stone(Item, Resource):
    __serialize_only__ = Item.__serialize_only__+Resource.__serialize_only__
    def __init__(self, value = 100):
        Item.__init__(self, name="Stone", description="", weight=1, sprite="stone")        
        Resource.__init__(self)
        self.value = value 
        self.type = "stone"
        self.description = f"It's a resource, you can store in a building pressing C. Used to buy creatures or building certificates."
    def get_utility_info(self):
        return Resource.get_utility_info(self)
        
class Metal(Item, Resource):
    __serialize_only__ = Item.__serialize_only__+Resource.__serialize_only__
    def __init__(self, value = 100):
        Item.__init__(self, name="Metal", description="", weight=1, sprite="metal")
        Resource.__init__(self)
        self.value = value 
        self.type = "metal"
        self.description = f"It's a resource, you can store in a building pressing C. Used to buy creatures or building certificates."
    def get_utility_info(self):
        return Resource.get_utility_info(self)
        
# WeaponRepairTool.use() || { Usable.use() } || { Character.remove_item() }
class WeaponRepairTool(Usable):
    __serialize_only__ = Usable.__serialize_only__+["repairing_factor"]
    def __init__(self, name="", repairing_factor=1.05, description="", weight=1, uses = 10):
        Usable.__init__(self, name = name, description = description, weight = weight, sprite=name.lower(), uses = uses)
        self.repairing_factor = repairing_factor
        if not description: self.description = f"It's a repair tool, press R to repair the currently primary hand weapon."
    def use(self, char):        
        primary = char.primary_hand 
        secondary = char.secondary_hand 
        if primary:
            if primary.damage < 0.9*primary.max_damage:
                super().use(char)
                primary.damage = min( self.repairing_factor*primary.damage, primary.max_damage)
                return True
        if secondary: 
            if secondary.damage < 0.9*secondary.max_damage:
                super().use(char)
                secondary.damage = min( self.repairing_factor*secondary.damage, secondary.max_damage)
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
        return False 
        
class OfensiveCharacter(Damageable):
    __serialize_only__ = Damageable.__serialize_only__ + ["base_damage"]
    def __init__(self):
        Damageable.__init__(self)
        self.base_damage = 0
    def do_damage(self):
        damage = self.base_damage
        if self.primary_hand and hasattr(self.primary_hand, 'damage'):
            if not isinstance(self.primary_hand, Fireweapon):
                damage += d(self.primary_hand.damage/2.0, 1.5*self.primary_hand.damage)
        if self.secondary_hand and hasattr(self.secondary_hand, 'damage'):
            if not isinstance(self.primary_hand, Fireweapon):
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
            return True 
        else:
            super().receive_damage(attacker, damage)
            return False 
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
                primary_parry = primary_parry/3.0
                secondary_parry = secondary_parry/2.5
        if isinstance(self, Hero): print("Parry Chance :", primary_parry+secondary_parry)
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
        self.current_target = None # Attacking Target, never serialize this, can lead to infinite saving. 
        self.current_target_building = None # Building Target, never serialize this, can lead to infinite saving. 
        self.current_target_healing = None # Healing Target, never serialize this, can lead to infinite saving. 
        self.current_target_tile = None # Tile Destination Target, never serialize this, can lead to infinite saving. 
    def behaviour_update(self, game_instance): 
        if hasattr(self,"current_map"):
            if self.current_map != game_instance.map.coords: return False
            if self.current_map != game_instance.current_map: return False 
        return AB_behavior_default(char=self, game_instance=game_instance)
        
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
    __serialize_only__ = EquippedCharacter.__serialize_only__ + BehaviourCharacter.__serialize_only__ +  ["name", "description"]
    def __init__(self, name="", hp=100, x=50, y=50):
        EquippedCharacter.__init__(self)
        BehaviourCharacter.__init__(self)
        self.name = name
        self.description = ""
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
    def can_see_character(self, another, game_map, max_dist = 7):
        if not isinstance(another, Character): return None
        distance = self.distance(another)
        if distance <= max_dist:
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
    def update_available_skills(self):
        pass 

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
        RegenerativeCharacter.__init__(self)
        SkilledCharacter.__init__(self, name = name, hp = hp, x = x, y = y)
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
        self.equip_item(Sword(name="Bastard_Sword", damage=8.5, durability_factor=0.9995, description="Although with no name, this Bastard Sword was master-crafted and passed as heirloom in generations of my family, that swords reminds me of the values my father teach me ..."), "primary_hand")
        self.add_item(WeaponRepairTool(name="Whetstone", uses=12))
        self.add_item(Food(name="Bread", nutrition=250))
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
    def _angle(self, v1, v2):
        dir_norm = self._normalize(v1)
        vec_norm = self._normalize(v2)
        # Compute dot product and angle
        dot = dir_norm[0]*vec_norm[0] + dir_norm[1]*vec_norm[1]
        angle_rad = math.acos(max(min(dot, 1.0), -1.0)) # Clamp dot to avoid domain errors
        angle_deg = math.degrees(angle_rad)
        return angle_deg
    def _signed_angle(self, v1, v2):
        dir_norm = self._normalize(v1)
        vec_norm = self._normalize(v2)
        # Dot product for angle magnitude
        dot = dir_norm[0]*vec_norm[0] + dir_norm[1]*vec_norm[1]
        dot = max(min(dot, 1.0), -1.0)  # Clamp to avoid domain errors
        angle_rad = math.acos(dot)
        # Cross product (scalar in 2D) to get the sign
        cross = dir_norm[0]*vec_norm[1] - dir_norm[1]*vec_norm[0]
        # Right-hand rule: positive if v2 is counter-clockwise from v1
        if cross < 0: angle_rad = -angle_rad
        angle_deg = math.degrees(angle_rad)
        return angle_deg    
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
        vec_to_point = (point[0] - observer[0], point[1] - observer[1])
        return self._angle(direction, vec_to_point) <= fov_deg / 2.0
    def can_see_character(self, another, game_map, max_dist=7):
        if super().can_see_character(another, game_map, max_dist):
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
        """ return True if a behaviour is selected, return False if no behaviour was select so the entity is free to perform another task """
        if hasattr(self,"current_map"):
            if self.current_map != game_instance.map.coords: return False
            if self.current_map != game_instance.current_map: return False
        if AB_behavior_default(char=self, game_instance=game_instance):
            self.regenerate_stamina()
            self.regenerate_health()
            return True 
        return False 
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
    def get_sprite_with_hud(self):
        pix = QPixmap(self.get_sprite())
        if pix is None: return None 
        painter = QPainter(pix)
        self.paint_hp_hud_to(painter)
        painter.end()
        return pix 
    def paint_hp_hud_to(self, painter):
        painter.setPen(QColor("black"))
        painter.setBrush(QColor("red"))
        painter.drawRect(0,TILE_SIZE-10,int(self.hp/self.max_hp*TILE_SIZE),5)
    def paint_to(self, painter, game_instance = None):
        Entity.paint_to(self, painter)
        if game_instance and not (self is game_instance.player):
            self.paint_hp_hud_to(painter)

class Healer(Player):
    __serialize_only__ = Player.__serialize_only__
    def __init__(self, name="", hp=PLAYER_MAX_HP, x=MAP_WIDTH//2, y=MAP_HEIGHT//2, b_generate_items = False, sprite = "player", current_map = (0,0,0)):
        Player.__init__(self, name=name, hp=hp, x=x, y=y, b_generate_items = b_generate_items, sprite = sprite, current_map = current_map)
        self.sprite = Tile.get_random_sprite("sorceress") 
    def behaviour_update(self, game_instance):
        if hasattr(self,"current_map"):
            if self.current_map != game_instance.map.coords: return False
            if self.current_map != game_instance.current_map: return False
        if AB_behavior_healer(char = self, game_instance = game_instance):
            self.regenerate_stamina()
            self.regenerate_health()
            return True 
        return False 
    def heal_skill(self, target, game_instance):
        if self.stamina <= 20: 
            if self is game_instance.player: game_instance.add_message(f"Not Enough Energy to Heal")
            return False 
        self.stamina -= 20 
        cure = 0.1*target.max_hp 
        if target.hp >= target.max_hp: return False 
        target.hp = min( target.max_hp, target.hp + cure )
        if self is game_instance.player: game_instance.add_message(f"Healed {cure} hp points of {target.name}")
        return True 

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
        if len(self.party_members) >= 7: return 
        # -- 
        self.party_members.add(key)
        npc.party = True
        game_instance.map.remove_character(npc)
        game_instance.update_prior_next_selection()
        game_instance.update_all_gui()
        game_instance.draw()
    def release_party_member(self, key, game_instance):
        x = self.x 
        y = self.y 
        if not key in self.party_members: return 
        for dx,dy in CROSS_DIFF_MOVES_1x1:
            if not game_instance.map.can_place_character_at(x+dx,y+dy): continue 
            if dx == 0 and dy == 0: continue
            value = game_instance.players.get(key, None)
            if value is None: # Bug Fix - Character can't Release Party
                self.party_members.remove(key)
                continue 
            if not value.party: 
                self.party_members.remove(key)
                continue         
            value.x = x+dx 
            value.y = y+dy 
            value.party = False 
            self.party_members.remove(key)
            game_instance.map.place_character(value)
            game_instance.draw()
            break 
        game_instance.update_all_gui() 
    def release_party(self, game_instance):
        game_instance.check_player_dict()
        x = self.x 
        y = self.y 
        for dx,dy in CROSS_DIFF_MOVES_1x1:
            if not game_instance.map.can_place_character_at(x+dx,y+dy): continue 
            if dx == 0 and dy == 0: continue
            to_remove = set()
            for key in self.party_members:
                value = game_instance.players.get(key, None)
                if value is None: # Bug Fix - Character can't Release Party
                    to_remove.add(key) # self.party_members.remove(key)
                    continue 
                if value and value.party:
                    value.x = x+dx 
                    value.y = y+dy 
                    value.party = False 
                    self.party_members.remove(key)
                    game_instance.map.place_character(value)
                    game_instance.draw()
                    break 
            for key in to_remove:
                self.party_members.remove(key)
        game_instance.update_all_gui() 
    def count_party(self):
        return len(self.party_members)
    
class Enemy(Character, OfensiveCharacter):
    __serialize_only__ = Character.__serialize_only__ + OfensiveCharacter.__serialize_only__ +["type","stance","canSeeCharacter","patrol_direction"]
    def __init__(self, name="", hp=30, x=50, y=50, b_generate_items = False):
        OfensiveCharacter.__init__(self)
        Character.__init__(self, name = name, hp = hp, x = x, y = y)
        self.description = ""
        self.type = "Generic"
        self.stance = "Aggressive"
        self.canSeeCharacter = False
        self.patrol_direction = (random.choice([-1, 1]), 0)
        self.sprite = "enemy"
        self.activity = 0.3 
        self.tolerance = 15 
        if b_generate_items: self.generate_initial_items()
    
class Raider(Enemy): # interface class, is an enemy that will try to find the nearest building if don't find any target 
    __serialize_only__ = Enemy.__serialize_only__
    def __init__(self, name="", hp=30, x=50, y=50, b_generate_items = False, sprite = "enemy"):
        Enemy.__init__(self, name=name, hp=hp, x=x, y=y, b_generate_items = b_generate_items)
        self.sprite = sprite 
        self.base_damage = 5
    def pursue_target(self, entities, game_instance, default_target = None):
        """ return True if a behaviour is selected, return False if no behaviour was select so the entity is free to perform another task """
        enemy, distance = self.get_closest_visible(entities, game_instance, default_target)
        map = game_instance.map 
        if not enemy or not distance: return False 
        if isinstance(enemy, TileBuilding):
            if distance <= 3: return False 
            path = map.find_path(self.x, self.y, enemy.x, enemy.y)
            # if distance < 10 : print("pursue_target() || distance :", enemy, distance, game_instance.player.distance(self))
            if path:
                next_x, next_y = path[0]
                dx, dy = next_x - self.x, next_y - self.y
                tile = map.get_tile(next_x, next_y)
                if tile:
                    if tile.can_place_character():
                        self.move(dx, dy, map)
                        return True 
                    elif tile.current_char is enemy and isinstance(enemy, Damageable):
                        damage = self.do_damage()
                        game_instance.events.append(AttackEvent(self, enemy, damage))
                        if isinstance(self, Player):print(self, damage)
                        return True 
        else:        
            if distance <= self.tolerance:
                path = map.find_path(self.x, self.y, enemy.x, enemy.y)
                if path:
                    next_x, next_y = path[0]
                    dx, dy = next_x - self.x, next_y - self.y
                    tile = map.get_tile(next_x, next_y)
                    if tile:
                        if tile.can_place_character():
                            self.move(dx, dy, map)
                            return True 
                        elif tile.current_char is enemy and isinstance(enemy, Damageable):
                            damage = self.do_damage()
                            game_instance.events.append(AttackEvent(self, enemy, damage))
                            if isinstance(self, Player):print(self, damage)
                            return True 
        return False     
    def behaviour_update(self, game_instance):
        """ return True if a behaviour is selected, return False if no behaviour was select so the entity is free to perform another task """
        if hasattr(self,"current_map"):
            if self.current_map != game_instance.map.coords: return False
            if self.current_map != game_instance.current_map: return False
        return AB_behavior_raider(char=self, game_instance=game_instance)
        # primary = self.primary_hand 
        # if isinstance(primary, Fireweapon):            
            # target, path = primary.find_target(self, game_instance)
            # if primary.perform_attack(self, target, path, game_instance): return True 
        # if self.pursue_target(game_instance.players, game_instance, game_instance.player): return True 
        # if len(game_instance.map.buildings)>0:
            # if self.pursue_target(game_instance.map.buildings, game_instance): 
                # return True 
        # self.random_walk(game_instance) 
        # return True 
    def generate_initial_items(self):
        self.equip_item(Sword("Long_Sword", damage=10), "primary_hand")
        if random.random() < 0.3:
            self.add_item(Food(name="bread", nutrition=random.randint(50, 100)))

class RangedRaider(Raider):
    __serialize_only__ = Raider.__serialize_only__
    def __init__(self, name="", hp=30, x=50, y=50, b_generate_items = False, sprite = "enemy"):
        Raider.__init__(self, name=name, hp=hp, x=x, y=y, b_generate_items = b_generate_items, sprite = sprite)
    def generate_initial_items(self):
        # __init__(self, name='Crossbow', damage=7, description='', weight=1, stamina_consumption=1, durability_factor=0.995, ammo=0, range=12, projectile_sprite='bolt', ammo_type='bolt')
        self.equip_item(Fireweapon(name = "Crossbow", damage = 5, ammo=70, range=7, projectile_sprite='bolt', ammo_type='bolt'), "primary_hand")
        if random.random() < 0.3:
            self.add_item(Food(name="bread", nutrition=random.randint(50, 100)))

class Zombie(Enemy):
    __serialize_only__ = Enemy.__serialize_only__
    def __init__(self, name="", hp=40, x=50, y=50, b_generate_items = False):
        Enemy.__init__(self, name = name, hp = hp, x = x, y = y, b_generate_items = b_generate_items)
        self.type = "Zombie"
        self.description = "Zombies, people affected by the plague, they are still alive but because of this strange disease their bodies smells like rotten flesh. Before they lose their minds, they try to acummulate food to satiate hunger, it's almost certain to find food with them ..."
        self.sprite = Tile.get_random_sprite("zombie")
    def do_damage(self):
        return d(5, 25)
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
        self.base_damage = 5
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
        self.base_damage = 5
    def generate_initial_items(self):
        self.equip_item(Mace("mace", damage=10), "primary_hand")
        if random.random() < 0.3:
            self.add_item(Food(name="bread", nutrition=random.randint(50, 100)))
        else:
            self.add_item(Food(name="meat", nutrition=random.randint(150, 200)))
    
class Bear(Enemy):
    __serialize_only__ = Enemy.__serialize_only__
    def __init__(self, name="", hp=80 , x=50, y=50, b_generate_items = False):
        Enemy.__init__(self, name = name, hp = hp, x = x, y = y, b_generate_items = b_generate_items)
        self.description = "Bears, these woods are their home, stronger than any man, don't try to mess with them ..."
        self.sprite = "bear"
        self.activity = 0.1
        self.tolerance = 10 
        self.base_damage = 20
    def generate_initial_items(self):
        self.add_item(Food(name="meat", nutrition=250))
    def behaviour_update(self, game_instance):
        if hasattr(self,"current_map"):
            if self.current_map != game_instance.map.coords: return False
            if self.current_map != game_instance.current_map: return False
        return AB_behavior_grudge(char=self, game_instance=game_instance)
        
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
    def get_transparent_image(self):
        # todo 
        return 
    def paint_items(self, painter):
        if len(self.items) == 0: return 
        if len(self.items) == 1: self.items[0].paint_to(painter)
        if len(self.items) > 1:
            painter.drawPixmap(0, 0, Tile.SPRITES.get("sack", self.get_default_pixmap() ))
    def draw(self, scene, x, y, tile_size = TILE_SIZE, extra_pixmap = None, game_instance = None):
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
        if self.current_char: self.current_char.paint_to(painter, game_instance = game_instance) 
        if not extra_pixmap is None:
            painter.drawPixmap(0, 0, extra_pixmap )
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
    def is_grass(self):
        if self.default_sprite_key == "grass": return True 
        idx = self.get_layer_index("grass")
        if idx is None: return False 
        return True 
    def is_rock(self):
        if self.default_sprite_key == "rock": return True 
        idx = self.get_layer_index("rock")
        if idx is None: return False 
        return True 
    def is_water(self):
        if self.default_sprite_key == "water": return True 
        if self.default_sprite_key == "shallow_water": return True 
        idx1 = self.get_layer_index("water")
        idx2 = self.get_layer_index("shallow_water")
        if idx1 is None and idx2 is None: return False 
        return True 
    def is_forest(self):
        if self.default_sprite_key == "tree": return True 
        idx = self.get_layer_index("tree")
        if idx is None: return False 
        return True 
    
    @classmethod    
    def get_rotated_sprite(cls, key, rotation = 0):
        transform = QTransform().rotate(-rotation)
        return cls.SPRITES[key].transformed( transform , mode = 1 )
    
    @classmethod    
    def get_random_sprite(cls, key_filter=""):
        cdts = [ key for key in cls.SPRITES.keys() if key_filter in key ]
        if cdts: return random.choice(cdts)
        return None

    @classmethod
    def _try_load(cls, key, size = TILE_SIZE):
        # cls.SPRITES will store the sprites in memory 
        try: 
            qpx = QPixmap("./assets/"+key)
            print(f"Loading Sprite {key}")
            cls.SPRITES[key] = qpx.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        except Exception as e:
            print(f"Failed to load sprites: {e}, key {key}")
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
    __serialize_only__ = Tile.__serialize_only__ + ["villagers", "villagers_max", "food", "stone", "metal", "wood", "b_enemy", "turn_counter"]
    def __init__(self, x=0,y=0,front_sprite = "Castle", walkable=True, sprite_key="grass", b_enemy = False):
        ActionTile.__init__(self, x = x, y = y, front_sprite = front_sprite, walkable=walkable, sprite_key=sprite_key )
        self.villagers = 5
        self.villagers_max = 40
        self.food = 0
        self.wood = 0
        self.stone = 0
        self.metal = 0
        self.turn_counter = 0 
        self.b_enemy = b_enemy
        if self.b_enemy: self.villagers = self.villagers_max 
        self.enemy_table = TILE_BUILDING_ENEMY_TABLE 
    def clear_resources(self):
        self.food = 0
        self.wood = 0
        self.stone = 0
        self.metal = 0 
    def bonus_resources(self, max = 100):
        self.food += d(0,max)
        self.wood += d(0,max)
        self.stone += d(0,max)
        self.metal += d(0,max) 
    def production(self, multiplier = 1.0):
        if self.b_enemy: return 
        self.villagers = min( (1.0+0.005*multiplier)*self.villagers, self.villagers_max )
        self.food += multiplier*d(0,self.villagers/PROD_INV_FACTOR)
        self.wood += multiplier*d(0,self.villagers/PROD_INV_FACTOR)
        self.stone += multiplier*d(0,self.villagers/PROD_INV_FACTOR)
        self.metal += multiplier*d(0,self.villagers/PROD_INV_FACTOR)
    def enemy_building_update(self, ply_dist, map):
        if not self.b_enemy: 
            self.remove_layer("red_flag")
            return         
        self.add_layer_if_not_already("red_flag")
        if ply_dist >= 4: return 
        if not map.can_place_character_at(self.x, self.y): return 
        if self.villagers > 0:
            enemy = map.generate_enemy_by_chance_by_list_at(self.x, self.y, self.enemy_table)
            if enemy:
                self.villagers -= 5
                map.enemies.append(enemy)
                map.place_character(enemy)
        else:
            self.b_enemy = False 
            self.villagers = 1
            self.bonus_resources() 
    def building_attack(self, game_instance):
        return True 
    def update(self, game_instance = None):
        if not game_instance: return 
        mult = 1.0
        if self.turn_counter > 500*game_instance.turn: mult = 10.0 # still better to stay in the map
        self.turn_counter = game_instance.turn
        self.production(multiplier = mult)
        ply_dist = game_instance.player.distance(self)
        map = game_instance.map
        # message when close to a village 
        if ply_dist < 20:
            game_instance.flag_near_to_village = True 
        else:
            game_instance.flag_near_to_village = False 
        # -- 
        self.building_attack(game_instance)
        # -- 
        self.enemy_building_update(ply_dist, map)
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
    def retrieve_metal(self, game_instance, quantity = 500):
        if self.metal >= quantity:
            self.metal -= quantity
            game_instance.player.add_item(Metal(value = quantity))
            game_instance.update_inv_window()
            return True 
        return False
    def retrieve_stone(self, game_instance, quantity = 500):
        if self.stone >= quantity:
            self.stone -= quantity
            game_instance.player.add_item(Stone(value = quantity))
            game_instance.update_inv_window()
            return True 
        return False
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
                hero.x = player.x + dx
                hero.y = player.y + dy
                self.heroes.pop(current_item)
                game_instance.players.update({current_item: hero})
                print( hero.name, hero.party, hero.current_map )
                game_instance.place_players()
                game_instance.update_prior_next_selection() # -- fix -- Can't cycle hero that comes from garrison
                if game_instance.journal_window: game_instance.journal_window.update_journal() 
                game_instance.draw()
                return True
        return False
    def menu_resources(self, current_menu, current_item, menu_instance, game_instance):
        """ return True means that the menu should close """
        from gui import info 
        # counter = [0]
        # def resource_counter(obj, counter):
            # if isinstance(obj, Food) or isinstance(obj, Resource):
                # counter[0] += 1
                # return True
            # else:
                # return False
        resources = { e.info() : e for e in game_instance.player.items if isinstance(e, Food) or isinstance(e, Resource) }
        # -- 
        if current_item == "Resources >":
            menu_instance.set_list("Resources >",[ 
                f"-> food: {self.food:.0f}", 
                f"-> wood: {self.wood:.0f}", 
                f"-> metal: {self.metal:.0f}", 
                f"-> stone: {self.stone:.0f}", 
                "Resources+", 
                "Resources++", 
                "Resources--",
                "Food-", 
                "Wood-", 
                "Metal-", 
                "Stone-", 
                ".." 
            ])
            return False 
        # -- 
        if current_menu == "Resources >":
            match current_item:
                case "..":
                    menu_instance.set_list()
                    return False
                case "Resources+":
                    if self.update_resource_p_menu(menu_instance, resources): return False 
                    # if len(resources) > 0:
                        # menu_instance.set_list("Resources+", list(resources.keys()))
                        # return False # necessary ? 
                case "Resources++":
                    if len(resources) > 0:
                        for k,v in iter(resources.items()):
                            self.store_resource(v, game_instance.player)
                        game_instance.update_inv_window()
                        return True 
                case "Food-":
                    qtt, ok = QInputDialog.getDouble(
                        menu_instance, 
                        'Input Dialog', 
                        f'Quantity ({self.food:.1f}) :',
                        self.food
                    )
                    if ok and qtt > 0 and self.retrieve_food(game_instance, qtt):
                        return True 
                case "Wood-":
                    qtt, ok = QInputDialog.getDouble(
                        menu_instance, 
                        'Input Dialog', 
                        f'Quantity ({self.wood:.1f}) :',
                        self.wood 
                    )
                    if ok and qtt > 0 and self.retrieve_wood(game_instance, qtt):
                        return True 
                case "Metal-":
                    qtt, ok = QInputDialog.getDouble(
                        menu_instance, 
                        'Input Dialog', 
                        f'Quantity ({self.metal:.1f}) :',
                        self.metal 
                    )
                    if ok and qtt > 0 and self.retrieve_metal(game_instance, qtt):
                        return True
                case "Stone-":
                    qtt, ok = QInputDialog.getDouble(
                        menu_instance, 
                        'Input Dialog', 
                        f'Quantity ({self.stone:.1f}) :',
                        self.stone 
                    )
                    if ok and qtt > 0 and self.retrieve_stone(game_instance, qtt):
                        return True 
                case "Resources--":
                    if self.food>0.1: self.retrieve_food(game_instance, self.food)
                    if self.wood>0.1: self.retrieve_wood(game_instance, self.wood)
                    if self.metal>0.1: self.retrieve_metal(game_instance, self.metal)
                    if self.stone>0.1: self.retrieve_stone(game_instance, self.stone)
                    return True 
        if current_menu == "Resources+":
            if current_item in resources:
                res_obj = resources.pop(current_item)
                self.store_resource(res_obj, game_instance.player)
                game_instance.update_inv_window()
                return not self.update_resource_p_menu(menu_instance, resources)
        return False 
    def update_resource_p_menu(self, menu_instance, resources):
        if len(resources) > 0:
            menu_instance.set_list("Resources+", [f"-> food: {self.food:.0f}", f"-> wood: {self.wood:.0f}", f"-> metal: {self.metal:.0f}", f"-> stone: {self.stone:.0f}", ]+list(resources.keys())+[".."])
            return True 
        return False 
    def set_population_menu(self, menu_instance):
         menu_instance.set_list( "Overview >" ,
            [f"Population : {self.villagers:.1f}/{self.villagers_max}",f"Mean Production : {self.villagers/PROD_INV_FACTOR/2.0:.1f}/turn"]+[f"Food : {self.food:.1f}" if self.food else None ]+[f"Wood : {self.wood:.1f}" if self.wood else None ]+[f"Stone : {self.stone:.1f}" if self.stone else None ]+[f"Metal : {self.metal:.1f}" if self.metal else None ]+[".."]
         )
    def refresh_game_instance(self, x, y, game_instance):
        game_instance.place_players()
        game_instance.update_prior_next_selection()
        game_instance.dirty_tiles.add((x, y))
        game_instance.draw()
    def add_char_to_garrison(self, char):
        # meant to be used on building creation.
        if not hasattr( self,"heroes" ): return False # not meant to be used without that attribute 
        self.heroes.update({ char.name : char })
        return True 
    def set_background_sprite(self, sprite_key):
        self.default_sprite_key = sprite_key 
    def set_background_tile(self, tile):
        self.default_sprite_key = tile.default_sprite_key 

# Castle.action() || { Castle.update_menu_list() | Castle.new_npc() | TileBuilding.menu_garrison() | TileBuilding.menu_resources() } || { Character.add_item(), TileBuilding.update_inv_window(), Character.remove_item() }
class Castle(TileBuilding):
    __serialize_only__ = TileBuilding.__serialize_only__ + ["name","heroes","num_heroes"]
    def __init__(self, x=0, y =0, name = "Home", b_enemy=False):
        TileBuilding.__init__(self, x=x,y=y, front_sprite = "castle", walkable=True, sprite_key="grass", b_enemy=b_enemy)
        self.name = name 
        self.heroes = {}
        self.num_heroes = 0
        self.menu_list = []    
    def production(self, multiplier = 1.0):
        if self.b_enemy: return 
        if self.villagers == 0: self.villagers = 0.1
        self.villagers = min( (1.0+0.005*multiplier)*self.villagers, self.villagers_max )
        self.food += multiplier*d(0,self.villagers/PROD_INV_FACTOR)
    def action(self):
        from gui import info 
        self.update_menu_list()
        def f(current_menu, current_item, menu_instance, game_instance):
            self.update_menu_list(menu_instance)
            if current_item == "..": menu_instance.set_list()
            if current_item == "Overview >": self.set_population_menu(menu_instance)
            if current_item == "Exit": menu_instance.close()
            if current_item == "Certificates >": 
                menu_instance.set_list("Certificates >", ["Lumber Mill (500 Wood, 250 Food)", "Farm (500 Wood, 500 Food)", "Guard Tower (2000 Wood, 2500 Food)", ".."])
                return 
            if "Weapon Repair" in current_item: 
                if self.metal >= 100:
                    self.metal -= 100
                    game_instance.player.add_item(WeaponRepairTool(name="Whetstone", uses=10))
                    game_instance.add_message("Whetstone Added to Inventory")
                    game_instance.update_inv_window()
                    menu_instance.close()
                    return 
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
                        self.food -= 2000 
                        self.villagers -= 15
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
            "Certificates >",
            "Weapon Repair (100 Metal)",
            "Exit"
        ]
    def new_hero(self, game_instance):
        if self.villagers <= 15: 
            game_instance.add_message("There are no villagers to recruit ...")
            return False 
        dx, dy = game_instance.player.get_forward_direction()
        player = game_instance.player 
        spawn_tile = game_instance.map.get_tile(player.x+dx, player.y + dy)
        if not spawn_tile:
            print("invalid tile")
            game_instance.add_message("Can't generate player at this position, please rotate the current character")
            return False
        if spawn_tile.current_char:
            print("tile occupied by character")
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
        self.refresh_game_instance(game_instance.player.x+dx, game_instance.player.y+dy, game_instance)
        return True
    
    @classmethod
    def new(cls, game_instance, x = None,y = None):
        if not x: x = game_instance.player.x
        if not y: y = game_instance.player.y
        obj = Castle(x=x,y=y)
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
    def production(self, multiplier = 1.0):
        if self.b_enemy: return 
        self.villagers = min( (1.0+0.005*multiplier)*self.villagers, self.villagers_max )
        self.food += multiplier*d(0,2*self.villagers/PROD_INV_FACTOR)

# LumberMill.action() || { LumberMill.update_menu_list() | TileBuilding.menu_resources() } || { Character.add_item(), TileBuilding.update_inv_window(), Character.remove_item() }
class LumberMill(TileBuilding):
    __serialize_only__ = TileBuilding.__serialize_only__ + ["name"]
    def __init__(self, x=0, y =0, name = "Lumber Mill", wood = d(500,2000), b_enemy=False):
        TileBuilding.__init__(self, x=x,y=y,front_sprite = "lumber_mill", walkable=True, sprite_key="grass", b_enemy=b_enemy)
        self.name = name 
        self.menu_list = []
        self.wood = wood
        self.melt_weap_dict = None
    def update_melt_menu(self, menu_instance):
        menu_instance.set_list("Melt Weapons >", ["Lumber Mill > Melt Weapons"] + list(self.melt_weap_dict.keys())+[".."])
    def action(self):
        self.update_menu_list()
        def f(current_menu, current_item, menu_instance, game_instance):
            self.update_menu_list(menu_instance)
            if current_item == "..": 
                menu_instance.set_list()
                return 
            if current_item == "Exit": 
                menu_instance.close()
                return     
            if current_menu == "main":
                if current_item == "Overview >": 
                    self.set_population_menu(menu_instance)
                    return 
                if current_item == "Buy 100 Bolts for Crossbows (500 Wood)": 
                    if self.wood >= 500:
                        self.wood -= 500
                        game_instance.player.add_item( Ammo(name="bolt", uses=100) )
                        game_instance.add_message("100 Bolts Added to Inventory")
                        game_instance.update_inv_window()
                        menu_instance.close()
                        return 
                if current_item == "Melt Weapons >":
                    self.melt_weap_dict = { it.info() : it for it in game_instance.player.items if isinstance(it, Sword) or isinstance(it, Mace) }
                    self.update_melt_menu(menu_instance)
                    return 
            if self.menu_resources(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
            if current_menu == "Melt Weapons >":
                if self.melt_weap_dict:
                    if current_item in self.melt_weap_dict:
                        game_instance.player.remove_item( self.melt_weap_dict.pop(current_item) )
                        self.metal += 50 
                        self.update_melt_menu(menu_instance)
                        return 
        return f
    def update_menu_list(self, selection_box_instance = None):
        self.menu_list.clear()
        self.menu_list += [
            f"Resource [{self.name}]",
            f"-> wood: {self.wood:.0f}",
            "Overview >",
            "Resources >",
            "Buy 100 Bolts for Crossbows (500 Wood)",
            "Melt Weapons >",
            "Exit"
        ]
    def production(self, multiplier = 1.0):
        if self.b_enemy: return 
        self.villagers = min( (1.0+0.005*multiplier)*self.villagers, self.villagers_max )
        self.wood += multiplier*d(0,2*self.villagers/PROD_INV_FACTOR)

# GuardTower.action() || { GuardTower.update_menu_list() | GuardTower.new_swordman() | GuardTower.new_mounted_knight() | TileBuilding.menu_garrison() | TileBuilding.menu_resources() } || { Character.add_item(), TileBuilding.update_inv_window(), Character.remove_item() }
class GuardTower(TileBuilding):
    __serialize_only__ = TileBuilding.__serialize_only__ + ["name","heroes","num_heroes","turret"]
    def __init__(self, x=0, y =0,name = "Guard Tower", b_enemy=False, floor_sprite = "grass"):
        TileBuilding.__init__(self, x=x, y=y, front_sprite = "tower", walkable=True, sprite_key=floor_sprite, b_enemy=b_enemy)
        self.name = name 
        self.heroes = {}
        self.num_heroes = 0
        self.menu_list = []
        self.turret = None
        if self.b_enemy: self.add_enemy_turret() 
    def add_enemy_turret(self):
        self.turret = RangedRaider(name='turret', hp=200, b_generate_items=True, sprite='evil_crossbowman')
    def building_attack(self, game_instance):
        if self.turret is None: return False 
        self.turret.x = self.x 
        self.turret.y = self.y
        if self.turret.hp <= 0 or self.villagers <= 0 : 
            self.turret = None 
            return False 
        primary = self.turret.primary_hand 
        if primary and primary.ammo <= 0: # ammo recharge  
            if self.b_enemy: 
                primary.ammo += 50 
            else: 
                if self.wood >=10 and self.metal >= 10: 
                    primary.ammo += 50 
                    self.wood -= 10 
                    self.metal -= 10 
        if AB_ranged_attack(char=self.turret, game_instance=game_instance): return True 
    def add_sentinel(self, game_instance): 
        if self.b_enemy: return False 
        if self.villagers < 2: 
            game_instance.add_message("Not enough villagers to recruit ...") 
            return False 
        if isinstance(self.turret, Player): 
            self.turret.hp += 50 
            return True 
        else: 
            self.turret = Player(name = "turret", hp=50,x=self.x, y=self.y) 
            self.turret.equip_item(Fireweapon(name = "Crossbow", damage = 7, ammo=100, range=7, projectile_sprite='bolt', ammo_type='bolt'), "primary_hand")
            return True 
    def action(self):
        from gui import info 
        self.update_menu_list()
        def f(current_menu, current_item, menu_instance, game_instance):
            self.update_menu_list(menu_instance)
            if current_item == "..": menu_instance.set_list()
            if current_item == "Overview >": self.set_population_menu(menu_instance)
            if current_item == "Exit": menu_instance.close()
            if "Add a Tower Sentinel" in current_item:
                if self.food >= 200 and self.wood >= 400:
                    if self.add_sentinel(game_instance):
                        self.villagers -= 2 
                        self.food -= 200 
                        self.wood -= 400 
                else:
                    game_instance.add_message("Can't afford to purchase a sentinel ...")
                menu_instance.close()
                return 
            if "Recruit Swordman" in current_item: 
                if self.food >= 500: 
                    if self.new_swordman(game_instance):
                        self.villagers -= 2 
                        self.food -= 500 
                else:
                    game_instance.add_message("Can't afford to purchase Swordman ...")
                menu_instance.close()
                return 
            if "Recruit Crossbowman" in current_item:
                if self.food >= 400 and self.wood >= 700:
                    if self.new_crossbowman(game_instance):
                        self.villagers -= 3
                        self.food -= 400 
                        self.wood -= 700 
                else:
                    game_instance.add_message("Can't afford to purchase Swordman ...")
                menu_instance.close()
                return 
            if "Recruit Mounted Knight" in current_item:
                if self.food >= 700 and self.wood >= 1200:
                    if self.new_mounted_knight(game_instance):
                        self.villagers -= 5 
                        self.food -= 700 
                        self.wood -= 1200 
                else:
                    game_instance.add_message("Can't afford to purchase Mounted Knight ...")
                menu_instance.close()
                return 
            if self.menu_garrison(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
            if self.menu_resources(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
        return f
    def update_menu_list(self, selection_box_instance = None):
        self.menu_list.clear()
        if self.turret:
            sentinel_str = f"-> sentinel: {self.turret.hp} (HP) {self.turret.primary_hand.ammo} (Shoots)"
        else:
            sentinel_str = f"-> sentinel: {0} (HP)"
        self.menu_list += [
            f"Building [{self.name}]",
            sentinel_str, 
            f"-> garrison: {len(self.heroes)}",
            f"-> food: {self.food:.0f}",
            f"-> wood: {self.wood:.0f}",
            f"-> metal: {self.metal:.0f}",
            f"-> stone: {self.stone:.0f}",
            "Overview >",
            "Add a Tower Sentinel +50 HP (200 Food, 400 Wood)", 
            "Recruit Swordman (500 Food)",
            "Recruit Crossbowman (400 Food, 700 Wood)",
            "Recruit Mounted Knight (700 Food 1200 Wood)",
            "Garrison >",
            "Resources >",
            "Exit"
        ]
    def new_swordman(self, game_instance):
        if self.villagers <= 2:
            game_instance.add_message("There are no villagers to recruit ...")
            return False 
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
        self.refresh_game_instance(game_instance.player.x+dx, game_instance.player.y+dy, game_instance)
        return True
    def new_mounted_knight(self, game_instance): # not used yet 
        if self.villagers <= 5:
            game_instance.add_message("There are no villagers to recruit ...")
            return False 
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
        self.refresh_game_instance(game_instance.player.x+dx, game_instance.player.y+dy, game_instance)
        return True    
    def new_crossbowman(self, game_instance):
        if self.villagers <= 3:
            game_instance.add_message("There are no villagers to recruit ...")
            return False 
        dx, dy = game_instance.player.get_forward_direction()
        player = game_instance.player 
        spawn_tile = game_instance.map.get_tile(player.x+dx, player.y + dy)
        if not spawn_tile:
            game_instance.add_message("Can't generate player at this position, please rotate the current character")
            return False
        if spawn_tile.current_char:
            game_instance.add_message("Can't generate player at this position, please rotate the current character")
            return False
        npc_name = "Crossbowman_"+rn(7)
        npc_obj = game_instance.add_player(
            key = npc_name, 
            name = npc_name, 
            hp = 45,
            x = game_instance.player.x+dx, 
            y = game_instance.player.y+dy, 
            b_generate_items = False, 
            current_map = game_instance.current_map,
            sprite = "crossbowman"
        )
        npc_obj.equip_item(Fireweapon(name = "Crossbow", damage = 5, ammo=70, range=7, projectile_sprite='bolt', ammo_type='bolt'), "primary_hand")
        npc_obj.hunger = npc_obj.max_hunger
        self.refresh_game_instance(game_instance.player.x+dx, game_instance.player.y+dy, game_instance)
        return True
    def production(self, multiplier = 1.0):
        if self.b_enemy: return 
        if self.villagers == 0: self.villagers = 0.1
        self.villagers = min( (1.0+0.005*multiplier)*self.villagers, self.villagers_max )

class MagicTower(TileBuilding):
    __serialize_only__ = TileBuilding.__serialize_only__ + ["name","heroes","num_heroes"]
    def __init__(self, x=0, y =0,name = "Magic Tower", b_enemy=False, floor_sprite = "grass"):
        TileBuilding.__init__(self, x=x, y=y, front_sprite = "magic_tower", walkable=True, sprite_key=floor_sprite, b_enemy=b_enemy)
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
            if "Recruit Healer" in current_item:
                if self.food >= 500 and self.wood >= 500 and self.metal >= 500 and self.stone >= 500:
                    if self.new_healer(game_instance):
                        self.villagers -= 15
                        self.food -= 500 
                        self.wood -= 500 
                        self.stone -= 500 
                        self.metal -= 500 
                else:
                    game_instance.add_message("Can't afford to purchase a Healer ...")
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
            f"-> stone: {self.stone:.0f}",
            f"-> metal: {self.metal:.0f}",
            "Overview >",
            "Recruit Healer (500 food, 500 wood, 500 stone, 500 Metal)",
            "Garrison >",
            "Resources >",
            "Exit"
        ]
    def new_healer(self, game_instance):
        if self.villagers <= 15:
            game_instance.add_message("There are no villagers to recruit ...")
            return False 
        dx, dy = game_instance.player.get_forward_direction()
        player = game_instance.player 
        spawn_tile = game_instance.map.get_tile(player.x+dx, player.y + dy)
        if not spawn_tile:
            game_instance.add_message("Can't generate player at this position, please rotate the current character")
            return False
        if spawn_tile.current_char:
            game_instance.add_message("Can't generate player at this position, please rotate the current character")
            return False
        npc_name = "Healer_"+rn(7)
        npc_obj = game_instance.add_player(
            key = npc_name, 
            cls_constructor = Healer,
            name = npc_name, 
            x = game_instance.player.x+dx, 
            y = game_instance.player.y+dy, 
            b_generate_items = False, 
            current_map = game_instance.current_map
        )
        npc_obj.hunger = npc_obj.max_hunger
        self.refresh_game_instance(game_instance.player.x+dx, game_instance.player.y+dy, game_instance)
        return True
    def production(self, multiplier = 1.0):
        if self.b_enemy: return 
        if self.villagers == 0: self.villagers = 0.1
        self.villagers = min( (1.0+0.005*multiplier)*self.villagers, self.villagers_max )    

# --- END 