"""
Acciones del juego: jugar cartas, efectos, rotación, intercambio, selección de color.
Todas las funciones reciben `game` como primer argumento.
"""

from src.rules import is_valid_play, get_effect
from src.turn_manager import advance_turn, check_winner, get_next_turn


def rotate_hands(game):
    """Rota todas las manos una posición en la dirección actual."""
    n = len(game.players)
    if n == 0:
        return
    hands = [p.hand for p in game.players]
    new_hands = []

    if game.direction == 1:  # Horario: i recibe de i-1
        for i in range(n):
            new_hands.append(hands[(i - 1) % n])
    else:  # Antihorario: i recibe de i+1
        for i in range(n):
            new_hands.append(hands[(i + 1) % n])

    for i, player in enumerate(game.players):
        player.hand = new_hands[i]
        player.sort_hand()

    print(f"[ROTACION] Manos rotadas en dirección {game.direction}")
    game.show_notification("¡Manos rotadas!", (100, 150, 255), 1.5)
    game.pause_action(1.8)
    print("[PAUSA] Activada desde rotate_hands")


def apply_swap(game, player1, player2):
    """Intercambia las manos de dos jugadores."""
    player1.hand, player2.hand = player2.hand, player1.hand
    player1.sort_hand()
    player2.sort_hand()
    print(f"[INTERCAMBIO] Manos intercambiadas entre {player1.name} y {player2.name}")
    game.show_notification(f"{player1.name} ↔ {player2.name}", (100, 150, 255), 1.5)

    game.pending_swap_player = None
    game.opponent_rects = []
    game.opponent_indices = []
    game.game_state = "PLAYING"
    game.selection_timer = 0.0
    game.pause_action(1.8)
    print("[PAUSA] Activada desde apply_swap")


def select_opponent(game, player):
    """Inicia la selección de oponente para intercambio (carta 7)."""
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


def apply_sad_effect(game, target_player):
    """
    Aplica el efecto de la carta Sad sobre el jugador objetivo:
    - Acumula 2 cartas de penalización.
    - Marca el flag skip_next_turn para que pierda su próximo turno.
    """
    target_index = game.players.index(target_player)

    # 1. Acumular penalización de 2 cartas
    from src.penalty_manager import apply_pending_penalty

    if game.pending_draws > 0 and game.pending_victim == target_index:
        game.pending_draws += 2
        print(
            f"[SAD] Se acumulan 2 cartas a {target_player.name}. Total: {game.pending_draws}"
        )
    else:
        # Si hay penalización para otro, aplicar primero
        if game.pending_draws > 0:
            print("[SAD] Había penalización para otro, se aplica ahora.")
            apply_pending_penalty(game)
        game.pending_draws = 2
        game.pending_victim = target_index
        print(f"[SAD] Nueva penalización de 2 cartas para {target_player.name}")

    # 2. Marcar para saltar su próximo turno
    target_player.skip_next_turn = True
    print(f"[SAD] {target_player.name} perderá su próximo turno.")
    # Notificación visual para Sad
    game.show_notification(
        f"{target_player.name} recibe Sad: roba 2 y pierde turno",
        (255, 100, 100),  # rojo suave
        1.5,
    )
    game.pause_action(1.8)
    print("[PAUSA] Activada desde apply_sad_effect")


