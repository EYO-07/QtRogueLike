# artificial_behavior.py 

# project 
from globals_variables import *
from events import * 

# built-in
import math 
import random

# Conditional Network : Is a functional paradigm implementation of a complex decision structure. Event processing, Artificial Behavior, and Menus are natural choices for this paradigm.
# 1. Conditional Network Class: is a family of functions that are building blocks for a conditional structure.
# 2. TopLevel Function : Is the first caller for a family of functions that belongs to a conditional network and represents a implementation of a complex decision structure. 
# 3. Member Function : Is a function that belongs to a conditional network class. 
# 4.A member function is called from a toplevel function or another member function.
# 5. A member function return True if the choice for the structure has been made, so all the other functions that calls him recursively should return True until the toplevel function that can perform aditional tasks but should return True (or whatever is designed to return).
# 6. A member function return False if the only the function should return, but the network should still process to find the desired choice. 
# 7. Forker Function is a special member function which the True means a path choice in decision tree, and aren't used to tell the toplevel function to return. Ordinary member functions should be used as simple if, fork functions should be used in if-else or if-elif-else structure. 

# Let T be a toplevel function and F, G members for the conditional network class. The DSL Logic should be of the form:
# T() || % F() || additional things | return whatever 
# F() || % G() || return True ... which means that whoever calls him should return True (possibly doing additional things) to the toplevel caller.

class Function_Family:
    def __init__(self, function = None):
        self.function = function 
    def __call__(self, *args, **kwargs):
        if not self.function: return None
        return self.function(*args, **kwargs)
class Conditional_Network(Function_Family):
    def __init__(self, function = None):
        Function_Family.__init__(self, function = function)
    def __add__(self, another):
        if not isinstance(another, Conditional_Network): raise TypeError("Can only combine with another Conditional_Network.")
        def _function(*args, **kwargs):
            return self(*args, **kwargs) or another(*args, **kwargs)
        return Conditional_Network(_function)
    def __mul__(self, another):
        if not isinstance(another, Conditional_Network): raise TypeError("Can only combine with another Conditional_Network.")
        def _function(*args, **kwargs):
            return self(*args, **kwargs) and another(*args, **kwargs)
        return Conditional_Network(_function)
    def __neg__(self):
        return ~self
    def __sub__(self, another):
        if not isinstance(another, Conditional_Network):
            raise TypeError("Can only combine with another Conditional_Network.")
        def _function(*args, **kwargs):
            return self(*args, **kwargs) and not another(*args, **kwargs)
        return Conditional_Network(_function)
    def __invert__(self):
        def _function(*args, **kwargs):
            return not self(*args, **kwargs)
        return Conditional_Network(_function)    
    def __truediv__(self, another):
        if not isinstance(another, Conditional_Network): raise TypeError("Can only combine with another Conditional_Network.")
        def _function(*args, **kwargs):
            return self(*args, **kwargs) and not another(*args, **kwargs)
        return Conditional_Network(_function)
    def __eq__(self, other):
        if not isinstance(other, Conditional_Network):
            return False
        return all(self(x) == other(x) for x in test_domain)  # You define test_domain
    def __repr__(self):
        name = getattr(self.function, '__name__', repr(self.function))
        return f"<Conditional_Network({name})>"
True_F = Conditional_Network(lambda *args, **kwargs: True)
False_F = Conditional_Network(lambda *args, **kwargs: False)

