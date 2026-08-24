from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.compute
import cartography.intel.gcp.iam
import tests.data.gcp.compute
from cartography.analysis.gcp.analysis import GCP_COMPUTE_INSTANCE_VPC_ANALYSIS
from cartography.util import run_typed_analysis_job
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "project-abc"

# A service account whose email matches the one attached to the instances in
# tests.data.gcp.compute.GCP_LIST_INSTANCES_RESPONSE, so that running iam.sync()
# before compute.sync() lets the RUNS_AS edge match on email.
INSTANCE_SERVICE_ACCOUNTS = [
    {
        "name": (
            "projects/project-abc/serviceAccounts/"
            "my-svc-account@developer.gserviceaccount.com"
        ),
        "projectId": "project-abc",
        "uniqueId": "111111111111111111111",
        "email": "my-svc-account@developer.gserviceaccount.com",
        "displayName": "Instance Service Account",
        "oauth2ClientId": "111111111111111111111",
        "disabled": False,
    },
]


def _create_test_project(neo4j_session, project_id: str, update_tag: int):
    """Helper to create a GCPProject node for testing."""
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id:$ProjectId})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $gcp_update_tag
        """,
        ProjectId=project_id,
        gcp_update_tag=update_tag,
    )


def _create_test_service_account(
    neo4j_session, sa_id: str, email: str, update_tag: int
):
    """Helper to create a GCPServiceAccount node for testing."""
    neo4j_session.run(
        """
        MERGE (sa:GCPServiceAccount{id:$SaId})
        ON CREATE SET sa.firstseen = timestamp()
        SET sa.email = $Email, sa.lastupdated = $gcp_update_tag
        """,
        SaId=sa_id,
        Email=email,
        gcp_update_tag=update_tag,
    )


def test_update_gcp_project_compute_metadata_preserves_existing_properties(
    neo4j_session,
):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG - 1)
    neo4j_session.run(
        """
        MATCH (p:GCPProject {id: $project_id})
        SET p.displayname = "Existing project",
            p.projectnumber = "123456"
        """,
        project_id=TEST_PROJECT_ID,
    )

    cartography.intel.gcp.compute.update_gcp_project_compute_metadata(
        neo4j_session,
        TEST_PROJECT_ID,
        {
            "commonInstanceMetadata": {
                "items": [{"key": "enable-oslogin", "value": "TRUE"}],
            },
        },
        TEST_UPDATE_TAG,
    )

    project = neo4j_session.run(
        """
        MATCH (p:GCPProject {id: $project_id})
        RETURN p.compute_project_enable_oslogin AS enable_oslogin,
               p.displayname AS displayname,
               p.projectnumber AS projectnumber,
               p.lastupdated AS lastupdated
        """,
        project_id=TEST_PROJECT_ID,
    ).single()
    assert project["enable_oslogin"] == "TRUE"
    assert project["displayname"] == "Existing project"
    assert project["projectnumber"] == "123456"
    assert project["lastupdated"] == TEST_UPDATE_TAG


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpcs",
    return_value=tests.data.gcp.compute.VPC_RESPONSE,
)
def test_sync_gcp_vpcs(mock_get_vpcs, neo4j_session):
    """Test sync_gcp_vpcs() loads VPCs and creates relationships."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Act
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - VPC nodes created with correct properties
    assert check_nodes(
        neo4j_session,
        "GCPVpc",
        ["id", "name", "project_id", "auto_create_subnetworks"],
    ) == {
        (
            "projects/project-abc/global/networks/default",
            "default",
            "project-abc",
            True,
        ),
    }

    # Assert - VirtualNetwork semantic label + normalized _ont_* fields.
    # GCP VPCs are global and keep CIDRs on subnets, so _ont_cidr/_ont_region
    # are intentionally unset.
    assert check_nodes(
        neo4j_session,
        "VirtualNetwork",
        ["_ont_name", "_ont_source"],
    ) == {
        ("default", "gcp"),
    }

    # Assert - Project to VPC relationship created
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPVpc",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("project-abc", "projects/project-abc/global/networks/default"),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_subnets",
    return_value=tests.data.gcp.compute.VPC_SUBNET_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpcs",
    return_value=tests.data.gcp.compute.VPC_RESPONSE,
)
def test_sync_gcp_subnets(mock_get_vpcs, mock_get_subnets, neo4j_session):
    """Test sync_gcp_subnets() loads subnets and creates relationships."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Pre-load VPCs so subnets can connect to them
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act
    cartography.intel.gcp.compute.sync_gcp_subnets(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        ["europe-west2"],
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Subnet nodes created with correct properties
    assert check_nodes(
        neo4j_session,
        "GCPSubnet",
        [
            "id",
            "region",
            "gateway_address",
            "ip_cidr_range",
            "private_ip_google_access",
        ],
    ) == {
        (
            "projects/project-abc/regions/europe-west2/subnetworks/default",
            "europe-west2",
            "10.0.0.1",
            "10.0.0.0/20",
            False,
        ),
    }

    # Assert - Subnet semantic label + normalized _ont_* fields
    assert check_nodes(
        neo4j_session,
        "Subnet",
        ["_ont_name", "_ont_cidr_block", "_ont_region", "_ont_source"],
    ) == {
        ("default", "10.0.0.0/20", "europe-west2", "gcp"),
    }

    # Assert - VPC to Subnet relationship created
    assert check_rels(
        neo4j_session,
        "GCPVpc",
        "id",
        "GCPSubnet",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/global/networks/default",
            "projects/project-abc/regions/europe-west2/subnetworks/default",
        ),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_instance_responses",
    return_value=[tests.data.gcp.compute.GCP_LIST_INSTANCES_RESPONSE],
)
def test_gcp_subnet_stub_not_labeled_subnet(mock_get_instances, neo4j_session):
    """Regression: GCP subnet stubs created by the instance path only know
    partial_uri, so they must NOT carry the Subnet semantic label. Otherwise
    cross-cloud (:Subnet) queries would return nameless GCP subnet nodes (no
    _ont_name/_ont_cidr_block/_ont_region) until a full subnet sync runs."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Act - sync instances only; this creates GCPSubnet stub nodes without full
    # subnet data.
    cartography.intel.gcp.compute.sync_gcp_instances(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        None,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - stub subnet nodes exist, but none carry the Subnet label.
    assert check_nodes(neo4j_session, "GCPSubnet", ["id"]) != set()
    assert check_nodes(neo4j_session, "Subnet", ["id"]) == set()


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_instance_responses",
    return_value=[tests.data.gcp.compute.GCP_LIST_INSTANCES_RESPONSE],
)
def test_sync_gcp_instances(mock_get_instances, neo4j_session):
    """Test sync_gcp_instances() loads instances and creates relationships."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    # Create project first - required for RESOURCE relationship with data model
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Act
    cartography.intel.gcp.compute.sync_gcp_instances(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        None,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Instance nodes created with correct properties
    assert check_nodes(
        neo4j_session,
        "GCPInstance",
        ["id", "instancename", "zone_name", "project_id"],
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1",
            "instance-1",
            "europe-west2-b",
            "project-abc",
        ),
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test",
            "instance-1-test",
            "europe-west2-b",
            "project-abc",
        ),
    }

    # Assert - Ontology projection fields populated from raw API payload
    assert check_nodes(
        neo4j_session,
        "GCPInstance",
        ["id", "creation_timestamp", "private_ip", "public_ip"],
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1",
            "2018-02-16T10:42:04.362-08:00",
            "10.0.0.2",
            "1.2.3.4",
        ),
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test",
            "2018-04-19T05:24:54.903-07:00",
            "10.0.0.3",
            "1.3.4.5",
        ),
    }

    # Assert - Project to Instance relationship created
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPInstance",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            "project-abc",
            "projects/project-abc/zones/europe-west2-b/instances/instance-1",
        ),
        (
            "project-abc",
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test",
        ),
    }

    # Assert - Network interface nodes created
    assert check_nodes(
        neo4j_session,
        "GCPNetworkInterface",
        ["id", "name", "private_ip"],
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1/networkinterfaces/nic0",
            "nic0",
            "10.0.0.2",
        ),
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test/networkinterfaces/nic0",
            "nic0",
            "10.0.0.3",
        ),
    }

    # Assert - Instance to NetworkInterface relationship created
    assert check_rels(
        neo4j_session,
        "GCPInstance",
        "id",
        "GCPNetworkInterface",
        "id",
        "NETWORK_INTERFACE",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1",
            "projects/project-abc/zones/europe-west2-b/instances/instance-1/networkinterfaces/nic0",
        ),
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test",
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test/networkinterfaces/nic0",
        ),
    }

    # Assert - NetworkInterface to Subnet relationship created
    assert check_rels(
        neo4j_session,
        "GCPNetworkInterface",
        "id",
        "GCPSubnet",
        "id",
        "PART_OF_SUBNET",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1/networkinterfaces/nic0",
            "projects/project-abc/regions/europe-west2/subnetworks/default",
        ),
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test/networkinterfaces/nic0",
            "projects/project-abc/regions/europe-west2/subnetworks/default",
        ),
    }

    # Assert - Access config nodes created
    assert check_nodes(
        neo4j_session,
        "GCPNicAccessConfig",
        ["id", "public_ip"],
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1/networkinterfaces/nic0/accessconfigs/ONE_TO_ONE_NAT",
            "1.2.3.4",
        ),
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test/networkinterfaces/nic0/accessconfigs/ONE_TO_ONE_NAT",
            "1.3.4.5",
        ),
    }

    # Assert - NetworkInterface to AccessConfig relationship created
    assert check_rels(
        neo4j_session,
        "GCPNetworkInterface",
        "id",
        "GCPNicAccessConfig",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1/networkinterfaces/nic0",
            "projects/project-abc/zones/europe-west2-b/instances/instance-1/networkinterfaces/nic0/accessconfigs/ONE_TO_ONE_NAT",
        ),
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test/networkinterfaces/nic0",
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test/networkinterfaces/nic0/accessconfigs/ONE_TO_ONE_NAT",
        ),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_instance_responses",
    return_value=[tests.data.gcp.compute.GCP_LIST_INSTANCES_RESPONSE],
)
def test_sync_gcp_instances_service_account(mock_get_instances, neo4j_session):
    """Test that instances expose service_account_email and link to their GCPServiceAccount."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    # Pre-load the service account the instances run as, so the RUNS_AS edge can match on email
    _create_test_service_account(
        neo4j_session,
        "my-svc-account",
        "my-svc-account@developer.gserviceaccount.com",
        TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.gcp.compute.sync_gcp_instances(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        None,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - service_account_email property is populated on the instances
    assert check_nodes(
        neo4j_session,
        "GCPInstance",
        ["id", "service_account_email"],
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1",
            "my-svc-account@developer.gserviceaccount.com",
        ),
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test",
            "my-svc-account@developer.gserviceaccount.com",
        ),
    }

    # Assert - Instance to ServiceAccount RUNS_AS relationship created
    assert check_rels(
        neo4j_session,
        "GCPInstance",
        "id",
        "GCPServiceAccount",
        "email",
        "RUNS_AS",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1",
            "my-svc-account@developer.gserviceaccount.com",
        ),
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test",
            "my-svc-account@developer.gserviceaccount.com",
        ),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_instance_responses",
    return_value=[tests.data.gcp.compute.GCP_LIST_INSTANCES_RESPONSE],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_project_custom_roles",
    return_value=[],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_service_accounts",
    return_value=INSTANCE_SERVICE_ACCOUNTS,
)
def test_iam_then_compute_creates_runs_as(
    mock_get_sa, mock_get_roles, mock_get_instances, neo4j_session
):
    """Run iam.sync() then compute.sync() in the orchestration order and confirm
    compute matches the GCPServiceAccount that iam just created (RUNS_AS edge)."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
        "ORG_RESOURCE_NAME": "organizations/123456789012",
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Act - IAM first (creates GCPServiceAccount), then Compute (creates RUNS_AS)
    cartography.intel.gcp.iam.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    cartography.intel.gcp.compute.sync_gcp_instances(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        None,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - instances are linked to the service account ingested by iam.sync
    assert check_rels(
        neo4j_session,
        "GCPInstance",
        "id",
        "GCPServiceAccount",
        "email",
        "RUNS_AS",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1",
            "my-svc-account@developer.gserviceaccount.com",
        ),
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test",
            "my-svc-account@developer.gserviceaccount.com",
        ),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_instance_responses",
    return_value=[tests.data.gcp.compute.GCP_LIST_INSTANCES_RESPONSE],
)
def test_compute_alone_creates_no_runs_as(mock_get_instances, neo4j_session):
    """Selective-sync caveat: with `--gcp-requested-syncs compute`, IAM does not
    run, so no GCPServiceAccount exists and no RUNS_AS edge is created. The
    service_account_email property is still populated on the instance."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Act - compute only, no IAM sync beforehand
    cartography.intel.gcp.compute.sync_gcp_instances(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        None,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - property populated even though IAM did not run
    assert check_nodes(
        neo4j_session,
        "GCPInstance",
        ["id", "service_account_email"],
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1",
            "my-svc-account@developer.gserviceaccount.com",
        ),
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test",
            "my-svc-account@developer.gserviceaccount.com",
        ),
    }

    # Assert - no RUNS_AS edge, since the service account node does not exist
    assert (
        check_rels(
            neo4j_session,
            "GCPInstance",
            "id",
            "GCPServiceAccount",
            "email",
            "RUNS_AS",
            rel_direction_right=True,
        )
        == set()
    )


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_instance_responses",
    return_value=[tests.data.gcp.compute.GCP_LIST_INSTANCES_RESPONSE],
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_subnets",
    return_value=tests.data.gcp.compute.VPC_SUBNET_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpcs",
    return_value=tests.data.gcp.compute.VPC_RESPONSE,
)
def test_sync_gcp_instances_with_vpc_relationship(
    mock_get_vpcs, mock_get_subnets, mock_get_instances, neo4j_session
):
    """Test that instances are connected to VPCs via MEMBER_OF_GCP_VPC relationship."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Load VPCs and subnets first
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    cartography.intel.gcp.compute.sync_gcp_subnets(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        ["europe-west2"],
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act
    cartography.intel.gcp.compute.sync_gcp_instances(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        None,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Run the analysis job to create MEMBER_OF_GCP_VPC relationships
    run_typed_analysis_job(
        GCP_COMPUTE_INSTANCE_VPC_ANALYSIS,
        neo4j_session,
        common_job_parameters,
    )

    # Assert - Instance to VPC relationship created
    assert check_rels(
        neo4j_session,
        "GCPInstance",
        "id",
        "GCPVpc",
        "id",
        "MEMBER_OF_GCP_VPC",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1",
            "projects/project-abc/global/networks/default",
        ),
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1-test",
            "projects/project-abc/global/networks/default",
        ),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_instance_responses",
    return_value=[tests.data.gcp.compute.GCP_LIST_INSTANCES_RESPONSE],
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpcs",
    return_value=tests.data.gcp.compute.VPC_RESPONSE,
)
def test_sync_gcp_instances_with_tags(mock_get_vpcs, mock_get_instances, neo4j_session):
    """Test that instances with tags create GCPNetworkTag nodes and relationships."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Pre-load VPCs so tags can connect to them
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act
    cartography.intel.gcp.compute.sync_gcp_instances(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        None,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Network tag nodes created (only instance-1 has tags)
    assert check_nodes(
        neo4j_session,
        "GCPNetworkTag",
        ["id", "value"],
    ) == {
        (
            "projects/project-abc/global/networks/default/tags/test",
            "test",
        ),
    }

    # Assert - Instance to Tag relationship created
    assert check_rels(
        neo4j_session,
        "GCPInstance",
        "id",
        "GCPNetworkTag",
        "id",
        "TAGGED",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/zones/europe-west2-b/instances/instance-1",
            "projects/project-abc/global/networks/default/tags/test",
        ),
    }

    # Assert - Tag to VPC relationship created (Tag)-[DEFINED_IN]->(VPC)
    assert check_rels(
        neo4j_session,
        "GCPNetworkTag",
        "id",
        "GCPVpc",
        "id",
        "DEFINED_IN",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/global/networks/default/tags/test",
            "projects/project-abc/global/networks/default",
        ),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_global_forwarding_rules",
    return_value=tests.data.gcp.compute.LIST_GLOBAL_FORWARDING_RULES_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_regional_forwarding_rules",
    return_value=tests.data.gcp.compute.LIST_FORWARDING_RULES_RESPONSE,
)
def test_sync_gcp_forwarding_rules(mock_get_regional, mock_get_global, neo4j_session):
    """Test sync_gcp_forwarding_rules() loads both global and regional forwarding rules."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }

    # Act
    cartography.intel.gcp.compute.sync_gcp_forwarding_rules(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        ["europe-west2"],
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Both global and regional forwarding rule nodes created
    assert check_nodes(
        neo4j_session,
        "GCPForwardingRule",
        ["id", "ip_address", "project_id", "region"],
    ) == {
        # Global rule (no region)
        (
            "projects/project-abc/global/forwardingRules/global-rule-1",
            "35.235.1.2",
            "project-abc",
            None,
        ),
        # Regional rules
        (
            "projects/project-abc/regions/europe-west2/forwardingRules/internal-service-1111",
            "10.0.0.10",
            "project-abc",
            "europe-west2",
        ),
        (
            "projects/project-abc/regions/europe-west2/forwardingRules/public-ingress-controller-1234567",
            "1.2.3.11",
            "project-abc",
            "europe-west2",
        ),
        (
            "projects/project-abc/regions/europe-west2/forwardingRules/shard-server-22222",
            "10.0.0.20",
            "project-abc",
            "europe-west2",
        ),
        (
            "projects/project-abc/regions/europe-west2/forwardingRules/internal-tcp-no-target-3333",
            "10.0.0.30",
            "project-abc",
            "europe-west2",
        ),
    }

    # Assert - lb_type derived from the target proxy / pool collection
    assert check_nodes(
        neo4j_session,
        "GCPForwardingRule",
        ["id", "lb_type"],
    ) == {
        ("projects/project-abc/global/forwardingRules/global-rule-1", "https"),
        (
            "projects/project-abc/regions/europe-west2/forwardingRules/internal-service-1111",
            "network",
        ),
        (
            "projects/project-abc/regions/europe-west2/forwardingRules/public-ingress-controller-1234567",
            "vpn",
        ),
        (
            "projects/project-abc/regions/europe-west2/forwardingRules/shard-server-22222",
            "network",
        ),
        # Backend-service-only forwarding rule (no `target`): lb_type falls back
        # to the backendService collection => "network" (L4 Network LB family).
        (
            "projects/project-abc/regions/europe-west2/forwardingRules/internal-tcp-no-target-3333",
            "network",
        ),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_global_forwarding_rules",
    return_value=tests.data.gcp.compute.LIST_GLOBAL_FORWARDING_RULES_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_regional_forwarding_rules",
    return_value=tests.data.gcp.compute.LIST_FORWARDING_RULES_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_subnets",
    return_value=tests.data.gcp.compute.VPC_SUBNET_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpcs",
    return_value=tests.data.gcp.compute.VPC_RESPONSE,
)
def test_sync_gcp_forwarding_rules_with_relationships(
    mock_get_vpcs, mock_get_subnets, mock_get_regional, mock_get_global, neo4j_session
):
    """Test forwarding rules relationships: Subnet->ForwardingRule for regional, VPC->ForwardingRule for global."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Pre-load VPCs and subnets
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    cartography.intel.gcp.compute.sync_gcp_subnets(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        ["europe-west2"],
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act
    cartography.intel.gcp.compute.sync_gcp_forwarding_rules(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        ["europe-west2"],
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Subnet to ForwardingRule relationship (for INTERNAL regional rules with subnetwork)
    assert check_rels(
        neo4j_session,
        "GCPSubnet",
        "id",
        "GCPForwardingRule",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/regions/europe-west2/subnetworks/default",
            "projects/project-abc/regions/europe-west2/forwardingRules/internal-service-1111",
        ),
        (
            "projects/project-abc/regions/europe-west2/subnetworks/default",
            "projects/project-abc/regions/europe-west2/forwardingRules/shard-server-22222",
        ),
        (
            "projects/project-abc/regions/europe-west2/subnetworks/default",
            "projects/project-abc/regions/europe-west2/forwardingRules/internal-tcp-no-target-3333",
        ),
    }

    # Assert - VPC to ForwardingRule relationship (for global rules without subnetwork)
    assert check_rels(
        neo4j_session,
        "GCPVpc",
        "id",
        "GCPForwardingRule",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/global/networks/default",
            "projects/project-abc/global/forwardingRules/global-rule-1",
        ),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_firewall_ingress_rules",
    return_value=tests.data.gcp.compute.LIST_FIREWALLS_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpcs",
    return_value=tests.data.gcp.compute.VPC_RESPONSE,
)
def test_sync_gcp_firewall_rules(mock_get_vpcs, mock_get_firewalls, neo4j_session):
    """Test sync_gcp_firewall_rules() loads firewalls and creates relationships."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Pre-load VPCs so firewalls can connect to them
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act
    cartography.intel.gcp.compute.sync_gcp_firewall_rules(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Firewall nodes created
    assert check_nodes(
        neo4j_session,
        "GCPFirewall",
        ["id", "name", "direction", "priority", "has_target_service_accounts"],
    ) == {
        (
            "projects/project-abc/global/firewalls/default-allow-icmp",
            "default-allow-icmp",
            "INGRESS",
            65534,
            False,
        ),
        (
            "projects/project-abc/global/firewalls/default-allow-internal",
            "default-allow-internal",
            "INGRESS",
            65534,
            False,
        ),
        (
            "projects/project-abc/global/firewalls/default-allow-rdp",
            "default-allow-rdp",
            "INGRESS",
            65534,
            False,
        ),
        (
            "projects/project-abc/global/firewalls/default-allow-ssh",
            "default-allow-ssh",
            "INGRESS",
            65534,
            False,
        ),
        (
            "projects/project-abc/global/firewalls/custom-port-incoming",
            "custom-port-incoming",
            "INGRESS",
            1000,
            False,
        ),
    }

    # Assert - VPC to Firewall relationship created
    assert check_rels(
        neo4j_session,
        "GCPVpc",
        "id",
        "GCPFirewall",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/global/networks/default",
            "projects/project-abc/global/firewalls/default-allow-icmp",
        ),
        (
            "projects/project-abc/global/networks/default",
            "projects/project-abc/global/firewalls/default-allow-internal",
        ),
        (
            "projects/project-abc/global/networks/default",
            "projects/project-abc/global/firewalls/default-allow-rdp",
        ),
        (
            "projects/project-abc/global/networks/default",
            "projects/project-abc/global/firewalls/default-allow-ssh",
        ),
        (
            "projects/project-abc/global/networks/default",
            "projects/project-abc/global/firewalls/custom-port-incoming",
        ),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_firewall_ingress_rules",
    return_value=tests.data.gcp.compute.LIST_FIREWALLS_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpcs",
    return_value=tests.data.gcp.compute.VPC_RESPONSE,
)
def test_sync_gcp_firewall_rules_with_ip_rules(
    mock_get_vpcs, mock_get_firewalls, neo4j_session
):
    """Test that firewalls create IpRule and IpRange nodes with proper relationships."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Pre-load VPCs
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act
    cartography.intel.gcp.compute.sync_gcp_firewall_rules(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - IpRule nodes created (checking SSH rule as example)
    ip_rules = check_nodes(
        neo4j_session,
        "IpRule",
        ["id", "protocol", "fromport", "toport"],
    )
    # The SSH rule should exist
    assert (
        "projects/project-abc/global/firewalls/default-allow-ssh/allow/22tcp",
        "tcp",
        22,
        22,
    ) in ip_rules

    # Assert - IpRange nodes created
    ip_ranges = check_nodes(
        neo4j_session,
        "IpRange",
        ["id"],
    )
    assert ("0.0.0.0/0",) in ip_ranges

    # Assert - IpRange to IpRule relationship (MEMBER_OF_IP_RULE)
    assert check_rels(
        neo4j_session,
        "IpRange",
        "id",
        "IpRule",
        "id",
        "MEMBER_OF_IP_RULE",
        rel_direction_right=True,
    )

    # Assert - IpRule to Firewall relationship (IpRule)-[ALLOWED_BY]->(GCPFirewall)
    allowed_by_rels = check_rels(
        neo4j_session,
        "IpRule",
        "id",
        "GCPFirewall",
        "id",
        "ALLOWED_BY",
        rel_direction_right=True,
    )
    # SSH rule should be allowed by the SSH firewall
    assert (
        "projects/project-abc/global/firewalls/default-allow-ssh/allow/22tcp",
        "projects/project-abc/global/firewalls/default-allow-ssh",
    ) in allowed_by_rels


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_firewall_ingress_rules",
    return_value=tests.data.gcp.compute.LIST_FIREWALLS_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpcs",
    return_value=tests.data.gcp.compute.VPC_RESPONSE,
)
def test_sync_gcp_firewall_rules_with_target_tags(
    mock_get_vpcs, mock_get_firewalls, neo4j_session
):
    """Test that firewalls with target tags create TARGET_TAG relationships."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Pre-load VPCs
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act
    cartography.intel.gcp.compute.sync_gcp_firewall_rules(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Firewall to NetworkTag TARGET_TAG relationship (custom-port-incoming has targetTags: ["test"])
    assert check_rels(
        neo4j_session,
        "GCPFirewall",
        "id",
        "GCPNetworkTag",
        "id",
        "TARGET_TAG",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/global/firewalls/custom-port-incoming",
            "projects/project-abc/global/networks/default/tags/test",
        ),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpcs",
    side_effect=[
        tests.data.gcp.compute.VPC_RESPONSE,
        tests.data.gcp.compute.VPC_RESPONSE_2,
    ],
)
def test_vpc_cleanup_scoped_to_project(mock_get_vpcs, neo4j_session):
    """Test that VPC cleanup is scoped to the current project and preserves other projects' VPCs."""
    # Arrange
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "PROJECT_ID": "project-abc"}
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Create projects
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id:$ProjectId})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $gcp_update_tag
        """,
        ProjectId="project-abc",
        gcp_update_tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id:$ProjectId})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $gcp_update_tag
        """,
        ProjectId="project-def",
        gcp_update_tag=TEST_UPDATE_TAG,
    )

    # First sync for project-abc
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        "project-abc",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert that the first project->vpc rel is created
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPVpc",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("project-abc", "projects/project-abc/global/networks/default"),
    }, "First project->vpc rels is not created"

    # Act: sync the second project at a later time
    new_tag = TEST_UPDATE_TAG + 1
    common_job_parameters["UPDATE_TAG"] = new_tag
    common_job_parameters["PROJECT_ID"] = "project-def"
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        "project-def",
        new_tag,
        common_job_parameters,
    )

    # Assert that the second project->vpc rel is created and the first project->vpc rel remains
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPVpc",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("project-abc", "projects/project-abc/global/networks/default"),
        ("project-def", "projects/project-def/global/networks/default2"),
    }, "Second project->vpc rels are not created"


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpcs",
    return_value=tests.data.gcp.compute.VPC_PEERING_RESPONSE,
)
def test_sync_gcp_vpc_peerings(mock_get_vpcs, neo4j_session):
    """Test that sync_gcp_vpcs() extracts peerings from the VPC response, loads
    one GCPVpcPeering node per side, links them to local and peer VPCs, and
    creates stub GCPVpc nodes for peer networks in unsynced projects."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Act
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Peering nodes created with correct properties
    assert check_nodes(
        neo4j_session,
        "GCPVpcPeering",
        ["id", "name", "state", "peer_project_id", "export_custom_routes"],
    ) == {
        (
            "projects/project-abc/global/networks/vpc-a/networkPeerings/peering-a-to-b",
            "peering-a-to-b",
            "ACTIVE",
            "project-def",
            True,
        ),
        (
            "projects/project-abc/global/networks/vpc-a/networkPeerings/peering-a-to-ext",
            "peering-a-to-ext",
            "INACTIVE",
            "project-xyz",
            False,
        ),
    }

    # Assert - Project to Peering RESOURCE relationships created
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPVpcPeering",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            "project-abc",
            "projects/project-abc/global/networks/vpc-a/networkPeerings/peering-a-to-b",
        ),
        (
            "project-abc",
            "projects/project-abc/global/networks/vpc-a/networkPeerings/peering-a-to-ext",
        ),
    }

    # Assert - Peering to local VPC relationships created
    assert check_rels(
        neo4j_session,
        "GCPVpcPeering",
        "id",
        "GCPVpc",
        "id",
        "LOCAL_NETWORK",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/global/networks/vpc-a/networkPeerings/peering-a-to-b",
            "projects/project-abc/global/networks/vpc-a",
        ),
        (
            "projects/project-abc/global/networks/vpc-a/networkPeerings/peering-a-to-ext",
            "projects/project-abc/global/networks/vpc-a",
        ),
    }

    # Assert - Peering to peer VPC relationships created, including stubs in
    # unsynced projects
    assert check_rels(
        neo4j_session,
        "GCPVpcPeering",
        "id",
        "GCPVpc",
        "id",
        "PEER_NETWORK",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/global/networks/vpc-a/networkPeerings/peering-a-to-b",
            "projects/project-def/global/networks/vpc-b",
        ),
        (
            "projects/project-abc/global/networks/vpc-a/networkPeerings/peering-a-to-ext",
            "projects/project-xyz/global/networks/vpc-ext",
        ),
    }

    # Assert - Peer VPC stubs exist, carry no name, and deliberately do NOT have
    # the VirtualNetwork ontology label (mirrors the GCPSubnet stub rationale:
    # stubs lack the data needed for _ont_* fields).
    stub_nodes = neo4j_session.run(
        """
        MATCH (v:GCPVpc)
        WHERE v.id IN $stub_ids
        RETURN v.id AS id, labels(v) AS labels, v.name AS name
        """,
        stub_ids=[
            "projects/project-def/global/networks/vpc-b",
            "projects/project-xyz/global/networks/vpc-ext",
        ],
    )
    stub_results = {r["id"]: r for r in stub_nodes}
    assert set(stub_results) == {
        "projects/project-def/global/networks/vpc-b",
        "projects/project-xyz/global/networks/vpc-ext",
    }
    for r in stub_results.values():
        assert r["labels"] == ["GCPVpc"]
        assert r["name"] is None


def test_sync_gcp_vpc_peerings_both_sides(neo4j_session):
    """Test that syncing both projects of a peering creates one peering node per
    side, and that the real VPC sync upgrades the stub node with full data and
    the VirtualNetwork label."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    _create_test_project(neo4j_session, "project-def", TEST_UPDATE_TAG)

    def _vpc_response_for_project(projectid, compute):
        if projectid == "project-def":
            return tests.data.gcp.compute.VPC_PEERING_PEER_RESPONSE
        return tests.data.gcp.compute.VPC_PEERING_RESPONSE

    # Act - sync project-abc first (creates a stub for project-def's vpc-b),
    # then project-def (upgrades the stub with real data).
    with patch.object(
        cartography.intel.gcp.compute,
        "get_gcp_vpcs",
        side_effect=_vpc_response_for_project,
    ):
        cartography.intel.gcp.compute.sync_gcp_vpcs(
            neo4j_session,
            MagicMock(),
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )
        common_job_parameters["PROJECT_ID"] = "project-def"
        cartography.intel.gcp.compute.sync_gcp_vpcs(
            neo4j_session,
            MagicMock(),
            "project-def",
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

    # Assert - one peering node per side
    assert check_nodes(
        neo4j_session,
        "GCPVpcPeering",
        ["id", "project_id"],
    ) == {
        (
            "projects/project-abc/global/networks/vpc-a/networkPeerings/peering-a-to-b",
            "project-abc",
        ),
        (
            "projects/project-abc/global/networks/vpc-a/networkPeerings/peering-a-to-ext",
            "project-abc",
        ),
        (
            "projects/project-def/global/networks/vpc-b/networkPeerings/peering-b-to-a",
            "project-def",
        ),
    }

    # Assert - the second side's LOCAL_NETWORK/PEER_NETWORK edges point the
    # other way, joining the two sides through the same VPC nodes
    assert check_rels(
        neo4j_session,
        "GCPVpcPeering",
        "id",
        "GCPVpc",
        "id",
        "LOCAL_NETWORK",
        rel_direction_right=True,
    ) >= {
        (
            "projects/project-def/global/networks/vpc-b/networkPeerings/peering-b-to-a",
            "projects/project-def/global/networks/vpc-b",
        ),
    }
    assert check_rels(
        neo4j_session,
        "GCPVpcPeering",
        "id",
        "GCPVpc",
        "id",
        "PEER_NETWORK",
        rel_direction_right=True,
    ) >= {
        (
            "projects/project-def/global/networks/vpc-b/networkPeerings/peering-b-to-a",
            "projects/project-abc/global/networks/vpc-a",
        ),
    }

    # Assert - the stub for project-def's vpc-b was upgraded by the real sync:
    # full properties, RESOURCE edge from project-def, and VirtualNetwork label.
    vpc_b = neo4j_session.run(
        """
        MATCH (v:GCPVpc {id: $id})
        RETURN labels(v) AS labels, v.name AS name, v.description AS description
        """,
        id="projects/project-def/global/networks/vpc-b",
    ).single()
    assert vpc_b["name"] == "vpc-b"
    assert vpc_b["description"] == "Peered network in project-def"
    assert "VirtualNetwork" in vpc_b["labels"]
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPVpc",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) >= {
        ("project-def", "projects/project-def/global/networks/vpc-b"),
    }


