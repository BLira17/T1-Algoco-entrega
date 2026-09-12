#!/usr/bin/env python3
# Tarea 1 - INF-221 Algoritmos y Complejidad - 2026-2
# Benjamin Lira <blira@usm.cl> - Rol: 202473586-1
"""Orquestador del barrido de mediciones de multiplicacion de matrices.

Lanza UN PROCESO por cada par (algoritmo, caso de prueba) y consolida las filas
CSV en data/measurements/matrix_multiplication.csv. Un proceso por caso porque
el pico de memoria de un proceso es monotono creciente y contaminaria al
siguiente.

Misma politica de escalada que en el experimento de ordenamiento: los casos
corren en orden creciente de n y, si un (algoritmo, tipo, dominio) agota el
timeout o revienta a tamano n, los tamanos mayores de esa combinacion se omiten
con estado 'omitido_por_escalada'.

Uso:
    py -3 scripts/run_experiments.py [opciones]
    py -3 scripts/run_experiments.py --smoke
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

RAIZ        = Path(__file__).resolve().parent.parent   # code/matrix_multiplication/
DIR_ENTRADA = RAIZ / "data" / "matrix_input"
DIR_SALIDA  = RAIZ / "data" / "matrix_output"
DIR_MEDIDAS = RAIZ / "data" / "measurements"
BINARIO     = RAIZ / ("matrix_multiplication.exe" if sys.platform == "win32"
                      else "matrix_multiplication")

ALGORITMOS = ["naive", "strassen"]

ENCABEZADO = [
    "algoritmo", "n", "tipo", "dominio", "muestra", "repeticion",
    "tiempo_ms", "memoria_pico_kb", "memoria_algoritmo_kb", "estado",
]


class Caso:
    """Un caso {n}_{tipo}_{dominio}_{muestra}, con sus archivos _1.txt y _2.txt."""

    def __init__(self, base: str):
        partes = base.split("_")
        if len(partes) != 4:
            raise ValueError(f"caso fuera de formato: {base}")
        self.base = base
        self.n = int(partes[0])
        self.tipo, self.dominio, self.muestra = partes[1], partes[2], partes[3]

    @property
    def clave_escalada(self) -> tuple:
        return (self.tipo, self.dominio)

    def __str__(self) -> str:
        return self.base


def descubrir_casos(args) -> list[Caso]:
    """Un caso existe solo si estan sus DOS archivos de matrices."""
    casos = []
    for ruta in sorted(DIR_ENTRADA.glob("*_1.txt")):
        base = ruta.name[:-len("_1.txt")]
        if not (DIR_ENTRADA / f"{base}_2.txt").exists():
            print(f"  aviso: {base} tiene _1.txt pero no _2.txt, se omite", file=sys.stderr)
            continue
        try:
            caso = Caso(base)
        except ValueError:
            continue
        if args.n        and caso.n       not in args.n:        continue
        if args.tipos    and caso.tipo    not in args.tipos:    continue
        if args.dominios and caso.dominio not in args.dominios: continue
        if args.muestras and caso.muestra not in args.muestras: continue
        casos.append(caso)
    casos.sort(key=lambda c: (c.n, c.tipo, c.dominio, c.muestra))
    return casos


def fila_sintetica(algoritmo: str, caso: Caso, estado: str) -> list:
    return [algoritmo, caso.n, caso.tipo, caso.dominio, caso.muestra,
            1, "", "", "", estado]


def main() -> int:
    p = argparse.ArgumentParser(description="Barrido de mediciones de multiplicacion.")
    p.add_argument("--algoritmos", nargs="+", default=ALGORITMOS, choices=ALGORITMOS)
    p.add_argument("--n", nargs="+", type=int, help="tamanos a incluir (def. todos)")
    p.add_argument("--tipos", nargs="+", help="dispersa diagonal densa")
    p.add_argument("--dominios", nargs="+", help="D0 D10")
    p.add_argument("--muestras", nargs="+", help="a b c")
    p.add_argument("--repeticiones", type=int, default=3)
    p.add_argument("--timeout", type=float, default=300.0,
                   help="segundos por caso antes de darlo por timeout (def. 300)")
    p.add_argument("--csv", type=Path, default=DIR_MEDIDAS / "matrix_multiplication.csv")
    p.add_argument("--append", action="store_true")
    p.add_argument("--escribir-salida", action="store_true")
    p.add_argument("--verificar", action="store_true")
    p.add_argument("--sin-escalada", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--smoke", action="store_true",
                   help="prueba de humo: solo n=16, 1 repeticion, con verificacion")
    p.add_argument("--solo-verificar", action="store_true",
                   help="correr n<=64 con verificacion y sin escribir CSV")
    args = p.parse_args()

    if args.smoke:
        args.n = [16]
        args.repeticiones = 1
        args.verificar = True
        args.escribir_salida = True
        args.csv = DIR_MEDIDAS / "smoke_matrix.csv"
        args.timeout = 30.0

    if args.solo_verificar:
        args.n = args.n or [16, 64]
        args.repeticiones = 1
        args.verificar = True

    if not BINARIO.exists():
        print(f"ERROR: falta el binario {BINARIO.name}. Corre `make` primero.", file=sys.stderr)
        return 1

    casos = descubrir_casos(args)
    if not casos:
        print(f"ERROR: no hay entradas en {DIR_ENTRADA}. Corre `make datos` primero.",
              file=sys.stderr)
        return 1

    total = len(casos) * len(args.algoritmos)
    print(f"Binario     : {BINARIO}")
    print(f"Casos       : {len(casos)} pares de matrices en {DIR_ENTRADA}")
    print(f"Algoritmos  : {', '.join(args.algoritmos)}")
    print(f"Corridas    : {total}   (repeticiones por corrida: {args.repeticiones})")
    print(f"Timeout     : {args.timeout:g} s por corrida")
    print(f"CSV         : {args.csv}")
    print()

    if args.dry_run:
        for caso in casos:
            for alg in args.algoritmos:
                print(f"  {alg:<10} {caso}")
        return 0

    escribir_csv = not args.solo_verificar
    if escribir_csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        if not args.append or not args.csv.exists():
            with args.csv.open("w", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerow(ENCABEZADO)

    bloqueados: dict[tuple, int] = {}
    resumen: dict[str, int] = {}
    hecho = 0

    for caso in casos:
        for alg in args.algoritmos:
            hecho += 1
            prefijo = f"[{hecho:>4}/{total}] {alg:<10} {str(caso):<30}"
            clave = (alg, *caso.clave_escalada)

            if not args.sin_escalada and clave in bloqueados and caso.n > bloqueados[clave]:
                estado = "omitido_por_escalada"
                print(f"{prefijo} {estado} (fallo en n={bloqueados[clave]})")
                if escribir_csv:
                    with args.csv.open("a", newline="", encoding="utf-8") as fh:
                        csv.writer(fh).writerow(fila_sintetica(alg, caso, estado))
                resumen[estado] = resumen.get(estado, 0) + 1
                continue

            cmd = [str(BINARIO),
                   "--algoritmo", alg,
                   "--caso", caso.base,
                   "--dir-entrada", str(DIR_ENTRADA),
                   "--repeticiones", str(args.repeticiones)]
            if escribir_csv:
                cmd += ["--csv", str(args.csv)]
            if args.verificar:
                cmd += ["--verificar"]
            if args.escribir_salida:
                cmd += ["--escribir-salida", "--dir-salida", str(DIR_SALIDA)]

            try:
                proc = subprocess.run(cmd, capture_output=True, text=True,
                                      timeout=args.timeout, cwd=RAIZ)
            except subprocess.TimeoutExpired:
                estado = "timeout"
                print(f"{prefijo} {estado} (>{args.timeout:g}s)")
                if escribir_csv:
                    with args.csv.open("a", newline="", encoding="utf-8") as fh:
                        csv.writer(fh).writerow(fila_sintetica(alg, caso, estado))
                bloqueados.setdefault(clave, caso.n)
                resumen[estado] = resumen.get(estado, 0) + 1
                continue

            # Codigos de salida definidos en matrix_multiplication.cpp:
            #   0 ok | 1 error | 2 uso | 3 error_verificacion | 4 no_implementado
            if proc.returncode == 0:
                tiempos = [float(l.split(",")[6]) for l in proc.stdout.strip().splitlines()
                           if l.count(",") == 9]
                promedio = sum(tiempos) / len(tiempos) if tiempos else float("nan")
                estado = "ok"
                print(f"{prefijo} ok        {promedio:12.3f} ms")
            elif proc.returncode == 4:
                estado = "no_implementado"
                print(f"{prefijo} {estado}")
            elif proc.returncode == 3:
                estado = "error_verificacion"
                print(f"{prefijo} *** {estado.upper()} ***")
            else:
                estado = "crash"
                detalle = (proc.stderr or "").strip().splitlines()
                print(f"{prefijo} crash (codigo {proc.returncode})"
                      + (f": {detalle[-1]}" if detalle else ""))
                if escribir_csv:
                    with args.csv.open("a", newline="", encoding="utf-8") as fh:
                        csv.writer(fh).writerow(fila_sintetica(alg, caso, estado))
                bloqueados.setdefault(clave, caso.n)

            resumen[estado] = resumen.get(estado, 0) + 1

    print("\n--- resumen ---")
    for estado in sorted(resumen):
        print(f"  {estado:<22} {resumen[estado]:>4}")
    if escribir_csv:
        print(f"\nMediciones en {args.csv}")

    return 1 if resumen.get("error_verificacion") else 0


if __name__ == "__main__":
    sys.exit(main())
