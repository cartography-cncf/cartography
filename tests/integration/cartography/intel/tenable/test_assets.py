import cartography.intel.tenable.assets
from tests.data.tenable.assets import ASSET_ID_1
from tests.data.tenable.assets import ASSET_ID_2
from tests.data.tenable.assets import ASSETS_DATA
from tests.data.tenable.assets import AWS_EC2_INSTANCE_ID_1
from tests.data.tenable.assets import AZURE_VM_ID_2
from tests.data.tenable.assets import NETWORK_ID
from tests.data.tenable.assets import TAG_ID_1
from tests.data.tenable.assets import TENABLE_TENANT_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://cloud.tenable.com"

SOURCE_ID_1 = f"{ASSET_ID_1}::NESSUS_AGENT"
SOURCE_ID_2 = f"{ASSET_ID_2}::NESSUS_SCAN"


def _sync_assets(neo4j_session, mocker, data=None):
    """Helper: run assets sync with optional custom data."""
    mocker.patch(
        "cartography.intel.tenable.assets.export_and_download",
        return_value=data if data is not None else ASSETS_DATA,
    )
    cartography.intel.tenable.assets.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        TENABLE_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENABLE_TENANT_ID": TENABLE_TENANT_ID},
    )


def test_sync_assets(neo4j_session, mocker):
    """Test that asset sync correctly creates TenableAsset nodes and relationships."""
    mocker.patch(
        "cartography.intel.tenable.assets.export_and_download",
        return_value=ASSETS_DATA,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENABLE_TENANT_ID": TENABLE_TENANT_ID,
    }

    cartography.intel.tenable.assets.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        TENABLE_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Verify tenant node exists
    tenant_nodes = check_nodes(neo4j_session, "TenableTenant", ["id"])
    assert (TENABLE_TENANT_ID,) in tenant_nodes

    # Verify asset nodes (cloud detail fields are on sub-nodes, not here)
    actual_nodes = check_nodes(
        neo4j_session,
        "TenableAsset",
        [
            "id",
            "has_agent",
            "is_public",
            "aws_ec2_instance_id",
            "azure_vm_id",
            "gcp_instance_id",
            "is_licensed",
            "acr_score",
            "aes_score",
            "serial_number",
            "fqdn",
        ],
    )
    expected_nodes = {
        (
            ASSET_ID_1,
            True,
            False,
            AWS_EC2_INSTANCE_ID_1,
            None,
            None,
            True,
            5,
            600,
            None,
            "server1.example.com",
        ),
        (
            ASSET_ID_2,
            False,
            True,
            None,
            AZURE_VM_ID_2,
            None,
            True,
            7,
            800,
            "ABCDEFG",
            "server2.example.com",
        ),
    }
    assert actual_nodes == expected_nodes

    # Verify RESOURCE relationships from TenableTenant to TenableAsset
    actual_rels = check_rels(
        neo4j_session,
        "TenableTenant",
        "id",
        "TenableAsset",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    )
    assert actual_rels == {
        (TENABLE_TENANT_ID, ASSET_ID_1),
        (TENABLE_TENANT_ID, ASSET_ID_2),
    }


def test_sync_networks(neo4j_session, mocker):
    """Test that TenableNetwork nodes are created and linked to assets."""
    mocker.patch(
        "cartography.intel.tenable.assets.export_and_download",
        return_value=ASSETS_DATA,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENABLE_TENANT_ID": TENABLE_TENANT_ID,
    }

    cartography.intel.tenable.assets.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        TENABLE_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Both assets share the same network; only one node should exist
    actual_networks = check_nodes(neo4j_session, "TenableNetwork", ["id", "name"])
    assert actual_networks == {(NETWORK_ID, "Default")}

    actual_rels = check_rels(
        neo4j_session,
        "TenableAsset",
        "id",
        "TenableNetwork",
        "id",
        "MEMBER_OF_NETWORK",
        rel_direction_right=True,
    )
    assert actual_rels == {
        (ASSET_ID_1, NETWORK_ID),
        (ASSET_ID_2, NETWORK_ID),
    }


