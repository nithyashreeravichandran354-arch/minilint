"""Command-line entry point: `python -m minilint file1.py file2.py ...`"""

import argparse
import sys

from .engine import lint_file


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="minilint",
        description="A tiny AST-based static analysis tool for Python.",
    )
    parser.add_argument("files", nargs="+", help="Python source files to lint")
    args = parser.parse_args(argv)

    total = 0
    for path in args.files:
        diagnostics = lint_file(path)
        for diag in diagnostics:
            print(diag.format(path))
        total += len(diagnostics)

    if total:
        print(f"\n{total} issue(s) found.")
        return 1
    print("No issues found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
