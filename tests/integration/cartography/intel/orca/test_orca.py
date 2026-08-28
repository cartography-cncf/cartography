from copy import deepcopy
from typing import Any

import pytest
import requests

import cartography.intel.cve_metadata
import cartography.intel.orca
from cartography.config import Config
from tests.data.orca import ALERT_ID_1
from tests.data.orca import ALERT_ID_2
from tests.data.orca import ALERTS
from tests.data.orca import API_ENDPOINT
from tests.data.orca import API_TOKEN
from tests.data.orca import ASSET_UNIQUE_ID_1
from tests.data.orca import ASSET_UNIQUE_ID_2
from tests.data.orca import CVE_ID_1
from tests.data.orca import INVENTORY_ID_1
from tests.data.orca import INVENTORY_ID_2
from tests.data.orca import ORGANIZATION
from tests.data.orca import ORGANIZATION_ID
from tests.data.orca import PROVIDER_ID_1
from tests.data.orca import PROVIDER_ID_2
from tests.data.orca import TARGET_ARN_1
from tests.data.orca import VULNERABILITIES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
OTHER_ORGANIZATION_ID = "other-orca-organization"


def _sync_metadata_id(organization_id: str) -> str:
    return f"OrcaOrganization_{organization_id}_OrcaData"


@pytest.fixture(autouse=True)
def cleanup_orca_test_data(neo4j_session):
    metadata_ids = [
        _sync_metadata_id(ORGANIZATION_ID),
        _sync_metadata_id(OTHER_ORGANIZATION_ID),
    ]
    cleanup_query = """
    MATCH (n)
    WHERE n:OrcaOrganization
       OR n:OrcaAsset
       OR n:OrcaAlert
       OR n:OrcaVulnerability
       OR n:OrcaVulnerabilityFinding
    DETACH DELETE n
    """
    neo4j_session.run(cleanup_query)
    neo4j_session.run(
        "MATCH (n:CVEMetadata {id: $cve_id}) DETACH DELETE n",
        cve_id=CVE_ID_1,
    )
    neo4j_session.run(
        "MATCH (n:CVEMetadataFeed {id: 'CVE_METADATA'}) DETACH DELETE n",
    )
    neo4j_session.run(
        """
        MATCH (n:ModuleSyncMetadata)
        WHERE n.id IN $metadata_ids
        DETACH DELETE n
        """,
        metadata_ids=metadata_ids,
    )

    yield

    neo4j_session.run(cleanup_query)
    neo4j_session.run(
        "MATCH (n:CVEMetadata {id: $cve_id}) DETACH DELETE n",
        cve_id=CVE_ID_1,
    )
    neo4j_session.run(
        "MATCH (n:CVEMetadataFeed {id: 'CVE_METADATA'}) DETACH DELETE n",
    )
    neo4j_session.run(
        """
        MATCH (n:ModuleSyncMetadata)
        WHERE n.id IN $metadata_ids
        DETACH DELETE n
        """,
        metadata_ids=metadata_ids,
    )


def _config(update_tag: int = TEST_UPDATE_TAG) -> Config:
    return Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        orca_api_endpoint=API_ENDPOINT,
        orca_api_token=API_TOKEN,
    )


def _patch_orca_api(
    mocker,
    *,
    organization: dict[str, Any] | None = None,
    alerts: list[dict[str, Any]] | None = None,
    vulnerabilities: list[dict[str, Any]] | None = None,
):
    state: dict[str, Any] = {
        "organization": deepcopy(
            ORGANIZATION if organization is None else organization
        ),
        "Alert": deepcopy(ALERTS if alerts is None else alerts),
        "VulnerabilityV2": deepcopy(
            VULNERABILITIES if vulnerabilities is None else vulnerabilities,
        ),
    }

    def get_organization(_session, _api_endpoint):
        return deepcopy(state["organization"])

    mocker.patch(
        "cartography.intel.orca.api.get_organization",
        side_effect=get_organization,
    )

    def query(_session, _api_endpoint, payload):
        models = payload["query"]["models"]
        if models == ["Inventory"]:
            raise AssertionError("Orca must not enumerate standalone Inventory")
        if models not in (["Alert"], ["VulnerabilityV2"]):
            raise AssertionError(f"Unexpected Orca Serving Layer models: {models!r}")

        rows = state[models[0]]
        start_index = payload["start_at_index"]
        page = rows[start_index : start_index + payload["limit"]]
        return {"data": deepcopy(page), "total_items": len(rows)}

    query_mock = mocker.patch(
        "cartography.intel.orca.api.serving_layer_query",
        side_effect=query,
    )
    return state, query_mock


