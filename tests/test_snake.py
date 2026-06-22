# -*- coding: utf-8 -*-
import json


def test_snake_json_has_events():
    with open("games/snake_evolved.json") as f:
        data = json.load(f)

    assert "events" in data


def test_snake_tick_does_not_include_eat_food_actions():
    with open("games/snake_evolved.json") as f:
        data = json.load(f)

    tick_actions = data["events"]["ON_TICK"]["actions"]
    eat_actions = data["events"]["ON_EAT_FOOD"]["actions"]

    assert [a["accion"] for a in tick_actions] == ["MOVE"]
    assert [a["accion"] for a in eat_actions] == [
        "INCREASE_SCORE",
        "GROW",
        "SPAWN",
    ]