def select_sad_target(game, player):
    """
    Inicia la selección del objetivo de la carta Sad.
    Para humanos: abre un menú.
    Para bots: elige al oponente con menos cartas y aplica el efecto.
    """
    if player.is_human:
        game.pending_sad_player = player
        game.game_state = "SELECTING_SAD_TARGET"
        game.selection_timer = 0.0
        print("[SAD] Jugador humano debe elegir oponente para Sad.")
    else:
        # Bot: elige al oponente con menos cartas
        opponents = [p for p in game.players if p is not player]
        chosen = min(opponents, key=lambda p: len(p.hand))
        print(f"[SAD] {player.name} elige a {chosen.name} para Sad.")
        # Aplicar efecto directamente (apply_sad_penalty ya avanza el turno)
        from src.penalty_manager import apply_sad_penalty

        apply_sad_penalty(game, chosen)


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

    # 🔥 NUEVO: Si es Sad, seleccionar objetivo y aplicar efecto
    if callback == "sad":
        select_sad_target(game, player)
        return  # select_sad_target se encarga de todo (incluye avance de turno)

    if callback == "play":
        if game.center_card is not None:
            game.discard_pile.append(game.center_card)
        game.center_card = card
        turn_modified = apply_effect(game, player, card)
        if check_winner(game):
            return
        if not turn_modified:
            advance_turn(game)
        # Eliminamos la pausa genérica; cada efecto maneja la suya
        return

    elif callback == "response":
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
        return False

    if effect == "Reverse":
        game.direction *= -1
        print(f"[REVERSE] Direccion ahora {game.direction}")
        game.show_notification("¡Dirección invertida!", (255, 220, 50), 1.5)
        game.pause_action(1.0)
        return False

    elif effect == "Skip":
        next_player_index = get_next_turn(game)
        if game.pending_draws > 0 and game.pending_victim == next_player_index:
            print(
                f"[SKIP] {game.players[next_player_index].name} tiene penalización pendiente. Aplicando antes de saltar."
            )
            from src.penalty_manager import apply_pending_penalty

            apply_pending_penalty(game)
        else:
            victim = game.players[next_player_index]
            game.show_notification(f"Salta a {victim.name}", (100, 150, 255), 1.5)
            advance_turn(game)
            game.pause_action(1.2)
            print("[PAUSA] Activada desde Skip (víctima)")
            advance_turn(game)
        return True

    elif effect in ["+2", "+4", "+6", "+10"]:
        amount = int(effect)
        from src.penalty_manager import apply_attack

        apply_attack(game, amount, reverse=False)
        return False

    elif effect == "+4 Reverse":
        game.direction *= -1
        game.last_penalty_value = 4
        print(f"[REVERSE] Direccion invertida a {game.direction}")
        game.show_notification("¡Dirección invertida!", (255, 220, 50), 1.5)

        victim_index = get_next_turn(game)
        victim = game.players[victim_index]
        print(f"[ATAQUE] Jugador {player.name} ataca a {victim.name} con +4 (reverse)")

        from src.penalty_manager import (
            get_penalty_cards,
            execute_penalty_response,
            _get_penalty_value,
        )

        all_penalty_cards = get_penalty_cards(game, victim)

        if victim.is_human and all_penalty_cards:
            game.pending_draws = 4
            game.pending_victim = victim_index
            game.waiting_for_penalty_response = True
            game.penalty_response_timer = 0.0
            print(f"[RESPUESTA] {victim.name} puede responder al +4 Reverse")
            return False

        if not victim.is_human and all_penalty_cards:
            valid_cards = [
                (idx, card)
                for idx, card in all_penalty_cards
                if _get_penalty_value(card) >= 4
            ]
            if valid_cards:
                index, card = valid_cards[0]
                print(f"[BOT] {victim.name} responde con {card.value}")
                execute_penalty_response(game, victim, card, index)
                return False

        game.pending_draws = 4
        game.pending_victim = victim_index
        game.pause_action(1.0)
        print("[PAUSA] Activada desde +4 Reverse")
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
        # Si es Sad, usamos callback "sad" para que después de elegir color se maneje la selección de objetivo
        callback_type = "sad" if card.value == "Sad" else "play"
        select_color(game, player, card, callback_type)
        return True

    # Carta 7: seleccionar oponente
    if card.value == "7":
        select_opponent(game, player)
        return True

    # Guardar la carta anterior en el descarte antes de reemplazarla
    if game.center_card is not None:
        game.discard_pile.append(game.center_card)

    # Otras cartas
    game.center_card = card
    turn_modified = apply_effect(game, player, card)

    if check_winner(game):
        return True

    # Pausa solo si la carta NO tiene efecto especial
    if get_effect(card) is None:
        game.pause_action(1.8)
        print("[PAUSA] Activada desde play_card (numérica)")

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

    # FIX: Si la carta aún está en la mano, eliminarla (evita duplicación)
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
