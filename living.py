# living.py
import random, math
from items import *
from PyQt5.QtGui import QPixmap
from mapping import *  # Use shared sprite dictionary
from events import * 

class Character(Container):
    def __init__(self, name, hp, x, y):
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
        self.items = []
    
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
    def __init__(self, name, hp, x, y, b_generate_items = True):
        super().__init__(name, hp, x, y)
        self.class_name = "Adventurer"
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
    def __init__(self, name, hp, x, y, b_generate_items = True):
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
    def __init__(self, name, hp, x, y, b_generate_items = True):
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
    def __init__(self, name, hp , x, y, b_generate_items = True):
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