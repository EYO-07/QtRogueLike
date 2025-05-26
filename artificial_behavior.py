# artificial_behavior.py 

# project 
from globals_variables import *

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

# Let T be a toplevel function and F, G members for the conditional network class. The DSL Logic should be of the form:
# T() || % F() || additional things | return whatever 
# F() || % G() || return True ... which means that whoever calls him should return True to the toplevel caller.

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
    primary = self.primary_hand 
    if not isinstance(primary, Fireweapon): return False 
    target, path = primary.find_target(char, game_instance)
    if primary.perform_attack(char, target, path, game_instance):
        primary.do_ammo_consumption() # maybe add full stats update, but for simplicity
        return True 
    return False 
def AB_melee_attack(char = None, game_instance = None):
    from reality import Damageable, Player
    if char is None: return False 
    if game_instance is None: return False 
    map = game_instance.map 
    if not map: return False 
    # --
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
    # --
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
        if target.hp <= 0.8*target.max_hp: break 
    if not target: return False 
    cure = 0.1*target.max_hp 
    target.hp = min( target.max_hp, target.hp + cure )
    return True 
def AB_pillage(char = None, game_instance = None):
    from reality import TileBuilding
    if char is None: return False 
    if game_instance is None: return False 
    map = game_instance.map 
    if not map: return False 
    # --
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
    if target.villagers == 0:
        target.clear_resources()
        target.b_enemy = True 
        target.villagers = 10
    return True 
    
def AB_pursue(char = None, target = None, game_instance = None): pass 
def AB_pursue_destination(char = None, target = None, game_instance = None): pass 
def AB_pursue_attack_target(char = None, target = None, game_instance = None): pass 

def AB_pursue_heal_target(char = None, target = None, game_instance = None): pass 
def AB_pursue_building(char = None, target = None, game_instance = None): pass 

# -- END        