""" Algebraic Properties 
1. Identity Elements
A + False_F == A (OR identity)
A * True_F == A (AND identity)

2. Domination (Annihilation)
A + True_F == True_F
A * False_F == False_F

3. Idempotent Laws
A + A == A
A * A == A

4. Commutative Laws
A + B == B + A
A * B == B * A

5. Associative Laws
(A + B) + C == A + (B + C)
(A * B) * C == A * (B * C)

6. Distributive Laws
A * (B + C) == (A * B) + (A * C)
A + (B * C) == (A + B) * (A + C)

7. De Morgan’s Laws
~(A + B) == ~A * ~B
~(A * B) == ~A + ~B

8. Double Negation
~~A == A

9. Absorption Laws
A + (A * B) == A
A * (A + B) == A

10. Difference (Defined as A * ~B)
A - B == A * ~B
A / B == A - B (in your implementation)

A + B/A is equivalent of
------------------------
if A(): 
    return True
else: 
    return B()

A + B is equivalent of
----------------------
if A(): 
    return True
else: 
    return B()    
    
"""

def is_enemy_of(char1, char2):
    from reality import Player, Enemy
    if isinstance(char1, Player) and isinstance(char2, Player): return False 
    if isinstance(char1, Enemy) and isinstance(char2, Enemy): return False 
    if isinstance(char1, Player) and isinstance(char2, Enemy): return True 
    if isinstance(char1, Enemy) and isinstance(char2, Player): return True 
    return False 
def get_closest_visible(origin = None, default_target = None, entities = None, game_instance = None):
    from reality import TileBuilding, Player, Enemy, Healer
    if not origin: return None, None 
    if not game_instance: return None, None 
    if default_target is None and entities is None: return None, None 
    entity = None 
    distance = None 
    if default_target:
        entity = default_target
        distance = origin.distance(entity)
    if len(entities) == 0: 
        return entity, distance 
    if type(entities) == list: 
        if not default_target:
            entity = entities[0]
            distance = origin.distance(entity)
        if len(entities) == 1: 
            return entity, distance 
        for v in entities:
            if not v: continue # possibly unnecessary 
            if v is origin: continue 
            if isinstance(v, TileBuilding): # if is a TileBuilding
                new_distance = origin.distance(v)
                if new_distance < distance:
                    entity = v
                    distance = new_distance 
            else:
                if not v.current_tile: continue 
                tile = game_instance.map.get_tile(v.x,v.y)
                if not tile: continue
                if not tile.current_char is v: continue 
                new_distance = origin.distance(v)
                if new_distance < distance:
                    entity = v
                    distance = new_distance 
    elif type(entities) == dict:
        for k,v in entities.items():
            if not k or not v: continue # possibly unnecessary 
            if v is origin: continue 
            if isinstance(origin, Enemy):
                if not origin.can_see_character(v, game_instance.map): continue 
            if not v.current_tile: continue 
            tile = game_instance.map.get_tile(v.x,v.y)
            if not tile: continue
            if not tile.current_char is v: continue 
            new_distance = origin.distance(v)
            if distance is None:
                entity = v
                distance = new_distance
            elif new_distance < distance:
                entity = v
                distance = new_distance 
    if entity and distance:
        if isinstance(origin, Player):
            return entity, distance
        else:
            if isinstance(entity, TileBuilding): # for building pursue it's not necessary to see 
                return entity, distance 
            if origin.can_see_character(entity, game_instance.map):
                return entity, distance
            else:
                return None, None 
    else:
        return None, None 
    
# -- AB : Artificial Behavior Function Family  
def AB_random_walk(char = None, game_instance = None):
    if char is None: return False 
    if game_instance is None: return False 
    if d() >= char.activity: return False 
    for i in range(5): # 5 attempts
        dx, dy = random.choice(ADJACENT_DIFF_MOVES)
        target_x, target_y = char.x + dx, char.y + dy
        tile = game_instance.map.get_tile(target_x, target_y)
        if not tile: continue 
        if tile.can_place_character(): return char.move(dx, dy, game_instance.map)
    return False 
def AB_ranged_attack(char = None, game_instance = None): 
    from reality import Fireweapon
    primary = char.primary_hand 
    if not isinstance(primary, Fireweapon): return False 
    target, path = primary.find_target(char, game_instance)
    if primary.perform_attack(char, target, path, game_instance):
        primary.do_ammo_consumption() # maybe add full stats update, but for simplicity
        return True 
    return False 
