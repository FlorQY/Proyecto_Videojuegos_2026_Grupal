"""
Manejo de penalizaciones: acumulación, respuesta y ejecución.
Todas las funciones reciben `game` como primer argumento.
"""

from src.turn_manager import advance_turn, get_next_turn, check_winner


def _get_penalty_value(card):
    """
    Devuelve el valor numérico de una carta de penalización.
    +2 -> 2, +4 -> 4, +6 -> 6, +10 -> 10, +4 Reverse -> 4.
    Si no es una carta de penalización, retorna 0.
    """
    if card.value in ["+2", "+4", "+6", "+10"]:
        return int(card.value)
    elif card.value == "+4 Reverse":
        return 4
    return 0


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

    # Actualizar el valor de la última carta jugada en la cadena
    game.last_penalty_value = amount

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

    game.pause_action(1.0)
    print("[PAUSA] Activada desde apply_attack")


def apply_pending_penalty(game):
    if game.pending_draws > 0 and game.pending_victim is not None:
        victim = game.players[game.pending_victim]
        # Notificación de robo
        game.show_notification(
            f"{victim.name} roba {game.pending_draws} cartas", (255, 80, 80), 2.0
        )
        print(
            f"[PENALIZACION] {victim.name} tiene {len(victim.hand)} cartas. Robará {game.pending_draws}."
        )
        game._apply_draw_penalty(victim.hand, game.pending_draws)
        game.pending_draws = 0
        game.pending_victim = None
        print("[PENALIZACION] Penalizacion aplicada y reseteada. Saltando turno.")
        print(f"[SALTO] {victim.name} pierde su turno por penalización.")
        # Notificación de pérdida de turno (con retraso para que se vea después del robo)
        game.show_notification(f"{victim.name} pierde su turno", (255, 200, 50), 1.5)
        advance_turn(game)
        game.pause_action(2.5)  # Pausa más larga
        print("[PAUSA] Activada desde apply_pending_penalty")


def execute_penalty_response(game, player, card, card_index):
    """Ejecuta la respuesta a una penalización (acumula y cambia víctima)."""
    amount = 0
    reverse = False
    if card.value in ["+2", "+4", "+6", "+10"]:
        amount = int(card.value)
    elif card.value == "+4 Reverse":
        amount = 4
        reverse = True

    game.last_penalty_value = amount
    player.play_card(card_index)
    print(f"[RESPUESTA] {player.name} responde con {card.value}")
    game.show_notification(
        f"{player.name} responde con {card.value}", (100, 200, 100), 1.5
    )

    game.pending_draws += amount
    print(f"[RESPUESTA] Penalización acumulada: {game.pending_draws}")

    if reverse:
        game.direction *= -1
        print(f"[RESPUESTA] Dirección invertida: {game.direction}")

    # 🔥 Log para depurar
    print(
        f"[DEBUG] Antes de actualizar pending_victim: dir={game.direction}, current_turn={game.current_turn}"
    )
    game.pending_victim = get_next_turn(game)
    print(f"[RESPUESTA] Nueva víctima: {game.players[game.pending_victim].name}")

    game.waiting_for_penalty_response = False
    game.penalty_response_timer = 0.0
    game.penalty_card_rects = []
    game.penalty_card_indices = []
    game.btn_rob_rect = None

    if check_winner(game):
        return

    print(f"[SALTO] Turno avanza después de respuesta de {player.name}.")
    advance_turn(game)
    game.pause_action(1.8)
    print("[PAUSA] Activada desde execute_penalty_response")


def respond_to_penalty(game, card_index):
    player = game.players[game.current_turn]
    card = player.hand[card_index]

    # Comparar contra la última carta lanzada, NO contra el acumulado
    card_value = _get_penalty_value(card)
    if card_value < game.last_penalty_value:
        print(
            f"[ERROR] No puedes apilar {card.value} sobre {game.last_penalty_value} (debe ser igual o mayor)."
        )
        game.show_notification(
            f"Debes jugar +{game.last_penalty_value} o superior",
            (255, 100, 100),  # rojo
            1.5,
        )
        return

    if card.color == "Wild":
        print("[RESPUESTA] Comodín detectado, seleccionando color...")
        from src.action_manager import select_color

        select_color(game, player, card, "response")
        return

    execute_penalty_response(game, player, card, card_index)


def bot_respond_to_penalty(game):
    player = game.players[game.current_turn]
    all_penalty_cards = get_penalty_cards(game, player)

    # Filtrar contra game.last_penalty_value
    valid_cards = [
        (idx, card)
        for idx, card in all_penalty_cards
        if _get_penalty_value(card) >= game.last_penalty_value
    ]

    if valid_cards:
        index, card = valid_cards[0]
        if card.color == "Wild":
            chosen_color = player.choose_color()
            card.color = chosen_color
            print(f"[BOT] {player.name} elige color {chosen_color} para responder")
        print(f"[BOT] {player.name} responde con {card.value}")
        execute_penalty_response(game, player, card, index)
    else:
        print(
            f"[BOT] {player.name} no tiene cartas de penalización válidas (>= {game.last_penalty_value}), roba."
        )
        apply_pending_penalty(game)


def apply_sad_penalty(game, target_player):
    """
    Aplica el efecto de la carta Sad sobre el jugador objetivo.
    - Roba 2 cartas.
    - Marca skip_next_turn.
    - Muestra notificación, pausa y avanza el turno.
    """
    if target_player is None:
        return

    game._apply_draw_penalty(target_player.hand, 2)
    target_player.skip_next_turn = True

    game.show_notification(
        f"{target_player.name} recibe Sad: roba 2 y pierde turno",
        (255, 100, 100),  # rojo suave
        1.8,
    )
    game.pause_action(1.8)
    print("[PAUSA] Activada desde apply_sad_penalty")

    # 🔥 Avanzar al siguiente jugador
    from src.turn_manager import advance_turn

    advance_turn(game)
