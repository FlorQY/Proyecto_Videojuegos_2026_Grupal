import pygame
from src.deck import Deck
from src.player import Player
from src.rules import is_valid_play, get_effect


class Game:
    def __init__(self):
        # Crear mazo
        self.deck = Deck()

        # Crear jugadores
        self.players = [
            Player("Tú", is_human=True),
            Player("Bot 1", is_human=False),
            Player("Bot 2", is_human=False),
            Player("Bot 3", is_human=False),
        ]

        # Repartir 7 cartas a cada uno
        for _ in range(7):
            for player in self.players:
                player.draw_card(self.deck)

        # Carta central (primera del mazo)
        self.center_card = self.deck.draw_card()
        # Si la primera es comodín, se le asigna un color por defecto (Rojo)
        if self.center_card.color == "Wild":
            self.center_card.color = "Red"

        # Estado del juego
        self.current_turn = 0  # Índice en self.players
        self.direction = 1  # 1 = horario, -1 = antihorario
        self.winner = None
        self.pending_draws = 0  # Para acumulación (futuro)
        self.game_state = "PLAYING"  # "PLAYING", "SELECTING_COLOR", "GAME_OVER"
        self.bot_timer = 0  # Para el retraso de los bots

        # Variables temporales para la interacción (se usarán en siguientes bloques)
        self.drawn_card_temp = None  # Carta robada y aún no decidida

    def _get_next_turn(self):
        """Devuelve el índice del siguiente jugador según la dirección."""
        next_turn = self.current_turn + self.direction
        if next_turn > 3:
            next_turn = 0
        elif next_turn < 0:
            next_turn = 3
        return next_turn

    def _advance_turn(self):
        """Avanza el turno al siguiente jugador."""
        self.current_turn = self._get_next_turn()

    def _apply_draw_penalty(self, hand, amount):
        """Aplica una penalización de robo (versión actual, sin acumulación)."""
        for _ in range(amount):
            if len(self.deck.cards) > 0:
                hand.append(self.deck.draw_card())

    def _check_winner(self):
        """Verifica si algún jugador se ha quedado sin cartas."""
        for player in self.players:
            if len(player.hand) == 0:
                self.winner = player
                self.game_state = "GAME_OVER"
                return True
        return False

    def _apply_effect(self, player, card):
        """
        Aplica el efecto especial de una carta.
        Retorna True si el turno ya fue modificado (para no avanzar dos veces).
        """
        effect = get_effect(card)

        if effect == "Reverse":
            self.direction *= -1
            return False  # No se salta turno, solo cambia dirección

        elif effect == "Skip":
            self._advance_turn()  # Salta al siguiente (la víctima)
            return True  # Ya se avanzó

        elif effect in ["+2", "+4", "+6", "+10"]:
            # Determinar cantidad
            amount = int(effect)  # +2 -> 2, etc.
            # La víctima es el siguiente jugador
            victim_index = self._get_next_turn()
            victim = self.players[victim_index]
            self._apply_draw_penalty(victim.hand, amount)
            # Se salta el turno de la víctima
            self._advance_turn()  # Primero avanzamos a la víctima...
            self._advance_turn()  # ...y luego la saltamos
            return True  # Ya se avanzó dos veces

        elif effect == "+4 Reverse":
            self.direction *= -1
            victim_index = self._get_next_turn()
            victim = self.players[victim_index]
            self._apply_draw_penalty(victim.hand, 4)
            self._advance_turn()
            self._advance_turn()
            return True

        # "Sad", "7", "0" se implementarán en bloques posteriores

        return False  # Por defecto, no se ha modificado el turno

    def _play_card(self, player, card_index):
        """
        Ejecuta la jugada de una carta.
        Retorna True si la jugada fue exitosa.
        """
        if card_index >= len(player.hand):
            return False

        card = player.hand[card_index]

        # Validar si se puede jugar
        if not is_valid_play(card, self.center_card):
            return False

        # Quitar la carta de la mano
        player.play_card(card_index)

        # Actualizar carta central
        self.center_card = card

        # Si es comodín, se debe elegir color (se hará en bloque posterior)
        # Por ahora, si es Wild, le asignamos Rojo por defecto para que no se rompa
        if card.color == "Wild":
            card.color = "Red"  # Temporal, luego se pedirá al jugador

        # Aplicar efecto especial
        turn_modified = self._apply_effect(player, card)

        # Verificar si el jugador ganó
        if self._check_winner():
            return True

        # Si el efecto no modificó el turno, avanzamos normalmente
        if not turn_modified:
            self._advance_turn()

        return True

    def _bot_play(self, player):
        """Lógica para que un bot juegue automáticamente."""
        # Buscar cartas válidas
        valid_indices = []
        for i, card in enumerate(player.hand):
            if is_valid_play(card, self.center_card):
                valid_indices.append(i)

        if valid_indices:
            # Elige la primera carta válida (comportamiento original)
            # (En bloque futuro se mejorará la IA)
            index = valid_indices[0]
            self._play_card(player, index)
        else:
            # Roba una carta
            if len(self.deck.cards) > 0:
                player.draw_card(self.deck)
            # Termina su turno (se avanza al siguiente)
            self._advance_turn()

    def handle_event(self, event):
        """Procesa eventos de Pygame (clics, teclas)."""
        if self.game_state != "PLAYING":
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            # Solo el jugador humano (turno 0) puede interactuar
            if self.current_turn != 0:
                return

            player = self.players[0]  # El jugador

            # --- Clic en el mazo ---
            # Necesitamos el rect del mazo. Lo pasaremos como atributo o lo definiremos en ui.
            # Por ahora, usaremos un rect fijo (coincide con el original)
            deck_rect = pygame.Rect(280, 150, 100, 150)
            if deck_rect.collidepoint(mouse_pos):
                if len(self.deck.cards) > 0:
                    player.draw_card(self.deck)
                    # En el original, al robar se pasaba turno. Lo mantenemos.
                    self._advance_turn()
                return

            # --- Clic en una carta del jugador ---
            for i, card in enumerate(player.hand):
                if card.rect.collidepoint(mouse_pos):
                    self._play_card(player, i)
                    break

    def update(self, dt):
        """Actualiza la lógica del juego (turnos de bots, temporizadores, etc.)."""
        if self.game_state != "PLAYING":
            return

        # Si el turno actual es de un bot
        if self.current_turn != 0 and self.winner is None:
            self.bot_timer += 1
            # Esperar 60 ticks (~1 segundo a 60 FPS)
            if self.bot_timer >= 60:
                bot = self.players[self.current_turn]
                self._bot_play(bot)
                self.bot_timer = 0

    def reset(self):
        """Reinicia la partida (para futura funcionalidad)."""
        # Por ahora, simplemente recreamos el juego
        self.__init__()
