#!/usr/bin/env python3
# Tarea 1 - INF-221 Algoritmos y Complejidad - 2026-2
# Benjamin Lira <blira@usm.cl> - Rol: 202473586-1
"""Generacion de graficos del experimento de ordenamiento.

Lee data/measurements/sorting.csv y escribe en data/plots/:
    sorting_tiempo_vs_n.png    tiempo vs n, log-log, panel por (tipo, dominio)
    sorting_memoria_vs_n.png   memoria adicional vs n, mismos paneles
    sorting_barras_nmax.png    comparacion directa en el mayor n disponible

Esquema de entrada (contrato fijado en sorting.cpp):
    algoritmo,n,tipo,dominio,muestra,repeticion,tiempo_ms,
    memoria_pico_kb,memoria_algoritmo_kb,estado

FUENTES
 [1] matplotlib, "pyplot API". https://matplotlib.org/stable/api/pyplot_summary.html
 [2] pandas, "DataFrame.groupby".
     https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.groupby.html
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")           # sin GUI: escribimos archivos, no ventanas
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Tipografia y tamano pensados para el INFORME: la figura se inserta a ancho de
# pagina (unos 16 cm), asi que se genera compacta y con fuente grande. Si se
# generara con el tamano por defecto de matplotlib, al reducirla a la pagina la
# fuente quedaria en ~4 pt e ilegible.
plt.rcParams.update({
    "font.size":        13,
    "axes.titlesize":   14,
    "axes.labelsize":   13,
    "xtick.labelsize":  11,
    "ytick.labelsize":  11,
    "legend.fontsize":  12,
})

RAIZ        = Path(__file__).resolve().parent.parent
DIR_MEDIDAS = RAIZ / "data" / "measurements"
DIR_PLOTS   = RAIZ / "data" / "plots"

ORDEN_TIPOS    = ["ascendente", "descendente", "aleatorio"]
ORDEN_DOMINIOS = ["D1", "D7"]

# Paleta y marcador fijos por algoritmo: el mismo algoritmo se ve igual en todos
# los graficos del informe.
ESTILO = {
    "sort":         {"color": "#1f77b4", "marker": "o", "label": "std::sort"},
    "mergesort":    {"color": "#2ca02c", "marker": "s", "label": "merge sort"},
    "quicksort":    {"color": "#d62728", "marker": "^", "label": "quick sort"},
    "patiencesort": {"color": "#9467bd", "marker": "D", "label": "patience sort"},
}


def cargar(ruta: Path) -> pd.DataFrame:
    if not ruta.exists():
        sys.exit(f"ERROR: no existe {ruta}. Corre `make run` (o `make smoke`) primero.")
    df = pd.read_csv(ruta)
    faltantes = {"algoritmo", "n", "tipo", "dominio", "tiempo_ms", "estado"} - set(df.columns)
    if faltantes:
        sys.exit(f"ERROR: al CSV le faltan columnas: {sorted(faltantes)}")
    return df


def resumir(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Promedia sobre muestras y repeticiones, quedandose solo con estado ok."""
    ok = df[df["estado"] == "ok"].copy()
    ok[columna] = pd.to_numeric(ok[columna], errors="coerce")
    ok = ok.dropna(subset=[columna])
    return (ok.groupby(["tipo", "dominio", "algoritmo", "n"], as_index=False)
              .agg(valor=(columna, "mean"), desv=(columna, "std"), corridas=(columna, "size")))


