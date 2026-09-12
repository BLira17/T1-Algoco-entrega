#!/usr/bin/env python3
# Tarea 1 - Algoritmos y Complejidad - 2026-2
# Benjamin Lira <blira@usm.cl> - Rol: 202473586-1
"""Orquestador del barrido de mediciones de ordenamiento.

Lanza UN PROCESO por cada par (algoritmo, archivo de entrada) y consolida las
filas CSV en data/measurements/sorting.csv. Un proceso por caso porque el pico
de memoria de un proceso es monotono creciente y contaminaria al siguiente.

Los casos corren en orden creciente de n y, si un (algoritmo, tipo, dominio)
agota el timeout o revienta a tamano n, los tamanos mayores de esa combinacion
se omiten con estado 'omitido_por_escalada'. Con las implementaciones actuales
no se omite ninguno.

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

# --- rutas, resueltas desde la ubicacion del script (no desde el cwd) --------
RAIZ         = Path(__file__).resolve().parent.parent      # code/sorting/
DIR_ENTRADA  = RAIZ / "data" / "array_input"
DIR_SALIDA   = RAIZ / "data" / "array_output"
DIR_MEDIDAS  = RAIZ / "data" / "measurements"
BINARIO      = RAIZ / ("sorting.exe" if sys.platform == "win32" else "sorting")

ALGORITMOS = ["sort", "mergesort", "quicksort", "patiencesort"]

ENCABEZADO = [
    "algoritmo", "n", "tipo", "dominio", "muestra", "repeticion",
    "tiempo_ms", "memoria_pico_kb", "memoria_algoritmo_kb", "estado",
]


class Caso:
    """Un archivo de entrada {n}_{tipo}_{dominio}_{muestra}.txt."""

    def __init__(self, ruta: Path):
        partes = ruta.stem.split("_")
        if len(partes) != 4:
            raise ValueError(f"nombre fuera de formato: {ruta.name}")
        self.ruta = ruta
        self.n = int(partes[0])
        self.tipo, self.dominio, self.muestra = partes[1], partes[2], partes[3]

    @property
    def clave_escalada(self) -> tuple:
        return (self.tipo, self.dominio)

    def __str__(self) -> str:
        return self.ruta.stem


def descubrir_casos(args) -> list[Caso]:
    casos = []
    for ruta in sorted(DIR_ENTRADA.glob("*.txt")):
        try:
            caso = Caso(ruta)
        except ValueError:
            continue  # placeholders como a.txt
        if args.n        and caso.n       not in args.n:        continue
        if args.tipos    and caso.tipo    not in args.tipos:    continue
        if args.dominios and caso.dominio not in args.dominios: continue
        if args.muestras and caso.muestra not in args.muestras: continue
        casos.append(caso)
    # Orden creciente de n: la politica de escalada depende de este orden.
    casos.sort(key=lambda c: (c.n, c.tipo, c.dominio, c.muestra))
    return casos


def fila_sintetica(algoritmo: str, caso: Caso, estado: str) -> list:
    """Fila para un caso que no produjo medicion (timeout, crash, omitido)."""
    return [algoritmo, caso.n, caso.tipo, caso.dominio, caso.muestra,
            1, "", "", "", estado]


def main() -> int:
    p = argparse.ArgumentParser(description="Barrido de mediciones de ordenamiento.")
    p.add_argument("--algoritmos", nargs="+", default=ALGORITMOS, choices=ALGORITMOS)
    p.add_argument("--n", nargs="+", type=int, help="tamanos a incluir (def. todos)")
    p.add_argument("--tipos", nargs="+", help="ascendente descendente aleatorio")
    p.add_argument("--dominios", nargs="+", help="D1 D7")
    p.add_argument("--muestras", nargs="+", help="a b c")
    p.add_argument("--repeticiones", type=int, default=3)
    p.add_argument("--timeout", type=float, default=120.0,
                   help="segundos por caso antes de darlo por timeout (def. 120)")
    p.add_argument("--csv", type=Path, default=DIR_MEDIDAS / "sorting.csv")
    p.add_argument("--append", action="store_true",
                   help="anexar al CSV existente en vez de recrearlo")
    p.add_argument("--escribir-salida", action="store_true",
                   help="escribir los arreglos ordenados en data/array_output/")
    p.add_argument("--verificar", action="store_true",
                   help="comprobar correctitud de cada resultado")
    p.add_argument("--sin-escalada", action="store_true",
                   help="desactivar la politica de omision por escalada")
    p.add_argument("--dry-run", action="store_true", help="listar sin ejecutar")
    p.add_argument("--smoke", action="store_true",
                   help="prueba de humo: solo n=10, 1 repeticion, con verificacion")
    p.add_argument("--solo-verificar", action="store_true",
                   help="correr n<=1000 con verificacion y sin escribir CSV")
    args = p.parse_args()

    if args.smoke:
        args.n = [10]
        args.repeticiones = 1
        args.verificar = True
        args.escribir_salida = True
        args.csv = DIR_MEDIDAS / "smoke_sorting.csv"
        args.timeout = 30.0

    if args.solo_verificar:
        args.n = args.n or [10, 1000]
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
    print(f"Entradas    : {len(casos)} archivos en {DIR_ENTRADA}")
    print(f"Algoritmos  : {', '.join(args.algoritmos)}")
    print(f"Corridas    : {total}   (repeticiones por corrida: {args.repeticiones})")
    print(f"Timeout     : {args.timeout:g} s por corrida")
    print(f"CSV         : {args.csv}")
    print()

    if args.dry_run:
        for caso in casos:
            for alg in args.algoritmos:
                print(f"  {alg:<14} {caso}")
        return 0

    escribir_csv = not args.solo_verificar
    if escribir_csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        if not args.append or not args.csv.exists():
            with args.csv.open("w", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerow(ENCABEZADO)

    # (algoritmo, tipo, dominio) -> menor n en que fallo por tiempo o crash
    bloqueados: dict[tuple, int] = {}
    resumen: dict[str, int] = {}
    hecho = 0

    for caso in casos:
        for alg in args.algoritmos:
            hecho += 1
            prefijo = f"[{hecho:>4}/{total}] {alg:<14} {str(caso):<34}"
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
                   "--entrada", str(caso.ruta),
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

            # Codigos de salida definidos en sorting.cpp:
            #   0 ok | 1 error | 2 uso | 3 error_verificacion | 4 no_implementado
            if proc.returncode == 0:
                tiempos = [float(l.split(",")[6]) for l in proc.stdout.strip().splitlines()
                           if l.count(",") == 9]
                promedio = sum(tiempos) / len(tiempos) if tiempos else float("nan")
                estado = "ok"
                print(f"{prefijo} ok        {promedio:10.3f} ms")
            elif proc.returncode == 4:
                estado = "no_implementado"
                print(f"{prefijo} {estado}")
            elif proc.returncode == 3:
                estado = "error_verificacion"
                print(f"{prefijo} *** {estado.upper()} ***")
            else:
                # Un quicksort ingenuo sobre entrada ordenada desborda la pila y
                # el proceso muere: no es una excepcion capturable en C++.
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
