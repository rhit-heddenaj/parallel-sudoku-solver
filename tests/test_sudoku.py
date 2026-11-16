#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


SIZE = 25
BOX_SIZE = 5
SYMBOLS = set("ABCDEFGHIJKLMNOPQRSTUVWXY")
EMPTY = "-"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD_FILE = Path(__file__).with_name("board.txt")


class TestFailure(Exception):
    pass


def read_board(board_arg, board_file):
    board = board_arg if board_arg is not None else board_file.read_text().strip()
    if len(board) != SIZE * SIZE:
        raise TestFailure(
            f"board must contain exactly {SIZE * SIZE} characters; got {len(board)}"
        )
    invalid = sorted(set(board) - SYMBOLS - {EMPTY})
    if invalid:
        raise TestFailure(f"board contains invalid characters: {''.join(invalid)}")
    return board


def extract_solution(output):
    marker = re.search(r"(?m)^Solved Sudoku puzzle:\s*$", output)
    if marker is None:
        raise TestFailure("solver did not report a solved puzzle")

    rows = []
    for line in output[marker.end():].splitlines():
        if line.startswith("|"):
            values = re.findall(r"[A-Y-]", line)
            if len(values) != SIZE:
                raise TestFailure(
                    f"could not parse a {SIZE}-cell row from solver output"
                )
            rows.append("".join(values))
            if len(rows) == SIZE:
                break

    if len(rows) != SIZE:
        raise TestFailure(f"expected {SIZE} solution rows, found {len(rows)}")
    return rows


def validate_solution(puzzle, rows):
    expected = SYMBOLS
    for row_index, row in enumerate(rows):
        if set(row) != expected:
            raise TestFailure(f"solution row {row_index + 1} is not a permutation of A-Y")

    for column in range(SIZE):
        values = {rows[row][column] for row in range(SIZE)}
        if values != expected:
            raise TestFailure(f"solution column {column + 1} is not a permutation of A-Y")

    for box_row in range(0, SIZE, BOX_SIZE):
        for box_column in range(0, SIZE, BOX_SIZE):
            values = {
                rows[row][column]
                for row in range(box_row, box_row + BOX_SIZE)
                for column in range(box_column, box_column + BOX_SIZE)
            }
            if values != expected:
                raise TestFailure(
                    f"solution box at row {box_row + 1}, column "
                    f"{box_column + 1} is not a permutation of A-Y"
                )

    for index, given in enumerate(puzzle):
        if given != EMPTY and rows[index // SIZE][index % SIZE] != given:
            raise TestFailure(
                f"solution changed the given at row {index // SIZE + 1}, "
                f"column {index % SIZE + 1}"
            )


def run_solver(name, command, puzzle, threads, timeout):
    environment = os.environ.copy()
    environment["OMP_NUM_THREADS"] = str(threads)
    environment["OMP_DYNAMIC"] = "FALSE"
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise TestFailure(f"{name} timed out after {timeout} seconds") from error

    if result.returncode != 0:
        details = (result.stdout + result.stderr).strip().splitlines()[-8:]
        raise TestFailure(
            f"{name} exited with status {result.returncode}:\n"
            + "\n".join(details)
        )

    rows = extract_solution(result.stdout)
    validate_solution(puzzle, rows)
    print(f"{name}: PASS")


def main():
    parser = argparse.ArgumentParser(
        description="Check the serial and parallel 25x25 Sudoku solvers."
    )
    parser.add_argument(
        "--board",
        help="override the board in tests/board.txt (625 characters: '-' and A-Y)",
    )
    parser.add_argument("--threads", type=int, default=4, help="parallel thread count")
    parser.add_argument("--cutoff", type=int, default=6, help="parallel task cutoff")
    parser.add_argument("--timeout", type=int, default=120, help="per-solver timeout")
    args = parser.parse_args()

    if args.threads < 1 or args.cutoff < 1 or args.timeout < 1:
        parser.error("--threads, --cutoff, and --timeout must be positive")

    try:
        puzzle = read_board(args.board, DEFAULT_BOARD_FILE)
        run_solver(
            "serial",
            [str(ROOT / "sudoku_serial"), f"--board={puzzle}"],
            puzzle,
            args.threads,
            args.timeout,
        )
        run_solver(
            "parallel",
            [
                str(ROOT / "sudoku_parallel"),
                f"--board={puzzle}",
                f"--cutoff={args.cutoff}",
            ],
            puzzle,
            args.threads,
            args.timeout,
        )
    except (OSError, TestFailure) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print("All Sudoku tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
