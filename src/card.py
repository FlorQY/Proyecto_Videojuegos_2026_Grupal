import pygame


class Card:

    def __init__(self, color, value):

        self.color = color
        self.value = value

        # Posición
        self.x = 0
        self.y = 0

        # Tamaño
        self.width = 90
        self.height = 140

        # Área clickeable
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update_rect(self):

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def __str__(self):

        return f"{self.color} {self.value}"
