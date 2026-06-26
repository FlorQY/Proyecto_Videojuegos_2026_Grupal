import random
from src.card import Card


class Deck:

    def __init__(self):
        self.cards = []
        self.create_deck()
        self.shuffle()

    def create_deck(self):

        colors = ["Red", "Blue", "Green", "Yellow"]

        # CARTAS NUMÉRICAS
        for color in colors:

            for number in range(10):

                self.cards.append(Card(color, str(number)))

                self.cards.append(Card(color, str(number)))
        # CARTAS DE ACCIÓN
        # bloqueo
        for color in colors:

            for i in range(3):

                self.cards.append(Card(color, "Skip"))

        # reverse
        for color in colors:

            for i in range(3):

                self.cards.append(Card(color, "Reverse"))

        # descarte
        for color in colors:

            for i in range(3):

                self.cards.append(Card(color, "Discard"))

        # volver a jugar
        for color in colors:

            for i in range(2):

                self.cards.append(Card(color, "PlayAgain"))

        # +2
        for color in colors:

            for i in range(3):

                self.cards.append(Card(color, "+2"))

        # +4 de color:
        for color in colors:

            for i in range(2):

                self.cards.append(Card(color, "+4"))

        # CARTAS COMODÍN
        # +6 y +10
        for i in range(4):

            self.cards.append(Card("Wild", "+6"))

        for i in range(4):

            self.cards.append(Card("Wild", "+10"))

        # +4reverse
        for i in range(8):

            self.cards.append(Card("Wild", "+4 Reverse"))

        # carita triste
        for i in range(8):

            self.cards.append(Card("Wild", "Sad"))

    def shuffle(self):
        random.shuffle(self.cards)

    def draw_card(self):

        if len(self.cards) > 0:
            return self.cards.pop()

        return None
