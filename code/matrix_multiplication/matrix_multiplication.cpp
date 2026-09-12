// Tarea 1 - INF-221 Algoritmos y Complejidad - 2026-2
// Benjamin Lira <blira@usm.cl> - Rol: 202473586-1
// matrix_multiplication.cpp - Programa principal de medicion de tiempo y
//               memoria. Mide UN algoritmo sobre UN caso ({base}_1.txt y
//               {base}_2.txt) y emite una fila CSV por repeticion; el barrido lo
//               orquesta scripts/run_experiments.py.
//
// En el cronometro entra solo la llamada al algoritmo. La reserva de la matriz
// de salida SI queda dentro, porque forma parte del contrato y ambos la pagan.
//
// Uso:
//   matrix_multiplication --algoritmo <nombre> --caso <base> [opciones]
//   matrix_multiplication --listar

#include "algorithms/algorithms.hpp"
#include "../common/medicion.hpp"

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using std::string;
using std::vector;

namespace fs = std::filesystem;

// ---------------------------------------------------------------------------
using FnMultiplicacion = Matriz (*)(const Matriz&, const Matriz&);

struct Algoritmo {
    const char* nombre;
    FnMultiplicacion fn;
};

static const Algoritmo ALGORITMOS[] = {
    {"naive",    naive},
    {"strassen", strassen},
};

static const Algoritmo* buscar_algoritmo(const string& nombre) {
    for (const Algoritmo& a : ALGORITMOS) {
        if (nombre == a.nombre) return &a;
    }
    return nullptr;
}

// ---------------------------------------------------------------------------
// Metadatos del caso: {n}_{t}_{d}_{m} (Apendice A.2 del enunciado).
// Ej: 256_dispersa_D10_b  ->  archivos 256_dispersa_D10_b_1.txt y _2.txt
// ---------------------------------------------------------------------------
struct Caso {
    string base, n, tipo, dominio, muestra;
};

static Caso parsear_caso(const string& base) {
    Caso c;
    c.base = base;

    vector<string> partes;
    string actual;
    for (char ch : base) {
        if (ch == '_') {
            partes.push_back(actual);
            actual.clear();
        } else {
            actual.push_back(ch);
        }
    }
    partes.push_back(actual);

    if (partes.size() != 4) {
        throw std::runtime_error(
            "el caso '" + base + "' no sigue el formato {n}_{tipo}_{dominio}_{muestra}");
    }
    c.n       = partes[0];
    c.tipo    = partes[1];
    c.dominio = partes[2];
    c.muestra = partes[3];
    return c;
}