def test_sync_gcp_vpc_peerings_cleanup(neo4j_session):
    """Test that peerings removed from the VPC response are deleted on the next sync."""
    # Arrange - sync once with peerings present
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    with patch.object(
        cartography.intel.gcp.compute,
        "get_gcp_vpcs",
        return_value=tests.data.gcp.compute.VPC_PEERING_RESPONSE,
    ):
        cartography.intel.gcp.compute.sync_gcp_vpcs(
            neo4j_session,
            MagicMock(),
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )
    assert check_nodes(neo4j_session, "GCPVpcPeering", ["id"]) != set()

    # Act - sync again with the peerings removed at a later update tag
    new_tag = TEST_UPDATE_TAG + 1
    common_job_parameters["UPDATE_TAG"] = new_tag
    with patch.object(
        cartography.intel.gcp.compute,
        "get_gcp_vpcs",
        return_value=tests.data.gcp.compute.VPC_PEERING_RESPONSE_NO_PEERINGS,
    ):
        cartography.intel.gcp.compute.sync_gcp_vpcs(
            neo4j_session,
            MagicMock(),
            TEST_PROJECT_ID,
            new_tag,
            common_job_parameters,
        )

    # Assert - peering nodes are deleted; the VPC itself remains
    assert check_nodes(neo4j_session, "GCPVpcPeering", ["id"]) == set()
    assert check_nodes(neo4j_session, "GCPVpc", ["id"]) >= {
        ("projects/project-abc/global/networks/vpc-a",),
    }


