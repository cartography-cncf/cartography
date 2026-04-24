import logging

from cartography.config import Config


def test_config_legacy_s3_source_shim_matches_cli_normalization(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        config = Config(
            neo4j_uri="bolt://localhost:7687",
            trivy_s3_bucket="example-bucket",
            trivy_s3_prefix="/reports/trivy/",
        )

    assert config.trivy_source == "s3://example-bucket/reports/trivy/"
    assert "DEPRECATED: `trivy_s3_bucket`/`trivy_s3_prefix`" in caplog.text
    assert "Cartography v1.0.0" in caplog.text


def test_config_legacy_s3_source_shim_omits_trailing_slash_for_empty_prefix(
    caplog,
) -> None:
    with caplog.at_level(logging.WARNING):
        config = Config(
            neo4j_uri="bolt://localhost:7687",
            aibom_s3_bucket="example-bucket",
            aibom_s3_prefix="",
        )

    assert config.aibom_source == "s3://example-bucket"
    assert "DEPRECATED: `aibom_s3_bucket`/`aibom_s3_prefix`" in caplog.text


def test_config_legacy_local_source_shim_emits_warning(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        config = Config(
            neo4j_uri="bolt://localhost:7687",
            docker_scout_results_dir="/tmp/docker-scout",
        )

    assert config.docker_scout_source == "/tmp/docker-scout"
    assert "DEPRECATED: `docker_scout_results_dir`" in caplog.text
