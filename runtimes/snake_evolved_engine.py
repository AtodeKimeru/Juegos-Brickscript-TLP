# -*- coding: utf-8 -*-
# runtime.py - Actividad 4: Snake Evolucionado y Tetris Remake
import sys, json, random, Tkinter as tk, tkMessageBox, bisect, math

from runtimes.events import get_actions

def seleccion_ponderada(nombres, pesos):
    total = sum(pesos)
    acc = []
    s = 0
    for p in pesos:
        s += p
        acc.append(s)
    r = random.uniform(0, total)
    idx = bisect.bisect_left(acc, r)
    if idx >= len(nombres): idx = len(nombres)-1
    return nombres[idx]

class Juego:
    def __init__(self, datos):
        self.datos = datos
        self.tipo = datos.get('tipo_juego', 'TETRIS')
        cfg = datos.get('config', {})
        self.w = cfg.get('grid_size', [10,20])[0]
        self.h = cfg.get('grid_size', [10,20])[1]
        self.grid = [[0]*self.w for _ in range(self.h)]
        self.score = 0
        self.terminado = False

        # Normalizar shapes
        self._normalizar_shapes()

        # Tetris
        self.pieza_actual = None
        self.pieza_nombre = None
        self.pieza_x = self.pieza_y = self.pieza_rot = 0
        self.pieza_color = '#00FFFF'
        self.gravedad = 0.4
        self.lineas_simultaneas = 0
        self.rotaciones_l = 0
        self.powerup_activo = False
        self.pu_x = self.pu_y = 0
        self.pu_datos = None

        # Snake
        self.serpiente = []
        self.dir = (1,0)
        self.comida = None
        self.veneno = None
        self.powerup_item = None
        self.nubes = set()
        self.invencible = False
        self.timer_inv = None
        self.comidas_contador = 0

        # Niveles
        self.niveles = datos.get('niveles', {})
        self.nivel_act = 'BABY'
        self._aplicar_nivel(self.nivel_act)

        # GUI
        self.root = tk.Tk()
        self.root.title("BrickScript - "+self.tipo+" [Act4]")
        self.root.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.cell = 25
        self.canvas = tk.Canvas(self.root, width=self.w*self.cell, height=self.h*self.cell, bg='#111')
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)
        frame = tk.Frame(self.root, width=160, bg='#222')
        frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        self.label_score = tk.Label(frame, text="PUNTUACION\n0", bg='#222', fg='white', font=('Consolas',16,'bold'))
        self.label_score.pack(pady=20)
        if self.tipo == 'SNAKE':
            self.label_nivel = tk.Label(frame, text="NIVEL: BABY", bg='#222', fg='#FFD700', font=('Consolas',10,'bold'))
            self.label_nivel.pack()
            tk.Label(frame, text="1:Baby  2:Entu  3:Nyan", bg='#222', fg='gray', font=('Consolas',8)).pack()
        tk.Frame(frame, height=1, bg='#444').pack(fill=tk.X, padx=10)
        tk.Label(frame, text="POWER-UP", bg='#222', fg='#888', font=('Consolas',9)).pack(pady=(12,0))
        self.canvas_pu = tk.Canvas(frame, width=40, height=40, bg='#111', highlightthickness=1)
        self.canvas_pu.pack(pady=6)
        self.label_pu = tk.Label(frame, text="No disponible", bg='#222', fg='#555', wraplength=140)
        self.label_pu.pack()
        tk.Frame(frame, height=1, bg='#444').pack(fill=tk.X, padx=10)
        self.label_ctrl = tk.Label(frame, text="CONTROLES\nFlechas\nQ: Salir", bg='#222', fg='gray', justify=tk.LEFT)
        self.label_ctrl.pack(pady=16)
        self.root.bind('<Key>', self._tecla)

        self._ejecutar('ON_START')
        self.timer_grav = 0
        self.loop_id = None
        self._loop()

    def _normalizar_shapes(self):
        new = {}
        for name, data in self.datos.get('shapes', {}).items():
            if isinstance(data, list):
                new[name] = {'estados': data, 'color': '#00FFFF', 'chance': 10, 'tipo': 'RECTANGLE'}
            else:
                d = data
                new[name] = {
                    'estados': d.get('estados', []),
                    'color': d.get('color', '#00FFFF'),
                    'chance': d.get('chance', 10),
                    'tipo': d.get('tipo', 'RECTANGLE')
                }
        self.datos['shapes'] = new

    def _aplicar_nivel(self, nivel):
        cfg = self.niveles.get(nivel, self.niveles.get('BABY', {'speed':0.15, 'poison_enabled':False, 'clouds_enabled':False, 'powerup_duration':0}))
        self.gravedad = cfg['speed']
        self.poison_ena = cfg.get('poison_enabled', False)
        self.clouds_ena = cfg.get('clouds_enabled', False)
        self.pu_duracion = cfg.get('powerup_duration', 0)
        if self.tipo == 'SNAKE' and hasattr(self, 'label_nivel'):
            self.label_nivel.config(text="NIVEL: "+nivel)

    def cambiar_nivel(self, nivel):
        if nivel in self.niveles:
            self.nivel_act = nivel
            self._aplicar_nivel(nivel)
            self._reiniciar()

    def _reiniciar(self):
        self.terminado = False
        self.score = 0
        self.grid = [[0]*self.w for _ in range(self.h)]
        self.serpiente = []
        self.nubes = set()
        self.comida = self.veneno = self.powerup_item = None
        self.invencible = False
        if self.timer_inv:
            self.root.after_cancel(self.timer_inv)
        self._ejecutar('ON_START')

    def _loop(self):
        if self.terminado:
            self._game_over()
            return
        self.timer_grav += 0.05
        if self.timer_grav >= self.gravedad:
            self.timer_grav = 0
            if self.tipo == 'TETRIS' and not self.powerup_activo:
                self._ejecutar('ON_TICK')
            elif self.tipo == 'SNAKE':
                self._ejecutar('ON_TICK')
                # Spawn aleatorio de nubes solo en NYAN CAT
                if self.nivel_act == 'NYAN_CAT' and self.clouds_ena:
                    if not hasattr(self, 'contador_nubes'):
                        self.contador_nubes = 0
                    self.contador_nubes += 1
                    if self.contador_nubes >= 30:   # cada 30 movimientos
                        self.contador_nubes = 0
                        self._spawn_nube_aleatoria()
        self._dibujar()
        self.loop_id = self.root.after(50, self._loop)

    def _cerrar(self):
        if self.loop_id:
            self.root.after_cancel(self.loop_id)
        self.root.destroy()
        sys.exit(0)

    def _tecla(self, ev):
        k = ev.keysym.upper()
        if k == 'Q':
            self._cerrar()
        if self.tipo == 'TETRIS':
            if self.powerup_activo:
                if k == 'LEFT': self._mover_pu(-1,0)
                elif k == 'RIGHT': self._mover_pu(1,0)
                elif k == 'UP': self._mover_pu(0,-1)
                elif k == 'DOWN': self._mover_pu(0,1)
                elif k in ('SPACE','RETURN'): self._fijar_pu()
            else:
                if k == 'UP': self._ejecutar('ON_KEY_UP')
                elif k == 'DOWN': self._ejecutar('ON_KEY_DOWN')
                elif k == 'LEFT': self._ejecutar('ON_KEY_LEFT')
                elif k == 'RIGHT': self._ejecutar('ON_KEY_RIGHT')
        elif self.tipo == 'SNAKE':
            if k == '1': self.cambiar_nivel('BABY')
            elif k == '2': self.cambiar_nivel('ENTHUSIAST')
            elif k == '3': self.cambiar_nivel('NYAN_CAT')
            if k == 'UP': self._snake_dir('UP')
            elif k == 'DOWN': self._snake_dir('DOWN')
            elif k == 'LEFT': self._snake_dir('LEFT')
            elif k == 'RIGHT': self._snake_dir('RIGHT')

    # ------------------ DIBUJO ------------------
    def _dibujar_celda(self, x, y, color, borde='#000'):
        x1,y1 = x*self.cell, y*self.cell
        x2,y2 = x1+self.cell, y1+self.cell
        self.canvas.create_rectangle(x1,y1,x2,y2, fill=color, outline=borde)

    def _dibujar_forma(self, x, y, forma, color, borde='#000'):
        x1,y1 = x*self.cell, y*self.cell
        if forma == 'CIRCLE':
            self.canvas.create_oval(x1,y1, x1+self.cell, y1+self.cell, fill=color, outline=borde)
        elif forma == 'TRIANGLE':
            cx, cy = x1+self.cell/2, y1
            dx, dy = x1+self.cell, y1+self.cell
            ex, ey = x1, y1+self.cell
            self.canvas.create_polygon(cx,cy, dx,dy, ex,ey, fill=color, outline=borde)
        else:
            self.canvas.create_rectangle(x1,y1, x1+self.cell, y1+self.cell, fill=color, outline=borde)

    def _dibujar(self):
        self.canvas.delete('all')
        self.label_score.config(text="PUNTUACION\n"+str(self.score))

        # fondo fijo
        for y in range(self.h):
            for x in range(self.w):
                if self.grid[y][x]:
                    self._dibujar_celda(x,y,'#343434')

        if self.tipo == 'TETRIS':
            if self.pieza_actual:
                mat = self.pieza_actual[self.pieza_rot]
                for yo,row in enumerate(mat):
                    for xo,v in enumerate(row):
                        if v:
                            self._dibujar_celda(self.pieza_x+xo, self.pieza_y+yo, self.pieza_color)
            if self.powerup_activo and self.pu_datos:
                col = self.pu_datos.get('color','#FF69B4')
                mat = self.pu_datos['estados'][0]
                for yo,row in enumerate(mat):
                    for xo,v in enumerate(row):
                        if v:
                            self._dibujar_celda(self.pu_x+xo, self.pu_y+yo, col, '#FFF')

        elif self.tipo == 'SNAKE':
            if self.comida:
                self._dibujar_celda(self.comida[0], self.comida[1], '#FF0000')
            if self.veneno and self.poison_ena:
                self._dibujar_celda(self.veneno[0], self.veneno[1], '#8B008B')
            if self.powerup_item and self.pu_duracion>0:
                self._dibujar_celda(self.powerup_item[0], self.powerup_item[1], '#FFD700')
            if self.clouds_ena:
                for (cx,cy) in self.nubes:
                    self._dibujar_celda(cx,cy,'#AAAAAA','#666')
            # serpiente
            colores_arco = ['#FF0000','#FF7F00','#FFFF00','#00FF00','#0000FF','#4B0082','#9400D3']
            for i,(sx,sy) in enumerate(self.serpiente):
                if self.nivel_act == 'NYAN_CAT':
                    if i == 0:
                        forma = 'CIRCLE'
                        color = '#FFB347'
                    else:
                        forma = 'TRIANGLE'
                        color = colores_arco[i % len(colores_arco)]
                else:
                    forma = 'RECTANGLE'
                    color = '#00FF00' if i==0 else '#33CC33'
                self._dibujar_forma(sx, sy, forma, color)

    # ------------------ EVENTOS ------------------
    def _ejecutar(self, evento):
        if evento not in self.datos['events']:
            return
        for acc in get_actions(self.datos['events'][evento]):
            if not isinstance(acc, dict):
                continue
            v = acc['accion']
            o = acc['objeto']
            p = acc['params']

            if v == 'GAME_OVER':
                self.terminado = True
            elif v == 'INCREASE_SCORE':
                self.score += int(o)
            elif v == 'DECREASE_SCORE':
                self.score -= int(o)
                if self.score < 0:
                    self.terminado = True
            elif v == 'RESET_SCORE':
                self.score = 0

            if self.tipo == 'TETRIS':
                if v == 'SPAWN' and o == 'RANDOM_SHAPE':
                    self._tetris_spawn()
                elif v == 'MOVE' and o == 'CURRENT_PIECE':
                    self._tetris_mover(p[0] if p else 'DOWN')
                elif v == 'ROTATE' and o == 'CURRENT_PIECE':
                    self._tetris_rotar()

            if self.tipo == 'SNAKE':
                if v == 'SPAWN':
                    if o == 'PLAYER':
                        coords = p[0] if p else [self.w//2, self.h//2]
                        self.serpiente = [(coords[0], coords[1])]
                        self.dir = (1,0)
                    elif o == 'FOOD':
                        self._snake_spawn_comida()
                    elif o == 'POISON_FRUIT' and self.poison_ena:
                        self._snake_spawn_veneno()
                    elif o == 'POWERUP' and self.pu_duracion>0:
                        self._snake_spawn_powerup()
                    elif o == 'CLOUD' and self.clouds_ena:
                        if p and len(p[0])==2:
                            self.nubes.add(tuple(p[0]))
                elif v == 'MOVE' and o == 'PLAYER':
                    self._snake_mover()
                elif v == 'SET_DIRECTION':
                    self._snake_dir(o)
                elif v == 'GROW' and o == 'PLAYER':
                    c = int(p[0]) if p else 1
                    for _ in range(c):
                        if self.serpiente:
                            self.serpiente.append(self.serpiente[-1])

    # ------------------ LOGICA TETRIS ------------------
    def _tetris_spawn(self):
        shapes = self.datos['shapes']
        names = shapes.keys()
        pesos = [shapes[n]['chance'] for n in names]
        name = seleccion_ponderada(names, pesos)
        self.pieza_nombre = name
        self.pieza_actual = shapes[name]['estados']
        self.pieza_color = shapes[name]['color']
        self.pieza_x = self.w//2 - 2
        self.pieza_y = 0
        self.pieza_rot = 0
        if self._colision_tetris(self.pieza_x, self.pieza_y, 0):
            self.terminado = True

    def _colision_tetris(self, x, y, rot):
        if not self.pieza_actual: return False
        mat = self.pieza_actual[rot]
        for yo,row in enumerate(mat):
            for xo,v in enumerate(row):
                if v:
                    nx, ny = x+xo, y+yo
                    if nx<0 or nx>=self.w or ny>=self.h or ny<0 or (ny>=0 and self.grid[ny][nx]):
                        return True
        return False

    def _tetris_mover(self, direc):
        if not self.pieza_actual: return
        dx,dy = {'LEFT':(-1,0), 'RIGHT':(1,0), 'DOWN':(0,1)}.get(direc, (0,0))
        if not self._colision_tetris(self.pieza_x+dx, self.pieza_y+dy, self.pieza_rot):
            self.pieza_x += dx
            self.pieza_y += dy
        elif dy>0:
            self._tetris_fijar()

    def _tetris_rotar(self):
        if not self.pieza_actual: return
        new_rot = (self.pieza_rot+1)%len(self.pieza_actual)
        if not self._colision_tetris(self.pieza_x, self.pieza_y, new_rot):
            self.pieza_rot = new_rot
            if self.pieza_nombre == 'L_PIECE':
                self.rotaciones_l += 1
                self._verificar_powerup()

    def _tetris_fijar(self):
        mat = self.pieza_actual[self.pieza_rot]
        for yo,row in enumerate(mat):
            for xo,v in enumerate(row):
                if v:
                    ny, nx = self.pieza_y+yo, self.pieza_x+xo
                    if 0<=ny<self.h and 0<=nx<self.w:
                        self.grid[ny][nx] = 1
        self.pieza_actual = None
        self._tetris_limpiar()
        self._ejecutar('ON_START')

    def _tetris_limpiar(self):
        nuevas = [fila for fila in self.grid if not all(fila)]
        lineas = self.h - len(nuevas)
        if lineas>0:
            self.grid = [[0]*self.w for _ in range(lineas)] + nuevas
            self.lineas_simultaneas = lineas
            self._verificar_powerup()
            for _ in range(lineas):
                self._ejecutar('ON_LINE_CLEAR')
        else:
            self.lineas_simultaneas = 0

    def _verificar_powerup(self):
        if self.powerup_activo: return
        for name, pu in self.datos.get('powerups',{}).items():
            ok = True
            for cond in pu.get('condiciones',[]):
                t = cond['tipo']
                v = cond['valor']
                if t == 'LINES_CLEARED_AT_ONCE' and self.lineas_simultaneas < v:
                    ok=False
                elif t == 'L_PIECE_ROTATIONS' and self.rotaciones_l < v:
                    ok=False
            if ok and pu['condiciones']:
                self.pu_datos = pu
                self._powerup_spawn()
                break

    def _powerup_spawn(self):
        self.powerup_activo = True
        self.pu_x = self.w//2
        self.pu_y = 0
        self.pieza_actual = None
        self.lineas_simultaneas = 0
        self.rotaciones_l = 0
        self._dibujar_estrella(self.pu_datos.get('color','#FF69B4'), True)

    def _mover_pu(self, dx, dy):
        nx, ny = self.pu_x+dx, self.pu_y+dy
        if 0<=nx<self.w: self.pu_x = nx
        if 0<=ny<self.h: self.pu_y = ny

    def _fijar_pu(self):
        x = self.pu_x
        for y in range(self.h):
            self.grid[y][x] = 0
        self.powerup_activo = False
        self.pu_datos = None
        self.score += 500
        self._dibujar_estrella('#FF69B4', False)
        self._ejecutar('ON_START')

    def _dibujar_estrella(self, color, activo):
        self.canvas_pu.delete('all')
        if not activo: return
        cx,cy,r1,r2 = 20,20,16,7
        pts = []
        for i in range(10):
            ang = math.pi/2 + i*math.pi/5
            r = r1 if i%2==0 else r2
            pts.append(cx + r*math.cos(ang))
            pts.append(cy - r*math.sin(ang))
        self.canvas_pu.create_polygon(pts, fill=color, outline='#FFF')

    # ------------------ LOGICA SNAKE ------------------
    def _snake_spawn_comida(self):
        while True:
            x = random.randint(0,self.w-1)
            y = random.randint(0,self.h-1)
            if (x,y) not in self.serpiente and (x,y) not in self.nubes:
                self.comida = (x,y)
                break

    def _snake_spawn_veneno(self):
        while True:
            x = random.randint(0,self.w-1)
            y = random.randint(0,self.h-1)
            if (x,y) not in self.serpiente and (x,y) not in self.nubes and (x,y) != self.comida:
                self.veneno = (x,y)
                break

    def _snake_spawn_powerup(self):
        while True:
            x = random.randint(0,self.w-1)
            y = random.randint(0,self.h-1)
            if (x,y) not in self.serpiente and (x,y) not in self.nubes and (x,y) != self.comida and (x,y) != self.veneno:
                self.powerup_item = (x,y)
                break
    
    def _spawn_nube_aleatoria(self):
        """Genera una nube en una posición libre (no ocupada por serpiente, comida, veneno, powerup ni otra nube).
        Solo funciona si self.clouds_ena es True (nivel NYAN CAT)."""
        if not self.clouds_ena:
            return
        # Intentar hasta 100 veces encontrar una celda vacía
        for _ in range(100):
            x = random.randint(0, self.w-1)
            y = random.randint(0, self.h-1)
            ocupado = ((x,y) in self.serpiente or 
                    (x,y) == self.comida or 
                    (x,y) == self.veneno or 
                    (x,y) == self.powerup_item or 
                    (x,y) in self.nubes)
            if not ocupado:
                self.nubes.add((x,y))
                break

    def _snake_dir(self, d):
        if d == 'UP' and self.dir[1] != 1:
            self.dir = (0,-1)
        elif d == 'DOWN' and self.dir[1] != -1:
            self.dir = (0,1)
        elif d == 'LEFT' and self.dir[0] != 1:
            self.dir = (-1,0)
        elif d == 'RIGHT' and self.dir[0] != -1:
            self.dir = (1,0)

    def _snake_mover(self):
        if not self.serpiente:
            return
        head = self.serpiente[0]
        nx, ny = head[0] + self.dir[0], head[1] + self.dir[1]

        # Pared 
        if not (0 <= nx < self.w and 0 <= ny < self.h):
            self._ejecutar('ON_COLLISION_WALL')
            return

        # Autocolisión 
        if (nx, ny) in self.serpiente[:-1]:
            self._ejecutar('ON_COLLISION_SELF')
            return

        # Nube (solo si está habilitada, ej. NYAN CAT) 
        if self.clouds_ena and (nx, ny) in self.nubes:
            if not self.invencible:
                antes = self.score
                self._ejecutar('ON_HIT_CLOUD')   # Normalmente RESET_SCORE
                if antes == 0:
                    self.terminado = True
                # Si tenía puntos, se queda en 0 y sigue vivo
            return   # No mover la serpiente hacia la nube

        # Comida normal 
        if (nx, ny) == self.comida:
            self.serpiente.insert(0, (nx, ny))
            self._ejecutar('ON_EAT_FOOD')
            self.comidas_contador += 1
            if self.comidas_contador >= 5 and self.pu_duracion > 0 and not self.invencible:
                self._activar_invencible()
                self.comidas_contador = 0
            self.comida = None
        # Fruta venenosa 
        elif self.poison_ena and (nx, ny) == self.veneno:
            self.serpiente.insert(0, (nx, ny))
            self._ejecutar('ON_EAT_POISON')
            self.veneno = None
        # Power-up item 
        elif self.pu_duracion > 0 and (nx, ny) == self.powerup_item:
            self.serpiente.insert(0, (nx, ny))
            self._ejecutar('ON_COLLECT_POWERUP')
            self._activar_invencible()
            self.powerup_item = None
        # Movimiento normal sin comer nada 
        else:
            self.serpiente.insert(0, (nx, ny))
            self.serpiente.pop()

        # respawn elementos
        if self.comida is None:
            self._snake_spawn_comida()
        if self.poison_ena and self.veneno is None and random.random() < 0.1:
            self._snake_spawn_veneno()
        if self.pu_duracion > 0 and self.powerup_item is None and random.random() < 0.05:
            self._snake_spawn_powerup()

    def _activar_invencible(self):
        self.invencible = True
        if self.timer_inv:
            self.root.after_cancel(self.timer_inv)
        self.timer_inv = self.root.after(int(self.pu_duracion*1000), self._desactivar_invencible)
        self.label_pu.config(text="INVENCIBLE!", fg='#FFD700')

    def _desactivar_invencible(self):
        self.invencible = False
        self.label_pu.config(text="No disponible", fg='#555')

    def _game_over(self):
        tkMessageBox.showinfo("Game Over", "Puntuacion final: "+str(self.score))
        self.root.destroy()
        sys.exit(0)


def run_game(data):
    juego = Juego(data)
    juego.root.mainloop()


if __name__ == '__main__':
    if len(sys.argv)!=2:
        print "Uso: python runtime.py <archivo.json>"
        sys.exit(1)
    with open(sys.argv[1],'r') as f:
        data = json.load(f)
    juego = Juego(data)
    juego.root.mainloop()