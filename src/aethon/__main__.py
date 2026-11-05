"""Run an existing research entry point without changing its arguments."""
import argparse
import runpy
import sys

COMMANDS = {
    "benchmark": "run_benchmark",
    "detect": "run_detection_benchmark",
    "train": "train_detector",
    "integrity": "research_integrity",
    "generalization": "research_generalization",
    "baseline": "research_baseline",
    "dp": "research_dp",
}


def main():
    parser = argparse.ArgumentParser(description="AETHON research commands")
    parser.add_argument("command", choices=COMMANDS)
    # Parse only the command: remaining flags belong to the original CLI.
    args = parser.parse_args(sys.argv[1:2])
    original = sys.argv
    try:
        sys.argv = [COMMANDS[args.command], *original[2:]]
        runpy.run_module(COMMANDS[args.command], run_name="__main__")
    finally:
        sys.argv = original


if __name__ == "__main__":
    main()
