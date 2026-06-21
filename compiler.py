# -*- coding: utf-8 -*-
# compiler.py - COMPILADOR UNIFICADO Y RETROCOMPATIBLE
# Soporta: Tetris, Snake Evolved, Tanks, RetroBrik
# Uso: python compiler.py <archivo_entrada.brick>

import sys
import re
import json

def lexer(codigo_fuente):
    """
    Lexer unificado que protege colores hex (#RRGGBB) antes de eliminar comentarios.
    Compatible con todos los juegos.
    """
    # Proteger colores hex ANTES de eliminar comentarios
    codigo_fuente = re.sub(r'#([0-9A-Fa-f]{6})\b', r'HEXCOLOR_\1', codigo_fuente)
    # Eliminar comentarios reales (# seguido de texto no-hex)
    codigo_fuente = re.sub(r'#.*', '', codigo_fuente)
    # Tokens: palabras clave, colores protegidos, números, símbolos
    token_regex = r'HEXCOLOR_[0-9A-Fa-f]{6}|\b[A-Z_0-9]+\b|\d+|[\[\](),:]'
    tokens = re.findall(token_regex, codigo_fuente)
    # Restaurar tokens de color al formato #RRGGBB original
    tokens = [('#' + t[9:]) if t.startswith('HEXCOLOR_') else t for t in tokens]
    return tokens


