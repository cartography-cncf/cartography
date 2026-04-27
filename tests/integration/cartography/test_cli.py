import logging
import unittest.mock

import typer

import cartography.cli
from tests.integration import settings


def test_cli():
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, "test")
    cli.main(["--neo4j-uri", settings.get("NEO4J_URL")])
    sync.run.assert_called_once()


def test_cli_neo4j_liveness_check_timeout():
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, "test")
    cli.main(
        [
            "--neo4j-uri",
            settings.get("NEO4J_URL"),
            "--neo4j-liveness-check-timeout",
            "60",
        ],
    )
    sync.run.assert_called_once()
    config = sync.run.call_args[0][1]
    assert config.neo4j_liveness_check_timeout == 60


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


def test_cli_trivy_source_sets_config():
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, "test")

    cli.main(
        [
            "--neo4j-uri",
            settings.get("NEO4J_URL"),
            "--trivy-source",
            "gs://example-bucket/reports/trivy/",
        ],
    )

    sync.run.assert_called_once()
    config = sync.run.call_args[0][1]
    assert config.trivy_source == "gs://example-bucket/reports/trivy/"


def test_cli_trivy_legacy_results_dir_sets_source(caplog):
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, "test")

    with caplog.at_level(logging.WARNING):
        cli.main(
            [
                "--neo4j-uri",
                settings.get("NEO4J_URL"),
                "--trivy-results-dir",
                "/tmp/trivy-results",
            ],
        )

    sync.run.assert_called_once()
    config = sync.run.call_args[0][1]
    assert config.trivy_source == "/tmp/trivy-results"
    assert config.trivy_results_dir == "/tmp/trivy-results"
    assert "DEPRECATED: --trivy-results-dir" in caplog.text


def test_cli_trivy_legacy_s3_flags_preserve_config_fields(caplog):
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, "test")

    with caplog.at_level(logging.WARNING):
        cli.main(
            [
                "--neo4j-uri",
                settings.get("NEO4J_URL"),
                "--trivy-s3-bucket",
                "example-bucket",
                "--trivy-s3-prefix",
                "reports/trivy/",
            ],
        )

    sync.run.assert_called_once()
    config = sync.run.call_args[0][1]
    assert config.trivy_source == "s3://example-bucket/reports/trivy/"
    assert config.trivy_s3_bucket == "example-bucket"
    assert config.trivy_s3_prefix == "reports/trivy/"
    assert caplog.text.count("DEPRECATED: --trivy-s3-bucket/--trivy-s3-prefix") == 1


def test_cli_rejects_mixed_trivy_source_flags():
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, "test")

    exit_code = cli.main(
        [
            "--neo4j-uri",
            settings.get("NEO4J_URL"),
            "--trivy-source",
            "s3://example-bucket/reports/trivy/",
            "--trivy-results-dir",
            "/tmp/trivy-results",
        ],
    )

    assert exit_code == 1
    sync.run.assert_not_called()