def guias_complejidad(ax, ns, y_datos_max):
    """Rectas de referencia n log n y n^2.

    QUE SON: en escala log-log una complejidad n^k se dibuja como una recta de
    pendiente k. Superponer la pendiente teorica permite leer el resultado a
    ojo: si la curva medida corre PARALELA a la guia, el algoritmo tiene esa
    complejidad. Es la comparacion teoria-practica que pide el enunciado.

    DOS DECISIONES DE PRESENTACION:

     1. Se anclan al tamano MAS GRANDE medido. Ancladas a la izquierda, la guia
        n^2 se dispara varios ordenes de magnitud por encima de los datos y
        obliga al eje a abarcar una decena de decadas.

     2. Se levantan un factor SEPARACION por encima del dato mayor. Sin esto la
        guia de n log n queda tapada por las curvas de colores -- justamente
        porque los algoritmos SON n log n -- y el lector no puede verificar el
        paralelismo. Las guias indican PENDIENTE, no valor absoluto, asi que
        desplazarlas verticalmente no altera lo que comunican.
    """
    if len(ns) < 2 or y_datos_max <= 0:
        return
    SEPARACION = 4.0
    ns = np.array(sorted(ns), dtype=float)
    n0 = ns[-1]
    y_ancla = y_datos_max * SEPARACION

    for etiqueta, f, guion in ((r"referencia $n \log n$", lambda x: x * np.log2(x), (0, (5, 2))),
                               ("referencia $n^2$",        lambda x: x ** 2,        (0, (1, 2)))):
        ax.plot(ns, y_ancla * f(ns) / f(n0), ls=guion, lw=1.3, color="0.45",
                zorder=0, label=etiqueta)


def grafico_paneles(resumen: pd.DataFrame, titulo: str, etiqueta_y: str,
                    destino: Path, con_guias: bool) -> None:
    tipos     = [t for t in ORDEN_TIPOS if t in set(resumen["tipo"])]
    dominios  = [d for d in ORDEN_DOMINIOS if d in set(resumen["dominio"])]
    if not tipos or not dominios:
        print(f"  (sin datos para {destino.name})")
        return

    fig, axes = plt.subplots(len(dominios), len(tipos),
                             figsize=(3.8 * len(tipos), 3.2 * len(dominios)),
                             squeeze=False, sharex=True, sharey=True)

    for i, dominio in enumerate(dominios):
        for j, tipo in enumerate(tipos):
            ax = axes[i][j]
            panel = resumen[(resumen["tipo"] == tipo) & (resumen["dominio"] == dominio)]

            ancla, ns_panel = None, []
            for alg, grupo in panel.groupby("algoritmo"):
                grupo = grupo.sort_values("n")
                est = ESTILO.get(alg, {"color": None, "marker": "x", "label": alg})

                # Barras de error asimetricas. En escala logaritmica el extremo
                # inferior no puede llegar a cero: en los tamanos mas chicos el
                # tiempo esta en el limite de resolucion del reloj y la
                # desviacion supera al propio valor, lo que estiraria el eje
                # una decena de decadas hacia abajo y aplastaria los datos.
                valores = grupo["valor"].to_numpy(dtype=float)
                desv    = grupo["desv"].fillna(0.0).to_numpy(dtype=float)
                inferior = np.minimum(desv, valores * 0.95)

                ax.errorbar(grupo["n"], valores, yerr=[inferior, desv],
                            color=est["color"], marker=est["marker"], label=est["label"],
                            lw=1.5, ms=5, capsize=3)
                ns_panel = sorted(set(ns_panel) | set(grupo["n"]))
                # Ancla: el valor mas alto del panel, sobre el que se levantan las
                # guias. Ver la explicacion en guias_complejidad.
                ultimo = grupo["valor"].max()
                ancla = ultimo if ancla is None else max(ancla, ultimo)

            if con_guias and ancla:
                guias_complejidad(ax, ns_panel, ancla)

            # Las guias se extienden muy por debajo de los datos (la de n^2, al
            # estar anclada a la derecha, cae varias decadas hacia la izquierda).
            # Se fija el rango del eje a partir de los DATOS para que las guias
            # queden recortadas y las curvas medidas ocupen el panel.
            positivos = panel["valor"][panel["valor"] > 0]
            if len(positivos):
                ax.set_ylim(float(positivos.min()) / 20.0, float(positivos.max()) * 60.0)

            ax.set_xscale("log")
            # La escala log del eje y solo tiene sentido si hay valores > 0. Un
            # algoritmo in situ (std::sort) reporta memoria adicional 0, y en
            # ese caso matplotlib no puede escalar logaritmicamente.
            if (panel["valor"] > 0).any():
                ax.set_yscale("log")
            ax.grid(True, which="both", ls="-", lw=0.3, alpha=0.4)
            ax.set_title(f"{tipo} / {dominio}", fontsize=10)
            if i == len(dominios) - 1:
                ax.set_xlabel("n (elementos)")
            if j == 0:
                ax.set_ylabel(etiqueta_y)

    manejadores, etiquetas = axes[0][0].get_legend_handles_labels()
    if manejadores:
        fig.legend(manejadores, etiquetas, loc="lower center",
                   ncol=len(etiquetas), frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle(titulo, fontsize=13)
    fig.tight_layout(rect=(0, 0.03, 1, 0.97))
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  {destino.relative_to(RAIZ)}")


def grafico_barras(resumen: pd.DataFrame, destino: Path) -> None:
    if resumen.empty:
        return
    n_max = resumen["n"].max()
    datos = resumen[resumen["n"] == n_max]

    etiquetas = [f"{t}\n{d}" for t, d in
                 sorted({(t, d) for t, d in zip(datos["tipo"], datos["dominio"])})]
    algoritmos = sorted(set(datos["algoritmo"]), key=lambda a: list(ESTILO).index(a)
                        if a in ESTILO else 99)

    fig, ax = plt.subplots(figsize=(max(6.0, 1.6 * len(etiquetas)), 4.2))
    ancho = 0.8 / max(len(algoritmos), 1)
    base = np.arange(len(etiquetas))

    for k, alg in enumerate(algoritmos):
        alturas = []
        for etiqueta in etiquetas:
            tipo, dominio = etiqueta.split("\n")
            fila = datos[(datos["algoritmo"] == alg) & (datos["tipo"] == tipo) &
                         (datos["dominio"] == dominio)]
            alturas.append(float(fila["valor"].iloc[0]) if not fila.empty else 0.0)
        est = ESTILO.get(alg, {"color": None, "label": alg})
        ax.bar(base + k * ancho, alturas, ancho, color=est["color"], label=est["label"])

    ax.set_xticks(base + ancho * (len(algoritmos) - 1) / 2)
    ax.set_xticklabels(etiquetas, fontsize=9)
    if (datos["valor"] > 0).any():
        ax.set_yscale("log")
    ax.set_ylabel("tiempo medio (ms)")
    ax.set_title(f"Comparacion directa en n = {n_max}")
    ax.grid(True, axis="y", which="both", ls="-", lw=0.3, alpha=0.4)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=150)
    plt.close(fig)
    print(f"  {destino.relative_to(RAIZ)}")


