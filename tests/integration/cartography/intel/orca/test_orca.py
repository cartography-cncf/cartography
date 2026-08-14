from copy import deepcopy
from typing import Any

import pytest
import requests

import cartography.intel.cve_metadata
import cartography.intel.orca
from cartography.config import Config
from cartography.intel.orca.assets import load_assets
from cartography.intel.orca.assets import transform as transform_assets
from cartography.intel.orca.organization import load_organization
from tests.data.orca import ALERT_ID_1
from tests.data.orca import ALERTS
from tests.data.orca import API_ENDPOINT
from tests.data.orca import API_TOKEN
from tests.data.orca import ASSET_ID_1
from tests.data.orca import ASSET_ID_2
from tests.data.orca import ASSETS
from tests.data.orca import CVE_ID_1
from tests.data.orca import INVENTORY_ID_2
from tests.data.orca import ORGANIZATION
from tests.data.orca import ORGANIZATION_ID
from tests.data.orca import VULNERABILITIES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
SYNC_METADATA_ID = f"OrcaOrganization_{ORGANIZATION_ID}_OrcaData"


@pytest.fixture(autouse=True)
def cleanup_orca_test_data(neo4j_session):
    # Arrange
    neo4j_session.run(
        """
        MATCH (n)
        WHERE n:OrcaOrganization
           OR n:OrcaAsset
           OR n:OrcaAlert
           OR n:OrcaVulnerability
        DETACH DELETE n
        """,
    )
    neo4j_session.run(
        "MATCH (n:CVEMetadata {id: $cve_id}) DETACH DELETE n",
        cve_id=CVE_ID_1,
    )
    neo4j_session.run(
        "MATCH (n:CVEMetadataFeed {id: 'CVE_METADATA'}) DETACH DELETE n",
    )
    neo4j_session.run(
        "MATCH (n:ModuleSyncMetadata {id: $id}) DETACH DELETE n",
        id=SYNC_METADATA_ID,
    )

    yield

    # Assert/teardown
    neo4j_session.run(
        """
        MATCH (n)
        WHERE n:OrcaOrganization
           OR n:OrcaAsset
           OR n:OrcaAlert
           OR n:OrcaVulnerability
        DETACH DELETE n
        """,
    )
    neo4j_session.run(
        "MATCH (n:CVEMetadata {id: $cve_id}) DETACH DELETE n",
        cve_id=CVE_ID_1,
    )
    neo4j_session.run(
        "MATCH (n:CVEMetadataFeed {id: 'CVE_METADATA'}) DETACH DELETE n",
    )
    neo4j_session.run(
        "MATCH (n:ModuleSyncMetadata {id: $id}) DETACH DELETE n",
        id=SYNC_METADATA_ID,
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
    assets: list[dict[str, Any]] | None = None,
    alerts: list[dict[str, Any]] | None = None,
    vulnerabilities: list[dict[str, Any]] | None = None,
):
    datasets = {
        "Inventory": deepcopy(ASSETS if assets is None else assets),
        "Alert": deepcopy(ALERTS if alerts is None else alerts),
        "VulnerabilityV2": deepcopy(
            VULNERABILITIES if vulnerabilities is None else vulnerabilities,
        ),
    }
    mocker.patch(
        "cartography.intel.orca.api.get_organization",
        return_value=deepcopy(ORGANIZATION),
    )

    def query(_session, _api_endpoint, payload):
        model = payload["query"]["models"][0]
        rows = datasets[model]
        return {"data": deepcopy(rows), "total_items": len(rows)}

    mocker.patch(
        "cartography.intel.orca.api.serving_layer_query",
        side_effect=query,
    )
    return datasets


