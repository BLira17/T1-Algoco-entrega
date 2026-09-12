#!/usr/bin/env python3
# Tarea 1 - INF-221 Algoritmos y Complejidad - 2026-2
# Benjamin Lira <blira@usm.cl> - Rol: 202473586-1
"""Generacion de graficos del experimento de multiplicacion de matrices.

Lee data/measurements/matrix_multiplication.csv y escribe en data/plots/:
    matrix_tiempo_vs_n.png    tiempo vs n, log-log, panel por (tipo, dominio)
    matrix_memoria_vs_n.png   memoria adicional vs n, mismos paneles
    matrix_barras_nmax.png    comparacion directa en el mayor n disponible
    matrix_razon_vs_n.png     razon naive/Strassen vs n, en eje lineal

Esquema de entrada (mismo contrato que el experimento de ordenamiento):
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
matplotlib.use("Agg")
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

ORDEN_TIPOS    = ["dispersa", "diagonal", "densa"]
ORDEN_DOMINIOS = ["D0", "D10"]

ESTILO = {
    "naive":    {"color": "#1f77b4", "marker": "o", "label": "naive"},
    "strassen": {"color": "#d62728", "marker": "^", "label": "Strassen"},
}

# Exponente de Strassen: log2(7) = 2.807...
EXP_STRASSEN = np.log2(7)


def cargar(ruta: Path) -> pd.DataFrame:
    if not ruta.exists():
        sys.exit(f"ERROR: no existe {ruta}. Corre `make run` (o `make smoke`) primero.")
    df = pd.read_csv(ruta)
    faltantes = {"algoritmo", "n", "tipo", "dominio", "tiempo_ms", "estado"} - set(df.columns)
    if faltantes:
        sys.exit(f"ERROR: al CSV le faltan columnas: {sorted(faltantes)}")
    return df


def resumir(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    ok = df[df["estado"] == "ok"].copy()
    ok[columna] = pd.to_numeric(ok[columna], errors="coerce")
    ok = ok.dropna(subset=[columna])
    return (ok.groupby(["tipo", "dominio", "algoritmo", "n"], as_index=False)
              .agg(valor=(columna, "mean"), desv=(columna, "std"), corridas=(columna, "size")))


def guias_complejidad(ax, ns, y_datos_max):
    """Rectas de referencia n^2.807 (Strassen) y n^3 (naive).

    En escala log-log una complejidad n^k es una recta de pendiente k: si la
    curva medida corre PARALELA a la guia, el exponente empirico coincide con el
    teorico. Se anclan al tamano mayor y se levantan un factor SEPARACION por
    encima del dato mas alto, para que no queden tapadas por las curvas. Las
    guias indican PENDIENTE, no valor absoluto.
    """
    if len(ns) < 2 or y_datos_max <= 0:
        return
    SEPARACION = 4.0
    ns = np.array(sorted(ns), dtype=float)
    n0 = ns[-1]
    y_ancla = y_datos_max * SEPARACION

    for etiqueta, exp, guion in (("referencia $n^{2.807}$", EXP_STRASSEN, (0, (5, 2))),
                                 ("referencia $n^3$",       3.0,          (0, (1, 2)))):
        ax.plot(ns, y_ancla * (ns / n0) ** exp, ls=guion, lw=1.3, color="0.45",
                zorder=0, label=etiqueta)


def grafico_paneles(resumen: pd.DataFrame, titulo: str, etiqueta_y: str,
                    destino: Path, con_guias: bool) -> None:
    tipos    = [t for t in ORDEN_TIPOS if t in set(resumen["tipo"])]
    dominios = [d for d in ORDEN_DOMINIOS if d in set(resumen["dominio"])]
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

            ax.set_xscale("log", base=2)   # los n son potencias de 2
            if (panel["valor"] > 0).any():
                ax.set_yscale("log")
            ax.grid(True, which="both", ls="-", lw=0.3, alpha=0.4)
            ax.set_title(f"{tipo} / {dominio}", fontsize=10)
            if i == len(dominios) - 1:
                ax.set_xlabel("n (dimension)")
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
    algoritmos = sorted(set(datos["algoritmo"]),
                        key=lambda a: list(ESTILO).index(a) if a in ESTILO else 99)

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


def grafico_razon(resumen: pd.DataFrame, destino: Path) -> None:
    """Razon naive/Strassen frente a n, en eje LINEAL.

    El grafico de tiempo usa escala log-log, que es lo correcto para leer el
    exponente empirico como pendiente, pero comprime las razones: en el rango de
    casi ocho decadas del eje y, un factor 2,7 ocupa un 6% de la altura del
    panel. Este grafico muestra esa misma magnitud sin comprimir.
    """
    if resumen.empty:
        return

    pivote = resumen.pivot_table(index=["tipo", "dominio", "n"],
                                 columns="algoritmo", values="valor")
    if not {"naive", "strassen"}.issubset(pivote.columns):
        return
    pivote = pivote.dropna(subset=["naive", "strassen"])
    pivote = pivote[pivote["strassen"] > 0]
    if pivote.empty:
        return
    pivote["razon"] = pivote["naive"] / pivote["strassen"]

    fig, ax = plt.subplots(figsize=(7.5, 4.4))

    for (tipo, dominio), grupo in pivote.groupby(level=["tipo", "dominio"]):
        grupo = grupo.sort_index(level="n")
        ns = [idx[2] for idx in grupo.index]
        ax.plot(ns, grupo["razon"], marker="o", ms=4, lw=1.2, alpha=0.85,
                label=f"{tipo} / {dominio}")

    ax.axhline(1.0, color="0.35", ls="--", lw=1.0)

    ax.set_xscale("log", base=2)
    ax.set_xlabel("n (dimension)")
    ax.set_ylabel("razon  naive / Strassen")
    ax.set_title("Cuantas veces mas rapido es Strassen que el algoritmo clasico")
    ax.set_ylim(bottom=0.0)
    ax.grid(True, which="major", ls="-", lw=0.3, alpha=0.4)

    # Region donde Strassen gana, para que el cruce se lea de un vistazo.
    ax.axhspan(1.0, ax.get_ylim()[1], color="#2ca02c", alpha=0.06)
    ax.text(0.985, 0.96, "Strassen mas rapido", transform=ax.transAxes,
            ha="right", va="top", fontsize=8, color="#2ca02c")
    ax.text(0.985, 0.04, "algoritmo clasico mas rapido", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=8, color="0.35")

    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper left")
    fig.tight_layout()
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=150)
    plt.close(fig)
    print(f"  {destino.relative_to(RAIZ)}")


def main() -> int:
    p = argparse.ArgumentParser(description="Graficos del experimento de multiplicacion.")
    p.add_argument("--csv", type=Path, default=DIR_MEDIDAS / "matrix_multiplication.csv")
    p.add_argument("--prefijo", default="matrix", help="prefijo de los PNG de salida")
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
                    "Tiempo de ejecucion vs dimension de la matriz",
                    "tiempo medio (ms)",
                    DIR_PLOTS / f"{args.prefijo}_tiempo_vs_n.png", con_guias=True)

    grafico_paneles(resumir(df, "memoria_algoritmo_kb"),
                    "Memoria adicional del algoritmo vs dimension",
                    "memoria adicional (KiB)",
                    DIR_PLOTS / f"{args.prefijo}_memoria_vs_n.png", con_guias=False)

    grafico_barras(resumir(df, "tiempo_ms"),
                   DIR_PLOTS / f"{args.prefijo}_barras_nmax.png")

    grafico_razon(resumir(df, "tiempo_ms"),
                  DIR_PLOTS / f"{args.prefijo}_razon_vs_n.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
