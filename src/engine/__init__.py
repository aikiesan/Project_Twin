"""SP Biomethane Engine.

Techno-economic and spatial simulation of biomethane production in São Paulo State.
Modules: ingest · supply · process · economics · siting · calibrate · export.
See docs/00_INDEX.md.
"""

import os
import shutil
import sys
from collections.abc import MutableMapping
from pathlib import Path

__version__ = "0.0.1"

#: Repository root (the folder containing ``pyproject.toml``).
ROOT = Path(__file__).resolve().parents[2]
REGISTRY_DIR = ROOT / "registry"
EVIDENCE_DIR = ROOT / "evidence"
DATA_DIR = ROOT / "data"

#: PyTensor flags used on Windows machines without a C++ compiler (docs/04 §0).
WINDOWS_NO_CXX_PYTENSOR_FLAGS = "mode=NUMBA,cxx="


def configure_pytensor_defaults(
    env: MutableMapping[str, str] | None = None,
    platform: str | None = None,
    has_cxx: bool | None = None,
) -> bool:
    """Default PyTensor (PyMC's backend) to Numba on Windows when ``g++`` is not on PATH.

    Without a C++ compiler PyTensor falls back to pure-Python ops and PyMC sampling becomes very
    slow. On the project PC (2026-10-04) the Bayesian tests had not finished after minutes; with
    Numba they pass in under a minute. Numba is installed with PyMC, so nothing extra is needed.

    An explicit ``PYTENSOR_FLAGS`` is never overridden. PyTensor reads the flags once, at its
    first import, so this only works when ``engine`` is imported before ``pymc``/``pytensor``.

    Returns:
        True when the default was applied.
    """
    env = os.environ if env is None else env
    platform = sys.platform if platform is None else platform
    if "PYTENSOR_FLAGS" in env or platform != "win32":
        return False
    if has_cxx is None:
        has_cxx = shutil.which("g++") is not None
    if has_cxx:
        return False
    env["PYTENSOR_FLAGS"] = WINDOWS_NO_CXX_PYTENSOR_FLAGS
    return True


configure_pytensor_defaults()
