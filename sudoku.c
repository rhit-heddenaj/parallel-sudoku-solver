#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define SIZE 9

void print_board(int board[SIZE][SIZE]) {
    for (int i = 0; i < SIZE; i++) {
        if (i % 3 == 0) {
            printf("+-------+-------+-------+\n");
        }
        for (int j = 0; j < SIZE; j++) {
            if (j % 3 == 0) {
                printf("| ");
            }
            printf("%d ", board[i][j]);
        }
        printf("|\n");
    }
    printf("+-------+-------+-------+\n");
}

int find_empty(int board[SIZE][SIZE], int *row, int *col) {
    for (*row = 0; *row < SIZE; (*row)++) {
        for (*col = 0; *col < SIZE; (*col)++) {
            if (board[*row][*col] == 0) {
                return 1;
            }
        }
    }
    return 0;
}

int is_valid(int board[SIZE][SIZE], int num, int row, int col) {
    for (int i = 0; i < SIZE; i++) {
        if (board[row][i] == num || board[i][col] == num) {
            return 0;
        }
    }

    int box_row_start = (row / 3) * 3;
    int box_col_start = (col / 3) * 3;
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            if (board[box_row_start + i][box_col_start + j] == num) {
                return 0;
            }
        }
    }
    return 1;
}

int solve(int board[SIZE][SIZE]) {
    int row, col;
    if (!find_empty(board, &row, &col)) {
        return 1;
    }

    for (int num = 1; num <= SIZE; num++) {
        if (is_valid(board, num, row, col)) {
            board[row][col] = num;

            if (solve(board)) {
                return 1;
            }

            board[row][col] = 0;
        }
    }
    return 0;
}

void parse_board(const char *input, int board[SIZE][SIZE]) {
    for (int i = 0; i < SIZE * SIZE; i++) {
        board[i / SIZE][i % SIZE] = input[i] - '0';
    }
}

int main(int argc, char *argv[]) {
    if (argc != 2 || strncmp(argv[1], "--board=", 8) != 0) {
        printf("Usage: %s --board=530070000...\n", argv[0]);
        return 1;
    }

    const char *input = argv[1] + 8;
    if (strlen(input) != SIZE * SIZE) {
        printf("The board must be exactly 81 characters long.\n");
        return 1;
    }

    int board[SIZE][SIZE];
    parse_board(input, board);

    printf("Sudoku puzzle:\n");
    print_board(board);

    clock_t start_time = clock();

    if (solve(board)) {
        clock_t end_time = clock();
        double time_spent = (double)(end_time - start_time) / CLOCKS_PER_SEC * 1000; // Convert to milliseconds
        printf("\nSolved Sudoku puzzle:\n");
        print_board(board);
        printf("\nExecution time: %.3f ms\n", time_spent);
    } else {
        printf("No solution exists\n");
    }

    return 0;
}
