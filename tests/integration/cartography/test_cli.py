import logging
import unittest.mock
from typing import get_args

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


def test_cli_help_hides_deprecated_report_source_flags(capsys):
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, "test")
    app = cli._build_app(cartography.cli._parse_selected_modules_from_argv(["--help"]))
    annotations = app.registered_commands[0].callback.__annotations__

    for field in (
        "trivy_source",
        "syft_source",
        "aibom_source",
        "docker_scout_source",
    ):
        assert get_args(annotations[field])[1].hidden is False

    for field in (
        "trivy_results_dir",
        "trivy_s3_bucket",
        "trivy_s3_prefix",
        "syft_results_dir",
        "syft_s3_bucket",
        "syft_s3_prefix",
        "aibom_results_dir",
        "aibom_s3_bucket",
        "aibom_s3_prefix",
        "docker_scout_results_dir",
        "docker_scout_s3_bucket",
        "docker_scout_s3_prefix",
    ):
        assert get_args(annotations[field])[1].hidden is True

    exit_code = cli.main(["--help"])
    captured = capsys.readouterr()

    assert exit_code == 0
    for flag in (
        "--trivy-results-dir",
        "--trivy-s3-bucket",
        "--trivy-s3-prefix",
        "--syft-results-dir",
        "--syft-s3-bucket",
        "--syft-s3-prefix",
        "--aibom-results-dir",
        "--aibom-s3-bucket",
        "--aibom-s3-prefix",
        "--docker-scout-results-dir",
        "--docker-scout-s3-bucket",
        "--docker-scout-s3-prefix",
    ):
        assert flag not in captured.out
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
    assert caplog.text.count("DEPRECATED: --trivy-results-dir") == 1


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
