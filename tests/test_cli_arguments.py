import pytest
from dataclasses import fields

from src.cli_edition import (
    CLI,
    CliOptions,
    ROOT,
    load_arguments,
    parse_arguments,
    reset_options,
)


@pytest.fixture(autouse=True)
def isolated_cli_options():
    reset_options()
    yield
    reset_options()


def test_parse_arguments_defaults():
    options = parse_arguments([])

    assert options == CliOptions()


def test_parse_arguments_values():
    options = parse_arguments(
        [
            "--original-quality-mode",
            "global",
            "--original-quality",
            "true",
            "--record",
            "false",
            "--suspend-batches",
            "10",
            "--suspend-interval",
            "300",
        ]
    )

    assert options.original_quality_mode == "global"
    assert options.original_quality_value is True
    assert options.record is False
    assert options.suspend_batches == 10
    assert options.suspend_interval == 300


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("true", True),
        ("TRUE", True),
        ("1", True),
        ("false", False),
        ("0", False),
    ],
)
def test_record_boolean_parsing(value, expected):
    options = parse_arguments(["--record", value])

    assert options.record is expected


def test_original_quality_with_config_mode_rejected():
    with pytest.raises(SystemExit):
        parse_arguments(["--original-quality", "true"])


def test_global_mode_requires_original_quality():
    with pytest.raises(SystemExit):
        parse_arguments(["--original-quality-mode", "global"])


def test_invalid_boolean_rejected():
    with pytest.raises(SystemExit):
        parse_arguments(["--record", "invalid"])


def test_invalid_non_negative_integer_rejected():
    with pytest.raises(SystemExit):
        parse_arguments(["--suspend-batches", "invalid"])


def test_load_arguments_updates_global_cli():
    load_arguments(
        [
            "--record",
            "false",
            "--suspend-batches",
            "10",
        ]
    )

    assert CLI.record is False
    assert CLI.suspend_batches == 10


def test_volume_default():
    options = parse_arguments([])

    assert options.volume == ROOT / "Volume"


def test_volume_field_is_first():
    assert fields(CliOptions)[0].name == "volume"


def test_parse_volume_argument(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    options = parse_arguments(["--volume", "data/v1"])

    assert options.volume == (tmp_path / "data/v1").resolve()


def test_empty_volume_treated_as_unset():
    options = parse_arguments(["--volume", ""])

    assert options.volume == ROOT / "Volume"


def test_load_arguments_updates_volume(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    load_arguments(["--volume", "custom"])

    assert CLI.volume == (tmp_path / "custom").resolve()


def test_failed_load_does_not_overwrite_global_cli():
    load_arguments(["--record", "false"])

    with pytest.raises(SystemExit):
        load_arguments(["--original-quality", "true"])

    assert CLI.record is False
