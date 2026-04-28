from unittest.mock import patch

import cartography.intel.gcp.permission_relationships
from tests.data.gcp.permission_relationships import MOCK_PERMISSION_RELATIONSHIPS_YAML
from tests.integration.util import check_rels

TEST_PROJECT_ID = "project-abc"
TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "ORG_RESOURCE_NAME": "organizations/1337",
    "PROJECT_ID": TEST_PROJECT_ID,
    "gcp_permission_relationships_file": "dummy_path",
}


def _create_test_project(neo4j_session):
    """Create a test GCP project node with no other data."""
    neo4j_session.run(
        """
        MERGE (project:GCPProject{id: $project_id})
        ON CREATE SET project.firstseen = timestamp()
        SET project.lastupdated = $update_tag
        """,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.gcp.permission_relationships,
    "parse_permission_relationships_file",
    return_value=MOCK_PERMISSION_RELATIONSHIPS_YAML,
)
def test_permission_relationships_fresh_graph_no_relationships(
    mock_parse_yaml,
    neo4j_session,
):
    """
    Test that permission_relationships.sync() on a fresh graph (no iam/policy_bindings data)
    creates no relationships.

    This simulates a selective sync run with --gcp-requested-syncs=permission_relationships
    on a fresh graph where iam and policy_bindings have not been synced.
    """
    # ARRANGE - Only a bare GCPProject node exists, no IAM roles, policy bindings, or resources
    _create_test_project(neo4j_session)

    # ACT
    cartography.intel.gcp.permission_relationships.sync(
        neo4j_session,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
        {},
    )

    # ASSERT - No CAN_READ relationships were created (from the YAML config's GCPBucket entry)
    assert (
        check_rels(
            neo4j_session,
            "GCPPrincipal",
            "email",
            "GCPBucket",
            "id",
            "CAN_READ",
            rel_direction_right=True,
        )
        == set()
    )

    # ASSERT - No CAN_GET_ACCELERATOR_TYPES relationships were created (from the GCPInstance entry)
    assert (
        check_rels(
            neo4j_session,
            "GCPPrincipal",
            "email",
            "GCPInstance",
            "id",
            "CAN_GET_ACCELERATOR_TYPES",
            rel_direction_right=True,
        )
        == set()
    )
