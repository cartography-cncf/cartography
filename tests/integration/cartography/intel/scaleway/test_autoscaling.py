from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.instances.autoscaling
from tests.data.scaleway.autoscaling import SCALEWAY_INSTANCE_GROUPS
from tests.data.scaleway.autoscaling import SCALEWAY_INSTANCE_TEMPLATES
from tests.data.scaleway.autoscaling import SCALEWAY_SCALING_POLICIES
from tests.data.scaleway.autoscaling import TEST_BACKEND_ID
from tests.data.scaleway.autoscaling import TEST_INSTANCE_GROUP_ID
from tests.data.scaleway.autoscaling import TEST_INSTANCE_TEMPLATE_ID
from tests.data.scaleway.autoscaling import TEST_LB_ID
from tests.data.scaleway.autoscaling import TEST_ORG_ID
from tests.data.scaleway.autoscaling import TEST_PRIVATE_NETWORK_ID
from tests.data.scaleway.autoscaling import TEST_PROJECT_ID
from tests.data.scaleway.autoscaling import TEST_SCALING_POLICY_ID
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_autoscaling_dependencies(neo4j_session):
    neo4j_session.run(
        """
        MERGE (:ScalewayPrivateNetwork {id: $private_network_id})
        MERGE (:ScalewayLoadBalancer {id: $lb_id})
        MERGE (:ScalewayLBBackend {id: $backend_id})
        """,
        private_network_id=TEST_PRIVATE_NETWORK_ID,
        lb_id=TEST_LB_ID,
        backend_id=TEST_BACKEND_ID,
    )


@patch.object(
    cartography.intel.scaleway.instances.autoscaling,
    "get",
    return_value=(
        SCALEWAY_INSTANCE_TEMPLATES,
        SCALEWAY_INSTANCE_GROUPS,
        SCALEWAY_SCALING_POLICIES,
    ),
)
def test_load_scaleway_autoscaling(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    _ensure_local_neo4j_has_test_autoscaling_dependencies(neo4j_session)

    # Act
    cartography.intel.scaleway.instances.autoscaling.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert nodes exist
    assert check_nodes(neo4j_session, "ScalewayInstanceTemplate", ["id", "name"]) == {
        (TEST_INSTANCE_TEMPLATE_ID, "demo-template"),
    }
    assert check_nodes(neo4j_session, "ScalewayInstanceGroup", ["id", "name"]) == {
        (TEST_INSTANCE_GROUP_ID, "demo-group"),
    }
    assert check_nodes(neo4j_session, "ScalewayScalingPolicy", ["id", "name"]) == {
        (TEST_SCALING_POLICY_ID, "scale-up-cpu"),
    }

    # Assert everything is linked to the project
    for label in (
        "ScalewayInstanceTemplate",
        "ScalewayInstanceGroup",
        "ScalewayScalingPolicy",
    ):
        assert check_rels(
            neo4j_session,
            label,
            "id",
            "ScalewayProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        ), f"{label} not linked to project"

    # Assert Instance Group uses its template
    assert check_rels(
        neo4j_session,
        "ScalewayInstanceGroup",
        "id",
        "ScalewayInstanceTemplate",
        "id",
        "USES",
        rel_direction_right=True,
    ) == {(TEST_INSTANCE_GROUP_ID, TEST_INSTANCE_TEMPLATE_ID)}

    # Assert Scaling Policy applies to Instance Group
    assert check_rels(
        neo4j_session,
        "ScalewayScalingPolicy",
        "id",
        "ScalewayInstanceGroup",
        "id",
        "APPLIES_TO",
        rel_direction_right=True,
    ) == {(TEST_SCALING_POLICY_ID, TEST_INSTANCE_GROUP_ID)}

    # Assert Instance Group uses its load balancer
    assert check_rels(
        neo4j_session,
        "ScalewayInstanceGroup",
        "id",
        "ScalewayLoadBalancer",
        "id",
        "USES",
        rel_direction_right=True,
    ) == {(TEST_INSTANCE_GROUP_ID, TEST_LB_ID)}

    # Assert the Template is attached to the private network
    assert check_rels(
        neo4j_session,
        "ScalewayInstanceTemplate",
        "id",
        "ScalewayPrivateNetwork",
        "id",
        "ATTACHED_TO",
        rel_direction_right=True,
    ) == {(TEST_INSTANCE_TEMPLATE_ID, TEST_PRIVATE_NETWORK_ID)}

    # Assert the Load Balancer (not the Group) is attached to the private
    # network: this is a fact about the LB, sourced from the Autoscaling API,
    # and linked via a MatchLink so the LB node's own properties aren't
    # touched by this sync.
    assert check_rels(
        neo4j_session,
        "ScalewayLoadBalancer",
        "id",
        "ScalewayPrivateNetwork",
        "id",
        "ATTACHED_TO",
        rel_direction_right=True,
    ) == {(TEST_LB_ID, TEST_PRIVATE_NETWORK_ID)}


@patch.object(cartography.intel.scaleway.instances.autoscaling, "get")
def test_stale_autoscaling_resources_are_cleaned_up(mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    _ensure_local_neo4j_has_test_autoscaling_dependencies(neo4j_session)

    # Act: initial sync loads a template, group, and policy
    mock_get.return_value = (
        SCALEWAY_INSTANCE_TEMPLATES,
        SCALEWAY_INSTANCE_GROUPS,
        SCALEWAY_SCALING_POLICIES,
    )
    cartography.intel.scaleway.instances.autoscaling.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Act: second sync with a new update tag and nothing returned, simulating
    # the template, group, and policy being removed upstream
    next_update_tag = TEST_UPDATE_TAG + 1
    mock_get.return_value = ([], [], [])
    cartography.intel.scaleway.instances.autoscaling.sync(
        neo4j_session,
        client,
        {**common_job_parameters, "UPDATE_TAG": next_update_tag},
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=next_update_tag,
    )

    # Assert stale nodes and relationships were removed
    assert check_nodes(neo4j_session, "ScalewayInstanceTemplate", ["id"]) == set()
    assert check_nodes(neo4j_session, "ScalewayInstanceGroup", ["id"]) == set()
    assert check_nodes(neo4j_session, "ScalewayScalingPolicy", ["id"]) == set()
    assert (
        check_rels(
            neo4j_session,
            "ScalewayInstanceGroup",
            "id",
            "ScalewayInstanceTemplate",
            "id",
            "USES",
            rel_direction_right=True,
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "ScalewayScalingPolicy",
            "id",
            "ScalewayInstanceGroup",
            "id",
            "APPLIES_TO",
            rel_direction_right=True,
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "ScalewayLoadBalancer",
            "id",
            "ScalewayPrivateNetwork",
            "id",
            "ATTACHED_TO",
            rel_direction_right=True,
        )
        == set()
    )
