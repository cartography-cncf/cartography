import cartography.intel.tenable.assets
from tests.data.tenable.assets import ASSET_ID_1
from tests.data.tenable.assets import ASSET_ID_2
from tests.data.tenable.assets import ASSETS_DATA
from tests.data.tenable.assets import AWS_EC2_INSTANCE_ID_1
from tests.data.tenable.assets import AZURE_VM_ID_2
from tests.data.tenable.assets import NETWORK_ID
from tests.data.tenable.assets import SCOPED_ASSET_ID_1
from tests.data.tenable.assets import SCOPED_ASSET_ID_2
from tests.data.tenable.assets import SCOPED_AWS_EC2_INSTANCE_ID_1
from tests.data.tenable.assets import SCOPED_AZURE_VM_ID_2
from tests.data.tenable.assets import SCOPED_NETWORK_ID
from tests.data.tenable.assets import SCOPED_TAG_ID_1
from tests.data.tenable.assets import TAG_ID_1
from tests.data.tenable.assets import tenable_id
from tests.data.tenable.assets import TENABLE_TENANT_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://cloud.tenable.com"

SOURCE_ID_1 = tenable_id(f"{ASSET_ID_1}::NESSUS_AGENT")
SOURCE_ID_2 = tenable_id(f"{ASSET_ID_2}::NESSUS_SCAN")
AZURE_RESOURCE_ID_2 = (
    "/subscriptions/sub-123/resourceGroups/rg-prod/"
    "providers/Microsoft.Compute/virtualMachines/test-vm"
)
GCP_ASSET_ID = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
SCOPED_GCP_ASSET_ID = tenable_id(GCP_ASSET_ID)
GCP_INSTANCE_NAME = "gcp-test-instance"
GCP_PROJECT_ID = "tenable-test-project"
GCP_ZONE = "us-central1-a"
GCP_INSTANCE_ID = (
    f"projects/{GCP_PROJECT_ID}/zones/{GCP_ZONE}/instances/{GCP_INSTANCE_NAME}"
)


def _gcp_asset_data():
    return {
        "id": GCP_ASSET_ID,
        "cloud": {
            "gcp": {
                "instance_id": GCP_INSTANCE_NAME,
                "project_id": GCP_PROJECT_ID,
                "zone": GCP_ZONE,
            }
        },
        "sources": [],
        "tags": [],
    }


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


