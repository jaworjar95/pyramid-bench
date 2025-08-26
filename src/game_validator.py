"""
Game validator for the Pyramid Puzzle benchmark.
Validates paths and calculates Movement Points (MP) according to game rules.
"""

import re
from typing import List, Dict, Any, Tuple, Set


class GameState:
    """Tracks the current state of the game including position, items, and blocked tiles."""
    
    def __init__(self, blocked_tiles: List[str], collectibles: Dict[str, str]):
        self.position = None
        self.collected_items: Set[str] = set()
        self.blocked_tiles: Set[str] = set(blocked_tiles)
        self.collectibles = collectibles  # {item_type: tile_location}
        self.has_ladder = False
        self.has_key = False
        self.dynamite_used = False
        
    def collect_item(self, tile: str) -> str:
        """Collect item from tile if available. Returns item type or None."""
        for item_type, location in self.collectibles.items():
            if location == tile and item_type not in self.collected_items:
                self.collected_items.add(item_type)
                if item_type == "ladder":
                    self.has_ladder = True
                elif item_type == "key":
                    self.has_key = True
                return item_type
        return None
        
    def use_dynamite(self, target_tile: str) -> bool:
        """Use dynamite to clear a blocked tile."""
        if "dynamite" in self.collected_items and not self.dynamite_used:
            if target_tile in self.blocked_tiles:
                self.blocked_tiles.remove(target_tile)
                self.dynamite_used = True
                return True
        return False


