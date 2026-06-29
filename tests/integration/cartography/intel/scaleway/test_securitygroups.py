from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.instances.securitygroups
from tests.data.scaleway.securitygroups import SCALEWAY_SECURITY_GROUP_RULES
from tests.data.scaleway.securitygroups import SCALEWAY_SECURITY_GROUPS
from tests.integration.cartography.intel.scaleway.test_instances import (
    _ensure_local_neo4j_has_test_instances,
)
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_SG_ID = "b2c3d4e5-1111-4820-b8d6-0eef10cfcd6d"
TEST_INSTANCE_ID = "345627e9-18ff-47e0-b73d-3f38fddb4390"


@patch.object(
    cartography.intel.scaleway.instances.securitygroups,
    "get",
    return_value=(
        SCALEWAY_SECURITY_GROUPS,
        {TEST_SG_ID: SCALEWAY_SECURITY_GROUP_RULES},
    ),
)
def test_load_scaleway_security_groups(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    _ensure_local_neo4j_has_test_instances(neo4j_session)

    # Act
    cartography.intel.scaleway.instances.securitygroups.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert SecurityGroup exists
    assert check_nodes(neo4j_session, "ScalewaySecurityGroup", ["id", "name"]) == {
        (TEST_SG_ID, "demo-sg"),
    }

    # Assert Rules exist and carry their direction
    assert check_nodes(
        neo4j_session, "ScalewaySecurityGroupRule", ["id", "direction"]
    ) == {
        ("aaaa1111-2222-4820-b8d6-0eef10cfcd6d", "inbound"),
        ("bbbb2222-3333-4820-b8d6-0eef10cfcd6d", "outbound"),
    }

    # Assert cross-cloud ontology labels are applied to rules
    assert check_nodes(neo4j_session, "IpPermissionInbound", ["id"]) == {
        ("aaaa1111-2222-4820-b8d6-0eef10cfcd6d",),
    }
    assert check_nodes(neo4j_session, "IpPermissionEgress", ["id"]) == {
        ("bbbb2222-3333-4820-b8d6-0eef10cfcd6d",),
    }

    # Assert SecurityGroup is linked to the project
    assert check_rels(
        neo4j_session,
        "ScalewaySecurityGroup",
        "id",
        "ScalewayProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(TEST_SG_ID, TEST_PROJECT_ID)}

    # Assert Rules are linked to their SecurityGroup
    assert check_rels(
        neo4j_session,
        "ScalewaySecurityGroupRule",
        "id",
        "ScalewaySecurityGroup",
        "id",
        "MEMBER_OF_SCALEWAY_SECURITY_GROUP",
        rel_direction_right=True,
    ) == {
        ("aaaa1111-2222-4820-b8d6-0eef10cfcd6d", TEST_SG_ID),
        ("bbbb2222-3333-4820-b8d6-0eef10cfcd6d", TEST_SG_ID),
    }

    # Assert SecurityGroup is linked to the instance it protects
    assert check_rels(
        neo4j_session,
        "ScalewayInstance",
        "id",
        "ScalewaySecurityGroup",
        "id",
        "MEMBER_OF_SCALEWAY_SECURITY_GROUP",
        rel_direction_right=True,
    ) == {(TEST_INSTANCE_ID, TEST_SG_ID)}
