import pygame
import psutil
import os
from src.sprite_loader import get_scaled_sprite

# Al inicio del archivo, después de las importaciones
_textura_fondo = None
_textura_fondo_cargada = False

# botón uno
_uno_button = None
_uno_button_cargado = False

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


def cargar_boton_uno():
    """Carga la imagen del botón UNO."""
    global _uno_button, _uno_button_cargado

    if _uno_button_cargado:
        return

    ruta = os.path.join("assets", "img", "uno_button.png")

    if os.path.exists(ruta):

        try:
            img = pygame.image.load(ruta).convert_alpha()

            # Tamaño del botón uno
            _uno_button = pygame.transform.smoothscale(img, (150, 110))

            _uno_button_cargado = True

            print("[UI] Botón UNO cargado.")

        except Exception as e:

            print(f"[UI] Error cargando botón UNO: {e}")

            _uno_button_cargado = True

    else:

        print("[UI] No se encontró uno_button.png")

        _uno_button_cargado = True


def draw_game(screen, game, clock):
    # PRINT DE DEPURACIÓN (solo una vez)
    if not hasattr(draw_game, "_init"):
        draw_game._init = True
        print("[UI] Iniciando dibujo con sistema de sprites...")

    # Cargar textura de fondo si no está cargada
    global _textura_fondo, _textura_fondo_cargada
    global _uno_button, _uno_button_cargado

    if not _textura_fondo_cargada:
        cargar_textura_fondo()

    if not _uno_button_cargado:
        cargar_boton_uno()

    font = pygame.font.SysFont("arial", 30)
    font_small = pygame.font.SysFont("arial", 24)
    font_big = pygame.font.SysFont("arial", 40)

    # Dibujar fondo (textura o color sólido)
    if _textura_fondo is not None:
        screen.blit(_textura_fondo, (0, 0))
    else:
        screen.fill(BACKGROUND)  # fallback al color rojo

    # Título y turno (mejorado: muestra el nombre)
    title = font.render("UNO NO MERCY", True, WHITE)
    # Asegurar que current_turn sea válido
    if game.current_turn < len(game.players):
        nombre_actual = game.players[game.current_turn].name
    else:
        nombre_actual = "Desconocido"
    turn_text = font.render(f"Turno: {nombre_actual}", True, WHITE)
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

    # NOMBRES DE JUGADORES CON RESALTADO (dinámico, sin índices fijos)
    # Posiciones de los nombres (basadas en el nombre del jugador)
    name_positions = {
        "Tú": (640, 490),
        "Bot 1": (50, 300),
        "Bot 2": (350, 70),
        "Bot 3": (1160, 300),
    }

    for player in game.players:
        nombre = player.name
        x, y = name_positions.get(nombre, (640, 490))  # posición por defecto

        if player == game.players[game.current_turn]:
            # Jugador activo: nombre grande, amarillo, con icono ▶
            texto = f"▶ {nombre}"
            shadow_surf = font_big.render(texto, True, (200, 180, 0))
            surf = font_big.render(texto, True, YELLOW)
            screen.blit(shadow_surf, (x - 2, y - 2))
            screen.blit(surf, (x, y))
        else:
            # Jugador inactivo: blanco normal
            surf = font.render(nombre, True, WHITE)
            screen.blit(surf, (x, y))

    # DORSOS DE BOTS (dinámico, basado en jugadores existentes)
    # Configuración de posición para cada bot (por nombre)
    bot_config = {
        "Bot 1": {
            "x": 150,
            "y": 220,
            "spacing": 25,
            "max_size": 400,
            "orientation": "vertical",
        },
        "Bot 2": {
            "x": 450,
            "y": 40,
            "spacing": 35,
            "max_size": 500,
            "orientation": "horizontal",
        },
        "Bot 3": {
            "x": 1050,
            "y": 220,
            "spacing": 25,
            "max_size": 400,
            "orientation": "vertical",
        },
    }

    for player in game.players:
        if player.name == "Tú":
            continue  # Saltar al jugador humano

        config = bot_config.get(player.name)
        if config is None:
            continue  # Si no está configurado, saltar

        hand = player.hand
        total = len(hand)
        if total == 0:
            continue

        x_base = config["x"]
        y_base = config["y"]
        spacing = config["spacing"]
        max_size = config["max_size"]

        if config["orientation"] == "vertical":
            if total * spacing <= max_size:
                cols = 1
            else:
                cols = 2
            if cols == 1:
                for i in range(total):
                    y = y_base + i * spacing
                    draw_card(
                        screen, None, x_base, y, 60, 90, border_radius=8, border_width=2
                    )
            else:
                half = (total + 1) // 2
                x1, x2 = x_base, x_base + 35
                for i in range(total):
                    y = y_base + (i % half) * spacing
                    x = x1 if i < half else x2
                    draw_card(
                        screen, None, x, y, 60, 90, border_radius=8, border_width=2
                    )
        else:  # horizontal
            if total * spacing <= max_size:
                rows = 1
            else:
                rows = 2
            if rows == 1:
                for i in range(total):
                    x = x_base + i * spacing
                    draw_card(
                        screen, None, x, y_base, 60, 90, border_radius=8, border_width=2
                    )
            else:
                half = (total + 1) // 2
                y1, y2 = y_base, y_base + 20
                for i in range(total):
                    x = x_base + (i % half) * spacing
                    y = y1 if i < half else y2
                    draw_card(
                        screen, None, x, y, 60, 90, border_radius=8, border_width=2
                    )
    # ------------------------------------------------------------
    # CARTAS DEL JUGADOR (CON APILAMIENTO DINÁMICO)
    # ------------------------------------------------------------
    player = game.players[0]
    total = len(player.hand)
    if total > 0:
        x_start = 300
        y_base = 520
        card_width = 90
        card_height = 140
        max_width = 900
        spacing = 95
        rows = 1

        # Calcular espaciado horizontal
        if total * spacing > max_width:
            spacing = max(45, max_width // total)  # 🔥 mínimo 45px
            if spacing < 50:  # Si es muy pequeño, forzar dos filas
                rows = 2

        # Determinar número de filas
        if rows == 1:
            y_positions = [y_base]
            per_row = [total]
        else:
            # 🔥 Separación vertical aumentada a 70px
            y_positions = [y_base, y_base + 70]
            per_row = [(total + 1) // 2, total // 2]

        card_index = 0
        for row_idx in range(rows):
            y = y_positions[row_idx]
            x = x_start
            count = per_row[row_idx]
            for _ in range(count):
                if card_index >= total:
                    break
                card = player.hand[card_index]
                card.x = x
                card.y = y
                card.update_rect()  # 🔥 Actualizar rectángulo de colisión
                draw_card(
                    screen,
                    card,
                    x,
                    y,
                    card_width,
                    card_height,
                    border_radius=12,
                    border_width=3,
                )
                x += spacing
                card_index += 1

    # -------- OVERLAYS (llamadas a ui_overlays) --------
    from src.ui_overlays import (
        draw_decision_overlay,
        draw_penalty_response_overlay,
        draw_color_selection,
        draw_opponent_selection,
        draw_pending_penalty,
        draw_uno_report_overlay,
        draw_uno_popup,
        draw_sad_target_selection,
        draw_notification,
        draw_direction_indicator,
    )

    draw_decision_overlay(screen, game, font, font_small)
    draw_penalty_response_overlay(screen, game, font, font_big, font_small)

    if game.game_state == "SELECTING_COLOR":
        draw_color_selection(screen, game, font_big, font)

    if game.game_state == "SELECTING_OPPONENT":
        draw_opponent_selection(screen, game, font_big, font)

    if game.game_state == "SELECTING_SAD_TARGET":
        draw_sad_target_selection(screen, game, font_big, font)

    # Botón UNO
    game.uno_button_rect = pygame.Rect(1135, 575, 150, 110)

    if _uno_button is not None:
        if game.uno_button_pressed:
            pressed = _uno_button.copy()
            pressed.fill((180, 180, 180, 255), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(pressed, game.uno_button_rect.topleft)
        else:
            screen.blit(_uno_button, game.uno_button_rect.topleft)

    # Ganador
    if game.winner is not None:
        winner_text = font_big.render(f"{game.winner.name} WINS!", True, YELLOW)
        screen.blit(winner_text, (560, 180))

    # Penalización pendiente (indicador general)
    draw_pending_penalty(screen, game, font)

    # Ventana de denuncia UNO
    draw_uno_report_overlay(screen, game)

    # globo de texto UNO!
    draw_uno_popup(screen, game)

    # Notificaciones visuales (se dibujan encima de todo)
    draw_notification(screen, game, font_big)

    # Indicador de dirección
    draw_direction_indicator(screen, game, font)

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
