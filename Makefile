# Makefile for Sudoku Solver

# Compiler
CC = gcc

# Compiler Flags
CFLAGS = -O3 -march=native -flto -funroll-loops -ffast-math -fomit-frame-pointer -finline-functions -fmerge-all-constants -ffunction-sections -fdata-sections -fstack-protector-strong -falign-functions=32 -fopenmp
# Default target
all: sudoku_serial sudoku_parallel

sudoku_serial: sudoku.c
	$(CC) $(CFLAGS) -o sudoku_serial sudoku.c

sudoku_parallel: sudoku_parallel.c
	$(CC) $(CFLAGS) -o sudoku_parallel sudoku_parallel.c
	
# Phony targets
.PHONY: all clean pgo_gen pgo_use pgo
