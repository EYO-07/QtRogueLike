# items.py
from PyQt5.QtGui import QPixmap

class Item:
    def __init__(self, name, description="", weight=1, sprite="item"):
        self.name = name
        self.description = description
        self.weight = weight
        self.sprite = sprite

    def __str__(self):
        return f"{self.name} ({self.weight}kg): {self.description}"
        
    def use(self, character):
        pass  # Default: no effect    

class Container:
    def __init__(self, current_char = None):
        self.items = []
        self.current_char = current_char

    def add_item(self, item):
        if isinstance(item, Item):
            self.items.append(item)
            return True
        return False

    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item)
            return True
        return False

    def to_dict(self):
        """Serialize Container to a dictionary."""
        return {
            "items": [item.to_dict() for item in self.items],
            "current_char": self.current_char.to_dict() if self.current_char else None
        }
    
    @classmethod
    def from_dict(cls, data, characters=None):
        """Deserialize Container from a dictionary."""
        container = cls()
        for item_data in data.get("items", []):
            item_type = item_data.get("type")
            if item_type in ["food", "apple", "fish"]:
                item = Food.from_dict(item_data)
            elif item_type in ["long_sword", "club"]:
                item = Weapon.from_dict(item_data)
            else:
                item = Item.from_dict(item_data)
            container.add_item(item)
        if data.get("current_char") and characters is not None:
            char_data = data["current_char"]
            if char_data["type"] == "zombie":
                container.current_char = Zombie.from_dict(char_data)
            # Add other character types if needed
        return container


class Equippable(Item):
    def __init__(self, name, description="", weight=1, slot="primary_hand"):
        super().__init__(name, description, weight, sprite=name.lower())
        self.slot = slot
        
    def unequip(self, char):
        if self == char.primary_hand:
            char.primary_hand = None
            char.items.append(self)
            return 
        if self == char.secondary_hand:
            char.secondary_hand = None
            char.items.append(self)
            return 
        if self == char.head: 
            char.head = None
            char.items.append(self)
            return 
        if self == char.neck:
            char.neck = None
            char.items.append(self)
            return 
        if self == char.torso:
            char.torso = None
            char.items.append(self)
            return 
        if self == char.waist: 
            char.waist = None
            char.items.append(self)
            return 
        if self == char.legs:
            char.legs = None
            char.items.append(self)
            return 
        if self == char.foot:
            char.foot = None
            char.items.append(self)
            return 

    def get_slot(self, char):
        if self == char.primary_hand:
            return "primary_hand"
        if self == char.secondary_hand:
            return "secondary_hand"
        if self == char.head: 
            return "head"
        if self == char.neck:
            return "neck"
        if self == char.torso:
            return "torso"
        if self == char.waist: 
            return "waist"
        if self == char.legs:
            return "legs"
        if self == char.foot:
            return "foot"
        return None
    
class Weapon(Equippable):
    def __init__(self, name, damage ,description="", weight=1, stamina_consumption=1):
        super().__init__(name, description, weight, slot="primary_hand")
        self.damage = damage # damages decrease when successfully hit and restored to max_damage using special item 
        self.stamina_consumption = stamina_consumption 
        self.max_damage = damage 

class Food(Item):
    def __init__(self, name, nutrition, description="", weight=1):
        super().__init__(name, description, weight, sprite=name.lower())
        self.nutrition = nutrition

    def use(self, character):
        if hasattr(character, 'hunger') and hasattr(character, 'max_hunger'):
            character.hunger = min(character.hunger + self.nutrition, character.max_hunger)
            character.hp = min(character.hp + self.nutrition/20.0, character.max_hp)
            return True
        return False
        
class WeaponRepairTool(Item):
    def __init__(self, name, repairing_factor=1.05, description="", weight=1):
        super().__init__(name, description, weight, sprite=name.lower())
        self.repairing_factor = repairing_factor
    def use(self, character):
        if character.primary_hand:
            primary = character.primary_hand
            if primary.damage < 0.9*primary.max_damage:
                primary.damage = min( self.repairing_factor*primary.damage, primary.max_damage)
                return True
        return False
     
class Armor(Equippable):
    def __init__(self, name, armor, description="", weight=1, slot="torso"):
        super().__init__(name, description, weight, slot)
        self.armor = armor



















# --- END 