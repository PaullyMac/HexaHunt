# game_logic.py

import math
import copy
import random
import pygame  # Add this import

# Constants
TOLERANCE = 10
TREASURES = {
    'copper': 1,
    'silver': 3,
    'gold': 5,
    'platinum': 8,
    'diamond': 8,
}
ARTIFACTS = ['hourglass', 'gauntlet', 'compass']

# Game State Initialization

def polygon_vertices(center, size):
    cx, cy = center
    return [
        (round(cx + size * math.cos(math.radians(60 * i - 30))),
         round(cy + size * math.sin(math.radians(60 * i - 30))))
        for i in range(6)
    ]

def normalize_edge(v1, v2):
    return tuple(sorted([v1, v2]))

def init_state(board_radius, hex_size, scale):
    # Get current window dimensions
    current_width = pygame.display.get_surface().get_width()
    current_height = pygame.display.get_surface().get_height()
    
    current_hex_size = hex_size * scale

    temp_vertices = {}
    valid_cells = []
    for q in range(-board_radius, board_radius + 1):
        for r in range(-board_radius, board_radius + 1):
            s = -q - r
            if max(abs(q), abs(r), abs(s)) <= board_radius:
                valid_cells.append((q, r))
                cx = current_hex_size * math.sqrt(3) * (q + r / 2)
                cy = current_hex_size * 3 / 2 * r
                temp_vertices[(q, r)] = polygon_vertices((cx, cy), current_hex_size)

    # Calculate board bounds
    all_x, all_y = zip(*[v for poly in temp_vertices.values() for v in poly])
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    board_width = max_x - min_x
    board_height = max_y - min_y

    # Calculate offsets to center the board in the current window
    # Add margins for UI elements
    margin_top = 80 * scale  # Space for logo at top
    margin_bottom = 60 * scale  # Space for scores at bottom
    margin_sides = 20 * scale  # Space for buttons on sides
    
    # Calculate available space
    available_width = current_width - (2 * margin_sides)
    available_height = current_height - margin_top - margin_bottom
    
    # Center the board in the available space
    offset_x = margin_sides + (available_width - board_width) / 2 - min_x
    offset_y = margin_top + (available_height - board_height) / 2 - min_y

    state = {
        'cells': {},
        'edges': {},
        'cell_edges': {},
        'edge_cells': {},
        'cell_vertices': {},
        'turn': 0,
        'score': [0, 0],
        'last_move': None,
        'treasures': {},
        'artifacts': {},
        'claimed_items': {},
        'gauntlet_available': {0: False, 1: False},
        'gauntlet_timer':     {0: 0,     1: 0},
        'gauntlet_cell':      {0: None,  1: None},
        'last_treasure_value': {0: 0, 1: 0},
        'compass_available': {0: False, 1: False},
        'compass_cell': {0: None, 1: None},
    }

    for cell in valid_cells:
        q, r = cell
        cx = current_hex_size * math.sqrt(3) * (q + r / 2) + offset_x
        cy = current_hex_size * 3 / 2 * r + offset_y
        center = (cx, cy)
        vertices = polygon_vertices(center, current_hex_size)
        state['cells'][cell] = -1
        state['cell_vertices'][cell] = vertices

        cell_edge_list = []
        for i in range(6):
            v1 = vertices[i]
            v2 = vertices[(i + 1) % 6]
            edge = normalize_edge(v1, v2)
            cell_edge_list.append(edge)
            if edge not in state['edges']:
                state['edges'][edge] = -1
                state['edge_cells'][edge] = []
            if cell not in state['edge_cells'][edge]:
                state['edge_cells'][edge].append(cell)
        state['cell_edges'][cell] = cell_edge_list

    # Assign treasures and artifacts randomly
    shuffled = valid_cells.copy()
    random.shuffle(shuffled)
    total_cells = len(valid_cells)
    treasure_count = int(total_cells * 0.6)
    artifact_count = int(total_cells * 0.1)

    for cell in shuffled[:treasure_count]:
        state['treasures'][cell] = random.choice(list(TREASURES.keys()))

    for cell in shuffled[treasure_count:treasure_count + artifact_count]:
        state['artifacts'][cell] = random.choice(ARTIFACTS)

    return state

# Move Logic

def get_possible_moves(state):
    return [edge for edge, owner in state['edges'].items() if owner == -1]