def test_sync_aws_cloud(neo4j_session, mocker):
    """Test that TenableAssetAWS nodes are created and linked to assets."""
    mocker.patch(
        "cartography.intel.tenable.assets.export_and_download",
        return_value=ASSETS_DATA,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENABLE_TENANT_ID": TENABLE_TENANT_ID,
    }

    cartography.intel.tenable.assets.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        TENABLE_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    actual_aws = check_nodes(
        neo4j_session,
        "TenableAssetAWS",
        ["id", "region", "ec2_instance_type", "vpc_id"],
    )
    assert actual_aws == {
        (AWS_EC2_INSTANCE_ID_1, "us-east-1", "t3.medium", "vpc-12345678"),
    }

    actual_rels = check_rels(
        neo4j_session,
        "TenableAsset",
        "id",
        "TenableAssetAWS",
        "id",
        "HAS_AWS_INFO",
        rel_direction_right=True,
    )
    assert actual_rels == {(ASSET_ID_1, AWS_EC2_INSTANCE_ID_1)}


def test_sync_azure_cloud(neo4j_session, mocker):
    """Test that TenableAssetAzure nodes are created and linked to assets."""
    mocker.patch(
        "cartography.intel.tenable.assets.export_and_download",
        return_value=ASSETS_DATA,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENABLE_TENANT_ID": TENABLE_TENANT_ID,
    }

    cartography.intel.tenable.assets.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        TENABLE_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    actual_azure = check_nodes(
        neo4j_session, "TenableAssetAzure", ["id", "resource_id"]
    )
    assert actual_azure == {
        (
            AZURE_VM_ID_2,
            "/subscriptions/sub-123/resourceGroups/rg-prod/providers/Microsoft.Compute/virtualMachines/test-vm",
        )
    }

    actual_rels = check_rels(
        neo4j_session,
        "TenableAsset",
        "id",
        "TenableAssetAzure",
        "id",
        "HAS_AZURE_INFO",
        rel_direction_right=True,
    )
    assert actual_rels == {(ASSET_ID_2, AZURE_VM_ID_2)}


def test_sync_sources(neo4j_session, mocker):
    """Test that TenableAssetSource nodes are created and linked to assets."""
    mocker.patch(
        "cartography.intel.tenable.assets.export_and_download",
        return_value=ASSETS_DATA,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENABLE_TENANT_ID": TENABLE_TENANT_ID,
    }

    cartography.intel.tenable.assets.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        TENABLE_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    actual_sources = check_nodes(neo4j_session, "TenableAssetSource", ["id", "name"])
    assert actual_sources == {
        (SOURCE_ID_1, "NESSUS_AGENT"),
        (SOURCE_ID_2, "NESSUS_SCAN"),
    }

    actual_rels = check_rels(
        neo4j_session,
        "TenableAsset",
        "id",
        "TenableAssetSource",
        "id",
        "HAS_SOURCE",
        rel_direction_right=True,
    )
    assert actual_rels == {
        (ASSET_ID_1, SOURCE_ID_1),
        (ASSET_ID_2, SOURCE_ID_2),
    }


def test_sync_tags(neo4j_session, mocker):
    """Test that TenableAssetTag nodes are created and linked to assets."""
    mocker.patch(
        "cartography.intel.tenable.assets.export_and_download",
        return_value=ASSETS_DATA,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENABLE_TENANT_ID": TENABLE_TENANT_ID,
    }

    cartography.intel.tenable.assets.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        TENABLE_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    actual_tags = check_nodes(
        neo4j_session, "TenableAssetTag", ["id", "tag_key", "tag_value"]
    )
    assert actual_tags == {(TAG_ID_1, "Environment", "Production")}

    actual_rels = check_rels(
        neo4j_session,
        "TenableAsset",
        "id",
        "TenableAssetTag",
        "id",
        "HAS_TAG",
        rel_direction_right=True,
    )
    assert actual_rels == {(ASSET_ID_1, TAG_ID_1)}


