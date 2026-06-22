# -*- coding: utf-8 -*-
import sys
import random
import Tkinter as tk
import tkMessageBox

from runtimes.events import get_actions


class SnakeEngine(object):
    def __init__(self, datos):
        self.datos = datos
        cfg = datos.get('config', {})
        self.w = cfg.get('grid_size', [10, 20])[0]
        self.h = cfg.get('grid_size', [10, 20])[1]
        self.grid = [[0] * self.w for _ in range(self.h)]
        self.score = 0
        self.terminado = False
        self.gravedad = 0.15

        niveles = datos.get('niveles', {})
        nivel_cfg = niveles.get('DEFAULT', niveles.get('BABY', {}))
        if nivel_cfg.get('speed'):
            self.gravedad = nivel_cfg['speed']

        self._normalizar_shapes()

        self.serpiente = []
        self.dir = (1, 0)
        self.comida = None
        self._ate_food = False

        
        self.root = tk.Tk()
        self.root.title("BrickScript - SNAKE")
        self.root.protocol("WM_DELETE_WINDOW", self._cerrar)

        self.cell = 25
        self.canvas = tk.Canvas(
            self.root, width=self.w * self.cell, height=self.h * self.cell, bg='#111111'
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
            frame, text="CONTROLES\nFlechas: Mover", bg='#222222', fg='gray',
            font=('Consolas', 10)
        ).pack(pady=20, padx=10)

        self.root.bind('<Key>', self._tecla)

        self.timer_grav = 0
        self.loop_id = None
        self._ejecutar('ON_START')
        
        self._loop()

    def _normalizar_shapes(self):
        new = {}
        for name, data in self.datos.get('shapes', {}).items():
            if isinstance(data, list):
                new[name] = {
                    'estados': data, 'color': '#00FFFF', 'chance': 10, 'tipo': 'RECTANGLE'
                }
            else:
                new[name] = {
                    'estados': data.get('estados', []),
                    'color': data.get('color', '#00FFFF'),
                    'chance': data.get('chance', 10),
                    'tipo': data.get('tipo', 'RECTANGLE'),
                }
        self.datos['shapes'] = new

    def _loop(self):
        if self.terminado:
            self._game_over()
            return
        self.timer_grav += 0.05
        if self.timer_grav >= self.gravedad:
            self.timer_grav = 0
            self._ejecutar('ON_TICK')
        self._dibujar()
        self.loop_id = self.root.after(50, self._loop)

    def _cerrar(self):
        if self.loop_id:
            self.root.after_cancel(self.loop_id)
        self.root.destroy()
        sys.exit(0)

    def _tecla(self, ev):
        key_map = {
            'UP': 'ON_KEY_UP',
            'DOWN': 'ON_KEY_DOWN',
            'LEFT': 'ON_KEY_LEFT',
            'RIGHT': 'ON_KEY_RIGHT',
        }
        evento = key_map.get(ev.keysym.upper())
        if evento:
            self._ejecutar(evento)

    def _ejecutar(self, evento):
        eventos = self.datos.get('events', {})
        if evento not in eventos:
            return
        acciones = get_actions(eventos[evento])
        self._ejecutar_acciones(acciones)

    def _ejecutar_acciones(self, acciones):
        i = 0
        while i < len(acciones):
            acc = acciones[i]
            if not isinstance(acc, dict):
                i += 1
                continue

            verbo = acc.get('accion')
            objeto = acc.get('objeto')

            if verbo == 'FORWARD':
                i += 1
                continue

            if verbo == 'ON':
                if self._ate_food:
                    i += 1
                    while i < len(acciones):
                        if acciones[i].get('accion') == 'ON':
                            break
                        self._aplicar_accion(acciones[i])
                        i += 1
                else:
                    i += 1
                    while i < len(acciones):
                        if acciones[i].get('accion') == 'ON':
                            break
                        i += 1
                continue

            self._aplicar_accion(acc)
            i += 1

    def _aplicar_accion(self, acc):
        verbo = acc.get('accion')
        objeto = acc.get('objeto')
        params = acc.get('params', [])

        if verbo == 'GAME_OVER':
            self.terminado = True
        elif verbo == 'INCREASE_SCORE':
            self.score += int(objeto) if objeto else 0
        elif verbo == 'SPAWN' and objeto == 'PLAYER':
            coords = params[0] if params else [self.w // 2, self.h // 2]
            self.serpiente = [(coords[0], coords[1])]
            self.dir = (1, 0)
        elif verbo == 'SPAWN' and objeto == 'FOOD':
            self._spawn_comida()
        elif verbo == 'MOVE' and objeto == 'PLAYER':
            self._mover()
        elif verbo == 'SET_DIRECTION':
            self._set_direction(objeto)
        elif verbo == 'GROW' and objeto == 'PLAYER':
            count = int(params[0]) if params else 1
            for _ in range(count):
                if self.serpiente:
                    self.serpiente.append(self.serpiente[-1])

    def _set_direction(self, direccion):
        if direccion == 'UP' and self.dir[1] != 1:
            self.dir = (0, -1)
        elif direccion == 'DOWN' and self.dir[1] != -1:
            self.dir = (0, 1)
        elif direccion == 'LEFT' and self.dir[0] != 1:
            self.dir = (-1, 0)
        elif direccion == 'RIGHT' and self.dir[0] != -1:
            self.dir = (1, 0)

    def _spawn_comida(self):
        for _ in range(200):
            x = random.randint(0, self.w - 1)
            y = random.randint(0, self.h - 1)
            if (x, y) not in self.serpiente:
                self.comida = (x, y)
                return

    def _mover(self):
        if not self.serpiente:
            return

        self._ate_food = False
        cabeza = self.serpiente[0]
        nx = cabeza[0] + self.dir[0]
        ny = cabeza[1] + self.dir[1]

        if not (0 <= nx < self.w and 0 <= ny < self.h):
            self._ejecutar('ON_COLLISION_WALL')
            return

        if (nx, ny) in self.serpiente[:-1]:
            self._ejecutar('ON_COLLISION_SELF')
            return

        self.serpiente.insert(0, (nx, ny))

        if self.comida and (nx, ny) == self.comida:
            self._ate_food = True
            self.comida = None
        else:
            self.serpiente.pop()

    def _dibujar_celda(self, x, y, color):
        x1, y1 = x * self.cell, y * self.cell
        x2, y2 = x1 + self.cell, y1 + self.cell
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='#000000')

    def _dibujar(self):
        self.canvas.delete('all')
        self.label_score.config(text="PUNTUACION\n" + str(self.score))

        if self.comida:
            self._dibujar_celda(self.comida[0], self.comida[1], '#FF0000')

        for i, (sx, sy) in enumerate(self.serpiente):
            color = '#00FF00' if i == 0 else '#33CC33'
            self._dibujar_celda(sx, sy, color)

    def _game_over(self):
        tkMessageBox.showinfo("Juego Terminado", "Puntuacion Final: " + str(self.score))
        self.root.destroy()
        sys.exit(0)


def run_game(data):

    juego = SnakeEngine(data)

    juego.root.mainloop()
    