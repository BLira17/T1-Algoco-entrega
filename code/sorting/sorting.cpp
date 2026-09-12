// Tarea 1 - INF-221 Algoritmos y Complejidad - 2026-2
// Benjamin Lira <blira@usm.cl> - Rol: 202473586-1
// sorting.cpp - Programa principal de medicion de tiempo y memoria. Mide UN
//               algoritmo sobre UN archivo de entrada y emite una fila CSV por
//               repeticion; el barrido lo orquesta scripts/run_experiments.py.
//
// En el cronometro entra solo la llamada al algoritmo: quedan fuera la lectura
// del archivo, la copia del arreglo de trabajo, la verificacion y la escritura.
//
// FUENTE
//   cppreference, "std::is_sorted".
//   https://en.cppreference.com/w/cpp/algorithm/is_sorted
//
// Uso:
//   sorting --algoritmo <nombre> --entrada <ruta> [opciones]
//   sorting --listar

#include "algorithms/algorithms.hpp"
#include "../common/medicion.hpp"

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

using std::string;
using std::vector;

namespace fs = std::filesystem;

// ---------------------------------------------------------------------------
// Tabla de algoritmos: el unico lugar donde se registran. Agregar uno nuevo es
// declararlo en algorithms.hpp y sumar una linea aca.
// ---------------------------------------------------------------------------
using FnOrdenamiento = vector<int>& (*)(vector<int>&);

struct Algoritmo {
    const char* nombre;
    FnOrdenamiento fn;
};

static const Algoritmo ALGORITMOS[] = {
    {"sort",         sortArray},
    {"mergesort",    mergeSort},
    {"quicksort",    quickSort},
    {"patiencesort", patienceSort},
};

static const Algoritmo* buscar_algoritmo(const string& nombre) {
    for (const Algoritmo& a : ALGORITMOS) {
        if (nombre == a.nombre) return &a;
    }
    return nullptr;
}

// ---------------------------------------------------------------------------
// Metadatos del caso, derivados del nombre del archivo: {n}_{t}_{d}_{m}.txt
// (Apendice A.1 del enunciado). Ej: 100000_aleatorio_D7_b.txt
// ---------------------------------------------------------------------------
struct Caso {
    string base;     // 100000_aleatorio_D7_b
    string n;        // 100000
    string tipo;     // aleatorio
    string dominio;  // D7
    string muestra;  // b
};

static Caso parsear_caso(const fs::path& ruta) {
    Caso c;
    c.base = ruta.stem().string();

    vector<string> partes;
    string actual;
    for (char ch : c.base) {
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
            "el nombre '" + c.base + "' no sigue el formato {n}_{tipo}_{dominio}_{muestra}");
    }
    c.n       = partes[0];
    c.tipo    = partes[1];
    c.dominio = partes[2];
    c.muestra = partes[3];
    return c;
}

// ---------------------------------------------------------------------------
// E/S rapida: se lee el archivo completo a memoria y se parsea a mano, porque
// el operador >> sobre los ~80 MB de n = 10^7 domina el tiempo del barrido.
// Ocurre fuera del cronometro, asi que no afecta la medicion.
// ---------------------------------------------------------------------------
static vector<int> leer_arreglo(const fs::path& ruta) {
    std::ifstream in(ruta, std::ios::binary);
    if (!in) throw std::runtime_error("no se pudo abrir " + ruta.string());

    string buf((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());

    vector<int> v;
    v.reserve(buf.size() / 2 + 1);

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
        v.push_back(static_cast<int>(negativo ? -x : x));
    }
    return v;
}

static void escribir_arreglo(const fs::path& ruta, const vector<int>& v) {
    string out;
    out.reserve(v.size() * 4 + 1);
    char tmp[16];
    for (std::size_t i = 0; i < v.size(); ++i) {
        if (i) out.push_back(' ');
        const int len = std::snprintf(tmp, sizeof tmp, "%d", v[i]);
        out.append(tmp, static_cast<std::size_t>(len));
    }
    out.push_back('\n');

    if (!ruta.parent_path().empty()) fs::create_directories(ruta.parent_path());
    std::ofstream o(ruta, std::ios::binary);
    if (!o) throw std::runtime_error("no se pudo escribir " + ruta.string());
    o.write(out.data(), static_cast<std::streamsize>(out.size()));
}

// ---------------------------------------------------------------------------
// Verificacion de correctitud. Dos condiciones, ambas necesarias:
//   (a) el resultado esta ordenado de forma no decreciente;
//   (b) el resultado es una PERMUTACION de la entrada -- si no, un algoritmo
//       que devolviera n ceros pasaria (a) sin haber ordenado nada.
// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// Iteraciones internas por medicion. En los tamanos chicos una sola ejecucion
// dura menos que unas pocas cuentas del reloj, asi que se ejecuta el algoritmo K
// veces dentro de UNA region cronometrada y se divide. Las K copias de trabajo
// se preparan antes de arrancar el cronometro. K se elige para que cada medicion
// procese ~2*10^6 elementos.
// ---------------------------------------------------------------------------
static int iteraciones_internas(std::size_t n) {
    if (n == 0) return 1;
    constexpr std::size_t ELEMENTOS_OBJETIVO = 2000000;
    constexpr std::size_t TOPE               = 5000;
    const std::size_t k = ELEMENTOS_OBJETIVO / n;
    if (k < 1)    return 1;
    if (k > TOPE) return static_cast<int>(TOPE);
    return static_cast<int>(k);
}

