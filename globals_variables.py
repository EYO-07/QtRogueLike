import random 
import os 

# Global Functions
def Generate_Square_Diffs(radius=3):
    return [ (x,y) for y in range(-radius+1,radius) for x in range(-radius+1,radius) ]
    
def Generate_Square_Spiral_Traversal_Diffs(radius=3):
    """
    Generate (x, y) coordinate offsets in a square spiral order
    starting from (0, 0) within a square of side length 2*radius - 1.

    Parameters:
        radius (int): Distance from center to edge (half side-length + 1)

    Returns:
        List[Tuple[int, int]]: Spiral-ordered (x, y) coordinates
    """
    max_distance = radius - 1
    x, y = 0, 0
    dx, dy = 1, 0  # Initial direction: right
    spiral = [(x, y)]
    step_size = 1  # Number of steps in current direction
    direction_changes = 0
    while True:
        for _ in range(2):  # Repeat each step size twice (e.g., right, down; then step_size++)
            for _ in range(step_size):
                x += dx
                y += dy
                if abs(x) <= max_distance and abs(y) <= max_distance:
                    spiral.append((x, y))
                else:
                    return spiral  # Exit if out of bounds
            # Rotate direction clockwise
            dx, dy = -dy, dx
            direction_changes += 1
        step_size += 1    
    
def d(a = None,b = None): # float dice 
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

def Get_Sprite_Names_From(folder):
    S = set()
    valid_exts = {".png", ".webp", ".jpg", ".jpeg"}
    for file in os.listdir(folder):
        path = os.path.join(folder, file)
        if os.path.isdir(path): continue
        path_, ext = os.path.splitext(path)
        _, filename = os.path.split(path_)
        if ext.lower() not in valid_exts: continue
        S.add(filename)
    return list(S)
    
# Global Variables
PERFORMANCE_DISTANCE = 8
PERFORMANCE_TIME = 0.02 
H_REST_TURNS = 15
RAIDER_SPAWN_PROBABILITY = 0.1
SPAWNER_COOLDOWN = 200
FILL_ENEMIES_QT = 20 
FILL_SPAWNERS_QT = 40 

# map configuration 
MAP_WIDTH = 70
MAP_HEIGHT = 70 

# View Port
TILE_SIZE = 65
VIEW_WIDTH_IN_TILES = 7
VIEW_HEIGHT_IN_TILES = 9

# player
PLAYER_MAX_HP = 100
PLAYER_MAX_STAMINA = 200
PLAYER_MAX_HUNGER = 1000

# buildings 
PROD_INV_FACTOR = 100.0 

# Pop-up GUIs
POPUP_GUI_ALPHA = 0.8 
POPUP_WIDTH = 400
POPUP_HEIGHT = 500 

# cached diff moves 
ADJACENT_DIFF_MOVES = [(1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)]
CARDINAL_DIFF_MOVES = [(1, 0), (-1, 0), (0, 1), (0, -1)]
CHESS_KNIGHT_DIFF_MOVES = [
    (2, 1), (2, -1), (-2, 1), (-2, -1),
    (1, 2), (1, -2), (-1, 2), (-1, -2)
]
SQUARE_DIFF_MOVES = Generate_Square_Diffs(2)
SQUARE_DIFF_MOVES_5x5 = Generate_Square_Diffs(3)
SQUARE_DIFF_MOVES_10 = Generate_Square_Diffs(10)
SQUARE_DIFF_SPIRAL_MOVES_10 = Generate_Square_Spiral_Traversal_Diffs(10)
SQUARE_DIFF_SPIRAL_MOVES_15 = Generate_Square_Spiral_Traversal_Diffs(15)
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
    "long_sword", 
    "bastard_sword",
    "mace",
    "crossbow",
    "bolt"
]
SPRITE_NAMES_PLAYABLES = [
    "player",
    "player_2",
    "player_3"    
]
SPRITE_NAMES_CHARACTERS = SPRITE_NAMES_PLAYABLES + [
    "zombie", 
    "zombie_2",
    "bear",
    "enemy", 
    "rogue",
    "mercenary",
    "swordman",
    "upg_swordman",
    "mounted_knight",
    "evil_swordman",
    "crossbowman",
    "evil_crossbowman",
    "sorceress",
    "sorceress_2"
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
SPRITE_NAMES = Get_Sprite_Names_From("./assets")

# loot
HAND_SLOTS = ['primary_hand', 'secondary_hand' ]
EQUIPMENT_SLOTS = HAND_SLOTS + ['head', 'neck', 'torso', 'waist', 'legs', 'foot']
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
TILE_BUILDING_ENEMY_TABLE = [
    {"enemy": "Mercenary", "chance": 0.4, "b_generate_items": True, "extra_items": [
        {"item_name": "WeaponRepairTool", "name":"Whetstone", "uses": 5},
        {"item_name": "Food", "name":"meat", "nutrition":250}
    ]},
    {"enemy": "Rogue", "chance": 0.7, "b_generate_items": True, "extra_items": [
        {"item_name": "WeaponRepairTool", "name":"Whetstone", "uses": 2}
    ]}
]
ZOMBIE_SPAWNER_LIST = [
    {"enemy": "Zombie", "chance": 0.25, "b_generate_items": True, "hp": 70},
    {"enemy": "Zombie", "chance": 0.01, "b_generate_items": True, "hp": 100},
    {"enemy": "Zombie", "chance": 0.75, "b_generate_items": True}
]
ROGUE_SPAWNER_LIST = [
    {"enemy": "Mercenary", "chance": 0.05, "b_generate_items": True, "extra_items": [
        {"item_name": "WeaponRepairTool", "name":"Whetstone", "uses": 5},
        {"item_name": "Food", "name":"meat", "nutrition":250}
    ]},
    {"enemy": "RangedRaider", "chance": 0.03, "b_generate_items": True, "sprite": "evil_crossbowman", "hp": 50},
    {"enemy": "Raider", "chance": 0.01, "b_generate_items": True, "sprite": "evil_swordman", "hp": 100},
    {"enemy": "Rogue", "chance": 0.3, "b_generate_items": True, "extra_items": [
        {"item_name": "WeaponRepairTool", "name":"Whetstone", "uses": 2}
    ]}
]
RAIDERS_TABLE = [
    {"enemy": "RangedRaider", "chance": 0.45, "b_generate_items": True, "sprite": "evil_crossbowman", "hp": 100},
    {"enemy": "Raider", "chance": 0.75, "b_generate_items": True, "sprite": "evil_swordman", "hp": 200}
]

# descriptions
ZOMBIE_DESC = "Zombies, people affected by the plague, they are still alive but because of this strange disease their bodies smells like rotten flesh. Before they lose their minds, they try to acummulate food to satiate hunger, it's almost certain to find food with them ..."
ROGUE_DESC = "Rogues and Bandits, they are just robbers, ambushing travellers on the road. Always carry a sword with you ..."


