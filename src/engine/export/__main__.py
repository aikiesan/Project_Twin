"""CLI: ``python -m engine.export verify <bundle_dir>`` re-checks a release bundle.

Exit code 0 when every file matches ``manifest.json`` (hash, size, rows, columns) and the
manifest is schema-valid; 1 otherwise (each problem is printed on its own line).
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from engine.export.bundle import verify_bundle


def main(argv: Sequence[str] | None = None) -> int:
    """Run the export CLI and return the process exit code."""
    parser = argparse.ArgumentParser(
        prog="python -m engine.export", description="Release bundle tools (engine -> PILAR-2b)."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p_verify = sub.add_parser("verify", help="re-check hashes, rows and columns of a bundle")
    p_verify.add_argument("bundle_dir", type=Path, help="bundle folder, e.g. exports/v0.1.0")
    args = parser.parse_args(argv)

    problems = verify_bundle(args.bundle_dir)
    for problem in problems:
        print(problem)
    print(f"{args.bundle_dir}: {'OK' if not problems else f'{len(problems)} problem(s)'}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
