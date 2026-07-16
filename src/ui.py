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

# Dorso de carta y mazo
_dorso_sprite = None
_dorso_cargado = False
_mazo_sprite = None
_mazo_cargado = False

_menu_fondo = None
_menu_fondo_cargada = False

# Imagen de las Reglas
_rules_image = None
_rules_image_loaded = False
_rules_image_height = 0
_rules_image_width = 0
MENU_RED = (200, 0, 0)

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
        global _dorso_sprite, _dorso_cargado
        if not _dorso_cargado:
            cargar_dorso()

        if _dorso_sprite is not None:
            # Escalar el sprite al tamaño deseado
            scaled_dorso = pygame.transform.smoothscale(_dorso_sprite, (width, height))
            if shadow:
                shadow_rect = pygame.Rect(x + 3, y + 3, width, height)
                pygame.draw.rect(
                    screen, (0, 0, 0, 50), shadow_rect, border_radius=border_radius
                )
            screen.blit(scaled_dorso, (x, y))
            return
        else:
            # Fallback: rectángulo negro con borde blanco
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

    # Si la carta es un comodín (valor especial), usar sprite de comodín con color "Wild"
    wild_values = ["+4 Reverse", "+6", "+10", "Color Roulette"]
    if card.value in wild_values:
        sprite = get_scaled_sprite(card, width, height, force_color="Wild")
    else:
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


def cargar_dorso():
    global _dorso_sprite, _dorso_cargado
    if _dorso_cargado:
        return

    ruta = os.path.join("assets", "img", "cards", "carta_volteada.png")
    if os.path.exists(ruta):
        try:
            img = pygame.image.load(ruta).convert_alpha()
            # Aplicar redondeo de esquinas (opcional)
            from src.sprite_loader import _round_corners

            _dorso_sprite = _round_corners(img, 10)
            _dorso_cargado = True
            print("[UI] Dorso de carta cargado.")
        except Exception as e:
            print(f"[UI] Error cargando dorso: {e}")
            _dorso_cargado = True
    else:
        print("[UI] No se encontró carta_volteada.png, usando rectángulo negro.")
        _dorso_cargado = True


def cargar_mazo():
    """Carga la imagen del mazo y aplica bordes redondeados."""
    global _mazo_sprite, _mazo_cargado
    if _mazo_cargado:
        return

    ruta = os.path.join("assets", "img", "cards", "carta_volteada.png")
    if os.path.exists(ruta):
        try:
            from src.sprite_loader import _round_corners

            img = pygame.image.load(ruta).convert_alpha()
            # Aplicar redondeo de esquinas como a las cartas normales
            img = _round_corners(img, 10)
            # Escalar al tamaño del mazo (100x150)
            _mazo_sprite = pygame.transform.smoothscale(img, (100, 150))
            _mazo_cargado = True
            print("[UI] Mazo cargado con bordes redondeados.")
        except Exception as e:
            print(f"[UI] Error cargando mazo: {e}")
            _mazo_cargado = True
    else:
        print("[UI] No se encontró mazo.png, usando rectángulo negro.")
        _mazo_cargado = True


