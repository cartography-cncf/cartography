import inspect
import logging

import pytest

from cartography.config import Config


def test_aws_organization_account_ids_preserves_config_positional_compatibility() -> (
    None
):
    parameters = list(inspect.signature(Config.__init__).parameters)

    assert parameters.index("aws_organization_account_ids") > parameters.index(
        "_warn_on_legacy_report_source",
    )
    assert parameters.index("microsoft_tenant_id") > parameters.index(
        "aws_organization_account_ids",
    )
    assert parameters.index("microsoft_client_id") > parameters.index(
        "microsoft_tenant_id",
    )
    assert parameters.index("microsoft_client_secret") > parameters.index(
        "microsoft_client_id",
    )


def test_config_microsoft_credentials_are_canonical(caplog) -> None:
    # Arrange and act
    with caplog.at_level(logging.WARNING):
        config = Config(
            neo4j_uri="bolt://localhost:7687",
            microsoft_tenant_id="tenant-id",
            microsoft_client_id="client-id",
            microsoft_client_secret="client-secret",
        )

    # Assert
    assert config.microsoft_tenant_id == "tenant-id"
    assert config.microsoft_client_id == "client-id"
    assert config.microsoft_client_secret == "client-secret"
    assert config.entra_tenant_id == "tenant-id"
    assert config.entra_client_id == "client-id"
    assert config.entra_client_secret == "client-secret"
    assert "DEPRECATED" not in caplog.text


def test_config_legacy_entra_credentials_populate_microsoft_aliases(caplog) -> None:
    # Arrange and act
    with caplog.at_level(logging.WARNING):
        config = Config(
            neo4j_uri="bolt://localhost:7687",
            entra_tenant_id="tenant-id",
            entra_client_id="client-id",
            entra_client_secret="client-secret",
        )

    # Assert
    assert config.microsoft_tenant_id == "tenant-id"
    assert config.microsoft_client_id == "client-id"
    assert config.microsoft_client_secret == "client-secret"
    assert config.entra_tenant_id == "tenant-id"
    assert config.entra_client_id == "client-id"
    assert config.entra_client_secret == "client-secret"
    assert "DEPRECATED: `entra_tenant_id`/`entra_client_id`" in caplog.text
    assert "Cartography v1.0.0" in caplog.text


def test_config_rejects_mixed_microsoft_and_entra_credentials() -> None:
    # Act and assert
    with pytest.raises(ValueError, match="Cannot mix Microsoft credential"):
        Config(
            neo4j_uri="bolt://localhost:7687",
            microsoft_tenant_id="tenant-id",
            entra_client_id="client-id",
        )


def test_config_legacy_s3_source_shim_matches_cli_normalization(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        config = Config(
            neo4j_uri="bolt://localhost:7687",
            trivy_s3_bucket="example-bucket",
            trivy_s3_prefix="/reports/trivy/",
        )

    assert config.trivy_source == "s3://example-bucket/reports/trivy/"
    assert config.trivy_s3_bucket == "example-bucket"
    assert config.trivy_s3_prefix == "/reports/trivy/"
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
            syft_results_dir="/tmp/syft-results",
        )

    assert config.syft_source == "/tmp/syft-results"
    assert config.syft_results_dir == "/tmp/syft-results"
    assert "DEPRECATED: `syft_results_dir`" in caplog.text


def test_config_rejects_empty_legacy_local_source() -> None:
    with pytest.raises(ValueError, match="Report source cannot be empty"):
        Config(
            neo4j_uri="bolt://localhost:7687",
            syft_results_dir="",
        )


def test_config_rejects_source_with_legacy_s3_fields() -> None:
    with pytest.raises(ValueError, match="Cannot use `trivy_source`"):
        Config(
            neo4j_uri="bolt://localhost:7687",
            trivy_source="gs://example-bucket/reports/trivy/",
            trivy_s3_bucket="example-bucket",
        )


def test_config_rejects_legacy_prefix_without_bucket() -> None:
    with pytest.raises(ValueError, match="`syft_s3_prefix` requires `syft_s3_bucket`"):
        Config(
            neo4j_uri="bolt://localhost:7687",
            syft_s3_prefix="reports/syft/",
        )
