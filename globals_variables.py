# Global Variables

# map configuration 
MAP_WIDTH = 100
MAP_HEIGHT = 100 

# player
PLAYER_MAX_HP = 100
PLAYER_MAX_STAMINA = 200
PLAYER_MAX_HUNGER = 1000

CHESS_KNIGHT_DIFF_MOVES = [
    (2, 1), (2, -1), (-2, 1), (-2, -1),
    (1, 2), (1, -2), (-1, 2), (-1, -2)
]
    
SQUARE_DIFF_MOVES = [
    (-1,-1), (-1,0), (-1,1), 
    (0,-1), (0,0) ,(0,-1),
    (1,-1), (1,0), (1,1)
]

CROSS_DIFF_MOVES = [
    (0,1), (0,2), (0,3),
    (0,-1), (0,-2), (0,-3),
    (1,0), (2,0), (3,0),
    (-1,0), (-2,0), (-3,0)
]
    
SPRITE_NAMES = [
    "grass",
    "dirt",
    "floor", 
    "player", 
    "enemy", 
    "zombie", 
    "wall", 
    "tree", 
    "water",
    "food", 
    "long_sword", 
    "club", 
    "sack",
    "apple",
    "fish",
    "bread",
    "HUD_arrow",
    "rogue",
    "stair_up",
    "stair_down",
    "dungeon_entrance",
    "rock",
    "whetstone",
    "bear",
    "meat",
    "mercenary"
]

EQUIPMENT_SLOTS = [
    'primary_hand', 
    'secondary_hand', 
    'head', 
    'neck', 
    'torso', 
    'waist', 
    'legs', 
    'foot'
]

LOOT_TABLE = [
    { "item_name": "Food", "chance": 0.3, "name":"apple", "nutrition":10 },
    { "item_name": "Food", "chance": 0.2, "name":"fish", "nutrition":80 },
    { "item_name": "Food", "chance": 0.1, "name":"bread", "nutrition":50 },
    { "item_name": "Food", "chance": 0.01, "name":"meat", "nutrition":280 },
    { "item_name": "Sword", "chance": 0.001, "name":"Long_Sword", "damage":12,"durability_factor":0.998 },
    { "item_name": "Sword", "chance": 0.2, "name":"Long_Sword", "damage":10,"durability_factor":0.95 },
    { "item_name": "Sword", "chance": 0.1, "name":"Long_Sword", "damage":10,"durability_factor":0.8 },
    { "item_name": "WeaponRepairTool", "chance": 0.01, "name":"Whetstone", "uses":10 }
]










