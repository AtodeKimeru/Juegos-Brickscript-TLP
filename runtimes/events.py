# -*- coding: utf-8 -*-


def get_actions(evento):
    """
    Normaliza eventos legacy (lista de acciones) y nuevos (dict con actions).
    """
    if evento is None:
        return []

    if isinstance(evento, list):
        return evento

    if isinstance(evento, dict):
        return evento.get('actions', [])

    return []