// ---------------------------------------------------------------------------
// E/S. Se lee el archivo completo y se parsea a mano: una matriz de 1024x1024
// son ~2 MB de texto y el barrido abre 144 archivos.
// ---------------------------------------------------------------------------
static Matriz leer_matriz(const fs::path& ruta) {
    std::ifstream in(ruta, std::ios::binary);
    if (!in) throw std::runtime_error("no se pudo abrir " + ruta.string());

    string buf((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());

    vector<int> valores;
    valores.reserve(buf.size() / 2 + 1);

    const char* p   = buf.data();
    const char* fin = p + buf.size();
    while (p < fin) {
        while (p < fin && (*p < '0' || *p > '9') && *p != '-') ++p;
        if (p >= fin) break;
        bool negativo = false;
        if (*p == '-') {
            negativo = true;
            ++p;
        }
        long long x = 0;
        while (p < fin && *p >= '0' && *p <= '9') {
            x = x * 10 + (*p - '0');
            ++p;
        }
        valores.push_back(static_cast<int>(negativo ? -x : x));
    }

    // La matriz es cuadrada: n = sqrt(cantidad de valores).
    std::size_t n = 0;
    while (n * n < valores.size()) ++n;
    if (n * n != valores.size()) {
        throw std::runtime_error(ruta.string() + ": " + std::to_string(valores.size()) +
                                 " valores no forman una matriz cuadrada");
    }

    Matriz M(n, vector<int>(n));
    for (std::size_t i = 0; i < n; ++i) {
        for (std::size_t j = 0; j < n; ++j) {
            M[i][j] = valores[i * n + j];
        }
    }
    return M;
}

static void escribir_matriz(const fs::path& ruta, const Matriz& M) {
    string out;
    out.reserve(M.size() * M.size() * 4 + M.size());
    char tmp[16];
    for (const vector<int>& fila : M) {
        for (std::size_t j = 0; j < fila.size(); ++j) {
            if (j) out.push_back(' ');
            const int len = std::snprintf(tmp, sizeof tmp, "%d", fila[j]);
            out.append(tmp, static_cast<std::size_t>(len));
        }
        out.push_back('\n');
    }

    if (!ruta.parent_path().empty()) fs::create_directories(ruta.parent_path());
    std::ofstream o(ruta, std::ios::binary);
    if (!o) throw std::runtime_error("no se pudo escribir " + ruta.string());
    o.write(out.data(), static_cast<std::streamsize>(out.size()));
}

// ---------------------------------------------------------------------------
// Verificacion de correctitud. El oraculo NO es el otro algoritmo sino la
// definicion del producto: se recalcula el producto punto de posiciones (i,j) y
// se compara con C[i][j], de modo que naive y strassen se verifican por igual.
// Para n <= 64 se revisan las n^2 posiciones; sobre eso, una muestra aleatoria
// con semilla fija.
// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// Iteraciones internas por medicion. En n = 16 una multiplicacion dura unos 4
// microsegundos y la medicion queda dominada por la resolucion del cronometro,
// asi que se ejecuta el algoritmo K veces dentro de UNA region cronometrada y se
// divide. K se elige para que cada medicion realice ~5*10^7 operaciones.
// ---------------------------------------------------------------------------
static int iteraciones_internas(std::size_t n) {
    if (n == 0) return 1;
    constexpr double OPERACIONES_OBJETIVO = 5e7;
    constexpr double TOPE                 = 500.0;
    const double costo = static_cast<double>(n) * static_cast<double>(n) * static_cast<double>(n);
    const double k = OPERACIONES_OBJETIVO / costo;
    if (k < 1.0)  return 1;
    if (k > TOPE) return static_cast<int>(TOPE);
    return static_cast<int>(k);
}

static bool verificar(const Matriz& A, const Matriz& B, const Matriz& C,
                      std::size_t muestras = 2000) {
    const std::size_t n = A.size();
    if (C.size() != n) return false;
    for (const vector<int>& fila : C) {
        if (fila.size() != n) return false;
    }

    auto producto_punto = [&](std::size_t i, std::size_t j) {
        long long s = 0;
        for (std::size_t k = 0; k < n; ++k) s += static_cast<long long>(A[i][k]) * B[k][j];
        return s;
    };

    if (n * n <= 64 * 64) {
        for (std::size_t i = 0; i < n; ++i) {
            for (std::size_t j = 0; j < n; ++j) {
                if (producto_punto(i, j) != C[i][j]) return false;
            }
        }
        return true;
    }

    std::mt19937 gen(12345);  // semilla fija: la verificacion es reproducible
    std::uniform_int_distribution<std::size_t> dist(0, n - 1);
    for (std::size_t t = 0; t < muestras; ++t) {
        const std::size_t i = dist(gen), j = dist(gen);
        if (producto_punto(i, j) != C[i][j]) return false;
    }
    return true;
}

// ---------------------------------------------------------------------------
// CSV. Mismo esquema que el experimento de ordenamiento, para que ambos
// generadores de graficos compartan estructura.
// ---------------------------------------------------------------------------
static const char* CSV_ENCABEZADO =
    "algoritmo,n,tipo,dominio,muestra,repeticion,tiempo_ms,"
    "memoria_pico_kb,memoria_algoritmo_kb,estado";

static string fila_csv(const string& algoritmo, const Caso& c, int repeticion,
                            double tiempo_ms, std::uint64_t pico_kb,
                            std::uint64_t algoritmo_kb, const string& estado) {
    char tmp[64];
    std::snprintf(tmp, sizeof tmp, "%.6f", tiempo_ms);
    return algoritmo + "," + c.n + "," + c.tipo + "," + c.dominio + "," + c.muestra + "," +
           std::to_string(repeticion) + "," + tmp + "," +
           std::to_string(pico_kb) + "," + std::to_string(algoritmo_kb) + "," + estado;
}

static void anexar_csv(const fs::path& ruta, const string& fila) {
    const bool nuevo = !fs::exists(ruta) || fs::file_size(ruta) == 0;
    if (!ruta.parent_path().empty()) fs::create_directories(ruta.parent_path());
    std::ofstream o(ruta, std::ios::app);
    if (!o) throw std::runtime_error("no se pudo escribir " + ruta.string());
    if (nuevo) o << CSV_ENCABEZADO << '\n';
    o << fila << '\n';
}

// ---------------------------------------------------------------------------
static void uso() {
    std::cout <<
        "Uso: matrix_multiplication --algoritmo <nombre> --caso <base> [opciones]\n"
        "     matrix_multiplication --listar\n\n"
        "Opciones:\n"
        "  --algoritmo <nombre>   naive | strassen\n"
        "  --caso <base>          base del caso, sin sufijo ni extension\n"
        "                         (ej. 256_densa_D10_a -> _1.txt y _2.txt)\n"
        "  --dir-entrada <ruta>   donde buscar las matrices (def. data/matrix_input)\n"
        "  --repeticiones <N>     corridas sobre el mismo caso (def. 3)\n"
        "  --csv <ruta>           archivo CSV al que anexar (def. no escribe)\n"
        "  --escribir-salida      escribe {base}_out.txt en el directorio de salida\n"
        "  --dir-salida <ruta>    destino de --escribir-salida (def. data/matrix_output)\n"
        "  --verificar            comprueba correctitud contra la definicion\n"
        "  --listar               imprime los algoritmos registrados y termina\n";
}

int main(int argc, char** argv) {
    string nombre_algoritmo, base_caso, ruta_csv;
    fs::path dir_entrada = "data/matrix_input";
    fs::path dir_salida  = "data/matrix_output";
    int  repeticiones    = 3;
    bool escribir_salida = false;
    bool verificar_flag  = false;

    try {
        for (int i = 1; i < argc; ++i) {
            const string a = argv[i];
            auto siguiente = [&](const char* opcion) -> string {
                if (i + 1 >= argc) throw std::runtime_error(string(opcion) + " requiere un valor");
                return argv[++i];
            };
            if      (a == "--algoritmo")       nombre_algoritmo = siguiente("--algoritmo");
            else if (a == "--caso")            base_caso        = siguiente("--caso");
            else if (a == "--dir-entrada")     dir_entrada      = siguiente("--dir-entrada");
            else if (a == "--dir-salida")      dir_salida       = siguiente("--dir-salida");
            else if (a == "--csv")             ruta_csv         = siguiente("--csv");
            else if (a == "--repeticiones")    repeticiones     = std::atoi(siguiente("--repeticiones").c_str());
            else if (a == "--escribir-salida") escribir_salida  = true;
            else if (a == "--verificar")       verificar_flag   = true;
            else if (a == "--listar") {
                for (const Algoritmo& x : ALGORITMOS) std::cout << x.nombre << '\n';
                return 0;
            } else if (a == "--ayuda" || a == "-h" || a == "--help") {
                uso();
                return 0;
            } else {
                std::cerr << "opcion desconocida: " << a << "\n\n";
                uso();
                return 2;
            }
        }
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << '\n';
        return 2;
    }

    if (nombre_algoritmo.empty() || base_caso.empty()) {
        uso();
        return 2;
    }
    if (repeticiones < 1) repeticiones = 1;

    const Algoritmo* algoritmo = buscar_algoritmo(nombre_algoritmo);
    if (!algoritmo) {
        std::cerr << "algoritmo desconocido: " << nombre_algoritmo << '\n';
        return 2;
    }

    try {
        const Caso caso = parsear_caso(base_caso);

        // --- fuera del cronometro: carga de las dos matrices -----------------
        const Matriz A = leer_matriz(dir_entrada / (caso.base + "_1.txt"));
        const Matriz B = leer_matriz(dir_entrada / (caso.base + "_2.txt"));
        if (A.size() != B.size()) {
            throw std::runtime_error("las matrices del caso " + caso.base +
                                     " tienen dimensiones distintas");
        }

        Matriz resultado;
        string estado_final = "ok";

        const int k_interno = iteraciones_internas(A.size());

        // Calentamiento: una ejecucion que NO se cronometra, para no medir los
        // fallos de cache y de TLB de la primera llamada. Ver la nota
        // equivalente en ../sorting/sorting.cpp.
        try {
            volatile std::size_t retener = algoritmo->fn(A, B).size();
            (void)retener;
        } catch (const std::exception&) {
            // Se reporta en el ciclo de medicion, que arma la fila del CSV.
        }

        for (int rep = 1; rep <= repeticiones; ++rep) {
            Matriz C;
            double tiempo_ms = 0.0;
            std::uint64_t alg_kb = 0;
            string estado = "ok";
            try {
                medicion::Cronometro crono;
                medicion::reiniciar_heap();       // contador de memoria a cero
                crono.iniciar();
                for (int it = 0; it < k_interno; ++it) {
                    C = algoritmo->fn(A, B);      // <-- UNICO codigo cronometrado
                }
                tiempo_ms = crono.detener_ms() / k_interno;
                alg_kb    = medicion::heap_pico_kb();
            } catch (const std::logic_error& e) {
                estado = "no_implementado";
                std::cerr << e.what() << '\n';
            } catch (const std::exception& e) {
                estado = "error";
                std::cerr << e.what() << '\n';
            }

            const std::uint64_t pico_kb = medicion::memoria_pico_kb();

            if (estado == "ok" && verificar_flag && !verificar(A, B, C)) {
                estado = "error_verificacion";
            }

            const string fila = fila_csv(nombre_algoritmo, caso, rep, tiempo_ms,
                                              pico_kb, alg_kb, estado);
            std::cout << fila << '\n';
            if (!ruta_csv.empty()) anexar_csv(ruta_csv, fila);

            estado_final = estado;
            if (estado == "no_implementado") break;
            if (rep == repeticiones) resultado = std::move(C);
        }

        if (escribir_salida && estado_final == "ok") {
            escribir_matriz(dir_salida / (caso.base + "_out.txt"), resultado);
        }

        if (estado_final == "error_verificacion") return 3;
        if (estado_final == "no_implementado")    return 4;
        if (estado_final == "error")              return 1;
        return 0;

    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << '\n';
        return 1;
    }
}
