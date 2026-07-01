"""
Acciones del juego: jugar cartas, efectos, rotación, intercambio, selección de color.
Todas las funciones reciben `game` como primer argumento.
"""

from src.rules import is_valid_play, get_effect
from src.turn_manager import advance_turn, check_winner


def rotate_hands(game):
    """Rota todas las manos una posición en la dirección actual."""
    hands = [p.hand for p in game.players]
    new_hands = []

    if game.direction == 1:  # Horario: i recibe de i-1
        for i in range(4):
            new_hands.append(hands[(i - 1) % 4])
    else:  # Antihorario: i recibe de i+1
        for i in range(4):
            new_hands.append(hands[(i + 1) % 4])

    for i, player in enumerate(game.players):
        player.hand = new_hands[i]
        player.sort_hand()

    print(f"[ROTACION] Manos rotadas en dirección {game.direction}")


def apply_swap(game, player1, player2):
    """Intercambia las manos de dos jugadores."""
    player1.hand, player2.hand = player2.hand, player1.hand
    player1.sort_hand()
    player2.sort_hand()
    print(f"[INTERCAMBIO] Manos intercambiadas entre {player1.name} y {player2.name}")

    game.pending_swap_player = None
    game.opponent_rects = []
    game.opponent_indices = []
    game.game_state = "PLAYING"
    game.selection_timer = 0.0


def select_opponent(game, player):
    if player.is_human:
        game.pending_swap_player = player
        game.game_state = "SELECTING_OPPONENT"
        game.selection_timer = 0.0
        print("[INTERCAMBIO] Jugador humano debe elegir oponente.")
    else:
        # Bot: elige al oponente con menos cartas
        opponents = [p for p in game.players if p is not player]
        chosen = min(opponents, key=lambda p: len(p.hand))
        print(f"[INTERCAMBIO] {player.name} intercambia con {chosen.name}")
        apply_swap(game, player, chosen)
        # FIX: Avanzar turno para que el bot no repita el turno
        from src.turn_manager import advance_turn

        advance_turn(game)


def select_color(game, player, card, callback_type):
    """Inicia la selección de color para un comodín."""
    if player.is_human:
        game.pending_color_card = card
        game.pending_color_player = player
        game.pending_color_callback = callback_type
        game.game_state = "SELECTING_COLOR"
        game.selection_timer = 0.0
        print("[COLOR] Jugador humano debe elegir color.")
    else:
        chosen_color = player.choose_color()
        print(f"[COLOR] {player.name} elige color {chosen_color}")
        # CORRECCIÓN: Asignar atributos también para bots
        game.pending_color_card = card
        game.pending_color_player = player
        game.pending_color_callback = callback_type
        apply_color_and_continue(game, chosen_color)


def apply_color_and_continue(game, chosen_color):
    """Aplica el color elegido y continúa con el flujo pendiente."""
    if game.pending_color_card is None:
        print("[ERROR] apply_color_and_continue llamado sin pending_color_card.")
        return

    card = game.pending_color_card
    player = game.pending_color_player
    callback = game.pending_color_callback

    card.color = chosen_color
    print(f"[COLOR] Color aplicado: {chosen_color} a {card}")

    # Limpiar estado
    game.pending_color_card = None
    game.pending_color_player = None
    game.pending_color_callback = None
    game.color_rects = []
    game.game_state = "PLAYING"
    game.selection_timer = 0.0

    if callback == "play":
        game.center_card = card
        turn_modified = apply_effect(game, player, card)
        if check_winner(game):
            return
        if not turn_modified:
            advance_turn(game)

    elif callback == "response":
        # Encontrar el índice de la carta en la mano
        card_index = None
        for i, c in enumerate(player.hand):
            if c is card:
                card_index = i
                break
        if card_index is not None:
            player.play_card(card_index)
            from src.penalty_manager import execute_penalty_response

            execute_penalty_response(game, player, card, card_index)
        else:
            print("[ERROR] No se encontró la carta en la mano para respuesta.")


def apply_effect(game, player, card):
    """Aplica el efecto de una carta (Reverse, Skip, penalizaciones, 0, 7)."""
    effect = get_effect(card)
    print(f"[EFECTO] Carta {card.value} jugada por {player.name}, efecto={effect}")

    # Efectos especiales: 0 y 7
    if card.value == "0":
        rotate_hands(game)
        return False

    if card.value == "7":
        # La selección de oponente ya se maneja en play_card
        return False

    if effect == "Reverse":
        game.direction *= -1
        print(f"[REVERSE] Direccion ahora {game.direction}")
        return False

    elif effect == "Skip":
        advance_turn(game)
        return True

    elif effect in ["+2", "+4", "+6", "+10"]:
        amount = int(effect)
        # Importación local para evitar circularidad
        from src.penalty_manager import apply_attack

        apply_attack(game, amount, reverse=False)
        return False

    elif effect == "+4 Reverse":
        # Importación local para evitar circularidad
        from src.penalty_manager import apply_attack

        apply_attack(game, 4, reverse=True)
        return False

    return False


def play_card(game, player, card_index):
    """Ejecuta la jugada de una carta desde la mano."""
    if card_index >= len(player.hand):
        return False

    card = player.hand[card_index]
    if not is_valid_play(card, game.center_card):
        print(f"[JUGADA] {player.name} intento jugar {card} pero no es valida.")
        return False

    print(f"[JUGADA] {player.name} juega {card}")
    player.play_card(card_index)

    # Comodín: pedir color
    if card.color == "Wild":
        select_color(game, player, card, "play")
        return True

    # Carta 7: seleccionar oponente
    if card.value == "7":
        select_opponent(game, player)
        return True

    # Otras cartas
    game.center_card = card
    turn_modified = apply_effect(game, player, card)

    if check_winner(game):
        return True

    if not turn_modified:
        advance_turn(game)

    return True


def play_drawn_card(game):
    if game.drawn_card_temp is None:
        return False

    card = game.drawn_card_temp
    player = game.players[0]
    print(f"[JUGADA] Jugador juega carta robada: {card}")

    # Añadir a la mano y jugar
    player.hand.append(card)
    idx = len(player.hand) - 1
    print(f"[JUGADA] Mano antes de jugar: {len(player.hand)} cartas.")
    success = play_card(game, player, idx)
    print(f"[JUGADA] Mano después de jugar: {len(player.hand)} cartas.")

    # 🔥 FIX: Si la carta aún está en la mano, eliminarla (evita duplicación)
    if success and card in player.hand:
        player.hand.remove(card)
        print(
            "[FIX] Carta jugada eliminada manualmente de la mano (evita duplicación)."
        )

    # Limpiar estado de decisión
    game.drawn_card_temp = None
    game.waiting_for_decision = False
    game.decision_timer = 0.0

    return success


def keep_drawn_card(game):
    """Guarda la carta robada en la mano y avanza el turno."""
    if game.drawn_card_temp is None:
        return

    player = game.players[0]
    player.hand.append(game.drawn_card_temp)
    print(f"[DECISION] Carta {game.drawn_card_temp} guardada en la mano.")

    game.drawn_card_temp = None
    game.waiting_for_decision = False
    game.decision_timer = 0.0
    advance_turn(game)
