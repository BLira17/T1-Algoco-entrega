# Tarea 1 - INF-221 Algoritmos y Complejidad - 2026-2
# Benjamin Lira <blira@usm.cl> - Rol: 202473586-1
# makefile - Compilacion y ejecucion del experimento de ordenamiento.
#
# Objetivos principales:
#   make            compila el binario sorting
#   make datos      genera los arreglos de entrada (scripts/array_generator.py)
#   make smoke      prueba de humo del pipeline completo con n = 10
#   make verificar  corre todos los algoritmos con --verificar sobre casos chicos
#   make run        barrido completo de mediciones -> data/measurements/
#   make plots      genera los graficos PNG -> data/plots/
#   make clean      borra objetos y binario

CXX      ?= g++
CXXSTD   := -std=c++17
OPT      := -O2
WARN     := -Wall -Wextra -pedantic
CXXFLAGS := $(CXXSTD) $(OPT) $(WARN)

# Enlazado estatico. Dos razones:
#  (1) En este equipo conviven dos entornos MSYS2 (ucrt64 y mingw64). g++ es el
#      de ucrt64 pero el loader de Windows resuelve libstdc++-6.dll contra
#      mingw64, y el binario muere al arrancar sin mensaje (exit 127).
#  (2) Un binario autocontenido no depende de que DLL este primera en el PATH,
#      lo que hace las mediciones reproducibles.
LDSTATIC := -static -static-libgcc -static-libstdc++

ifeq ($(OS),Windows_NT)
  EXE  := .exe
  # -lpsapi: GetProcessMemoryInfo (ver common/medicion.hpp)
  LIBS := -lpsapi
  PY   ?= py -3
else
  EXE  :=
  LIBS :=
  PY   ?= python3
endif

BIN  := sorting$(EXE)
SRCS := sorting.cpp \
        ../common/medicion.cpp \
        algorithms/sort.cpp \
        algorithms/mergesort.cpp \
        algorithms/quicksort.cpp \
        algorithms/patiencesort.cpp
OBJS := $(SRCS:.cpp=.o)
DEPS := algorithms/algorithms.hpp ../common/medicion.hpp

.PHONY: all datos smoke verificar run plots clean distclean

all: $(BIN)

$(BIN): $(OBJS)
	$(CXX) $(CXXFLAGS) $(LDSTATIC) -o $@ $^ $(LIBS)

%.o: %.cpp $(DEPS)
	$(CXX) $(CXXFLAGS) -c $< -o $@

datos:
	$(PY) scripts/array_generator.py

smoke: $(BIN)
	$(PY) scripts/array_generator.py --n 10 --semilla 1
	$(PY) scripts/run_experiments.py --smoke
	$(PY) scripts/plot_generator.py --csv data/measurements/smoke_sorting.csv --prefijo smoke_sorting

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
