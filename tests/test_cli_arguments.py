import pytest

from src.cli_edition import CLI, CliOptions, load_arguments, parse_arguments, reset_options


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
            "--suspend-batches",
            "10",
            "--suspend-interval",
            "300",
        ]
    )

    assert options.original_quality_mode == "global"
    assert options.original_quality_value is True
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
def test_original_quality_boolean_parsing(value, expected):
    options = parse_arguments(
        [
            "--original-quality-mode",
            "override",
            "--original-quality",
            value,
        ]
    )

    assert options.original_quality_value is expected


def test_original_quality_with_config_mode_rejected():
    with pytest.raises(SystemExit):
        parse_arguments(["--original-quality", "true"])


def test_global_mode_requires_original_quality():
    with pytest.raises(SystemExit):
        parse_arguments(["--original-quality-mode", "global"])


def test_invalid_non_negative_integer_rejected():
    with pytest.raises(SystemExit):
        parse_arguments(["--suspend-batches", "invalid"])


def test_load_arguments_updates_global_cli():
    load_arguments(
        [
            "--original-quality-mode",
            "global",
            "--original-quality",
            "true",
            "--suspend-batches",
            "10",
        ]
    )

    assert CLI.original_quality_mode == "global"
    assert CLI.original_quality_value is True
    assert CLI.suspend_batches == 10


def test_failed_load_does_not_overwrite_global_cli():
    load_arguments(["--original-quality-mode", "global", "--original-quality", "true"])

    with pytest.raises(SystemExit):
        load_arguments(["--original-quality", "true"])

    assert CLI.original_quality_value is True


def test_reset_options_restores_defaults():
    load_arguments(["--original-quality-mode", "global", "--original-quality", "true"])

    reset_options()

    assert CLI == CliOptions()
