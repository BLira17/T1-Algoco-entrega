// Tarea 1 - INF-221 Algoritmos y Complejidad - 2026-2
// Benjamin Lira <blira@usm.cl> - Rol: 202473586-1
// patiencesort.cpp - Patience Sort: reparto en pilas (busqueda binaria sobre los
//                    topes) y fusion k-vias con un heap de minimos.
//
// FUENTES
//   [1] C. L. Mallows. "Patience Sorting". SIAM Review, 5(4):375-376, 1963.
//       Descripcion original del procedimiento.
//   [2] D. Aldous, P. Diaconis. "Longest Increasing Subsequences: From Patience
//       Sorting to the Baik-Deift-Johansson Theorem". Bulletin of the AMS,
//       36(4):413-432, 1999, seccion 1: el numero de pilas es la longitud de la
//       subsecuencia creciente mas larga, y vale ~2*sqrt(n) en permutaciones
//       aleatorias.
//   [3] B. Chandramouli, J. Goldstein. "Patience is a Virtue: Revisiting Merge
//       and Sort on Modern Processors". SIGMOD 2014, pags. 731-742: busqueda
//       binaria para ubicar la pila y fusion k-vias con heap.

#include "algorithms.hpp"

#include <algorithm>
#include <cstddef>
#include <functional>
#include <queue>
#include <utility>

using std::vector;

vector<int>& patienceSort(vector<int>& arr) {
    const std::size_t n = arr.size();
    if (n < 2) return arr;

    // --- Fase 1: repartir en pilas ------------------------------------------
    vector<vector<int>> pilas;
    // topes[i] == pilas[i].back(). Se mantiene aparte, y estrictamente
    // creciente, para poder hacer busqueda binaria: recorrer las pilas una por
    // una dejaria la fase 1 en O(n*k), que para entrada ascendente (k = n) es
    // O(n^2).
    vector<int> topes;

    for (const int x : arr) {
        // Primera pila cuyo tope es >= x.
        const auto it = std::lower_bound(topes.begin(), topes.end(), x);
        const auto i  = static_cast<std::size_t>(it - topes.begin());

        if (i == topes.size()) {      // ninguna sirve: se abre una pila nueva
            pilas.emplace_back();
            topes.push_back(x);
        } else {                      // x pasa a ser el nuevo tope de la pila i
            topes[i] = x;
        }
        pilas[i].push_back(x);
    }

    // --- Fase 2: fusion k-vias ----------------------------------------------
    // Cada pila esta ordenada de forma no creciente de abajo hacia arriba, asi
    // que su tope (back) es su minimo. El minimo global esta siempre entre los
    // topes: basta un heap de minimos sobre ellos.
    using Entrada = std::pair<int, std::size_t>;   // (valor del tope, indice de pila)
    std::priority_queue<Entrada, vector<Entrada>, std::greater<Entrada>> heap;

    for (std::size_t i = 0; i < pilas.size(); ++i) {
        heap.emplace(pilas[i].back(), i);
    }

    for (std::size_t k = 0; k < n; ++k) {
        const Entrada menor = heap.top();
        heap.pop();

        arr[k] = menor.first;

        vector<int>& pila = pilas[menor.second];
        pila.pop_back();
        if (!pila.empty()) {
            heap.emplace(pila.back(), menor.second);
        }
    }

    return arr;
}
