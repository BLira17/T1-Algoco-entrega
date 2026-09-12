# Tarea 1 - INF-221 Algoritmos y Complejidad - 2026-2
# Benjamin Lira <blira@usm.cl> - Rol: 202473586-1
# makefile - Compilacion y ejecucion del experimento de multiplicacion de matrices.
#
# Objetivos principales:
#   make            compila el binario matrix_multiplication
#   make datos      genera las matrices de entrada (scripts/matrix_generator.py)
#   make smoke      prueba de humo del pipeline completo con n = 16
#   make verificar  corre los algoritmos con --verificar sobre casos chicos
#   make run        barrido completo de mediciones -> data/measurements/
#   make plots      genera los graficos PNG -> data/plots/
#   make clean      borra objetos y binario
#
# -O2 fijo, igual que en el experimento de ordenamiento, para que ambos sean
# comparables entre si. Declarado en el informe.

CXX      ?= g++
CXXSTD   := -std=c++17
OPT      := -O2
WARN     := -Wall -Wextra -pedantic
CXXFLAGS := $(CXXSTD) $(OPT) $(WARN)

# Enlazado estatico: ver la explicacion en ../sorting/makefile. En este equipo
# conviven dos entornos MSYS2 y el binario dinamico muere al arrancar.
LDSTATIC := -static -static-libgcc -static-libstdc++

ifeq ($(OS),Windows_NT)
  EXE  := .exe
  # -lpsapi: GetProcessMemoryInfo (ver ../common/medicion.hpp)
  LIBS := -lpsapi
  PY   ?= py -3
else
  EXE  :=
  LIBS :=
  PY   ?= python3
endif

BIN  := matrix_multiplication$(EXE)
SRCS := matrix_multiplication.cpp \
        ../common/medicion.cpp \
        algorithms/naive.cpp \
        algorithms/strassen.cpp
OBJS := $(SRCS:.cpp=.o)
DEPS := algorithms/algorithms.hpp ../common/medicion.hpp

.PHONY: all datos smoke verificar run plots clean distclean

all: $(BIN)

$(BIN): $(OBJS)
	$(CXX) $(CXXFLAGS) $(LDSTATIC) -o $@ $^ $(LIBS)

%.o: %.cpp $(DEPS)
	$(CXX) $(CXXFLAGS) -c $< -o $@

datos:
	$(PY) scripts/matrix_generator.py

# Prueba de humo: pipeline completo (generar -> medir -> graficar) con n = 16.
smoke: $(BIN)
	$(PY) scripts/matrix_generator.py --n 16 --semilla 1
	$(PY) scripts/run_experiments.py --smoke
	$(PY) scripts/plot_generator.py --csv data/measurements/smoke_matrix.csv --prefijo smoke_matrix

verificar: $(BIN)
	$(PY) scripts/run_experiments.py --solo-verificar

run: $(BIN)
	$(PY) scripts/run_experiments.py

plots:
	$(PY) scripts/plot_generator.py

clean:
	rm -f $(OBJS) $(BIN)

distclean: clean
	rm -f data/measurements/*.csv data/plots/*.png