@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpn_tunnels",
    return_value=(tests.data.gcp.compute.VPN_TUNNELS_RESPONSE["items"], False),
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpn_gateways",
    return_value=(tests.data.gcp.compute.VPN_GATEWAYS_RESPONSE["items"], False),
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_vpcs",
    return_value=tests.data.gcp.compute.VPC_PEERING_RESPONSE_NO_PEERINGS,
)
def test_sync_gcp_vpn_gateways_and_tunnels(
    mock_get_vpcs, mock_get_gateways, mock_get_tunnels, neo4j_session
):
    """Test that VPN gateways and tunnels are loaded with their project, VPC,
    and gateway relationships, that cross-project peer gateways become stubs,
    and that shared secrets are never ingested."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Act
    cartography.intel.gcp.compute.sync_gcp_vpcs(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    cartography.intel.gcp.compute.sync_gcp_vpn_gateways(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    cartography.intel.gcp.compute.sync_gcp_vpn_tunnels(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - VPN gateway node created with correct properties
    assert check_nodes(
        neo4j_session,
        "GCPVpnGateway",
        ["id", "name", "region", "project_id", "stack_type"],
    ) == {
        (
            "projects/project-abc/regions/us-central1/vpnGateways/gw-a",
            "gw-a",
            "us-central1",
            "project-abc",
            "IPV4_ONLY",
        ),
        # Stub for the peer gateway in unsynced project-xyz: only id and
        # project_id are set, all other checked fields are None.
        (
            "projects/project-xyz/regions/us-central1/vpnGateways/gw-ext",
            None,
            None,
            "project-xyz",
            None,
        ),
        # Stub for the peer gateway in unsynced project-def.
        (
            "projects/project-def/regions/us-central1/vpnGateways/gw-b",
            None,
            None,
            "project-def",
            None,
        ),
    }

    # Assert - Gateway to project and VPC relationships created
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPVpnGateway",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) >= {
        ("project-abc", "projects/project-abc/regions/us-central1/vpnGateways/gw-a"),
    }
    assert check_rels(
        neo4j_session,
        "GCPVpnGateway",
        "id",
        "GCPVpc",
        "id",
        "PART_OF_VPC",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/regions/us-central1/vpnGateways/gw-a",
            "projects/project-abc/global/networks/vpc-a",
        ),
    }

    # Assert - VPN tunnel nodes created with correct properties
    assert check_nodes(
        neo4j_session,
        "GCPVpnTunnel",
        ["id", "name", "status", "ike_version", "peer_ip"],
    ) == {
        (
            "projects/project-abc/regions/us-central1/vpnTunnels/tunnel-a-to-b",
            "tunnel-a-to-b",
            "ESTABLISHED",
            2,
            None,
        ),
        (
            "projects/project-abc/regions/us-central1/vpnTunnels/tunnel-a-to-ext",
            "tunnel-a-to-ext",
            "ESTABLISHED",
            2,
            None,
        ),
        (
            "projects/project-abc/regions/us-central1/vpnTunnels/tunnel-classic",
            "tunnel-classic",
            "ESTABLISHED",
            2,
            "198.51.100.1",
        ),
    }

    # Assert - Tunnel to project relationships created
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPVpnTunnel",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            "project-abc",
            "projects/project-abc/regions/us-central1/vpnTunnels/tunnel-a-to-b",
        ),
        (
            "project-abc",
            "projects/project-abc/regions/us-central1/vpnTunnels/tunnel-a-to-ext",
        ),
        (
            "project-abc",
            "projects/project-abc/regions/us-central1/vpnTunnels/tunnel-classic",
        ),
    }

    # Assert - HA tunnels connect to their local gateway (classic tunnel does not)
    assert check_rels(
        neo4j_session,
        "GCPVpnTunnel",
        "id",
        "GCPVpnGateway",
        "id",
        "USES_GATEWAY",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/regions/us-central1/vpnTunnels/tunnel-a-to-b",
            "projects/project-abc/regions/us-central1/vpnGateways/gw-a",
        ),
        (
            "projects/project-abc/regions/us-central1/vpnTunnels/tunnel-a-to-ext",
            "projects/project-abc/regions/us-central1/vpnGateways/gw-a",
        ),
    }

    # Assert - Cross-project CONNECTS_TO_GATEWAY edges land on stub gateways
    assert check_rels(
        neo4j_session,
        "GCPVpnTunnel",
        "id",
        "GCPVpnGateway",
        "id",
        "CONNECTS_TO_GATEWAY",
        rel_direction_right=True,
    ) == {
        (
            "projects/project-abc/regions/us-central1/vpnTunnels/tunnel-a-to-b",
            "projects/project-def/regions/us-central1/vpnGateways/gw-b",
        ),
        (
            "projects/project-abc/regions/us-central1/vpnTunnels/tunnel-a-to-ext",
            "projects/project-xyz/regions/us-central1/vpnGateways/gw-ext",
        ),
    }

    # Assert - the IKE shared secret from the API response was never ingested
    tunnels = neo4j_session.run("MATCH (t:GCPVpnTunnel) RETURN keys(t) AS keys")
    for record in tunnels:
        assert "sharedSecret" not in record["keys"]
        assert "sharedSecretHash" not in record["keys"]
        assert "shared_secret" not in record["keys"]


def test_sync_gcp_vpn_tunnels_both_sides(neo4j_session):
    """Test that syncing both projects of a cross-project HA VPN yields gateway
    and tunnel nodes on both sides, with CONNECTS_TO_GATEWAY edges crossing the
    project boundary in both directions, and the peer-side stub upgraded."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    _create_test_project(neo4j_session, "project-def", TEST_UPDATE_TAG)

    def _vpc_response_for_project(projectid, compute):
        if projectid == "project-def":
            return tests.data.gcp.compute.VPC_PEERING_PEER_RESPONSE
        return tests.data.gcp.compute.VPC_PEERING_RESPONSE

    def _gateway_response_for_project(projectid, compute):
        if projectid == "project-def":
            return (tests.data.gcp.compute.VPN_GATEWAYS_PEER_RESPONSE["items"], False)
        return (tests.data.gcp.compute.VPN_GATEWAYS_RESPONSE["items"], False)

    def _tunnel_response_for_project(projectid, compute):
        if projectid == "project-def":
            return (tests.data.gcp.compute.VPN_TUNNELS_PEER_RESPONSE["items"], False)
        return (tests.data.gcp.compute.VPN_TUNNELS_RESPONSE["items"], False)

    # Act - sync project-abc first (creates a stub for project-def's gw-b),
    # then project-def (upgrades the stub with real data).
    with (
        patch.object(
            cartography.intel.gcp.compute,
            "get_gcp_vpcs",
            side_effect=_vpc_response_for_project,
        ),
        patch.object(
            cartography.intel.gcp.compute,
            "get_gcp_vpn_gateways",
            side_effect=_gateway_response_for_project,
        ),
        patch.object(
            cartography.intel.gcp.compute,
            "get_gcp_vpn_tunnels",
            side_effect=_tunnel_response_for_project,
        ),
    ):
        for project in (TEST_PROJECT_ID, "project-def"):
            common_job_parameters["PROJECT_ID"] = project
            cartography.intel.gcp.compute.sync_gcp_vpcs(
                neo4j_session,
                MagicMock(),
                project,
                TEST_UPDATE_TAG,
                common_job_parameters,
            )
            cartography.intel.gcp.compute.sync_gcp_vpn_gateways(
                neo4j_session,
                MagicMock(),
                project,
                TEST_UPDATE_TAG,
                common_job_parameters,
            )
            cartography.intel.gcp.compute.sync_gcp_vpn_tunnels(
                neo4j_session,
                MagicMock(),
                project,
                TEST_UPDATE_TAG,
                common_job_parameters,
            )

    # Assert - the stub for project-def's gw-b was upgraded by the real sync
    gw_b = neo4j_session.run(
        """
        MATCH (g:GCPVpnGateway {id: $id})
        RETURN g.name AS name, g.description AS description
        """,
        id="projects/project-def/regions/us-central1/vpnGateways/gw-b",
    ).single()
    assert gw_b["name"] == "gw-b"
    assert gw_b["description"] == "HA VPN gateway in project-def"

    # Assert - both tunnel directions exist with cross-project
    # CONNECTS_TO_GATEWAY edges pointing at real gateway nodes
    assert check_rels(
        neo4j_session,
        "GCPVpnTunnel",
        "id",
        "GCPVpnGateway",
        "id",
        "CONNECTS_TO_GATEWAY",
        rel_direction_right=True,
    ) >= {
        (
            "projects/project-abc/regions/us-central1/vpnTunnels/tunnel-a-to-b",
            "projects/project-def/regions/us-central1/vpnGateways/gw-b",
        ),
        (
            "projects/project-def/regions/us-central1/vpnTunnels/tunnel-b-to-a",
            "projects/project-abc/regions/us-central1/vpnGateways/gw-a",
        ),
    }

    # Assert - gateway gw-b links to its own project's VPC
    assert check_rels(
        neo4j_session,
        "GCPVpnGateway",
        "id",
        "GCPVpc",
        "id",
        "PART_OF_VPC",
        rel_direction_right=True,
    ) >= {
        (
            "projects/project-def/regions/us-central1/vpnGateways/gw-b",
            "projects/project-def/global/networks/vpc-b",
        ),
    }


