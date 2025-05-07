import random 

# Global Functions
def Generate_Square_Diffs(radius=3):
    return [ (x,y) for y in range(-radius+1,radius) for x in range(-radius+1,radius) ]
    
def d(a,b = None): # float dice 
    if (a is None) and (b is None):
        return random.random()
    if b is None:
        return random.uniform(1,a)
    else:
        return random.uniform(a,b)

def rn(num = 5):
    if num == 1:
        return str(random.randint(0,9))
    return str(random.randint(0,9))+rn(num-1)

# Global Variables

# map configuration 
MAP_WIDTH = 70
MAP_HEIGHT = 70 

# View Port
TILE_SIZE = 70
VIEW_WIDTH_IN_TILES = 7
VIEW_HEIGHT_IN_TILES = 7

# player
PLAYER_MAX_HP = 100
PLAYER_MAX_STAMINA = 200
PLAYER_MAX_HUNGER = 1000

PROD_INV_FACTOR = 100.0 

# cached diff moves 
ADJACENT_DIFF_MOVES = [(1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)]
CHESS_KNIGHT_DIFF_MOVES = [
    (2, 1), (2, -1), (-2, 1), (-2, -1),
    (1, 2), (1, -2), (-1, 2), (-1, -2)
]
SQUARE_DIFF_MOVES = Generate_Square_Diffs(2)
SQUARE_DIFF_MOVES_5x5 = Generate_Square_Diffs(3)
CROSS_DIFF_MOVES = [
    (0,1), (0,2), (0,3),
    (0,-1), (0,-2), (0,-3),
    (1,0), (2,0), (3,0),
    (-1,0), (-2,0), (-3,0)
]
CROSS_DIFF_MOVES_1x1 = [
    (0,1), (0,-1), (1,0), (-1,0)
]

# sprite names
SPRITE_NAMES_WEAPONS = [
    "club", # +
    "long_sword", 
    "bastard_sword",
    "mace",
    "wand", # +
    "staff" # +
]

SPRITE_NAMES_PLAYABLES = [
    "player",
    "player_2",
    "player_3"    
]

SPRITE_NAMES_CHARACTERS = SPRITE_NAMES_PLAYABLES + [
    "zombie", 
    "bear",
    "enemy", 
    "rogue",
    "mercenary",
    "swordman",
    "mounted_knight"
]
SPRITE_NAMES_FOODS = [
    "food", 
    "apple",
    "fish",
    "bread",
    "meat"
]
SPRITE_NAMES_TILES = [
    "grass",
    "dirt",
    "floor", 
    "wall", 
    "tree", 
    "water",
    "stair_up",
    "stair_down",
    "dungeon_entrance",
    "shallow_water",
    "rock"
]
SPRITE_NAMES = SPRITE_NAMES_WEAPONS + SPRITE_NAMES_CHARACTERS + SPRITE_NAMES_FOODS + SPRITE_NAMES_TILES + [
    "sack",
    "HUD_arrow",
    "whetstone",
    "house", # +
    "castle", # +
    "lumber_mill", #+
    "quarry",
    "mill",
    "wood",
    "tower"
]

# loot
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

# enemy tables 
DUNGEON_ENEMY_TABLE = [
    {"enemy": "Mercenary", "chance": 0.1, "b_generate_items": True, "extra_items": [
            {"item_name": "WeaponRepairTool", "name":"Whetstone", "uses": 5},
            {"item_name": "Food", "name":"meat", "nutrition":250}
        ]},
    {"enemy": "Rogue", "chance": 0.3, "b_generate_items": True, "extra_items": [
        {"item_name": "WeaponRepairTool", "name":"Whetstone", "uses": 3},
        {"item_name": "Food", "name":"meat", "nutrition":200}
    ]},
    {"enemy": "Zombie", "chance": 0.75, "b_generate_items": True}
]
FOREST_ENEMY_TABLE = [
    {"enemy": "Bear", "chance": 0.07, "b_generate_items": True},
    {"enemy": "Mercenary", "chance": 0.05, "b_generate_items": True, "extra_items": [
        {"item_name": "WeaponRepairTool", "name":"Whetstone", "uses": 5},
        {"item_name": "Food", "name":"meat", "nutrition":250}
    ]},
    {"enemy": "Rogue", "chance": 0.3, "b_generate_items": True, "extra_items": [
        {"item_name": "WeaponRepairTool", "name":"Whetstone", "uses": 2}
    ]},
    {"enemy": "Zombie", "chance": 0.75, "b_generate_items": True}
]
FIELD_ENEMY_TABLE = [
    {"enemy": "Bear", "chance": 0.03, "b_generate_items": True},
    {"enemy": "Rogue", "chance": 0.05, "b_generate_items": True},
    {"enemy": "Zombie", "chance": 0.9, "b_generate_items": True}
]
DEFAULT_ENEMY_TABLE = [
    {"enemy": "Bear", "chance": 0.03, "b_generate_items": True},
    {"enemy": "Rogue", "chance": 0.05, "b_generate_items": True},
    {"enemy": "Zombie", "chance": 0.9, "b_generate_items": True}
]
ROAD_ENEMY_TABLE = [
    {"enemy": "Rogue", "chance": 0.1, "b_generate_items": True},
    {"enemy": "Zombie", "chance": 0.9, "b_generate_items": True}
] 
LAKE_ENEMY_TABLE = [
    {"enemy": "Rogue", "chance": 0.25, "b_generate_items": True},
    {"enemy": "Zombie", "chance": 0.75, "b_generate_items": True}
] 