def _second_target_inventory() -> dict[str, Any]:
    return {
        "id": INVENTORY_ID_2,
        "type": "AzureStorageAccount",
        "name": "synthetic-storage",
        "asset_unique_id": ASSET_UNIQUE_ID_2,
        "data": {
            "UiUniqueField": {"value": PROVIDER_ID_2},
            "CloudProvider": {"value": "azure"},
            "CloudAccountId": {"value": "subscription-1"},
            "Region": {"value": "westus2"},
        },
    }


def _resource_edges(neo4j_session) -> set[tuple[str, str]]:
    alert_edges = check_rels(
        neo4j_session,
        "OrcaOrganization",
        "id",
        "OrcaAlert",
        "id",
        "RESOURCE",
    )
    vulnerability_edges = check_rels(
        neo4j_session,
        "OrcaOrganization",
        "id",
        "OrcaVulnerabilityFinding",
        "id",
        "RESOURCE",
    )
    return alert_edges | vulnerability_edges


def _affects_count(neo4j_session) -> int:
    return neo4j_session.run(
        """
        MATCH (finding)-[r:AFFECTS]->()
        WHERE finding:OrcaAlert OR finding:OrcaVulnerabilityFinding
        RETURN count(r) AS count
        """,
    ).single()["count"]


def test_start_orca_ingestion_loads_finding_only_ontology_graph(
    neo4j_session,
    mocker,
):
    # Arrange
    _patch_orca_api(mocker)

    # Act
    cartography.intel.orca.start_orca_ingestion(neo4j_session, _config())

    # Assert
    assert check_nodes(
        neo4j_session,
        "OrcaOrganization",
        ["id", "name", "_ont_name", "_ont_source"],
    ) == {
        (
            ORGANIZATION_ID,
            "Example Orca Organization",
            "Example Orca Organization",
            "orca",
        ),
    }
    assert check_nodes(neo4j_session, "OrcaAsset", ["id"]) == set()
    assert check_nodes(
        neo4j_session,
        "OrcaAlert",
        [
            "orca_id",
            "target_orca_inventory_id",
            "target_orca_asset_unique_id",
            "target_provider_id",
            "target_arn",
            "target_cloud_provider",
            "target_cloud_account_id",
            "target_region",
            "target_name",
            "target_type",
        ],
    ) == {
        (
            ALERT_ID_1,
            INVENTORY_ID_1,
            ASSET_UNIQUE_ID_1,
            PROVIDER_ID_1,
            TARGET_ARN_1,
            "aws",
            "111122223333",
            "us-west-2",
            "synthetic-app-server",
            "AwsEc2Instance",
        ),
        (
            ALERT_ID_2,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            "removed-asset",
            "Unknown",
        ),
    }
    assert check_nodes(
        neo4j_session,
        "SecurityIssue",
        [
            "orca_id",
            "_ont_title",
            "_ont_severity",
            "_ont_type",
            "_ont_status",
            "_ont_source",
        ],
    ) == {
        (
            ALERT_ID_1,
            "Internet-facing compute asset",
            "high",
            "CONFIGURATION",
            "open",
            "orca",
        ),
        (
            ALERT_ID_2,
            "Deleted asset retained for investigation",
            "low",
            "DATA_AT_RISK",
            "ignored",
            "orca",
        ),
    }
    assert check_nodes(
        neo4j_session,
        "OrcaVulnerabilityFinding",
        [
            "cve_id",
            "target_orca_inventory_id",
            "target_orca_asset_unique_id",
            "target_provider_id",
            "target_arn",
            "target_cloud_provider",
            "target_cloud_account_id",
            "target_region",
            "target_name",
            "target_type",
            "_ont_cve_id",
            "_ont_base_score",
            "_ont_base_severity",
            "_ont_source",
        ],
    ) == {
        (
            CVE_ID_1,
            None,
            ASSET_UNIQUE_ID_1,
            PROVIDER_ID_1,
            TARGET_ARN_1,
            "aws",
            "111122223333",
            "us-west-2",
            "synthetic-app-server",
            "AwsEc2Instance",
            CVE_ID_1,
            9.8,
            "critical",
            "orca",
        ),
    }
    assert check_rels(
        neo4j_session,
        "OrcaOrganization",
        "id",
        "OrcaAlert",
        "orca_id",
        "RESOURCE",
    ) == {
        (ORGANIZATION_ID, ALERT_ID_1),
        (ORGANIZATION_ID, ALERT_ID_2),
    }
    assert check_rels(
        neo4j_session,
        "OrcaOrganization",
        "id",
        "OrcaVulnerabilityFinding",
        "cve_id",
        "RESOURCE",
    ) == {(ORGANIZATION_ID, CVE_ID_1)}
    assert _affects_count(neo4j_session) == 0
    semantic_collisions = neo4j_session.run(
        """
        MATCH (n)
        WHERE (n:OrcaAlert AND n:CVE)
           OR (n:OrcaVulnerabilityFinding AND n:SecurityIssue)
        RETURN count(n) AS count
        """,
    ).single()
    assert semantic_collisions["count"] == 0


