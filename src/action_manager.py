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

    elif effect == "Discard":
        # Obtener el color de la carta jugada
        discard_color = card.color

        # Recorrer la mano del jugador (usando una copia para evitar modificar mientras se itera)
        cards_to_discard = []
        for c in player.hand[:]:
            if c.color == discard_color:
                cards_to_discard.append(c)

        # Eliminar las cartas de la mano
        for c in cards_to_discard:
            player.hand.remove(c)

        # Añadir al descarte
        game.discard_pile.extend(cards_to_discard)

        # Notificación y pausa
        if len(cards_to_discard) > 0:
            game.show_notification(
                f"¡Descartaste {len(cards_to_discard)} cartas {discard_color}!",
                (100, 200, 255),  # azul claro
                1.5,
            )
            game.pause_action(0.8)
        else:
            game.show_notification(
                f"No tenías cartas {discard_color} para descartar.",
                (200, 200, 200),  # gris
                1.0,
            )
            game.pause_action(0.3)

        return False  # No modifica el turno

    elif effect == "PlayAgain":
        # Notificación ANTES de saltar (para que sea visible)
        game.show_notification(
            f"¡{player.name} juega de nuevo!", (100, 200, 255), 1.5  # azul claro
        )
        game.pause_action(0.8)
        print("[PAUSA] Activada desde PlayAgain")

        # Saltar a todos los jugadores y volver al mismo (N saltos para dar la vuelta completa)
        # Si hay 4 jugadores, avanzar 4 veces = vuelve al mismo
        skip_count = len(game.players)
        for _ in range(skip_count):
            advance_turn(game)

        # Ya se manejó el turno (se avanzó manualmente)
        return True

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

    # Reproducir sonido de carta
    game.play_card_sound()

    # Comodín: pedir color
    if card.color == "Wild":
        # Si es Ruleta de Color, la víctima elige color, no el jugador actual
        if card.value == "Color Roulette":
            # Guardar la carta anterior en el descarte y asignar la nueva
            if game.center_card is not None:
                game.discard_pile.append(game.center_card)
            game.center_card = card
            select_roulette_color(game, player)
            return True
        else:
            select_color(game, player, card, "play")
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


def select_roulette_color(game, player):
    """
    Inicia la selección de color para la Ruleta de Color.
    La víctima (siguiente jugador) elige el color.
    """
    # Calcular la víctima (siguiente jugador)
    victim_index = get_next_turn(game)
    victim = game.players[victim_index]

    if victim.is_human:
        # Guardar la víctima y abrir menú de color para ella
        game.pending_roulette_victim = victim
        game.game_state = "SELECTING_ROULETTE_COLOR"
        game.selection_timer = 0.0
        print(f"[RULETA] {victim.name} debe elegir un color.")
    else:
        # Bot: elige un color automáticamente (el que más tiene en su mano)
        chosen_color = victim.choose_color()
        print(f"[RULETA] {victim.name} elige color {chosen_color}")
        execute_color_roulette(game, victim, chosen_color)


def execute_color_roulette(game, victim, chosen_color):
    """
    Ejecuta el efecto de la Ruleta de Color sobre la víctima.
    - Roba cartas del mazo hasta encontrar una carta del color elegido (sin comodines).
    - Añade todas las cartas robadas a la mano de la víctima.
    - La víctima pierde su turno.
    """
    if victim is None or chosen_color is None:
        return

    cards_drawn = []
    print(
        f"[RULETA] {victim.name} elige {chosen_color}. Robando hasta encontrar una carta de ese color..."
    )

    # Robar cartas hasta encontrar una del color elegido (excluyendo comodines)
    while True:
        card = game.deck.draw_card()
        if card is None:
            # Intentar rebarajar el descarte
            if game._reshuffle_discard():
                continue
            else:
                print("[RULETA] No hay más cartas disponibles en el mazo ni descarte.")
                break
        cards_drawn.append(card)
        # Si la carta es del color elegido y NO es comodín, detener el bucle
        if card.color == chosen_color and card.color != "Wild":
            break

    # Añadir todas las cartas robadas a la mano de la víctima
    victim.hand.extend(cards_drawn)
    # Actualizar el color de la carta central (la Ruleta)
    if game.center_card is not None and game.center_card.value == "Color Roulette":
        game.center_card.color = chosen_color
    print(
        f"[RULETA] {victim.name} robó {len(cards_drawn)} cartas (la última es del color elegido)."
    )

    # Notificación visual
    game.show_notification(
        f"{victim.name} robó {len(cards_drawn)} cartas por la Ruleta de Color",
        (255, 200, 50),  # amarillo
        2.0,
    )

    # La víctima pierde su turno (avanzar al siguiente)
    advance_turn(game)
    game.pause_action(1.8)
    print("[PAUSA] Activada desde execute_color_roulette")
