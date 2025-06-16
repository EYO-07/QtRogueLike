# special_tiles.py 

# project
from reality import * 
from events import * 
from serialization import * 
from globals_variables import *
from artificial_behavior import *

# built-in
import random
import math
import os 
from heapq import heappush, heappop
from itertools import product
        
class ActionTile(Tile): # tile which the player can interact - interface class
    __serialize_only__ = Tile.__serialize_only__ + ["description"]
    def __init__(self, x =0,y=0,front_sprite = "stair_up", walkable=True, sprite_key="grass"):
        Tile.__init__(self, x=x, y=y, walkable=walkable, sprite_key=sprite_key)
        self.add_layer( front_sprite )
        self.description = "" 
    def set_description(self,text):
        self.description = text 
    def write_quest_note(self, game_instance):
        map = game_instance.map 
        if not map: return 
        text = "Quest : "+self.description+"\n"+f"- Location : {self.x}, {map.height-self.y}\n- Destroy : press C to destroy the spawner"
        game_instance.take_note_on_diary(text = text)
        
class Spawner(ActionTile):
    __serialize_only__ = ActionTile.__serialize_only__ + ["spawn_list"]
    def __init__(self, x=0, y=0, front_sprite = "abandoned_house", sprite_key="grass", spawn_list = "FOREST_ENEMY_TABLE", spawn_distance = 7):
        ActionTile.__init__(self, x=x,y=y,front_sprite=front_sprite, walkable=True, sprite_key=sprite_key)
        self.spawn_list = spawn_list 
        self.spawn_distance = spawn_distance 
        self.spawn_cooldown = 0    
    def update(self, game_instance):
        # turn based update 
        if self.spawn_cooldown > 0: 
            self.spawn_cooldown -= 1 
            return False     
        player = game_instance.player 
        if player.distance(self) > self.spawn_distance: return False 
        map = game_instance.map         
        if map.get_enemy_count() > 70: return False 
        count = 0
        for dx, dy in CROSS_DIFF_MOVES_1x1:
            x = self.x + dx 
            y = self.y + dy 
            if not map.can_place_character_at(x,y): continue 
            if map.generate_and_place_enemy_by_list_at(x=x,y=y, enemy_list=globals()[self.spawn_list]): count += 1
        if count: 
            self.spawn_cooldown = SPAWNER_COOLDOWN 
            return True 
        return False 
    def add_bonus_resources(self, tile):
        if tile is None: return 
        order = 1000
        if d()<0.3: tile.add_item(Wood(d(0,order)))
        if d()<0.25: tile.add_item(Stone(d(0,order)))
        if d()<0.2: tile.add_item(Metal(d(0,order)))
    def destroy_spawner(self, game_instance):
        player = game_instance.player 
        map = game_instance.map 
        if player.stamina < 30: 
            game_instance.add_message("You're too exhausted to destroy the spawner ...")
            return 
        player.stamina -= 30 
        tile = Tile(self.x,self.y,walkable=True, sprite_key=self.default_sprite_key)
        self.add_bonus_resources(tile = tile)
        map.set_tile(self.x,self.y, tile)
        if self in map.spawners: map.spawners.remove(self)
        map.place_character(player)
        game_instance.add_message("You've destroyed the spawner ...") 
    def set_spawner_at(self, x,y, map):
        self.x = x 
        self.y = y 
        map.set_tile(x,y,self)
    
def new_zombie_spawner(x,y,map):
    tile = map.get_tile(x,y)
    if not tile: return None 
    floor_sprite = tile.default_sprite_key 
    SP = Spawner(x=x, y=y, front_sprite = "abandoned_house", sprite_key = floor_sprite, spawn_list = "ZOMBIE_SPAWNER_LIST")
    SP.set_description(text=ZOMBIE_DESC)
    SP.set_spawner_at(x=x,y=y, map=map)
    return SP 
def new_rogue_spawner(x,y,map):
    tile = map.get_tile(x,y)
    if not tile: return None 
    floor_sprite = tile.default_sprite_key 
    SP = Spawner(x=x, y=y, front_sprite = "abandoned_house", sprite_key = floor_sprite, spawn_list = "ROGUE_SPAWNER_LIST")
    SP.set_description(text=ROGUE_DESC)
    SP.set_spawner_at(x=x,y=y, map=map)
    return SP 
def new_demon_spawner(x,y,map): 
    tile = map.get_tile(x,y)
    if not tile: return None 
    floor_sprite = tile.default_sprite_key 
    SP = Spawner(x=x, y=y, front_sprite = "spawner_demon", sprite_key = floor_sprite, spawn_list = "DEMON_SPAWNER_LIST")
    SP.set_description(text=DEMON_DESC)
    SP.set_spawner_at(x=x,y=y, map=map)
    return SP 
def new_enemy_tower_spawner(x,y,map):
    tile = map.get_tile(x,y)
    if not tile: return None 
    floor_sprite = tile.default_sprite_key 
    SP = Spawner(x=x, y=y, front_sprite = "enemy_tower", sprite_key = floor_sprite, spawn_list = "ENEMY_FACTION_LIST")
    SP.set_description(text="Once valiant and honorable bannermens, now they do anything for money, worst than mercenaries ...")
    SP.set_spawner_at(x=x,y=y, map=map)
    return SP 

class Stair(ActionTile): # not used yet 
    def __init__(self, x=0, y = 0,front_sprite = "stair_up", walkable=True, sprite_key="grass"):
        ActionTile.__init__(self, x=x, y = y, front_sprite = front_sprite, walkable = walkable, sprite_key = sprite_key)
        self.stair = None # used to store a tuple map coord to connect between maps 
        self.stair_x = None # points to the stair tile from the map with coord self.stair
        self.stair_y = None # points to the stair tile from the map with coord self.stair 
    