static bool verificar(const vector<int>& original, const vector<int>& resultado) {
    if (original.size() != resultado.size())                 return false;
    if (!std::is_sorted(resultado.begin(), resultado.end())) return false;
    vector<int> referencia = original;
    std::sort(referencia.begin(), referencia.end());
    return referencia == resultado;
}

// ---------------------------------------------------------------------------
// Salida CSV. Esquema (contrato con scripts/plot_generator.py):
//   algoritmo,n,tipo,dominio,muestra,repeticion,tiempo_ms,
//   memoria_pico_kb,memoria_algoritmo_kb,estado
//   memoria_pico_kb       pico absoluto del proceso tras la repeticion
//   memoria_algoritmo_kb  memoria adicional que pide el algoritmo
//   estado                ok | no_implementado | error_verificacion | error
//                         (el runner agrega timeout | crash | omitido)
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
        "Uso: sorting --algoritmo <nombre> --entrada <ruta> [opciones]\n"
        "     sorting --listar\n\n"
        "Opciones:\n"
        "  --algoritmo <nombre>   sort | mergesort | quicksort | patiencesort\n"
        "  --entrada <ruta>       archivo {n}_{tipo}_{dominio}_{muestra}.txt\n"
        "  --repeticiones <N>     corridas sobre la misma entrada (def. 3)\n"
        "  --csv <ruta>           archivo CSV al que anexar (def. no escribe)\n"
        "  --escribir-salida      escribe {base}_out.txt en el directorio de salida\n"
        "  --dir-salida <ruta>    destino de --escribir-salida (def. data/array_output)\n"
        "  --verificar            comprueba correctitud contra std::sort\n"
        "  --listar               imprime los algoritmos registrados y termina\n";
}

int main(int argc, char** argv) {
    string nombre_algoritmo, ruta_entrada, ruta_csv;
    fs::path dir_salida = "data/array_output";
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
            else if (a == "--entrada")         ruta_entrada     = siguiente("--entrada");
            else if (a == "--csv")             ruta_csv         = siguiente("--csv");
            else if (a == "--dir-salida")      dir_salida       = siguiente("--dir-salida");
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

    if (nombre_algoritmo.empty() || ruta_entrada.empty()) {
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
        const Caso caso = parsear_caso(ruta_entrada);

        // --- fuera del cronometro: carga de la entrada ----------------------
        const vector<int> original = leer_arreglo(ruta_entrada);

        vector<int> resultado;
        string estado_final = "ok";

        const int k_interno = iteraciones_internas(original.size());

        // Calentamiento: una ejecucion que NO se cronometra. La primera llamada
        // paga fallos de cache, de TLB y predictores de salto sin entrenar. Sin
        // esto, la repeticion 1 salia sistematicamente sesgada al alza: 2.3x mas
        // lenta que la repeticion 3 en n = 10, y 1.14x en n = 1000.
        try {
            vector<int> calentamiento = original;
            algoritmo->fn(calentamiento);
        } catch (const std::exception&) {
            // Un algoritmo no implementado o con error se reporta en el ciclo
            // de medicion, que es donde se construye la fila del CSV.
        }

        for (int rep = 1; rep <= repeticiones; ++rep) {
            // k_interno copias de trabajo, preparadas FUERA del cronometro.
            vector<vector<int>> copias(static_cast<std::size_t>(k_interno), original);

            double tiempo_ms = 0.0;
            std::uint64_t alg_kb = 0;
            string estado = "ok";
            try {
                medicion::Cronometro crono;
                medicion::reiniciar_heap();        // contador de memoria a cero
                crono.iniciar();
                for (int it = 0; it < k_interno; ++it) {
                    algoritmo->fn(copias[static_cast<std::size_t>(it)]);  // <-- cronometrado
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

            if (estado == "ok" && verificar_flag && !verificar(original, copias[0])) {
                estado = "error_verificacion";
            }

            const string fila = fila_csv(nombre_algoritmo, caso, rep, tiempo_ms,
                                              pico_kb, alg_kb, estado);
            std::cout << fila << '\n';
            if (!ruta_csv.empty()) anexar_csv(ruta_csv, fila);

            estado_final = estado;
            if (estado == "no_implementado") break;   // no tiene sentido repetir
            if (rep == repeticiones) resultado = std::move(copias[0]);
        }

        if (escribir_salida && estado_final == "ok") {
            escribir_arreglo(dir_salida / (caso.base + "_out.txt"), resultado);
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
