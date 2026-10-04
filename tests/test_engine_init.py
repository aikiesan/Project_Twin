"""Tests for the package-level PyTensor default (pure function, no real environment touched)."""

from engine import WINDOWS_NO_CXX_PYTENSOR_FLAGS, configure_pytensor_defaults


def test_windows_without_compiler_gets_numba():
    env: dict[str, str] = {}
    assert configure_pytensor_defaults(env, platform="win32", has_cxx=False)
    assert env == {"PYTENSOR_FLAGS": WINDOWS_NO_CXX_PYTENSOR_FLAGS}


def test_explicit_flags_win_and_other_platforms_untouched():
    env = {"PYTENSOR_FLAGS": "mode=FAST_RUN"}
    assert not configure_pytensor_defaults(env, platform="win32", has_cxx=False)
    assert env == {"PYTENSOR_FLAGS": "mode=FAST_RUN"}
    for platform, has_cxx in (("win32", True), ("linux", False), ("darwin", False)):
        env = {}
        assert not configure_pytensor_defaults(env, platform=platform, has_cxx=has_cxx)
        assert env == {}