class Parser:
    """
    Parser unificado compatible con:
    - Tetris (A2/A3)
    - Snake Evolved
    - Brick Tanks
    - RetroBrik
    """
    
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        # AST completo con todos los campos opcionales
        self.ast = {
            "tipo_juego": None,
            "config": {},
            "niveles": {},
            "shapes": {},
            "powerups": {},
            "bosses": {},
            "events": {}
        }

    def parse(self):
        """Main parser loop - maneja todos los tipos de declaraciones"""
        while self.pos < len(self.tokens):
            tok = self.tokens[self.pos]
            
            if tok == 'GAME_TYPE':
                self.parse_tipo_juego()
            elif tok == 'GAME_GRID':
                self.parse_grid()
            elif tok == 'LEVELS':
                self.parse_niveles()
            elif tok == 'DEFINE':
                sig = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else ''
                if sig == 'SHAPE':
                    self.parse_shape()
                elif sig == 'POWERUP':
                    self.parse_powerup()
                else:
                    self.pos += 1
            elif tok == 'BOSS':
                self.parse_boss()
            elif tok == 'ON':
                self.parse_evento()
            else:
                self.pos += 1
        
        return self.ast

    def consumir(self, esperado=None):
        """Consume un token, opcionalmente validando que sea el esperado"""
        if self.pos >= len(self.tokens):
            if esperado:
                raise Exception("Error: se esperaba '" + esperado + "' pero se llego al final")
            return None
        
        tok = self.tokens[self.pos]
        if esperado and tok != esperado:
            raise Exception(
                "Error de sintaxis: se esperaba '" + esperado + "' pero se encontro '" + tok + "' en pos " + str(self.pos)
            )
        self.pos += 1
        return tok

    def peek(self, offset=0):
        """Mira un token sin consumirlo"""
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return None

    def parse_tipo_juego(self):
        """GAME_TYPE <juego>"""
        self.consumir('GAME_TYPE')
        self.ast['tipo_juego'] = self.consumir()

    def parse_grid(self):
        """GAME_GRID (<ancho>, <alto>)"""
        self.consumir('GAME_GRID')
        self.consumir('(')
        w = int(self.consumir())
        self.consumir(',')
        h = int(self.consumir())
        self.consumir(')')
        self.ast['config']['grid_size'] = [w, h]

    def parse_niveles(self):
        """
        LEVELS:
            BABY: SPEED 0.15, POISON_ENABLED YES, CLOUDS_ENABLED NO, POWERUP_DURATION 0, ...
            ENTHUSIAST: ...
            NYAN_CAT: ...
        
        Si no hay sección LEVELS, crear nivel DEFAULT automático.
        """
        niveles = {}
        
        # Verificar si realmente hay LEVELS
        if self.peek() != 'LEVELS':
            # Crear nivel DEFAULT para retrocompatibilidad con Tetris
            niveles['DEFAULT'] = {
                'speed': 0.15,
                'poison_enabled': False,
                'clouds_enabled': False,
                'powerup_duration': 0
            }
            self.ast['niveles'] = niveles
            return
        
        # Parsear LEVELS
        self.consumir('LEVELS')
        self.consumir(':')
        
        while self.pos < len(self.tokens) and self.tokens[self.pos] in ('BABY', 'ENTHUSIAST', 'NYAN_CAT', 'DEFAULT'):
            nivel = self.consumir()
            self.consumir(':')
            
            cfg = {
                'speed': 0.15,
                'poison_enabled': False,
                'clouds_enabled': False,
                'powerup_duration': 0
            }
            
            # Parsear atributos del nivel
            while (self.pos < len(self.tokens) and 
                   self.tokens[self.pos] not in ('BABY', 'ENTHUSIAST', 'NYAN_CAT', 'DEFAULT', 
                                                   'ON', 'DEFINE', 'GAME_TYPE', 'GAME_GRID', 'BOSS')):
                clave = self.consumir()
                
                if clave == 'SPEED':
                    cfg['speed'] = float(self.consumir())
                elif clave == 'POISON_ENABLED':
                    valor = self.consumir()
                    cfg['poison_enabled'] = (valor == 'YES')
                elif clave == 'CLOUDS_ENABLED':
                    valor = self.consumir()
                    cfg['clouds_enabled'] = (valor == 'YES')
                elif clave == 'POWERUP_DURATION':
                    cfg['powerup_duration'] = int(self.consumir())
                
                # Consumir coma si existe
                if self.peek() == ',':
                    self.consumir(',')
            
            niveles[nivel] = cfg
        
        self.ast['niveles'] = niveles

    def parse_atributos_shape(self):
        """
        Parsea atributos opcionales de un shape y retorna DICCIONARIO.
        Campos soportados:
        - COLOR: #RRGGBB
        - CHANCE: int (probabilidad de aparición)
        - TYPE: RECTANGLE | CIRCLE | TRIANGLE | PLAYER | ENEMY | BULLET | WALL
        - HP: int (solo Tanks)
        - DAMAGE: int (solo Tanks)
        - SPEED: int (solo Tanks)
        
        Retorna diccionario con TODOS los campos, usando defaults si faltan.
        """
        attrs = {
            'color': '#00FFFF',
            'chance': 10,
            'tipo': 'RECTANGLE',
            'hp': 1,
            'damage': 1,
            'speed': 1
        }
        
        while self.pos < len(self.tokens):
            tok = self.tokens[self.pos]
            
            if tok == 'COLOR':
                self.consumir('COLOR')
                self.consumir(':')
                attrs['color'] = self.consumir()
            
            elif tok == 'CHANCE':
                self.consumir('CHANCE')
                self.consumir(':')
                attrs['chance'] = int(self.consumir())
            
            elif tok == 'TYPE':
                self.consumir('TYPE')
                self.consumir(':')
                tipo_leido = self.consumir()
                # Validar contra lista unificada de todos los juegos
                if tipo_leido in ('RECTANGLE', 'CIRCLE', 'TRIANGLE', 
                                 'PLAYER', 'ENEMY', 'BULLET', 'WALL'):
                    attrs['tipo'] = tipo_leido
                else:
                    attrs['tipo'] = 'RECTANGLE'  # fallback
            
            elif tok == 'HP':
                self.consumir('HP')
                self.consumir(':')
                attrs['hp'] = int(self.consumir())
            
            elif tok == 'DAMAGE':
                self.consumir('DAMAGE')
                self.consumir(':')
                attrs['damage'] = int(self.consumir())
            
            elif tok == 'SPEED':
                self.consumir('SPEED')
                self.consumir(':')
                attrs['speed'] = int(self.consumir())
            
            else:
                break  # Fin de atributos
        
        return attrs

    def parse_shape(self):
        """
        DEFINE SHAPE <nombre>:
            [COLOR: #RRGGBB]
            [CHANCE: int]
            [TYPE: tipo]
            [HP: int]
            [DAMAGE: int]
            [SPEED: int]
            STATE 0: [[...], [...], ...]
            STATE 1: [[...], [...], ...]
            ...
        END
        """
        self.consumir('DEFINE')
        self.consumir('SHAPE')
        nombre = self.consumir()
        self.consumir(':')
        
        # Parsear atributos opcionales
        attrs = self.parse_atributos_shape()
        
        # Parsear estados (matrices de píxeles)
        estados = []
        while self.pos < len(self.tokens) and self.tokens[self.pos] == 'STATE':
            self.consumir('STATE')
            self.consumir()  # número de estado
            self.consumir(':')
            
            matriz = []
            while self.peek() == '[':
                fila = []
                self.consumir('[')
                while self.peek() != ']':
                    fila.append(int(self.consumir()))
                    if self.peek() == ',':
                        self.consumir(',')
                self.consumir(']')
                matriz.append(fila)
            
            estados.append(matriz)
        
        self.consumir('END')
        
        # Guardar shape con estructura completa
        self.ast['shapes'][nombre] = {
            'estados': estados,
            'color': attrs['color'],
            'chance': attrs['chance'],
            'tipo': attrs['tipo'],
            'hp': attrs['hp'],
            'damage': attrs['damage'],
            'speed': attrs['speed']
        }

    def parse_powerup(self):
        """
        DEFINE POWERUP <nombre>:
            [COLOR: #RRGGBB]
            [CONDITION: <tipo> <valor>]
            STATE 0: [[...], [...], ...]
            ...
        END
        """
        self.consumir('DEFINE')
        self.consumir('POWERUP')
        nombre = self.consumir()
        self.consumir(':')
        
        color = '#FF69B4'
        condiciones = []
        
        # Parsear atributos del powerup
        while self.pos < len(self.tokens) and self.tokens[self.pos] != 'STATE':
            tok = self.tokens[self.pos]
            
            if tok == 'COLOR':
                self.consumir('COLOR')
                self.consumir(':')
                color = self.consumir()
            
            elif tok == 'CONDITION':
                self.consumir('CONDITION')
                self.consumir(':')
                cond_nombre = self.consumir()
                cond_valor = int(self.consumir())
                condiciones.append({'tipo': cond_nombre, 'valor': cond_valor})
            
            else:
                self.pos += 1
        
        # Parsear estados
        estados = []
        while self.pos < len(self.tokens) and self.tokens[self.pos] == 'STATE':
            self.consumir('STATE')
            self.consumir()
            self.consumir(':')
            
            matriz = []
            while self.peek() == '[':
                fila = []
                self.consumir('[')
                while self.peek() != ']':
                    fila.append(int(self.consumir()))
                    if self.peek() == ',':
                        self.consumir(',')
                self.consumir(']')
                matriz.append(fila)
            
            estados.append(matriz)
        
        self.consumir('END')
        
        self.ast['powerups'][nombre] = {
            'estados': estados,
            'color': color,
            'condiciones': condiciones
        }

    def parse_boss(self):
        """
        BOSS <nombre>:
            [COLOR: #RRGGBB]
            [HP: int]
            STATE 0: [[...], [...], ...]
            ...
        END
        """
        self.consumir('BOSS')
        nombre = self.consumir()
        self.consumir(':')
        
        color = '#FF00FF'
        hp = 100
        
        # Parsear atributos del boss
        while self.peek() not in ('STATE', 'END', None):
            tok = self.peek()
            
            if tok == 'COLOR':
                self.consumir('COLOR')
                self.consumir(':')
                color = self.consumir()
            elif tok == 'HP':
                self.consumir('HP')
                self.consumir(':')
                hp = int(self.consumir())
            else:
                break
        
        # Parsear estados
        estados = []
        while self.peek() == 'STATE':
            self.consumir('STATE')
            self.consumir()
            self.consumir(':')
            
            matriz = []
            while self.peek() == '[':
                fila = []
                self.consumir('[')
                while self.peek() != ']':
                    fila.append(int(self.consumir()))
                    if self.peek() == ',':
                        self.consumir(',')
                self.consumir(']')
                matriz.append(fila)
            
            estados.append(matriz)
        
        self.consumir('END')
        
        self.ast['bosses'][nombre] = {
            'type': 'BOSS',
            'hp': hp,
            'color': color,
            'estados': estados
        }

    def parse_evento(self):
        """
        ON <evento> [<parámetro>]:
            <acción> <objeto> [AT <ubicación>]
            ...
        END
        
        Soporta eventos especiales como TARGET_SCORE con parámetro.
        """
        self.consumir('ON')
        evento_base = self.consumir()
        nombre = 'ON_' + evento_base
        valor_objetivo = None
        
        # Manejo especial de eventos parametrizados (Tanks)
        if evento_base == 'TARGET_SCORE':
            if self.peek() not in [':', None] and self.peek() != 'END':
                valor_objetivo = self.consumir()
                nombre += "_" + str(valor_objetivo)
        
        self.consumir(':')
        acciones = []
        
        # Palabras clave para identificar fin de acciones
        palabras_clave = {
            'END', 'ON', 'DEFINE', 'GAME_TYPE', 'GAME_GRID', 'LEVELS', 'BOSS',
            'SPAWN', 'MOVE', 'ROTATE', 'INCREASE_SCORE', 'DECREASE_SCORE', 
            'RESET_SCORE', 'SET_DIRECTION', 'GROW', 'GAME_OVER', 'FORWARD'
        }
        
        # Parsear acciones
        while self.pos < len(self.tokens) and self.tokens[self.pos] != 'END':
            verbo = self.consumir()
            
            # Comando de una sola palabra
            if verbo == 'GAME_OVER':
                acciones.append({'accion': verbo, 'objeto': None, 'params': []})
                continue
            
            # Comando con objeto
            objeto = self.consumir()
            params = []
            
            # Parsear parámetros
            if self.peek() == 'AT':
                self.consumir('AT')
                if self.peek() == 'RANDOM':
                    params.append(self.consumir())
                else:
                    self.consumir('(')
                    x = int(self.consumir())
                    self.consumir(',')
                    y = int(self.consumir())
                    self.consumir(')')
                    params.append([x, y])
            elif self.peek() not in palabras_clave and self.peek() is not None:
                params.append(self.consumir())
            
            acciones.append({'accion': verbo, 'objeto': objeto, 'params': params})
        
        self.consumir('END')
        
        # Guardar evento con parámetro si existe
        self.ast['events'][nombre] = {
            'target': valor_objetivo,
            'actions': acciones
        }


