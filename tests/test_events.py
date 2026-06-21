# -*- coding: utf-8 -*-
from runtimes.events import get_actions


def test_event_format_new():
    evento = {
        "target": None,
        "actions": [
            {
                "accion": "GAME_OVER"
            }
        ]
    }

    acciones = get_actions(evento)

    assert len(acciones) == 1
    assert acciones[0]["accion"] == "GAME_OVER"


def test_event_format_old():
    evento = [
        {
            "accion": "GAME_OVER"
        }
    ]

    acciones = get_actions(evento)

    assert len(acciones) == 1
    assert acciones[0]["accion"] == "GAME_OVER"


def test_no_unicode_event_iteration():
    evento = {
        "target": None,
        "actions": [
            {
                "accion": "SPAWN",
                "objeto": "PLAYER"
            }
        ]
    }

    acciones = get_actions(evento)

    accion = acciones[0]

    assert accion["accion"] == "SPAWN"
