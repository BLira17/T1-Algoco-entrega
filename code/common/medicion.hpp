// Tarea 1 - INF-221 Algoritmos y Complejidad - 2026-2
// Benjamin Lira <blira@usm.cl> - Rol: 202473586-1
// medicion.hpp - Utilidades compartidas de medicion de tiempo y memoria.
//
// FUENTES
//   [1] cppreference, "std::chrono::steady_clock".
//       https://en.cppreference.com/w/cpp/chrono/steady_clock
//   [2] Microsoft Learn, "GetProcessMemoryInfo function (psapi.h)".
//       https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo
//   [3] Linux man-pages, "getrusage(2)".
//       https://man7.org/linux/man-pages/man2/getrusage.2.html

#ifndef MEDICION_HPP
#define MEDICION_HPP

#include <chrono>
#include <cstdint>

#if defined(_WIN32)
  #ifndef WIN32_LEAN_AND_MEAN
    #define WIN32_LEAN_AND_MEAN
  #endif
  #include <windows.h>
  #include <psapi.h>
#else
  #include <sys/resource.h>
#endif

namespace medicion {

// Cronometro monotono. Uso:
//     Cronometro c; c.iniciar(); ...codigo a medir...; double ms = c.detener_ms();
class Cronometro {
public:
    void iniciar() { t0_ = Reloj::now(); }

    double detener_ms() const {
        const Reloj::time_point t1 = Reloj::now();
        return std::chrono::duration<double, std::milli>(t1 - t0_).count();
    }

private:
    using Reloj = std::chrono::steady_clock;
    Reloj::time_point t0_{};
};

// Pico de memoria del proceso, en KiB. Devuelve 0 si el SO no lo entrega.
inline std::uint64_t memoria_pico_kb() {
#if defined(_WIN32)
    PROCESS_MEMORY_COUNTERS_EX pmc;
    pmc.cb = sizeof(pmc);
    if (GetProcessMemoryInfo(GetCurrentProcess(),
                             reinterpret_cast<PROCESS_MEMORY_COUNTERS*>(&pmc),
                             sizeof(pmc))) {
        return static_cast<std::uint64_t>(pmc.PeakPagefileUsage) / 1024u;
    }
    return 0;
#else
    struct rusage ru;
    if (getrusage(RUSAGE_SELF, &ru) == 0) {
        // En Linux ru_maxrss viene en KiB; en macOS viene en bytes.
    #if defined(__APPLE__)
        return static_cast<std::uint64_t>(ru.ru_maxrss) / 1024u;
    #else
        return static_cast<std::uint64_t>(ru.ru_maxrss);
    #endif
    }
    return 0;
#endif
}

// ---------------------------------------------------------------------------
// Memoria DINAMICA del algoritmo: maximo de bytes vivos pedidos al heap desde
// el reinicio. No contabiliza la pila. Implementado en medicion.cpp.
//
// Uso:
//     medicion::reiniciar_heap();      // justo antes de llamar al algoritmo
//     algoritmo(datos);
//     auto kb = medicion::heap_pico_kb();
// ---------------------------------------------------------------------------
void reiniciar_heap();
std::uint64_t heap_pico_kb();
std::uint64_t heap_pico_bytes();

}  // namespace medicion

#endif  // MEDICION_HPP