def normalizar(ast):
    """
    Post-procesamiento del AST:
    - Asegurar que todos los campos obligatorios existan
    - Llenar valores por defecto para campos opcionales
    - Mantener retrocompatibilidad con formatos antiguos
    """
    
    # 1. Asegurar que tipo_juego existe
    if not ast.get('tipo_juego'):
        ast['tipo_juego'] = 'UNKNOWN'
    
    # 2. Asegurar niveles existe (al menos con DEFAULT)
    if not ast.get('niveles') or len(ast.get('niveles', {})) == 0:
        ast['niveles'] = {
            'DEFAULT': {
                'speed': 0.15,
                'poison_enabled': False,
                'clouds_enabled': False,
                'powerup_duration': 0
            }
        }
    
    # 3. Asegurar bosses existe (puede estar vacío)
    if 'bosses' not in ast:
        ast['bosses'] = {}
    
    # 4. Procesar shapes - agregar campos faltantes con defaults
    for nombre, shape in ast.get('shapes', {}).items():
        if isinstance(shape, list):
            # Formato antiguo (solo lista de matrices) - convertir
            ast['shapes'][nombre] = {
                'estados': shape,
                'color': '#00FFFF',
                'chance': 10,
                'tipo': 'RECTANGLE',
                'hp': 1,
                'damage': 1,
                'speed': 1
            }
        else:
            # Asegurar todos los campos existen
            if 'tipo' not in shape:
                shape['tipo'] = 'RECTANGLE'
            if 'hp' not in shape:
                shape['hp'] = 1
            if 'damage' not in shape:
                shape['damage'] = 1
            if 'speed' not in shape:
                shape['speed'] = 1
            if 'chance' not in shape:
                shape['chance'] = 10
            if 'color' not in shape:
                shape['color'] = '#00FFFF'
    
    # 5. Procesar powerups - asegurar estructura
    for nombre, powerup in ast.get('powerups', {}).items():
        if 'condiciones' not in powerup:
            powerup['condiciones'] = []
    
    # 6. Procesar eventos - convertir formato antiguo si es necesario
    for nombre, evento in ast.get('events', {}).items():
        if isinstance(evento, list):
            # Formato antiguo (solo lista de acciones)
            ast['events'][nombre] = {
                'target': None,
                'actions': evento
            }
        elif 'actions' not in evento:
            # Asegurar que tiene 'actions'
            evento['actions'] = []
    
    return ast


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Uso: python compiler.py <archivo.brick>"
        sys.exit(1)
    
    archivo = sys.argv[1]
    salida = archivo.replace('.brick', '.json')
    
    print "Compilando " + archivo + "..."
    
    try:
        with open(archivo, 'r') as f:
            codigo = f.read()
        
        # Lexer
        tokens = lexer(codigo)
        
        # Parser
        parser = Parser(tokens)
        ast = parser.parse()
        
        # Normalizar
        ast = normalizar(ast)
        
        # Escribir JSON
        with open(salida, 'w') as f:
            json.dump(ast, f, indent=2)
        
        print "Compilacion exitosa! Archivo: " + salida
    
    except Exception as e:
        print "ERROR: " + str(e)
        import traceback
        traceback.print_exc()
        sys.exit(1)
