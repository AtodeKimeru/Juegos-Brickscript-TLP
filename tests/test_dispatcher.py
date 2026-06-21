# -*- coding: utf-8 -*-
from runtime import detect_game


def test_detect_tetris():
    data = {
        "tipo_juego": "TETRIS"
    }

    assert detect_game(data) == "TETRIS"


def test_detect_tetris_remake_explicit():
    data = {
        "tipo_juego": "TETRIS_REMAKE"
    }

    assert detect_game(data) == "TETRIS_REMAKE"


def test_detect_tetris_remake_from_powerups():
    data = {
        "tipo_juego": "TETRIS",
        "powerups": {"PU": {}},
    }

    assert detect_game(data) == "TETRIS_REMAKE"


def test_detect_snake():
    data = {
        "tipo_juego": "SNAKE"
    }

    assert detect_game(data) == "SNAKE"


def test_detect_snake_evolved_explicit():
    data = {
        "tipo_juego": "SNAKE_EVOLVED"
    }

    assert detect_game(data) == "SNAKE_EVOLVED"


def test_detect_snake_evolved_from_levels():
    data = {
        "tipo_juego": "SNAKE",
        "niveles": {
            "BABY": {},
            "ENTHUSIAST": {},
        },
    }

    assert detect_game(data) == "SNAKE_EVOLVED"


def test_detect_tanks():
    data = {
        "tipo_juego": "TANKS"
    }

    assert detect_game(data) == "TANKS"