def AB_melee_current_target(char = None, game_instance = None):
    target = char.current_target 
    if not target: 
        char.current_target = None 
        return False 
    from reality import Damageable 
    if not isinstance(target, Damageable): return False 
    if target.hp <= 0: 
        char.current_target = None 
        return False 
    if char.distance(target) > 1: return False 
    damage = char.do_damage()
    game_instance.events.append( AttackEvent(char, target, damage) )    
    return True 
def AB_heal_current_target(char = None, game_instance= None):
    target = char.current_target_healing 
    if not target: 
        char.current_target_healing = None 
        return False 
    from reality import Damageable 
    if not isinstance(target, Damageable): return False 
    if target.hp > 0.9*target.max_hp:
        char.current_target_healing = None 
        return False 
    if target.hp <= 0: 
        char.current_target_healing = None 
        return False 
    if char.distance(target) > 1: return False 
    if char.stamina <= 20: return False 
    char.stamina -= 20 
    cure = 0.1*target.max_hp 
    target.hp = min( target.max_hp, target.hp + cure )    
    return True
def AB_pillage_current_target(char = None, game_instance = None):
    target = char.current_target_building 
    if not target: 
        char.current_target_building = None 
        return False 
    from reality import TileBuilding
    if not isinstance(target, TileBuilding): return False 
    if target.b_enemy: 
        char.current_target_building = None 
        return False
    if char.distance(target) > 0: return False 
    damage = char.do_damage()
    target.villagers = max(0, target.villagers - damage)
    if target.villagers <= 0:
        target.clear_resources()
        target.b_enemy = True 
        target.villagers = 10
    return True 
    
# 1. AB_melee_attack() || % AB_ready_melee_current_target() || Attack 
# 2. AB_melee_attack() || % AB_ready_melee_current_target() | & Search Adjacent 
def AB_melee_attack(char = None, game_instance = None):
    if char is None: return False 
    if game_instance is None: return False 
    map = game_instance.map 
    if not map: return False 
    if AB_melee_current_target(char = char, game_instance = game_instance): return True 
    from reality import Damageable 
    target = None 
    for dx, dy in random.sample(CROSS_DIFF_MOVES_1x1):
        x = char.x + dx 
        y = char.y + dy
        target = map.get_char(x, y)
        if not target: continue 
        if not isinstance(target, Damageable): 
            target = None 
            continue 
        if is_enemy_of(char, target): break 
    if not target: return False 
    damage = char.do_damage()
    game_instance.events.append( AttackEvent(char, target, damage) )
    return True
def AB_healing(char = None, game_instance = None):
    from reality import Damageable, Player
    if char is None: return False 
    if game_instance is None: return False 
    map = game_instance.map 
    if not map: return False 
    if AB_heal_current_target(char = char, game_instance = game_instance): return True 
    target = None 
    for dx, dy in random.sample(CROSS_DIFF_MOVES_1x1):
        x = char.x + dx 
        y = char.y + dy
        target = map.get_char(x, y)
        if not target: continue 
        if not isinstance(target, Damageable): 
            target = None 
            continue 
        if is_enemy_of(char, target): 
            target = None 
            continue 
        if target.hp <= 0.9*target.max_hp: break 
    if not target: return False 
    if char.stamina <= 20: return False 
    char.stamina -= 20 
    cure = 0.1*target.max_hp 
    target.hp = min( target.max_hp, target.hp + cure )
    return True 
def AB_pillage(char = None, game_instance = None):
    from reality import TileBuilding
    if char is None: return False 
    if game_instance is None: return False 
    map = game_instance.map 
    if not map: return False 
    if AB_pillage_current_target(char = char, game_instance = game_instance): return True 
    target = None
    for dx, dy in random.sample(ADJACENT_DIFF_MOVES):
        x = char.x + dx 
        y = char.y + dy 
        target = map.get_tile(x,y) 
        if not target: continue 
        if not isinstance(target, TileBuilding): 
            target = None 
            continue 
        if not target.b_enemy: break # for instance, it's only for raiders and enemies for the player 
    if not target: return False 
    damage = char.do_damage()
    target.villagers = max(0, target.villagers - damage)
    if target.villagers <= 0:
        target.clear_resources()
        target.b_enemy = True 
        target.villagers = 10 
    return True 