class GameValidator:
    """Validates pyramid puzzle paths and calculates MP costs."""
    
    # Level max tiles
    LEVEL_MAX = {"A": 1, "B": 4, "C": 8, "D": 16, "E": 32}
    
    def __init__(self):
        pass
    
    def parse_tile(self, tile_str: str) -> Tuple[str, int]:
        """Parse tile string like 'E24' into level and number."""
        if not re.match(r'^[A-E]\d+$', tile_str):
            raise ValueError(f"Invalid tile format: {tile_str}")
        
        level = tile_str[0]
        number = int(tile_str[1:])
        
        if level not in self.LEVEL_MAX:
            raise ValueError(f"Invalid level: {level}")
        
        if number < 1 or number > self.LEVEL_MAX[level]:
            raise ValueError(f"Invalid tile number {number} for level {level}")
            
        return level, number
    
    def is_valid_move(self, from_tile: str, to_tile: str) -> Tuple[bool, str, int]:
        """
        Check if a move is valid and return (valid, move_type, mp_cost).
        Move types: 'clockwise', 'counter_clockwise', 'inward', 'outward_left', 'outward_right'
        """
        try:
            from_level, from_num = self.parse_tile(from_tile)
            to_level, to_num = self.parse_tile(to_tile)
        except ValueError as e:
            return False, "invalid_tile", 0
        
        # Same level movements (clockwise/counter-clockwise)
        if from_level == to_level:
            level_max = self.LEVEL_MAX[from_level]
            
            # Clockwise: X(Y+1) or X1 if Y=Xmax
            if (from_num < level_max and to_num == from_num + 1) or \
               (from_num == level_max and to_num == 1):
                return True, "clockwise", 1
            
            # Counter-clockwise: X(Y-1) or X(Xmax) if Y=1
            if (from_num > 1 and to_num == from_num - 1) or \
               (from_num == 1 and to_num == level_max):
                return True, "counter_clockwise", 1
        
        # Inward movement (up a level)
        if ord(to_level) == ord(from_level) - 1:  # B->A, C->B, D->C, E->D
            expected_to = (from_num + 1) // 2  # Ceiling division
            if to_num == expected_to:
                return True, "inward", 2  # Base cost, reduced by ladder
        
        # Outward movement (down a level)
        if ord(to_level) == ord(from_level) + 1:  # A->B, B->C, C->D, D->E
            # Outward-left: (X-1)(2Y-1)
            if to_num == 2 * from_num - 1:
                return True, "outward_left", 1
            # Outward-right: (X-1)(2Y)
            if to_num == 2 * from_num:
                return True, "outward_right", 1
        
        # Special case: From peak A1 to any B tile
        if from_tile == "A1" and to_level == "B":
            return True, "outward_from_peak", 1
        
        # Special case: From any B tile to peak A1
        if from_level == "B" and to_tile == "A1":
            return True, "inward_to_peak", 2
        
        return False, "invalid_move", 0
    
    def calculate_mp_cost(self, move_type: str, has_ladder: bool) -> int:
        """Calculate MP cost considering ladder effect."""
        base_costs = {
            "clockwise": 1,
            "counter_clockwise": 1,
            "outward_left": 1,
            "outward_right": 1,
            "outward_from_peak": 1,
            "inward": 2,
            "inward_to_peak": 2
        }
        
        cost = base_costs.get(move_type, 0)
        
        # Ladder reduces inward moves to 1 MP
        if has_ladder and move_type in ["inward", "inward_to_peak"]:
            cost = 1
            
        return cost
    
    def parse_path(self, path_str: str) -> List[Dict[str, Any]]:
        """
        Parse pipe-delimited path string into actions.
        Returns list of actions: {'type': 'move'/'collect'/'clear', 'tile': str, 'item': str}
        """
        if not path_str:
            raise ValueError("Empty path")
        
        actions = []
        elements = path_str.split("|")
        
        for element in elements:
            element = element.strip()
            
            if ":" in element:
                if element.startswith("clear:"):
                    # Dynamite usage: clear:TILE
                    target_tile = element[6:]  # Remove "clear:"
                    actions.append({"type": "clear", "tile": target_tile})
                else:
                    # Item collection: TILE:item_name
                    tile, item = element.split(":", 1)
                    actions.append({"type": "collect", "tile": tile, "item": item})
            else:
                # Regular movement: TILE
                actions.append({"type": "move", "tile": element})
        
        return actions
    
    def validate_path(self, path_str: str, scenario_config: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        Validate a complete path and calculate total MP.
        Returns (is_valid, error_message, total_mp)
        """
        try:
            actions = self.parse_path(path_str)
        except Exception as e:
            return False, f"Path parsing error: {str(e)}", 0
        
        # Initialize game state
        blocked_tiles = [tile_info["tile"] for tile_info in scenario_config.get("blocked", [])]
        collectibles = {item["type"]: item["location"] for item in scenario_config.get("collectibles", [])}
        game_state = GameState(blocked_tiles, collectibles)
        
        total_mp = 0
        current_position = None
        
        for i, action in enumerate(actions):
            if action["type"] == "move":
                tile = action["tile"]
                
                # Check if tile is blocked
                if tile in game_state.blocked_tiles:
                    return False, f"Cannot move to blocked tile {tile} at step {i+1}", total_mp
                
                # First move - validate starting position
                if current_position is None:
                    # Must start from E-level tile
                    try:
                        level, _ = self.parse_tile(tile)
                        if level != "E":
                            return False, f"Must start from E-level tile, not {tile}", total_mp
                    except ValueError:
                        return False, f"Invalid starting tile: {tile}", total_mp
                    
                    current_position = tile
                    continue
                
                # Validate move
                is_valid, move_type, base_cost = self.is_valid_move(current_position, tile)
                if not is_valid:
                    return False, f"Invalid move from {current_position} to {tile} at step {i+1}", total_mp
                
                # Calculate MP cost
                mp_cost = self.calculate_mp_cost(move_type, game_state.has_ladder)
                total_mp += mp_cost
                current_position = tile
                
            elif action["type"] == "collect":
                tile = action["tile"]
                item = action["item"]
                
                # Must be at the tile to collect
                if current_position != tile:
                    return False, f"Cannot collect {item} from {tile} - not at that position (currently at {current_position})", total_mp
                
                # Validate item exists at location
                collected_item = game_state.collect_item(tile)
                if collected_item != item:
                    return False, f"No {item} available at {tile}", total_mp
                
            elif action["type"] == "clear":
                target_tile = action["tile"]
                
                # Must have dynamite and target must be blocked
                if not game_state.use_dynamite(target_tile):
                    if "dynamite" not in game_state.collected_items:
                        return False, f"Cannot clear {target_tile} - no dynamite collected", total_mp
                    elif game_state.dynamite_used:
                        return False, f"Cannot clear {target_tile} - dynamite already used", total_mp
                    else:
                        return False, f"Cannot clear {target_tile} - tile not blocked", total_mp
        
        # Check if path ends at A1
        if current_position != "A1":
            return False, f"Path must end at A1, ended at {current_position}", total_mp
        
        # Check if key was collected
        if not game_state.has_key:
            return False, "Must collect key before reaching A1", total_mp
        
        return True, "Path is valid", total_mp


def validate_puzzle_solution(path_str: str, scenario_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main validation function for the benchmark.
    Returns validation result with details.
    """
    validator = GameValidator()
    is_valid, message, total_mp = validator.validate_path(path_str, scenario_config)
    
    optimal_mp = scenario_config.get("solution", {}).get("optimal_mp", None)
    is_optimal = optimal_mp is not None and total_mp == optimal_mp if is_valid else False
    
    return {
        "is_valid": is_valid,
        "message": message,
        "total_mp": total_mp,
        "optimal_mp": optimal_mp,
        "is_optimal": is_optimal
    }