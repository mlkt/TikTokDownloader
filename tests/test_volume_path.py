from pathlib import Path

import pytest

from main import parse_arguments
from src.custom import get_volume, is_custom_volume, set_volume_path
from src.custom import internal as custom_internal


@pytest.fixture(autouse=True)
def isolated_volume(monkeypatch, tmp_path):
    """将路径状态隔离到临时目录，避免测试污染真实 Volume。"""
    monkeypatch.setattr(custom_internal, "ROOT", tmp_path)
    monkeypatch.setattr(custom_internal, "_VOLUME_PATH", None)
    monkeypatch.setattr(custom_internal, "_CUSTOM_VOLUME", False)


def test_default_volume_path(tmp_path):
    path = set_volume_path(None)

    assert path == tmp_path / "Volume"
    assert path.is_dir()
    assert not is_custom_volume()


def test_custom_absolute_volume_path(tmp_path):
    target = tmp_path / "data" / "my-volume"

    path = set_volume_path(target)

    assert path == target.resolve()
    assert path.is_dir()
    assert get_volume() == path
    assert is_custom_volume()


def test_relative_volume_path(tmp_path):
    path = set_volume_path("data/Volume")

    assert path == (tmp_path / "data" / "Volume").resolve()
    assert path.is_dir()


def test_existing_file_is_rejected(tmp_path):
    target = tmp_path / "invalid"
    target.write_text("not a directory", encoding="utf-8")

    with pytest.raises(ValueError, match="指定的路径不是目录"):
        set_volume_path(target)


def test_custom_path_does_not_create_default_volume(tmp_path):
    set_volume_path(tmp_path / "custom-volume")

    assert is_custom_volume()
    assert not (tmp_path / "Volume").exists()


def test_reset_returns_to_default(tmp_path):
    set_volume_path(tmp_path / "custom-volume")

    path = set_volume_path(None)

    assert path == tmp_path / "Volume"
    assert not is_custom_volume()


def test_parse_volume_argument(tmp_path):
    args = parse_arguments(["--volume", str(tmp_path / "from-cli")])

    assert args.volume == str(tmp_path / "from-cli")


def test_volume_alias_resolves_current_path(tmp_path):
    from src.custom import VOLUME

    assert isinstance(VOLUME, Path)
