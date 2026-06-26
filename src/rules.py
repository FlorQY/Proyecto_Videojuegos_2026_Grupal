def is_valid_play(card, center_card):
    """Verifica si una carta se puede jugar sobre la carta central."""
    if card.color == "Wild":
        return True  # Los comodines siempre son jugables (regla actual)
    return card.color == center_card.color or card.value == center_card.value


def get_effect(card):
    """
    Devuelve el tipo de efecto de la carta.
    Si no tiene efecto especial, devuelve None.
    """
    specials = ["Reverse", "Skip", "+2", "+4", "+4 Reverse", "+6", "+10", "Sad"]
    if card.value in specials:
        return card.value
    return None


def apply_color_selection(card, chosen_color):
    """Cambia el color de una carta comodín (solo para Wild y derivados)."""
    if card.color == "Wild":
        card.color = chosen_color
        return True
    return False
