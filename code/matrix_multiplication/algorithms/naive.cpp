// Tarea 1 - INF-221 Algoritmos y Complejidad - 2026-2
// Benjamin Lira <blira@usm.cl> - Rol: 202473586-1
// naive.cpp - Multiplicacion de matrices por definicion, con los ciclos en el
//             orden i-j-k.
//
// FUENTE
//   T. H. Cormen, C. E. Leiserson, R. L. Rivest, C. Stein. "Introduction to
//   Algorithms", 3a ed., MIT Press, 2009, seccion 4.2: procedimiento
//   SQUARE-MATRIX-MULTIPLY (pag. 75).

#include "algorithms.hpp"

using std::vector;

Matriz naive(const Matriz& A, const Matriz& B) {
    const std::size_t n = A.size();
    Matriz C(n, vector<int>(n, 0));

    for (std::size_t i = 0; i < n; ++i) {
        for (std::size_t j = 0; j < n; ++j) {
            int suma = 0;
            for (std::size_t k = 0; k < n; ++k) {
                suma += A[i][k] * B[k][j];
            }
            C[i][j] = suma;
        }
    }
    return C;
}
