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

    # Reiniciar el temporizador del bot para que siempre espere
    # cuando llegue su turno (evita que actúe demasiado rápido)
    game.bot_timer = 0

    old = game.current_turn
    game.current_turn = get_next_turn(game)
    print(f"[TURNO] Avanzando: {old} -> {game.current_turn} (dir={game.direction})")
    # Mostrar nombre y tamaño de mano del jugador que inicia turno
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
    """
    Elimina jugadores con 25 o más cartas (regla Piedad).
    Retorna True si algún jugador fue eliminado.
    """
    eliminated = []
    for player in game.players:
        if len(player.hand) >= 25:
            eliminated.append(player)
            print(f"[PIEDAD] {player.name} eliminado con {len(player.hand)} cartas.")
            game.show_notification(
                f"{player.name} eliminado (25+ cartas)", (255, 100, 100), 2.0  # rojo
            )

    for player in eliminated:
        # Eliminar al jugador de la lista
        game.players.remove(player)
        # Si solo queda un jugador, es el ganador
        if len(game.players) == 1:
            game.winner = game.players[0]
            game.game_state = "GAME_OVER"
            print(f"[VICTORIA] {game.winner.name} gana por Piedad.")
            return True

    # Si se eliminó a alguien pero queda más de un jugador, ajustar turno
    if eliminated:
        # 🔥 Verificar que pending_victim sea válido (no apunte a un jugador eliminado)
        if game.pending_victim is not None:
            if game.pending_victim >= len(game.players):
                game.pending_victim = None
                print(
                    "[PIEDAD] pending_victim reseteado porque el jugador fue eliminado."
                )

        # Si el turno actual es un índice que ya no existe, resetear a 0
        if game.current_turn >= len(game.players):
            game.current_turn = 0

        print(f"[PIEDAD] Turno actual ajustado a {game.current_turn}.")

    return len(eliminated) > 0
