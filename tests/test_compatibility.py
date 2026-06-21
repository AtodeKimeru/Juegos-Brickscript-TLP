# -*- coding: utf-8 -*-
import json

from runtimes.events import get_actions


def test_legacy_event_in_compiled_json():
    with open("games/snake.json") as f:
        data = json.load(f)

    acciones = get_actions(data["events"]["ON_START"])
    assert len(acciones) >= 1
    assert acciones[0]["accion"] == "SPAWN"


def test_runtime_routes_compiled_games():
    from runtime import detect_game

    with open("games/snake_evolved.json") as f:
        assert detect_game(json.load(f)) == "SNAKE_EVOLVED"

    with open("games/tetris_remake.json") as f:
        assert detect_game(json.load(f)) == "TETRIS_REMAKE"


def test_all_games_have_tipo_juego():
    games = [
        "games/tetris.json",
        "games/tetris_remake.json",
        "games/snake.json",
        "games/snake_evolved.json",
        "games/tanks.json",
    ]
    for path in games:
        with open(path) as f:
            data = json.load(f)
        assert data.get("tipo_juego")
