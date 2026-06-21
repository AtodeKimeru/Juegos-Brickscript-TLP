# -*- coding: utf-8 -*-
import sys
import random
import bisect
import Tkinter as tk
import tkMessageBox

from runtimes.events import get_actions


def seleccion_ponderada(nombres, pesos):
    total = sum(pesos)
    acumulados = []
    acum = 0
    for p in pesos:
        acum += p
        acumulados.append(acum)
    r = random.uniform(0, total)
    indice = bisect.bisect_left(acumulados, r)
    if indice >= len(nombres):
        indice = len(nombres) - 1
    return nombres[indice]


class TetrisEngine(object):
    def __init__(self, datos):
        self.datos = datos
        cfg = datos.get('config', {})
        self.ancho = cfg.get('grid_size', [10, 20])[0]
        self.alto = cfg.get('grid_size', [10, 20])[1]
        self.grid = [[0 for _ in range(self.ancho)] for _ in range(self.alto)]
        self.puntuacion = 0
        self.juego_terminado = False
        self.velocidad_gravedad = 0.4

        self._normalizar_shapes()

        self.pieza_actual = None
        self.nombre_pieza = None
        self.pieza_x = 0
        self.pieza_y = 0
        self.pieza_rotacion = 0
        self.color_pieza = '#00FFFF'

        self.root = tk.Tk()
        self.root.title("BrickScript - TETRIS")
        self.root.protocol("WM_DELETE_WINDOW", self._cerrar)

        self.taman_celda = 25
        self.canvas = tk.Canvas(
            self.root,
            width=self.ancho * self.taman_celda,
            height=self.alto * self.taman_celda,
            bg='#111111',
        )
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)

        frame = tk.Frame(self.root, width=150, bg='#222222')
        frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        self.label_score = tk.Label(
            frame, text="PUNTUACION\n0", bg='#222222', fg='white',
            font=('Consolas', 16, 'bold')
        )
        self.label_score.pack(pady=40, padx=10)
        tk.Label(
            frame, text="CONTROLES\nFlechas: Mover/Rotar", bg='#222222', fg='gray',
            font=('Consolas', 10)
        ).pack(pady=20, padx=10)

        self.root.bind('<Key>', self._tecla)

        self.timer_gravedad = 0
        self.timer_id = None
        self._ejecutar('ON_START')
        self._loop()

    def _normalizar_shapes(self):
        shapes = {}
        for nombre, data in self.datos.get('shapes', {}).items():
            if isinstance(data, list):
                shapes[nombre] = {
                    'estados': data, 'color': '#00FFFF', 'chance': 10
                }
            else:
                shapes[nombre] = {
                    'estados': data.get('estados', []),
                    'color': data.get('color', '#00FFFF'),
                    'chance': data.get('chance', 10),
                }
        self.datos['shapes'] = shapes

    def _loop(self):
        if self.juego_terminado:
            self._game_over()
            return
        self.timer_gravedad += 0.05
        if self.timer_gravedad >= self.velocidad_gravedad:
            self.timer_gravedad = 0
            self._ejecutar('ON_TICK')
        self._dibujar()
        self.timer_id = self.root.after(50, self._loop)

    def _cerrar(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        self.root.destroy()
        sys.exit(0)

    def _tecla(self, event):
        key_map = {
            'UP': 'ON_KEY_UP',
            'DOWN': 'ON_KEY_DOWN',
            'LEFT': 'ON_KEY_LEFT',
            'RIGHT': 'ON_KEY_RIGHT',
        }
        evento = key_map.get(event.keysym.upper())
        if evento:
            self._ejecutar(evento)

    def _ejecutar(self, nombre_evento):
        eventos = self.datos.get('events', {})
        if nombre_evento not in eventos:
            return
        for accion in get_actions(eventos[nombre_evento]):
            if not isinstance(accion, dict):
                continue
            verbo = accion.get('accion')
            objeto = accion.get('objeto')
            params = accion.get('params', [])

            if verbo == 'INCREASE_SCORE':
                self.puntuacion += int(objeto) if objeto else 0
            elif verbo == 'GAME_OVER':
                self.juego_terminado = True
            elif verbo == 'SPAWN' and objeto == 'RANDOM_SHAPE':
                self._spawn_pieza()
            elif verbo == 'MOVE' and objeto == 'CURRENT_PIECE':
                self._mover_pieza(params[0] if params else 'DOWN')
            elif verbo == 'ROTATE' and objeto == 'CURRENT_PIECE':
                self._rotar_pieza()

    def _spawn_pieza(self):
        shapes = self.datos['shapes']
        nombres = shapes.keys()
        pesos = [shapes[n]['chance'] for n in nombres]
        nombre = seleccion_ponderada(nombres, pesos)
        self.nombre_pieza = nombre
        self.pieza_actual = shapes[nombre]['estados']
        self.color_pieza = shapes[nombre]['color']
        self.pieza_x = self.ancho / 2 - 2
        self.pieza_y = 0
        self.pieza_rotacion = 0
        if self._verificar_colision(self.pieza_x, self.pieza_y, self.pieza_rotacion):
            self.juego_terminado = True

    def _mover_pieza(self, direccion):
        if not self.pieza_actual:
            return
        dx, dy = 0, 0
        if direccion == 'LEFT':
            dx = -1
        elif direccion == 'RIGHT':
            dx = 1
        elif direccion == 'DOWN':
            dy = 1
        if not self._verificar_colision(
            self.pieza_x + dx, self.pieza_y + dy, self.pieza_rotacion
        ):
            self.pieza_x += dx
            self.pieza_y += dy
        elif dy > 0:
            self._fijar_pieza()

    def _rotar_pieza(self):
        if not self.pieza_actual:
            return
        nueva_rotacion = (self.pieza_rotacion + 1) % len(self.pieza_actual)
        if not self._verificar_colision(self.pieza_x, self.pieza_y, nueva_rotacion):
            self.pieza_rotacion = nueva_rotacion

    def _fijar_pieza(self):
        matriz = self.pieza_actual[self.pieza_rotacion]
        for y_offset, fila in enumerate(matriz):
            for x_offset, celda in enumerate(fila):
                if celda == 1:
                    ny = self.pieza_y + y_offset
                    nx = self.pieza_x + x_offset
                    if 0 <= ny < self.alto and 0 <= nx < self.ancho:
                        self.grid[ny][nx] = 1
        self.pieza_actual = None
        self.nombre_pieza = None
        self._limpiar_lineas()
        self._ejecutar('ON_START')

    def _verificar_colision(self, x, y, rotacion):
        if not self.pieza_actual:
            return False
        matriz = self.pieza_actual[rotacion]
        for y_offset, fila in enumerate(matriz):
            for x_offset, celda in enumerate(fila):
                if celda == 1:
                    nx = x + x_offset
                    ny = y + y_offset
                    if not (0 <= nx < self.ancho and 0 <= ny < self.alto and self.grid[ny][nx] == 0):
                        return True
        return False

    def _limpiar_lineas(self):
        nuevo_grid = [fila for fila in self.grid if not all(fila)]
        lineas = self.alto - len(nuevo_grid)
        if lineas > 0:
            self.grid = [[0] * self.ancho for _ in range(lineas)] + nuevo_grid
            for _ in range(lineas):
                self._ejecutar('ON_LINE_CLEAR')

    def _dibujar_celda(self, x, y, color):
        ts = self.taman_celda
        x1, y1 = x * ts, y * ts
        x2, y2 = x1 + ts, y1 + ts
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='#000000')

    def _dibujar(self):
        self.canvas.delete('all')
        self.label_score.config(text="PUNTUACION\n" + str(self.puntuacion))

        for y in range(self.alto):
            for x in range(self.ancho):
                if self.grid[y][x] == 1:
                    self._dibujar_celda(x, y, '#343434')

        if self.pieza_actual:
            matriz = self.pieza_actual[self.pieza_rotacion]
            for y_offset, fila in enumerate(matriz):
                for x_offset, celda in enumerate(fila):
                    if celda == 1:
                        self._dibujar_celda(
                            self.pieza_x + x_offset,
                            self.pieza_y + y_offset,
                            self.color_pieza,
                        )

    def _game_over(self):
        tkMessageBox.showinfo("Juego Terminado", "Puntuacion Final: " + str(self.puntuacion))
        self.root.destroy()
        sys.exit(0)


def run_game(data):
    TetrisEngine(data)
