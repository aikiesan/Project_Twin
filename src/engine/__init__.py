"""SP Biomethane Engine.

Techno-economic and spatial simulation of biomethane production in São Paulo State.
Modules: ingest · supply · process · economics · siting · calibrate · export.
See docs/00_INDEX.md.
"""

from pathlib import Path

__version__ = "0.0.1"

#: Repository root (the folder containing ``pyproject.toml``).
ROOT = Path(__file__).resolve().parents[2]
REGISTRY_DIR = ROOT / "registry"
EVIDENCE_DIR = ROOT / "evidence"
DATA_DIR = ROOT / "data"
