"""
Sistema UNO:
- Detectar cuando un jugador queda con una carta.
- Manejar la ventana de tiempo para decir UNO.
"""

from src.rules import is_valid_play


def check_uno(game):
    """
    Revisa si algún jugador quedó exactamente con una carta.
    """

    if game.uno_event_active:
        return

    for player in game.players:

        if len(player.hand) == 1:

            if game.uno_player is player:
                return

            game.uno_player = player
            game.uno_event_active = True
            game.uno_timer = 0.0

            if player.is_human and game.uno_predeclared:
                game.uno_declared = True
                game.uno_predeclared = False
                game.uno_window_open = False
                print("[UNO] Declaración anticipada válida.")
            else:
                game.uno_declared = False
                game.uno_window_open = True

                if not player.is_human:
                    import random

                    if random.random() < 0.80:
                        player.uno_said = True
                        game.play_uno_sound()
                        print(f"[UNO] {player.name} dijo UNO.")
                    else:
                        player.uno_said = False
                        print(f"[UNO] {player.name} olvidó decir UNO.")

            if game.uno_window_open and not player.uno_said:
                start_report_window(game, player)

            # 🔥 CORRECCIÓN: mensaje dinámico sin índices fijos
            manos_info = []
            for p in game.players:
                manos_info.append(f"{p.name}:{len(p.hand)}")
            print(f"[UNO] {player.name} tiene una carta. " + " ".join(manos_info))

            return

    for player in game.players:
        if len(player.hand) != 1:
            player.uno_said = False

    game.uno_player = None
    game.uno_event_active = False
    game.uno_window_open = False


def update_uno(game, dt):

    # -------------------------
    # Ventana para declarar UNO
    # -------------------------
    if game.uno_window_open:

        game.uno_timer += dt

        if game.uno_timer >= game.uno_timeout:

            game.uno_window_open = False

            if game.uno_player is not None:
                print(f"[UNO] Tiempo agotado para {game.uno_player.name}")

    # -------------------------
    # Ventana de denuncia
    # -------------------------
    if game.denounce_window_open:

        game.denounce_timer += dt

        # ---------------------------------
        # Bots denuncian automáticamente
        # ---------------------------------
        if (
            game.denounce_player is not None
            and game.denounce_player.is_human
            and not game.bot_denounced
            and game.denounce_timer >= game.bot_denounce_delay
        ):

            import random

            if random.random() < 0.8:

                game.bot_denounced = True

                print("[UNO] Un bot te denunció.")

                apply_uno_penalty(game)

                return

        # ---------------------------------
        # Tiempo agotado
        # ---------------------------------
        if game.denounce_timer >= game.denounce_timeout:

            game.denounce_window_open = False
            game.denounce_player = None

            game.uno_event_active = False
            game.uno_player = None

            print("[UNO] Tiempo de denuncia terminado.")


def start_report_window(game, player):
    game.denounce_player = player
    game.denounce_timer = 0.0
    game.denounce_window_open = True
    game.bot_denounced = False

    print(f"[UNO] {player.name} puede ser denunciado.")


def apply_uno_penalty(game):
    """
    Aplica la penalización de +2 cartas al jugador denunciado.
    """

    player = game.denounce_player

    if player is None:
        return

    print(f"[UNO] {player.name} roba 2 cartas por no decir UNO.")

    game._apply_draw_penalty(player.hand, 2)

    # Cerrar ventana de denuncia
    game.denounce_window_open = False
    game.denounce_player = None
    game.denounce_timer = 0.0

    # Reiniciar sistema UNO
    game.uno_player = None
    game.uno_window_open = False
    game.uno_declared = False
    game.uno_predeclared = False
    game.uno_timer = 0.0

    game.uno_event_active = False


def declare_uno(game):
    """
    El jugador humano puede declarar UNO:
    1. Antes de jugar (si tiene 2 cartas y al menos una es jugable).
    2. Después de jugar (si ya tiene 1 carta y sigue abierta la ventana de denuncia).
    """

    player = game.players[0]

    # ---------------------------------
    # Caso A: declaración anticipada
    # ---------------------------------
    if len(player.hand) == 2:

        can_play = any(is_valid_play(card, game.center_card) for card in player.hand)

        if not can_play:
            print("[UNO] No puedes declarar UNO: no tienes cartas jugables.")
            return

        game.uno_predeclared = True
        player.uno_said = True
        game.play_uno_sound()
        print("[UNO] Declaraste UNO antes de jugar.")

        return

    # ---------------------------------
    # Caso B: declaración después de jugar
    # ---------------------------------
    if (
        len(player.hand) == 1
        and game.denounce_window_open
        and game.denounce_player == player
    ):

        game.uno_declared = True

        game.denounce_window_open = False
        game.denounce_player = None
        game.denounce_timer = 0.0

        game.uno_event_active = False
        game.uno_player = None
        player.uno_said = True
        game.play_uno_sound()
        print("[UNO] Declaraste UNO a tiempo.")
        return

    print("[UNO] No puedes declarar UNO en este momento.")
