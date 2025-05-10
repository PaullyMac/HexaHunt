import pygame
import sys
import math
import copy
import time  # Add this import for time measurement
import random
from pygame import gfxdraw
import webbrowser

# ----- Constants & Board Configuration -----
DEFAULT_WIDTH, DEFAULT_HEIGHT = 800, 800  # Increased default size
CURRENT_WIDTH, CURRENT_HEIGHT = DEFAULT_WIDTH, DEFAULT_HEIGHT
TOLERANCE = 10                   # Pixel tolerance for clicking on an edge
DEPTH = 3                        # Depth for the minimax search
BOARD_RADIUS = 2                 # Board "radius" for hex board: cells with max(|q|,|r|,|s|)<=3
HEX_SIZE = 40                    # Size of each hexagon
MARGIN = 50                      # Margin from window edge to the board
SPACING = 100                    # Distance between adjacent dots

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)   # Human color
BLUE  = (0, 0, 255)   # AI color
GRAY  = (200, 200, 200)
LIGHT_GREEN = (200, 255, 200)  # For cache hits
LIGHT_YELLOW = (255, 255, 200) # For newly evaluated positions
YELLOW = (255, 255, 0)  # Bright yellow for last move highlight

# Menu colors
MENU_BG = (240, 240, 255)
BUTTON_COLOR = (180, 180, 250)
BUTTON_HOVER = (160, 160, 230)
BUTTON_TEXT = BLACK

# Add stats tracking for visualization
AI_STATS = {
    'cache_hits': 0,
    'positions_evaluated': 0,
    'thinking_time': 0.0,
    'visualization_edges': {},  # To track which edges to highlight
    'total_cache_size': 0,
    'show_stats': False  # Flag to control stats visibility
}

# ----- Updated Colors for Enhanced UI -----
# Replace your existing color definitions or add these new ones
MENU_BG_TOP = (229, 232, 247)  # #E5E8F7 (light lavender)
MENU_BG_BOTTOM = (200, 209, 244)  # #C8D1F4 (pale periwinkle)
BUTTON_COLOR = (143, 168, 246)  # #8FA8F6
BUTTON_HOVER = (111, 140, 224)  # #6F8CE0
TITLE_TEXT = (46, 48, 87)  # #2E3057 (dark indigo)
BODY_TEXT = (51, 58, 90)  # #333A5A
HEX_COLOR = (255, 255, 255, 51)  # #FFFFFF33 (white at 20% opacity)

# Track animation states
UI_ANIMATION = {
    'transition_alpha': 255,
    'target_screen': None,
    'current_screen': 'OPENING_SCREEN',
    'transition_active': False,
    'button_hover_state': {},  # For button hover animations
    'hexagons': []
}

# ----- Scale Calculation Functions -----
def get_scale_factor():
    """Calculate the scale factor based on current window size vs default size"""
    x_scale = CURRENT_WIDTH / DEFAULT_WIDTH
    y_scale = CURRENT_HEIGHT / DEFAULT_HEIGHT
    # Use the smaller scale to ensure everything fits
    return min(x_scale, y_scale)

def scale_point(point, scale_factor=None):
    """Scale a point based on the current window size"""
    if scale_factor is None:
        scale_factor = get_scale_factor()
    x, y = point
    scaled_x = x * scale_factor
    scaled_y = y * scale_factor
    return (scaled_x, scaled_y)

def scale_hex_size():
    """Scale the hexagon size based on the window size"""
    return HEX_SIZE * get_scale_factor()

# ----- Hex Geometry Helper Functions (Updated for scaling) -----
def axial_to_pixel(q, r, offset_x=0, offset_y=0):
    """
    Convert axial hex coordinates (q, r) to pixel coordinates
    using the pointy-topped layout, and add an additional offset.
    """
    scale = get_scale_factor()
    x = scale_hex_size() * math.sqrt(3) * (q + r/2) + offset_x * scale
    y = scale_hex_size() * 3/2 * r + offset_y * scale
    return (x, y)

def polygon_vertices(center, size):
    """
    Compute the 6 vertices for a pointy-topped hexagon given its center.
    """
    cx, cy = center
    vertices = []
    for i in range(6):
        angle_deg = 60 * i - 30  # so the top is a point
        angle_rad = math.radians(angle_deg)
        vx = cx + size * math.cos(angle_rad)
        vy = cy + size * math.sin(angle_rad)
        vertices.append((round(vx), round(vy)))
    return vertices

def normalize_edge(v1, v2):
    """
    Order the two endpoints of an edge so that every edge has a unique representation.
    """
    return tuple(sorted([v1, v2]))

# ----- Game State Setup for Hexagonal Board -----
def init_state(board_radius=None):
    """
    Build the hexagonal board state using axial coordinates.
    This version computes a bounding box for the board (with no offset) and then
    calculates an additional offset to center the board in the window.
    """
    global BOARD_RADIUS
    if board_radius is not None:
        BOARD_RADIUS = board_radius
        
    # First pass: compute vertices for each valid hex cell with no offset.
    temp_vertices = {}
    valid_cells = []
    for q in range(-BOARD_RADIUS, BOARD_RADIUS+1):
        for r in range(-BOARD_RADIUS, BOARD_RADIUS+1):
            s = -q - r
            if max(abs(q), abs(r), abs(s)) <= BOARD_RADIUS:
                valid_cells.append((q, r))
                center = axial_to_pixel(q, r, 0, 0)
                vertices = polygon_vertices(center, HEX_SIZE)
                temp_vertices[(q, r)] = vertices

    # Compute bounding box (min/max x and y) from all vertices.
    all_x = []
    all_y = []
    for vertices in temp_vertices.values():
        for (x, y) in vertices:
            all_x.append(x)
            all_y.append(y)
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    board_width = max_x - min_x
    board_height = max_y - min_y

    # Compute offsets to center the board in the window.
    # Calculate the available area, accounting for the top UI elements (buttons)
    top_ui_height = 70  # Approximate height for top UI elements
    WIDTH = CURRENT_WIDTH - 2 * MARGIN
    HEIGHT = CURRENT_HEIGHT - 2 * MARGIN - top_ui_height
    
    # Calculate offsets that will center the board in the available space
    offset_x = (WIDTH - board_width) / 2 + MARGIN - min_x
    offset_y = (HEIGHT - board_height) / 2 + MARGIN + top_ui_height - min_y

    # Build final state using the computed offset.
    state = {}
    state['cells'] = {}
    state['edges'] = {}
    state['cell_edges'] = {}
    state['edge_cells'] = {}
    state['cell_vertices'] = {}

    for cell in valid_cells:
        q, r = cell
        center = axial_to_pixel(q, r, offset_x, offset_y)
        vertices = polygon_vertices(center, HEX_SIZE)
        state['cells'][(q, r)] = -1  # Unclaimed
        state['cell_vertices'][(q, r)] = vertices
        cell_edge_list = []
        for i in range(6):
            v1 = vertices[i]
            v2 = vertices[(i + 1) % 6]
            edge = normalize_edge(v1, v2)
            cell_edge_list.append(edge)
            # Register the edge if not present and link the cell to the edge.
            if edge not in state['edges']:
                state['edges'][edge] = -1
                state['edge_cells'][edge] = []
            if (q, r) not in state['edge_cells'][edge]:
                state['edge_cells'][edge].append((q, r))
        state['cell_edges'][(q, r)] = cell_edge_list

    state['turn'] = 0  # Human starts
    state['score'] = [0, 0]
    state['last_move'] = None  # Initialize last_move to None
    return state

# ----- Move Utilities -----
def get_possible_moves(state):
    """Return a list of all undrawn edges."""
    moves = []
    for edge, owner in state['edges'].items():
        if owner == -1:
            moves.append(edge)
    return moves

def apply_move(state, move, player):
    """
    Apply the move (drawing an edge) by the given player.
    For each cell adjacent to the move, check if all 6 edges have been drawn.
    If so, mark the cell with the player's number and update score.
    Returns the new state and a flag for extra turn.
    """
    new_state = copy.deepcopy(state)
    extra_turn = False
    
    # First check if the move is valid (edge not already filled)
    if new_state['edges'][move] != -1:
        print(f"Warning: Attempting to play on already filled edge {move}")
        return new_state, False
        
    new_state['edges'][move] = player
    
    # Store the last move in the state
    new_state['last_move'] = move
    
    # Check each cell that uses this edge.
    for cell in new_state['edge_cells'][move]:
        if new_state['cells'][cell] == -1:  # still unclaimed
            completed = True
            for edge in new_state['cell_edges'][cell]:
                if new_state['edges'][edge] == -1:
                    completed = False
                    break
            if completed:
                new_state['cells'][cell] = player
                new_state['score'][player] += 1
                extra_turn = True
                print(f"Player {player} scored! New score: {new_state['score']}")  # Debug line
                
    if not extra_turn:
        new_state['turn'] = 1 - player
    return new_state, extra_turn