def test_start_orca_ingestion_loads_traversable_ontology_graph(
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
    assert check_nodes(
        neo4j_session,
        "OrcaAsset",
        ["id", "orca_id", "cloud_provider", "provider_id"],
    ) == {
        (ASSET_ID_1, ASSETS[0]["id"], "aws", "i-00000000000000001"),
        (ASSET_ID_2, ASSETS[1]["id"], "azure", "storage-account-1"),
    }
    assert check_nodes(
        neo4j_session,
        "SecurityIssue",
        ["orca_id", "_ont_title", "_ont_severity", "_ont_status", "_ont_source"],
    ) == {
        (ALERT_ID_1, "Internet-facing compute asset", "high", "open", "orca"),
        (
            "orca-alert-without-inventory",
            "Deleted asset retained for investigation",
            "low",
            "ignored",
            "orca",
        ),
    }
    assert check_nodes(
        neo4j_session,
        "OrcaVulnerability",
        ["cve_id", "_ont_cve_id", "_ont_base_severity", "_ont_source"],
    ) == {(CVE_ID_1, CVE_ID_1, "critical", "orca")}

    assert check_rels(
        neo4j_session,
        "OrcaOrganization",
        "id",
        "OrcaAsset",
        "id",
        "RESOURCE",
    ) == {(ORGANIZATION_ID, ASSET_ID_1), (ORGANIZATION_ID, ASSET_ID_2)}
    assert check_rels(
        neo4j_session,
        "OrcaOrganization",
        "id",
        "OrcaAlert",
        "orca_id",
        "RESOURCE",
    ) == {
        (ORGANIZATION_ID, ALERT_ID_1),
        (ORGANIZATION_ID, "orca-alert-without-inventory"),
    }
    assert check_rels(
        neo4j_session,
        "OrcaAlert",
        "orca_id",
        "OrcaAsset",
        "id",
        "AFFECTS",
    ) == {(ALERT_ID_1, ASSET_ID_1)}
    assert check_rels(
        neo4j_session,
        "OrcaVulnerability",
        "cve_id",
        "OrcaAsset",
        "id",
        "AFFECTS",
    ) == {(CVE_ID_1, ASSET_ID_1)}


def test_vulnerability_affects_is_scoped_by_organization(neo4j_session, mocker):
    # Arrange
    other_organization_id = "other-orca-organization"
    other_organization = {
        "id": other_organization_id,
        "name": "Other synthetic Orca organization",
        "api_url": API_ENDPOINT,
    }
    stale_update_tag = TEST_UPDATE_TAG - 1
    other_asset = transform_assets([ASSETS[0]], other_organization_id)
    load_organization(neo4j_session, other_organization, stale_update_tag)
    load_assets(
        neo4j_session,
        other_asset,
        other_organization_id,
        stale_update_tag,
    )
    _patch_orca_api(mocker)

    # Act
    cartography.intel.orca.start_orca_ingestion(neo4j_session, _config())

    # Assert
    assert check_rels(
        neo4j_session,
        "OrcaVulnerability",
        "cve_id",
        "OrcaAsset",
        "id",
        "AFFECTS",
    ) == {(CVE_ID_1, ASSET_ID_1)}
    assert check_nodes(
        neo4j_session,
        "OrcaAsset",
        ["id", "asset_unique_id", "organization_id"],
    ) == {
        (ASSET_ID_1, "asset-unique-1", ORGANIZATION_ID),
        (ASSET_ID_2, "asset-unique-2", ORGANIZATION_ID),
        (
            f"orca:{other_organization_id}:{ASSETS[0]['id']}",
            "asset-unique-1",
            other_organization_id,
        ),
    }


def test_cve_metadata_enriches_orca_vulnerability(neo4j_session, mocker):
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
        "OrcaVulnerability",
        "cve_id",
        "ENRICHES",
    ) == {(CVE_ID_1, CVE_ID_1)}


def test_complete_second_sync_removes_stale_orca_data(neo4j_session, mocker):
    # Arrange
    datasets = _patch_orca_api(mocker)
    cartography.intel.orca.start_orca_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )
    datasets["Inventory"] = deepcopy([ASSETS[1]])
    datasets["Alert"] = []
    datasets["VulnerabilityV2"] = []

    # Act
    cartography.intel.orca.start_orca_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG + 1),
    )

    # Assert
    assert check_nodes(neo4j_session, "OrcaAsset", ["id"]) == {(ASSET_ID_2,)}
    assert check_nodes(neo4j_session, "OrcaAlert", ["id"]) == set()
    assert check_nodes(neo4j_session, "OrcaVulnerability", ["id"]) == set()
    assert check_rels(
        neo4j_session,
        "OrcaOrganization",
        "id",
        "OrcaAsset",
        "id",
        "RESOURCE",
    ) == {(ORGANIZATION_ID, ASSET_ID_2)}
    assert (
        check_rels(
            neo4j_session,
            "OrcaOrganization",
            "id",
            "OrcaAlert",
            "id",
            "RESOURCE",
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "OrcaOrganization",
            "id",
            "OrcaVulnerability",
            "id",
            "RESOURCE",
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "OrcaAlert",
            "id",
            "OrcaAsset",
            "id",
            "AFFECTS",
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "OrcaVulnerability",
            "id",
            "OrcaAsset",
            "id",
            "AFFECTS",
        )
        == set()
    )


