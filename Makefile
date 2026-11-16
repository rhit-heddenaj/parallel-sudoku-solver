# Makefile for Sudoku Solver

CC = gcc
PYTHON ?= python3
CFLAGS = -O3 -march=native -flto -fopenmp -Wall -Wextra
TIMING_THREADS ?= 1,2,4,8,12
TIMING_CUTOFFS ?= 4,8,12,16,20,24
TIMING_REPEATS ?= 1

all: sudoku_serial sudoku_parallel

test: all
	$(PYTHON) tests/test_sudoku.py

time: all
	SUDOKU_BOARD="$(BOARD)" $(PYTHON) tests/time_sudoku.py \
		--threads "$(TIMING_THREADS)" \
		--cutoffs "$(TIMING_CUTOFFS)" \
		--repeats "$(TIMING_REPEATS)"

sudoku_serial: sudoku.c
	$(CC) $(CFLAGS) -o $@ $<

sudoku_parallel: sudoku_parallel.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f sudoku_serial sudoku_parallel sudoku_solver

.PHONY: all test time clean