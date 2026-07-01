"""
Gestión de turnos y verificación de ganador.
Todas las funciones reciben `game` como primer argumento.
"""


def get_next_turn(game):
    """Calcula el siguiente índice de jugador según la dirección."""
    next_turn = game.current_turn + game.direction
    if next_turn > 3:
        next_turn = 0
    elif next_turn < 0:
        next_turn = 3
    return next_turn


def advance_turn(game):
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
