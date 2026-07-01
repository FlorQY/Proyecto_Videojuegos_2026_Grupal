import pygame
from src.deck import Deck
from src.player import Player
from src.rules import is_valid_play
from src.turn_manager import advance_turn, check_winner
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
)
from src.bot_manager import bot_play


class Game:
    def __init__(self):
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

        # Acumulación
        self.pending_draws = 0
        self.pending_victim = None

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

        print("[GAME] Partida iniciada. Jugadores:", [p.name for p in self.players])
        print(f"[GAME] Carta central: {self.center_card}")

    # ------------------------------------------------------------
    #  Robo y mazo (se mantienen en game)
    # ------------------------------------------------------------
    def _apply_draw_penalty(self, hand, amount):
        print(f"[ROBO] Robando {amount} cartas...")
        for _ in range(amount):
            card = self.deck.draw_card()
            if card is None:
                print("[ROBO] Mazo vacío, no se pudo robar.")
                break
            hand.append(card)
        print(f"[ROBO] Mano ahora tiene {len(hand)} cartas.")

    def _reshuffle_discard(self):
        pass  # Se implementará en bloque futuro

    # ------------------------------------------------------------
    #  Métodos wrapper (delegan en los managers)
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    #  Eventos (solo jugador humano)
    # ------------------------------------------------------------
    def handle_event(self, event):
        if self.game_state == "GAME_OVER":
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            if self.current_turn != 0:
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
                if len(self.deck.cards) > 0:
                    # 🔥 CORRECCIÓN: Obtener carta del mazo SIN añadir a la mano aún
                    card = (
                        self.deck.draw_card()
                    )  # draw_card retira la carta del mazo, no la añade a la mano
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
                else:
                    print("[ROBO] Mazo vacio.")
                return

            for i, card in enumerate(player.hand):
                if card.rect.collidepoint(mouse_pos):
                    self._play_card(player, i)
                    break

    # ------------------------------------------------------------
    #  Update (se llama cada frame)
    # ------------------------------------------------------------
    def update(self, dt):
        if self.game_state == "GAME_OVER":
            return

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

        # Penalización pendiente
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

        # Temporizador de decisión (robo voluntario)
        if self.waiting_for_decision and self.current_turn == 0:
            self.decision_timer += dt
            if self.decision_timer >= self.decision_timeout:
                print(
                    f"[DECISION] Tiempo agotado ({self.decision_timeout}s). Guardando automaticamente."
                )
                self._keep_drawn_card()
                return

        # Turno de bot
        if self.current_turn != 0 and self.winner is None:
            self.bot_timer += 1
            if self.bot_timer >= 60:
                bot = self.players[self.current_turn]
                self._bot_play(bot)
                self.bot_timer = 0

    def reset(self):
        self.__init__()