def cargar_menu_fondo():
    global _menu_fondo, _menu_fondo_cargada
    if _menu_fondo_cargada:
        return
    ruta = os.path.join("assets", "img", "menu_bg.png")
    if os.path.exists(ruta):
        try:
            img = pygame.image.load(ruta).convert()
            _menu_fondo = pygame.transform.scale(img, (1280, 720))
            _menu_fondo_cargada = True
            print("[UI] Fondo de menú cargado.")
        except Exception as e:
            print(f"[UI] Error cargando fondo de menú: {e}")
            _menu_fondo_cargada = True
    else:
        print("[UI] No se encontró menu_bg.png, usando color negro.")
        _menu_fondo_cargada = True


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

    # Mazo (con efecto de pila de 3 cartas)
    deck_rect = pygame.Rect(280, 150, 100, 150)
    game._deck_rect = deck_rect

    global _mazo_sprite, _mazo_cargado
    if not _mazo_cargado:
        cargar_mazo()

    # Función auxiliar para dibujar una carta del mazo (sprite o fallback)
    def dibujar_carta_mazo(x, y):
        if _mazo_sprite is not None:
            screen.blit(_mazo_sprite, (x, y))
        else:
            # Fallback: rectángulo negro con borde blanco
            pygame.draw.rect(screen, BLACK, (x, y, 100, 150), border_radius=10)
            pygame.draw.rect(screen, WHITE, (x, y, 100, 150), 2, border_radius=10)
            deck_text = font.render("UNO", True, WHITE)
            screen.blit(deck_text, (x + 25, y + 55))

    # Dibujar tres capas para simular pila de cartas
    dibujar_carta_mazo(deck_rect.x - 20, deck_rect.y - 18)
    dibujar_carta_mazo(deck_rect.x - 18, deck_rect.y - 14)
    dibujar_carta_mazo(deck_rect.x - 14, deck_rect.y - 10)
    dibujar_carta_mazo(deck_rect.x - 12, deck_rect.y - 8)
    dibujar_carta_mazo(deck_rect.x - 6, deck_rect.y - 4)
    dibujar_carta_mazo(deck_rect.x, deck_rect.y)

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
            # 🔥 Separación vertical aumentada a 100px para mejorar detección de clics
            y_positions = [y_base, y_base + 100]
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
        draw_notification,
        draw_direction_indicator,
        draw_roulette_color_selection,
    )

    draw_decision_overlay(screen, game, font, font_small)
    draw_penalty_response_overlay(screen, game, font, font_big, font_small)

    if game.game_state == "SELECTING_COLOR":
        draw_color_selection(screen, game, font_big, font)

    if game.game_state == "SELECTING_OPPONENT":
        draw_opponent_selection(screen, game, font_big, font)

    if game.game_state == "SELECTING_ROULETTE_COLOR":
        draw_roulette_color_selection(screen, game, font_big, font)

    # Botón UNO
    game.uno_button_rect = pygame.Rect(1135, 575, 150, 110)

    if _uno_button is not None:
        if game.uno_button_pressed:
            pressed = _uno_button.copy()
            pressed.fill((180, 180, 180, 255), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(pressed, game.uno_button_rect.topleft)
        else:
            screen.blit(_uno_button, game.uno_button_rect.topleft)

    # GAME OVER / VICTORIA
    if game.game_state == "GAME_OVER":
        # Fondo semitransparente negro que cubre toda la pantalla
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Determinar mensaje y color según el estado
        if game.human_lost:
            msg = "¡GAME OVER! Has sido eliminado."
            color = RED
        elif game.winner is not None:
            if game.winner.is_human:
                msg = "¡FELICIDADES! ¡HAS GANADO!"
                color = (50, 255, 50)
            else:
                msg = f"{game.winner.name} WINS!"
                color = YELLOW
        else:
            msg = "GAME OVER"
            color = WHITE

        # Mostrar mensaje
        game_over_text = font_big.render(msg, True, color)
        text_rect = game_over_text.get_rect(center=(640, 180))
        bg_rect = text_rect.inflate(40, 20)
        s = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        screen.blit(s, bg_rect.topleft)
        screen.blit(game_over_text, text_rect)

        # ------ BOTONES DE GAME OVER ------
        font_button = pygame.font.SysFont("arial", 28)
        btn_width = 220
        btn_height = 50
        spacing = 30
        total_width = 2 * btn_width + spacing
        start_x = 640 - total_width // 2
        y = 620

        # Botón Reintentar
        rect_retry = pygame.Rect(start_x, y, btn_width, btn_height)
        pygame.draw.rect(screen, BLACK, rect_retry, border_radius=10)
        pygame.draw.rect(screen, (200, 0, 0), rect_retry, 3, border_radius=10)
        text_retry = font_button.render("REINTENTAR", True, (200, 0, 0))
        text_retry_rect = text_retry.get_rect(center=rect_retry.center)
        screen.blit(text_retry, text_retry_rect)
        game.btn_retry_rect = rect_retry

        # Botón Volver al Menú
        rect_menu = pygame.Rect(start_x + btn_width + spacing, y, btn_width, btn_height)
        pygame.draw.rect(screen, BLACK, rect_menu, border_radius=10)
        pygame.draw.rect(screen, (200, 0, 0), rect_menu, 3, border_radius=10)
        text_menu = font_button.render("VOLVER AL MENÚ", True, (200, 0, 0))
        text_menu_rect = text_menu.get_rect(center=rect_menu.center)
        screen.blit(text_menu, text_menu_rect)
        game.btn_menu_rect = rect_menu

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


def draw_menu(screen):
    global _menu_fondo, _menu_fondo_cargada
    if not _menu_fondo_cargada:
        cargar_menu_fondo()

    if _menu_fondo is not None:
        screen.blit(_menu_fondo, (0, 0))
    else:
        screen.fill((0, 0, 0))  # negro como fallback

    font_button = pygame.font.SysFont("arial", 36)

    button_width = 250
    button_height = 60
    spacing = 25
    start_y = 300

    # Nueva Partida
    rect_nueva = pygame.Rect(
        640 - button_width // 2, start_y, button_width, button_height
    )
    pygame.draw.rect(screen, BLACK, rect_nueva, border_radius=10)
    pygame.draw.rect(screen, MENU_RED, rect_nueva, 3, border_radius=10)
    text_nueva = font_button.render("NUEVA PARTIDA", True, MENU_RED)
    text_nueva_rect = text_nueva.get_rect(center=rect_nueva.center)
    screen.blit(text_nueva, text_nueva_rect)

    # Reglas
    rect_reglas = pygame.Rect(
        640 - button_width // 2,
        start_y + button_height + spacing,
        button_width,
        button_height,
    )
    pygame.draw.rect(screen, BLACK, rect_reglas, border_radius=10)
    pygame.draw.rect(screen, MENU_RED, rect_reglas, 3, border_radius=10)
    text_reglas = font_button.render("REGLAS", True, MENU_RED)
    text_reglas_rect = text_reglas.get_rect(center=rect_reglas.center)
    screen.blit(text_reglas, text_reglas_rect)

    # Salir
    rect_salir = pygame.Rect(
        640 - button_width // 2,
        start_y + 2 * (button_height + spacing),
        button_width,
        button_height,
    )
    pygame.draw.rect(screen, BLACK, rect_salir, border_radius=10)
    pygame.draw.rect(screen, MENU_RED, rect_salir, 3, border_radius=10)
    text_salir = font_button.render("SALIR", True, MENU_RED)
    text_salir_rect = text_salir.get_rect(center=rect_salir.center)
    screen.blit(text_salir, text_salir_rect)

    return (rect_nueva, rect_reglas, rect_salir)


def draw_rules(screen, scroll_y):
    global _rules_image, _rules_image_loaded, _rules_image_height, _rules_image_width
    global _menu_fondo, _menu_fondo_cargada

    if not _menu_fondo_cargada:
        cargar_menu_fondo()

    if _menu_fondo is not None:
        screen.blit(_menu_fondo, (0, 0))
    else:
        screen.fill((0, 0, 0))  # Fondo negro para menú

    if not _rules_image_loaded:
        ruta = os.path.join("assets", "img", "rules.png")
        if os.path.exists(ruta):
            try:
                img = pygame.image.load(ruta).convert_alpha()
                original_width, original_height = img.get_size()
                # Nuevo ancho deseado (800 píxeles en lugar de 1280)
                new_width = 800
                scale_factor = new_width / original_width
                new_height = int(original_height * scale_factor)
                _rules_image = pygame.transform.smoothscale(
                    img, (new_width, new_height)
                )
                _rules_image_height = new_height
                # Guardar también el ancho para centrar
                _rules_image_width = new_width
            except Exception as e:
                print(f"[UI] Error cargando reglas: {e}")
                _rules_image = None
                _rules_image_height = 0
                _rules_image_width = 0
        else:
            _rules_image = None
            _rules_image_height = 0
            _rules_image_width = 0
        _rules_image_loaded = True

    if _rules_image is not None:
        max_scroll = max(0, _rules_image_height - 720)
        if scroll_y < 0:
            scroll_y = 0
        elif scroll_y > max_scroll:
            scroll_y = max_scroll

        visible_rect = pygame.Rect(0, scroll_y, _rules_image_width, 720)
        # Centrar horizontalmente
        x_offset = (1280 - _rules_image_width) // 2
        screen.blit(_rules_image, (x_offset, 0), visible_rect)
    else:
        font_error = pygame.font.SysFont("arial", 40)
        error_text = font_error.render("No se encontró la imagen de reglas.", True, RED)
        error_rect = error_text.get_rect(center=(640, 360))
        screen.blit(error_text, error_rect)

    font_button = pygame.font.SysFont("arial", 30)
    rect_volver = pygame.Rect(1100, 650, 160, 50)
    pygame.draw.rect(screen, BLACK, rect_volver, border_radius=10)
    pygame.draw.rect(screen, MENU_RED, rect_volver, 3, border_radius=10)
    text_volver = font_button.render("VOLVER", True, MENU_RED)
    text_volver_rect = text_volver.get_rect(center=rect_volver.center)
    screen.blit(text_volver, text_volver_rect)

    return rect_volver, scroll_y
