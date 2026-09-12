// Tarea 1 - INF-221 Algoritmos y Complejidad - 2026-2
// Benjamin Lira <blira@usm.cl> - Rol: 202473586-1
// algorithms.hpp - Contrato comun de los algoritmos de ordenamiento: cada uno
// ordena arr in situ y devuelve una referencia al mismo arreglo.
//
// PROCEDENCIA: sortArray() viene del material entregado por la asignatura. Se
// cambio su tipo de retorno de std::vector<int> a std::vector<int>& para que no
// copie el arreglo dentro de la region cronometrada. Ver code/README.md.

#ifndef SORTING_ALGORITHMS_HPP
#define SORTING_ALGORITHMS_HPP

#include <vector>

// std::sort de la biblioteca estandar. Implementado en el material entregado.
std::vector<int>& sortArray(std::vector<int>& arr);

// Implementaciones propias.
std::vector<int>& mergeSort(std::vector<int>& arr);
std::vector<int>& quickSort(std::vector<int>& arr);
std::vector<int>& patienceSort(std::vector<int>& arr);

#endif  // SORTING_ALGORITHMS_HPP
