// Tarea 1 - INF-221 Algoritmos y Complejidad - 2026-2
// Benjamin Lira <blira@usm.cl> - Rol: 202473586-1
// mergesort.cpp - Merge Sort top-down.
//
// FUENTES
//   [1] T. H. Cormen, C. E. Leiserson, R. L. Rivest, C. Stein. "Introduction to
//       Algorithms", 3a ed., MIT Press, 2009, seccion 2.3.1: pseudocodigo de
//       MERGE-SORT y MERGE.
//   [2] R. Sedgewick, K. Wayne. "Algorithms", 4a ed., Addison-Wesley, 2011,
//       seccion 2.2, "Practical improvements" (pag. 275): las tres mejoras que
//       se usan aqui -- buffer auxiliar unico, corte a insertion sort y salto de
//       la mezcla cuando las mitades ya estan en orden.
//       Descripcion: https://algs4.cs.princeton.edu/22mergesort/
//       Codigo de referencia: MergeX.java, enlazado en esa pagina.

#include "algorithms.hpp"

#include <algorithm>
#include <cstddef>

using std::vector;

namespace {

// Por debajo de este tamano de subarreglo se usa insertion sort. Ver decision (b).
constexpr std::size_t UMBRAL_INSERCION = 32;

// Insertion sort sobre el rango semiabierto [lo, hi).
void insercion(vector<int>& a, std::size_t lo, std::size_t hi) {
    for (std::size_t i = lo + 1; i < hi; ++i) {
        const int v = a[i];
        std::size_t j = i;
        while (j > lo && a[j - 1] > v) {
            a[j] = a[j - 1];
            --j;
        }
        a[j] = v;
    }
}

// Mezcla [lo, mid) con [mid, hi), ambos ya ordenados, usando aux como respaldo.
void mezclar(vector<int>& a, vector<int>& aux,
             std::size_t lo, std::size_t mid, std::size_t hi) {
    std::copy(a.begin() + static_cast<std::ptrdiff_t>(lo),
              a.begin() + static_cast<std::ptrdiff_t>(hi),
              aux.begin() + static_cast<std::ptrdiff_t>(lo));

    std::size_t i = lo, j = mid, k = lo;
    while (i < mid && j < hi) {
        // '<' y no '<=': ante un empate se toma el elemento izquierdo, que es
        // lo que hace estable al algoritmo.
        a[k++] = (aux[j] < aux[i]) ? aux[j++] : aux[i++];
    }
    while (i < mid) a[k++] = aux[i++];
    while (j < hi)  a[k++] = aux[j++];
}

void ordenar(vector<int>& a, vector<int>& aux,
             std::size_t lo, std::size_t hi) {
    if (hi - lo <= UMBRAL_INSERCION) {
        insercion(a, lo, hi);
        return;
    }
    const std::size_t mid = lo + (hi - lo) / 2;
    ordenar(a, aux, lo, mid);
    ordenar(a, aux, mid, hi);

    // Optimizacion (c): si las mitades ya estan en orden entre si, no hay nada
    // que mezclar.
    if (a[mid - 1] <= a[mid]) return;

    mezclar(a, aux, lo, mid, hi);
}

}  // namespace

vector<int>& mergeSort(vector<int>& arr) {
    if (arr.size() < 2) return arr;

    // Buffer auxiliar reservado UNA sola vez. Ver decision (a).
    vector<int> aux(arr.size());
    ordenar(arr, aux, 0, arr.size());
    return arr;
}
