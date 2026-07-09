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


def draw_sad_target_selection(screen, game, font_big, font):
    """Dibuja el menú de selección de objetivo para la carta Sad."""
    overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    msg = font_big.render("ELIGE UN OPONENTE PARA SAD:", True, WHITE)
    msg_rect = msg.get_rect(center=(640, 200))
    screen.blit(msg, msg_rect)

    player = game.pending_sad_player
    opponents = []
    for i, p in enumerate(game.players):
        if p is not player:
            opponents.append((i, p))

    game.sad_opponent_rects = []
    game.sad_opponent_indices = []
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

        game.sad_opponent_rects.append(rect)
        game.sad_opponent_indices.append(i)

    remaining = max(0, game.selection_timeout - game.selection_timer)
    timer_text = font.render(f"Tiempo: {remaining:.1f}s", True, WHITE)
    screen.blit(timer_text, (640, 480))


def draw_uno_report_overlay(screen, game):
    if not game.denounce_window_open:
        return

    overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    box = pygame.Rect(390, 180, 500, 280)

    pygame.draw.rect(screen, (245, 245, 245), box, border_radius=15)
    pygame.draw.rect(screen, (40, 40, 40), box, 3, border_radius=15)

    font_title = pygame.font.SysFont("arial", 34, bold=True)
    font = pygame.font.SysFont("arial", 26)

    text = font_title.render("¡¡DENUNCIA!!", True, (200, 30, 30))
    screen.blit(text, text.get_rect(center=(640, 230)))

    player_text = font.render(
        f"{game.denounce_player.name} olvidó decir UNO", True, (20, 20, 20)
    )

    screen.blit(player_text, player_text.get_rect(center=(640, 290)))

    remaining = max(0, game.denounce_timeout - game.denounce_timer)
    timer = font.render(f"Tiempo: {remaining:.1f}s", True, (20, 20, 20))

    screen.blit(timer, timer.get_rect(center=(640, 340)))

    game.btn_denounce_rect = pygame.Rect(540, 390, 200, 60)

    pygame.draw.rect(screen, (210, 60, 60), game.btn_denounce_rect, border_radius=10)

    pygame.draw.rect(screen, (40, 40, 40), game.btn_denounce_rect, 2, border_radius=10)

    txt = font.render("DENUNCIAR", True, (255, 255, 255))

    screen.blit(txt, txt.get_rect(center=game.btn_denounce_rect.center))


def draw_uno_popup(screen, game):
    """
    Dibuja el globo 'UNO!' sobre cualquier jugador que:
    - haya dicho UNO
    - y todavía tenga exactamente una carta.
    """

    positions = {
        0: (140, 580),  # Tú
        1: (45, 340),  # Bot 1
        2: (290, 60),  # Bot 2
        3: (1160, 340),  # Bot 3
    }

    font = pygame.font.SysFont("arial", 24, bold=True)

    for i, player in enumerate(game.players):

        if not player.uno_said:
            continue

        if len(player.hand) != 1:
            continue

        x, y = positions[i]

        bubble = pygame.Rect(x, y, 85, 40)

        pygame.draw.ellipse(screen, (255, 255, 255), bubble)
        pygame.draw.ellipse(screen, (40, 40, 40), bubble, 3)

        text = font.render("UNO!", True, (0, 0, 0))
        screen.blit(text, text.get_rect(center=bubble.center))


def draw_notification(screen, game, font_big):
    """Dibuja la notificación emergente en el centro de la pantalla."""
    if game.notification_timer <= 0 or not game.notification_text:
        return

    # Fondo semitransparente para legibilidad
    text_surface = font_big.render(
        game.notification_text, True, game.notification_color
    )
    text_rect = text_surface.get_rect(center=(640, 360))

    # Fondo negro semitransparente
    padding = 20
    bg_rect = text_rect.inflate(padding * 2, padding * 2)
    bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
    bg_surface.fill((0, 0, 0, 180))
    screen.blit(bg_surface, bg_rect.topleft)

    # Borde blanco
    pygame.draw.rect(screen, (255, 255, 255), bg_rect, 2, border_radius=8)

    # Texto
    screen.blit(text_surface, text_rect)


def draw_direction_indicator(screen, game, font):
    """Dibuja una flecha indicando la dirección actual del juego."""
    direction_text = "→" if game.direction == 1 else "←"
    color = (255, 220, 50)  # amarillo
    text_surface = font.render(f"SENTIDO: {direction_text}", True, color)
    # Posicionar en la zona superior derecha de la mesa (por ejemplo, cerca de la carta central)
    x = 750
    y = 50
    screen.blit(text_surface, (x, y))
