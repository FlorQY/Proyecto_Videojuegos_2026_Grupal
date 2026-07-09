"""
Inteligencia artificial de los bots.
Todas las funciones reciben `game` como primer argumento.
"""

from src.rules import is_valid_play, get_effect
from src.turn_manager import advance_turn


def bot_play(game, player):
    """Lógica de juego para un bot: elige carta válida con prioridad estratégica."""
    print(f"[BOT] Turno de {player.name}")

    valid_indices = []
    for i, card in enumerate(player.hand):
        if is_valid_play(card, game.center_card):
            valid_indices.append(i)

    if valid_indices:
        # Clasificar cartas válidas por prioridad
        # Prioridad: comodines > acciones > numéricas
        wild_cards = []
        action_cards = []
        number_cards = []

        for idx in valid_indices:
            card = player.hand[idx]
            if card.color == "Wild":
                wild_cards.append(idx)
            elif get_effect(card) is not None:
                action_cards.append(idx)
            else:
                number_cards.append(idx)

        # Elegir según prioridad
        if wild_cards:
            chosen_idx = wild_cards[0]
            print(f"[BOT] {player.name} elige comodín: {player.hand[chosen_idx]}")
        elif action_cards:
            chosen_idx = action_cards[0]
            print(
                f"[BOT] {player.name} elige carta de acción: {player.hand[chosen_idx]}"
            )
        else:
            chosen_idx = number_cards[0]
            print(
                f"[BOT] {player.name} elige carta numérica: {player.hand[chosen_idx]}"
            )

        # Importación local para evitar circularidad
        from src.action_manager import play_card

        play_card(game, player, chosen_idx)
        return

    # No tiene carta válida: roba
    print(f"[BOT] {player.name} no tiene carta válida, roba.")
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
