# UNO No Mercy

Videojuego de cartas inspirado en la versión *UNO Show 'em No Mercy*, desarrollado en Python con Pygame.

---

## Descripción

Este proyecto es una adaptación digital completa del juego de cartas **UNO No Mercy**, una versión más intensa y estratégica del UNO clásico. Incluye todas las mecánicas oficiales: acumulación de penalizaciones, respuesta con apilamiento, cartas especiales (0, 7, Discard, PlayAgain, Ruleta de Color, +4 Reverse, +6, +10), sistema UNO con declaración y denuncia, rebaraje del descarte, y una interfaz gráfica rica en sprites, música y efectos de sonido.

El juego está diseñado para un **jugador humano** que compite contra **tres bots** con inteligencia artificial priorizada (comodines > acciones > numéricas). La arquitectura es **modular y mantenible**, basada en managers especializados, lo que facilita la extensión y depuración.

---

## Características implementadas

### Mecánicas de juego

- **Sistema de turnos** con dirección (horaria/antihoraria) y cambio mediante carta Reverse.
- **Acumulación de penalizaciones** (+2, +4, +6, +10, +4 Reverse): las cartas no roban de inmediato, se acumulan y la víctima roba el total al inicio de su turno, perdiéndolo.
- **Respuesta del atacado** (apilamiento): la víctima puede jugar una carta de penalización de **igual o mayor valor** para transferir la penalización al siguiente jugador.
- **Robo y decisión**: al robar, la carta se muestra separada con botones "JUGAR" (si es válida) y "GUARDAR"; temporizador de 5 segundos.
- **Selección de color** para comodines mediante menú de 4 círculos (Rojo, Azul, Verde, Amarillo) con temporizador de 5 segundos (Rojo por defecto).
- **Carta 0**: rota todas las manos una posición en la dirección actual.
- **Carta 7**: intercambia manos con un oponente elegido (menú para humano, automático para bots – elige al de menos cartas).
- **Sistema UNO**:
  - Detección automática cuando un jugador queda con 1 carta.
  - Ventana de 3 segundos para declarar "UNO" pulsando el botón.
  - Declaración anticipada (con 2 cartas y jugable) y posterior (con 1 carta).
  - Si no declara, ventana de denuncia de 2.5 segundos donde otros jugadores (humanos o bots con 80% de probabilidad) pueden denunciar; el infractor roba 2 cartas.
- **Rebaraje del descarte**: cuando el mazo se vacía, las cartas jugadas (excepto la central) se barajan y forman un nuevo mazo, evitando bloqueos.
- **Cartas especiales**:
  - **Discard**: descarta todas las cartas de tu mano que coincidan con el color de la carta jugada.
  - **PlayAgain**: el jugador obtiene otro turno inmediato (salta a todos).
  - **Ruleta de Color** (antes "Sad"): la víctima elige un color y roba cartas hasta obtener una de ese color; roba todas y pierde su turno.
- **Regla Piedad**: si un jugador acumula 25 cartas o más, es eliminado. Si el humano es eliminado, la partida termina con Game Over y mensaje personalizado.
- **Pantalla de Game Over** con botones "REINTENTAR" y "VOLVER AL MENÚ".

### Interfaz y experiencia de usuario

- **Sprites de 68 cartas** organizados por color (rojo, azul, verde, amarillo, comodín) con nombres en español y bordes redondeados.
- **Sistema de fallback**: si una imagen no existe, se dibuja un rectángulo con color y texto.
- **Dorso y mazo** con imagen `carta_volteada.png` y bordes redondeados, simulando una pila de cartas.
- **Menú principal** con fondo propio (`menu_bg.png`), botones estilo negro con borde rojo intenso, y tres opciones: "NUEVA PARTIDA", "REGLAS" (imagen con scroll vertical) y "SALIR".
- **Música de fondo** diferenciada para menú (`menu_music.wav`) y partida (`game_music.wav`) en bucle.
- **Efectos de sonido**: `uno.wav` al declarar UNO y `card_sound.mp3` al colocar cada carta.
- **Notificaciones emergentes** en pantalla para eventos clave (dirección invertida, penalizaciones, intercambios, rebaraje, etc.).
- **Indicadores visuales**: resaltado del turno activo (nombre grande en amarillo con ▶), flecha de dirección (→/←), indicador parpadeante de penalización pendiente.
- **Apilamiento dinámico de cartas** (dos filas superpuestas) para manos largas.

### Arquitectura y código

- **Modularización completa**: el código se divide en managers especializados (`turn_manager`, `penalty_manager`, `action_manager`, `bot_manager`, `uno_manager`) y módulos de interfaz (`ui`, `ui_overlays`), reduciendo `game.py` a ~200 líneas.
- **Gestión de estados** en `main.py` (MENU, RULES, PLAYING) y en `Game` (`game_state` para selecciones y Game Over).
- **Logs de depuración** detallados para seguir el flujo de penalizaciones, turnos y eventos.

---

## Tecnologías utilizadas

- **Lenguaje**: Python 3.11
- **Librería principal**: Pygame 2.5.0
- **Otras**: psutil (para métricas de rendimiento)
- **Control de versiones**: Git y GitHub

---

## Estructura del proyecto

Proyecto_Videojuegos_2026_Grupal/
├── main.py # Orquestador (menú, estados, música)
├── requirements.txt # Dependencias
├── assets/ # Recursos
│   ├── img/
│   │    ├── cards/ # Sprites de cartas (68 imágenes)
│   │    ├── menu_bg.png # Fondo del menú
│   │    ├── rules.png # Imagen de reglas
│   │    └── uno_button.png # Botón UNO
│   │
│   └── sounds/
│        ├── card_sound.mp3
│        ├── game_musicwav
│        ├── menu_music.wav
│        └── uno.wav
│
└── src/ # Código fuente
     ├── card.py # Clase Card
     ├── deck.py # Clase Deck
     ├── player.py # Clase Player
     ├── rules.py # Reglas puras
     ├── game.py # Orquestador del juego
     ├── turn_manager.py # Turnos y victoria
     ├── penalty_manager.py # Penalizaciones y apilamiento
     ├── action_manager.py # Jugar cartas, efectos, 0, 7, color
     ├── bot_manager.py # IA de bots
     ├── uno_manager.py # Sistema UNO
     ├── ui.py # Dibujo base
     ├── ui_overlays.py # Pantallas emergentes
     └── sprite_loader.py # Carga y gestión de sprites

---

## Cómo jugar

- **Menú principal**: elige "NUEVA PARTIDA" para comenzar, "REGLAS" para ver las instrucciones, o "SALIR" para cerrar.
- **Durante la partida**:
  - Haz clic en una carta de tu mano para jugarla (si es válida).
  - Haz clic en el mazo para robar una carta; luego decide si jugarla (botón "JUGAR") o guardarla ("GUARDAR").
  - Si te atacan con una penalización, podrás responder jugando una carta de igual o mayor valor o aceptar el robo (botón "ROBAR").
  - Cuando te quede una carta, pulsa el botón UNO para declarar (tienes 3 segundos).
  - En las selecciones de color u oponente, elige dentro del tiempo límite (5 segundos) o se tomará una decisión por defecto.
- **Game Over**: al finalizar, podrás reiniciar o volver al menú principal.

---

## Contribuciones

Este proyecto fue desarrollado por:

- Piero Cueto Luna
- Flor Quispe Yura
- Jhanilde Pozo Hernandez

**Repositorio**: https://github.com/FlorQY/Proyecto_Videojuegos_2026_Grupal