def AB_pursue_current_target(char = None, game_instance = None): 
    if char is None: return False 
    if game_instance is None: return False 
    target = char.current_target 
    if target is None: return False 
    map = game_instance.map 
    if map is None: 
        char.current_target = None 
        return False 
    if not hasattr(target, "x"): 
        char.current_target = None 
        return False 
    if not hasattr(target, "y"): 
        char.current_target = None 
        return False 
    path = map.find_path(char.x, char.y, target.x, target.y)
    if not path: return False 
    next_x, next_y = path[0] 
    dx, dy = next_x - char.x, next_y - char.y 
    tile = map.get_tile(next_x, next_y) 
    if not tile: return False 
    if not tile.can_place_character(): return False 
    char.move(dx, dy, map)
    return True 
def AB_pursue_current_target_building(char = None, game_instance = None):
    if char is None: return False 
    if game_instance is None: return False 
    target = char.current_target_building 
    if target is None: return False 
    map = game_instance.map 
    if map is None: 
        char.current_target_building = None 
        return False 
    if not hasattr(target, "x"): 
        char.current_target_building = None 
        return False 
    if not hasattr(target, "y"): 
        char.current_target_building = None 
        return False 
    path = map.find_path(char.x, char.y, target.x, target.y)
    if not path: return False 
    next_x, next_y = path[0] 
    dx, dy = next_x - char.x, next_y - char.y 
    tile = map.get_tile(next_x, next_y) 
    if not tile: return False 
    if not tile.can_place_character(): return False 
    char.move(dx, dy, map)
    return True 
def AB_pursue_current_target_healing(char = None, game_instance = None):
    if char is None: return False 
    if game_instance is None: return False 
    target = char.current_target_healing 
    if target is None: return False 
    map = game_instance.map 
    if map is None: 
        char.current_target_healing = None 
        return False 
    if not hasattr(target, "x"): 
        char.current_target_healing = None 
        return False 
    if not hasattr(target, "y"): 
        char.current_target_healing = None 
        return False 
    path = map.find_path(char.x, char.y, target.x, target.y)
    if not path: return False 
    next_x, next_y = path[0] 
    dx, dy = next_x - char.x, next_y - char.y 
    tile = map.get_tile(next_x, next_y) 
    if not tile: return False 
    if not tile.can_place_character(): return False 
    char.move(dx, dy, map)
    return True 
def AB_pursue_current_target_tile(char = None, game_instance = None): 
    if char is None: return False 
    if game_instance is None: return False 
    target = char.current_target_tile 
    if target is None: return False 
    map = game_instance.map 
    if map is None: 
        char.current_target_tile = None 
        return False 
    if not hasattr(target, "x"): 
        char.current_target_tile = None 
        return False 
    if not hasattr(target, "y"): 
        char.current_target_tile = None 
        return False 
    path = map.find_path(char.x, char.y, target.x, target.y)
    if not path: return False 
    next_x, next_y = path[0] 
    dx, dy = next_x - char.x, next_y - char.y 
    tile = map.get_tile(next_x, next_y) 
    if not tile: return False 
    if not tile.can_place_character(): return False 
    char.move(dx, dy, map)
    return True 