def _seed_native_cloud_nodes(neo4j_session):
    neo4j_session.run(
        """
        CREATE (aws:AWSAccount {id: '123456789012'})
        CREATE (other_aws:AWSAccount {id: '999999999999'})
        CREATE (ec2:EC2Instance {
            id: $aws_instance_id,
            instanceid: $aws_instance_id,
            region: 'us-east-1'
        })
        CREATE (wrong_account_ec2:EC2Instance {
            id: 'wrong-account-ec2',
            instanceid: $aws_instance_id,
            region: 'us-east-1'
        })
        CREATE (aws)-[:RESOURCE]->(ec2)
        CREATE (other_aws)-[:RESOURCE]->(wrong_account_ec2)
        CREATE (sub:AzureSubscription {id: 'sub-123'})
        CREATE (vm:AzureVirtualMachine {id: $azure_resource_id})
        CREATE (sub)-[:RESOURCE]->(vm)
        CREATE (project:GCPProject {id: $gcp_project_id})
        CREATE (gcp:GCPInstance {id: $gcp_instance_id})
        CREATE (project)-[:RESOURCE]->(gcp)
        """,
        aws_instance_id=AWS_EC2_INSTANCE_ID_1,
        azure_resource_id=AZURE_RESOURCE_ID_2,
        gcp_project_id=GCP_PROJECT_ID,
        gcp_instance_id=GCP_INSTANCE_ID,
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
            "asset_uuid",
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
            SCOPED_ASSET_ID_1,
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
            SCOPED_ASSET_ID_2,
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
        (TENABLE_TENANT_ID, SCOPED_ASSET_ID_1),
        (TENABLE_TENANT_ID, SCOPED_ASSET_ID_2),
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
    actual_networks = check_nodes(
        neo4j_session, "TenableNetwork", ["id", "network_id", "name"]
    )
    assert actual_networks == {(SCOPED_NETWORK_ID, NETWORK_ID, "Default")}

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
        (SCOPED_ASSET_ID_1, SCOPED_NETWORK_ID),
        (SCOPED_ASSET_ID_2, SCOPED_NETWORK_ID),
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
        ["id", "ec2_instance_id", "region", "ec2_instance_type", "vpc_id"],
    )
    assert actual_aws == {
        (
            SCOPED_AWS_EC2_INSTANCE_ID_1,
            AWS_EC2_INSTANCE_ID_1,
            "us-east-1",
            "t3.medium",
            "vpc-12345678",
        ),
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
    assert actual_rels == {(SCOPED_ASSET_ID_1, SCOPED_AWS_EC2_INSTANCE_ID_1)}


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
        neo4j_session, "TenableAssetAzure", ["id", "vm_id", "resource_id"]
    )
    assert actual_azure == {
        (
            SCOPED_AZURE_VM_ID_2,
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
    assert actual_rels == {(SCOPED_ASSET_ID_2, SCOPED_AZURE_VM_ID_2)}


def test_sync_native_cloud_observed_as_rels(neo4j_session, mocker):
    """Tenable assets correlate to existing native cloud compute nodes."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _seed_native_cloud_nodes(neo4j_session)

    # Act
    _sync_assets(neo4j_session, mocker, [*ASSETS_DATA, _gcp_asset_data()])

    # Assert
    aws_account_rows = neo4j_session.run(
        """
        MATCH (:TenableAsset {id: $asset_id})-[:OBSERVED_AS]->(:EC2Instance)
            <-[:RESOURCE]-(account:AWSAccount)
        RETURN collect(account.id) AS account_ids
        """,
        asset_id=SCOPED_ASSET_ID_1,
    ).single()
    assert aws_account_rows["account_ids"] == ["123456789012"]

    assert check_rels(
        neo4j_session,
        "TenableAsset",
        "id",
        "AzureVirtualMachine",
        "id",
        "OBSERVED_AS",
        rel_direction_right=True,
    ) == {(SCOPED_ASSET_ID_2, AZURE_RESOURCE_ID_2)}

    assert check_rels(
        neo4j_session,
        "TenableAsset",
        "id",
        "GCPInstance",
        "id",
        "OBSERVED_AS",
        rel_direction_right=True,
    ) == {(SCOPED_GCP_ASSET_ID, GCP_INSTANCE_ID)}


def test_sync_native_cloud_observed_as_skips_missing_native_nodes(
    neo4j_session, mocker
):
    """Tenable does not create native cloud correlation edges without a target node."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Act
    _sync_assets(neo4j_session, mocker, [*ASSETS_DATA, _gcp_asset_data()])

    # Assert
    record = neo4j_session.run(
        "MATCH (:TenableAsset)-[r:OBSERVED_AS]->() RETURN count(r) AS rel_count"
    ).single()
    assert record["rel_count"] == 0


def test_sync_native_cloud_observed_as_cleanup(neo4j_session, mocker):
    """Stale Tenable native cloud correlations are deleted after sync."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    old_update_tag = TEST_UPDATE_TAG - 1000
    neo4j_session.run(
        """
        CREATE (tenant:TenableTenant {id: $tenant_id})
        CREATE (asset:TenableAsset {id: $asset_id, lastupdated: $old_tag})
        CREATE (tenant)-[:RESOURCE]->(asset)
        CREATE (old_ec2:EC2Instance {id: 'old-ec2', instanceid: 'i-old'})
        CREATE (old_vm:AzureVirtualMachine {id: '/subscriptions/sub/old-vm'})
        CREATE (old_gcp:GCPInstance {id: 'projects/old/zones/old/instances/old'})
        CREATE (asset)-[:OBSERVED_AS {
            lastupdated: $old_tag,
            _sub_resource_label: 'TenableTenant',
            _sub_resource_id: $tenant_id
        }]->(old_ec2)
        CREATE (asset)-[:OBSERVED_AS {
            lastupdated: $old_tag,
            _sub_resource_label: 'TenableTenant',
            _sub_resource_id: $tenant_id
        }]->(old_vm)
        CREATE (asset)-[:OBSERVED_AS {
            lastupdated: $old_tag,
            _sub_resource_label: 'TenableTenant',
            _sub_resource_id: $tenant_id
        }]->(old_gcp)
        """,
        tenant_id=TENABLE_TENANT_ID,
        asset_id=SCOPED_ASSET_ID_1,
        old_tag=old_update_tag,
    )
    _seed_native_cloud_nodes(neo4j_session)

    # Act
    _sync_assets(neo4j_session, mocker, ASSETS_DATA)

    # Assert
    stale_record = neo4j_session.run(
        """
        MATCH (:TenableAsset {id: $asset_id})-[r:OBSERVED_AS]->(n)
        WHERE n.id IN [
            'old-ec2',
            '/subscriptions/sub/old-vm',
            'projects/old/zones/old/instances/old'
        ]
        RETURN count(r) AS rel_count
        """,
        asset_id=SCOPED_ASSET_ID_1,
    ).single()
    assert stale_record["rel_count"] == 0


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
        (SCOPED_ASSET_ID_1, SOURCE_ID_1),
        (SCOPED_ASSET_ID_2, SOURCE_ID_2),
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
        neo4j_session, "TenableAssetTag", ["id", "tag_uuid", "tag_key", "tag_value"]
    )
    assert actual_tags == {(SCOPED_TAG_ID_1, TAG_ID_1, "Environment", "Production")}

    actual_rels = check_rels(
        neo4j_session,
        "TenableAsset",
        "id",
        "TenableAssetTag",
        "id",
        "HAS_TAG",
        rel_direction_right=True,
    )
    assert actual_rels == {(SCOPED_ASSET_ID_1, SCOPED_TAG_ID_1)}


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
    assert SCOPED_ASSET_ID_1 in existing_ids


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
    assert SCOPED_NETWORK_ID in existing_ids


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
    assert SCOPED_TAG_ID_1 in existing_ids


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
    assert SCOPED_AWS_EC2_INSTANCE_ID_1 in existing_ids


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
    assert SCOPED_AZURE_VM_ID_2 in existing_ids


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
