import json
import sys

from runtimes.events import get_actions
from runtimes.tetris_engine import run_game as run_tetris
from runtimes.tetris_remake_engine import run_game as run_tetris_remake
from runtimes.snake_engine import run_game as run_snake
from runtimes.snake_evolved_engine import run_game as run_snake_evolved
from runtimes.tanks_engine import run_game as run_tanks


def detect_game(data):
    game_type = data.get("tipo_juego", "")

    if game_type == "TETRIS_REMAKE":
        return "TETRIS_REMAKE"
    if game_type == "SNAKE_EVOLVED":
        return "SNAKE_EVOLVED"
    if game_type == "TANKS":
        return "TANKS"

    if game_type == "SNAKE":
        niveles = data.get("niveles", {})
        if any(k in niveles for k in ("BABY", "ENTHUSIAST", "NYAN_CAT")):
            return "SNAKE_EVOLVED"
        return "SNAKE"

    if game_type == "TETRIS":
        if data.get("powerups"):
            return "TETRIS_REMAKE"
        return "TETRIS"

    return None


def main():
    if len(sys.argv) != 2:
        print "Uso: python runtime.py <archivo.json>"
        return

    with open(sys.argv[1], "r") as f:
        data = json.load(f)


    print "TIPO_JUEGO JSON =", data.get("tipo_juego")
    game = detect_game(data)
    print "DETECTADO =", game

    if game == "TETRIS":
        run_tetris(data)
    elif game == "TETRIS_REMAKE":
        run_tetris_remake(data)
    elif game == "SNAKE":
        print "Lanzando SNAKE"
        run_snake(data)
    elif game == "SNAKE_EVOLVED":
        run_snake_evolved(data)
    elif game == "TANKS":
        print "Lanzando TANKS"
        run_tanks(data)
    else:
        print "GAME_TYPE no soportado:", data.get("tipo_juego")


if __name__ == "__main__":
    main()