def test_sync_gcp_vpn_tunnels_cleanup(neo4j_session):
    """Test that gateways and tunnels removed from the API responses are deleted
    on the next sync, and that peer gateway stubs in unsynced projects are
    removed once no tunnel references them anymore."""
    # Arrange - sync once with gateways and tunnels present
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    with (
        patch.object(
            cartography.intel.gcp.compute,
            "get_gcp_vpn_gateways",
            return_value=(tests.data.gcp.compute.VPN_GATEWAYS_RESPONSE["items"], False),
        ),
        patch.object(
            cartography.intel.gcp.compute,
            "get_gcp_vpn_tunnels",
            return_value=(tests.data.gcp.compute.VPN_TUNNELS_RESPONSE["items"], False),
        ),
    ):
        cartography.intel.gcp.compute.sync_gcp_vpn_gateways(
            neo4j_session,
            MagicMock(),
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )
        cartography.intel.gcp.compute.sync_gcp_vpn_tunnels(
            neo4j_session,
            MagicMock(),
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )
    assert check_nodes(neo4j_session, "GCPVpnTunnel", ["id"]) != set()

    # Act - sync again with empty responses at a later update tag
    new_tag = TEST_UPDATE_TAG + 1
    common_job_parameters["UPDATE_TAG"] = new_tag
    with (
        patch.object(
            cartography.intel.gcp.compute,
            "get_gcp_vpn_gateways",
            return_value=(
                tests.data.gcp.compute.VPN_GATEWAYS_RESPONSE_EMPTY.get("items", []),
                False,
            ),
        ),
        patch.object(
            cartography.intel.gcp.compute,
            "get_gcp_vpn_tunnels",
            return_value=(
                tests.data.gcp.compute.VPN_TUNNELS_RESPONSE_EMPTY.get("items", []),
                False,
            ),
        ),
    ):
        cartography.intel.gcp.compute.sync_gcp_vpn_gateways(
            neo4j_session,
            MagicMock(),
            TEST_PROJECT_ID,
            new_tag,
            common_job_parameters,
        )
        cartography.intel.gcp.compute.sync_gcp_vpn_tunnels(
            neo4j_session,
            MagicMock(),
            TEST_PROJECT_ID,
            new_tag,
            common_job_parameters,
        )

    # Assert - project-abc's gateways and tunnels are deleted, and the peer
    # gateway stubs are gone too: with no tunnel referencing them, the orphan
    # stub cleanup removes them even though their owning projects never sync.
    assert check_nodes(neo4j_session, "GCPVpnTunnel", ["id"]) == set()
    assert check_nodes(neo4j_session, "GCPVpnGateway", ["id"]) == set()