def test_sync_assets_empty_response(neo4j_session, mocker):
    """Test that asset sync handles an empty export gracefully."""
    neo4j_session.run(
        """
        MATCH (n)
        WHERE n:TenableAsset OR n:TenableNetwork
           OR n:TenableAssetSource OR n:TenableAssetTag
           OR n:TenableAssetAWS OR n:TenableAssetAzure OR n:TenableAssetGCP
        DETACH DELETE n
        """
    )

    mocker.patch(
        "cartography.intel.tenable.assets.export_and_download",
        return_value=[],
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENABLE_TENANT_ID": TENABLE_TENANT_ID,
    }

    cartography.intel.tenable.assets.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        TENABLE_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    assert check_nodes(neo4j_session, "TenableAsset", ["id"]) == set()
    assert check_nodes(neo4j_session, "TenableNetwork", ["id"]) == set()
    assert check_nodes(neo4j_session, "TenableAssetSource", ["id"]) == set()
    assert check_nodes(neo4j_session, "TenableAssetTag", ["id"]) == set()
    assert check_nodes(neo4j_session, "TenableAssetAWS", ["id"]) == set()
    assert check_nodes(neo4j_session, "TenableAssetAzure", ["id"]) == set()
    assert check_nodes(neo4j_session, "TenableAssetGCP", ["id"]) == set()


def test_sync_assets_cleanup(neo4j_session, mocker):
    """Test that stale TenableAsset nodes are deleted after sync."""
    old_update_tag = TEST_UPDATE_TAG - 1000
    neo4j_session.run(
        """
        CREATE (t:TenableTenant {id: $tenant_id, lastupdated: $update_tag})
        CREATE (a:TenableAsset {id: 'stale-asset-id', lastupdated: $old_tag})
        CREATE (t)-[:RESOURCE]->(a)
        """,
        tenant_id=TENABLE_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
        old_tag=old_update_tag,
    )

    mocker.patch(
        "cartography.intel.tenable.assets.export_and_download",
        return_value=[ASSETS_DATA[0]],
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENABLE_TENANT_ID": TENABLE_TENANT_ID,
    }

    cartography.intel.tenable.assets.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        TENABLE_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    result = neo4j_session.run("MATCH (a:TenableAsset) RETURN a.id AS id")
    existing_ids = {r["id"] for r in result}
    assert "stale-asset-id" not in existing_ids
    assert ASSET_ID_1 in existing_ids


def test_sync_networks_cleanup(neo4j_session, mocker):
    """Test that stale TenableNetwork nodes are deleted after sync."""
    old_update_tag = TEST_UPDATE_TAG - 1000
    neo4j_session.run(
        """
        CREATE (t:TenableTenant {id: $tenant_id, lastupdated: $update_tag})
        CREATE (n:TenableNetwork {id: 'stale-network-id', lastupdated: $old_tag})
        CREATE (t)-[:RESOURCE]->(n)
        """,
        tenant_id=TENABLE_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
        old_tag=old_update_tag,
    )

    _sync_assets(neo4j_session, mocker)

    result = neo4j_session.run("MATCH (n:TenableNetwork) RETURN n.id AS id")
    existing_ids = {r["id"] for r in result}
    assert "stale-network-id" not in existing_ids
    assert NETWORK_ID in existing_ids


def test_sync_sources_cleanup(neo4j_session, mocker):
    """Test that stale TenableAssetSource nodes are deleted after sync."""
    old_update_tag = TEST_UPDATE_TAG - 1000
    neo4j_session.run(
        """
        CREATE (t:TenableTenant {id: $tenant_id, lastupdated: $update_tag})
        CREATE (s:TenableAssetSource {id: 'stale-source-id', lastupdated: $old_tag})
        CREATE (t)-[:RESOURCE]->(s)
        """,
        tenant_id=TENABLE_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
        old_tag=old_update_tag,
    )

    _sync_assets(neo4j_session, mocker)

    result = neo4j_session.run("MATCH (s:TenableAssetSource) RETURN s.id AS id")
    existing_ids = {r["id"] for r in result}
    assert "stale-source-id" not in existing_ids
    assert SOURCE_ID_1 in existing_ids
    assert SOURCE_ID_2 in existing_ids


