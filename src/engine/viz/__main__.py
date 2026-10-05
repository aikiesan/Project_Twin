"""CLI: ``python -m engine.viz`` builds the local viewer and optionally serves it.

Examples::

    uv run python -m engine.viz --serve            # build exports/viewer/ and serve :8765
    uv run python -m engine.viz --no-layers        # quick rebuild of tables only
    uv run python -m engine.viz --no-private --out exports/viewer_public  # no data/private

The viewer needs a web server (browsers block ``fetch`` from ``file://``).
"""

from __future__ import annotations

import argparse
import functools
import http.server
from collections.abc import Sequence
from pathlib import Path

from engine.viz.build import build


def main(argv: Sequence[str] | None = None) -> int:
    """Build (and optionally serve) the viewer; returns the process exit code."""
    ap = argparse.ArgumentParser(prog="python -m engine.viz", description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, default=Path("exports/viewer"))
    ap.add_argument("--no-private", action="store_true", help="leave out data/private layers")
    ap.add_argument("--no-layers", action="store_true", help="skip map layers (fast)")
    ap.add_argument("--no-prs", action="store_true", help="do not call the gh CLI")
    ap.add_argument("--serve", action="store_true", help="serve the folder after building")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args(argv)

    data = build(
        args.repo,
        args.out,
        include_private=not args.no_private,
        with_layers=not args.no_layers,
        with_prs=not args.no_prs,
    )
    print(
        f"viewer: {len(data['sources'])} sources, {len(data['layers'])} layers, "
        f"{len(data['commits'])} commits -> {args.out}"
    )
    for problem in data["layer_problems"]:
        print(f"  layer problem: {problem}")
    if args.serve:
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(args.out))
        with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as httpd:
            print(f"serving http://127.0.0.1:{args.port}/  (Ctrl+C to stop)")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