def test_same_target_identifiers_remain_scoped_by_organization(
    neo4j_session,
    mocker,
):
    # Arrange
    state, _ = _patch_orca_api(mocker)

    # Act
    cartography.intel.orca.start_orca_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )
    state["organization"] = {
        "id": OTHER_ORGANIZATION_ID,
        "name": "Other synthetic Orca organization",
        "api_url": API_ENDPOINT,
    }
    cartography.intel.orca.start_orca_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG + 1),
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "OrcaAlert",
        ["id", "organization_id", "orca_id", "target_orca_asset_unique_id"],
    ) == {
        (
            f"orca:{ORGANIZATION_ID}:{ALERT_ID_1}",
            ORGANIZATION_ID,
            ALERT_ID_1,
            ASSET_UNIQUE_ID_1,
        ),
        (
            f"orca:{ORGANIZATION_ID}:{ALERT_ID_2}",
            ORGANIZATION_ID,
            ALERT_ID_2,
            None,
        ),
        (
            f"orca:{OTHER_ORGANIZATION_ID}:{ALERT_ID_1}",
            OTHER_ORGANIZATION_ID,
            ALERT_ID_1,
            ASSET_UNIQUE_ID_1,
        ),
        (
            f"orca:{OTHER_ORGANIZATION_ID}:{ALERT_ID_2}",
            OTHER_ORGANIZATION_ID,
            ALERT_ID_2,
            None,
        ),
    }
    vulnerability_findings = check_nodes(
        neo4j_session,
        "OrcaVulnerabilityFinding",
        ["id", "organization_id", "target_orca_asset_unique_id"],
    )
    assert len(vulnerability_findings) == 2
    assert {
        (organization_id, target_id)
        for _, organization_id, target_id in vulnerability_findings
    } == {
        (ORGANIZATION_ID, ASSET_UNIQUE_ID_1),
        (OTHER_ORGANIZATION_ID, ASSET_UNIQUE_ID_1),
    }
    assert len({finding_id for finding_id, _, _ in vulnerability_findings}) == 2
    assert check_rels(
        neo4j_session,
        "OrcaOrganization",
        "id",
        "OrcaVulnerabilityFinding",
        "organization_id",
        "RESOURCE",
    ) == {
        (ORGANIZATION_ID, ORGANIZATION_ID),
        (OTHER_ORGANIZATION_ID, OTHER_ORGANIZATION_ID),
    }


