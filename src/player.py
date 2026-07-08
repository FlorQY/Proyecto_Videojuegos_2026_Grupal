class Player:
    def __init__(self, name, is_human=True):
        self.name = name
        self.hand = []
        self.is_human = is_human
        self.uno_said = False
        self.skip_next_turn = False  # Para la carta Sad (futuro)
        
    def draw_card(self, deck):
        """Roba una carta del mazo y la añade a la mano."""
        card = deck.draw_card()
        if card:
            self.hand.append(card)
        return card

    def play_card(self, index):
        """Elimina y devuelve la carta en la posición index."""
        if 0 <= index < len(self.hand):
            return self.hand.pop(index)
        return None

    def has_valid_card(self, center_card):
        """Devuelve True si el jugador tiene al menos una carta jugable."""
        for card in self.hand:
            if card.color == center_card.color or card.value == center_card.value:
                return True
        return False

    def get_valid_cards(self, center_card):
        """Devuelve una lista con los índices de las cartas jugables."""
        valid_indices = []
        for i, card in enumerate(self.hand):
            if card.color == center_card.color or card.value == center_card.value:
                valid_indices.append(i)
        return valid_indices

    def sort_hand(self):
        """Ordena la mano por color (para mejorar la interfaz)."""
        color_order = {"Red": 0, "Blue": 1, "Green": 2, "Yellow": 3, "Wild": 4}
        self.hand.sort(key=lambda card: color_order.get(card.color, 5))

    def choose_color(self):
        """
        Lógica para que un bot elija un color.
        Elige el color que más aparece en su mano.
        """
        color_count = {"Red": 0, "Blue": 0, "Green": 0, "Yellow": 0}
        for card in self.hand:
            if card.color in color_count:
                color_count[card.color] += 1
        # Si no tiene colores, devuelve Rojo por defecto
        return (
            max(color_count, key=color_count.get)
            if any(color_count.values())
            else "Red"
        )

    def __str__(self):
        return f"{self.name} ({len(self.hand)} cartas)"
