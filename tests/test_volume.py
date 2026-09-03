from pathlib import Path

from src.cli_edition import ROOT, resolve_volume_path


def test_resolve_volume_relative_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert resolve_volume_path("data") == (tmp_path / "data").resolve()


def test_resolve_volume_absolute_path(tmp_path):
    absolute = tmp_path / "absolute"

    assert resolve_volume_path(str(absolute)) == absolute.resolve()


def test_resolve_volume_default():
    assert resolve_volume_path() == ROOT / "Volume"
    assert resolve_volume_path("") == ROOT / "Volume"


def test_resolve_volume_returns_directory_path():
    path = resolve_volume_path("data")

    assert isinstance(path, Path)
