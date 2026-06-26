import pygame
import sys
from src.game import Game
from src.ui import draw_game


def main():
    pygame.init()

    WIDTH = 1280
    HEIGHT = 720
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("UNO No Mercy")
    clock = pygame.time.Clock()

    # Crear instancia del juego
    game = Game()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time en segundos (no usado aún)

        # Eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Pasar el evento al juego
            game.handle_event(event)

        # Actualización
        game.update(dt)

        # Dibujo
        draw_game(screen, game, clock)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
