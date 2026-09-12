#!/usr/bin/env python3
# Tarea 1 - INF-221 Algoritmos y Complejidad - 2026-2
# Benjamin Lira <blira@usm.cl> - Rol: 202473586-1
"""Generador de las matrices de entrada (Apendice A.2 del enunciado).

PROCEDENCIA: archivo entregado por la asignatura. Se conserva intacta la logica
de generar_matriz() y guardar_matriz(). Los cambios son: rutas resueltas desde la
ubicacion del script, interfaz de linea de comandos para generar subconjuntos, y
--semilla para que la generacion sea reproducible. Sin argumentos el
comportamiento es identico al original: la grilla completa de 144 archivos.

El tipo 'dispersa' del original elige (n*n)//10 posiciones al azar CON
reemplazo, asi que la densidad real queda algo por debajo del 10% nominal
(~9.5% para n grande). Se deja como esta para no alterar los datos del enunciado.

Uso:
    py -3 matrix_generator.py                 # grilla completa
    py -3 matrix_generator.py --n 16 64       # solo tamanos chicos
"""

import argparse
import os
import random
from itertools import product
from pathlib import Path

import numpy as np

DIR_SALIDA = Path(__file__).resolve().parent.parent / "data" / "matrix_input"

N_COMPLETO        = [2**4, 2**6, 2**8, 2**10]
TIPOS_COMPLETO    = ["dispersa", "diagonal", "densa"]
DOMINIOS_COMPLETO = ["D0", "D10"]
MUESTRAS_COMPLETO = ["a", "b", "c"]


def generar_matriz(n, tipo, dominio):
    """
    Genera una matriz de tamaño n x n según el tipo y dominio especificados.
    - tipo: 'dispersa', 'diagonal', 'densa'
    - dominio: 'D0' (valores en {0,1}) o 'D10' (valores en {0..9})
    """
    if dominio == 'D0':
        valores = [0, 1]
    elif dominio == 'D10':
        valores = list(range(10))
    else:
        raise ValueError("Dominio no válido. Usa 'D0' o 'D10'.")

    if tipo == 'densa':
        matriz = np.random.choice(valores, size=(n, n))
    elif tipo == 'diagonal':
        matriz = np.zeros((n, n), dtype=int)
        diag_vals = np.random.choice(valores, size=n)
        np.fill_diagonal(matriz, diag_vals)
    elif tipo == 'dispersa':
        matriz = np.zeros((n, n), dtype=int)
        cantidad = max(1, (n * n) // 10)  # solo 10% elementos diferentes de 0
        for _ in range(cantidad):
            i = random.randint(0, n-1)
            j = random.randint(0, n-1)
            matriz[i, j] = random.choice([v for v in valores if v != 0])
    else:
        raise ValueError("Tipo no válido. Usa 'densa', 'diagonal' o 'dispersa'.")

    return matriz


def guardar_matriz(matriz, nombre_archivo):
    """
    Guarda una matriz en un archivo de texto.
    """
    with open(nombre_archivo, 'w') as f:
        for fila in matriz:
            f.write(' '.join(map(str, fila)) + '\n')


def generar_y_guardar(n, t, d, m, carpeta=DIR_SALIDA):
    """
    Genera dos matrices y las guarda en archivos con nombres formateados.
    """
    Path(carpeta).mkdir(parents=True, exist_ok=True)

    M1 = generar_matriz(n, t, d)
    M2 = generar_matriz(n, t, d)

    base = f"{n}_{t}_{d}_{m}"
    archivo1 = os.path.join(carpeta, f"{base}_1.txt")
    archivo2 = os.path.join(carpeta, f"{base}_2.txt")

    guardar_matriz(M1, archivo1)
    guardar_matriz(M2, archivo2)

    print(f"Archivos guardados: {base}_1.txt, {base}_2.txt")


def generar_todos(Ns, Ts, Ds, Ms):
    total = len(Ns) * len(Ts) * len(Ds) * len(Ms)
    print(f"Generando {total * 2} archivos de matrices en {DIR_SALIDA}")

    for n, t, d, m in product(Ns, Ts, Ds, Ms):
        generar_y_guardar(n, t, d, m)

    print("Todas las matrices han sido generadas.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--n", nargs="+", type=int, default=N_COMPLETO)
    p.add_argument("--tipos", nargs="+", default=TIPOS_COMPLETO, choices=TIPOS_COMPLETO)
    p.add_argument("--dominios", nargs="+", default=DOMINIOS_COMPLETO, choices=DOMINIOS_COMPLETO)
    p.add_argument("--muestras", nargs="+", default=MUESTRAS_COMPLETO, choices=MUESTRAS_COMPLETO)
    p.add_argument("--semilla", type=int, default=None,
                   help="semilla de numpy y random, para generacion reproducible")
    args = p.parse_args()

    if args.semilla is not None:
        np.random.seed(args.semilla)
        random.seed(args.semilla)

    generar_todos(args.n, args.tipos, args.dominios, args.muestras)