def test_cve_metadata_enriches_orca_vulnerability_finding(
    neo4j_session,
    mocker,
):
    # Arrange
    _patch_orca_api(mocker)
    cartography.intel.orca.start_orca_ingestion(neo4j_session, _config())

    # Act
    cartography.intel.cve_metadata.load_cve_metadata_feed(
        neo4j_session,
        TEST_UPDATE_TAG,
        {"nvd"},
    )
    cartography.intel.cve_metadata.load_cve_metadata(
        neo4j_session,
        [{"id": CVE_ID_1, "description_en": "Synthetic NVD metadata"}],
        TEST_UPDATE_TAG,
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "CVEMetadata",
        "id",
        "OrcaVulnerabilityFinding",
        "cve_id",
        "ENRICHES",
    ) == {(CVE_ID_1, CVE_ID_1)}


def test_complete_sync_cleans_stale_findings_and_retargets_alert_context(
    neo4j_session,
    mocker,
):
    # Arrange
    state, _ = _patch_orca_api(mocker)
    cartography.intel.orca.start_orca_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )
    retargeted_alert = deepcopy(ALERTS[0])
    retargeted_alert["Inventory"] = _second_target_inventory()
    state["Alert"] = [retargeted_alert]
    state["VulnerabilityV2"] = []

    # Act
    cartography.intel.orca.start_orca_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG + 1),
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "OrcaAlert",
        [
            "id",
            "target_orca_inventory_id",
            "target_orca_asset_unique_id",
            "target_provider_id",
            "target_arn",
            "target_cloud_provider",
            "target_cloud_account_id",
            "target_region",
            "target_name",
            "target_type",
        ],
    ) == {
        (
            f"orca:{ORGANIZATION_ID}:{ALERT_ID_1}",
            INVENTORY_ID_2,
            ASSET_UNIQUE_ID_2,
            PROVIDER_ID_2,
            None,
            "azure",
            "subscription-1",
            "westus2",
            "synthetic-storage",
            "AzureStorageAccount",
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "OrcaVulnerabilityFinding",
            ["id"],
        )
        == set()
    )
    assert check_rels(
        neo4j_session,
        "OrcaOrganization",
        "id",
        "OrcaAlert",
        "orca_id",
        "RESOURCE",
    ) == {(ORGANIZATION_ID, ALERT_ID_1)}
    assert _affects_count(neo4j_session) == 0
    metadata = neo4j_session.run(
        """
        MATCH (n:ModuleSyncMetadata {id: $id})
        RETURN n.lastupdated AS lastupdated
        """,
        id=_sync_metadata_id(ORGANIZATION_ID),
    ).single()
    assert metadata["lastupdated"] == TEST_UPDATE_TAG + 1


def test_vulnerability_target_change_replaces_the_occurrence(
    neo4j_session,
    mocker,
):
    # Arrange
    state, _ = _patch_orca_api(mocker)
    cartography.intel.orca.start_orca_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )
    old_ids = {
        row[0]
        for row in check_nodes(
            neo4j_session,
            "OrcaVulnerabilityFinding",
            ["id"],
        )
    }
    retargeted_vulnerability = deepcopy(VULNERABILITIES[0])
    retargeted_vulnerability["Inventory"] = _second_target_inventory()
    state["VulnerabilityV2"] = [retargeted_vulnerability]

    # Act
    cartography.intel.orca.start_orca_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG + 1),
    )

    # Assert
    current_findings = check_nodes(
        neo4j_session,
        "OrcaVulnerabilityFinding",
        [
            "id",
            "target_orca_inventory_id",
            "target_orca_asset_unique_id",
            "target_provider_id",
            "target_cloud_provider",
        ],
    )
    assert len(current_findings) == 1
    new_id, inventory_id, target_id, provider_id, cloud_provider = next(
        iter(current_findings),
    )
    assert new_id not in old_ids
    assert (inventory_id, target_id, provider_id, cloud_provider) == (
        INVENTORY_ID_2,
        ASSET_UNIQUE_ID_2,
        PROVIDER_ID_2,
        "azure",
    )
    assert check_rels(
        neo4j_session,
        "OrcaOrganization",
        "id",
        "OrcaVulnerabilityFinding",
        "id",
        "RESOURCE",
    ) == {(ORGANIZATION_ID, new_id)}
    assert _affects_count(neo4j_session) == 0