def apply_move(state, move, player):
    """Apply a move and manage artifacts/tracking."""
    new_state = copy.deepcopy(state)
    # Ensure tracking dicts exist
    new_state.setdefault('gauntlet_available', {0: False, 1: False})
    new_state.setdefault('gauntlet_timer',     {0: 0,     1: 0})
    new_state.setdefault('gauntlet_cell',      {0: None,  1: None})
    new_state.setdefault('hourglass_bonus',    {0: 0,     1: 0})

    new_state.setdefault('last_treasure_value', {0: 0, 1: 0})
    new_state.setdefault('claimed_items', {})
    # Decrement gauntlet lifespan if held
    if new_state['gauntlet_available'][player] and new_state['gauntlet_timer'][player] > 0:
        new_state['gauntlet_timer'][player] -= 1
        print(f"DEBUG: Gauntlet turns left for player {player}: {new_state['gauntlet_timer'][player]}")
        if new_state['gauntlet_timer'][player] == 0:
            # Remove expired gauntlet
            cell0 = new_state['gauntlet_cell'][player]
            new_state['artifacts'].pop(cell0, None)
            new_state['claimed_items'].pop(cell0, None)
            new_state['gauntlet_available'][player] = False
            new_state['gauntlet_cell'][player] = None
            print(f"DEBUG: Gauntlet expired for player {player}")

    # Mark the edge
    new_state['edges'][move] = player
    new_state['last_move'] = move 
    extra_turn = False
    # Check each adjacent cell for completion
    for cell in new_state['edge_cells'][move]:
        if new_state['cells'][cell] == -1 and all(new_state['edges'][e] != -1 for e in new_state['cell_edges'][cell]):
            new_state['cells'][cell] = player
            new_state['score'][player] += 1  # <--- ADD THIS LINE to award 1 base point
            extra_turn = True
            print(f"DEBUG: Player {player} completed cell {cell}")
            # Treasure logic...
            if cell in new_state.get('treasures', {}):
                t = new_state['treasures'][cell]
                v = TREASURES[t]
                new_state['score'][player] += v
                new_state['claimed_items'][cell] = t
                new_state['last_treasure_value'][player] = v
                print(f"DEBUG: Treasure '{t}' (value {v}) claimed at {cell}")
            # Artifact logic
            if cell in new_state.get('artifacts', {}):
                a = new_state['artifacts'][cell]
                new_state['claimed_items'][cell] = a
                print(f"DEBUG: Artifact '{a}' claimed at {cell}")
                if a == 'hourglass':
                    # Give original extra turn and one bonus
                    new_state['hourglass_bonus'][player] += 1
                    print(f"DEBUG: Hourglass bonus granted for player {player}")
                elif a == 'gauntlet':
                    new_state['gauntlet_available'][player] = True
                    new_state['gauntlet_timer'][player] = 5
                    new_state['gauntlet_cell'][player] = cell
                    new_state['artifacts'].pop(cell, None)
                    print(f"DEBUG: Gauntlet picked up at {cell}, lifespan=5")
                elif a == 'compass':
                    new_state['compass_available'][player] = True
                    new_state['compass_cell'][player] = cell
                    print(f"DEBUG: Compass now available for player {player}")

    # AFTER checking for completions, we check if we need to spend a bonus turn.
    # We only spend a bonus if we DIDN'T already earn a standard extra turn on this move.
    if not extra_turn and new_state['hourglass_bonus'][player] > 0:
        extra_turn = True  # Grant an extra turn by cashing in the bonus.
        new_state['hourglass_bonus'][player] -= 1
        print(f"DEBUG: Using hourglass bonus turn. Remaining bonuses: {new_state['hourglass_bonus'][player]}")

    # Switch turn if no extra_turn
    if not extra_turn:
        new_state['turn'] = 1 - player
        print(f"DEBUG: Next turn: player {new_state['turn']}")

    return new_state, extra_turn


def is_terminal(state):
    return all(owner != -1 for owner in state['edges'].values())

def evaluate(state):
    return state['score'][1] - state['score'][0]

# Add helper to activate compass
def use_compass(state, player, target_cell):
    print(f"DEBUG: Player {player} attempts compass on {target_cell}")
    # need a compass and a recorded source cell
    if not state.get('compass_available', {}).get(player, False) or not state.get('compass_cell', {}).get(player):
        print("DEBUG: Compass not available or source missing")
        return state
    source = state['compass_cell'][player]
    opponent = 1 - player
    # only swap ownership and scores, keep treasures in place
    if state['cells'].get(target_cell) != opponent:
        print("DEBUG: Target cell not owned by opponent")
        return state
    print(f"DEBUG: Swapping ownership of cell {source} and {target_cell}")
    # swap ownership
    state['cells'][source], state['cells'][target_cell] = opponent, player
    # remove compass artifact so icon disappears
    if source in state.get('artifacts', {}):
        del state['artifacts'][source]
    if source in state.get('claimed_items', {}):
        del state['claimed_items'][source]
    # adjust scores: deduct source treasure value from player, add to opponent
    if source in state.get('treasures', {}):
        t = state['treasures'][source]; v = TREASURES[t]
        state['score'][player] -= v; state['score'][opponent] += v
        print(f"DEBUG: Player {player} loses {v} from source treasure")
    # deduct target treasure from opponent, add to player
    if target_cell in state.get('treasures', {}):
        t = state['treasures'][target_cell]; v = TREASURES[t]
        state['score'][opponent] -= v; state['score'][player] += v
        print(f"DEBUG: Player {player} gains {v} from target treasure")
    # clear compass availability
    state['compass_available'][player] = False
    state['compass_cell'][player] = None
    print(f"DEBUG: Scores after compass: {state['score']}")
    return state


def use_gauntlet(state, player, amount=None):
    opponent = 1 - player
    if not state['gauntlet_available'][player]:
        print("DEBUG: No gauntlet to use")
        return state
    last_val = state['last_treasure_value'][opponent]
    if last_val <= 0:
        print("DEBUG: Nothing to steal")
        return state
    steal = amount if amount is not None else last_val
    steal = min(steal, last_val, state['score'][opponent])
    print(f"DEBUG: Stealing {steal} from player {opponent}")
    state['score'][opponent] -= steal
    state['score'][player]   += steal
    # consume and remove PNG
    cell0 = state['gauntlet_cell'][player]
    state['artifacts'].pop(cell0, None)
    state['claimed_items'].pop(cell0, None)
    state['gauntlet_available'][player] = False
    state['gauntlet_timer'][player]     = 0
    state['gauntlet_cell'][player]      = None
    print("DEBUG: Gauntlet consumed")
    return state