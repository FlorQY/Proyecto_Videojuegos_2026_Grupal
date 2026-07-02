"""
Pantallas emergentes (overlays) para decisiones del jugador:
- Robo con decisión (carta separada + botones)
- Respuesta a penalización
- Selección de color
- Selección de oponente (carta 7)
- Indicador de penalización pendiente (parpadeante)
"""

import pygame
import time

# Importar constantes y colores desde ui.py
from src.ui import (
    WHITE,
    BLACK,
    GRAY,
    GREEN,
    RED,
    YELLOW,
    COLOR_DISPLAY,
    is_valid_play,
    draw_card,
)


def draw_decision_overlay(screen, game, font, font_small):
    """Dibuja la carta robada separada con botones JUGAR / GUARDAR."""
    if not (game.waiting_for_decision and game.drawn_card_temp is not None):
        return

    card = game.drawn_card_temp
    draw_x = 490
    draw_y = 400
    card_width = 90
    card_height = 140

    draw_card(
        screen,
        card,
        draw_x,
        draw_y,
        card_width,
        card_height,
        border_radius=10,
        border_width=0,
        shadow=True,
    )

    btn_width = 120
    btn_height = 50
    play_rect = pygame.Rect(460, 560, btn_width, btn_height)
    keep_rect = pygame.Rect(620, 560, btn_width, btn_height)

    game.btn_play_rect = play_rect
    game.btn_keep_rect = keep_rect

    if is_valid_play(card, game.center_card):
        play_color = GREEN
        play_text_color = WHITE
    else:
        play_color = GRAY
        play_text_color = (150, 150, 150)

    pygame.draw.rect(screen, play_color, play_rect, border_radius=8)
    pygame.draw.rect(screen, WHITE, play_rect, 2, border_radius=8)
    play_label = font.render("JUGAR", True, play_text_color)
    screen.blit(play_label, (play_rect.x + 20, play_rect.y + 10))

    pygame.draw.rect(screen, RED, keep_rect, border_radius=8)
    pygame.draw.rect(screen, WHITE, keep_rect, 2, border_radius=8)
    keep_label = font.render("GUARDAR", True, WHITE)
    screen.blit(keep_label, (keep_rect.x + 10, keep_rect.y + 10))

    remaining = max(0, game.decision_timeout - game.decision_timer)
    timer_text = font_small.render(f"Tiempo: {remaining:.1f}s", True, WHITE)
    screen.blit(timer_text, (draw_x + 10, draw_y - 30))


def draw_penalty_response_overlay(screen, game, font, font_big, font_small):
    """Dibuja la interfaz para responder a una penalización."""
    if not (game.waiting_for_penalty_response and game.current_turn == 0):
        return

    msg = font_big.render("¡PENALIZACIÓN PENDIENTE!", True, YELLOW)
    msg_rect = msg.get_rect(center=(640, 200))
    screen.blit(msg, msg_rect)

    draw_text = font.render(f"Total: +{game.pending_draws} cartas", True, WHITE)
    draw_rect = draw_text.get_rect(center=(640, 250))
    screen.blit(draw_text, draw_rect)

    player = game.players[0]
    penalty_cards = []
    for i, card in enumerate(player.hand):
        if card.value in ["+2", "+4", "+6", "+10", "+4 Reverse"]:
            penalty_cards.append((i, card))

    game.penalty_card_rects = []
    game.penalty_card_indices = []
    x_start = 320
    y_cards = 320
    spacing = 110

    for idx, (card_index, card) in enumerate(penalty_cards):
        x = x_start + idx * spacing
        rect = pygame.Rect(x, y_cards, 80, 120)
        game.penalty_card_rects.append(rect)
        game.penalty_card_indices.append(card_index)

        draw_card(screen, card, x, y_cards, 80, 120, border_radius=8, border_width=2)

    rob_rect = pygame.Rect(560, 480, 160, 50)
    game.btn_rob_rect = rob_rect
    pygame.draw.rect(screen, RED, rob_rect, border_radius=8)
    pygame.draw.rect(screen, WHITE, rob_rect, 2, border_radius=8)
    rob_label = font.render("ROBAR", True, WHITE)
    screen.blit(rob_label, (rob_rect.x + 40, rob_rect.y + 10))

    remaining = max(0, game.penalty_response_timeout - game.penalty_response_timer)
    timer_text = font_small.render(f"Tiempo: {remaining:.1f}s", True, WHITE)
    screen.blit(timer_text, (640, 540))


