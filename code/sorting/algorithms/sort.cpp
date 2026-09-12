// Tarea 1 - INF-221 Algoritmos y Complejidad - 2026-2
// Benjamin Lira <blira@usm.cl> - Rol: 202473586-1
// sort.cpp - Ordenamiento con std::sort de la biblioteca estandar.
//
// PROCEDENCIA: archivo entregado por la asignatura. Unica modificacion: el tipo
// de retorno pasa de std::vector<int> a std::vector<int>& para evitar una copia
// completa del arreglo dentro de la region cronometrada (ver algorithms.hpp).
//
// FUENTE
//   cppreference, "std::sort". https://en.cppreference.com/w/cpp/algorithm/sort

#include "algorithms.hpp"

#include <algorithm>

using std::vector;

vector<int>& sortArray(vector<int>& arr) {
    std::sort(arr.begin(), arr.end());  // std::sort de la STL
    return arr;
}
