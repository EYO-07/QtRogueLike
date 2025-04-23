# events.py
from globals_variables import *

class Event:
    def __init__(self, priority=0):
        self.priority = priority

class AttackEvent(Event):
    def __init__(self, attacker, target, damage):
        super().__init__(priority=1)
        self.attacker = attacker
        self.target = target
        self.damage = damage

class MoveEvent(Event):
    def __init__(self, character, old_x, old_y):
        super().__init__(priority=0)  # Lower priority than AttackEvent
        self.character = character
        self.old_x = old_x
        self.old_y = old_y
        
class PickupEvent(Event):
    def __init__(self, character, tile):
        super().__init__(priority=0)  # Same priority as MoveEvent
        self.character = character
        self.tile = tile        
        
class UseItemEvent(Event):
    def __init__(self, character, item):
        super().__init__(priority=0)  # Same priority as PickupEvent
        self.character = character
        self.item = item
        
# --- END         