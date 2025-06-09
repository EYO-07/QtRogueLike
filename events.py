# events.py
from globals_variables import *

class Event:
    def __init__(self, priority=0):
        self.priority = priority
        self.type = ""

class AttackEvent(Event):
    def __init__(self, attacker, target, damage):
        Event.__init__(self, priority=1)
        self.attacker = attacker
        self.target = target
        self.damage = damage
        self.type = "AttackEvent"

class MoveEvent(Event):
    def __init__(self, character, old_x, old_y):
        Event.__init__(self, priority=0)  # Lower priority than AttackEvent
        self.character = character
        self.old_x = old_x
        self.old_y = old_y
        self.type = "MoveEvent"
        
class PickupEvent(Event):
    def __init__(self, character, tile):
        Event.__init__(self, priority=0)  # Same priority as MoveEvent
        self.character = character
        self.tile = tile        
        self.type = "PickupEvent"
        
class UseItemEvent(Event):
    def __init__(self, character, item):
        Event.__init__(self, priority=0)  # Same priority as PickupEvent
        self.character = character
        self.item = item
        self.type = "UseItemEvent"
        
class TimeSpanEvent(Event):
    def __init__(self, duration=10, priority=2, prevent_map_transition = False, message = "", iteration=None, *args, **kwargs):
        Event.__init__(self, priority=priority) 
        self.iteration_function = iteration
        self.current_iteration = 0 
        self.duration = duration 
        self.args = args 
        self.kwargs = kwargs 
        self.prevent_map_transition = prevent_map_transition
        self.message = message 
        self.type = "TimeSpanEvent"
    def __repr__(self):
        return self.message 
    def get_message(self):
        return self.message 
    def set_inactive(self):
        self.current_iteration = self.duration
    def extend_duration(self, quantity = 10):
        self.duration += quantity 
    def is_active(self):
        return self.current_iteration < self.duration
    def update(self): 
        if not self.is_active(): return 
        if not self.iteration_function: return 
        self.current_iteration += 1 
        self.iteration_function(self.current_iteration, instance = self,*self.args, **self.kwargs) 
        
# --- END         