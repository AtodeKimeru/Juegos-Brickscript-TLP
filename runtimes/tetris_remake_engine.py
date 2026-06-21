# -*- coding: utf-8 -*-
# runtime.py - Actividad 3: Version Extendida
# Compatible con Python 2.7
# RETROCOMPATIBLE: acepta JSONs generados por el compiler.py original

import sys
import json
import random
import Tkinter as tk
import tkMessageBox

from runtimes.events import get_actions


# ===========================================================================
# SELECCION PONDERADA SIN NUMPY (Python 2.7 puro)
# Implementacion manual de random.choices() usando bisect
# ===========================================================================
import bisect

def seleccion_ponderada(nombres, pesos):
    """
    Selecciona un elemento de 'nombres' de forma ponderada segun 'pesos'.
    Equivalente a random.choices(nombres, weights=pesos, k=1)[0]
    pero compatible con Python 2.7 sin numpy ni librerias externas.
    Algoritmo: acumulados + busqueda binaria (O(n) build, O(log n) lookup).
    """
    total = sum(pesos)
    acumulados = []
    acum = 0
    for p in pesos:
        acum += p
        acumulados.append(acum)
    r = random.uniform(0, total)
    indice = bisect.bisect_left(acumulados, r)
    # Clampear por si hay error de punto flotante en el limite
    if indice >= len(nombres):
        indice = len(nombres) - 1
    return nombres[indice]


