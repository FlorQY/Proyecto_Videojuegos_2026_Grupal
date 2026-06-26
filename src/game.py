import pygame
from src.deck import Deck
from src.player import Player
from src.rules import is_valid_play, get_effect


class Game:
    def __init__(self):
        print("🔍 [GAME] Inicializando partida...")
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
        self.drawn_card_temp = None

        # Acumulación
        self.pending_draws = 0
        self.pending_victim = None

        print("🔍 [GAME] Partida iniciada. Jugadores:", [p.name for p in self.players])
        print(f"🔍 [GAME] Carta central: {self.center_card}")

    # ------------------------------------------------------------
    #  Métodos auxiliares de turnos
    # ------------------------------------------------------------
    def _get_next_turn(self):
        next_turn = self.current_turn + self.direction
        if next_turn > 3:
            next_turn = 0
        elif next_turn < 0:
            next_turn = 3
        return next_turn

    def _advance_turn(self):
        old = self.current_turn
        self.current_turn = self._get_next_turn()
        print(
            f"🔍 [TURNO] Avanzando: {old} -> {self.current_turn} (dir={self.direction})"
        )

    # ------------------------------------------------------------
    #  Robo y mazo
    # ------------------------------------------------------------
    def _apply_draw_penalty(self, hand, amount):
        print(f"🔍 [ROBO] Robando {amount} cartas para {hand}...")
        for _ in range(amount):
            card = self.deck.draw_card()
            if card is None:
                print("🔍 [ROBO] Mazo vacío, no se pudo robar.")
                break
            hand.append(card)
        print(f"🔍 [ROBO] Mano ahora tiene {len(hand)} cartas.")

    def _reshuffle_discard(self):
        # Placeholder
        pass

    # ------------------------------------------------------------
    #  Verificación de ganador
    # ------------------------------------------------------------
    def _check_winner(self):
        for player in self.players:
            if len(player.hand) == 0:
                self.winner = player
                self.game_state = "GAME_OVER"
                print(f"🔍 [VICTORIA] ¡{player.name} ha ganado!")
                return True
        return False

    # ------------------------------------------------------------
    #  🔥 Acumulación de penalizaciones
    # ------------------------------------------------------------
    def _apply_attack(self, amount, reverse=False):
        victim_index = self._get_next_turn()
        print(
            f"🔍 [ATAQUE] Jugador {self.current_turn} ataca con +{amount} a {victim_index} (reverse={reverse})"
        )

        if self.pending_draws > 0 and self.pending_victim == victim_index:
            self.pending_draws += amount
            print(f"🔍 [ACUMULADO] Se acumula: total ahora {self.pending_draws}")
        else:
            if self.pending_draws > 0:
                print(
                    f"🔍 [ACUMULADO] Había penalización para {self.pending_victim}, se aplica ahora"
                )
                self._apply_pending_penalty()
            self.pending_draws = amount
            self.pending_victim = victim_index
            print(
                f"🔍 [ACUMULADO] Nueva penalización: {self.pending_draws} para {self.pending_victim}"
            )

        if reverse:
            self.direction *= -1
            print(f"🔍 [REVERSE] Dirección invertida: {self.direction}")

    def _apply_pending_penalty(self):
        if self.pending_draws > 0 and self.pending_victim is not None:
            print(
                f"🔍 [PENALIZACIÓN] Aplicando {self.pending_draws} cartas a {self.players[self.pending_victim].name}"
            )
            victim = self.players[self.pending_victim]
            self._apply_draw_penalty(victim.hand, self.pending_draws)
            self.pending_draws = 0
            self.pending_victim = None
            print(
                "🔍 [PENALIZACIÓN] Penalización aplicada y reseteada. Saltando turno."
            )
            self._advance_turn()

    # ------------------------------------------------------------
    #  Aplicación de efectos de cartas
    # ------------------------------------------------------------
    def _apply_effect(self, player, card):
        effect = get_effect(card)
        print(
            f"🔍 [EFECTO] Carta {card.value} jugada por {player.name}, efecto={effect}"
        )

        if effect == "Reverse":
            self.direction *= -1
            print(f"🔍 [REVERSE] Dirección ahora {self.direction}")
            return False

        elif effect == "Skip":
            self._advance_turn()
            return True

        elif effect in ["+2", "+4", "+6", "+10"]:
            amount = int(effect)
            self._apply_attack(amount, reverse=False)
            return False

        elif effect == "+4 Reverse":
            self._apply_attack(4, reverse=True)
            return False

        return False

    # ------------------------------------------------------------
    #  Jugar una carta
    # ------------------------------------------------------------
    def _play_card(self, player, card_index):
        if card_index >= len(player.hand):
            return False

        card = player.hand[card_index]
        if not is_valid_play(card, self.center_card):
            print(f"🔍 [JUGADA] {player.name} intentó jugar {card} pero no es válida.")
            return False

        print(f"🔍 [JUGADA] {player.name} juega {card}")
        player.play_card(card_index)
        self.center_card = card

        if card.color == "Wild":
            card.color = "Red"  # temporal

        turn_modified = self._apply_effect(player, card)

        if self._check_winner():
            return True

        if not turn_modified:
            self._advance_turn()

        return True

    # ------------------------------------------------------------
    #  Lógica de bots
    # ------------------------------------------------------------
    def _bot_play(self, player):
        print(f"🔍 [BOT] Turno de {player.name}")
        valid_indices = []
        for i, card in enumerate(player.hand):
            if is_valid_play(card, self.center_card):
                valid_indices.append(i)

        if valid_indices:
            # Elige la primera carta válida
            index = valid_indices[0]
            print(f"🔍 [BOT] {player.name} juega {player.hand[index]}")
            self._play_card(player, index)
        else:
            print(f"🔍 [BOT] {player.name} no tiene carta válida, roba.")
            if len(self.deck.cards) > 0:
                player.draw_card(self.deck)
            self._advance_turn()

    # ------------------------------------------------------------
    #  Eventos (solo jugador humano)
    # ------------------------------------------------------------
    def handle_event(self, event):
        if self.game_state != "PLAYING":
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.current_turn != 0:
                return

            player = self.players[0]

            deck_rect = pygame.Rect(280, 150, 100, 150)
            if deck_rect.collidepoint(mouse_pos):
                if len(self.deck.cards) > 0:
                    player.draw_card(self.deck)
                    self._advance_turn()
                return

            for i, card in enumerate(player.hand):
                if card.rect.collidepoint(mouse_pos):
                    self._play_card(player, i)
                    break

    # ------------------------------------------------------------
    #  Update (se llama cada frame)
    # ------------------------------------------------------------
    def update(self, dt):
        if self.game_state != "PLAYING":
            return

        # 1. Aplicar penalización pendiente si corresponde
        if self.pending_draws > 0 and self.pending_victim == self.current_turn:
            print(
                f"🔍 [UPDATE] Jugador {self.current_turn} tiene penalización pendiente."
            )
            self._apply_pending_penalty()
            return

        # 2. Turno de bot
        if self.current_turn != 0 and self.winner is None:
            self.bot_timer += 1
            if self.bot_timer >= 60:
                bot = self.players[self.current_turn]
                self._bot_play(bot)
                self.bot_timer = 0

    def reset(self):
        self.__init__()
