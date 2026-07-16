import pygame
import sys
from src.game import Game
from src.ui import draw_game, draw_menu, draw_rules


def play_menu_music():
    pygame.mixer.music.load("assets/sounds/menu_music.wav")
    pygame.mixer.music.play(-1)


def play_game_music():
    pygame.mixer.music.load("assets/sounds/game_music.wav")
    pygame.mixer.music.play(-1)


def stop_music():
    pygame.mixer.music.stop()


def main():
    pygame.init()
    pygame.mixer.init()

    WIDTH = 1280
    HEIGHT = 720
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("UNO No Mercy")
    clock = pygame.time.Clock()

    game = None
    menu_state = "MENU"
    scroll_y = 0
    current_music = "menu"
    play_menu_music()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if menu_state == "MENU":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    rect_nueva, rect_reglas, rect_salir = draw_menu(screen)
                    if rect_nueva.collidepoint(mouse_pos):
                        game = Game()
                        menu_state = "PLAYING"
                        if current_music != "game":
                            play_game_music()
                            current_music = "game"
                    elif rect_reglas.collidepoint(mouse_pos):
                        menu_state = "RULES"
                        scroll_y = 0
                    elif rect_salir.collidepoint(mouse_pos):
                        running = False

            elif menu_state == "RULES":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    rect_volver, _ = draw_rules(screen, scroll_y)
                    if rect_volver.collidepoint(mouse_pos):
                        menu_state = "MENU"
                        if current_music != "menu":
                            play_menu_music()
                            current_music = "menu"
                elif event.type == pygame.MOUSEWHEEL:
                    scroll_y -= event.y * 20
                    if scroll_y < 0:
                        scroll_y = 0

            else:  # PLAYING
                if game:
                    game.handle_event(event)

        if menu_state == "PLAYING" and game:
            game.update(dt)
            if game.return_to_menu:
                game.return_to_menu = False
                menu_state = "MENU"
                if current_music != "menu":
                    play_menu_music()
                    current_music = "menu"

        if menu_state == "MENU":
            draw_menu(screen)
        elif menu_state == "RULES":
            _, scroll_y = draw_rules(screen, scroll_y)
        else:
            if game:
                draw_game(screen, game, clock)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