def draw_color_selection(screen, game, font_big, font):
    """Dibuja el menú de selección de color (4 círculos)."""
    overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    msg = font_big.render("ELIGE UN COLOR:", True, WHITE)
    msg_rect = msg.get_rect(center=(640, 200))
    screen.blit(msg, msg_rect)

    colors = ["Red", "Blue", "Green", "Yellow"]
    x_positions = [400, 560, 720, 880]
    y_pos = 320
    radius = 60

    game.color_rects = []
    for i, color in enumerate(colors):
        x = x_positions[i]
        pygame.draw.circle(screen, COLOR_DISPLAY[color], (x, y_pos), radius)
        pygame.draw.circle(screen, WHITE, (x, y_pos), radius, 3)
        text = font.render(color, True, WHITE)
        text_rect = text.get_rect(center=(x, y_pos + 90))
        screen.blit(text, text_rect)
        rect = pygame.Rect(x - radius, y_pos - radius, radius * 2, radius * 2)
        game.color_rects.append((rect, color))

    remaining = max(0, game.selection_timeout - game.selection_timer)
    timer_text = font.render(f"Tiempo: {remaining:.1f}s", True, WHITE)
    screen.blit(timer_text, (640, 480))


def draw_opponent_selection(screen, game, font_big, font):
    """Dibuja el menú de selección de oponente (carta 7)."""
    overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    msg = font_big.render("ELIGE UN OPONENTE:", True, WHITE)
    msg_rect = msg.get_rect(center=(640, 200))
    screen.blit(msg, msg_rect)

    player = game.pending_swap_player
    opponents = []
    for i, p in enumerate(game.players):
        if p is not player:
            opponents.append((i, p))

    game.opponent_rects = []
    game.opponent_indices = []
    x_positions = [400, 640, 880]
    y_pos = 320
    width = 160
    height = 80

    for idx, (i, p) in enumerate(opponents):
        x = x_positions[idx]
        rect = pygame.Rect(x - width // 2, y_pos, width, height)

        if game.current_turn == i:
            color = YELLOW
        else:
            color = GRAY

        pygame.draw.rect(screen, color, rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, rect, 3, border_radius=10)

        name_text = font.render(p.name, True, BLACK if color == YELLOW else WHITE)
        name_rect = name_text.get_rect(center=(x, y_pos + 40))
        screen.blit(name_text, name_rect)

        game.opponent_rects.append(rect)
        game.opponent_indices.append(i)

    remaining = max(0, game.selection_timeout - game.selection_timer)
    timer_text = font.render(f"Tiempo: {remaining:.1f}s", True, WHITE)
    screen.blit(timer_text, (640, 480))


def draw_pending_penalty(screen, game, font):
    """Dibuja el indicador parpadeante de penalización pendiente."""
    if game.pending_draws > 0 and game.pending_victim is not None:
        if game.pending_victim == 0:
            x, y = 640, 680
        elif game.pending_victim == 1:
            x, y = 80, 350
        elif game.pending_victim == 2:
            x, y = 640, 50
        else:
            x, y = 1200, 350

        text = f"¡+{game.pending_draws}!"
        penalty_text = font.render(text, True, RED)
        text_rect = penalty_text.get_rect(center=(x, y))

        if int(time.time() * 2) % 2 == 0:
            s = pygame.Surface(text_rect.inflate(20, 10).size, pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            screen.blit(s, text_rect.inflate(20, 10).topleft)
            screen.blit(penalty_text, text_rect)
