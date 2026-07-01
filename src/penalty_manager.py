"""
Manejo de penalizaciones: acumulación, respuesta y ejecución.
Todas las funciones reciben `game` como primer argumento.
"""

from src.turn_manager import advance_turn, get_next_turn, check_winner


def get_penalty_cards(game, player):
    """Devuelve lista de tuplas (índice, carta) para cartas de penalización."""
    penalty_values = ["+2", "+4", "+6", "+10", "+4 Reverse"]
    result = []
    for i, card in enumerate(player.hand):
        if card.value in penalty_values:
            result.append((i, card))
    return result


def apply_attack(game, amount, reverse=False):
    """Acumula una penalización sobre el siguiente jugador."""
    victim_index = get_next_turn(game)
    print(
        f"[ATAQUE] Jugador {game.current_turn} ataca con +{amount} a {victim_index} (reverse={reverse})"
    )

    if game.pending_draws > 0 and game.pending_victim == victim_index:
        game.pending_draws += amount
        print(f"[ACUMULADO] Se acumula: total ahora {game.pending_draws}")
    else:
        if game.pending_draws > 0:
            print(
                f"[ACUMULADO] Habia penalizacion para {game.pending_victim}, se aplica ahora"
            )
            apply_pending_penalty(game)
        game.pending_draws = amount
        game.pending_victim = victim_index
        print(
            f"[ACUMULADO] Nueva penalizacion: {game.pending_draws} para {game.pending_victim}"
        )

    if reverse:
        game.direction *= -1
        print(f"[REVERSE] Direccion invertida: {game.direction}")


def apply_pending_penalty(game):
    if game.pending_draws > 0 and game.pending_victim is not None:
        victim = game.players[game.pending_victim]
        # 🔥 NUEVO LOG: Mostrar tamaño de mano antes del robo
        print(
            f"[PENALIZACION] {victim.name} tiene {len(victim.hand)} cartas. Robará {game.pending_draws}."
        )
        print(f"[PENALIZACION] Aplicando {game.pending_draws} cartas a {victim.name}")
        game._apply_draw_penalty(victim.hand, game.pending_draws)
        game.pending_draws = 0
        game.pending_victim = None
        print("[PENALIZACION] Penalizacion aplicada y reseteada. Saltando turno.")
        advance_turn(game)


def execute_penalty_response(game, player, card, card_index):
    """Ejecuta la respuesta a una penalización (acumula y cambia víctima)."""
    amount = 0
    reverse = False
    if card.value in ["+2", "+4", "+6", "+10"]:
        amount = int(card.value)
    elif card.value == "+4 Reverse":
        amount = 4
        reverse = True

    player.play_card(card_index)
    print(f"[RESPUESTA] {player.name} responde con {card.value}")

    game.pending_draws += amount
    print(f"[RESPUESTA] Penalización acumulada: {game.pending_draws}")

    if reverse:
        game.direction *= -1
        print(f"[RESPUESTA] Dirección invertida: {game.direction}")

    game.pending_victim = get_next_turn(game)
    print(f"[RESPUESTA] Nueva víctima: {game.players[game.pending_victim].name}")

    game.waiting_for_penalty_response = False
    game.penalty_response_timer = 0.0
    game.penalty_card_rects = []
    game.penalty_card_indices = []
    game.btn_rob_rect = None

    if check_winner(game):
        return

    advance_turn(game)


def respond_to_penalty(game, card_index):
    """Inicia la respuesta a penalización, manejando comodines."""
    player = game.players[game.current_turn]
    card = player.hand[card_index]

    if card.color == "Wild":
        print("[RESPUESTA] Comodín detectado, seleccionando color...")
        # Importación local para evitar circularidad
        from src.action_manager import select_color

        select_color(game, player, card, "response")
        return

    execute_penalty_response(game, player, card, card_index)


def bot_respond_to_penalty(game):
    """Lógica de respuesta a penalización para bots."""
    player = game.players[game.current_turn]
    penalty_cards = get_penalty_cards(game, player)

    if penalty_cards:
        index, card = penalty_cards[0]
        if card.color == "Wild":
            chosen_color = player.choose_color()
            card.color = chosen_color
            print(f"[BOT] {player.name} elige color {chosen_color} para responder")
        print(f"[BOT] {player.name} responde con {card.value}")
        execute_penalty_response(game, player, card, index)
    else:
        print(f"[BOT] {player.name} no tiene cartas de penalización, roba.")
        apply_pending_penalty(game)
