#!/usr/bin/env python3
import argparse
import math
import os
import re
import statistics
import subprocess
import sys

from test_sudoku import (
    DEFAULT_BOARD_FILE,
    ROOT,
    TestFailure,
    extract_solution,
    read_board,
    validate_solution,
)


def parse_positive_list(value):
    try:
        values = [int(item.strip()) for item in value.split(",")]
    except ValueError as error:
        raise argparse.ArgumentTypeError("expected comma-separated integers") from error
    if not values or any(item < 1 for item in values):
        raise argparse.ArgumentTypeError("values must be positive integers")
    if len(set(values)) != len(values):
        raise argparse.ArgumentTypeError("values must not contain duplicates")
    return values


def measure(command, puzzle, threads, timeout, parallel):
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
        raise TestFailure(f"solver timed out after {timeout} seconds") from error

    if result.returncode != 0:
        details = (result.stdout + result.stderr).strip().splitlines()[-8:]
        raise TestFailure(
            f"solver exited with status {result.returncode}:\n"
            + "\n".join(details)
        )

    rows = extract_solution(result.stdout)
    validate_solution(puzzle, rows)

    if parallel:
        match = re.search(
            r"(?m)^Parallel execution time with (\d+) threads: "
            r"([0-9]+(?:\.[0-9]+)?) ms$",
            result.stdout,
        )
        if match is None:
            raise TestFailure("could not read parallel execution time from solver output")
        actual_threads = int(match.group(1))
        if actual_threads != threads:
            raise TestFailure(
                f"requested {threads} threads but solver reports {actual_threads}"
            )
    else:
        match = re.search(
            r"(?m)^Serial execution time: ([0-9]+(?:\.[0-9]+)?) ms$",
            result.stdout,
        )
        if match is None:
            raise TestFailure("could not read serial execution time from solver output")

    elapsed_ms = float(match.group(match.lastindex))
    if not math.isfinite(elapsed_ms) or elapsed_ms <= 0:
        raise TestFailure(
            "solver reported a non-positive execution time; "
            "use a board that takes longer to solve"
        )
    return elapsed_ms


def build_parser():
    parser = argparse.ArgumentParser(
        description="Benchmark parallel Sudoku configurations against the serial solver."
    )
    parser.add_argument(
        "--board",
        help="override the board in tests/board.txt (625 characters: '-' and A-Y)",
    )
    parser.add_argument(
        "--threads",
        type=parse_positive_list,
        default=parse_positive_list("1,2,4,8"),
        help="comma-separated thread counts (default: 1,2,4,8)",
    )
    parser.add_argument(
        "--cutoffs",
        type=parse_positive_list,
        default=parse_positive_list("4,8"),
        help="comma-separated parallel cutoffs (default: 4,8)",
    )
    parser.add_argument(
        "--repeats", type=int, default=3, help="timed runs per configuration (default: 3)"
    )
    parser.add_argument(
        "--timeout", type=int, default=120, help="timeout in seconds per run (default: 120)"
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.repeats < 1 or args.timeout < 1:
        parser.error("--repeats and --timeout must be positive")

    board_arg = args.board or os.environ.get("SUDOKU_BOARD") or None

    try:
        puzzle = read_board(board_arg, DEFAULT_BOARD_FILE)
        serial_command = [str(ROOT / "sudoku_serial"), f"--board={puzzle}"]
        parallel_executable = str(ROOT / "sudoku_parallel")

        print(f"Running serial warm-up and {args.repeats} timed runs...", flush=True)
        measure(serial_command, puzzle, 1, args.timeout, parallel=False)
        serial_runs = [
            measure(serial_command, puzzle, 1, args.timeout, parallel=False)
            for _ in range(args.repeats)
        ]
        serial_ms = statistics.median(serial_runs)

        results = []
        total_configs = len(args.threads) * len(args.cutoffs)
        config_index = 0
        for cutoff in args.cutoffs:
            for threads in args.threads:
                config_index += 1
                print(
                    f"Timing configuration {config_index}/{total_configs}: "
                    f"cutoff={cutoff}, threads={threads}",
                    flush=True,
                )
                command = [
                    parallel_executable,
                    f"--board={puzzle}",
                    f"--cutoff={cutoff}",
                ]
                measure(command, puzzle, threads, args.timeout, parallel=True)
                runs = [
                    measure(command, puzzle, threads, args.timeout, parallel=True)
                    for _ in range(args.repeats)
                ]
                results.append((cutoff, threads, statistics.median(runs)))
    except (OSError, TestFailure) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print(f"\nSerial baseline: {serial_ms:.3f} ms (median of {args.repeats} runs)")
    print(
        f"{'Cutoff':>8} | {'Threads':>7} | {'Parallel (ms)':>13} | "
        f"{'Speedup':>9}"
    )
    print("-" * 48)
    for cutoff, threads, elapsed_ms in results:
        speedup = serial_ms / elapsed_ms
        print(
            f"{cutoff:>8} | {threads:>7} | {elapsed_ms:>13.3f} | "
            f"{speedup:>8.2f}x"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
