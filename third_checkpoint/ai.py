# ai.py
import pygame
import math
from game_logic import apply_move, get_possible_moves, is_terminal, evaluate

# Helper function to create a unique hash for the game state
def hash_state(state):
    edge_tuples = tuple(sorted((edge, owner) for edge, owner in state['edges'].items()))
    return hash(edge_tuples)

# Order moves to improve alpha-beta pruning

def order_moves(state, moves, maximizing_player):
    move_scores = []
    for move in moves:
        score = 0
        for cell in state['edge_cells'][move]:
            if state['cells'][cell] == -1:
                edges_drawn = sum(1 for edge in state['cell_edges'][cell] if edge == move or state['edges'][edge] != -1)
                if edges_drawn == 6:
                    score += 100
                elif edges_drawn == 5:
                    score += 50
        move_scores.append((move, score))

    reverse = maximizing_player
    return [m for m, _ in sorted(move_scores, key=lambda x: x[1], reverse=reverse)]

# Minimax with alpha-beta pruning and transposition table

def minimax(state, depth, alpha, beta, maximizingPlayer, transposition_table=None):
    if transposition_table is None:
        transposition_table = {}

    state_hash = hash_state(state)
    if state_hash in transposition_table and transposition_table[state_hash]['depth'] >= depth:
        cached = transposition_table[state_hash]
        return cached['value'], cached['move']

    if depth == 0 or is_terminal(state):
        value = evaluate(state)
        transposition_table[state_hash] = {'value': value, 'move': None, 'depth': depth}
        return value, None

    possible_moves = get_possible_moves(state)
    ordered_moves = order_moves(state, possible_moves, maximizingPlayer)

    best_move = None
    if maximizingPlayer:
        maxEval = -math.inf
        for move in ordered_moves:
            new_state, extra_turn = apply_move(state, move, 1)
            if new_state['last_move']:
                for cell in new_state['edge_cells'][new_state['last_move']]:
                    if cell in new_state['claimed_items']:
                        item = new_state['claimed_items'][cell]
                        if item == "compass":
                            message = "🔄 Compass of Portals activated!"
                            message_timer = pygame.time.get_ticks()
                        elif item == "gauntlet":
                            message = "🧤 Shadow Gauntlet: You stole points!"
                            message_timer = pygame.time.get_ticks()
                        elif item == "hourglass":
                            message = "⏳ Hourglass: Extra turn granted!"
                            message_timer = pygame.time.get_ticks()

            score, _ = minimax(new_state, depth - 1, alpha, beta, True if extra_turn else False, transposition_table)
            if score > maxEval:
                maxEval = score
                best_move = move
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        transposition_table[state_hash] = {'value': maxEval, 'move': best_move, 'depth': depth}
        return maxEval, best_move
    else:
        minEval = math.inf
        for move in ordered_moves:
            new_state, extra_turn = apply_move(state, move, 0)
            if new_state['last_move']:
                for cell in new_state['edge_cells'][new_state['last_move']]:
                    if cell in new_state['claimed_items']:
                        item = new_state['claimed_items'][cell]
                        if item == "compass":
                            message = "🔄 Compass of Portals activated!"
                            message_timer = pygame.time.get_ticks()
                        elif item == "gauntlet":
                            message = "🧤 Shadow Gauntlet: You stole points!"
                            message_timer = pygame.time.get_ticks()
                        elif item == "hourglass":
                            message = "⏳ Hourglass: Extra turn granted!"
                            message_timer = pygame.time.get_ticks()

            score, _ = minimax(new_state, depth - 1, alpha, beta, False if extra_turn else True, transposition_table)
            if score < minEval:
                minEval = score
                best_move = move
            beta = min(beta, score)
            if beta <= alpha:
                break
        transposition_table[state_hash] = {'value': minEval, 'move': best_move, 'depth': depth}
        return minEval, best_move
