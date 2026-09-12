// Tarea 1 - INF-221 Algoritmos y Complejidad - 2026-2
// Benjamin Lira <blira@usm.cl> - Rol: 202473586-1
// medicion.cpp - Contador de memoria dinamica: reemplazo global de operator new
//                y operator delete. Mide el pico de bytes VIVOS en el heap desde
//                un punto de reinicio, no el pico del proceso.
//
// LIMITACION, a declarar en el informe: no contabiliza la PILA, de modo que los
// algoritmos in situ aparecen con 0 y no con su costo real de recursion.
//
// FUENTES
//   [1] cppreference, "operator new, operator new[] (replaceable allocation
//       functions)". https://en.cppreference.com/w/cpp/memory/new/operator_new
//   [2] cppreference, "operator delete, operator delete[]".
//       https://en.cppreference.com/w/cpp/memory/new/operator_delete

#include "medicion.hpp"

#include <cstddef>
#include <cstdlib>
#include <new>

namespace medicion {
namespace detalle {

// El programa es de un solo hilo, asi que contadores simples bastan: usar
// atomicos agregaria un costo por reserva sin ganar nada.
std::size_t g_vivos = 0;   // bytes actualmente vivos
std::size_t g_pico  = 0;   // maximo de g_vivos desde el ultimo reinicio
std::size_t g_base  = 0;   // valor de g_vivos en el ultimo reinicio

// Cabecera por bloque: guarda el tamano solicitado. Se redondea a la alineacion
// maxima para no romper la garantia de alineacion de operator new.
constexpr std::size_t CABECERA =
    (sizeof(std::size_t) + alignof(std::max_align_t) - 1) /
    alignof(std::max_align_t) * alignof(std::max_align_t);

void* reservar(std::size_t n) noexcept {
    void* crudo = std::malloc(n + CABECERA);
    if (!crudo) return nullptr;

    *static_cast<std::size_t*>(crudo) = n;

    g_vivos += n;
    if (g_vivos > g_pico) g_pico = g_vivos;

    return static_cast<char*>(crudo) + CABECERA;
}

void liberar(void* p) noexcept {
    if (!p) return;
    char* crudo = static_cast<char*>(p) - CABECERA;
    const std::size_t n = *reinterpret_cast<std::size_t*>(crudo);

    // Guarda defensiva: si por alguna razon se liberara mas de lo contabilizado,
    // se satura en 0 en vez de dar la vuelta al contador sin signo.
    g_vivos = (g_vivos >= n) ? g_vivos - n : 0;

    std::free(crudo);
}

}  // namespace detalle

void reiniciar_heap() {
    detalle::g_base = detalle::g_vivos;
    detalle::g_pico = detalle::g_vivos;
}

std::uint64_t heap_pico_kb() {
    const std::size_t extra = (detalle::g_pico > detalle::g_base)
                            ? detalle::g_pico - detalle::g_base
                            : 0;
    return static_cast<std::uint64_t>(extra) / 1024u;
}

std::uint64_t heap_pico_bytes() {
    return static_cast<std::uint64_t>((detalle::g_pico > detalle::g_base)
                                      ? detalle::g_pico - detalle::g_base
                                      : 0);
}

}  // namespace medicion

// ---------------------------------------------------------------------------
// Reemplazo global de los operadores de reserva y liberacion.
// ---------------------------------------------------------------------------

void* operator new(std::size_t n) {
    void* p = medicion::detalle::reservar(n);
    if (!p) throw std::bad_alloc();
    return p;
}

void* operator new[](std::size_t n) {
    void* p = medicion::detalle::reservar(n);
    if (!p) throw std::bad_alloc();
    return p;
}

void* operator new(std::size_t n, const std::nothrow_t&) noexcept {
    return medicion::detalle::reservar(n);
}

void* operator new[](std::size_t n, const std::nothrow_t&) noexcept {
    return medicion::detalle::reservar(n);
}

void operator delete(void* p) noexcept                    { medicion::detalle::liberar(p); }
void operator delete[](void* p) noexcept                  { medicion::detalle::liberar(p); }
void operator delete(void* p, std::size_t) noexcept       { medicion::detalle::liberar(p); }
void operator delete[](void* p, std::size_t) noexcept     { medicion::detalle::liberar(p); }
void operator delete(void* p, const std::nothrow_t&) noexcept   { medicion::detalle::liberar(p); }
void operator delete[](void* p, const std::nothrow_t&) noexcept { medicion::detalle::liberar(p); }
