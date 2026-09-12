// Tarea 1 - INF-221 Algoritmos y Complejidad - 2026-2
// Benjamin Lira <blira@usm.cl> - Rol: 202473586-1
// algorithms.hpp - Contrato comun de los algoritmos de multiplicacion: ambos
// reciben dos matrices n x n por referencia constante y devuelven A*B en una
// matriz nueva. Matriz = std::vector<std::vector<int>>, indexada [fila][columna].

#ifndef MATRIX_ALGORITHMS_HPP
#define MATRIX_ALGORITHMS_HPP

#include <vector>

using Matriz = std::vector<std::vector<int>>;

// Multiplicacion clasica de tres ciclos anidados. O(n^3).
Matriz naive(const Matriz& A, const Matriz& B);

// Algoritmo de Strassen. O(n^log2(7)) = O(n^2.807...).
Matriz strassen(const Matriz& A, const Matriz& B);

#endif  // MATRIX_ALGORITHMS_HPP
