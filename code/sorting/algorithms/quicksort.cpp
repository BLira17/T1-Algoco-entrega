// Tarea 1 - INF-221 Algoritmos y Complejidad - 2026-2
// Benjamin Lira <blira@usm.cl> - Rol: 202473586-1
// quicksort.cpp - Quick Sort con pivote aleatorio y particion de tres vias.
//
// FUENTE DEL CICLO DE PARTICION DE TRES VIAS
//   R. Sedgewick, K. Wayne. "Algorithms", 4a ed., seccion 2.3 "Quicksort".
//   El ciclo de abajo sigue el de Quick3way.java, incluidos los nombres lt/gt/i:
//     https://algs4.cs.princeton.edu/23quicksort/Quick3way.java.html
//   La explicacion y los diagramas del esquema (bandera holandesa de Dijkstra)
//   estan en https://algs4.cs.princeton.edu/23quicksort/ , pero esa pagina no
//   trae el codigo: esta en el .java enlazado arriba.
//
// DIFERENCIA CON LA FUENTE
//   Quick3way mezcla el arreglo COMPLETO una vez al inicio (StdRandom.shuffle) y
//   luego usa a[lo] como pivote. Aqui se sortea un pivote al azar en cada
//   llamada, que es la variante RANDOMIZED-QUICKSORT de T. H. Cormen, C. E.
//   Leiserson, R. L. Rivest, C. Stein, "Introduction to Algorithms", 3a ed.,
//   seccion 7.3. Ambas dan la misma garantia esperada de Theta(n log n); la
//   segunda evita reordenar la entrada antes de medirla.

#include "algorithms.hpp"

#include <algorithm>
#include <cstddef>
#include <random>

using std::vector;

namespace {

std::mt19937 generador(202473586u);

// Ordena el rango cerrado [lo, hi].
void ordenar(vector<int>& a, std::ptrdiff_t lo, std::ptrdiff_t hi) {
    if (lo >= hi) return;

    // Pivote al azar dentro del rango, movido a a[lo].
    std::uniform_int_distribution<std::ptrdiff_t> sorteo(lo, hi);
    std::swap(a[lo], a[sorteo(generador)]);
    const int pivote = a[lo];

    // Particion de tres vias. Al terminar:
    //   [lo, lt)  menores que el pivote
    //   [lt, gt]  iguales al pivote (ya en su posicion final)
    //   (gt, hi]  mayores que el pivote
    std::ptrdiff_t lt = lo, i = lo + 1, gt = hi;
    while (i <= gt) {
        if (a[i] < pivote)      std::swap(a[lt++], a[i++]);
        else if (a[i] > pivote) std::swap(a[i], a[gt--]);
        else                    ++i;
    }

    ordenar(a, lo, lt - 1);
    ordenar(a, gt + 1, hi);
}

}  // namespace

vector<int>& quickSort(vector<int>& arr) {
    if (arr.size() > 1) ordenar(arr, 0, static_cast<std::ptrdiff_t>(arr.size()) - 1);
    return arr;
}