class Juego:
    def __init__(self, datos_juego):
        self.datos_juego = datos_juego
        self.tipo_juego = self.datos_juego.get('tipo_juego', 'TETRIS')
        config = self.datos_juego.get('config', {})
        self.ancho = config.get('grid_size', [10, 20])[0]
        self.alto  = config.get('grid_size', [10, 20])[1]
        self.grid  = [[0 for _ in range(self.ancho)] for _ in range(self.alto)]
        self.puntuacion    = 0
        self.juego_terminado = False

        # -------------------------------------------------------
        # NUEVO (A3): normalizar shapes al formato extendido
        # Garantiza retrocompatibilidad con JSONs del compiler antiguo
        # -------------------------------------------------------
        self._normalizar_shapes()

        # -------------------------------------------------------
        # NUEVO (A3): contadores para condiciones del power-up
        # -------------------------------------------------------
        self.lineas_limpiadas_simultaneas = 0  # lineas en el ultimo turno
        self.rotaciones_l_piece = 0            # rotaciones totales de L_PIECE
        self.powerup_disponible = False        # se activo la condicion?
        self.powerup_activo = False            # hay un powerup en juego?
        self.powerup_x = 0
        self.powerup_y = 0
        self.powerup_datos = None              # datos del powerup seleccionado

        # --- Configuracion de la GUI ---
        self.root = tk.Tk()
        self.root.title("BrickScript - " + self.tipo_juego + " [Remake]")
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)

        self.taman_celda  = 25
        self.ancho_canvas = self.ancho * self.taman_celda
        self.alto_canvas  = self.alto  * self.taman_celda

        self.canvas = tk.Canvas(
            self.root,
            width=self.ancho_canvas,
            height=self.alto_canvas,
            bg='#111111'
        )
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)

        self.marco_score = tk.Frame(self.root, width=160, bg='#222222')
        self.marco_score.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        self.label_score = tk.Label(
            self.marco_score,
            text="PUNTUACION\n0",
            bg='#222222', fg='white',
            font=('Consolas', 16, 'bold')
        )
        self.label_score.pack(pady=30, padx=10)

        # NUEVO (A3): separador visual
        tk.Frame(self.marco_score, height=1, bg='#444444').pack(fill=tk.X, padx=10)

        # NUEVO (A3): titulo seccion power-up
        tk.Label(
            self.marco_score,
            text="POWER-UP",
            bg='#222222', fg='#888888',
            font=('Consolas', 9)
        ).pack(pady=(12, 0), padx=10)

        # NUEVO (A3): indicador grafico del power-up (canvas pequeño)
        self.canvas_pu = tk.Canvas(
            self.marco_score,
            width=40, height=40,
            bg='#111111',
            highlightthickness=1,
            highlightbackground='#444444'
        )
        self.canvas_pu.pack(pady=6)

        # NUEVO (A3): etiqueta de estado del power-up
        self.label_powerup = tk.Label(
            self.marco_score,
            text="No disponible",
            bg='#222222', fg='#555555',
            font=('Consolas', 9),
            wraplength=140
        )
        self.label_powerup.pack(pady=(0, 4), padx=10)

        # NUEVO (A3): instruccion de activacion
        self.label_pu_key = tk.Label(
            self.marco_score,
            text="",
            bg='#222222', fg='#FF69B4',
            font=('Consolas', 9, 'bold'),
            wraplength=140
        )
        self.label_pu_key.pack(pady=(0, 10), padx=10)

        tk.Frame(self.marco_score, height=1, bg='#444444').pack(fill=tk.X, padx=10)

        self.label_controles = tk.Label(
            self.marco_score,
            text="CONTROLES\n<  >  Mover\n^  Rotar\nv  Bajar\n---\nPU: flechas\n    Enter=colocar",
            bg='#222222', fg='gray',
            font=('Consolas', 9),
            justify=tk.LEFT
        )
        self.label_controles.pack(pady=16, padx=10)

        self.root.bind('<Key>', self.manejar_input_gui)

        if self.tipo_juego == 'TETRIS':
            self.pieza_actual    = None
            self.nombre_pieza_actual = None   # NUEVO (A3): para contar rotaciones de L
            self.pieza_x         = 0
            self.pieza_y         = 0
            self.pieza_rotacion  = 0
            self.color_pieza_actual = '#00FFFF'   # NUEVO (A3)
            self.velocidad_gravedad = 0.4

        if self.tipo_juego == 'SNAKE':
            self.serpiente_cuerpo    = []
            self.serpiente_direccion = (1, 0)
            self.posicion_comida     = None
            self.velocidad_gravedad  = 0.15

        self.timer_gravedad = 0
        self.ejecutar_evento('ON_START')
        self.timer_id = None

    # -------------------------------------------------------
    # NUEVO (A3): normalizar shapes para retrocompatibilidad
    # -------------------------------------------------------
    def _normalizar_shapes(self):
        """
        El compiler antiguo generaba shapes como lista de matrices:
            "T_PIECE": [[[0,1,0],[1,1,1],[0,0,0]], ...]

        El compiler nuevo genera:
            "T_PIECE": {"estados": [...], "color": "#...", "chance": N}

        Este metodo convierte el formato antiguo al nuevo en memoria,
        sin tocar el archivo JSON original.
        """
        shapes_normalizados = {}
        for nombre, datos in self.datos_juego.get('shapes', {}).items():
            if isinstance(datos, list):
                # Formato antiguo -> asignar defaults
                shapes_normalizados[nombre] = {
                    "estados": datos,
                    "color":   "#00FFFF",
                    "chance":  10
                }
            elif isinstance(datos, dict):
                # Formato nuevo -> asegurar que tenga todos los campos
                shapes_normalizados[nombre] = {
                    "estados": datos.get("estados", []),
                    "color":   datos.get("color", "#00FFFF"),
                    "chance":  datos.get("chance", 10)
                }
        self.datos_juego['shapes'] = shapes_normalizados

    def run(self):
        self.root.after(50, self.game_loop)
        self.root.mainloop()

    def game_loop(self):
        if self.juego_terminado:
            self.mostrar_game_over()
            return
        self.timer_gravedad += 0.05
        if self.timer_gravedad >= self.velocidad_gravedad:
            self.timer_gravedad = 0
            if not self.powerup_activo:
                self.ejecutar_evento('ON_TICK')
        self.dibujar()
        self.timer_id = self.root.after(50, self.game_loop)

    def cerrar_ventana(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        self.root.destroy()
        sys.exit(0)

    def manejar_input_gui(self, event):
        key = event.keysym.upper()
        if self.tipo_juego == 'TETRIS':
            # Cuando el power-up esta activo, el jugador lo mueve libremente
            if self.powerup_activo:
                if key == 'LEFT':              self.powerup_mover(-1,  0)
                elif key == 'RIGHT':           self.powerup_mover( 1,  0)
                elif key == 'UP':              self.powerup_mover( 0, -1)
                elif key == 'DOWN':            self.powerup_mover( 0,  1)
                elif key in ('SPACE', 'RETURN'): self.powerup_fijar()
            else:
                # Control normal de la pieza activa
                if key == 'UP':    self.ejecutar_evento('ON_KEY_UP')
                elif key == 'DOWN':  self.ejecutar_evento('ON_KEY_DOWN')
                elif key == 'LEFT':  self.ejecutar_evento('ON_KEY_LEFT')
                elif key == 'RIGHT': self.ejecutar_evento('ON_KEY_RIGHT')
        elif self.tipo_juego == 'SNAKE':
            if key == 'UP':    self.snake_cambiar_direccion('UP')
            elif key == 'DOWN':  self.snake_cambiar_direccion('DOWN')
            elif key == 'LEFT':  self.snake_cambiar_direccion('LEFT')
            elif key == 'RIGHT': self.snake_cambiar_direccion('RIGHT')

    # -------------------------------------------------------
    # DIBUJO
    # -------------------------------------------------------
    def dibujar(self):
        self.canvas.delete("all")
        self.label_score.config(text="PUNTUACION\n" + str(self.puntuacion))

        COLOR_GRID_FIJA   = '#343434'
        COLOR_SNAKE_CABEZA = '#00FF00'
        COLOR_SNAKE_CUERPO = '#33CC33'
        COLOR_FOOD        = '#FF0000'

        # Grid fija
        for y in range(self.alto):
            for x in range(self.ancho):
                if self.grid[y][x] == 1:
                    self.dibujar_celda(x, y, COLOR_GRID_FIJA)

        # NUEVO (A3): pieza activa con su color dinamico
        if self.tipo_juego == 'TETRIS' and self.pieza_actual:
            matriz_pieza = self.pieza_actual[self.pieza_rotacion]
            for y_offset, fila in enumerate(matriz_pieza):
                for x_offset, celda in enumerate(fila):
                    if celda == 1:
                        self.dibujar_celda(
                            self.pieza_x + x_offset,
                            self.pieza_y + y_offset,
                            self.color_pieza_actual   # NUEVO (A3)
                        )

        # NUEVO (A3): dibujar power-up activo
        if self.tipo_juego == 'TETRIS' and self.powerup_activo and self.powerup_datos:
            color_pu = self.powerup_datos.get('color', '#FF69B4')
            estado_pu = self.powerup_datos.get('estados', [[[1]]])[0]
            for y_offset, fila in enumerate(estado_pu):
                for x_offset, celda in enumerate(fila):
                    if celda == 1:
                        self.dibujar_celda(
                            self.powerup_x + x_offset,
                            self.powerup_y + y_offset,
                            color_pu,
                            borde='#FFFFFF'
                        )

        # Snake
        if self.tipo_juego == 'SNAKE':
            if self.posicion_comida:
                x, y = self.posicion_comida
                self.dibujar_celda(x, y, COLOR_FOOD)
            for i, segmento in enumerate(self.serpiente_cuerpo):
                x, y = segmento
                color = COLOR_SNAKE_CABEZA if i == 0 else COLOR_SNAKE_CUERPO
                self.dibujar_celda(x, y, color)

    def dibujar_celda(self, x, y, color, borde='#000000'):
        ts = self.taman_celda
        x1, y1 = x * ts, y * ts
        x2, y2 = x1 + ts, y1 + ts
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=borde)

    # -------------------------------------------------------
    # EVENTOS
    # -------------------------------------------------------
    def ejecutar_evento(self, nombre_evento):
        if nombre_evento in self.datos_juego['events']:
            for accion in get_actions(self.datos_juego['events'][nombre_evento]):
                if not isinstance(accion, dict):
                    continue
                verbo  = accion.get('accion')
                objeto = accion.get('objeto')

                if verbo == 'INCREASE_SCORE':
                    self.puntuacion += int(objeto)
                if verbo == 'GAME_OVER':
                    self.juego_terminado = True

                if self.tipo_juego == 'TETRIS':
                    if verbo == 'SPAWN':
                        self.tetris_spawn_pieza()
                    if verbo == 'MOVE':
                        self.tetris_mover_pieza(accion['params'][0])
                    if verbo == 'ROTATE':
                        self.tetris_rotar_pieza()

                if self.tipo_juego == 'SNAKE':
                    if verbo == 'SPAWN' and objeto == 'PLAYER':
                        self.snake_spawn_jugador(accion)
                    if verbo == 'SPAWN' and objeto == 'FOOD':
                        self.snake_spawn_comida()
                    if verbo == 'MOVE' and objeto == 'PLAYER':
                        self.snake_mover_jugador()
                    if verbo == 'GROW':
                        self.snake_crecer()

    # -------------------------------------------------------
    # LOGICA TETRIS
    # -------------------------------------------------------

    # NUEVO (A3): spawn ponderado por CHANCE
    def tetris_spawn_pieza(self):
        shapes = self.datos_juego['shapes']
        nombres = list(shapes.keys())
        pesos   = [shapes[n]['chance'] for n in nombres]

        # Seleccion ponderada sin numpy
        nombre_pieza = seleccion_ponderada(nombres, pesos)

        self.nombre_pieza_actual    = nombre_pieza         # NUEVO (A3)
        self.pieza_actual           = shapes[nombre_pieza]['estados']
        self.color_pieza_actual     = shapes[nombre_pieza]['color']  # NUEVO (A3)
        self.pieza_x                = self.ancho / 2 - 2
        self.pieza_y                = 0
        self.pieza_rotacion         = 0

        if self.tetris_verificar_colision(self.pieza_x, self.pieza_y, self.pieza_rotacion):
            self.juego_terminado = True

    def tetris_mover_pieza(self, direccion):
        if not self.pieza_actual:
            return
        dx, dy = 0, 0
        if direccion == 'LEFT':  dx = -1
        elif direccion == 'RIGHT': dx = 1
        elif direccion == 'DOWN':  dy = 1

        if not self.tetris_verificar_colision(
            self.pieza_x + dx, self.pieza_y + dy, self.pieza_rotacion
        ):
            self.pieza_x += dx
            self.pieza_y += dy
        elif dy > 0:
            self.tetris_fijar_pieza()

    # NUEVO (A3): contar rotaciones de L_PIECE para la condicion del power-up
    def tetris_rotar_pieza(self):
        if not self.pieza_actual:
            return
        nueva_rotacion = (self.pieza_rotacion + 1) % len(self.pieza_actual)
        if not self.tetris_verificar_colision(self.pieza_x, self.pieza_y, nueva_rotacion):
            self.pieza_rotacion = nueva_rotacion
            # NUEVO (A3): contar rotaciones de L_PIECE
            if self.nombre_pieza_actual == 'L_PIECE':
                self.rotaciones_l_piece += 1
                self._verificar_condiciones_powerup()

    def tetris_fijar_pieza(self):
        matriz_pieza = self.pieza_actual[self.pieza_rotacion]
        for y_offset, fila in enumerate(matriz_pieza):
            for x_offset, celda in enumerate(fila):
                if celda == 1:
                    ny = self.pieza_y + y_offset
                    nx = self.pieza_x + x_offset
                    if 0 <= ny < self.alto and 0 <= nx < self.ancho:
                        self.grid[ny][nx] = 1
        self.pieza_actual = None
        self.nombre_pieza_actual = None
        self.tetris_limpiar_lineas()
        self.ejecutar_evento('ON_START')

    def tetris_verificar_colision(self, x, y, rotacion):
        if not self.pieza_actual:
            return False
        matriz_pieza = self.pieza_actual[rotacion]
        for y_offset, fila in enumerate(matriz_pieza):
            for x_offset, celda in enumerate(fila):
                if celda == 1:
                    nx = x + x_offset
                    ny = y + y_offset
                    if not (0 <= nx < self.ancho and 0 <= ny < self.alto and
                            self.grid[ny][nx] == 0):
                        return True
        return False

    # NUEVO (A3): limpiar_lineas ahora cuenta lineas simultaneas
    def tetris_limpiar_lineas(self):
        nuevo_grid = [fila for fila in self.grid if not all(fila)]
        lineas_limpias = self.alto - len(nuevo_grid)
        if lineas_limpias > 0:
            self.grid = [[0] * self.ancho for _ in range(lineas_limpias)] + nuevo_grid
            # NUEVO (A3): guardar cuantas lineas se limpiaron de una vez
            self.lineas_limpiadas_simultaneas = lineas_limpias
            self._verificar_condiciones_powerup()
            for _ in range(lineas_limpias):
                self.ejecutar_evento('ON_LINE_CLEAR')
        else:
            self.lineas_limpiadas_simultaneas = 0

    # -------------------------------------------------------
    # NUEVO (A3): LOGICA DE POWER-UPS
    # -------------------------------------------------------

    def _verificar_condiciones_powerup(self):
        """
        Revisa si se cumplen TODAS las condiciones definidas en algun powerup.
        Si se cumplen, lanza el power-up AUTOMATICAMENTE (sin necesidad de tecla).
        """
        # No lanzar si ya hay uno activo
        if self.powerup_activo:
            return
        powerups = self.datos_juego.get('powerups', {})
        for nombre_pu, datos_pu in powerups.items():
            condiciones = datos_pu.get('condiciones', [])
            cumplidas = True
            for cond in condiciones:
                tipo  = cond.get('tipo', '')
                valor = cond.get('valor', 0)
                if tipo == 'LINES_CLEARED_AT_ONCE':
                    if self.lineas_limpiadas_simultaneas < valor:
                        cumplidas = False
                        break
                elif tipo == 'L_PIECE_ROTATIONS':
                    if self.rotaciones_l_piece < valor:
                        cumplidas = False
                        break
            if cumplidas and condiciones:
                self.powerup_datos = datos_pu
                # AUTO-SPAWN: lanza directamente sin necesidad de tecla
                self.powerup_spawn()
                break

    def _dibujar_canvas_pu(self, color, activo):
        """Dibuja el indicador visual del power-up en el canvas lateral."""
        self.canvas_pu.delete("all")
        if not activo:
            # Vacio, sin power-up
            return
        # Dibujar estrella de 5 puntas centrada en 20,20
        import math
        cx, cy, r_ext, r_int = 20, 20, 16, 7
        puntos = []
        for i in range(10):
            angulo = math.pi / 2 + i * math.pi / 5
            r = r_ext if i % 2 == 0 else r_int
            puntos.append(cx + r * math.cos(angulo))
            puntos.append(cy - r * math.sin(angulo))
        self.canvas_pu.create_polygon(puntos, fill=color, outline='#FFFFFF', width=1)

    def powerup_spawn(self):
        """Hace aparecer el powerup en la parte superior del tablero."""
        if not self.powerup_datos:
            return
        self.powerup_activo = True
        self.powerup_disponible = False
        # Aparece centrado para que el jugador tenga espacio a ambos lados
        self.powerup_x = self.ancho / 2
        self.powerup_y = 0
        self.lineas_limpiadas_simultaneas = 0
        self.rotaciones_l_piece = 0
        # Suspender la pieza actual: el jugador controla solo el PU
        self.pieza_actual = None
        self.nombre_pieza_actual = None
        color_pu = self.powerup_datos.get('color', '#FF69B4')
        self._dibujar_canvas_pu(color_pu, True)
        self.label_powerup.config(text="MOVER PU:", fg='#FF69B4')
        self.label_pu_key.config(text="Flechas: mover\nEnter: colocar")

    def powerup_mover(self, dx, dy):
        """Mueve el power-up libremente en cualquier direccion, traspasa bloques."""
        nx = self.powerup_x + dx
        ny = self.powerup_y + dy
        # Solo limitar al borde del tablero; ignora bloques existentes
        if 0 <= nx < self.ancho:
            self.powerup_x = nx
        if 0 <= ny < self.alto:
            self.powerup_y = ny

    def powerup_fijar(self):
        """El power-up toca el fondo o una pieza: aplica su efecto."""
        x = self.powerup_x
        # Efecto: elimina todas las celdas ocupadas en esa columna
        for y in range(self.alto):
            self.grid[y][x] = 0
        self.powerup_activo = False
        self.powerup_datos  = None
        self.puntuacion += 500
        self._dibujar_canvas_pu('#FF69B4', False)
        self.label_powerup.config(text="+500 pts!", fg='#FFD700')
        self.label_pu_key.config(text="")
        # Spawnear la siguiente pieza normal
        self.ejecutar_evento('ON_START')

    # -------------------------------------------------------
    # LOGICA SNAKE (sin cambios respecto al original)
    # -------------------------------------------------------
    def snake_spawn_jugador(self, accion):
        coords = accion['params'][0] if accion['params'] else [self.ancho / 2, self.alto / 2]
        self.serpiente_cuerpo    = [(coords[0], coords[1])]
        self.serpiente_direccion = (1, 0)

    def snake_spawn_comida(self):
        while True:
            x = random.randint(0, self.ancho - 1)
            y = random.randint(0, self.alto - 1)
            if (x, y) not in self.serpiente_cuerpo:
                self.posicion_comida = (x, y)
                break

    def snake_mover_jugador(self):
        if not self.serpiente_cuerpo:
            return
        cabeza_x, cabeza_y = self.serpiente_cuerpo[0]
        dir_x, dir_y = self.serpiente_direccion
        nueva_cabeza = (cabeza_x + dir_x, cabeza_y + dir_y)
        if not (0 <= nueva_cabeza[0] < self.ancho and 0 <= nueva_cabeza[1] < self.alto):
            self.ejecutar_evento('ON_COLLISION_WALL')
            return
        if nueva_cabeza in self.serpiente_cuerpo[:-1]:
            self.ejecutar_evento('ON_COLLISION_SELF')
            return
        self.serpiente_cuerpo.insert(0, nueva_cabeza)
        if nueva_cabeza == self.posicion_comida:
            self.ejecutar_evento('ON_EAT_FOOD')
        else:
            self.serpiente_cuerpo.pop()

    def snake_cambiar_direccion(self, direccion):
        if direccion == 'UP'    and self.serpiente_direccion[1] != 1:
            self.serpiente_direccion = (0, -1)
        elif direccion == 'DOWN'  and self.serpiente_direccion[1] != -1:
            self.serpiente_direccion = (0, 1)
        elif direccion == 'LEFT'  and self.serpiente_direccion[0] != 1:
            self.serpiente_direccion = (-1, 0)
        elif direccion == 'RIGHT' and self.serpiente_direccion[0] != -1:
            self.serpiente_direccion = (1, 0)

    def snake_crecer(self):
        pass

    # -------------------------------------------------------
    # GAME OVER
    # -------------------------------------------------------
    def mostrar_game_over(self):
        tkMessageBox.showinfo("Juego Terminado", "Puntuacion Final: " + str(self.puntuacion))
        self.root.destroy()
        sys.exit(0)


def run_game(data):
    juego = Juego(data)
    juego.run()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Uso: python runtime.py <archivo_juego.json>"
        sys.exit(1)
    archivo_juego = sys.argv[1]
    try:
        with open(archivo_juego, 'r') as f:
            datos_juego = json.load(f)
    except IOError:
        print "Error: No se pudo encontrar el archivo " + archivo_juego
        sys.exit(1)
    juego = Juego(datos_juego)
    juego.run()
