from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.backendservice
import cartography.intel.gcp.cloud_armor
import cartography.intel.gcp.instancegroup
from cartography.graph.job import GraphJob
from tests.data.gcp.compute_exposure import BACKEND_SERVICE_RESPONSE
from tests.data.gcp.compute_exposure import CLOUD_ARMOR_RESPONSE
from tests.data.gcp.compute_exposure import INSTANCE_GROUP_RESPONSES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "project-abc"


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


def _seed_instances(neo4j_session, project_id: str, update_tag: int) -> None:
    instance_ids = [
        "projects/sample-project-123456/zones/us-central1-a/instances/vm-private-1",
        "projects/sample-project-123456/zones/us-central1-a/instances/vm-private-2",
    ]
    neo4j_session.run(
        """
        MATCH (p:GCPProject{id:$ProjectId})
        UNWIND $InstanceIds AS instance_id
        MERGE (i:GCPInstance{id: instance_id})
        ON CREATE SET i.firstseen = timestamp()
        SET i.lastupdated = $gcp_update_tag
        MERGE (p)-[r:RESOURCE]->(i)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $gcp_update_tag
        """,
        ProjectId=project_id,
        InstanceIds=instance_ids,
        gcp_update_tag=update_tag,
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
def test_sync_gcp_compute_exposure_entities_and_relationships(
    mock_get_backend_services,
    mock_get_cloud_armor,
    mock_get_regional_igs,
    mock_get_zonal_igs,
    neo4j_session,
):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    _seed_instances(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

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

    assert check_nodes(
        neo4j_session,
        "GCPBackendService",
        ["id", "name", "load_balancing_scheme"],
    ) == {
        (
            "projects/sample-project-123456/global/backendServices/test-backend-service",
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
            "projects/sample-project-123456/zones/us-central1-a/instanceGroups/test-instance-group",
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
            "projects/sample-project-123456/global/securityPolicies/test-armor-policy",
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
            "projects/sample-project-123456/global/backendServices/test-backend-service",
            "projects/sample-project-123456/zones/us-central1-a/instanceGroups/test-instance-group",
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
            "projects/sample-project-123456/zones/us-central1-a/instanceGroups/test-instance-group",
            "projects/sample-project-123456/zones/us-central1-a/instances/vm-private-1",
        ),
        (
            "projects/sample-project-123456/zones/us-central1-a/instanceGroups/test-instance-group",
            "projects/sample-project-123456/zones/us-central1-a/instances/vm-private-2",
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
            "projects/sample-project-123456/global/securityPolicies/test-armor-policy",
            "projects/sample-project-123456/global/backendServices/test-backend-service",
        ),
    }


def test_scoped_gcp_compute_exposure_jobs_model_and_cleanup(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    neo4j_session.run(
        """
        MERGE (p:GCPProject{id:$ProjectId})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $update_tag
        MERGE (fr_ext:GCPForwardingRule{id:'projects/project-abc/global/forwardingRules/ext-fr'})
        ON CREATE SET fr_ext.firstseen = timestamp()
        SET fr_ext.load_balancing_scheme = 'EXTERNAL', fr_ext.lastupdated = $update_tag
        MERGE (fr_int:GCPForwardingRule{id:'projects/project-abc/regions/us-central1/forwardingRules/int-fr'})
        ON CREATE SET fr_int.firstseen = timestamp()
        SET fr_int.load_balancing_scheme = 'INTERNAL', fr_int.lastupdated = $update_tag
        MERGE (bs:GCPBackendService{id:'projects/project-abc/global/backendServices/ext-bs'})
        ON CREATE SET bs.firstseen = timestamp()
        SET bs.load_balancing_scheme = 'EXTERNAL', bs.lastupdated = $update_tag
        MERGE (ig:GCPInstanceGroup{id:'projects/project-abc/zones/us-central1-a/instanceGroups/ig-1'})
        ON CREATE SET ig.firstseen = timestamp()
        SET ig.lastupdated = $update_tag
        MERGE (i:GCPInstance{id:'projects/project-abc/zones/us-central1-a/instances/vm-1'})
        ON CREATE SET i.firstseen = timestamp()
        SET i.lastupdated = $update_tag
        MERGE (p)-[p_fr_ext:RESOURCE]->(fr_ext)
        ON CREATE SET p_fr_ext.firstseen = timestamp()
        SET p_fr_ext.lastupdated = $update_tag
        MERGE (p)-[p_fr_int:RESOURCE]->(fr_int)
        ON CREATE SET p_fr_int.firstseen = timestamp()
        SET p_fr_int.lastupdated = $update_tag
        MERGE (p)-[p_bs:RESOURCE]->(bs)
        ON CREATE SET p_bs.firstseen = timestamp()
        SET p_bs.lastupdated = $update_tag
        MERGE (p)-[p_ig:RESOURCE]->(ig)
        ON CREATE SET p_ig.firstseen = timestamp()
        SET p_ig.lastupdated = $update_tag
        MERGE (p)-[p_i:RESOURCE]->(i)
        ON CREATE SET p_i.firstseen = timestamp()
        SET p_i.lastupdated = $update_tag
        MERGE (bs)-[routes:ROUTES_TO]->(ig)
        ON CREATE SET routes.firstseen = timestamp()
        SET routes.lastupdated = $update_tag
        MERGE (ig)-[member:HAS_MEMBER]->(i)
        ON CREATE SET member.firstseen = timestamp()
        SET member.lastupdated = $update_tag
        """,
        ProjectId=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
        "LIMIT_SIZE": 1000,
    }

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

    assert check_nodes(
        neo4j_session,
        "GCPForwardingRule",
        ["id", "exposed_internet", "exposed_internet_type"],
    ) == {
        (
            "projects/project-abc/global/forwardingRules/ext-fr",
            True,
            "direct",
        ),
        (
            "projects/project-abc/regions/us-central1/forwardingRules/int-fr",
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
            "projects/project-abc/zones/us-central1-a/instances/vm-1",
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
            "projects/project-abc/global/backendServices/ext-bs",
            "projects/project-abc/zones/us-central1-a/instances/vm-1",
        ),
    }

    neo4j_session.run(
        """
        MATCH (ig:GCPInstanceGroup{id:'projects/project-abc/zones/us-central1-a/instanceGroups/ig-1'})
              -[r:HAS_MEMBER]->(:GCPInstance{id:'projects/project-abc/zones/us-central1-a/instances/vm-1'})
        DELETE r
        """,
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