def is_terminal(state):
    """The game is over if there are no moves left."""
    return len(get_possible_moves(state)) == 0

def evaluate(state):
    """
    Evaluation function for minimax.
    Returns (AI score - Human score).
    """
    return state['score'][1] - state['score'][0]

# Add this function to create a unique hash for a game state
def hash_state(state):
    """Create a hash representation of the board state for the transposition table"""
    # Use a tuple of sorted (edge, owner) pairs as the hash
    edge_tuples = tuple(sorted((edge, owner) for edge, owner in state['edges'].items()))
    return hash(edge_tuples)

# Modified minimax with transposition table
def minimax(state, depth, alpha, beta, maximizingPlayer, transposition_table=None):
    """Minimax algorithm with alpha-beta pruning and transposition table"""
    if transposition_table is None:
        transposition_table = {}
    
    # Generate a hash for the current state
    state_hash = hash_state(state)
    
    # Check if this state is already in our table at sufficient depth
    if state_hash in transposition_table and transposition_table[state_hash]['depth'] >= depth:
        AI_STATS['cache_hits'] += 1
        return transposition_table[state_hash]['value'], transposition_table[state_hash]['move']
    
    AI_STATS['positions_evaluated'] += 1
    
    if depth == 0 or is_terminal(state):
        value = evaluate(state)
        transposition_table[state_hash] = {'value': value, 'move': None, 'depth': depth}
        AI_STATS['total_cache_size'] = len(transposition_table)
        return value, None

    possible_moves = get_possible_moves(state)
    
    # Safety check - if no valid moves, return current evaluation
    if not possible_moves:
        value = evaluate(state)
        transposition_table[state_hash] = {'value': value, 'move': None, 'depth': depth}
        AI_STATS['total_cache_size'] = len(transposition_table)
        return value, None
    
    ordered_moves = order_moves(state, possible_moves, maximizingPlayer)
    
    best_move = None
    if maximizingPlayer:
        maxEval = -math.inf
        for move in ordered_moves:
            # Double-check the move is valid
            if state['edges'][move] != -1:
                continue
                
            new_state, extra_turn = apply_move(state, move, 1)
            if extra_turn:
                eval_score, _ = minimax(new_state, depth - 1, alpha, beta, True, transposition_table)
            else:
                eval_score, _ = minimax(new_state, depth - 1, alpha, beta, False, transposition_table)
            if eval_score > maxEval:
                maxEval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        
        # Safety check - if no best move was found, pick the first valid move
        if best_move is None and ordered_moves:
            best_move = ordered_moves[0]
            
        transposition_table[state_hash] = {'value': maxEval, 'move': best_move, 'depth': depth}
        AI_STATS['total_cache_size'] = len(transposition_table)
        return maxEval, best_move
    else:
        minEval = math.inf
        for move in ordered_moves:
            # Double-check the move is valid
            if state['edges'][move] != -1:
                continue
                
            new_state, extra_turn = apply_move(state, move, 0)
            if extra_turn:
                eval_score, _ = minimax(new_state, depth - 1, alpha, beta, False, transposition_table)
            else:
                eval_score, _ = minimax(new_state, depth - 1, alpha, beta, True, transposition_table)
            if eval_score < minEval:
                minEval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        
        # Safety check - if no best move was found, pick the first valid move
        if best_move is None and ordered_moves:
            best_move = ordered_moves[0]
            
        transposition_table[state_hash] = {'value': minEval, 'move': best_move, 'depth': depth}
        AI_STATS['total_cache_size'] = len(transposition_table)
        return minEval, best_move

# Helper function to order moves - prioritize moves that complete boxes
def order_moves(state, moves, maximizing_player):
    """Order moves to improve alpha-beta pruning efficiency"""
    move_scores = []
    player = 1 if maximizing_player else 0
    
    for move in moves:
        score = 0
        # Check how many edges are already drawn for each affected cell
        for cell in state['edge_cells'][move]:
            if state['cells'][cell] == -1:  # unclaimed cell
                edges_drawn = 0
                for edge in state['cell_edges'][cell]:
                    if edge == move or state['edges'][edge] != -1:
                        edges_drawn += 1
                # Prioritize moves that complete or nearly complete cells
                if edges_drawn == 6:  # Would complete a cell
                    score += 100
                elif edges_drawn == 5:  # One away from completion
                    score += 50
        
        move_scores.append((move, score))
    
    # Sort moves by score (descending for maximizing, ascending for minimizing)
    if maximizing_player:
        return [move for move, score in sorted(move_scores, key=lambda x: -x[1])]
    else:
        return [move for move, score in sorted(move_scores, key=lambda x: x[1])]

# ----- Updated Drawing Function -----
def draw_board(screen, state, font, back_button=None, stats_button=None):
    """
    Render the board with visualization of the AI's thinking process.
    """
    screen.fill(WHITE)
    scale = get_scale_factor()
    scaled_margin = MARGIN * scale
    
    # Fill claimed cells
    for cell, owner in state['cells'].items():
        if owner != -1:
            # Scale the vertices
            vertices = [scale_point(v) for v in state['cell_vertices'][cell]]
            color = RED if owner == 0 else BLUE
            pygame.draw.polygon(screen, color, vertices)
    
    # Draw edges with visualization highlights
    for edge, owner in state['edges'].items():
        # Scale the edge endpoints
        a, b = edge
        scaled_a = scale_point(a)
        scaled_b = scale_point(b)
        
        # Check if this is the last move
        is_last_move = (edge == state.get('last_move'))
        
        if owner != -1:
            # If this is the last move, highlight it in yellow
            if is_last_move:
                color = YELLOW
                width = int(6 * scale)  # Make it slightly wider for emphasis
            else:
                color = RED if owner == 0 else BLUE
                width = int(4 * scale)
        else:
            # Check if this edge is in our visualization dictionary and stats are visible
            if AI_STATS['show_stats'] and edge in AI_STATS['visualization_edges']:
                if AI_STATS['visualization_edges'][edge] == 'cache_hit':
                    color = LIGHT_GREEN  # Cache hit
                    width = int(2 * scale)
                else:
                    color = LIGHT_YELLOW  # Newly evaluated
                    width = int(2 * scale)
            else:
                color = GRAY
                width = max(1, int(1 * scale))
        
        pygame.draw.line(screen, color, scaled_a, scaled_b, width)
    
    # Draw vertices
    drawn_vertices = set()
    for vertices in state['cell_vertices'].values():
        for vertex in vertices:
            scaled_vertex = scale_point(vertex)
            if scaled_vertex not in drawn_vertices:
                pygame.draw.circle(screen, BLACK, scaled_vertex, int(4 * scale))
                drawn_vertices.add(scaled_vertex)
    
    # Draw score text at the bottom - Human on left, AI on right
    human_score_text = font.render(f"Human: {state['score'][0]}", True, BLUE)
    ai_score_text = font.render(f"AI: {state['score'][1]}", True, RED)

    # Place Human score at the left
    screen.blit(human_score_text, (scaled_margin, CURRENT_HEIGHT - scaled_margin))

    # Place AI score at the right side
    ai_score_x = CURRENT_WIDTH - scaled_margin - ai_score_text.get_width()
    screen.blit(ai_score_text, (ai_score_x, CURRENT_HEIGHT - scaled_margin))
    
    # Only draw AI stats if the show_stats flag is True
    if AI_STATS['show_stats']:
        # Draw AI stats - position based on current window size
        stats_x = CURRENT_WIDTH - 200 * scale
        stats_y = scaled_margin + 50 * scale  # Added 50 scaled pixels to move stats down below the button
        line_height = 30 * scale
        
        stats_text = font.render(f"Time: {AI_STATS['thinking_time']:.3f}s", True, BLUE)
        screen.blit(stats_text, (stats_x, stats_y))
        
        cache_text = font.render(f"Cache: {AI_STATS['total_cache_size']} positions", True, BLUE)
        screen.blit(cache_text, (stats_x, stats_y + line_height))
        
        hits_text = font.render(f"Hits: {AI_STATS['cache_hits']}", True, LIGHT_GREEN)
        screen.blit(hits_text, (stats_x, stats_y + line_height * 2))
        
        evals_text = font.render(f"Evals: {AI_STATS['positions_evaluated']}", True, LIGHT_YELLOW)
        screen.blit(evals_text, (stats_x, stats_y + line_height * 3))
        
        # If we have both hits and evaluations, show efficiency
        if AI_STATS['positions_evaluated'] + AI_STATS['cache_hits'] > 0:
            efficiency = AI_STATS['cache_hits'] / (AI_STATS['positions_evaluated'] + AI_STATS['cache_hits']) * 100
            eff_text = font.render(f"Efficiency: {efficiency:.1f}%", True, BLUE)
            screen.blit(eff_text, (stats_x, stats_y + line_height * 4))
        
        # Add legend
        pygame.draw.rect(screen, LIGHT_GREEN, (stats_x - 20 * scale, stats_y + line_height * 5, 15 * scale, 15 * scale))
        legend1 = font.render("Cache hit", True, BLACK)
        screen.blit(legend1, (stats_x, stats_y + line_height * 5))
        
        pygame.draw.rect(screen, LIGHT_YELLOW, (stats_x - 20 * scale, stats_y + line_height * 6, 15 * scale, 15 * scale))
        legend2 = font.render("New evaluation", True, BLACK)
        screen.blit(legend2, (stats_x, stats_y + line_height * 6))
    
    # Draw back button if provided
    if back_button:
        draw_button(screen, back_button, is_button_hovered(back_button, pygame.mouse.get_pos()))
    
    # Draw stats button if provided
    if stats_button:
        draw_button(screen, stats_button, is_button_hovered(stats_button, pygame.mouse.get_pos()))
    
    pygame.display.flip()