def test_failed_second_sync_preserves_last_known_good_data(neo4j_session, mocker):
    # Arrange
    datasets = _patch_orca_api(mocker)
    query = cartography.intel.orca.api.serving_layer_query
    original_query = query.side_effect
    cartography.intel.orca.start_orca_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )
    datasets["Inventory"] = []
    datasets["Alert"] = []
    mocker.patch("cartography.intel.orca.vulnerabilities.PAGE_SIZE", 1)

    def fail_on_second_vulnerability_page(session, api_endpoint, payload):
        if payload["query"]["models"] == ["VulnerabilityV2"]:
            if payload["start_at_index"] == 1:
                raise requests.HTTPError("synthetic vulnerability page failure")
            return {
                "data": deepcopy(VULNERABILITIES),
                "total_items": 2,
            }
        return original_query(session, api_endpoint, payload)

    query.side_effect = fail_on_second_vulnerability_page

    # Act
    with pytest.raises(
        requests.HTTPError, match="synthetic vulnerability page failure"
    ):
        cartography.intel.orca.start_orca_ingestion(
            neo4j_session,
            _config(TEST_UPDATE_TAG + 1),
        )

    # Assert
    assert check_nodes(neo4j_session, "OrcaAsset", ["id"]) == {
        (ASSET_ID_1,),
        (ASSET_ID_2,),
    }
    assert len(check_nodes(neo4j_session, "OrcaAlert", ["id"])) == 2
    assert check_nodes(neo4j_session, "OrcaVulnerability", ["cve_id"]) == {
        (CVE_ID_1,),
    }
    assert check_rels(
        neo4j_session,
        "OrcaOrganization",
        "id",
        "OrcaAsset",
        "id",
        "RESOURCE",
    ) == {(ORGANIZATION_ID, ASSET_ID_1), (ORGANIZATION_ID, ASSET_ID_2)}
    assert check_rels(
        neo4j_session,
        "OrcaAlert",
        "orca_id",
        "OrcaAsset",
        "id",
        "AFFECTS",
    ) == {(ALERT_ID_1, ASSET_ID_1)}
    assert check_rels(
        neo4j_session,
        "OrcaVulnerability",
        "cve_id",
        "OrcaAsset",
        "id",
        "AFFECTS",
    ) == {(CVE_ID_1, ASSET_ID_1)}
    preserved_edge_tags = neo4j_session.run(
        """
        MATCH (finding)-[affects:AFFECTS]->(asset:OrcaAsset)
        WHERE finding.organization_id = $organization_id
          AND asset.organization_id = $organization_id
        RETURN collect(DISTINCT affects.lastupdated) AS update_tags
        """,
        organization_id=ORGANIZATION_ID,
    ).single()
    assert preserved_edge_tags["update_tags"] == [TEST_UPDATE_TAG]
    metadata = neo4j_session.run(
        """
        MATCH (n:ModuleSyncMetadata {id: $id})
        RETURN n.lastupdated AS lastupdated
        """,
        id=SYNC_METADATA_ID,
    ).single()
    assert metadata["lastupdated"] == TEST_UPDATE_TAG


def test_alert_affects_edge_retargets_and_sync_is_idempotent(
    neo4j_session,
    mocker,
):
    # Arrange
    datasets = _patch_orca_api(mocker)
    cartography.intel.orca.start_orca_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )
    retargeted_alert = deepcopy(ALERTS[0])
    retargeted_alert["Inventory"] = {"id": INVENTORY_ID_2}
    datasets["Alert"] = [retargeted_alert]
    retargeted_vulnerability = deepcopy(VULNERABILITIES[0])
    retargeted_vulnerability["Inventory"]["AssetUniqueId"] = "asset-unique-2"
    datasets["VulnerabilityV2"] = [retargeted_vulnerability]

    # Act
    cartography.intel.orca.start_orca_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG + 1),
    )
    cartography.intel.orca.start_orca_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG + 1),
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "OrcaAlert",
        "orca_id",
        "OrcaAsset",
        "id",
        "AFFECTS",
    ) == {(ALERT_ID_1, ASSET_ID_2)}
    assert check_rels(
        neo4j_session,
        "OrcaVulnerability",
        "cve_id",
        "OrcaAsset",
        "id",
        "AFFECTS",
    ) == {(CVE_ID_1, ASSET_ID_2)}
    counts = neo4j_session.run(
        """
        MATCH (o:OrcaOrganization)
        OPTIONAL MATCH (a:OrcaAsset)
        OPTIONAL MATCH (f:OrcaAlert)
        OPTIONAL MATCH (v:OrcaVulnerability)
        RETURN count(DISTINCT o) AS organizations,
               count(DISTINCT a) AS assets,
               count(DISTINCT f) AS alerts,
               count(DISTINCT v) AS vulnerabilities
        """,
    ).single()
    assert tuple(counts.values()) == (1, 2, 1, 1)
    relationship_counts = neo4j_session.run(
        """
        MATCH (:OrcaOrganization {id: $organization_id})-[resource:RESOURCE]->()
        WITH count(resource) AS resources
        MATCH (finding)-[affects:AFFECTS]->(asset:OrcaAsset)
        WHERE finding.organization_id = $organization_id
          AND asset.organization_id = $organization_id
        RETURN resources, count(affects) AS affects
        """,
        organization_id=ORGANIZATION_ID,
    ).single()
    assert tuple(relationship_counts.values()) == (4, 2)
