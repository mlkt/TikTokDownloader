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
            "--suspend-batches",
            "10",
            "--suspend-interval",
            "300",
        ]
    )

    assert options.suspend_batches == 10
    assert options.suspend_interval == 300


def test_invalid_non_negative_integer_rejected():
    with pytest.raises(SystemExit):
        parse_arguments(["--suspend-batches", "invalid"])


def test_load_arguments_updates_global_cli():
    load_arguments(
        [
            "--suspend-batches",
            "10",
        ]
    )

    assert CLI.suspend_batches == 10
    assert CLI.suspend_interval == 30


def test_failed_load_does_not_overwrite_global_cli():
    load_arguments(["--suspend-batches", "10"])

    with pytest.raises(SystemExit):
        load_arguments(["--suspend-batches", "invalid"])

    assert CLI.suspend_batches == 10


def test_reset_options_restores_defaults():
    load_arguments(["--suspend-batches", "10"])

    reset_options()

    assert CLI == CliOptions()