# TileBuilding.production() || { TileBuilding.villagers() } || {}
# TileBuilding.update() || { TileBuilding.production() } || { TileBuilding.villagers() }
# TileBuilding.retrieve_food() || { Character.add_item() | TileBuilding.update_inv_window() } || {}
# TileBuilding.retrieve_wood() || { Character.add_item() | TileBuilding.update_inv_window() } || {}
# TileBuilding.store_resource() || { Character.remove_item() } || {}
class TileBuilding(ActionTile): # interface class
    __serialize_only__ = ActionTile.__serialize_only__ + ["villagers", "villagers_max", "food", "stone", "metal", "wood", "b_enemy", "turn_counter"]
    def __init__(self, x=0,y=0,front_sprite = "Castle", walkable=True, sprite_key="grass", b_enemy = False):
        ActionTile.__init__(self, x = x, y = y, front_sprite = front_sprite, walkable=walkable, sprite_key=sprite_key )
        self.villagers = 5
        self.villagers_max = 40
        self.food = 0
        self.wood = 0
        self.stone = 0
        self.metal = 0
        self.turn_counter = 0 
        self.b_enemy = b_enemy
        if self.b_enemy: self.villagers = self.villagers_max 
        self.enemy_table = TILE_BUILDING_ENEMY_TABLE 
    def clear_resources(self):
        self.food = 0
        self.wood = 0
        self.stone = 0
        self.metal = 0 
    def bonus_resources(self, max = 100):
        self.food += d(0,max)
        self.wood += d(0,max)
        self.stone += d(0,max)
        self.metal += d(0,max) 
    def production(self, multiplier = 1.0):
        if self.b_enemy: return 
        self.villagers = min( (1.0+0.005*multiplier)*self.villagers, self.villagers_max )
        self.food += multiplier*d(0,self.villagers/PROD_INV_FACTOR)
        self.wood += multiplier*d(0,self.villagers/PROD_INV_FACTOR)
        self.stone += multiplier*d(0,self.villagers/PROD_INV_FACTOR)
        self.metal += multiplier*d(0,self.villagers/PROD_INV_FACTOR)
    def enemy_building_update(self, ply_dist, map):
        if not self.b_enemy: 
            self.remove_layer("red_flag")
            return         
        self.add_layer_if_not_already("red_flag")
        if ply_dist >= 4: return 
        if not map.can_place_character_at(self.x, self.y): return 
        if self.villagers > 0:
            enemy = map.generate_enemy_by_chance_by_list_at(self.x, self.y, self.enemy_table)
            if enemy:
                self.villagers -= 5
                map.enemies.append(enemy)
                map.place_character(enemy)
        else:
            self.b_enemy = False 
            self.villagers = 1
            self.bonus_resources() 
    def building_attack(self, game_instance):
        return True 
    def update(self, game_instance = None):
        if not game_instance: return 
        mult = 1.0
        if self.turn_counter > 500*game_instance.turn: mult = 10.0 # still better to stay in the map
        self.turn_counter = game_instance.turn
        self.production(multiplier = mult)
        ply_dist = game_instance.player.distance(self)
        map = game_instance.map
        # message when close to a village 
        if ply_dist < 20:
            game_instance.flag_near_to_village = True 
        else:
            game_instance.flag_near_to_village = False 
        # -- 
        self.building_attack(game_instance)
        # -- 
        self.enemy_building_update(ply_dist, map)
    def retrieve_food(self, game_instance, quantity = 500):
        if self.food >= quantity:
            self.food -= quantity
            game_instance.player.add_item(Food(name = "Meat", nutrition = quantity))
            game_instance.update_inv_window()
            return True 
        return False
    def retrieve_wood(self, game_instance, quantity = 500):
        if self.wood >= quantity:
            self.wood -= quantity
            game_instance.player.add_item(Wood(value = quantity))
            game_instance.update_inv_window()
            return True 
        return False
    def retrieve_metal(self, game_instance, quantity = 500):
        if self.metal >= quantity:
            self.metal -= quantity
            game_instance.player.add_item(Metal(value = quantity))
            game_instance.update_inv_window()
            return True 
        return False
    def retrieve_stone(self, game_instance, quantity = 500):
        if self.stone >= quantity:
            self.stone -= quantity
            game_instance.player.add_item(Stone(value = quantity))
            game_instance.update_inv_window()
            return True 
        return False
    def store_resource(self, res, char):
        if isinstance(res, Resource): res.store(char, self)
    def menu_garrison(self, current_menu, current_item, menu_instance, game_instance):
        """ return True means that the menu should close """
        if not hasattr( self,"heroes" ): return False # not meant to be used without that attribute 
        # -- select and build the menu garrison on runtime
        if current_item == "Garrison >": 
            menu_instance.set_list("Garrison >", [ "Garrison+", "Garrison-", ".." ])
            return False # necessary ? 
        # --
        if current_menu == "Garrison >":
            if current_item == "..":
                menu_instance.set_list()
                return False
            if current_item == "Garrison+":
                if len(game_instance.players) > 1: 
                    self.heroes.update({ game_instance.player.name : game_instance.player})
                    game_instance.remove_player() 
                    game_instance.place_players() # maybe not necessary 
                    game_instance.draw() 
                    return True 
            if current_item == "Garrison-":
                if len( list( self.heroes.keys()) )>0:
                    menu_instance.set_list("Garrison-", self.heroes)
                    return False
        if current_menu == "Garrison-":
            if current_item:
                hero = self.heroes.get(current_item)
                if not hero: 
                    menu_instance.close()
                    return True
                dx, dy = game_instance.player.get_forward_direction()
                player = game_instance.player 
                spawn_tile = game_instance.map.get_tile(player.x+dx, player.y + dy)
                if not spawn_tile:
                    game_instance.add_message("Can't generate player at this position, please rotate the current character")
                    menu_instance.close()
                    return True
                if spawn_tile.current_char:
                    game_instance.add_message("Can't generate player at this position, please rotate the current character")
                    menu_instance.close()
                    return True 
                hero.x = player.x + dx
                hero.y = player.y + dy
                self.heroes.pop(current_item)
                game_instance.players.update({current_item: hero})
                print( hero.name, hero.party, hero.current_map )
                game_instance.place_players()
                game_instance.update_prior_next_selection() # -- fix -- Can't cycle hero that comes from garrison
                if game_instance.journal_window: game_instance.journal_window.update_journal() 
                game_instance.draw()
                return True
        return False
    def collect_all_resources(self, game_instance):
        self.store_all_resources(game_instance)
        if self.food>0.1: self.retrieve_food(game_instance, self.food)
        if self.wood>0.1: self.retrieve_wood(game_instance, self.wood)
        if self.metal>0.1: self.retrieve_metal(game_instance, self.metal)
        if self.stone>0.1: self.retrieve_stone(game_instance, self.stone)
        game_instance.add_message("Collected All Resources")
    def store_all_resources(self, game_instance):
        """ True means success """ 
        resources = [ e for e in game_instance.player.items if isinstance(e, Food) or isinstance(e, Resource) ]
        if not resources: return False 
        if len(resources)<=0: return False 
        for v in resources: self.store_resource(v, game_instance.player)
        game_instance.update_inv_window()
        return True 
    def menu_resources(self, current_menu, current_item, menu_instance, game_instance):
        """ return True means that the menu should close """
        from gui import info 
        resources = { e.info() : e for e in game_instance.player.items if isinstance(e, Food) or isinstance(e, Resource) }
        # -- 
        if current_item == "Resources >":
            menu_instance.set_list("Resources >",[ 
                f"-> food: {self.food:.0f}", 
                f"-> wood: {self.wood:.0f}", 
                f"-> metal: {self.metal:.0f}", 
                f"-> stone: {self.stone:.0f}", 
                "Resources+", 
                "Resources++", 
                "Resources--",
                "Food-", 
                "Wood-", 
                "Metal-", 
                "Stone-", 
                ".." 
            ])
            return False 
        # -- 
        if current_menu == "Resources >":
            match current_item:
                case "..":
                    menu_instance.set_list()
                    return False
                case "Resources+":
                    if self.update_resource_p_menu(menu_instance, resources): return False 
                case "Resources++":
                    # if len(resources) > 0:
                        # for k,v in iter(resources.items()):
                            # self.store_resource(v, game_instance.player)
                        # game_instance.update_inv_window()
                        # return True 
                    if self.store_all_resources(game_instance): return True 
                case "Food-":
                    qtt, ok = QInputDialog.getDouble(
                        menu_instance, 
                        'Input Dialog', 
                        f'Quantity ({self.food:.1f}) :',
                        self.food
                    )
                    if ok and qtt > 0 and self.retrieve_food(game_instance, qtt):
                        return True 
                case "Wood-":
                    qtt, ok = QInputDialog.getDouble(
                        menu_instance, 
                        'Input Dialog', 
                        f'Quantity ({self.wood:.1f}) :',
                        self.wood 
                    )
                    if ok and qtt > 0 and self.retrieve_wood(game_instance, qtt):
                        return True 
                case "Metal-":
                    qtt, ok = QInputDialog.getDouble(
                        menu_instance, 
                        'Input Dialog', 
                        f'Quantity ({self.metal:.1f}) :',
                        self.metal 
                    )
                    if ok and qtt > 0 and self.retrieve_metal(game_instance, qtt):
                        return True
                case "Stone-":
                    qtt, ok = QInputDialog.getDouble(
                        menu_instance, 
                        'Input Dialog', 
                        f'Quantity ({self.stone:.1f}) :',
                        self.stone 
                    )
                    if ok and qtt > 0 and self.retrieve_stone(game_instance, qtt):
                        return True 
                case "Resources--":
                    self.collect_all_resources(game_instance) 
                    return True 
        if current_menu == "Resources+":
            if current_item in resources:
                res_obj = resources.pop(current_item)
                self.store_resource(res_obj, game_instance.player)
                game_instance.update_inv_window()
                return not self.update_resource_p_menu(menu_instance, resources)
        return False 
    def update_resource_p_menu(self, menu_instance, resources):
        if len(resources) > 0:
            menu_instance.set_list("Resources+", [f"-> food: {self.food:.0f}", f"-> wood: {self.wood:.0f}", f"-> metal: {self.metal:.0f}", f"-> stone: {self.stone:.0f}", ]+list(resources.keys())+[".."])
            return True 
        return False 
    def set_population_menu(self, menu_instance):
         menu_instance.set_list( "Overview >" ,
            [f"Population : {self.villagers:.1f}/{self.villagers_max}",f"Mean Production : {self.villagers/PROD_INV_FACTOR/2.0:.1f}/turn"]+[f"Food : {self.food:.1f}" if self.food else None ]+[f"Wood : {self.wood:.1f}" if self.wood else None ]+[f"Stone : {self.stone:.1f}" if self.stone else None ]+[f"Metal : {self.metal:.1f}" if self.metal else None ]+[".."]
         )
    def refresh_game_instance(self, x, y, game_instance):
        game_instance.place_players()
        game_instance.update_prior_next_selection()
        game_instance.dirty_tiles.add((x, y))
        game_instance.draw()
    def add_char_to_garrison(self, char):
        # meant to be used on building creation.
        if not hasattr( self,"heroes" ): return False # not meant to be used without that attribute 
        self.heroes.update({ char.name : char })
        return True 
    def set_background_sprite(self, sprite_key):
        self.default_sprite_key = sprite_key 
    def set_background_tile(self, tile):
        self.default_sprite_key = tile.default_sprite_key 
    def get_free_spawn_position(self, game_instance):
        map = game_instance.map 
        for dx, dy in SQUARE_DIFF_SPIRAL_MOVES_15:
            x = self.x + dx
            y = self.y + dy 
            if map.can_place_character_at(x,y): return (x,y) 
        return None 
    def write_quest_note(self, game_instance):
        map = game_instance.map 
        if not map: return 
        text = "Quest : "+self.description+"\n"+f"- Location : {self.x}, {map.height-self.y}\n- Conquest : defeat all enemies and take control of this building."
        game_instance.take_note_on_diary(text = text)