def test_failed_second_sync_preserves_last_known_good_findings(
    neo4j_session,
    mocker,
):
    # Arrange
    state, query_mock = _patch_orca_api(mocker)
    cartography.intel.orca.start_orca_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )
    original_alerts = check_nodes(neo4j_session, "OrcaAlert", ["id"])
    original_vulnerabilities = check_nodes(
        neo4j_session,
        "OrcaVulnerabilityFinding",
        ["id"],
    )
    original_resource_edges = _resource_edges(neo4j_session)

    state["Alert"] = []
    second_vulnerability = deepcopy(VULNERABILITIES[0])
    second_vulnerability["Inventory"] = _second_target_inventory()
    state["VulnerabilityV2"] = [
        deepcopy(VULNERABILITIES[0]),
        second_vulnerability,
    ]
    mocker.patch("cartography.intel.orca.vulnerabilities.PAGE_SIZE", 1)
    original_query = query_mock.side_effect

    def fail_on_second_vulnerability_page(session, api_endpoint, payload):
        if (
            payload["query"]["models"] == ["VulnerabilityV2"]
            and payload["start_at_index"] == 1
        ):
            raise requests.HTTPError("synthetic vulnerability page failure")
        return original_query(session, api_endpoint, payload)

    query_mock.side_effect = fail_on_second_vulnerability_page

    # Act and assert
    with pytest.raises(
        requests.HTTPError,
        match="synthetic vulnerability page failure",
    ):
        cartography.intel.orca.start_orca_ingestion(
            neo4j_session,
            _config(TEST_UPDATE_TAG + 1),
        )

    # Assert
    assert check_nodes(neo4j_session, "OrcaAlert", ["id"]) == original_alerts
    assert (
        check_nodes(
            neo4j_session,
            "OrcaVulnerabilityFinding",
            ["id"],
        )
        == original_vulnerabilities
    )
    assert _resource_edges(neo4j_session) == original_resource_edges
    assert _affects_count(neo4j_session) == 0
    metadata = neo4j_session.run(
        """
        MATCH (n:ModuleSyncMetadata {id: $id})
        RETURN n.lastupdated AS lastupdated
        """,
        id=_sync_metadata_id(ORGANIZATION_ID),
    ).single()
    assert metadata["lastupdated"] == TEST_UPDATE_TAG


def test_identical_sync_is_idempotent_with_exact_counts(neo4j_session, mocker):
    # Arrange
    _patch_orca_api(mocker)

    # Act
    cartography.intel.orca.start_orca_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )
    cartography.intel.orca.start_orca_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG + 1),
    )

    # Assert
    node_counts = {}
    for label in (
        "OrcaOrganization",
        "OrcaAlert",
        "OrcaVulnerabilityFinding",
        "OrcaAsset",
    ):
        node_counts[label] = neo4j_session.run(
            f"MATCH (n:{label}) RETURN count(n) AS count",
        ).single()["count"]
    assert node_counts == {
        "OrcaOrganization": 1,
        "OrcaAlert": 2,
        "OrcaVulnerabilityFinding": 1,
        "OrcaAsset": 0,
    }
    resource_count = neo4j_session.run(
        """
        MATCH (:OrcaOrganization)-[r:RESOURCE]->(finding)
        WHERE finding:OrcaAlert OR finding:OrcaVulnerabilityFinding
        RETURN count(r) AS count
        """,
    ).single()["count"]
    assert resource_count == 3
    assert len(_resource_edges(neo4j_session)) == resource_count
    assert _affects_count(neo4j_session) == 0
    metadata_count = neo4j_session.run(
        """
        MATCH (n:ModuleSyncMetadata {id: $id})
        RETURN count(n) AS count
        """,
        id=_sync_metadata_id(ORGANIZATION_ID),
    ).single()["count"]
    assert metadata_count == 1
