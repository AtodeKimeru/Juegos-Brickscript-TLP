# -*- coding: utf-8 -*-
import json


def test_tetris_json_has_events():
    with open("games/tetris.json") as f:
        data = json.load(f)

    assert "events" in data
