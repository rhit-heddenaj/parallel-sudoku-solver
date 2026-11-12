# Makefile for Sudoku Solver

CC = gcc
CFLAGS = -O3 -march=native -flto -fopenmp -Wall -Wextra

all: sudoku_serial sudoku_parallel

sudoku_serial: sudoku.c
	$(CC) $(CFLAGS) -o $@ $<

sudoku_parallel: sudoku_parallel.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f sudoku_serial sudoku_parallel sudoku_solver

.PHONY: all clean