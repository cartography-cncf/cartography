import unittest.mock

import typer

import cartography.cli
from tests.integration import settings


def test_cli():
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, "test")
    cli.main(["--neo4j-uri", settings.get("NEO4J_URL")])
    sync.run.assert_called_once()


def test_cli_version(capsys):
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, "test")

    exit_code = cli.main(["--version"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "cartography release " in captured.out
    assert "commit revision " in captured.out
    sync.run.assert_not_called()


def test_cli_debug_alias():
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, "test")
    cli.main(["-d", "--neo4j-uri", settings.get("NEO4J_URL")])
    sync.run.assert_called_once()


def test_cli_short_help_flag(capsys):
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, "test")

    exit_code = cli.main(["-h"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Usage:" in captured.out
    sync.run.assert_not_called()


def test_cli_handles_typer_exit_code_zero():
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, "test")

    def _app(*_args, **_kwargs):
        raise typer.Exit(code=0)

    with unittest.mock.patch.object(cli, "_build_app", return_value=_app):
        exit_code = cli.main([])

    assert exit_code == 0