def test_sync_tags_cleanup(neo4j_session, mocker):
    """Test that stale TenableAssetTag nodes are deleted after sync."""
    old_update_tag = TEST_UPDATE_TAG - 1000
    neo4j_session.run(
        """
        CREATE (t:TenableTenant {id: $tenant_id, lastupdated: $update_tag})
        CREATE (tag:TenableAssetTag {id: 'stale-tag-id', lastupdated: $old_tag})
        CREATE (t)-[:RESOURCE]->(tag)
        """,
        tenant_id=TENABLE_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
        old_tag=old_update_tag,
    )

    _sync_assets(neo4j_session, mocker)

    result = neo4j_session.run("MATCH (tag:TenableAssetTag) RETURN tag.id AS id")
    existing_ids = {r["id"] for r in result}
    assert "stale-tag-id" not in existing_ids
    assert TAG_ID_1 in existing_ids


def test_sync_aws_cleanup(neo4j_session, mocker):
    """Test that stale TenableAssetAWS nodes are deleted after sync."""
    old_update_tag = TEST_UPDATE_TAG - 1000
    neo4j_session.run(
        """
        CREATE (t:TenableTenant {id: $tenant_id, lastupdated: $update_tag})
        CREATE (a:TenableAssetAWS {id: 'stale-aws-id', lastupdated: $old_tag})
        CREATE (t)-[:RESOURCE]->(a)
        """,
        tenant_id=TENABLE_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
        old_tag=old_update_tag,
    )

    _sync_assets(neo4j_session, mocker)

    result = neo4j_session.run("MATCH (a:TenableAssetAWS) RETURN a.id AS id")
    existing_ids = {r["id"] for r in result}
    assert "stale-aws-id" not in existing_ids
    assert AWS_EC2_INSTANCE_ID_1 in existing_ids


def test_sync_azure_cleanup(neo4j_session, mocker):
    """Test that stale TenableAssetAzure nodes are deleted after sync."""
    old_update_tag = TEST_UPDATE_TAG - 1000
    neo4j_session.run(
        """
        CREATE (t:TenableTenant {id: $tenant_id, lastupdated: $update_tag})
        CREATE (a:TenableAssetAzure {id: 'stale-azure-id', lastupdated: $old_tag})
        CREATE (t)-[:RESOURCE]->(a)
        """,
        tenant_id=TENABLE_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
        old_tag=old_update_tag,
    )

    _sync_assets(neo4j_session, mocker)

    result = neo4j_session.run("MATCH (a:TenableAssetAzure) RETURN a.id AS id")
    existing_ids = {r["id"] for r in result}
    assert "stale-azure-id" not in existing_ids
    assert AZURE_VM_ID_2 in existing_ids


def test_sync_gcp_cleanup(neo4j_session, mocker):
    """Test that stale TenableAssetGCP nodes are deleted after sync."""
    old_update_tag = TEST_UPDATE_TAG - 1000
    neo4j_session.run(
        """
        CREATE (t:TenableTenant {id: $tenant_id, lastupdated: $update_tag})
        CREATE (g:TenableAssetGCP {id: 'stale-gcp-id', lastupdated: $old_tag})
        CREATE (t)-[:RESOURCE]->(g)
        """,
        tenant_id=TENABLE_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
        old_tag=old_update_tag,
    )

    # ASSETS_DATA has no GCP assets; the stale node must still be removed
    _sync_assets(neo4j_session, mocker)

    result = neo4j_session.run("MATCH (g:TenableAssetGCP) RETURN g.id AS id")
    existing_ids = {r["id"] for r in result}
    assert "stale-gcp-id" not in existing_ids
