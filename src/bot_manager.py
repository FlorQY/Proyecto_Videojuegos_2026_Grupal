"""
Inteligencia artificial de los bots.
Todas las funciones reciben `game` como primer argumento.
"""

from src.rules import is_valid_play
from src.turn_manager import advance_turn


def bot_play(game, player):
    """Lógica de juego para un bot: elige carta válida o roba."""
    print(f"[BOT] Turno de {player.name}")

    valid_indices = []
    for i, card in enumerate(player.hand):
        if is_valid_play(card, game.center_card):
            valid_indices.append(i)

    if valid_indices:
        index = valid_indices[0]
        print(f"[BOT] {player.name} juega {player.hand[index]}")
        # Importación local para evitar circularidad
        from src.action_manager import play_card

        play_card(game, player, index)
        return

    print(f"[BOT] {player.name} no tiene carta valida, roba.")
    if len(game.deck.cards) > 0:
        drawn = player.draw_card(game.deck)
        if drawn is not None:
            if is_valid_play(drawn, game.center_card):
                print(f"[BOT] {player.name} juega la carta robada: {drawn}")
                idx = len(player.hand) - 1
                from src.action_manager import play_card

                play_card(game, player, idx)
            else:
                print(f"[BOT] {player.name} guarda la carta robada.")
                advance_turn(game)
        else:
            advance_turn(game)
    else:
        advance_turn(game)
