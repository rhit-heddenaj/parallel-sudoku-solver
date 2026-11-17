#!/usr/bin/env python3

# Disclaimer: AI was used to assist in the creation of this file.

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path


SIZE = 25
BOX_SIZE = 5
SYMBOLS = set("ABCDEFGHIJKLMNOPQRSTUVWXY")
EMPTY = "-"
ROOT = Path(__file__).resolve().parents[1]
BOARD_DIR = Path(__file__).resolve().parent
DEFAULT_BOARD_FILE = BOARD_DIR / "board.txt"

# (name, file in tests/, should the board be solvable?)
TEST_CASES = [
    ("default", "board.txt", True),
    ("easy", "easy_board.txt", True),
    ("hard", "hard_board.txt", True),
    ("impossible", "impossible_board.txt", False),
]


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


def run_solver(name, command, puzzle, threads, timeout, solvable=True):
    environment = os.environ.copy()
    environment["OMP_NUM_THREADS"] = str(threads)
    environment["OMP_DYNAMIC"] = "FALSE"
    start = time.perf_counter()
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
    elapsed = time.perf_counter() - start

    if result.returncode != 0:
        details = (result.stdout + result.stderr).strip().splitlines()[-8:]
        raise TestFailure(
            f"{name} exited with status {result.returncode}:\n"
            + "\n".join(details)
        )

    if solvable:
        rows = extract_solution(result.stdout)
        validate_solution(puzzle, rows)
    else:
        if "Solved Sudoku puzzle:" in result.stdout:
            raise TestFailure(f"{name} reported a solution for an unsolvable board")
        if "No solution exists" not in result.stdout:
            raise TestFailure(f"{name} did not report 'No solution exists'")
    return elapsed


def main():
    parser = argparse.ArgumentParser(
        description="Check the serial and parallel 25x25 Sudoku solvers."
    )
    parser.add_argument(
        "--board",
        help="override the contents of board.txt (625 characters: '-' and A-Y)",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        choices=[case[0] for case in TEST_CASES],
        help="run only these boards (default: all)",
    )
    parser.add_argument("--threads", type=int, default=4, help="parallel thread count")
    parser.add_argument("--cutoff", type=int, default=6, help="parallel task cutoff")
    parser.add_argument("--timeout", type=int, default=300, help="per-solver timeout")
    args = parser.parse_args()

    if args.threads < 1 or args.cutoff < 1 or args.timeout < 1:
        parser.error("--threads, --cutoff, and --timeout must be positive")

    failures = 0
    for case_name, filename, solvable in TEST_CASES:
        if args.only and case_name not in args.only:
            continue

        board_arg = args.board if case_name == "default" else None
        try:
            puzzle = read_board(board_arg, BOARD_DIR / filename)
        except (OSError, TestFailure) as error:
            print(f"[{case_name}] FAIL: {error}", file=sys.stderr, flush=True)
            failures += 1
            continue

        solvers = (
            ("serial", [str(ROOT / "sudoku_serial"), f"--board={puzzle}"]),
            (
                "parallel",
                [
                    str(ROOT / "sudoku_parallel"),
                    f"--board={puzzle}",
                    f"--cutoff={args.cutoff}",
                ],
            ),
        )
        for solver_name, command in solvers:
            label = f"[{case_name}] {solver_name}"
            try:
                elapsed = run_solver(
                    label, command, puzzle, args.threads, args.timeout, solvable
                )
                print(f"{label}: PASS ({elapsed:.1f} s)", flush=True)
            except (OSError, TestFailure) as error:
                print(f"{label}: FAIL: {error}", file=sys.stderr, flush=True)
                failures += 1

    if failures:
        print(f"{failures} test(s) failed.", file=sys.stderr)
        return 1

    print("All Sudoku tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())