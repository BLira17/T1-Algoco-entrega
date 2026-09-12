// Tarea 1 - INF-221 Algoritmos y Complejidad - 2026-2
// Benjamin Lira <blira@usm.cl> - Rol: 202473586-1
// strassen.cpp - Algoritmo de Strassen, con corte a naive por debajo de UMBRAL.
//
// FUENTES
//   [1] V. Strassen. "Gaussian Elimination is not Optimal". Numerische
//       Mathematik, 13(4):354-356, 1969: las siete multiplicaciones M1..M7.
//   [2] T. H. Cormen, C. E. Leiserson, R. L. Rivest, C. Stein. "Introduction to
//       Algorithms", 3a ed., MIT Press, 2009, seccion 4.2 (pags. 79-83):
//       particion en bloques, los siete productos y la recurrencia.
//   [3] N. J. Higham. "Accuracy and Stability of Numerical Algorithms", 2a ed.,
//       SIAM, 2002, cap. 23 "Fast Matrix Multiplication": necesidad del umbral
//       de corte y punto de cruce con el metodo clasico.
//   [4] S. Huss-Lederman et al. "Implementation of Strassen's Algorithm for
//       Matrix Multiplication". Supercomputing '96: tratamiento practico del
//       umbral y del manejo de dimensiones.

#include "algorithms.hpp"

#include <cstddef>

using std::vector;

namespace {

// Tamano de submatriz por debajo del cual se usa la multiplicacion clasica.
constexpr std::size_t UMBRAL = 32;

Matriz sumar(const Matriz& X, const Matriz& Y) {
    const std::size_t m = X.size();
    Matriz R(m, vector<int>(m));
    for (std::size_t i = 0; i < m; ++i)
        for (std::size_t j = 0; j < m; ++j)
            R[i][j] = X[i][j] + Y[i][j];
    return R;
}

Matriz restar(const Matriz& X, const Matriz& Y) {
    const std::size_t m = X.size();
    Matriz R(m, vector<int>(m));
    for (std::size_t i = 0; i < m; ++i)
        for (std::size_t j = 0; j < m; ++j)
            R[i][j] = X[i][j] - Y[i][j];
    return R;
}

// Extrae el bloque de m x m que empieza en (fila0, col0).
Matriz bloque(const Matriz& M, std::size_t fila0, std::size_t col0, std::size_t m) {
    Matriz R(m, vector<int>(m));
    for (std::size_t i = 0; i < m; ++i)
        for (std::size_t j = 0; j < m; ++j)
            R[i][j] = M[fila0 + i][col0 + j];
    return R;
}

// Escribe el bloque S en M a partir de (fila0, col0).
void colocar(Matriz& M, const Matriz& S, std::size_t fila0, std::size_t col0) {
    const std::size_t m = S.size();
    for (std::size_t i = 0; i < m; ++i)
        for (std::size_t j = 0; j < m; ++j)
            M[fila0 + i][col0 + j] = S[i][j];
}

Matriz strassen_rec(const Matriz& A, const Matriz& B) {
    const std::size_t n = A.size();

    // Corte a multiplicacion clasica. La guarda n % 2 evita dividir un tamano
    // impar; con los n del enunciado (potencias de 2) nunca se activa.
    if (n <= UMBRAL || n % 2 != 0) {
        return naive(A, B);
    }

    const std::size_t m = n / 2;

    const Matriz A11 = bloque(A, 0, 0, m), A12 = bloque(A, 0, m, m);
    const Matriz A21 = bloque(A, m, 0, m), A22 = bloque(A, m, m, m);
    const Matriz B11 = bloque(B, 0, 0, m), B12 = bloque(B, 0, m, m);
    const Matriz B21 = bloque(B, m, 0, m), B22 = bloque(B, m, m, m);

    // Los siete productos de Strassen [1][2].
    const Matriz M1 = strassen_rec(sumar(A11, A22), sumar(B11, B22));
    const Matriz M2 = strassen_rec(sumar(A21, A22), B11);
    const Matriz M3 = strassen_rec(A11, restar(B12, B22));
    const Matriz M4 = strassen_rec(A22, restar(B21, B11));
    const Matriz M5 = strassen_rec(sumar(A11, A12), B22);
    const Matriz M6 = strassen_rec(restar(A21, A11), sumar(B11, B12));
    const Matriz M7 = strassen_rec(restar(A12, A22), sumar(B21, B22));

    // Reconstruccion de los cuatro bloques de C.
    const Matriz C11 = sumar(restar(sumar(M1, M4), M5), M7);   // M1 + M4 - M5 + M7
    const Matriz C12 = sumar(M3, M5);                          // M3 + M5
    const Matriz C21 = sumar(M2, M4);                          // M2 + M4
    const Matriz C22 = sumar(restar(sumar(M1, M3), M2), M6);   // M1 - M2 + M3 + M6

    Matriz C(n, vector<int>(n));
    colocar(C, C11, 0, 0);
    colocar(C, C12, 0, m);
    colocar(C, C21, m, 0);
    colocar(C, C22, m, m);
    return C;
}

}  // namespace

Matriz strassen(const Matriz& A, const Matriz& B) {
    return strassen_rec(A, B);
}
