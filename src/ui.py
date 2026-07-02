import pygame
import psutil
import os
from src.sprite_loader import get_scaled_sprite

# Al inicio del archivo, después de las importaciones
_textura_fondo = None
_textura_fondo_cargada = False

# Colores y constantes
BACKGROUND = (120, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)
GREEN = (50, 200, 50)
RED = (200, 50, 50)
YELLOW = (255, 220, 0)
BLUE = (50, 80, 220)
DARK_RED = (180, 30, 30)

CARD_WIDTH = 90
CARD_HEIGHT = 140

CARD_COLORS = {
    "Red": (220, 50, 50),
    "Blue": (50, 80, 220),
    "Green": (50, 180, 80),
    "Yellow": (240, 210, 50),
    "Wild": (20, 20, 20),
}

# Colores para selección (se usan en ui_overlays)
COLOR_NAMES = ["Red", "Blue", "Green", "Yellow"]
COLOR_DISPLAY = {
    "Red": (220, 50, 50),
    "Blue": (50, 80, 220),
    "Green": (50, 180, 80),
    "Yellow": (240, 210, 50),
}


def is_valid_play(card, center_card):
    from src.rules import is_valid_play as rules_valid

    return rules_valid(card, center_card)


def draw_card(
    screen,
    card,
    x,
    y,
    width=CARD_WIDTH,
    height=CARD_HEIGHT,
    border_radius=10,
    border_width=2,
    shadow=True,
):
    """
    Dibuja una carta en la pantalla.
    - Si card es None, dibuja un dorso (carta boca abajo).
    - Si existe sprite, lo dibuja.
    - Si no, dibuja un rectángulo con el color y texto (fallback).
    """
    # Si card es None, dibujar dorso
    if card is None:
        if shadow:
            shadow_rect = pygame.Rect(x + 3, y + 3, width, height)
            pygame.draw.rect(
                screen, (0, 0, 0, 50), shadow_rect, border_radius=border_radius
            )
        pygame.draw.rect(
            screen, (20, 20, 20), (x, y, width, height), border_radius=border_radius
        )
        if border_width > 0:
            pygame.draw.rect(
                screen,
                WHITE,
                (x, y, width, height),
                border_width,
                border_radius=border_radius,
            )
        return

    # Intentar cargar el sprite
    sprite = get_scaled_sprite(card, width, height)

    if sprite is not None:
        # PRINT DE DEPURACIÓN: Sprite encontrado y dibujado
        # Usar un contador para no saturar la consola
        if not hasattr(draw_card, "_sprite_count"):
            draw_card._sprite_count = 0
        draw_card._sprite_count += 1
        if draw_card._sprite_count <= 20:  # Mostrar solo los primeros 20
            print(f"[UI] SPRITE: {card.color} {card.value} (tamaño: {width}x{height})")
        elif draw_card._sprite_count == 21:
            print("[UI] ... (más sprites ocultos para no saturar)")

        # Sombra
        if shadow:
            shadow_rect = pygame.Rect(x + 3, y + 3, width, height)
            pygame.draw.rect(
                screen, (0, 0, 0, 80), shadow_rect, border_radius=border_radius
            )
        screen.blit(sprite, (x, y))
        return

    # PRINT DE DEPURACIÓN: Fallback (no se encontró sprite)
    # Usar un contador para no saturar la consola
    if not hasattr(draw_card, "_fallback_count"):
        draw_card._fallback_count = 0
    draw_card._fallback_count += 1
    if draw_card._fallback_count <= 20:  # Mostrar solo los primeros 20
        print(f"[UI] FALLBACK (rectángulo) para: {card.color} {card.value}")
    elif draw_card._fallback_count == 21:
        print("[UI] ... (más fallbacks ocultos para no saturar)")

    # Fallback: dibujar rectángulo
    card_color = CARD_COLORS.get(card.color, (100, 100, 100))
    if shadow:
        shadow_rect = pygame.Rect(x + 3, y + 3, width, height)
        pygame.draw.rect(
            screen, (0, 0, 0, 50), shadow_rect, border_radius=border_radius
        )
    pygame.draw.rect(
        screen, card_color, (x, y, width, height), border_radius=border_radius
    )

    if border_width > 0:
        pygame.draw.rect(
            screen,
            WHITE,
            (x, y, width, height),
            border_width,
            border_radius=border_radius,
        )

    # Mostrar el valor de la carta
    font_size = max(14, min(28, width // 3))
    font = pygame.font.SysFont("arial", font_size)
    value_text = font.render(card.value, True, WHITE)
    text_rect = value_text.get_rect(center=(x + width // 2, y + height // 2))
    screen.blit(value_text, text_rect)


def cargar_textura_fondo():
    """Carga la imagen de fondo desde assets/img/background_02.png"""
    global _textura_fondo, _textura_fondo_cargada
    if _textura_fondo_cargada:
        return

    ruta = os.path.join("assets", "img", "background_02.png")
    if os.path.exists(ruta):
        try:
            img = pygame.image.load(ruta).convert()
            # Escalar al tamaño de la pantalla (1280x720)
            _textura_fondo = pygame.transform.scale(img, (1280, 720))
            _textura_fondo_cargada = True
            print("[UI] Fondo cargado desde el png")
        except Exception as e:
            print(f"[UI] Error cargando fondo: {e}")
            _textura_fondo_cargada = True
    else:
        print("[UI] No se encontró png, usando color rojo por defecto.")
        _textura_fondo_cargada = True


def draw_game(screen, game, clock):
    # PRINT DE DEPURACIÓN (solo una vez)
    if not hasattr(draw_game, "_init"):
        draw_game._init = True
        print("[UI] Iniciando dibujo con sistema de sprites...")

    # Cargar textura de fondo si no está cargada
    global _textura_fondo, _textura_fondo_cargada
    if not _textura_fondo_cargada:
        cargar_textura_fondo()

    font = pygame.font.SysFont("arial", 30)
    font_small = pygame.font.SysFont("arial", 24)
    font_big = pygame.font.SysFont("arial", 40)

    # Dibujar fondo (textura o color sólido)
    if _textura_fondo is not None:
        screen.blit(_textura_fondo, (0, 0))
    else:
        screen.fill(BACKGROUND)  # fallback al color rojo

    # Título y turno
    title = font.render("UNO NO MERCY", True, WHITE)
    turn_text = font.render(f"TURN: {game.current_turn}", True, WHITE)
    screen.blit(title, (20, 20))
    screen.blit(turn_text, (20, 60))

    # Círculo decorativo
    pygame.draw.circle(screen, (180, 120, 0), (640, 360), 130, 12)

    # Carta central (usando draw_card)
    draw_card(
        screen, game.center_card, 590, 285, 100, 150, border_radius=10, border_width=3
    )

    # Mazo
    deck_rect = pygame.Rect(280, 150, 100, 150)
    pygame.draw.rect(screen, BLACK, deck_rect, border_radius=10)
    deck_text = font.render("UNO", True, WHITE)
    screen.blit(deck_text, (300, 210))
    game._deck_rect = deck_rect

    # Nombres de bots (con color según turno)
    bot_colors = [WHITE, WHITE, WHITE]
    if game.current_turn == 1:
        bot_colors[0] = YELLOW
    elif game.current_turn == 2:
        bot_colors[1] = YELLOW
    elif game.current_turn == 3:
        bot_colors[2] = YELLOW

    bot1 = font.render("BOT 1", True, bot_colors[0])
    bot2 = font.render("BOT 2", True, bot_colors[1])
    bot3 = font.render("BOT 3", True, bot_colors[2])
    screen.blit(bot1, (50, 300))
    screen.blit(bot2, (800, 80))
    screen.blit(bot3, (1160, 300))

    # Dorsos de bots (card=None para dibujar dorso)
    x_bot2 = 450
    for _ in game.players[2].hand:
        draw_card(screen, None, x_bot2, 40, 60, 90, border_radius=8, border_width=2)
        x_bot2 += 35

    y_bot1 = 220
    for _ in game.players[1].hand:
        draw_card(screen, None, 150, y_bot1, 60, 90, border_radius=8, border_width=2)
        y_bot1 += 25

    y_bot3 = 220
    for _ in game.players[3].hand:
        draw_card(screen, None, 1050, y_bot3, 60, 90, border_radius=8, border_width=2)
        y_bot3 += 25

    # Cartas del jugador
    player = game.players[0]
    x = 300
    for card in player.hand:
        card.x = x
        card.y = 520
        card.update_rect()
        draw_card(screen, card, x, 520, 90, 140, border_radius=12, border_width=3)
        x += 95

    # -------- OVERLAYS (llamadas a ui_overlays) --------
    from src.ui_overlays import (
        draw_decision_overlay,
        draw_penalty_response_overlay,
        draw_color_selection,
        draw_opponent_selection,
        draw_pending_penalty,
    )

    draw_decision_overlay(screen, game, font, font_small)
    draw_penalty_response_overlay(screen, game, font, font_big, font_small)

    if game.game_state == "SELECTING_COLOR":
        draw_color_selection(screen, game, font_big, font)

    if game.game_state == "SELECTING_OPPONENT":
        draw_opponent_selection(screen, game, font_big, font)

    # Botón UNO (solo visual)
    pygame.draw.circle(screen, (220, 40, 40), (1180, 620), 45)
    pygame.draw.circle(screen, WHITE, (1180, 620), 45, 4)
    uno_text = font.render("UNO", True, WHITE)
    screen.blit(uno_text, (1153, 603))

    # Ganador
    if game.winner is not None:
        winner_text = font_big.render(f"{game.winner.name} WINS!", True, YELLOW)
        screen.blit(winner_text, (560, 180))

    # Penalización pendiente (indicador general)
    draw_pending_penalty(screen, game, font)

    # Métricas
    fps = clock.get_fps()
    if fps > 0:
        frame_time = 1000 / fps
    else:
        frame_time = 0
    process = psutil.Process(os.getpid())
    ram_mb = process.memory_info().rss / 1024 / 1024

    fps_text = font.render(f"FPS: {fps:.1f}", True, WHITE)
    frame_text = font.render(f"Frame: {frame_time:.2f} ms", True, WHITE)
    ram_text = font.render(f"RAM: {ram_mb:.1f} MB", True, WHITE)
    screen.blit(fps_text, (950, 20))
    screen.blit(frame_text, (950, 50))
    screen.blit(ram_text, (950, 80))
