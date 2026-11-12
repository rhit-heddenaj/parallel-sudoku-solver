#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <omp.h>

#define SIZE 25
#define BOX 5
#define CUTOFF 6
#define PRINT_BOARD 0

char *letters = "-ABCDEFGHIJKLMNOPQRSTUVWXY"; // Mapping letters to numbers

// Define the structure for the key-value pairs
typedef struct {
    const int num;
    char letter;
} DictEntry;

// Define the static dictionary (file-scoped and persistent)
static const DictEntry num_to_letter[] = {
    {1, 'A'},
    {2, 'B'},
    {3, 'C'},
    {4, 'D'},
    {5, 'E'},
    {6, 'F'},
    {7, 'G'},
    {8, 'H'},
    {9, 'I'},
    {10, 'J'},
    {11, 'K'},
    {12, 'L'},
    {13, 'M'},
    {14, 'N'},
    {15, 'O'},
    {16, 'P'},
    {17, 'Q'},
    {18, 'R'},
    {19, 'S'},
    {20, 'T'},
    {21, 'U'},
    {22, 'V'},
    {23, 'W'},
    {24, 'X'},
    {25, 'Y'}
};

int get_number_from_letter(const char *search_key) {
    char *pos = strchr(letters, search_key[0]);
    if (pos) {
        return pos - letters;
    }
    return -1; // Key not found indicator
}

char get_char_from_number(const int search_key) {
    for (size_t i = 0; i < sizeof(num_to_letter) / sizeof(num_to_letter[0]); i++) {
        if (num_to_letter[i].num == search_key) {
            return num_to_letter[i].letter;
        }
    }
    return '-'; // Return '-' if not found
}

void print_board(int board[SIZE][SIZE]) {
    if(!PRINT_BOARD) {
        return;
    }
    for (int i = 0; i < SIZE; i++) {
        if (i % BOX == 0) {
            printf("+-------+-------+-------+\n");
        }
        for (int j = 0; j < SIZE; j++) {
            if (j % BOX == 0) {
                printf("| ");
            }
            printf("%c ", get_char_from_number(board[i][j]));
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

    int box_row_start = (row / BOX) * BOX;
    int box_col_start = (col / BOX) * BOX;
    for (int i = 0; i < BOX; i++) {
        for (int j = 0; j < BOX; j++) {
            if (board[box_row_start + i][box_col_start + j] == num) {
                return 0;
            }
        }
    }
    return 1;
}

static int found = 0; //have found solution?
static int solution[SIZE][SIZE];

int solve_serial(int board[SIZE][SIZE]) {
    int row, col;
    int stop;
    #pragma omp atomic read
    stop = found;
    if(stop) {
        return 0;
    }
    if (!find_empty(board, &row, &col)) {
        return 1;
    }

    for (int num = 1; num <= SIZE; num++) {
        if (is_valid(board, num, row, col)) {
            board[row][col] = num;

            if (solve_serial(board)) {
                return 1;
            }

            board[row][col] = 0;
        }
    }
    return 0;
}

static void solve_par(int board[SIZE][SIZE], int depth) {
    int stop;
    #pragma omp atomic read
    stop = found;
    if (stop) return;

    if (depth >= CUTOFF) {
        if (solve_serial(board)) {
            #pragma omp critical
            {
                if (!found) {
                    memcpy(solution, board, sizeof(solution));
                    #pragma omp atomic write
                    found = 1;
                }
            }
        }
        return;
    }

    int row, col;
    if (!find_empty(board, &row, &col)) {
        #pragma omp critical
        {
            if (!found) {
                memcpy(solution, board, sizeof(solution));
                #pragma omp atomic write
                found = 1;
            }
        }
        return;
    }

    for (int num = 1; num <= SIZE; num++) {
        if (is_valid(board, num, row, col)) {
            int copy[SIZE][SIZE];
            memcpy(copy, board, sizeof(copy));
            copy[row][col] = num;
            #pragma omp task firstprivate(copy, depth)
            solve_par(copy, depth + 1);
        }
    }
    #pragma omp taskwait
}

int solve_parallel(int board[SIZE][SIZE]) {
    found = 0;
    #pragma omp parallel
    #pragma omp single
    solve_par(board, 0);

    if (found) {
        memcpy(board, solution, sizeof(solution));
        return 1;
    }
    return 0;
}

int parse_board(const char *input, int board[SIZE][SIZE]) {
    for (int i = 0; i < SIZE * SIZE; i++) {
        int num = get_number_from_letter(&input[i]);
        if (num == -1) {
            return 0;
        }
        board[i / SIZE][i % SIZE] = num;
    }
    return 1;
}

// idk whether or not we will want to parallelize this, but I got tired of constantly inputting faulty boards and waiting indefinitely
int is_initial_board_valid(int board[SIZE][SIZE]) {
    for (int r = 0; r < SIZE; r++) {
        for (int c = 0; c < SIZE; c++) {
            int val = board[r][c];
            if (val != 0) {
                board[r][c] = 0;
                if (!is_valid(board, val, r, c)) {
                    board[r][c] = val;
                    return 0;
                }
                board[r][c] = val;
            }
        }
    }
    return 1;
}

int main(int argc, char *argv[]) {
    if (argc != 2 || strncmp(argv[1], "--board=", 8) != 0) {
        printf("Usage: %s --board=530070000...\n", argv[0]);
        return 1;
    }

    const char *input = argv[1] + 8;
    if (strlen(input) != SIZE * SIZE) {
        printf("The board must be exactly %d characters long.\n", SIZE * SIZE);
        return 1;
    }

    int board[SIZE][SIZE];
    if (!parse_board(input, board)) {
        printf("bad board format\n");
        return 1;
    }

    printf("Sudoku puzzle:\n");
    print_board(board);


    if(!is_initial_board_valid(board)) {
        printf("bad board input\n");
        return 1;
    }

    // clock_t start_time = clock();
    double t0 = omp_get_wtime();
    double solved = solve_parallel(board);
    double ms = (omp_get_wtime() - t0) * 1000.0;
    if (solved) {
        // clock_t end_time = clock();
        // double time_spent = (double)(end_time - start_time) / CLOCKS_PER_SEC * 1000; // Convert to milliseconds
        printf("\nSolved Sudoku puzzle:\n");
        print_board(board);
        printf("\nParallel execution time with %d threads: %.3f ms\n", omp_get_max_threads(), ms);
    } else {
        printf("No solution exists\n");
    }

    return 0;
}
