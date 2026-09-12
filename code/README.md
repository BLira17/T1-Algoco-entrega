# Código de la Tarea 1 — INF-221

**Algoritmos y Complejidad · 2026-2 · Benjamin Lira · Rol: 202473586-1**

Implementación y medición de cuatro algoritmos de ordenamiento y dos de
multiplicación de matrices. Este README describe el uso del código; el análisis
de resultados y la discusión experimental se presentan en [el informe](../report/report.pdf).

## Contenido

| Directorio o archivo | Función |
|---|---|
| `sorting/algorithms/` | Merge sort, quick sort, patience sort y `std::sort`; declaraciones en `algorithms.hpp`. |
| `matrix_multiplication/algorithms/` | Multiplicación naive y Strassen; declaraciones en `algorithms.hpp`. |
| `sorting/sorting.cpp` y `matrix_multiplication/matrix_multiplication.cpp` | Ejecutan un algoritmo y registran tiempo y memoria. |
| `common/medicion.hpp` y `common/medicion.cpp` | Utilidades compartidas de medición. |
| `makefile` de cada problema | Compila y coordina generación de datos, mediciones y gráficos. |
| `scripts/` de cada problema | Generador de entradas, `run_experiments.py` y `plot_generator.py`. |
| `data/` de cada problema | Entradas, salidas, mediciones CSV y gráficos PNG. |

Las fuentes y referencias de implementación se indican al inicio de los archivos
correspondientes. `sort.cpp` y los generadores provienen del material de la
asignatura; sus adaptaciones se documentan en sus encabezados.

Los comentarios dentro de los archivos de algoritmos se escribieron sobre todo
como apoyo de estudio, para seguir el razonamiento de cada implementación y
entender por qué está escrita así, más que como documentación de uso.

## Variantes implementadas

Varios de los algoritmos admiten más de una implementación, y la elección cambia
la clase de complejidad. Lo que se midió es esto:

| Algoritmo | Variante implementada | Efecto |
|---|---|---|
| quick sort | Pivote aleatorio (`RANDOMIZED-QUICKSORT`) y partición de tres vías. | Θ(n log n) esperado en las seis familias de entrada. Con pivote fijo degenera a Θ(n²) sobre entrada ya ordenada. |
| patience sort | Búsqueda binaria sobre los topes de las pilas y fusión k-vías con un montículo de mínimos. | **O(n log k) en vez de O(n·k).** La transcripción directa del procedimiento recorre las pilas una por una, y sobre entrada ascendente (k = n) eso es Θ(n²). |
| merge sort | Buffer auxiliar único, corte a insertion sort y salto de la mezcla cuando las mitades ya están en orden. | El buffer único es la condición para medir el algoritmo y no al asignador de memoria: reservar en cada mezcla son ~2n reservas para n = 10⁷. |
| Strassen | Corte al algoritmo clásico por debajo de 32 × 32. | Por debajo del umbral se ejecuta `naive`, así que en n = 16 ambos algoritmos son el mismo código. |

La consecuencia para el experimento es que **los cuatro algoritmos de
ordenamiento quedan en la misma clase de complejidad**, Θ(n log n), y por lo
tanto compiten en igualdad de condiciones: lo que las mediciones comparan son
constantes y sensibilidad a la estructura de la entrada, no una diferencia de
orden de crecimiento. Un patience sort Θ(n²) o un quick sort de pivote fijo
habrían perdido los casos grandes por una razón trivial, y además no habrían
alcanzado a completar el barrido (a n = 10⁷, Θ(n²) son ~10¹⁴ operaciones).

El razonamiento detrás de cada elección está en el encabezado del archivo
correspondiente y, para las que afectan la lectura de los resultados, en el
informe.

## Compilación y ejecución

Requisitos: `g++` con C++17, GNU Make y Python 3 con `numpy`, `pandas` y
`matplotlib`. En Windows se puede usar MSYS2 con `g++` y GNU Make; los makefiles
usan `py -3` para Python. En Linux usan `python3`. Se puede ajustar con
`make PY=python3 <objetivo>`.

Desde `code/sorting` o `code/matrix_multiplication`, ejecutar:

```bash
make             # Compilar con C++17 y -O2.
make datos       # Generar las entradas del enunciado.
make verificar   # Verificar los algoritmos sobre los casos pequeños.
make run         # Medir los casos disponibles (3 repeticiones por defecto).
make plots       # Generar gráficos PNG a partir del CSV.
```

`make smoke` realiza una prueba pequeña de generación, medición y gráficos.
`make clean` elimina objetos y ejecutables.

Para medir verificando resultados y guardar también las salidas, sustituir
`make run` por el siguiente comando (en Linux, usar `python3` en lugar de `py -3`):

```bash
py -3 scripts/run_experiments.py --verificar --escribir-salida
```

Los generadores admiten `--n` para seleccionar tamaños y `--semilla` para fijar
la aleatoriedad. Por ejemplo, desde `code/sorting`:

```bash
py -3 scripts/array_generator.py --n 10 1000 100000 1000000 10000000 --semilla 1
```

Este ejemplo añade el tamaño intermedio de un millón de elementos utilizado en
las mediciones de ordenamiento. Una nueva generación con semilla fija permite
repetir esas entradas, pero no garantiza que coincidan con las del CSV existente.
Consultar `--help` en cada script para las demás opciones.

## Datos y mediciones

Las entradas están en `data/array_input/` o `data/matrix_input/`; las salidas,
en `data/array_output/` o `data/matrix_output/`. Las mediciones se guardan en
`data/measurements/sorting.csv` y `data/measurements/matrix_multiplication.csv`,
y los gráficos en `data/plots/` de cada problema.

Se cronometra la ejecución del algoritmo, excluyendo lectura, verificación y
escritura de archivos. Se realiza calentamiento y se usan iteraciones internas
para los tamaños pequeños. El CSV identifica algoritmo, caso, repetición y estado;
`tiempo_ms` expresa milisegundos, `memoria_pico_kb` registra el pico del proceso y
`memoria_algoritmo_kb` el pico de memoria dinámica contabilizada durante el algoritmo,
en KiB. Este último no incluye la pila de llamadas.

## Sobre los datos incluidos en la entrega

El ZIP de entrega contiene el código, el informe, los CSV de mediciones, los
gráficos y los archivos de entrada y salida, **salvo los de ordenamiento con
`n = 10^6` y `n = 10^7`**, que se omitieron por tamaño: solo el tramo de `10^7`
ocupa 1,7 GB entre entradas y salidas, y la plataforma de entrega admite 50 MB.
Todo lo demás va completo, incluidas las matrices de `n = 1024`.

Esta omisión **no afecta a los resultados**: los CSV de
`data/measurements/` contienen las 360 corridas de ordenamiento y las 144 de
multiplicación, incluidas todas las de `n = 10^7`, y los gráficos y las tablas
del informe se derivan de ellos. Lo que falta son los arreglos crudos de esos dos
tamaños, no sus mediciones.

Para reconstruirlos basta ejecutar, desde `code/sorting`:

```bash
make datos
py -3 scripts/run_experiments.py --verificar --escribir-salida
```

El primer comando regenera los 90 arreglos de entrada y el segundo produce las
salidas `_out.txt`. Como el generador usa una semilla aleatoria salvo que se le
pase `--semilla`, los arreglos no serán idénticos a los medidos, pero sí
equivalentes en tamaño, tipo y dominio.