def AB_find_melee_target(char = None, game_instance = None): # forker 
    """ True means a valid current_target at end of processing, False means that the function could not find a valid current_target. """
    if char is None: return False 
    if game_instance is None: return False 
    map = game_instance.map 
    if not map: return False
    player = game_instance.player 
    if not player: return False 
    from reality import Player, Enemy, Damageable
    target = None 
    distance = None 
    target = char.current_target 
    if target: distance = char.distance(target)
    flag_find_new = False 
    if target is None: flag_find_new = True 
    if not isinstance(target, Damageable): flag_find_new = True 
    if isinstance(char, Enemy) and not char.can_see_character(target, map): flag_find_new = True 
    if distance and distance > char.tolerance: flag_find_new = True 
    if flag_find_new:
        if isinstance(char, Player):
            char.current_target, distance = get_closest_visible(origin=char, entities=map.enemies, game_instance=game_instance)
        elif isinstance(char, Enemy):
            char.current_target, distance = get_closest_visible(origin=char, default_target=player, entities=game_instance.players, game_instance=game_instance)
    if char.current_target is None: return False 
    if distance is None: return False 
    if distance > char.tolerance: return False 
    return True 
def AB_find_melee_target_grudge(char = None, game_instance = None): # forker 
    """ True means a valid current_target at end of processing, False means that the function could not find a valid current_target. """
    if char is None: return False 
    if game_instance is None: return False 
    map = game_instance.map 
    if not map: return False
    player = game_instance.player 
    if not player: return False 
    from reality import Player, Enemy, Damageable
    target = None 
    distance = None 
    target = char.current_target 
    if target: distance = char.distance(target)
    flag_find_new = False 
    if target is None: flag_find_new = True 
    if not isinstance(target, Damageable): flag_find_new = True 
    if distance and distance > 5: flag_find_new = True 
    if flag_find_new:
        if isinstance(char, Player):
            char.current_target, distance = get_closest_visible(origin=char, entities=map.enemies, game_instance=game_instance)
        elif isinstance(char, Enemy):
            char.current_target, distance = get_closest_visible(origin=char, default_target=player, entities=game_instance.players, game_instance=game_instance)
    if char.current_target is None: return False 
    if distance is None: return False 
    if distance > char.tolerance: return False 
    return True     
def AB_find_healing_target(char = None, game_instance = None): # forker 
    """ True means a valid current_target at end of processing, False means that the function could not find a valid current_target. """
    if char is None: return False 
    if game_instance is None: return False 
    map = game_instance.map 
    if not map: return False
    player = game_instance.player 
    if not player: return False 
    from reality import Player, Enemy, Damageable
    target = None 
    distance = None 
    target = char.current_target_healing 
    if target: distance = char.distance(target)
    flag_find_new = False 
    if target is None: flag_find_new = True 
    if not isinstance(target, Damageable): flag_find_new = True 
    if distance and distance > 5: flag_find_new = True 
    if flag_find_new:
        if isinstance(char, Player):
            char.current_target_healing, distance = get_closest_visible(origin=char, entities=game_instance.players, game_instance=game_instance)
        elif isinstance(char, Enemy):
            char.current_target_healing, distance = get_closest_visible(origin=char, entities=map.enemies, game_instance=game_instance)
    if char.current_target_healing is None: return False 
    if distance is None: return False 
    return True 
def AB_find_building_target(char = None, game_instance = None): # forker 
    """ True means a valid current_target at end of processing, False means that the function could not find a valid current_target. """
    if char is None: return False 
    if game_instance is None: return False 
    map = game_instance.map 
    if not map: return False 
    from reality import Player, Enemy, TileBuilding
    player = game_instance.player 
    if not player: return False 
    target = None 
    distance = None 
    target = char.current_target_building 
    if target: distance = char.distance(target)
    flag_find_new = False 
    if target is None: flag_find_new = True 
    if not isinstance(target, TileBuilding): flag_find_new = True 
    if not hasattr(target, "b_enemy"): 
        flag_find_new = True
    else:
        if isinstance(char, Player) and not target.b_enemy: flag_find_new = True 
        if isinstance(char, Enemy) and target.b_enemy: flag_find_new = True 
    if flag_find_new: 
        buildings = None 
        if isinstance(char, Player): buildings = [ i for i in map.buildings if i.b_enemy ] 
        if isinstance(char, Enemy): buildings = [ i for i in map.buildings if not i.b_enemy ] 
        if not buildings: return False 
        if len(buildings)==0: return False 
        if len(buildings)==1: 
            char.current_target_building = buildings[0] 
            return True 
        char.current_target_building, distance = get_closest_visible(origin=char, entities=buildings, game_instance=game_instance)
    if char.current_target_building is None: return False 
    if distance is None: return False 
    return True 
