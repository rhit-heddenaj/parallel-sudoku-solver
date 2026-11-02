gcc -O3 -march=native -flto -funroll-loops -ffast-math -fomit-frame-pointer -finline-functions -fmerge-all-constants -falign-functions=32 -mtune=native -fno-rtti -o sudoku_solver sudoku.c 

chmod +x ./sudoku_solver

./sudoku_solver --board=530070000600195000098000060800060003400803001700020006060000280000419005000080079