def point_line_distance(p, a, b):
    """
    Compute the minimum distance from point p to the line segment defined by endpoints a and b.
    """
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0, min(1, t))
    proj_x = ax + t * dx
    proj_y = ay + t * dy
    return math.hypot(px - proj_x, py - proj_y)

# Updated click detection for resized windows
def get_clicked_edge(pos, state):
    """
    Given the mouse position, determine if it is close to an undrawn edge.
    Returns the edge if found, otherwise None.
    """
    x, y = pos
    scale = get_scale_factor()
    inverse_scale = 1 / scale
    
    # Convert mouse position to original coordinate system
    original_x, original_y = x * inverse_scale, y * inverse_scale
    
    for edge, owner in state['edges'].items():
        if owner == -1:
            a, b = edge
            if point_line_distance((original_x, original_y), a, b) < TOLERANCE:
                return edge
    return None

# ----- UI Helper Functions -----
def create_button(text, x, y, width, height, font, id=None):
    """Create a button with the given text and position"""
    button_id = id if id else text  # Use provided ID or default to text
    
    text_surface = font.render(text, True, TITLE_TEXT)
    text_rect = text_surface.get_rect()
    text_rect.center = (x + width // 2, y + height // 2)
    button_rect = pygame.Rect(x, y, width, height)
    
    # Initialize hover animation state if not exists
    if button_id not in UI_ANIMATION['button_hover_state']:
        UI_ANIMATION['button_hover_state'][button_id] = 0.0
    
    return {
        'rect': button_rect,
        'text': text,
        'text_surface': text_surface,
        'text_rect': text_rect,
        'id': button_id
    }

def draw_button(screen, button, is_hover=False):
    """Draw a button with enhanced styling"""
    button_id = button['id']
    
    # Update hover state with smooth transition
    target_hover = 1.0 if is_hover else 0.0
    current_hover = UI_ANIMATION['button_hover_state'][button_id]
    
    # Smooth transition - move 10% of the way to target each frame
    UI_ANIMATION['button_hover_state'][button_id] = current_hover + (target_hover - current_hover) * 0.2
    hover_factor = UI_ANIMATION['button_hover_state'][button_id]
    
    # Interpolate color based on hover state
    r = int(BUTTON_COLOR[0] * (1 - hover_factor) + BUTTON_HOVER[0] * hover_factor)
    g = int(BUTTON_COLOR[1] * (1 - hover_factor) + BUTTON_HOVER[1] * hover_factor)
    b = int(BUTTON_COLOR[2] * (1 - hover_factor) + BUTTON_HOVER[2] * hover_factor)
    color = (r, g, b)
    
    # Calculate size expansion based on hover (up to 5% larger)
    expansion = 1 + (0.05 * hover_factor)
    expanded_width = int(button['rect'].width * expansion)
    expanded_height = int(button['rect'].height * expansion)
    
    # Center the expanded button
    expanded_x = button['rect'].x - (expanded_width - button['rect'].width) // 2
    expanded_y = button['rect'].y - (expanded_height - button['rect'].height) // 2
    expanded_rect = pygame.Rect(expanded_x, expanded_y, expanded_width, expanded_height)
    
    # Draw button with rounded corners
    pygame.draw.rect(screen, color, expanded_rect, border_radius=15)
    pygame.draw.rect(screen, TITLE_TEXT, expanded_rect, 2, border_radius=15)  # Border
    
    # Create a shadow offset for the text
    shadow_offset = 1 + int(hover_factor * 2)  # More shadow when hovered
    
    # Render text with shadow
    shadow_color = (20, 20, 40, 150)  # Dark blue-ish shadow
    text_with_shadow = render_text_with_shadow(
        button['text'], 
        pygame.font.SysFont(None, int(32 * get_scale_factor())), 
        WHITE,
        shadow_color,
        shadow_offset
    )
    
    # Calculate center position for the text
    text_rect = text_with_shadow.get_rect(center=expanded_rect.center)
    screen.blit(text_with_shadow, text_rect)

def is_button_hovered(button, pos):
    """Check if the mouse is hovering over a button"""
    return button['rect'].collidepoint(pos)

def draw_text_block(screen, text, x, y, font, max_width=None, line_height=None):
    """Draw a multi-line text block on the screen"""
    if line_height is None:
        line_height = font.get_height() + 5
    
    if max_width:
        words = text.split(' ')
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            word_surface = font.render(word + ' ', True, BLACK)
            word_width = word_surface.get_width()
            
            if current_width + word_width > max_width:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
            else:
                current_line.append(word)
                current_width += word_width
        
        if current_line:
            lines.append(' '.join(current_line))
    else:
        lines = text.split('\n')
    
    y_pos = y
    for line in lines:
        text_surface = font.render(line, True, BLACK)
        screen.blit(text_surface, (x, y_pos))
        y_pos += line_height
    
    return y_pos  # Return the y position after the last line

# ----- Menu Drawing Functions -----
def draw_opening_screen(screen, font, button_font, settings, skip_display=False):
    """Draw the enhanced opening/main menu screen"""
    # Draw gradient background
    gradient = create_gradient_surface(CURRENT_WIDTH, CURRENT_HEIGHT, MENU_BG_TOP, MENU_BG_BOTTOM)
    screen.blit(gradient, (0, 0))
    
    # Draw animated hexagons
    draw_hexagons(screen)
    
    # Title with shadow
    title_font = pygame.font.SysFont(None, int(70 * get_scale_factor()))
    subtitle_font = pygame.font.SysFont(None, int(30 * get_scale_factor()))
    
    title = render_text_with_shadow("HexaHunt", title_font, TITLE_TEXT)
    subtitle = render_text_with_shadow("A Treasure Hunting Game using Minimax Algorithm", 
                                     subtitle_font, BODY_TEXT)
    
    title_rect = title.get_rect(center=(CURRENT_WIDTH//2, CURRENT_HEIGHT//4))
    subtitle_rect = subtitle.get_rect(center=(CURRENT_WIDTH//2, CURRENT_HEIGHT//4 + 60 * get_scale_factor()))
    
    screen.blit(title, title_rect)
    screen.blit(subtitle, subtitle_rect)
    
    # Draw buttons
    for idx, button in enumerate(settings['buttons']['opening']):
        draw_button(screen, button, is_button_hovered(button, pygame.mouse.get_pos()))
    
    # Update the display unless we're in a transition
    if not skip_display:
        pygame.display.flip()

def draw_how_to_play_screen(screen, font, settings, skip_display=False):
    """Draw the enhanced how to play screen with scrolling"""
    # Draw gradient background
    gradient = create_gradient_surface(CURRENT_WIDTH, CURRENT_HEIGHT, MENU_BG_TOP, MENU_BG_BOTTOM)
    screen.blit(gradient, (0, 0))
    
    # Draw animated hexagons
    draw_hexagons(screen)
    
    # Initialize scroll position if not exists
    if 'how_to_play_scroll' not in settings:
        settings['how_to_play_scroll'] = 0
    
    # Get current scroll position
    scroll_y = settings['how_to_play_scroll']
    
    # Calculate visible area (with room for back button)
    visible_top = 0
    visible_bottom = CURRENT_HEIGHT - 100 * get_scale_factor()
    
    # Content starting position - moved up since title will be part of scrollable content
    base_y = 50 * get_scale_factor()  # Reduced from 110
    line_height = int(30 * get_scale_factor())
    center_x = CURRENT_WIDTH // 2
    
    # Create a surface to hold content
    content_surface = pygame.Surface((CURRENT_WIDTH, 2000 * get_scale_factor()), pygame.SRCALPHA)
    y_pos = 0  # Starting at 0 for the content surface
    
    # Title with shadow (now part of scrollable content)
    title_font = pygame.font.SysFont(None, int(50 * get_scale_factor()))
    title = render_text_with_shadow("How to Play HexaHunt", title_font, TITLE_TEXT)
    title_rect = title.get_rect(center=(center_x, y_pos + title.get_height()//2))
    content_surface.blit(title, title_rect)
    y_pos += title.get_height() + 20 * get_scale_factor()  # Add spacing after title
    
    # Game mechanics section
    texts = [
        "Game Objective:",
        "Gather the most treasure by completing hexagons on the board.",
        "",
        "Game Mechanics:",
        "• Players take turns drawing lines between dots.",
        "• Completing a hexagon claims it and gives you points.",
        "• When you complete a hexagon, you get an extra turn.",
        "• The human player goes first.",
        ""
    ]
    
    for text in texts:
        # Headers bold, normal text regular
        if ":" in text or text.startswith("•"):
            text_surf = render_text_with_shadow(text, font, TITLE_TEXT)
        else:
            text_surf = render_text_with_shadow(text, font, BODY_TEXT)
        
        # Center align text
        text_rect = text_surf.get_rect(center=(center_x, y_pos + text_surf.get_height()//2))
        content_surface.blit(text_surf, text_rect)
        y_pos += line_height
    
    # Treasures section - center the header
    treasure_title = render_text_with_shadow("Treasures:", font, TITLE_TEXT)
    treasure_title_rect = treasure_title.get_rect(center=(center_x, y_pos + treasure_title.get_height()//2))
    content_surface.blit(treasure_title, treasure_title_rect)
    y_pos += line_height
    
    treasure_info = render_text_with_shadow("In each tile, players find treasures with hidden values revealed only upon claiming the hex.", font, BODY_TEXT)
    treasure_info_rect = treasure_info.get_rect(center=(center_x, y_pos + treasure_info.get_height()//2))
    content_surface.blit(treasure_info, treasure_info_rect)
    y_pos += line_height * 1.2
    
    # Table - FURTHER INCREASED spacing for columns
    table_width = 850 * get_scale_factor()  # Wider table (increased from 700)
    col1_x = center_x - table_width/2
    col2_x = col1_x + 250 * get_scale_factor()  # Increased from 220
    col3_x = col2_x + 400 * get_scale_factor()  # Increased from 350
    
    headers = ["Treasure", "Description", "Points"]
    for i, header in enumerate(headers):
        x_pos = col1_x if i == 0 else (col2_x if i == 1 else col3_x)
        header_surf = render_text_with_shadow(header, font, TITLE_TEXT)
        content_surface.blit(header_surf, (x_pos, y_pos))
    y_pos += line_height
    
    # Draw horizontal line under headers
    pygame.draw.line(content_surface, BODY_TEXT, (col1_x, y_pos - line_height//3), 
                    (col3_x + 80 * get_scale_factor(), y_pos - line_height//3), 2)
    
    # Treasures table data
    treasures = [
        ["Copper Coin", "A simple coin, worn yet still valuable.", "1"],
        ["Silver Relic", "Ancient token with mysterious engravings.", "3"],
        ["Golden Idol", "A small statue fashioned from pure gold.", "5"],
        ["Platinum Crown", "A magnificent royal headpiece.", "8"],
        ["Diamond Scepter", "Rod crowned with rare gemstones.", "8"]
    ]
    
    for treasure in treasures:
        name_surf = render_text_with_shadow(treasure[0], font, BODY_TEXT)
        desc_surf = render_text_with_shadow(treasure[1], font, BODY_TEXT)
        points_surf = render_text_with_shadow(treasure[2], font, BODY_TEXT)
        
        content_surface.blit(name_surf, (col1_x, y_pos))
        content_surface.blit(desc_surf, (col2_x, y_pos))
        content_surface.blit(points_surf, (col3_x, y_pos))
        
        y_pos += line_height
    
    y_pos += line_height * 0.5
    
    # Artifacts section - center the header
    artifact_title = render_text_with_shadow("Artifacts:", font, TITLE_TEXT)
    artifact_title_rect = artifact_title.get_rect(center=(center_x, y_pos + artifact_title.get_height()//2))
    content_surface.blit(artifact_title, artifact_title_rect)
    y_pos += line_height
    
    artifact_info = render_text_with_shadow("Powerful items that grant significant advantages when discovered.", font, BODY_TEXT)
    artifact_info_rect = artifact_info.get_rect(center=(center_x, y_pos + artifact_info.get_height()//2))
    content_surface.blit(artifact_info, artifact_info_rect)
    y_pos += line_height * 1.2
    
    # Table headers - use the same wider spacing for artifact table
    headers = ["Artifact", "Description", "Bonus Effect"]
    for i, header in enumerate(headers):
        x_pos = col1_x if i == 0 else (col2_x if i == 1 else col3_x)
        header_surf = render_text_with_shadow(header, font, TITLE_TEXT)
        content_surface.blit(header_surf, (x_pos, y_pos))
    y_pos += line_height
    
    # Draw horizontal line under headers
    pygame.draw.line(content_surface, BODY_TEXT, (col1_x, y_pos - line_height//3), 
                    (col3_x + 80 * get_scale_factor(), y_pos - line_height//3), 2)
    
    # Artifacts table data
    artifacts = [
        ["Hourglass of Quickening", "Enchanted sands that bend time.", "Extra move"],
        ["Shadow Gauntlet", "Glove that siphons wealth.", "Steal treasure"],
        ["Compass of Portals", "Contains cosmic stardust.", "Swap hex ownership"]
    ]
    
    for artifact in artifacts:
        name_surf = render_text_with_shadow(artifact[0], font, BODY_TEXT)
        desc_surf = render_text_with_shadow(artifact[1], font, BODY_TEXT)
        effect_surf = render_text_with_shadow(artifact[2], font, BODY_TEXT)
        
        content_surface.blit(name_surf, (col1_x, y_pos))
        content_surface.blit(desc_surf, (col2_x, y_pos))
        content_surface.blit(effect_surf, (col3_x, y_pos))
        
        y_pos += line_height
    
    # Game End section - center align
    y_pos += line_height * 0.5
    end_title = render_text_with_shadow("Game End:", font, TITLE_TEXT)
    end_title_rect = end_title.get_rect(center=(center_x, y_pos + end_title.get_height()//2))
    content_surface.blit(end_title, end_title_rect)
    y_pos += line_height
    
    end_text = render_text_with_shadow("The game ends when all possible lines have been drawn.", font, BODY_TEXT)
    end_text_rect = end_text.get_rect(center=(center_x, y_pos + end_text.get_height()//2))
    content_surface.blit(end_text, end_text_rect)
    y_pos += line_height
    
    winner_text = render_text_with_shadow("The player with the highest score wins!", font, BODY_TEXT)
    winner_text_rect = winner_text.get_rect(center=(center_x, y_pos + end_text.get_height()//2))
    content_surface.blit(winner_text, winner_text_rect)
    
    # Calculate total content height
    content_height = y_pos + line_height * 3
    
    # Clamp scroll position
    max_scroll = max(0, content_height - (visible_bottom - base_y))
    settings['how_to_play_scroll'] = max(0, min(scroll_y, max_scroll))
    
    # Draw scrollable content at the right position
    screen.blit(content_surface, (0, base_y - settings['how_to_play_scroll']))
    
    # Removed scroll indicators since mouse scroll works fine
    
    # Back button (fixed position, doesn't scroll)
    back_button = settings['buttons']['how_to_play'][0]
    draw_button(screen, back_button, is_button_hovered(back_button, pygame.mouse.get_pos()))
    
    # Update the display unless we're in a transition
    if not skip_display:
        pygame.display.flip()

def draw_about_screen(screen, font, settings, skip_display=False):
    """Draw the enhanced about screen"""
    # Draw gradient background
    gradient = create_gradient_surface(CURRENT_WIDTH, CURRENT_HEIGHT, MENU_BG_TOP, MENU_BG_BOTTOM)
    screen.blit(gradient, (0, 0))
    
    # Draw animated hexagons
    draw_hexagons(screen)
    
    # Title with shadow
    title_font = pygame.font.SysFont(None, int(50 * get_scale_factor()))
    title = render_text_with_shadow("About HexaHunt", title_font, TITLE_TEXT)
    title_rect = title.get_rect(center=(CURRENT_WIDTH//2, 60 * get_scale_factor()))
    screen.blit(title, title_rect)
    
    # Add logo below title
    try:
        # Load the logo image if not already stored in settings
        if 'logo_image' not in settings:
            logo_img = pygame.image.load('logo.png')
            # Scale logo to appropriate size (about 100px height at default scale)
            logo_height = int(100 * get_scale_factor())
            logo_width = int(logo_img.get_width() * (logo_height / logo_img.get_height()))
            settings['logo_image'] = pygame.transform.scale(logo_img, (logo_width, logo_height))
        
        # Calculate position - center horizontally, place below title
        logo_rect = settings['logo_image'].get_rect()
        logo_rect.centerx = CURRENT_WIDTH // 2
        logo_rect.top = title_rect.bottom + 20 * get_scale_factor()
        
        # Draw the logo
        screen.blit(settings['logo_image'], logo_rect)
        
        # Adjust the starting y-position for the text content
        text_y = logo_rect.bottom + 20 * get_scale_factor()
    except (pygame.error, FileNotFoundError):
        print("Could not load logo image 'logo.png'")
        # If logo can't be loaded, use original text position
        text_y = 120 * get_scale_factor()
    
    # About content
    line_height = int(30 * get_scale_factor())
    
    texts = [
        "HexaHunt: A Treasure Hunting Game using Minimax Algorithm",
        "Case Study Project",
        "",
        "Polytechnic University of the Philippines",
        "College of Computer and Information Sciences",
        "Academic Year: 2024-2025",
        "",
        "Developers:"
    ]
    
    # GitHub URLs for each developer
    github_links = {
        "Frilles, Roljohn C.": "https://github.com/psychammer",
        "Macaraeg, Paul Angelo O.": "https://github.com/PaullyMac",
        "Manansala, Roan P.": "https://github.com/rn-mnsl",
        "Manucom, Precious Grace Deborah S.": "https://github.com/Debb1ie"
    }
    
    # Create GitHub icon if not exists
    if not hasattr(settings, 'github_icon'):
        # Create a simple "GitHub" text as a clickable element
        settings['github_icon'] = {}
        for dev in github_links:
            settings['github_icon'][dev] = render_text_with_shadow("[GitHub]", font, (0, 0, 255))  # Blue color for links
    
    # Initialize clickable areas if not exists
    if 'github_clickable' not in settings:
        settings['github_clickable'] = {}
    
    y_pos = text_y
    for text in texts:
        # Headers bold, normal text regular
        if ":" in text or text == "Developers:":
            text_surf = render_text_with_shadow(text, font, TITLE_TEXT)
        else:
            text_surf = render_text_with_shadow(text, font, BODY_TEXT)
            
        # Center align - calculate x position so text is centered
        text_rect = text_surf.get_rect(center=(CURRENT_WIDTH // 2, y_pos + text_surf.get_height() // 2))
        screen.blit(text_surf, text_rect.topleft)
        y_pos += line_height
    
    # Developer names with GitHub links
    developer_names = [
        "• Frilles, Roljohn C.",
        "• Macaraeg, Paul Angelo O.",
        "• Manansala, Roan P.",
        "• Manucom, Precious Grace Deborah S."
    ]
    
    # Draw developer names with GitHub links
    for dev_text in developer_names:
        # Get the developer name without the bullet point
        dev_name = dev_text[2:]  # Remove "• " prefix
        
        # Draw the name
        text_surf = render_text_with_shadow(dev_text, font, TITLE_TEXT)
        # Left-align to make space for GitHub link, but still centered overall
        text_rect = text_surf.get_rect(center=(CURRENT_WIDTH // 2 - 50, y_pos + text_surf.get_height() // 2))
        screen.blit(text_surf, text_rect.topleft)
        
        # Draw the GitHub link
        github_surf = settings['github_icon'][dev_name]
        github_rect = github_surf.get_rect(midleft=(text_rect.right + 15, text_rect.centery))
        screen.blit(github_surf, github_rect.topleft)
        
        # Store the clickable area for this link
        settings['github_clickable'][dev_name] = github_rect
        
        y_pos += line_height
    
    y_pos += line_height * 0.5
    
    # Continue with the rest of the about content
    texts = [
        "",
        "Core Technology:",
        "AI opponent driven by the Minimax algorithm with Alpha-Beta Pruning",
        "",
        "Game Concept:",
        "A variation of Dots and Boxes played on a hexagonal grid"
    ]
    
    for text in texts:
        # Headers bold, normal text regular
        if ":" in text:
            text_surf = render_text_with_shadow(text, font, TITLE_TEXT)
        else:
            text_surf = render_text_with_shadow(text, font, BODY_TEXT)
            
        # Center align - calculate x position so text is centered
        text_rect = text_surf.get_rect(center=(CURRENT_WIDTH // 2, y_pos + text_surf.get_height() // 2))
        screen.blit(text_surf, text_rect.topleft)
        y_pos += line_height
    
    # Back button
    back_button = settings['buttons']['about'][0]
    draw_button(screen, back_button, is_button_hovered(back_button, pygame.mouse.get_pos()))
    
    # Update the display unless we're in a transition
    if not skip_display:
        pygame.display.flip()

def draw_settings_screen(screen, font, settings, skip_display=False):
    """Draw the enhanced settings screen"""
    # Draw gradient background
    gradient = create_gradient_surface(CURRENT_WIDTH, CURRENT_HEIGHT, MENU_BG_TOP, MENU_BG_BOTTOM)
    screen.blit(gradient, (0, 0))
    
    # Draw animated hexagons
    draw_hexagons(screen)
    
    # Title with shadow
    title_font = pygame.font.SysFont(None, int(50 * get_scale_factor()))
    title = render_text_with_shadow("Settings", title_font, TITLE_TEXT)
    title_rect = title.get_rect(center=(CURRENT_WIDTH//2, 60 * get_scale_factor()))
    screen.blit(title, title_rect)
    
    # Settings content
    text_x = CURRENT_WIDTH // 4
    text_y = 150 * get_scale_factor()
    line_height = int(40 * get_scale_factor())
    
    # Board Radius Setting with shadow
    radius_text = render_text_with_shadow(
        f"Board Radius: {settings['board_radius']}", font, TITLE_TEXT)
    radius_text_width = radius_text.get_width()
    screen.blit(radius_text, (text_x, text_y))
    
    # Calculate proper positions for buttons to align them consistently
    button_size = 50 * get_scale_factor()
    button_spacing = 20 * get_scale_factor()
    
    # Position the - button to start at a consistent distance from the text's right edge
    minus_x = text_x + radius_text_width + button_spacing
    plus_x = minus_x + button_size + button_spacing/2
    
    # Update positions of radius adjustment buttons
    radius_left_button = settings['buttons']['settings'][1]
    radius_right_button = settings['buttons']['settings'][2]
    radius_left_button['rect'].x = minus_x
    radius_left_button['rect'].y = text_y - (radius_left_button['rect'].height - radius_text.get_height())/2
    radius_right_button['rect'].x = plus_x
    radius_right_button['rect'].y = radius_left_button['rect'].y
    radius_left_button['text_rect'].center = radius_left_button['rect'].center
    radius_right_button['text_rect'].center = radius_right_button['rect'].center
    
    # Draw radius adjustment buttons
    draw_button(screen, radius_left_button, is_button_hovered(radius_left_button, pygame.mouse.get_pos()))
    draw_button(screen, radius_right_button, is_button_hovered(radius_right_button, pygame.mouse.get_pos()))
    
    # AI Difficulty Setting with shadow
    difficulty_text = render_text_with_shadow(
        f"AI Depth: {settings['ai_depth']} ({get_difficulty_text(settings['ai_depth'])})", 
        font, TITLE_TEXT)
    screen.blit(difficulty_text, (text_x, text_y + line_height))
    
    # Update positions of depth adjustment buttons - use same horizontal positions for alignment
    depth_left_button = settings['buttons']['settings'][3]
    depth_right_button = settings['buttons']['settings'][4]
    depth_left_button['rect'].x = minus_x
    depth_left_button['rect'].y = text_y + line_height - (depth_left_button['rect'].height - difficulty_text.get_height())/2
    depth_right_button['rect'].x = plus_x
    depth_right_button['rect'].y = depth_left_button['rect'].y
    depth_left_button['text_rect'].center = depth_left_button['rect'].center
    depth_right_button['text_rect'].center = depth_right_button['rect'].center
    
    # Draw difficulty adjustment buttons
    draw_button(screen, depth_left_button, is_button_hovered(depth_left_button, pygame.mouse.get_pos()))
    draw_button(screen, depth_right_button, is_button_hovered(depth_right_button, pygame.mouse.get_pos()))
    
    # Back button
    back_button = settings['buttons']['settings'][0]
    draw_button(screen, back_button, is_button_hovered(back_button, pygame.mouse.get_pos()))
    
    # Update the display unless we're in a transition
    if not skip_display:
        pygame.display.flip()

def get_difficulty_text(depth):
    """Convert AI depth to difficulty text"""
    if depth == 2:
        return "Easy"
    elif depth == 3:
        return "Medium"
    elif depth == 4:
        return "Hard"
    else:
        return "Custom"

# ----- Event Handling Functions -----
def handle_opening_events(event, settings):
    """Handle events on the opening screen"""
    current_state = 'OPENING_SCREEN'
    
    if event.type == pygame.MOUSEBUTTONDOWN:
        pos = pygame.mouse.get_pos()
        
        # Check if any button was clicked
        for button in settings['buttons']['opening']:
            if button['rect'].collidepoint(pos):
                if button['text'] == "Start Game":
                    current_state = 'GAME_RUNNING'
                elif button['text'] == "How to Play":
                    start_transition('HOW_TO_PLAY_SCREEN')
                    return 'TRANSITION'
                elif button['text'] == "About":
                    start_transition('ABOUT_SCREEN')
                    return 'TRANSITION'
                elif button['text'] == "Settings":
                    start_transition('SETTINGS_SCREEN')
                    return 'TRANSITION'
                elif button['text'] == "Quit":
                    current_state = 'QUIT'
                break
                
    return current_state

def handle_how_to_play_events(event, settings):
    """Handle events on the how to play screen"""
    current_state = 'HOW_TO_PLAY_SCREEN'
    
    if event.type == pygame.MOUSEBUTTONDOWN:
        pos = pygame.mouse.get_pos()
        
        # Check if back button was clicked
        back_button = settings['buttons']['how_to_play'][0]
        if back_button['rect'].collidepoint(pos):
            start_transition('OPENING_SCREEN')
            return 'TRANSITION'
        
        # Handle mouse wheel scrolling
        if event.button == 4:  # Scroll up
            if 'how_to_play_scroll' in settings:
                settings['how_to_play_scroll'] = max(0, settings['how_to_play_scroll'] - 30 * get_scale_factor())
        elif event.button == 5:  # Scroll down
            if 'how_to_play_scroll' in settings:
                settings['how_to_play_scroll'] += 30 * get_scale_factor()
                # Clamping happens in the draw function
                
    # Also handle mouse wheel events separately (some systems use this event)
    elif event.type == pygame.MOUSEWHEEL:
        scroll_amount = event.y * 30 * get_scale_factor()  # Adjust scroll speed
        if 'how_to_play_scroll' in settings:
            settings['how_to_play_scroll'] = max(0, settings['how_to_play_scroll'] - scroll_amount)
                
    return current_state

def handle_about_events(event, settings):
    """Handle events on the about screen"""
    current_state = 'ABOUT_SCREEN'
    
    if event.type == pygame.MOUSEBUTTONDOWN:
        pos = pygame.mouse.get_pos()
        
        # Check if back button was clicked
        back_button = settings['buttons']['about'][0]
        if back_button['rect'].collidepoint(pos):
            start_transition('OPENING_SCREEN')
            return 'TRANSITION'
        
        # Check if any GitHub link was clicked
        github_links = {
            "Frilles, Roljohn C.": "https://github.com/psychammer",
            "Macaraeg, Paul Angelo O.": "https://github.com/PaullyMac",
            "Manansala, Roan P.": "https://github.com/rn-mnsl",
            "Manucom, Precious Grace Deborah S.": "https://github.com/Debb1ie"
        }
        
        if 'github_clickable' in settings:
            for dev_name, rect in settings['github_clickable'].items():
                if rect.collidepoint(pos):
                    # Open the GitHub URL in the default web browser
                    import webbrowser
                    webbrowser.open(github_links[dev_name])
                    break
                
    return current_state

def handle_settings_events(event, settings):
    """Handle events on the settings screen"""
    current_state = 'SETTINGS_SCREEN'
    
    if event.type == pygame.MOUSEBUTTONDOWN:
        pos = pygame.mouse.get_pos()
        
        # Check button clicks
        # Back button
        back_button = settings['buttons']['settings'][0]
        if back_button['rect'].collidepoint(pos):
            start_transition('OPENING_SCREEN')
            return 'TRANSITION'
        
        # Radius decrease button
        radius_left_button = settings['buttons']['settings'][1]
        if radius_left_button['rect'].collidepoint(pos) and settings['board_radius'] > 1:
            settings['board_radius'] -= 1
        
        # Radius increase button
        radius_right_button = settings['buttons']['settings'][2]
        if radius_right_button['rect'].collidepoint(pos) and settings['board_radius'] < 4:
            settings['board_radius'] += 1
        
        # Depth decrease button
        depth_left_button = settings['buttons']['settings'][3]
        if depth_left_button['rect'].collidepoint(pos) and settings['ai_depth'] > 2:
            settings['ai_depth'] -= 1
        
        # Depth increase button
        depth_right_button = settings['buttons']['settings'][4]
        if depth_right_button['rect'].collidepoint(pos) and settings['ai_depth'] < 4:
            settings['ai_depth'] += 1
                
    return current_state

# ----- Original Game Loop (renamed) -----
def run_game_loop(screen, font, settings):
    """Main game loop (former main function)"""
    global CURRENT_WIDTH, CURRENT_HEIGHT, DEPTH
    
    # Apply settings
    DEPTH = settings['ai_depth']
    
    clock = pygame.time.Clock()
    state = init_state(settings['board_radius'])
    running = True

    # Create a transposition table that persists between moves
    transposition_table = {}
    
    # Create back button for game screen
    button_font = pygame.font.SysFont(None, int(32 * get_scale_factor()))
    back_button = create_button("Back", 20 * get_scale_factor(), 20 * get_scale_factor(), 
                              100 * get_scale_factor(), 40 * get_scale_factor(), button_font)
    
    # Create a new stats toggle button
    stats_button_text = "Show Stats"
    stats_button = create_button(stats_button_text, CURRENT_WIDTH - 120 * get_scale_factor(), 20 * get_scale_factor(),
                               120 * get_scale_factor(), 40 * get_scale_factor(), button_font)
    
    # Set initial AI stats visibility to False
    AI_STATS['show_stats'] = False
    
    while running:
        # Handle events (e.g. closing window, clicks, resize)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                # Update current window size
                CURRENT_WIDTH, CURRENT_HEIGHT = event.size
                screen = pygame.display.set_mode((CURRENT_WIDTH, CURRENT_HEIGHT), pygame.RESIZABLE)
                # Recalculate font size based on new window size
                font_size = int(28 * get_scale_factor())
                font = pygame.font.SysFont(None, max(12, font_size))
                # Update button positions and sizes
                button_font = pygame.font.SysFont(None, int(32 * get_scale_factor()))
                back_button = create_button("Back", 20 * get_scale_factor(), 20 * get_scale_factor(), 
                                          100 * get_scale_factor(), 40 * get_scale_factor(), button_font)
                stats_button_text = "Show Stats" if not AI_STATS['show_stats'] else "Hide Stats"
                stats_button = create_button(stats_button_text, CURRENT_WIDTH - 120 * get_scale_factor(), 
                                           20 * get_scale_factor(), 120 * get_scale_factor(), 
                                           40 * get_scale_factor(), button_font)
                # Rebuild the game state to recenter the board
                state = init_state(settings['board_radius'])
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                
                # Check if back button was clicked
                if back_button['rect'].collidepoint(pos):
                    return  # Exit game loop and return to main menu
                
                # Check if stats button was clicked
                if stats_button['rect'].collidepoint(pos):
                    # Toggle stats visibility
                    AI_STATS['show_stats'] = not AI_STATS['show_stats']
                    # Update button text
                    stats_button_text = "Show Stats" if not AI_STATS['show_stats'] else "Hide Stats"
                    stats_button = create_button(stats_button_text, CURRENT_WIDTH - 120 * get_scale_factor(), 
                                               20 * get_scale_factor(), 120 * get_scale_factor(), 
                                               40 * get_scale_factor(), button_font)
                
                # Only allow moves if it is the human player's turn.
                if state['turn'] == 0:
                    move = get_clicked_edge(pos, state)
                    if move is not None:
                        new_state, extra_turn = apply_move(state, move, 0)
                        state = new_state
                        draw_board(screen, state, font, back_button, stats_button)
                        # Reset visualization edges after human move
                        AI_STATS['visualization_edges'] = {}

        # AI turn
        if state['turn'] == 1:
            pygame.display.set_caption("AI is thinking...")
            
            # Reset counters for this turn
            AI_STATS['cache_hits'] = 0
            AI_STATS['positions_evaluated'] = 0
            AI_STATS['visualization_edges'] = {}
            
            # Small delay to show update and redraw the board
            draw_board(screen, state, font, back_button, stats_button)
            pygame.time.delay(200)
            
            # Double-check that there are valid moves available
            possible_moves = get_possible_moves(state)
            if not possible_moves:
                print("No valid moves available for AI")
                pygame.display.set_caption("HexaHunt - Hexagonal Dots and Boxes")
                continue
            
            # Record start time for AI thinking
            start_time = time.time()
            
            # AI makes its move
            _, move = minimax(state, DEPTH, -math.inf, math.inf, True, transposition_table)
            
            # Validate the AI's move
            if move is None or state['edges'][move] != -1:
                # AI selected an invalid move, select a random valid move instead
                print("AI attempted an invalid move, selecting random valid move")
                if possible_moves:
                    move = possible_moves[0]
                else:
                    continue
            
            # Calculate and store thinking time
            AI_STATS['thinking_time'] = time.time() - start_time
            
            # Visualize the move chosen by the AI
            if move is not None:
                # Generate visualization data showing which edges were evaluated
                possible_moves = get_possible_moves(state)
                for edge in possible_moves:
                    edge_hash = hash_state(apply_move(state, edge, 1)[0])
                    if edge_hash in transposition_table:
                        if edge == move:
                            # Highlight the chosen move differently
                            AI_STATS['visualization_edges'][edge] = 'chosen'
                        else:
                            AI_STATS['visualization_edges'][edge] = 'cache_hit'
                
                # Show visualization for a moment before making the move
                draw_board(screen, state, font, back_button, stats_button)
                pygame.display.flip()
                pygame.time.delay(1000)  # Pause to show the visualization
                
                # Apply the AI's move
                new_state, extra_turn = apply_move(state, move, 1)
                state = new_state
                
            pygame.display.set_caption("HexaHunt - Hexagonal Dots and Boxes")

        draw_board(screen, state, font, back_button, stats_button)
        if is_terminal(state):
            # Final drawing and delay before returning to menu
            draw_board(screen, state, font, back_button, stats_button)
            
            # Determine winner
            if state['score'][0] > state['score'][1]:
                result = "You Win!"
            elif state['score'][0] < state['score'][1]:
                result = "AI Wins!"
            else:
                result = "It's a Tie!"
            
            # Scale text position for game over message    
            final_text = font.render(f"Game Over! {result}", True, BLACK)
            screen.blit(final_text, (CURRENT_WIDTH // 2 - 120 * get_scale_factor(), CURRENT_HEIGHT // 2))
            pygame.display.flip()
            pygame.time.delay(3000)
            return
            
        clock.tick(30)
        
# ----- Hexagon Background Animation -----
class AnimatedHexagon:
    """Class to represent a floating background hexagon"""
    def __init__(self, width, height):
        # Random size between 20 and 80
        self.size = random.randint(20, 80)
        # Random position anywhere on screen
        self.x = random.randint(0, width)
        self.y = random.randint(0, height)
        # Random slow velocity
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.5, 0.5)
        # Random rotation state and speed
        self.angle = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-1, 1)
        # Random transparency
        self.alpha = random.randint(20, 80)
        self.width = width
        self.height = height

    def update(self):
        # Update position
        self.x += self.vx
        self.y += self.vy
        # Wrap around edges
        if self.x < -self.size:
            self.x = self.width + self.size
        elif self.x > self.width + self.size:
            self.x = -self.size
        if self.y < -self.size:
            self.y = self.height + self.size
        elif self.y > self.height + self.size:
            self.y = -self.size
        # Update rotation
        self.angle += self.rotation_speed
        if self.angle >= 360:
            self.angle -= 360

    def draw(self, screen):
        # Calculate vertices based on current position and rotation
        vertices = []
        for i in range(6):
            angle_deg = 60 * i + self.angle
            angle_rad = math.radians(angle_deg)
            vx = self.x + self.size * math.cos(angle_rad)
            vy = self.y + self.size * math.sin(angle_rad)
            vertices.append((int(vx), int(vy)))
        
        # Draw filled hexagon with alpha
        gfxdraw.filled_polygon(screen, vertices, 
                              (HEX_COLOR[0], HEX_COLOR[1], HEX_COLOR[2], self.alpha))
        
        # Draw outline with slightly more alpha
        outline_alpha = min(255, self.alpha + 30)
        gfxdraw.aapolygon(screen, vertices, 
                         (HEX_COLOR[0], HEX_COLOR[1], HEX_COLOR[2], outline_alpha))

def initialize_hexagons(count, width, height):
    """Create a pool of animated hexagons"""
    return [AnimatedHexagon(width, height) for _ in range(count)]

def update_hexagons():
    """Update all hexagons in the pool"""
    for hexagon in UI_ANIMATION['hexagons']:
        hexagon.update()

def draw_hexagons(screen):
    """Draw all hexagons from the pool"""
    for hexagon in UI_ANIMATION['hexagons']:
        hexagon.draw(screen)

# ----- Gradient Background -----
def create_gradient_surface(width, height, color_top, color_bottom):
    """Create a vertical gradient surface"""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    for y in range(height):
        # Calculate interpolation factor
        factor = y / height
        
        # Interpolate between colors
        r = int(color_top[0] * (1 - factor) + color_bottom[0] * factor)
        g = int(color_top[1] * (1 - factor) + color_bottom[1] * factor)
        b = int(color_top[2] * (1 - factor) + color_bottom[2] * factor)
        
        # Draw a horizontal line with the calculated color
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))
    
    return surface

# ----- Enhanced Text Rendering -----
def render_text_with_shadow(text, font, color, shadow_color=(50, 50, 50, 128), offset=2):
    """Render text without shadow effect"""
    # Simply return regular text without applying shadow effects
    return font.render(text, True, color)

# ----- Screen Transition System -----
def start_transition(target_screen):
    """Begin a screen transition to the target screen"""
    UI_ANIMATION['transition_active'] = True
    UI_ANIMATION['target_screen'] = target_screen
    UI_ANIMATION['transition_alpha'] = 0

def update_transition():
    """Update the screen transition effect"""
    if UI_ANIMATION['transition_active']:
        # Fade in by increasing alpha
        UI_ANIMATION['transition_alpha'] += 15  # Adjust speed here
        
        if UI_ANIMATION['transition_alpha'] >= 255:
            # Transition complete
            UI_ANIMATION['transition_alpha'] = 255
            UI_ANIMATION['transition_active'] = False
            UI_ANIMATION['current_screen'] = UI_ANIMATION['target_screen']
            return UI_ANIMATION['target_screen']
    
    return None

def draw_transition(screen, next_screen_func, settings):
    """Draw the transition effect"""
    # If we're in an active transition, draw the target screen with partial alpha
    if UI_ANIMATION['transition_active']:
        # Create a surface for the target screen
        target_surface = pygame.Surface((CURRENT_WIDTH, CURRENT_HEIGHT), pygame.SRCALPHA)
        
        # Draw the target screen to our surface
        if UI_ANIMATION['target_screen'] == 'OPENING_SCREEN':
            draw_opening_screen(target_surface, base_font, button_font, settings, skip_display=True)
        elif UI_ANIMATION['target_screen'] == 'HOW_TO_PLAY_SCREEN':
            draw_how_to_play_screen(target_surface, base_font, settings, skip_display=True)
        elif UI_ANIMATION['target_screen'] == 'ABOUT_SCREEN':
            draw_about_screen(target_surface, base_font, settings, skip_display=True)
        elif UI_ANIMATION['target_screen'] == 'SETTINGS_SCREEN':
            draw_settings_screen(target_surface, base_font, settings, skip_display=True)
        
        # Apply alpha to the entire surface
        alpha_surface = pygame.Surface((CURRENT_WIDTH, CURRENT_HEIGHT), pygame.SRCALPHA)
        alpha_surface.fill((255, 255, 255, UI_ANIMATION['transition_alpha']))
        target_surface.blit(alpha_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # Draw the alpha-adjusted surface to the screen
        screen.blit(target_surface, (0, 0))

# ----- New Main Function with State Machine -----
def main():
    global CURRENT_WIDTH, CURRENT_HEIGHT, base_font, button_font
    
    pygame.init()
    
    # Set custom window icon
    try:
        icon = pygame.image.load('logo.png')
        pygame.display.set_icon(icon)
    except pygame.error:
        print("Could not load icon image 'logo.png'")
    
    screen = pygame.display.set_mode((DEFAULT_WIDTH, DEFAULT_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("HexaHunt")
    
    # Initialize fonts
    base_font = pygame.font.SysFont(None, 28)  # Base font for game
    button_font = pygame.font.SysFont(None, 32)  # Slightly larger for buttons
    
    # Setup settings and buttons
    settings = {
        'board_radius': 2,
        'ai_depth': 3,
        'buttons': {}
    }
    
    # Create buttons for all screens
    def update_buttons():
        # Calculate button positions based on current window size
        button_width = 200 * get_scale_factor()
        button_height = 50 * get_scale_factor()
        button_spacing = 70 * get_scale_factor()
        start_y = CURRENT_HEIGHT//2
        
        # Calculate center position - ensure buttons are always centered
        center_x = (CURRENT_WIDTH - button_width) // 2
        
        # Opening screen buttons
        settings['buttons']['opening'] = [
            create_button("Start Game", center_x, start_y, button_width, button_height, button_font, "start"),
            create_button("How to Play", center_x, start_y + button_spacing, button_width, button_height, button_font, "howto"),
            create_button("About", center_x, start_y + 2*button_spacing, button_width, button_height, button_font, "about"),
            create_button("Settings", center_x, start_y + 3*button_spacing, button_width, button_height, button_font, "settings"),
            create_button("Quit", center_x, start_y + 4*button_spacing, button_width, button_height, button_font, "quit")
        ]
        
        # How to Play screen buttons
        settings['buttons']['how_to_play'] = [
            create_button("Back", 50 * get_scale_factor(), CURRENT_HEIGHT - 80 * get_scale_factor(), 
                          button_width, button_height, button_font, "back_howto")
        ]
        
        # About screen buttons
        settings['buttons']['about'] = [
            create_button("Back", 50 * get_scale_factor(), CURRENT_HEIGHT - 80 * get_scale_factor(), 
                          button_width, button_height, button_font, "back_about")
        ]
        
        # Settings screen buttons
        settings['buttons']['settings'] = [
            create_button("Back", 50 * get_scale_factor(), CURRENT_HEIGHT - 80 * get_scale_factor(), 
                          button_width, button_height, button_font, "back_settings"),
            create_button("-", CURRENT_WIDTH//2 + 50 * get_scale_factor(), 150 * get_scale_factor(), 
                          50 * get_scale_factor(), button_height, button_font, "radius_minus"),
            create_button("+", CURRENT_WIDTH//2 + 110 * get_scale_factor(), 150 * get_scale_factor(), 
                          50 * get_scale_factor(), button_height, button_font, "radius_plus"),
            create_button("-", CURRENT_WIDTH//2 + 50 * get_scale_factor(), 190 * get_scale_factor(), 
                          50 * get_scale_factor(), button_height, button_font, "depth_minus"),
            create_button("+", CURRENT_WIDTH//2 + 110 * get_scale_factor(), 190 * get_scale_factor(), 
                          50 * get_scale_factor(), button_height, button_font, "depth_plus")
        ]
    
    update_buttons()
    
    # Initialize hexagons (adjust count as needed)
    UI_ANIMATION['hexagons'] = initialize_hexagons(25, CURRENT_WIDTH, CURRENT_HEIGHT)
    
    # Initialize state and game loop
    current_state = 'OPENING_SCREEN'
    UI_ANIMATION['current_screen'] = current_state
    clock = pygame.time.Clock()
    running = True
    
    while running:
        # Update hexagons for animation
        update_hexagons()
        
        # Handle window resize event outside of state-specific handlers
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            elif event.type == pygame.VIDEORESIZE:
                # Update current window size
                CURRENT_WIDTH, CURRENT_HEIGHT = event.size
                screen = pygame.display.set_mode((CURRENT_WIDTH, CURRENT_HEIGHT), pygame.RESIZABLE)
                # Recalculate font size based on new window size
                base_font = pygame.font.SysFont(None, int(28 * get_scale_factor()))
                button_font = pygame.font.SysFont(None, int(32 * get_scale_factor()))
                update_buttons()
                # Reinitialize hexagons for the new screen size
                UI_ANIMATION['hexagons'] = initialize_hexagons(25, CURRENT_WIDTH, CURRENT_HEIGHT)
            
            # Pass the event to state-specific handlers only if not in transition
            if not UI_ANIMATION['transition_active']:
                if current_state == 'OPENING_SCREEN':
                    current_state = handle_opening_events(event, settings)
                elif current_state == 'HOW_TO_PLAY_SCREEN':
                    current_state = handle_how_to_play_events(event, settings)
                elif current_state == 'ABOUT_SCREEN':
                    current_state = handle_about_events(event, settings)
                elif current_state == 'SETTINGS_SCREEN':
                    current_state = handle_settings_events(event, settings)
        
        # Update transitions if active
        transition_result = update_transition()
        if transition_result:
            current_state = transition_result
        
        # Draw the current screen
        if current_state == 'TRANSITION':
            # Draw the current screen as base
            if UI_ANIMATION['current_screen'] == 'OPENING_SCREEN':
                draw_opening_screen(screen, base_font, button_font, settings)
            elif UI_ANIMATION['current_screen'] == 'HOW_TO_PLAY_SCREEN':
                draw_how_to_play_screen(screen, base_font, settings)
            elif UI_ANIMATION['current_screen'] == 'ABOUT_SCREEN':
                draw_about_screen(screen, base_font, settings)
            elif UI_ANIMATION['current_screen'] == 'SETTINGS_SCREEN':
                draw_settings_screen(screen, base_font, settings)
                
            # Draw transition effect on top
            draw_transition(screen, None, settings)
        elif current_state == 'OPENING_SCREEN':
            draw_opening_screen(screen, base_font, button_font, settings)
        elif current_state == 'HOW_TO_PLAY_SCREEN':
            draw_how_to_play_screen(screen, base_font, settings)
        elif current_state == 'ABOUT_SCREEN':
            draw_about_screen(screen, base_font, settings)
        elif current_state == 'SETTINGS_SCREEN':
            draw_settings_screen(screen, base_font, settings)
        elif current_state == 'GAME_RUNNING':
            pygame.display.set_caption("HexaHunt - Playing Game")
            run_game_loop(screen, base_font, settings)
            # After game ends, return to opening screen and update buttons
            current_state = 'OPENING_SCREEN'
            update_buttons()  # Add this line to recalculate button positions
        elif current_state == 'QUIT':
            running = False
        
        clock.tick(60)  # Increase to 60 FPS for smoother animations
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()