def AB_find_random_tile_target(char = None, game_instance = None): # forker -- bad performance 
    """ True means a valid current_target at end of processing, False means that the function could not find a valid current_target. """
    if char is None: return False 
    if game_instance is None: return False 
    map = game_instance.map 
    if not map: return False 
    from reality import Player, Enemy, Tile
    player = game_instance.player 
    if not player: return False 
    target = None 
    distance = None 
    target = char.current_target_tile 
    if target: distance = char.distance(target)
    flag_find_new = False 
    if target is None: flag_find_new = True 
    if distance and distance < 1: flag_find_new = True 
    if not isinstance(target, Tile): flag_find_new = True 
    if flag_find_new: char.current_target_tile = map.get_tile( *map.get_random_walkable_tile() )
    if char.current_target_tile is None: return False 
    distance = char.distance(char.current_target_tile)
    if not distance: return False 
    if distance < 1: return False 
    return True 

# 1. AB_find_melee_target ; Imediatly cease the pursue if can't see the target
# 2. AB_find_melee_target_grudge ; Keep pursuing even if can't see the target until the character is far away 
    
# --     
def AB_behavior_default(char = None, game_instance = None): # - [ok]
    if AB_ranged_attack(char=char, game_instance=game_instance): return True 
    if AB_find_melee_target(char=char, game_instance=game_instance): 
        if AB_melee_current_target(char=char, game_instance=game_instance): return True 
        if AB_pursue_current_target(char=char, game_instance=game_instance): return True 
    if AB_random_walk(char=char, game_instance=game_instance): return True 
    return True 
def AB_behavior_grudge(char = None, game_instance = None): # - [ok]
    if AB_ranged_attack(char=char, game_instance=game_instance): return True 
    if AB_find_melee_target_grudge(char=char, game_instance=game_instance): 
        if AB_melee_current_target(char=char, game_instance=game_instance): return True 
        if AB_pursue_current_target(char=char, game_instance=game_instance): return True 
    if AB_random_walk(char=char, game_instance=game_instance): return True 
    return True 
def AB_behavior_raider(char = None, game_instance = None): # - [ok] - performace? 
    if AB_ranged_attack(char=char, game_instance=game_instance): return True 
    if AB_find_melee_target(char=char, game_instance=game_instance): 
        if AB_melee_current_target(char=char, game_instance=game_instance): return True 
        if AB_pursue_current_target(char=char, game_instance=game_instance): return True 
    if AB_find_building_target(char=char, game_instance=game_instance): 
        if AB_pillage_current_target(char=char, game_instance=game_instance): return True 
        if AB_pursue_current_target_building(char=char, game_instance=game_instance): return True 
    if AB_random_walk(char=char, game_instance=game_instance): return True 
    return True 
def AB_behavior_healer(char = None, game_instance = None): # - [ok] 
    if AB_find_healing_target(char=char, game_instance=game_instance): 
        if AB_heal_current_target(char=char, game_instance=game_instance): return True 
        if AB_pursue_current_target_healing(char=char, game_instance=game_instance): return True 
    if AB_ranged_attack(char=char, game_instance=game_instance): return True 
    if AB_find_melee_target(char=char, game_instance=game_instance): 
        if AB_melee_current_target(char=char, game_instance=game_instance): return True 
        if AB_pursue_current_target(char=char, game_instance=game_instance): return True 
    if AB_random_walk(char=char, game_instance=game_instance): return True 
    return True 

# -- END 