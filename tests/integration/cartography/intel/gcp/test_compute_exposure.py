from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.backendservice
import cartography.intel.gcp.cloud_armor
import cartography.intel.gcp.compute
import cartography.intel.gcp.instancegroup
from cartography.graph.job import GraphJob
from tests.data.gcp.compute_exposure import BACKEND_SERVICE_RESPONSE
from tests.data.gcp.compute_exposure import CLOUD_ARMOR_RESPONSE
from tests.data.gcp.compute_exposure import GLOBAL_FORWARDING_RULES_RESPONSE
from tests.data.gcp.compute_exposure import INSTANCE_GROUP_RESPONSES
from tests.data.gcp.compute_exposure import INSTANCE_RESPONSES
from tests.data.gcp.compute_exposure import REGIONAL_FORWARDING_RULES_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "sample-project-123456"


def _create_test_project(neo4j_session, project_id: str, update_tag: int) -> None:
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id:$ProjectId})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $gcp_update_tag
        """,
        ProjectId=project_id,
        gcp_update_tag=update_tag,
    )


def _sync_exposure_entities(neo4j_session, common_job_parameters: dict) -> None:
    cartography.intel.gcp.instancegroup.sync_gcp_instance_groups(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        [],
        [],
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    cartography.intel.gcp.cloud_armor.sync_gcp_cloud_armor(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    cartography.intel.gcp.backendservice.sync_gcp_backend_services(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        [],
        TEST_UPDATE_TAG,
        common_job_parameters,
    )


@patch.object(
    cartography.intel.gcp.instancegroup,
    "get_gcp_zonal_instance_groups",
    return_value=INSTANCE_GROUP_RESPONSES,
)
@patch.object(
    cartography.intel.gcp.instancegroup,
    "get_gcp_regional_instance_groups",
    return_value=[],
)
@patch.object(
    cartography.intel.gcp.cloud_armor,
    "get_gcp_cloud_armor_policies",
    return_value=CLOUD_ARMOR_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.backendservice,
    "get_gcp_global_backend_services",
    return_value=BACKEND_SERVICE_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_instance_responses",
    return_value=INSTANCE_RESPONSES,
)
def test_sync_gcp_compute_exposure_entities_and_relationships(
    mock_get_instances,
    mock_get_backend_services,
    mock_get_cloud_armor,
    mock_get_regional_igs,
    mock_get_zonal_igs,
    neo4j_session,
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    cartography.intel.gcp.compute.sync_gcp_instances(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        None,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act
    _sync_exposure_entities(neo4j_session, common_job_parameters)

    # Assert
    assert check_nodes(
        neo4j_session,
        "GCPBackendService",
        ["id", "name", "load_balancing_scheme"],
    ) == {
        (
            f"projects/{TEST_PROJECT_ID}/global/backendServices/test-backend-service",
            "test-backend-service",
            "EXTERNAL",
        ),
    }

    assert check_nodes(
        neo4j_session,
        "GCPInstanceGroup",
        ["id", "name", "zone"],
    ) == {
        (
            f"projects/{TEST_PROJECT_ID}/zones/us-central1-a/instanceGroups/test-instance-group",
            "test-instance-group",
            "us-central1-a",
        ),
    }

    assert check_nodes(
        neo4j_session,
        "GCPCloudArmorPolicy",
        ["id", "name", "policy_type"],
    ) == {
        (
            f"projects/{TEST_PROJECT_ID}/global/securityPolicies/test-armor-policy",
            "test-armor-policy",
            "CLOUD_ARMOR",
        ),
    }

    assert check_rels(
        neo4j_session,
        "GCPBackendService",
        "id",
        "GCPInstanceGroup",
        "id",
        "ROUTES_TO",
        rel_direction_right=True,
    ) == {
        (
            f"projects/{TEST_PROJECT_ID}/global/backendServices/test-backend-service",
            f"projects/{TEST_PROJECT_ID}/zones/us-central1-a/instanceGroups/test-instance-group",
        ),
    }

    assert check_rels(
        neo4j_session,
        "GCPInstanceGroup",
        "id",
        "GCPInstance",
        "id",
        "HAS_MEMBER",
        rel_direction_right=True,
    ) == {
        (
            f"projects/{TEST_PROJECT_ID}/zones/us-central1-a/instanceGroups/test-instance-group",
            f"projects/{TEST_PROJECT_ID}/zones/us-central1-a/instances/vm-private-1",
        ),
        (
            f"projects/{TEST_PROJECT_ID}/zones/us-central1-a/instanceGroups/test-instance-group",
            f"projects/{TEST_PROJECT_ID}/zones/us-central1-a/instances/vm-private-2",
        ),
    }

    assert check_rels(
        neo4j_session,
        "GCPCloudArmorPolicy",
        "id",
        "GCPBackendService",
        "id",
        "PROTECTS",
        rel_direction_right=True,
    ) == {
        (
            f"projects/{TEST_PROJECT_ID}/global/securityPolicies/test-armor-policy",
            f"projects/{TEST_PROJECT_ID}/global/backendServices/test-backend-service",
        ),
    }


@patch.object(
    cartography.intel.gcp.instancegroup,
    "get_gcp_zonal_instance_groups",
    return_value=INSTANCE_GROUP_RESPONSES,
)
@patch.object(
    cartography.intel.gcp.instancegroup,
    "get_gcp_regional_instance_groups",
    return_value=[],
)
@patch.object(
    cartography.intel.gcp.cloud_armor,
    "get_gcp_cloud_armor_policies",
    return_value=CLOUD_ARMOR_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.backendservice,
    "get_gcp_global_backend_services",
    return_value=BACKEND_SERVICE_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_instance_responses",
    return_value=INSTANCE_RESPONSES,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_global_forwarding_rules",
    return_value=GLOBAL_FORWARDING_RULES_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_regional_forwarding_rules",
    return_value=REGIONAL_FORWARDING_RULES_RESPONSE,
)
def test_scoped_gcp_compute_exposure_jobs_model_and_cleanup(
    mock_get_regional_forwarding_rules,
    mock_get_global_forwarding_rules,
    mock_get_instances,
    mock_get_backend_services,
    mock_get_cloud_armor,
    mock_get_regional_igs,
    mock_get_zonal_igs,
    neo4j_session,
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
        "LIMIT_SIZE": 1000,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    cartography.intel.gcp.compute.sync_gcp_instances(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        None,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    _sync_exposure_entities(neo4j_session, common_job_parameters)
    cartography.intel.gcp.compute.sync_gcp_forwarding_rules(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        ["us-central1"],
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act
    GraphJob.run_from_json_file(
        "cartography/data/jobs/scoped_analysis/gcp_compute_exposure.json",
        neo4j_session,
        common_job_parameters,
    )
    GraphJob.run_from_json_file(
        "cartography/data/jobs/scoped_analysis/gcp_lb_exposure.json",
        neo4j_session,
        common_job_parameters,
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "GCPForwardingRule",
        ["id", "exposed_internet", "exposed_internet_type"],
    ) == {
        (
            f"projects/{TEST_PROJECT_ID}/global/forwardingRules/ext-fr",
            True,
            "direct",
        ),
        (
            f"projects/{TEST_PROJECT_ID}/regions/us-central1/forwardingRules/int-fr",
            False,
            None,
        ),
    }

    assert check_nodes(
        neo4j_session,
        "GCPInstance",
        ["id", "exposed_internet", "exposed_internet_type"],
    ) == {
        (
            f"projects/{TEST_PROJECT_ID}/zones/us-central1-a/instances/vm-private-1",
            True,
            "gcp_lb",
        ),
        (
            f"projects/{TEST_PROJECT_ID}/zones/us-central1-a/instances/vm-private-2",
            True,
            "gcp_lb",
        ),
    }

    assert check_rels(
        neo4j_session,
        "GCPBackendService",
        "id",
        "GCPInstance",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {
        (
            f"projects/{TEST_PROJECT_ID}/global/backendServices/test-backend-service",
            f"projects/{TEST_PROJECT_ID}/zones/us-central1-a/instances/vm-private-1",
        ),
        (
            f"projects/{TEST_PROJECT_ID}/global/backendServices/test-backend-service",
            f"projects/{TEST_PROJECT_ID}/zones/us-central1-a/instances/vm-private-2",
        ),
    }

    # Remove all members from the instance group to force stale EXPOSE cleanup.
    neo4j_session.run(
        """
        MATCH (ig:GCPInstanceGroup{id:$instance_group_id})-[r:HAS_MEMBER]->(:GCPInstance)
        DELETE r
        """,
        instance_group_id=f"projects/{TEST_PROJECT_ID}/zones/us-central1-a/instanceGroups/test-instance-group",
    )

    GraphJob.run_from_json_file(
        "cartography/data/jobs/scoped_analysis/gcp_lb_exposure.json",
        neo4j_session,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG + 1,
            "PROJECT_ID": TEST_PROJECT_ID,
            "LIMIT_SIZE": 1000,
        },
    )

    assert (
        check_rels(
            neo4j_session,
            "GCPBackendService",
            "id",
            "GCPInstance",
            "id",
            "EXPOSE",
            rel_direction_right=True,
        )
        == set()
    )