# Castle.action() || { Castle.update_menu_list() | Castle.new_npc() | TileBuilding.menu_garrison() | TileBuilding.menu_resources() } || { Character.add_item(), TileBuilding.update_inv_window(), Character.remove_item() }
class Castle(TileBuilding):
    __serialize_only__ = TileBuilding.__serialize_only__ + ["name","heroes","num_heroes"]
    def __init__(self, x=0, y=0, name = "Home", b_enemy=False):
        TileBuilding.__init__(self, x=x,y=y, front_sprite = Tile.get_random_sprite(key_filter="castle"), walkable=True, sprite_key="grass", b_enemy=b_enemy)
        self.name = name 
        self.heroes = {}
        self.num_heroes = 0
        self.menu_list = []    
    def production(self, multiplier = 1.0):
        if self.b_enemy: return 
        if self.villagers == 0: self.villagers = 0.1
        self.villagers = min( (1.0+0.005*multiplier)*self.villagers, self.villagers_max )
        self.food += multiplier*d(0,self.villagers/PROD_INV_FACTOR)
    def action(self):
        from gui import info 
        self.update_menu_list()
        def f(current_menu, current_item, menu_instance, game_instance):
            self.update_menu_list(menu_instance)
            if current_item == "..": menu_instance.set_list()
            if current_item == "Overview >": self.set_population_menu(menu_instance)
            if current_item == "Exit": menu_instance.close()
            if current_item == "Certificates >": 
                menu_instance.set_list("Certificates >", [
                    "Lumber Mill (500 Wood, 250 Food)", 
                    "Quarry (500 Wood 500 Food 500 Metal)",
                    "Farm (500 Wood, 500 Food)", 
                    "Blacksmith (500 Wood, 500 Food, 200 Metal)",
                    "Guard Tower (2000 Wood, 2500 Food)", 
                    "Tavern (100 Wood 150 Food)",
                    ".."])
                return 
            if "Guard Tower" in current_item:
                if self.wood >= 2000 and self.food >= 2500:
                    self.wood -= 2000 
                    self.food -= 2500
                    game_instance.certificates.append("Guard Tower")
                    menu_instance.close()
                    return 
            if "Lumber Mill" in current_item:
                if self.wood >= 500 and self.food >= 250:
                    self.wood -= 500 
                    self.food -= 250
                    game_instance.certificates.append("Lumber Mill")
                    menu_instance.close()
                    return 
            if "Farm" in current_item:
                if self.wood >= 500 and self.food >= 500:
                    self.wood -= 500 
                    self.food -= 500
                    game_instance.certificates.append("Farm")
                    menu_instance.close()
                    return 
            if "Quarry" in current_item:
                if self.wood >= 500 and self.food >= 500 and self.metal >= 500:
                    self.wood -= 500 
                    self.food -= 500
                    self.metal -= 500
                    game_instance.certificates.append("Quarry")
                    menu_instance.close()
                    return 
            if "Blacksmith" in current_item:
                if self.wood >= 500 and self.food >= 500 and self.metal >= 200:
                    self.wood -= 500 
                    self.food -= 500
                    self.metal -= 200
                    game_instance.certificates.append("Blacksmith")
                    menu_instance.close()
                    return 
            if "Tavern" in current_item:
                if self.wood >= 100 and self.food >= 150:
                    self.wood -= 100 
                    self.food -= 150
                    game_instance.certificates.append("Tavern")
                    menu_instance.close()
                    return 
            if "Quest" in current_item:
                if self.food >=50:
                    self.food -= 50 
                    map = game_instance.map 
                    if len(map.spawners)>0:
                        SP = random.choice(map.spawners) 
                        SP.write_quest_note(game_instance)
                    if len(map.enemy_buildings)>0:
                        SP = random.choice( list(map.enemy_buildings) ) 
                        SP.write_quest_note(game_instance)
                    menu_instance.close()
                    return 
                
            if "New Hero" in current_item:
                if self.food >= 2000:
                    if self.new_hero(game_instance):
                        self.food -= 2000 
                        self.villagers -= 15
                else:
                    game_instance.add_message("Can't afford to purchase new heroes ...")
                menu_instance.close()
            if self.menu_garrison(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
            if self.menu_resources(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
        return f
    def update_menu_list(self, selection_box_instance = None):
        self.menu_list.clear()
        self.menu_list += [
            f"Castle [{self.name}]",
            f"-> heroes: {len(self.heroes)}",
            f"-> food: {self.food:.0f}",
            f"-> wood: {self.wood:.0f}",
            f"-> metal: {self.metal:.0f}",
            f"-> stone: {self.stone:.0f}",
            "Overview >",
            "New Hero (2000 Food)",
            "Garrison >",
            "Resources >",
            "Certificates >",
            "Quest (50 Food)",
            "Exit"
        ]
    def new_hero(self, game_instance):
        if self.villagers <= 15: 
            game_instance.add_message("There are no villagers to recruit ...")
            return False 
        # dx, dy = game_instance.player.get_forward_direction()
        # player = game_instance.player 
        spawn_tile = game_instance.map.get_tile( *self.get_free_spawn_position(game_instance) ) #player.x+dx, player.y + dy)
        if not spawn_tile:
            print("invalid tile")
            game_instance.add_message("Can't generate player at this position, please rotate the current character")
            return False
        # if spawn_tile.current_char:
            # print("tile occupied by character")
            # game_instance.add_message("Can't generate player at this position, please rotate the current character")
            # return False
        new_name = QInputDialog.getText(game_instance, 'Input Dialog', 'Character Name :')
        if new_name:
            npc_name = new_name[0]
        if not npc_name:
            npc_name = "Hero_"+rn(7)
        game_instance.add_hero(
            key = npc_name, 
            name = npc_name, 
            x = spawn_tile.x, 
            y = spawn_tile.y, 
            b_generate_items = False, 
            current_map = game_instance.current_map,
            sprite = random.choice(SPRITE_NAMES_PLAYABLES)
        )
        self.refresh_game_instance(spawn_tile.x, spawn_tile.y, game_instance)
        return True
    
    @classmethod
    def new(cls, game_instance, x = None,y = None):
        if not x: x = game_instance.player.x
        if not y: y = game_instance.player.y
        obj = Castle(x=x,y=y)
        obj.food = 2000 
        game_instance.map.set_tile(x, y, obj)
        game_instance.map.buildings.append(obj)
        game_instance.draw()
        
class Tavern(TileBuilding):
    __serialize_only__ = TileBuilding.__serialize_only__ + ["name"]
    def __init__(self, x=0, y=0, name = "Tavern", b_enemy=False, background_sprite = "grass"):
        TileBuilding.__init__(self, x=x,y=y, front_sprite = "tavern", walkable=True, sprite_key=background_sprite, b_enemy=b_enemy)
        self.name = name 
        self.menu_list = [] 
    def action(self):
        from gui import info 
        self.update_menu_list()
        def f(current_menu, current_item, menu_instance, game_instance):
            self.update_menu_list(menu_instance)
            if current_item == "..": menu_instance.set_list()
            if current_item == "Overview >": self.set_population_menu(menu_instance)
            if current_item == "Exit": menu_instance.close()
            if "Quest" in current_item:
                if self.food >=50:
                    self.food -= 50 
                    map = game_instance.map 
                    if len(map.spawners)>0:
                        SP = random.choice(map.spawners) 
                        SP.write_quest_note(game_instance)
                    if len(map.enemy_buildings)>0:
                        SP = random.choice( list(map.enemy_buildings) ) 
                        SP.write_quest_note(game_instance)
                    menu_instance.close()
                    return 
            if "New Hero" in current_item:
                if self.food >= 2000:
                    if self.new_hero(game_instance):
                        self.food -= 2000 
                        self.villagers -= 15
                else:
                    game_instance.add_message("Can't afford to purchase new heroes ...")
                menu_instance.close()
            if self.menu_garrison(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
            if self.menu_resources(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
        return f
    def update_menu_list(self, selection_box_instance = None):
        self.menu_list.clear()
        self.menu_list += [
            f"Tavern",
            f"-> food: {self.food:.0f}",
            f"-> wood: {self.wood:.0f}",
            f"-> metal: {self.metal:.0f}",
            f"-> stone: {self.stone:.0f}",
            "Overview >",
            "New Hero (2000 Food)",
            "Resources >",
            "Quest (50 Food)",
            "Exit"
        ]
    def new_hero(self, game_instance):
        if self.villagers <= 15: 
            game_instance.add_message("There are no villagers to recruit ...")
            return False 
        spawn_tile = game_instance.map.get_tile( *self.get_free_spawn_position(game_instance) ) #player.x+dx, player.y + dy)
        if not spawn_tile:
            print("invalid tile")
            game_instance.add_message("Can't generate player at this position, please rotate the current character")
            return False
        new_name = QInputDialog.getText(game_instance, 'Input Dialog', 'Character Name :')
        if new_name:
            npc_name = new_name[0]
        if not npc_name:
            npc_name = "Hero_"+rn(7)
        game_instance.add_hero(
            key = npc_name, 
            name = npc_name, 
            x = spawn_tile.x, 
            y = spawn_tile.y, 
            b_generate_items = False, 
            current_map = game_instance.current_map,
            sprite = random.choice(SPRITE_NAMES_PLAYABLES)
        )
        self.refresh_game_instance(spawn_tile.x, spawn_tile.y, game_instance)
        return True        
    def production(self, multiplier = 1.0):
        if self.b_enemy: return 
        if self.villagers == 0: self.villagers = 0.1
        self.villagers = min( (1.0+0.005*multiplier)*self.villagers, self.villagers_max )

# Mill.action() || { Mill.update_menu_list() | TileBuilding.menu_resources() } || { Character.add_item(), TileBuilding.update_inv_window(), Character.remove_item() }
class Mill(TileBuilding):
    __serialize_only__ = TileBuilding.__serialize_only__ + ["name"]
    def __init__(self, x=0, y =0, name = "Farm", food = d(500,2000), b_enemy=False):
        TileBuilding.__init__(self, x=x, y=y, front_sprite = "mill", walkable=True, sprite_key="grass", b_enemy=b_enemy)
        self.name = name 
        self.menu_list = []
        self.food = food 
        self.description = MILL_DESC
    def action(self):
        self.update_menu_list()
        def f(current_menu, current_item, menu_instance, game_instance):
            self.update_menu_list(menu_instance)
            if current_item == "..": menu_instance.set_list()
            if current_item == "Overview >": self.set_population_menu(menu_instance)
            if current_item == "Exit": menu_instance.close()
            if self.menu_resources(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
        return f
    def update_menu_list(self, selection_box_instance = None):
        self.menu_list.clear()
        self.menu_list += [
            f"Resource [{self.name}]",
            f"-> food: {self.food:.0f}",
            "Overview >",
            "Resources >",
            "Exit"
        ]
    def production(self, multiplier = 1.0):
        if self.b_enemy: return 
        self.villagers = min( (1.0+0.005*multiplier)*self.villagers, self.villagers_max )
        self.food += multiplier*d(0,2*self.villagers/PROD_INV_FACTOR)

# LumberMill.action() || { LumberMill.update_menu_list() | TileBuilding.menu_resources() } || { Character.add_item(), TileBuilding.update_inv_window(), Character.remove_item() }
class LumberMill(TileBuilding):
    __serialize_only__ = TileBuilding.__serialize_only__ + ["name"]
    def __init__(self, x=0, y =0, name = "Lumber Mill", wood = d(500,2000), b_enemy=False):
        TileBuilding.__init__(self, x=x,y=y,front_sprite = "lumber_mill", walkable=True, sprite_key="grass", b_enemy=b_enemy)
        self.name = name 
        self.menu_list = []
        self.wood = wood
        self.melt_weap_dict = None
        self.description = LUMBER_DESC
    def action(self):
        self.update_menu_list()
        def f(current_menu, current_item, menu_instance, game_instance):
            self.update_menu_list(menu_instance)
            if current_item == "..": 
                menu_instance.set_list()
                return 
            if current_item == "Exit": 
                menu_instance.close()
                return     
            if current_menu == "main":
                if current_item == "Overview >": 
                    self.set_population_menu(menu_instance)
                    return 
            if self.menu_resources(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
        return f
    def update_menu_list(self, selection_box_instance = None):
        self.menu_list.clear()
        self.menu_list += [
            f"Resource [{self.name}]",
            f"-> wood: {self.wood:.0f}",
            "Overview >",
            "Resources >",
            "Exit"
        ]
    def production(self, multiplier = 1.0):
        if self.b_enemy: return 
        self.villagers = min( (1.0+0.005*multiplier)*self.villagers, self.villagers_max )
        self.wood += multiplier*d(0,2*self.villagers/PROD_INV_FACTOR)
        
class Quarry(TileBuilding):
    __serialize_only__ = TileBuilding.__serialize_only__ + ["name"]
    def __init__(self, x=0, y =0, name = "Quarry", stone = d(500,2000), b_enemy=False):
        TileBuilding.__init__(self, x=x,y=y,front_sprite = "quarry", walkable=True, sprite_key="grass", b_enemy=b_enemy)
        self.name = name 
        self.menu_list = []
        self.stone = stone
        self.melt_weap_dict = None
        self.description = QUARRY_DESC
    def action(self):
        self.update_menu_list()
        def f(current_menu, current_item, menu_instance, game_instance):
            self.update_menu_list(menu_instance)
            if current_item == "..": 
                menu_instance.set_list()
                return 
            if current_item == "Exit": 
                menu_instance.close()
                return     
            if current_menu == "main":
                if current_item == "Overview >": 
                    self.set_population_menu(menu_instance)
                    return 
            if self.menu_resources(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
        return f
    def update_menu_list(self, selection_box_instance = None):
        self.menu_list.clear()
        self.menu_list += [
            f"Resource [{self.name}]",
            f"-> stone: {self.stone:.0f}",
            "Overview >",
            "Resources >",
            "Exit"
        ]
    def production(self, multiplier = 1.0):
        if self.b_enemy: return 
        self.villagers = min( (1.0+0.005*multiplier)*self.villagers, self.villagers_max )
        self.stone += multiplier*d(0,2*self.villagers/PROD_INV_FACTOR) 

class Blacksmith(TileBuilding):
    __serialize_only__ = TileBuilding.__serialize_only__ + ["name"]
    def __init__(self, x=0, y =0, name = "Blacksmith", b_enemy=False):
        TileBuilding.__init__(self, x=x,y=y,front_sprite = "blacksmith", walkable=True, sprite_key="dirt", b_enemy=b_enemy)
        self.name = name 
        self.menu_list = []
        self.melt_weap_dict = None
        self.description = BLACKSMITH_DESC
    def update_melt_menu(self, menu_instance):
        menu_instance.set_list("Melt Weapons >", ["Blacksmith > Melt Weapons"] + list(self.melt_weap_dict.keys())+[".."])
    def action(self):
        self.update_menu_list()
        def f(current_menu, current_item, menu_instance, game_instance):
            self.update_menu_list(menu_instance)
            if current_item == "..": 
                menu_instance.set_list()
                return 
            if current_item == "Exit": 
                menu_instance.close()
                return     
            if current_menu == "main":
                if current_item == "Overview >": 
                    self.set_population_menu(menu_instance)
                    return 
                if "Weapon Repair" in current_item: 
                    if self.metal >= 100:
                        self.metal -= 100
                        game_instance.player.add_item(WeaponRepairTool(name="Whetstone", uses=10))
                        game_instance.add_message("Whetstone Added to Inventory")
                        game_instance.update_inv_window()
                        menu_instance.close()
                        return     
                if current_item == "Buy 100 Bolts for Crossbows (500 Wood)": 
                    if self.wood >= 500:
                        self.wood -= 500
                        game_instance.player.add_item( Ammo(name="bolt", uses=100) )
                        game_instance.add_message("100 Bolts Added to Inventory")
                        game_instance.update_inv_window()
                        menu_instance.close()
                        return 
                if current_item == "Melt Weapons >":
                    ptr_counter = [0]
                    def boolean_test(it, ctr):                        
                        if isinstance(it, Sword) or isinstance(it, Mace) or isinstance(it, Fireweapon):
                            ctr[0] += 1
                            return True 
                        return False 
                    self.melt_weap_dict = { f"{ptr_counter[0]}. "+it.info() : it for it in game_instance.player.items if boolean_test(it, ptr_counter) }
                    self.update_melt_menu(menu_instance)
                    return 
            if self.menu_resources(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
            if current_menu == "Melt Weapons >":
                if self.melt_weap_dict:
                    if current_item in self.melt_weap_dict:
                        mt_item = self.melt_weap_dict.pop(current_item)
                        game_instance.player.remove_item(mt_item)
                        if isinstance(mt_item, Fireweapon):
                            self.wood += 50 
                        else:    
                            self.metal += 50 
                        self.update_melt_menu(menu_instance)
                        return 
        return f
    def update_menu_list(self, selection_box_instance = None):
        self.menu_list.clear()
        self.menu_list += [
            f"Resource [{self.name}]",
            f"-> metal: {self.metal:.0f}",
            "Overview >",
            "Resources >",
            "Melt Weapons >",
            "Weapon Repair (100 Metal)",
            "Buy 100 Bolts for Crossbows (500 Wood)",
            "Exit"
        ]
    def production(self, multiplier = 1.0):
        if self.b_enemy: return 
        self.villagers = min( (1.0+0.005*multiplier)*self.villagers, self.villagers_max )
        # self.metal += multiplier*d(0,2*self.villagers/PROD_INV_FACTOR)

# GuardTower.action() || { GuardTower.update_menu_list() | GuardTower.new_swordman() | GuardTower.new_mounted_knight() | TileBuilding.menu_garrison() | TileBuilding.menu_resources() } || { Character.add_item(), TileBuilding.update_inv_window(), Character.remove_item() }
class GuardTower(TileBuilding):
    __serialize_only__ = TileBuilding.__serialize_only__ + ["name","heroes","num_heroes","turret","b_upg_swordman"]
    def __init__(self, x=0, y =0,name = "Guard Tower", b_enemy=False, floor_sprite = "grass"):
        TileBuilding.__init__(self, x=x, y=y, front_sprite = "tower", walkable=True, sprite_key=floor_sprite, b_enemy=b_enemy)
        self.name = name 
        self.heroes = {}
        self.num_heroes = 0
        self.menu_list = []
        self.turret = None
        if self.b_enemy: self.add_enemy_turret() 
        self.b_upg_swordman = False 
        self.description = TOWER_DESC
    def add_enemy_turret(self):
        self.turret = RangedRaider(name='turret', hp=200, b_generate_items=True, sprite='evil_crossbowman')
    def building_attack(self, game_instance):
        if self.turret is None: return False 
        self.turret.x = self.x 
        self.turret.y = self.y
        if self.turret.hp <= 0 or self.villagers <= 0 : 
            self.turret = None 
            return False 
        primary = self.turret.primary_hand 
        if primary and primary.ammo <= 30: # ammo recharge  
            if self.b_enemy: 
                primary.ammo += 50 
            else: 
                if self.wood >=10 and self.metal >= 10: 
                    primary.ammo += 50 
                    self.wood -= 10 
                    self.metal -= 10 
        if AB_ranged_attack(char=self.turret, game_instance=game_instance): return True 
    def add_sentinel(self, game_instance): 
        if self.b_enemy: return False 
        if self.villagers < 2: 
            game_instance.add_message("Not enough villagers to recruit ...") 
            return False 
        if isinstance(self.turret, Player): 
            self.turret.hp += 50 
            return True 
        else: 
            self.turret = Player(name = "turret", hp=50,x=self.x, y=self.y) 
            self.turret.equip_item(Fireweapon(name = "Crossbow", damage = 7, ammo=100, range=7, projectile_sprite='bolt', ammo_type='bolt'), "primary_hand")
            return True 
    def action(self):
        from gui import info 
        self.update_menu_list()
        def f(current_menu, current_item, menu_instance, game_instance):
            self.update_menu_list(menu_instance)
            if current_item == "..": menu_instance.set_list()
            if current_item == "Overview >": self.set_population_menu(menu_instance)
            if current_item == "Exit": menu_instance.close()
            if "Upgrade Swordman" in current_item:
                if self.metal >= 2000 and self.stone >= 2000:
                    self.metal -= 2000
                    self.stone -= 2000 
                    self.b_upg_swordman = True 
                    menu_instance.close()
                    return 
            if "Add a Tower Sentinel" in current_item:
                if self.food >= 200 and self.wood >= 400:
                    if self.add_sentinel(game_instance):
                        self.villagers -= 2 
                        self.food -= 200 
                        self.wood -= 400 
                else:
                    game_instance.add_message("Can't afford to purchase a sentinel ...")
                menu_instance.close()
                return 
            if "Recruit Swordman" in current_item: 
                if self.food >= 500: 
                    if self.new_swordman(game_instance):
                        self.villagers -= 2 
                        self.food -= 500 
                else:
                    game_instance.add_message("Can't afford to purchase Swordman ...")
                menu_instance.close()
                return 
            if "Recruit Crossbowman" in current_item:
                if self.food >= 400 and self.wood >= 700:
                    if self.new_crossbowman(game_instance):
                        self.villagers -= 3
                        self.food -= 400 
                        self.wood -= 700 
                else:
                    game_instance.add_message("Can't afford to purchase Swordman ...")
                menu_instance.close()
                return 
            if "Recruit Mounted Knight" in current_item:
                if self.food >= 700 and self.wood >= 1200:
                    if self.new_mounted_knight(game_instance):
                        self.villagers -= 5 
                        self.food -= 700 
                        self.wood -= 1200 
                else:
                    game_instance.add_message("Can't afford to purchase Mounted Knight ...")
                menu_instance.close()
                return 
            if self.menu_garrison(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
            if self.menu_resources(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
        return f
    def update_menu_list(self, selection_box_instance = None):
        self.menu_list.clear()
        if self.turret:
            sentinel_str = f"-> sentinel: {self.turret.hp} (HP) {self.turret.primary_hand.ammo} (Shoots)"
        else:
            sentinel_str = f"-> sentinel: {0} (HP)"
        self.menu_list += [
            f"Building [{self.name}]",
            sentinel_str, 
            f"-> garrison: {len(self.heroes)}",
            f"-> food: {self.food:.0f}",
            f"-> wood: {self.wood:.0f}",
            f"-> metal: {self.metal:.0f}",
            f"-> stone: {self.stone:.0f}",
            "Overview >",
            "Add a Tower Sentinel +50 HP (200 Food, 400 Wood)", 
            "Recruit Swordman (500 Food)",
            "Recruit Crossbowman (400 Food, 700 Wood)",
            "Recruit Mounted Knight (700 Food 1200 Wood)",
            "Garrison >",
            "Resources >"
        ]
        if not self.b_upg_swordman: 
            self.menu_list += [ "Upgrade Swordman (2000 Metal 2000 Stone)" ]
        self.menu_list += ["Exit"]
    def new_swordman(self, game_instance):
        if self.villagers <= 2:
            game_instance.add_message("There are no villagers to recruit ...")
            return False 
        spawn_tile = game_instance.map.get_tile( *self.get_free_spawn_position(game_instance) ) 
        if not spawn_tile: return False
        npc_name = "Swordman_"+rn(10)
        # --
        sw_sprite = "swordman"
        sw_hp = 70 
        sw_st = 80
        sw_dmg = 7
        if self.b_upg_swordman:
            sw_sprite = "upg_swordman"
            sw_hp = 100 
            sw_st = 100 
            sw_dmg = 8 
        # -- 
        npc_obj = game_instance.add_player(
            key = npc_name, 
            name = npc_name, 
            x = spawn_tile.x, 
            y = spawn_tile.y, 
            b_generate_items = False, 
            current_map = game_instance.current_map,
            sprite = sw_sprite
        )
        npc_obj.set_max_stats(hp=sw_hp, st=sw_st)
        npc_obj.equip_item( Sword(name="Long_Sword", damage=sw_dmg, durability_factor=0.9995), "primary_hand" )
        npc_obj.hunger = npc_obj.max_hunger
        npc_obj.can_use_thrust_skill = True 
        npc_obj.copy_behaviour_config(game_instance.player)
        self.refresh_game_instance(spawn_tile.x, spawn_tile.y, game_instance)
        return True    
    def new_mounted_knight(self, game_instance): # not used yet 
        if self.villagers <= 5:
            game_instance.add_message("There are no villagers to recruit ...")
            return False 
        # dx, dy = game_instance.player.get_forward_direction()
        # player = game_instance.player 
        spawn_tile = game_instance.map.get_tile( *self.get_free_spawn_position(game_instance) ) # player.x+dx, player.y + dy)
        if not spawn_tile:
            game_instance.add_message("Can't generate player at this position, please rotate the current character")
            return False
        # if spawn_tile.current_char:
            # game_instance.add_message("Can't generate player at this position, please rotate the current character")
            # return False
        npc_name = "Knight_"+rn(7)
        npc_obj = game_instance.add_player(
            key = npc_name, 
            name = npc_name, 
            hp = 120,
            x = spawn_tile.x, 
            y = spawn_tile.y, 
            b_generate_items = False, 
            current_map = game_instance.current_map,
            sprite = "mounted_knight"
        )
        npc_obj.equip_item( Sword(name="Long_Sword", damage=10, durability_factor=0.9995), "primary_hand" )
        npc_obj.equip_item( Mace(damage=10, durability_factor=0.9995), "secondary_hand" )
        npc_obj.hunger = npc_obj.max_hunger
        npc_obj.can_use_thrust_skill = True 
        npc_obj.can_use_knight_skill = True 
        npc_obj.copy_behaviour_config(game_instance.player)
        self.refresh_game_instance(spawn_tile.x, spawn_tile.y, game_instance)
        return True    
    def new_crossbowman(self, game_instance):
        if self.villagers <= 3:
            game_instance.add_message("There are no villagers to recruit ...")
            return False 
        # dx, dy = game_instance.player.get_forward_direction()
        # player = game_instance.player 
        spawn_tile = game_instance.map.get_tile( *self.get_free_spawn_position(game_instance) ) # player.x+dx, player.y + dy)
        if not spawn_tile:
            game_instance.add_message("Can't generate player at this position, please rotate the current character")
            return False
        # if spawn_tile.current_char:
            # game_instance.add_message("Can't generate player at this position, please rotate the current character")
            # return False
        npc_name = "Crossbowman_"+rn(7)
        npc_obj = game_instance.add_player(
            key = npc_name, 
            name = npc_name, 
            hp = 80,
            x = spawn_tile.x, 
            y = spawn_tile.y, 
            b_generate_items = False, 
            current_map = game_instance.current_map,
            sprite = "crossbowman"
        )
        npc_obj.equip_item(Fireweapon(name = "Crossbow", damage = 5, ammo=70, range=7, projectile_sprite='bolt', ammo_type='bolt'), "primary_hand")
        npc_obj.hunger = npc_obj.max_hunger
        npc_obj.copy_behaviour_config(game_instance.player)
        self.refresh_game_instance(spawn_tile.x, spawn_tile.y, game_instance)
        return True
    def production(self, multiplier = 1.0):
        if self.b_enemy: return 
        if self.villagers == 0: self.villagers = 0.1
        self.villagers = min( (1.0+0.005*multiplier)*self.villagers, self.villagers_max )

class MagicTower(TileBuilding):
    __serialize_only__ = TileBuilding.__serialize_only__ + ["name","heroes","num_heroes"]
    def __init__(self, x=0, y =0,name = "Magic Tower", b_enemy=False, floor_sprite = "grass"):
        TileBuilding.__init__(self, x=x, y=y, front_sprite = "magic_tower", walkable=True, sprite_key=floor_sprite, b_enemy=b_enemy)
        self.name = name 
        self.heroes = {}
        self.num_heroes = 0
        self.menu_list = []
    def action(self):
        from gui import info 
        self.update_menu_list()
        def f(current_menu, current_item, menu_instance, game_instance):
            self.update_menu_list(menu_instance)
            if current_item == "..": menu_instance.set_list()
            if current_item == "Overview >": self.set_population_menu(menu_instance)
            if current_item == "Exit": menu_instance.close()
            if "Recruit Healer" in current_item:
                if self.food >= 500 and self.wood >= 500 and self.metal >= 500 and self.stone >= 500:
                    if self.new_healer(game_instance):
                        self.villagers -= 15
                        self.food -= 500 
                        self.wood -= 500 
                        self.stone -= 500 
                        self.metal -= 500 
                else:
                    game_instance.add_message("Can't afford to purchase a Healer ...")
                menu_instance.close()
            if self.menu_garrison(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
            if self.menu_resources(current_menu, current_item, menu_instance, game_instance):
                menu_instance.close()
                return 
        return f
    def update_menu_list(self, selection_box_instance = None):
        self.menu_list.clear()
        self.menu_list += [
            f"Building [{self.name}]",
            f"-> garrison: {len(self.heroes)}",
            f"-> food: {self.food:.0f}",
            f"-> wood: {self.wood:.0f}",
            f"-> stone: {self.stone:.0f}",
            f"-> metal: {self.metal:.0f}",
            "Overview >",
            "Recruit Healer (500 food, 500 wood, 500 stone, 500 Metal)",
            "Garrison >",
            "Resources >",
            "Exit"
        ]
    def new_healer(self, game_instance):
        if self.villagers <= 15:
            game_instance.add_message("There are no villagers to recruit ...")
            return False 
        # dx, dy = game_instance.player.get_forward_direction()
        # player = game_instance.player 
        spawn_tile = game_instance.map.get_tile( *self.get_free_spawn_position(game_instance) ) # player.x+dx, player.y + dy)
        if not spawn_tile:
            game_instance.add_message("Can't generate player at this position, please rotate the current character")
            return False
        # if spawn_tile.current_char:
            # game_instance.add_message("Can't generate player at this position, please rotate the current character")
            # return False
        npc_name = "Healer_"+rn(7)
        npc_obj = game_instance.add_player(
            key = npc_name, 
            cls_constructor = Healer,
            name = npc_name, 
            x = spawn_tile.x, 
            y = spawn_tile.y, 
            b_generate_items = False, 
            current_map = game_instance.current_map
        )
        npc_obj.hunger = npc_obj.max_hunger
        self.refresh_game_instance(spawn_tile.x, spawn_tile.y, game_instance)
        return True
    def production(self, multiplier = 1.0):
        if self.b_enemy: return 
        if self.villagers == 0: self.villagers = 0.1
        self.villagers = min( (1.0+0.005*multiplier)*self.villagers, self.villagers_max )    

# -- END 