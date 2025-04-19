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
    def __init__(self):
        self.items = []

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

class Equippable(Item):
    def __init__(self, name, description="", weight=1, slot="primary_hand"):
        super().__init__(name, description, weight, sprite=f"equippable_{name.lower()}")
        self.slot = slot

class Weapon(Equippable):
    def __init__(self, name, damage, description="", weight=1):
        super().__init__(name, description, weight, slot="primary_hand")
        self.damage = damage

class Food(Item):
    def __init__(self, name, nutrition, description="", weight=1):
        super().__init__(name, description, weight, sprite="food")
        self.nutrition = nutrition

    def use(self, character):
        if hasattr(character, 'hunger') and hasattr(character, 'max_hunger'):
            character.hunger = min(character.hunger + self.nutrition, character.max_hunger)
            return True
        return False
     
class Armor(Equippable):
    def __init__(self, name, armor, description="", weight=1, slot="torso"):
        super().__init__(name, description, weight, slot)
        self.armor = armor



















# --- END 