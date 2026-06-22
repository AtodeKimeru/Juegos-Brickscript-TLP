BrickScript - Proyecto Final
Manual de Usuario Final

Este proyecto contiene el ecosistema final de BrickScript. Desde una misma carpeta se
pueden compilar y ejecutar los juegos originales, las versiones extendidas y el juego
de tanques usando el mismo compiler.py, runtime.py y jugar.bat.

REQUISITOS

1. Windows.
2. Python 2.7 instalado en C:\Python27\python.exe.
3. Tkinter disponible para Python 2.7.
4. Ejecutar los comandos desde la carpeta final_project.

COMO EJECUTAR

Abra una terminal en la carpeta final_project y use:

  jugar nombre_del_juego

Ejemplos:

  jugar tetris
  jugar snake
  jugar tetris_remake
  jugar snake_evolved
  jugar tanks

El script jugar.bat compila primero el archivo .brick correspondiente y luego abre el
juego usando runtime.py.

JUEGOS INCLUIDOS

1. tetris

Version original de Tetris.

Objetivo:
  Completar lineas horizontales para ganar puntos.

Controles:
  Flecha izquierda: mover pieza a la izquierda.
  Flecha derecha: mover pieza a la derecha.
  Flecha abajo: bajar pieza.
  Flecha arriba: rotar pieza.
  Q: salir.

2. snake

Version original de Snake.

Objetivo:
  Comer comida, crecer y evitar chocar contra paredes o contra el cuerpo.

Controles:
  Flechas: cambiar direccion.
  Q: salir.

3. tetris_remake

Version extendida de Tetris con colores, probabilidades CHANCE, piezas adicionales,
rotaciones completas y power-ups.

Objetivo:
  Completar lineas y activar power-ups segun las condiciones del juego.

Controles:
  Flecha izquierda: mover pieza a la izquierda.
  Flecha derecha: mover pieza a la derecha.
  Flecha abajo: bajar pieza.
  Flecha arriba: rotar pieza.
  Cuando un power-up esta activo, las flechas mueven el power-up y SPACE/ENTER lo fija.
  Q: salir.

4. snake_evolved

Version evolucionada de Snake con niveles de dificultad, fruta venenosa, nubes,
power-ups e indicadores visuales de estilo Nyan Cat.

Objetivo:
  Comer comida, evitar veneno y nubes, y usar power-ups de invencibilidad.

Controles:
  Flechas: cambiar direccion.
  1: nivel BABY.
  2: nivel ENTHUSIAST.
  3: nivel NYAN_CAT.
  Q: salir.

5. tanks

Juego de tanques con jugador, enemigos, proyectiles, puntos de vida y Final Boss.

Objetivo:
  Mover el tanque, disparar a enemigos, acumular puntaje y derrotar al Final Boss.

Controles:
  Flechas: mover el tanque.
  Barra espaciadora: disparar.
  Q: salir.

VIDEO DE INTEGRACION

Link del video:

  https://youtu.be/Beh36MhLfQk

El video muestra que todos los juegos se ejecutan desde el mismo compiler.py,
runtime.py y jugar.bat sin modificar codigo Python entre ejecuciones.

CONTENIDO DEL PROYECTO

  compiler.py        Compilador unificado de BrickScript.
  runtime.py         Runtime polimorfico que detecta el tipo de juego.
  jugar.bat          Script para compilar y ejecutar juegos.
  games/             Archivos .brick y .json de todos los juegos.
  gramaticas bnf/    Especificaciones BNF de los lenguajes soportados.
  runtimes/          Motores de ejecucion por tipo de juego.
  MANUAL.txt         Manual tecnico para extender el ecosistema.
