# Makefile for Sudoku Solver

# Compiler
CC = gcc

# Compiler Flags
CFLAGS = -O3 -march=native -flto -funroll-loops -ffast-math -fomit-frame-pointer -finline-functions -fmerge-all-constants -ffunction-sections -fdata-sections -fstack-protector-strong -falign-functions=32

# Target executable
TARGET = sudoku_solver

# Source files
SRCS = sudoku.c

# Object files
OBJS = $(SRCS:.c=.o)

# Profile data directory
PROF_DIR = prof_data

# Profile data file
PROF_FILE = $(PROF_DIR)/default.profraw

# Default target
all: $(TARGET)

# Build the target executable
$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJS)

# Compile source files to object files
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# Clean target to remove generated files
clean:
	rm -f $(TARGET) $(OBJS)

# Profile guided optimization (PGO) steps
pgo_gen: $(SRCS)
	$(CC) $(CFLAGS) -fprofile-generate=$(PROF_DIR) -o $(TARGET)_gen $(SRCS)
	./$(TARGET)_gen --board=530070000600195000098000060800060003400803001700020006060000280000419005000080079

pgo_use: $(SRCS)
	$(CC) $(CFLAGS) -fprofile-use=$(PROF_DIR) -o $(TARGET) $(SRCS)

# PGO full process
pgo: pgo_gen pgo_use

# Phony targets
.PHONY: all clean pgo_gen pgo_use pgo
