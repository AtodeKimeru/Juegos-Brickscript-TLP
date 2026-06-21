# -*- coding: utf-8 -*-
# runtime.py - Tanks (Fijado de Congelamientos y Compilacion)
import sys, json, random, Tkinter as tk, tkMessageBox, bisect, math

from runtimes.events import get_actions

def seleccion_ponderada(nombres, pesos):
    total = sum(pesos)
    acc, s = [], 0
    for p in pesos:
        s += p; acc.append(s)
    r = random.uniform(0, total)
    idx = bisect.bisect_left(acc, r)
    return nombres[idx if idx < len(nombres) else -1]

class Juego:
    def __init__(self, datos):
        # FIX VIDA: Inicializar vida en la primera línea para evitar AttributeError
        self.player_hp = 100 
        self.max_hp = 100
        
        self.datos = datos
        self.tipo = datos.get('tipo_juego', 'TETRIS')
        cfg = datos.get('config', {})
        self.w, self.h = cfg.get('grid_size', [10,20])
        self.grid = [[0]*self.w for _ in range(self.h)]
        self.score, self.terminado, self.gravedad = 0, False, 0.4
        self.triggered_events = set()

        self._normalizar_shapes()

        # Variables Retrocompatibilidad
        self.pieza_actual = self.comida = self.veneno = self.powerup_item = None
        self.pieza_x = self.pieza_y = self.pieza_rot = self.lineas_simultaneas = self.rotaciones_l = 0
        self.pu_x = self.pu_y = 0; self.pu_datos = None
        self.serpiente, self.dir, self.nubes = [], (1,0), set()
        self.invencible = self.powerup_activo = False
        self.timer_inv, self.comidas_contador = None, 0

        self.niveles = datos.get('niveles', {})
        self.nivel_act = 'BABY'
        self._aplicar_nivel(self.nivel_act)

        # ---------------- GUI ----------------
        self.root = tk.Tk(); self.root.title("BrickScript - " + self.tipo)
        self.root.configure(bg='#0B0C10'); self.root.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.cell = 25
        self.canvas = tk.Canvas(self.root, width=self.w*self.cell, height=self.h*self.cell, bg='#1F2833', highlightthickness=2, highlightbackground='#45A29E')
        self.canvas.pack(side=tk.LEFT, padx=15, pady=15)
        
        frame = tk.Frame(self.root, width=180, bg='#0B0C10')
        frame.pack(side=tk.RIGHT, fill=tk.Y, padx=15, pady=15)
        
        self.label_score = tk.Label(frame, text="PUNTUACION\n0", bg='#0B0C10', fg='#66FCF1', font=('Impact', 20)); self.label_score.pack(pady=10)
        
        if self.tipo == 'TANKS':
            self.label_hp = tk.Label(frame, text="VIDA: 100", bg='#0B0C10', fg='#FF4C4C', font=('Consolas', 14, 'bold')); self.label_hp.pack(pady=5)
            self.label_ctrl = tk.Label(frame, text="CONTROLES:\n▲▼◄► : Mover\n[Espacio] : Disparar\n[Q] : Salir", bg='#0B0C10', fg='#C5C6C7', font=('Consolas', 9), justify=tk.LEFT)
        else:
            self.label_ctrl = tk.Label(frame, text="CONTROLES:\nFlechas : Jugar\n[Q] : Salir", bg='#0B0C10', fg='#C5C6C7', font=('Consolas', 9), justify=tk.LEFT)
        self.label_ctrl.pack(pady=10)
        
        self.root.bind('<Key>', self._tecla)

        self._ejecutar('ON_START')
        if self.tipo == 'TANKS': self._tanks_init()
        self.timer_grav, self.loop_id = 0, None
        self._loop()

    def _normalizar_shapes(self):
        new = {}
        for name, data in self.datos.get('shapes', {}).items():
            if isinstance(data, list): new[name] = {'estados': data, 'color': '#00FFFF', 'chance': 10, 'tipo': 'RECTANGLE', 'hp':1, 'damage':1}
            else: new[name] = {'estados': data.get('estados', []), 'color': data.get('color', '#00FFFF'), 'chance': data.get('chance', 10), 'tipo': data.get('tipo', 'RECTANGLE'), 'hp': data.get('hp', 1), 'damage': data.get('damage', 1)}
        self.datos['shapes'] = new

    def _aplicar_nivel(self, nivel):
        cfg = self.niveles.get(nivel, self.niveles.get('BABY', {'speed':0.15}))
        self.gravedad = cfg['speed']

    def _reiniciar(self):
        self.terminado, self.score = False, 0
        self.grid = [[0]*self.w for _ in range(self.h)]
        self._ejecutar('ON_START')

    def _loop(self):
        if self.terminado: self._game_over(); return
        self.timer_grav += 0.05
        if self.timer_grav >= self.gravedad:
            self.timer_grav = 0
            if self.tipo == 'TETRIS' and not self.powerup_activo: self._ejecutar('ON_TICK')
            elif self.tipo == 'SNAKE': self._ejecutar('ON_TICK')
            elif self.tipo == 'TANKS': self._tanks_update()
        self._dibujar(); self.loop_id = self.root.after(50, self._loop)

    def _cerrar(self):
        if self.loop_id: self.root.after_cancel(self.loop_id)
        self.root.destroy(); sys.exit(0)

    def _tecla(self, ev):
        k = ev.keysym.upper()
        if k == 'Q': self._cerrar()
        if self.tipo == 'TANKS':
            nx, ny = self.player['x'], self.player['y']
            
            if k == 'LEFT' and nx > 0: nx -= 1
            elif k == 'RIGHT' and nx < self.w-1: nx += 1
            elif k == 'UP' and ny > 0: ny -= 1
            elif k == 'DOWN' and ny < self.h-1: ny += 1
            
            if k in ['LEFT', 'RIGHT', 'UP', 'DOWN']:
                colision = False
                for w in self.walls:
                    if w['x'] == nx and w['y'] == ny: colision = True; break
                if self.boss:
                    if self.boss['x'] <= nx < self.boss['x'] + self.boss['w']:
                        if self.boss['y'] <= ny < self.boss['y'] + self.boss['h']: colision = True
                
                if not colision:
                    self.player['x'], self.player['y'] = nx, ny
                    
            elif k == 'SPACE': 
                self._tank_shoot()

    def _dibujar_celda(self, x, y, color, borde='#111111'):
        x1, y1 = x * self.cell, y * self.cell
        x2, y2 = x1 + self.cell, y1 + self.cell
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=borde, width=1)
        self.canvas.create_rectangle(x1+2, y1+2, x2-2, y2-2, fill='', outline='#FFFFFF', width=1, stipple='gray50')

    def _dibujar(self):
        self.canvas.delete('all')
        self.label_score.config(text="PUNTUACION\n" + str(self.score))
        if self.tipo == 'TANKS': self.label_hp.config(text="VIDA: " + str(self.player_hp))

        if self.tipo == 'TANKS':
            for w in self.walls:
                self._dibujar_celda(w['x'], w['y'], '#888888', '#555555')
                
            self._dibujar_celda(self.player['x'], self.player['y'], self.player_shape.get('color', '#66FCF1'))
            
            for e in self.enemies: self._dibujar_celda(e['x'], e['y'], e.get('color', '#FF4C4C'))
            
            for b in self.bullets: self.canvas.create_line(b['x']*self.cell+12, b['y']*self.cell, b['x']*self.cell+12, (b['y']+1)*self.cell, fill='#FFFF00', width=3)
            for b in self.enemy_bullets: self.canvas.create_line(b['x']*self.cell+12, b['y']*self.cell, b['x']*self.cell+12, (b['y']+1)*self.cell, fill='#FF7700', width=2)
            
            for h in self.hammers: self.canvas.create_polygon(h['x']*self.cell+12, h['y']*self.cell, h['x']*self.cell+25, h['y']*self.cell+25, h['x']*self.cell, h['y']*self.cell+25, fill='#FFD700', outline='#FFF', width=1)
            
            if self.boss:
                for y in range(self.boss['h']):
                    for x in range(self.boss['w']):
                        self._dibujar_celda(self.boss['x'] + x, self.boss['y'] + y, self.boss['color'])

    def _ejecutar(self, evento):
        if evento not in self.datos.get('events', {}): return
        for acc in get_actions(self.datos['events'][evento]):
            if not isinstance(acc, dict): continue
            
            v = acc.get('accion')
            o = acc.get('objeto')
            p = acc.get('params', [])
            
            if v == 'GAME_OVER': self.terminado = True
            elif v == 'INCREASE_SCORE': self.score += int(o) if o else 0
            elif v == 'DECREASE_SCORE': self.score -= int(o) if o else 0
            
            if self.tipo == 'TANKS' and v == 'SPAWN' and o in self.datos.get('bosses', {}):
                self._spawn_boss_fallback()

    def _tanks_init(self):
        self.player_shape = {'color': '#00FF00', 'hp': 100, 'damage': 1}
        self.enemy_shapes = []
        for name, d in self.datos.get('shapes', {}).items():
            if d.get('tipo', '') == 'PLAYER': self.player_shape = d
            elif d.get('tipo', '') == 'ENEMY': self.enemy_shapes.append(d)
            
        if not self.enemy_shapes: self.enemy_shapes = [{'color': '#FF0000', 'hp': 1, 'damage': 10}]
            
        self.player = {'x': self.w // 2, 'y': self.h - 2, 'dir': 'UP'}
        self.player_hp = self.player_shape.get('hp', 100)
        self.max_hp = self.player_hp
        
        self.enemies, self.bullets, self.enemy_bullets, self.hammers, self.walls = [], [], [], [], []
        self.boss = None; self.boss_spawned = False
        
        for i in range(12):
            self.walls.append({'x': random.randint(1, self.w-2), 'y': random.randint(4, self.h-6), 'hp': 3})
            
        self._spawn_tank_wave()

    def _spawn_tank_wave(self):
        for i in range(5):
            esh = random.choice(self.enemy_shapes)
            self.enemies.append({
                'x': random.randint(0, self.w-1), 'y': random.randint(0, 3),
                'hp': esh.get('hp', 1), 'damage': esh.get('damage', 10),
                'color': esh.get('color', '#FF0000'), 'dir': random.choice([-1, 1])
            })

    def _tank_shoot(self):
        self.bullets.append({'x': self.player['x'], 'y': self.player['y'] - 1})

    def _tanks_update(self):
        # FIX: Lectura segura del Target Score para que no crashee si viene mal en el archivo
        for ev_name in self.datos.get('events', {}).keys():
            if ev_name.startswith('ON_TARGET_SCORE_'):
                try:
                    tgt = int(ev_name.split('_')[-1])
                    if self.score >= tgt and ev_name not in self.triggered_events:
                        self._ejecutar(ev_name)
                        self.triggered_events.add(ev_name)
                except ValueError: pass

        # Invocación de Respaldo por si el evento falla al leerse
        if self.score >= 1000 and not self.boss_spawned:
            self._spawn_boss_fallback()

        self._update_bullets()
        self._enemy_shoot()
        
        if random.random() < 0.005:
            self.hammers.append({'x': random.randint(0, self.w-1), 'y': random.randint(0, self.h-1)})
            
        self._update_enemy_bullets()
        
        for h in self.hammers[:]:
            if h['x'] == self.player['x'] and h['y'] == self.player['y']:
                self.player_hp = min(self.max_hp, self.player_hp + 25)
                self.hammers.remove(h)
                
        if len(self.enemies) == 0 and not self.boss_spawned:
            self._spawn_tank_wave()

    def _enemy_shoot(self):
        if random.random() < 0.05 and self.enemies:
            e = random.choice(self.enemies)
            self.enemy_bullets.append({'x': e['x'], 'y': e['y'] + 1, 'dmg': e['damage']})
            
        if self.boss and random.random() < 0.15:
            bx = self.boss['x'] + random.randint(0, self.boss['w']-1)
            self.enemy_bullets.append({'x': bx, 'y': self.boss['y'] + self.boss['h'], 'dmg': self.boss.get('damage', 30)})

        for e in self.enemies:
            if random.random() < 0.1:
                e['x'] += e['dir']
                if e['x'] <= 0 or e['x'] >= self.w-1: e['dir'] *= -1

    def _update_bullets(self):
        nuevas = []
        for b in self.bullets:
            b['y'] -= 1
            if b['y'] < 0: continue
            hit = False
            
            for w in self.walls[:]:
                if w['x'] == b['x'] and w['y'] == b['y']:
                    w['hp'] -= 1
                    if w['hp'] <= 0: self.walls.remove(w)
                    hit = True; break
            if hit: continue
            
            for e in self.enemies:
                if int(e['x']) == b['x'] and int(e['y']) == b['y']:
                    e['hp'] -= 1
                    if e['hp'] <= 0:
                        self.enemies.remove(e)
                        self.score += 100
                    hit = True; break
            if hit: continue
            
            if self.boss:
                if self.boss['x'] <= b['x'] < self.boss['x'] + self.boss['w']:
                    if self.boss['y'] <= b['y'] < self.boss['y'] + self.boss['h']:
                        self.boss['hp'] -= 1
                        if self.boss['hp'] <= 0: self._victory()
                        hit = True
            if not hit: nuevas.append(b)
        self.bullets = nuevas

    def _update_enemy_bullets(self):
        nuevas = []
        for b in self.enemy_bullets:
            b['y'] += 1
            if b['y'] >= self.h: continue
            
            hit = False
            for w in self.walls[:]:
                if w['x'] == b['x'] and w['y'] == b['y']:
                    w['hp'] -= 1
                    if w['hp'] <= 0: self.walls.remove(w)
                    hit = True; break
            if hit: continue
            
            if self.player:
                if int(b['x']) == self.player['x'] and int(b['y']) == self.player['y']:
                    self.player_hp -= b.get('dmg', 10)
                    if self.player_hp <= 0: self.terminado = True
                    continue
            nuevas.append(b)
        self.enemy_bullets = nuevas

    def _spawn_boss_fallback(self):
        self.boss = {
            'x': self.w // 2 - 3, 'y': 1, 'w': 6, 'h': 3,
            'hp': 150, 'color': '#9B5DE5', 'damage': 30
        }
        self.boss_spawned = True
        self.enemies = []

    def _victory(self):
        tkMessageBox.showinfo("VICTORIA", "¡FINAL BOSS DESTRUIDO!\nHas completado el juego.")
        self.root.destroy(); sys.exit(0)
    def _game_over(self):
        tkMessageBox.showinfo("Game Over", "El tanque fue destruido.\nPuntuacion: " + str(self.score))
        self.root.destroy(); sys.exit(0)


def run_game(data):
    juego = Juego(data)
    juego.root.mainloop()


if __name__ == '__main__':
    if len(sys.argv) != 2: sys.exit(1)
    with open(sys.argv[1], 'r') as f: juego = Juego(json.load(f))
    juego.root.mainloop()