def test_sync_gcp_vpc_peerings_orphan_stub_cleanup(neo4j_session):
    """Two-sync test: peer VPC stubs created for unsynced projects must be
    removed once the peerings referencing them disappear, while the real local
    VPC is untouched."""
    # Arrange - sync 1: vpc-a has peerings to vpc-b (project-def) and vpc-c
    # (project-xyz), both unsynced, so stubs are created for both.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    with patch.object(
        cartography.intel.gcp.compute,
        "get_gcp_vpcs",
        return_value=tests.data.gcp.compute.VPC_PEERING_RESPONSE,
    ):
        cartography.intel.gcp.compute.sync_gcp_vpcs(
            neo4j_session,
            MagicMock(),
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

    assert check_nodes(neo4j_session, "GCPVpc", ["id"]) == {
        ("projects/project-abc/global/networks/vpc-a",),
        ("projects/project-def/global/networks/vpc-b",),
        ("projects/project-xyz/global/networks/vpc-ext",),
    }
    assert check_nodes(neo4j_session, "GCPVpcPeering", ["id"]) != set()

    # Act - sync 2: all peerings are gone from the API response.
    new_tag = TEST_UPDATE_TAG + 1
    common_job_parameters["UPDATE_TAG"] = new_tag
    with patch.object(
        cartography.intel.gcp.compute,
        "get_gcp_vpcs",
        return_value=tests.data.gcp.compute.VPC_PEERING_RESPONSE_NO_PEERINGS,
    ):
        cartography.intel.gcp.compute.sync_gcp_vpcs(
            neo4j_session,
            MagicMock(),
            TEST_PROJECT_ID,
            new_tag,
            common_job_parameters,
        )

    # Assert - peerings and their orphan stub VPCs are deleted; the real local
    # VPC (owned by the synced project via RESOURCE) remains.
    assert check_nodes(neo4j_session, "GCPVpcPeering", ["id"]) == set()
    assert check_nodes(neo4j_session, "GCPVpc", ["id"]) == {
        ("projects/project-abc/global/networks/vpc-a",),
    }
