import pygame
import os
from src.deck import Deck
from src.player import Player
from src.rules import is_valid_play
from src.turn_manager import advance_turn, check_winner, check_pity
from src.penalty_manager import (
    apply_pending_penalty,
    bot_respond_to_penalty,
    get_penalty_cards,
)
from src.action_manager import (
    play_card,
    play_drawn_card,
    keep_drawn_card,
    select_color,
    apply_color_and_continue,
    apply_swap,
    select_sad_target,
)
from src.bot_manager import bot_play
from src.uno_manager import (
    update_uno,
    declare_uno,
    apply_uno_penalty,
)


class Game:
    def __init__(self):

        # Sonidos
        ruta_uno = os.path.join("assets", "sounds", "uno.wav")

        try:
            self.uno_sound = pygame.mixer.Sound(ruta_uno)
            print("[SONIDO] uno.wav cargado correctamente.")
        except Exception as e:
            print(f"[SONIDO] Error cargando uno.wav: {e}")
            self.uno_sound = None
        print("[GAME] Inicializando partida...")
        self.deck = Deck()
        self.players = [
            Player("Tú", is_human=True),
            Player("Bot 1", is_human=False),
            Player("Bot 2", is_human=False),
            Player("Bot 3", is_human=False),
        ]
        for _ in range(7):
            for player in self.players:
                player.draw_card(self.deck)

        self.center_card = self.deck.draw_card()
        if self.center_card.color == "Wild":
            self.center_card.color = "Red"

        self.current_turn = 0
        self.direction = 1
        self.winner = None
        self.game_state = "PLAYING"
        self.bot_timer = 0
        # Pila de descarte
        self.discard_pile = []

        # Pausa post-acción (para evitar saltos abruptos)
        self.action_timer = 0.0
        self.action_pause = 1.8  # segundos

        # Sistema UNO
        self.uno_player = None  # jugador con una carta
        self.uno_predeclared = False  # Pulsó UNO antes de jugar
        self.uno_declared = False  # Ya quedó protegido
        self.uno_timer = 0.0  # tiempo transcurrido
        self.uno_timeout = 3.0  # segundos para decir UNO
        self.uno_window_open = False  # la ventana está activa
        self.uno_button_rect = None  # área clickeable del botón UNO
        self.uno_event_active = False

        # Denuncia de UNO
        self.denounce_player = None
        self.denounce_timer = 0.0
        self.denounce_timeout = 2.5
        self.denounce_window_open = False
        self.btn_denounce_rect = None

        # Denuncia automática de bots
        self.bot_denounced = False  # evita que varios bots denuncien al mismo tiempo
        self.bot_denounce_delay = 0.8  # Tiempo de reacción de los bots

        # botón uno
        self.uno_button_pressed = False
        self.uno_button_timer = 0.0

        # Acumulación
        self.pending_draws = 0
        self.pending_victim = None
        # Valor de la última carta de penalización jugada (para validar apilamiento)
        self.last_penalty_value = 0

        # Robo con decisión
        self.waiting_for_decision = False
        self.drawn_card_temp = None
        self.decision_timer = 0.0
        self.decision_timeout = 5.0

        self.btn_play_rect = None
        self.btn_keep_rect = None

        # Respuesta a penalización
        self.waiting_for_penalty_response = False
        self.penalty_response_timer = 0.0
        self.penalty_response_timeout = 5.0
        self.penalty_card_rects = []
        self.penalty_card_indices = []
        self.btn_rob_rect = None

        # Selección de color
        self.pending_color_card = None
        self.pending_color_player = None
        self.pending_color_callback = None
        self.color_rects = []
        self.selection_timer = 0.0
        self.selection_timeout = 5.0

        # Selección de oponente (carta 7)
        self.pending_swap_player = None
        self.opponent_rects = []
        self.opponent_indices = []

        # Selección de objetivo para SAD
        self.pending_sad_player = None  # jugador que jugó Sad
        self.sad_opponent_rects = []  # rectángulos de los botones
        self.sad_opponent_indices = []  # índices de los oponentes

        # Notificaciones visuales en pantalla
        self.notification_text = ""
        self.notification_timer = 0.0
        self.notification_duration = 1.5  # segundos
        self.notification_color = (255, 255, 255)  # blanco por defecto

        # Para logs de penalización no repetitivos
        self._last_penalty_log = None
        # Temporizador para penalizaciones huérfanas
        self._orphan_timer = 0.0

        print("[GAME] Partida iniciada. Jugadores:", [p.name for p in self.players])
        print(f"[GAME] Carta central: {self.center_card}")

    def show_notification(self, text, color=(255, 255, 255), duration=2.0):
        """Muestra una notificación en pantalla durante 'duration' segundos."""
        self.notification_text = text
        self.notification_color = color
        self.notification_timer = duration
        self.notification_duration = duration

    def pause_action(self, duration=1.8):
        """Activa una pausa visual para que el jugador vea la acción."""
        self.action_timer = duration
        print(f"[PAUSA] Esperando {duration:.2f} segundos...")

    #  Robo y mazo (se mantienen en game)
    def _apply_draw_penalty(self, hand, amount):
        print(f"[ROBO] Robando {amount} cartas...")
        cartas_robadas = 0
        while cartas_robadas < amount:
            card = self.deck.draw_card()
            if card is None:
                # Intentar rebarajar el descarte
                if self._reshuffle_discard():
                    # Reintentar robar después del rebaraje
                    continue
                else:
                    print("[ROBO] No hay cartas disponibles en mazo ni descarte.")
                    break
            hand.append(card)
            cartas_robadas += 1
        print(f"[ROBO] Mano ahora tiene {len(hand)} cartas.")
        # Regla Piedad: verificar si alguien superó 25 cartas
        check_pity(self)

    def _reshuffle_discard(self):
        """
        Toma todas las cartas del descarte, las baraja y las coloca en el mazo.
        Retorna True si se rebarajaron cartas, False si no había cartas.
        """
        if len(self.discard_pile) == 0:
            print("[REBARAJANDO] El descarte está vacío. No hay cartas para rebarajar.")
            return False

        # Copiar y vaciar el descarte
        cards_to_shuffle = self.discard_pile.copy()
        self.discard_pile.clear()

        # Barajar
        import random

        random.shuffle(cards_to_shuffle)

        # Añadir al mazo
        self.deck.cards.extend(cards_to_shuffle)

        print(
            f"[REBARAJANDO] Se han rebarajado {len(cards_to_shuffle)} cartas del descarte."
        )

        self.show_notification(
            f"Se rebarajaron {len(cards_to_shuffle)} cartas",
            (255, 220, 50),  # amarillo
            2.0,
        )
        return True

    #  Métodos wrapper (delegan en los managers)
    def _get_next_turn(self):
        from src.turn_manager import get_next_turn

        return get_next_turn(self)

    def _advance_turn(self):
        advance_turn(self)

    def _check_winner(self):
        return check_winner(self)

    def _apply_attack(self, amount, reverse=False):
        from src.penalty_manager import apply_attack

        apply_attack(self, amount, reverse)

    def _apply_pending_penalty(self):
        apply_pending_penalty(self)

    def _get_penalty_cards(self, player):
        return get_penalty_cards(self, player)

    def _respond_to_penalty(self, card_index):
        from src.penalty_manager import respond_to_penalty

        respond_to_penalty(self, card_index)

    def _bot_respond_to_penalty(self):
        bot_respond_to_penalty(self)

    def _select_color(self, player, card, callback_type):
        select_color(self, player, card, callback_type)

    def _apply_color_and_continue(self, chosen_color):
        apply_color_and_continue(self, chosen_color)

    def _rotate_hands(self):
        from src.action_manager import rotate_hands

        rotate_hands(self)

    def _select_opponent(self, player):
        from src.action_manager import select_opponent

        select_opponent(self, player)

    def _apply_swap(self, player1, player2):
        apply_swap(self, player1, player2)

    def _select_sad_target(self, player):
        select_sad_target(self, player)

    def _apply_sad_effect(self, target_player):
        from src.penalty_manager import apply_sad_penalty

        apply_sad_penalty(self, target_player)

    def _apply_effect(self, player, card):
        from src.action_manager import apply_effect

        return apply_effect(self, player, card)

    def _play_card(self, player, card_index):
        return play_card(self, player, card_index)

    def _play_drawn_card(self):
        return play_drawn_card(self)

    def _keep_drawn_card(self):
        keep_drawn_card(self)

    def _bot_play(self, player):
        bot_play(self, player)

    #  Eventos (solo jugador humano)
    def handle_event(self, event):
        if self.game_state == "GAME_OVER":
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            # Botón UNO
            if self.uno_button_rect is not None and self.uno_button_rect.collidepoint(
                mouse_pos
            ):
                self.uno_button_pressed = True
                self.uno_button_timer = 0.12

                declare_uno(self)
                return

            if self.current_turn != 0:

                # Denunciar UNO
                if self.denounce_window_open:

                    if (
                        self.btn_denounce_rect is not None
                        and self.btn_denounce_rect.collidepoint(mouse_pos)
                    ):

                        print(f"[UNO] Denunciaste a {self.denounce_player.name}")

                        apply_uno_penalty(self)

                        return
                return

            player = self.players[0]

            # Selección de color
            if self.game_state == "SELECTING_COLOR":
                for rect, color in self.color_rects:
                    if rect.collidepoint(mouse_pos):
                        print(f"[COLOR] Jugador eligió {color}")
                        self._apply_color_and_continue(color)
                        return
                return

            # Selección de oponente
            if self.game_state == "SELECTING_OPPONENT":
                for rect, idx in zip(self.opponent_rects, self.opponent_indices):
                    if rect.collidepoint(mouse_pos):
                        opponent = self.players[idx]
                        print(f"[INTERCAMBIO] Jugador eligió a {opponent.name}")
                        self._apply_swap(player, opponent)
                        self._advance_turn()
                        return
                return

            # Selección de objetivo para SAD
            if self.game_state == "SELECTING_SAD_TARGET":
                for rect, idx in zip(
                    self.sad_opponent_rects, self.sad_opponent_indices
                ):
                    if rect.collidepoint(mouse_pos):
                        target = self.players[idx]
                        print(f"[SAD] Jugador eligió a {target.name} para Sad.")
                        self._apply_sad_effect(target)
                        self.game_state = "PLAYING"
                        self.sad_opponent_rects = []
                        self.sad_opponent_indices = []
                        self.selection_timer = 0.0
                        self.pending_sad_player = None
                        # NO llamar a self._advance_turn() aquí
                        return
                return

            # Respuesta a penalización
            if self.waiting_for_penalty_response:
                for i, rect in enumerate(self.penalty_card_rects):
                    if rect.collidepoint(mouse_pos):
                        card_index = self.penalty_card_indices[i]
                        self._respond_to_penalty(card_index)
                        return

                if self.btn_rob_rect is not None and self.btn_rob_rect.collidepoint(
                    mouse_pos
                ):
                    print("[RESPUESTA] Jugador elige robar.")
                    self._apply_pending_penalty()
                    self.waiting_for_penalty_response = False
                    self.penalty_response_timer = 0.0
                    self.penalty_card_rects = []
                    self.penalty_card_indices = []
                    self.btn_rob_rect = None
                    return
                return

            # Robo con decisión
            if self.waiting_for_decision:
                if self.btn_play_rect is not None and self.btn_play_rect.collidepoint(
                    mouse_pos
                ):
                    if is_valid_play(self.drawn_card_temp, self.center_card):
                        self._play_drawn_card()
                    else:
                        print("[DECISION] La carta no es valida, no se puede jugar.")
                    return

                if self.btn_keep_rect is not None and self.btn_keep_rect.collidepoint(
                    mouse_pos
                ):
                    self._keep_drawn_card()
                    return
                return

            # Comportamiento normal: clic en mazo o en carta
            deck_rect = pygame.Rect(280, 150, 100, 150)
            if deck_rect.collidepoint(mouse_pos):
                # Intentar robar una carta
                card = self.deck.draw_card()
                if card is None:
                    # Si el mazo está vacío, intentar rebarajar
                    if self._reshuffle_discard():
                        card = self.deck.draw_card()
                    if card is None:
                        print("[ROBO] No hay cartas disponibles en mazo ni descarte.")
                        return

                # Ahora tenemos una carta (o None si no hay)
                if card is not None:
                    self.drawn_card_temp = card
                    self.waiting_for_decision = True
                    self.decision_timer = 0.0
                    valida = (
                        "válida"
                        if is_valid_play(card, self.center_card)
                        else "no válida"
                    )
                    print(
                        f"[ROBO] Has robado: {card} ({valida}). Decide: JUGAR o GUARDAR."
                    )
                return

            for i, card in enumerate(player.hand):
                if card.rect.collidepoint(mouse_pos):
                    self._play_card(player, i)
                    break

    def update(self, dt):
        if self.game_state == "GAME_OVER":
            return

        # Pausa post-acción
        if self.action_timer > 0:
            self.action_timer -= dt
            if self.action_timer < 0:
                self.action_timer = 0
            if hasattr(self, "_last_log_time") and self.action_timer > 0:
                if self._last_log_time - self.action_timer > 0.2:
                    print(f"[PAUSA] Restante: {self.action_timer:.2f}s")
                    self._last_log_time = self.action_timer
            return

        # Actualizar temporizador de notificaciones
        if self.notification_timer > 0:
            self.notification_timer -= dt
            if self.notification_timer < 0:
                self.notification_timer = 0

        update_uno(self, dt)

        # Animación del botón UNO
        if self.uno_button_pressed:
            self.uno_button_timer -= dt
            if self.uno_button_timer <= 0:
                self.uno_button_pressed = False
                self.uno_button_timer = 0.0

        # Temporizador selección de color
        if self.game_state == "SELECTING_COLOR":
            self.selection_timer += dt
            if self.selection_timer >= self.selection_timeout:
                print("[COLOR] Tiempo agotado. Eligiendo Rojo por defecto.")
                self._apply_color_and_continue("Red")
                return

        # Temporizador selección de oponente
        if self.game_state == "SELECTING_OPPONENT":
            self.selection_timer += dt
            if self.selection_timer >= self.selection_timeout:
                player = self.pending_swap_player
                opponents = [p for p in self.players if p is not player]
                chosen = min(opponents, key=lambda p: len(p.hand))
                print(f"[INTERCAMBIO] Tiempo agotado. Intercambiando con {chosen.name}")
                self._apply_swap(player, chosen)
                self._advance_turn()
                return

        # Temporizador selección de objetivo para SAD
        if self.game_state == "SELECTING_SAD_TARGET":
            self.selection_timer += dt
            if self.selection_timer >= self.selection_timeout:
                player = self.pending_sad_player
                opponents = [p for p in self.players if p is not player]
                chosen = min(opponents, key=lambda p: len(p.hand))
                print(f"[SAD] Tiempo agotado. Eligiendo a {chosen.name} para Sad.")
                self._apply_sad_effect(chosen)
                self.game_state = "PLAYING"
                self.sad_opponent_rects = []
                self.sad_opponent_indices = []
                self.selection_timer = 0.0
                self.pending_sad_player = None
                # 🔥 NO llamar a self._advance_turn() aquí
                return

        # 🔥 Log de estado de penalización (solo cuando cambia)
        if self.pending_draws > 0 or self.pending_victim is not None:
            current_state = (self.pending_draws, self.pending_victim)
            if current_state != self._last_penalty_log:
                victim_name = "ninguno"
                if self.pending_victim is not None and self.pending_victim < len(
                    self.players
                ):
                    victim_name = self.players[self.pending_victim].name
                print(
                    f"[INFO] Penalización pendiente: {self.pending_draws} cartas para {victim_name}"
                )
                self._last_penalty_log = current_state

        # 🔥 Manejo de penalizaciones huérfanas
        if (
            self.pending_draws > 0
            and self.pending_victim is not None
            and self.pending_victim != self.current_turn
        ):
            self._orphan_timer += dt
            if self._orphan_timer > 2.0:
                print(
                    f"[FIX] Penalización huérfana: aplicando a {self.players[self.current_turn].name} (victima original era {self.players[self.pending_victim].name if self.pending_victim < len(self.players) else 'eliminado'})"
                )
                self.pending_victim = self.current_turn
                self._orphan_timer = 0.0
        else:
            self._orphan_timer = 0.0

        # 🔥 PENALIZACIÓN PENDIENTE (se ejecuta ANTES que cualquier otra acción)
        if self.pending_draws > 0 and self.pending_victim == self.current_turn:
            player = self.players[self.current_turn]
            penalty_cards = self._get_penalty_cards(player)

            if player.is_human:
                if penalty_cards:
                    if not self.waiting_for_penalty_response:
                        print(
                            f"[RESPUESTA] Jugador {self.current_turn} puede responder a la penalización."
                        )
                        self.waiting_for_penalty_response = True
                        self.penalty_response_timer = 0.0
                        # 🔥 Salir del update para no repetir logs este frame
                        return
                    else:
                        self.penalty_response_timer += dt
                        if self.penalty_response_timer >= self.penalty_response_timeout:
                            print(
                                "[RESPUESTA] Tiempo agotado. Robando automáticamente."
                            )
                            self._apply_pending_penalty()
                            self.waiting_for_penalty_response = False
                            self.penalty_response_timer = 0.0
                            self.penalty_card_rects = []
                            self.penalty_card_indices = []
                            self.btn_rob_rect = None
                    return
                else:
                    print(
                        f"[UPDATE] Jugador {self.current_turn} no tiene cartas de penalización."
                    )
                    self._apply_pending_penalty()
                    return
            else:
                self._bot_respond_to_penalty()
                return

        # Verificar skip_next_turn (efecto Sad)
        current_player = self.players[self.current_turn]
        if current_player.skip_next_turn:
            current_player.skip_next_turn = False
            print(f"[TURNO] {current_player.name} pierde su turno por efecto Sad.")
            self.pause_action(1.0)
            self._advance_turn()
            return

        # Temporizador de decisión (robo voluntario)
        if self.waiting_for_decision and self.current_turn == 0:
            self.decision_timer += dt
            if self.decision_timer >= self.decision_timeout:
                print(
                    f"[DECISION] Tiempo agotado ({self.decision_timeout}s). Guardando automaticamente."
                )
                self._keep_drawn_card()
                return

        # 🔥 Turno de bot (sin log excesivo)
        if self.current_turn != 0 and self.winner is None:
            self.bot_timer += 1
            if self.bot_timer >= 60:
                bot = self.players[self.current_turn]
                self._bot_play(bot)
                self.bot_timer = 0

        # Regla Piedad: verificar al final del turno
        check_pity(self)

    def play_uno_sound(self):
        if self.uno_sound is not None:
            self.uno_sound.play()

    def reset(self):
        self.__init__()
