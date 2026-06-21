# -*- coding: utf-8 -*-
import json


def test_snake_json_has_events():
    with open("games/snake_evolved.json") as f:
        data = json.load(f)

    assert "events" in data
