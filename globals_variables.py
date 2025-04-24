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
    "meat"
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












