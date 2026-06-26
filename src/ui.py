import pygame
import psutil
import os
import time

# Colores y constantes
BACKGROUND = (120, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)

CARD_COLORS = {
    "Red": (220, 50, 50),
    "Blue": (50, 80, 220),
    "Green": (50, 180, 80),
    "Yellow": (240, 210, 50),
    "Wild": (20, 20, 20),
}


def draw_game(screen, game, clock):
    font = pygame.font.SysFont("arial", 30)

    # Fondo
    screen.fill(BACKGROUND)

    # Título y turno
    title = font.render("UNO NO MERCY", True, WHITE)
    turn_text = font.render(f"TURN: {game.current_turn}", True, WHITE)
    screen.blit(title, (20, 20))
    screen.blit(turn_text, (20, 60))

    # Círculo decorativo central
    pygame.draw.circle(screen, (180, 120, 0), (640, 360), 130, 12)

    # Carta central
    center_color = CARD_COLORS.get(game.center_card.color, (100, 100, 100))
    pygame.draw.rect(screen, center_color, (590, 285, 100, 150), border_radius=10)
    pygame.draw.rect(screen, WHITE, (590, 285, 100, 150), 3, border_radius=10)
    center_text = font.render(f"{game.center_card.value}", True, WHITE)
    screen.blit(center_text, (632, 340))

    # Mazo
    deck_rect = pygame.Rect(280, 150, 100, 150)
    pygame.draw.rect(screen, BLACK, deck_rect, border_radius=10)
    deck_text = font.render("UNO", True, WHITE)
    screen.blit(deck_text, (300, 210))
    # Guardamos el rect para usarlo en eventos (desde game)
    game._deck_rect = deck_rect

    # Nombres de los bots (con color según turno)
    bot_colors = [WHITE, WHITE, WHITE]
    if game.current_turn == 1:
        bot_colors[0] = (255, 220, 0)
    elif game.current_turn == 2:
        bot_colors[1] = (255, 220, 0)
    elif game.current_turn == 3:
        bot_colors[2] = (255, 220, 0)

    bot1 = font.render("BOT 1", True, bot_colors[0])
    bot2 = font.render("BOT 2", True, bot_colors[1])
    bot3 = font.render("BOT 3", True, bot_colors[2])
    screen.blit(bot1, (50, 300))
    screen.blit(bot2, (800, 80))
    screen.blit(bot3, (1160, 300))

    # Cartas de los bots (dorsos)
    # Bot 2 (arriba, horizontal)
    x_bot2 = 450
    for _ in game.players[2].hand:
        pygame.draw.rect(screen, BLACK, (x_bot2, 40, 60, 90), border_radius=10)
        pygame.draw.rect(screen, WHITE, (x_bot2, 40, 60, 90), 2, border_radius=10)
        x_bot2 += 35

    # Bot 1 (izquierda, vertical)
    y_bot1 = 220
    for _ in game.players[1].hand:
        pygame.draw.rect(screen, BLACK, (150, y_bot1, 60, 90), border_radius=10)
        pygame.draw.rect(screen, WHITE, (150, y_bot1, 60, 90), 2, border_radius=10)
        y_bot1 += 25

    # Bot 3 (derecha, vertical)
    y_bot3 = 220
    for _ in game.players[3].hand:
        pygame.draw.rect(screen, BLACK, (1050, y_bot3, 60, 90), border_radius=10)
        pygame.draw.rect(screen, WHITE, (1050, y_bot3, 60, 90), 2, border_radius=10)
        y_bot3 += 25

    # Cartas del jugador (abajo)
    player = game.players[0]
    x = 300
    for card in player.hand:
        card.x = x
        card.y = 520
        card.update_rect()

        card_color = CARD_COLORS.get(card.color, (100, 100, 100))
        pygame.draw.rect(screen, card_color, (x, 520, 90, 140), border_radius=12)
        pygame.draw.rect(screen, WHITE, (x, 520, 90, 140), 3, border_radius=12)
        value_text = font.render(card.value, True, WHITE)
        screen.blit(value_text, (x + 40, 575))
        x += 95

    # Botón UNO (visual)
    pygame.draw.circle(screen, (220, 40, 40), (1180, 620), 45)
    pygame.draw.circle(screen, WHITE, (1180, 620), 45, 4)
    uno_text = font.render("UNO", True, WHITE)
    screen.blit(uno_text, (1153, 603))

    # Ganador
    if game.winner is not None:
        winner_text = font.render(f"{game.winner.name} WINS!", True, WHITE)
        screen.blit(winner_text, (560, 180))

    # 🔥 Indicador de penalización pendiente
    draw_pending_penalty(screen, game, font)

    # Métricas técnicas
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


def draw_pending_penalty(screen, game, font):
    """
    Dibuja un indicador visual de la penalización pendiente sobre el jugador afectado.
    Parpadea usando time.time().
    """
    if game.pending_draws > 0 and game.pending_victim is not None:
        # Posición según el jugador afectado (usamos el índice)
        if game.pending_victim == 0:  # Jugador humano
            x, y = 640, 680
        elif game.pending_victim == 1:  # Bot 1 (izquierda)
            x, y = 80, 350
        elif game.pending_victim == 2:  # Bot 2 (arriba)
            x, y = 640, 50
        else:  # Bot 3 (derecha)
            x, y = 1200, 350

        # Texto con el número de cartas a robar
        text = f"¡+{game.pending_draws}!"
        penalty_text = font.render(text, True, (255, 0, 0))  # Rojo intenso
        text_rect = penalty_text.get_rect(center=(x, y))

        # Efecto de parpadeo (cada 0.5 segundos)
        if int(time.time() * 2) % 2 == 0:
            # Fondo semitransparente para resaltar
            s = pygame.Surface(text_rect.inflate(20, 10).size, pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            screen.blit(s, text_rect.inflate(20, 10).topleft)
            # Dibujar el texto
            screen.blit(penalty_text, text_rect)