def main() -> int:
    p = argparse.ArgumentParser(description="Graficos del experimento de ordenamiento.")
    p.add_argument("--csv", type=Path, default=DIR_MEDIDAS / "sorting.csv")
    p.add_argument("--prefijo", default="sorting", help="prefijo de los PNG de salida")
    args = p.parse_args()

    df = cargar(args.csv)

    no_ok = df[df["estado"] != "ok"]
    if not no_ok.empty:
        print("Casos sin medicion (se documentan en el informe, no se grafican):")
        for estado, grupo in no_ok.groupby("estado"):
            combos = sorted({f"{r.algoritmo}/{r.tipo}/{r.dominio}/n={r.n}"
                             for r in grupo.itertuples()})
            print(f"  {estado:<22} {len(grupo):>4} filas")
            for c in combos[:6]:
                print(f"      {c}")
            if len(combos) > 6:
                print(f"      ... y {len(combos) - 6} mas")
        print()

    print("Graficos generados:")
    grafico_paneles(resumir(df, "tiempo_ms"),
                    "Tiempo de ejecucion vs tamano de entrada",
                    "tiempo medio (ms)",
                    DIR_PLOTS / f"{args.prefijo}_tiempo_vs_n.png", con_guias=True)

    grafico_paneles(resumir(df, "memoria_algoritmo_kb"),
                    "Memoria adicional del algoritmo vs tamano de entrada",
                    "memoria adicional (KiB)",
                    DIR_PLOTS / f"{args.prefijo}_memoria_vs_n.png", con_guias=False)

    grafico_barras(resumir(df, "tiempo_ms"),
                   DIR_PLOTS / f"{args.prefijo}_barras_nmax.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
