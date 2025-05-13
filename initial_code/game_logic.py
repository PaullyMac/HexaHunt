# game_logic.py

import math
import copy
import random

# Constants
TOLERANCE = 10

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
    
    offset_x, offset_y = 0, 0  # Will be calculated
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

    all_x, all_y = zip(*[v for poly in temp_vertices.values() for v in poly])
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    board_width = max_x - min_x
    board_height = max_y - min_y

    offset_x = -min_x + 50 * scale
    offset_y = -min_y + 50 * scale

    state = {
        'cells': {},
        'edges': {},
        'cell_edges': {},
        'edge_cells': {},
        'cell_vertices': {},
        'turn': 0,
        'score': [0, 0],
        'last_move': None,
        'treasures': {},      # cell → treasure type
        'artifacts': {},      # cell → artifact type
        'claimed_items': {},  # cell → revealed item

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

    return state

# Move Logic

def get_possible_moves(state):
    return [edge for edge, owner in state['edges'].items() if owner == -1]

def apply_move(state, move, player):
    new_state = copy.deepcopy(state)
    extra_turn = False

    if new_state['edges'][move] != -1:
        print(f"Invalid move: {move} already taken.")
        return new_state, False

    new_state['edges'][move] = player
    new_state['last_move'] = move

    for cell in new_state['edge_cells'][move]:
        if new_state['cells'][cell] == -1:
            if all(new_state['edges'][e] != -1 for e in new_state['cell_edges'][cell]):
                new_state['cells'][cell] = player
                new_state['score'][player] += 1
                extra_turn = True

    if not extra_turn:
        new_state['turn'] = 1 - player

    return new_state, extra_turn

def is_terminal(state):
    return all(owner != -1 for owner in state['edges'].values())

def evaluate(state):
    return state['score'][1] - state['score'][0]
