#!/bin/bash
#SBATCH --job-name=sudoku_solver
#SBATCH --output=output.txt
#SBATCH --time=00:05:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=2GB

make

BOARD="530070000600195000098000060800060003400803001700020006060000280000419005000080079"
./sudoku_solver --board=$BOARD
