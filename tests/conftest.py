"""Shared pytest fixtures. Tests never touch the network."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def registry_dir(root: Path) -> Path:
    return root / "registry"


@pytest.fixture(scope="session")
def evidence_dir(root: Path) -> Path:
    return root / "evidence"
