"""
Gestión de turnos y verificación de ganador.
Todas las funciones reciben `game` como primer argumento.
"""

from src.uno_manager import check_uno


def get_next_turn(game):
    n = len(game.players)
    if n == 0:
        return 0  # No debería ocurrir, pero por seguridad
    next_turn = game.current_turn + game.direction
    if next_turn >= n:
        next_turn = 0
    elif next_turn < 0:
        next_turn = n - 1
    return next_turn


def advance_turn(game):
    # Antes de cambiar el turno revisamos si alguien quedó con una carta
    check_uno(game)

    # Reiniciar el temporizador del bot
    game.bot_timer = 0

    # LOG: estado de penalización pendiente
    if game.pending_draws > 0 and game.pending_victim is not None:
        victim_name = (
            game.players[game.pending_victim].name
            if game.pending_victim < len(game.players)
            else "INVÁLIDO"
        )
        print(
            f"[TURNO AVANCE] Penalización pendiente: {game.pending_draws} cartas para {victim_name} (current_turn={game.current_turn})"
        )

    old = game.current_turn
    game.current_turn = get_next_turn(game)
    print(f"[TURNO] Avanzando: {old} -> {game.current_turn} (dir={game.direction})")
    current_player = game.players[game.current_turn]
    print(f"[TURNO] Turno de {current_player.name} ({len(current_player.hand)} cartas)")


def check_winner(game):
    """Verifica si algún jugador se quedó sin cartas y actualiza el estado."""
    for player in game.players:
        if len(player.hand) == 0:
            game.winner = player
            game.game_state = "GAME_OVER"
            print(f"[VICTORIA] {player.name} ha ganado!")
            return True
    return False


def check_pity(game):
    eliminated = []
    human_eliminated = False

    for player in game.players:
        if len(player.hand) >= 25:
            eliminated.append(player)
            if player.is_human:
                human_eliminated = True
                print(
                    f"[PIEDAD] {player.name} eliminado con {len(player.hand)} cartas."
                )
                game.show_notification(
                    f"{player.name} eliminado (25+ cartas)", (255, 100, 100), 2.0
                )

    if human_eliminated:
        game.human_lost = True
        game.winner = None
        game.game_state = "GAME_OVER"
        # Limpiar penalización pendiente si apuntaba al humano
        if game.pending_victim is not None and game.pending_victim < len(game.players):
            if game.players[game.pending_victim].is_human:
                game.pending_draws = 0
                game.pending_victim = None
                game.last_penalty_value = 0
        print("[GAME OVER] Has sido eliminado por Piedad.")
        return True

    # Eliminar bots
    for player in eliminated:
        game.players.remove(player)
        if len(game.players) == 1:
            game.winner = game.players[0]
            game.game_state = "GAME_OVER"
            print(f"[VICTORIA] {game.winner.name} gana por Piedad.")
            return True

    # Ajustar penalización pendiente si la víctima fue eliminada
    if eliminated:
        if game.pending_victim is not None:
            if game.pending_victim >= len(game.players):
                print("[PIEDAD] La víctima de penalización fue eliminada. Limpiando.")
                game.pending_draws = 0
                game.pending_victim = None
                game.last_penalty_value = 0

        if game.current_turn >= len(game.players):
            game.current_turn = 0
        print(f"[PIEDAD] Turno actual ajustado a {game.current_turn}.")

    return len(eliminated) > 0
