#!/usr/bin/env python3
# Tarea 1 - INF-221 Algoritmos y Complejidad - 2026-2
# Benjamin Lira <blira@usm.cl> - Rol: 202473586-1
"""Generador de los arreglos de entrada (Apendice A.1 del enunciado).

PROCEDENCIA: archivo entregado por la asignatura. Se conservan intactas
generar_arreglo() y guardar_arreglo(). Los cambios son: rutas resueltas desde la
ubicacion del script, interfaz de linea de comandos para generar subconjuntos, y
--semilla para que la generacion sea reproducible. Sin argumentos el
comportamiento es identico al original: la grilla completa de 72 archivos.

Uso:
    py -3 array_generator.py                    # grilla completa (~500 MB)
    py -3 array_generator.py --n 10 1000        # solo tamanos chicos
    py -3 array_generator.py --n 10 --muestras a
"""

import argparse
import os
from pathlib import Path

import numpy as np

DIR_SALIDA = Path(__file__).resolve().parent.parent / "data" / "array_input"

N_COMPLETO        = [10**1, 10**3, 10**5, 10**7]
TIPOS_COMPLETO    = ["ascendente", "descendente", "aleatorio"]
DOMINIOS_COMPLETO = ["D1", "D7"]
MUESTRAS_COMPLETO = ["a", "b", "c"]


def generar_arreglo(n, tipo, dominio):
    if dominio == "D1":
        valores = np.arange(10)
    elif dominio == "D7":
        valores = np.arange(10**7 + 1)
    else:
        raise ValueError("Dominio no reconocido")

    if tipo == "ascendente":
        return np.sort(np.random.choice(valores, n, replace=True))
    elif tipo == "descendente":
        return np.sort(np.random.choice(valores, n, replace=True))[::-1]
    elif tipo == "aleatorio":
        return np.random.choice(valores, n, replace=True)
    else:
        raise ValueError("Tipo de ordenamiento no reconocido")


def guardar_arreglo(nombre_archivo, arreglo):
    DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    with open(os.path.join(DIR_SALIDA, nombre_archivo), "w") as f:
        f.write(" ".join(map(str, arreglo)))


def generar_archivos(N, T, D, M):
    total = len(N) * len(T) * len(D) * len(M)
    print(f"Generando {total} arreglos en {DIR_SALIDA}")
    for n in N:
        for t in T:
            for d in D:
                for m in M:
                    nombre_archivo = f"{n}_{t}_{d}_{m}.txt"
                    arreglo = generar_arreglo(n, t, d)
                    guardar_arreglo(nombre_archivo, arreglo)
                    peso = (DIR_SALIDA / nombre_archivo).stat().st_size
                    print(f"Generado: {nombre_archivo}  ({peso/1024/1024:.1f} MiB)"
                          if peso > 1024 * 1024 else f"Generado: {nombre_archivo}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--n", nargs="+", type=int, default=N_COMPLETO)
    p.add_argument("--tipos", nargs="+", default=TIPOS_COMPLETO, choices=TIPOS_COMPLETO)
    p.add_argument("--dominios", nargs="+", default=DOMINIOS_COMPLETO, choices=DOMINIOS_COMPLETO)
    p.add_argument("--muestras", nargs="+", default=MUESTRAS_COMPLETO, choices=MUESTRAS_COMPLETO)
    p.add_argument("--semilla", type=int, default=None,
                   help="semilla de numpy, para generacion reproducible")
    args = p.parse_args()

    if args.semilla is not None:
        np.random.seed(args.semilla)

    generar_archivos(args.n, args.tipos, args.dominios, args.muestras)
