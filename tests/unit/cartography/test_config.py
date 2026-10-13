import inspect
import logging

import pytest

from cartography.config import Config


@pytest.mark.parametrize(
    "later,earlier",
    [
        pytest.param(
            "aws_organization_account_ids",
            "_warn_on_legacy_report_source",
            id="aws_org_ids_after_warn_legacy",
        ),
        pytest.param(
            "microsoft_tenant_id",
            "aws_organization_account_ids",
            id="ms_tenant_after_aws_org_ids",
        ),
        pytest.param(
            "microsoft_client_id",
            "microsoft_tenant_id",
            id="ms_client_id_after_ms_tenant",
        ),
        pytest.param(
            "microsoft_client_secret",
            "microsoft_client_id",
            id="ms_secret_after_ms_client_id",
        ),
        pytest.param("bbot_source", "netlify_base_url", id="bbot_after_netlify"),
        pytest.param(
            "orca_api_endpoint",
            "gcp_exclude_org_root_projects",
            id="orca_endpoint_after_gcp_exclude_root",
        ),
        pytest.param(
            "orca_api_token",
            "orca_api_endpoint",
            id="orca_token_after_orca_endpoint",
        ),
        pytest.param(
            "microsoft_delegated_auth",
            "orca_api_token",
            id="ms_delegated_after_orca_token",
        ),
        pytest.param(
            "notion_config",
            "zendesk_oauth_token",
            id="notion_after_zendesk_token",
        ),
    ],
)
def test_config_positional_order(later, earlier):
    # Act
    parameters = list(inspect.signature(Config.__init__).parameters)

    # Assert: new arguments are appended after existing ones so positional
    # callers keep working.
    assert parameters.index(later) > parameters.index(earlier)


def test_zoom_preserves_existing_positional_config_arguments() -> None:
    # Arrange: construct the positional argument list available before Zoom.
    parameters = inspect.signature(Config).parameters
    names = [name for name in parameters if not name.startswith("zoom_")]
    names = names[: names.index("microsoft_delegated_auth") + 1]
    args = [parameters[name].default for name in names]
    args[0] = "bolt://localhost:7687"
    args[names.index("jumpcloud_api_key")] = "legacy-api-key"
    args[names.index("orca_api_token")] = "legacy-orca-token"
    args[names.index("microsoft_tenant_id")] = "legacy-tenant-id"
    args[names.index("microsoft_delegated_auth")] = True

    # Act
    config = Config(*args)

    # Assert
    assert config.jumpcloud_api_key == "legacy-api-key"
    assert config.orca_api_token == "legacy-orca-token"
    assert config.microsoft_tenant_id == "legacy-tenant-id"
    assert config.microsoft_delegated_auth is True
    assert config.zoom_account_id is None
    assert config.zoom_client_id is None
    assert config.zoom_client_secret is None


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


def test_config_rejects_delegated_auth_with_application_credentials() -> None:
    # Act and assert
    with pytest.raises(ValueError, match="cannot be combined"):
        Config(
            neo4j_uri="bolt://localhost:7687",
            microsoft_tenant_id="tenant-id",
            microsoft_client_id="client-id",
            microsoft_delegated_auth=True,
        )


def test_config_requires_tenant_for_delegated_auth() -> None:
    # Act and assert
    with pytest.raises(ValueError, match="requires a Microsoft tenant ID"):
        Config(
            neo4j_uri="bolt://localhost:7687",
            microsoft_delegated_auth=True,
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


def test_jira_config_preserves_legacy_positional_slots() -> None:
    # Act
    parameters = list(inspect.signature(Config.__init__).parameters)

    # Assert
    assert parameters[72] == "lastpass_cid"
    assert parameters[225] == "orca_api_token"
    assert all(
        parameters.index(name) > parameters.index("zoom_client_secret")
        for name in ("jira_cloud_id", "jira_email", "jira_api_token", "jira_site_url")
    )


def test_microsoft_access_token_implies_delegated_auth() -> None:
    # Act
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        microsoft_tenant_id="tenant-id",
        microsoft_access_token="graph-token",
    )

    # Assert
    assert config.microsoft_delegated_auth is True
    assert config.microsoft_access_token == "graph-token"


def test_config_rejects_microsoft_access_token_with_application_credentials() -> None:
    # Act and assert
    with pytest.raises(ValueError, match="cannot be combined"):
        Config(
            neo4j_uri="bolt://localhost:7687",
            microsoft_tenant_id="tenant-id",
            microsoft_client_id="client-id",
            microsoft_client_secret="client-secret",
            microsoft_access_token="graph-token",
        )
