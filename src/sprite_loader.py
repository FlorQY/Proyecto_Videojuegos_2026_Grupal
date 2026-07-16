"""
Carga de sprites (imágenes) para las cartas.
Soporta nombres de archivo en español dentro de carpetas por color.
Las imágenes se cargan con esquinas redondeadas (pre-procesado).
"""

import pygame
import os

# Diccionario global de sprites
_sprites = {}
_sprites_loaded = False

# Radio de redondeo para las esquinas de las cartas (en píxeles)
ROUND_RADIUS = 16

# Mapeo de valores de carta (en inglés) a nombres de archivo en español
VALUE_TO_SPANISH = {
    "0": "0",
    "1": "1",
    "2": "2",
    "3": "3",
    "4": "4",
    "5": "5",
    "6": "6",
    "7": "7",
    "8": "8",
    "9": "9",
    "Skip": "bloqueo",
    "+2": "mas2",
    "+4": "mas4",
    "Reverse": "reversa",
    "Wild": "tirarcolor",
    "PlayAgain": "vuelveatirar",
    "+4 Reverse": "mas4reversa",
    "+6": "mas6",
    "+10": "mas10",
    "Color Roulette": "ruleta_color",
    "Discard": "tirarcolor",
}

# Mapeo de colores en inglés a español
COLOR_TO_SPANISH = {
    "Red": "rojo",
    "Blue": "azul",
    "Green": "verde",
    "Yellow": "amarillo",
    "Wild": "comodin",
}

# Colores disponibles para buscar carpetas
COLORS = ["Red", "Blue", "Green", "Yellow", "Wild"]


def _round_corners(image, radius):
    """
    Aplica esquinas redondeadas a una superficie.
    - image: superficie pygame con canal alfa (convert_alpha)
    - radius: radio de redondeo en píxeles
    Devuelve una nueva superficie con las esquinas redondeadas.
    """
    size = image.get_size()
    # Crear una máscara con esquinas redondeadas (blanco opaco en el interior)
    mask = pygame.Surface(size, pygame.SRCALPHA)
    mask.fill((0, 0, 0, 0))  # totalmente transparente
    pygame.draw.rect(
        mask,
        (255, 255, 255, 255),  # blanco opaco
        (0, 0, size[0], size[1]),
        border_radius=radius,
    )
    # Aplicar la máscara multiplicando los canales alfa
    rounded = image.copy()
    rounded.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return rounded


def load_sprites():
    """Carga todas las imágenes de cartas desde la carpeta assets/img/cards/."""
    global _sprites, _sprites_loaded
    if _sprites_loaded:
        return

    # RUTA CORREGIDA
    base_path = os.path.join("assets", "img", "cards")

    if not os.path.exists(base_path):
        print(f"[SPRITES] CARPETA NO ENCONTRADA: {base_path}")
        print("[SPRITES] Usando rectangulos como fallback.")
        _sprites_loaded = True
        return

    print(f"[SPRITES] Buscando cartas en: {base_path}")
    print(f"[SPRITES] Aplicando redondeo de esquinas (radio={ROUND_RADIUS})")

    # Buscar carpetas por color (ej. amarillo/, rojo/, etc.)
    for color_en, color_es in COLOR_TO_SPANISH.items():
        color_path = os.path.join(base_path, color_es)
        if not os.path.exists(color_path):
            print(f"[SPRITES] Carpeta no encontrada: {color_es}/")
            continue

        print(f"[SPRITES] Cargando desde: {color_es}/")
        files_found = 0
        for filename in os.listdir(color_path):
            if filename.endswith(".png"):
                name = filename[:-4]  # quitar .png
                path = os.path.join(color_path, filename)
                try:
                    img = pygame.image.load(path).convert_alpha()
                    # Aplicar esquinas redondeadas
                    img = _round_corners(img, ROUND_RADIUS)
                    _sprites[name] = img
                    files_found += 1
                    print(f"[SPRITES] Cargado: {filename} (con bordes redondeados)")
                except Exception as e:
                    print(f"[SPRITES] Error cargando {filename}: {e}")
        print(f"[SPRITES] {files_found} archivos cargados desde {color_es}/")

    _sprites_loaded = True
    print(f"[SPRITES] TOTAL: {len(_sprites)} sprites cargados.")


def get_sprite(card):
    """
    Devuelve la imagen correspondiente a una carta, o None si no existe.
    """
    global _sprites
    if not _sprites_loaded:
        load_sprites()

    if card is None:
        return None

    # Si el color es Wild, buscar en carpeta "comodin"
    if card.color == "Wild":
        color_es = "comodin"
    else:
        color_es = COLOR_TO_SPANISH.get(card.color, card.color.lower())

    value_es = VALUE_TO_SPANISH.get(card.value, card.value)
    filename = f"{color_es}_{value_es}"

    sprite = _sprites.get(filename)

    return sprite


def get_sprite_with_color(card, force_color=None):
    """
    Devuelve la imagen correspondiente a una carta, con color forzado si se especifica.
    """
    global _sprites
    if not _sprites_loaded:
        load_sprites()

    if card is None:
        return None

    # Determinar color a usar
    if force_color is not None:
        color_es = COLOR_TO_SPANISH.get(force_color, force_color.lower())
    else:
        if card.color == "Wild":
            color_es = "comodin"
        else:
            color_es = COLOR_TO_SPANISH.get(card.color, card.color.lower())

    value_es = VALUE_TO_SPANISH.get(card.value, card.value)
    filename = f"{color_es}_{value_es}"
    return _sprites.get(filename)


def get_scaled_sprite(card, width, height, force_color=None):
    """
    Devuelve la imagen de la carta escalada al tamaño deseado.
    Si force_color se especifica, se usa ese color en lugar del color de la carta.
    """
    sprite = get_sprite_with_color(card, force_color)
    if sprite is None:
        return None
    return pygame.transform.smoothscale(sprite, (width, height))
