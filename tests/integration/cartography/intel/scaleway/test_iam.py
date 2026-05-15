from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.iam.apikeys
import cartography.intel.scaleway.iam.applications
import cartography.intel.scaleway.iam.groups
import cartography.intel.scaleway.iam.permissionsets
import cartography.intel.scaleway.iam.policies
import cartography.intel.scaleway.iam.users
import tests.data.scaleway.iam
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"


def _ensure_local_neo4j_has_test_users(neo4j_session):
    data = cartography.intel.scaleway.iam.users.transform_users(
        tests.data.scaleway.iam.SCALEWAY_USERS
    )
    cartography.intel.scaleway.iam.users.load_users(
        neo4j_session, data, TEST_ORG_ID, TEST_UPDATE_TAG
    )


def _ensure_local_neo4j_has_test_applications(neo4j_session):
    data = cartography.intel.scaleway.iam.applications.transform_applications(
        tests.data.scaleway.iam.SCALEWAY_APPLICATIONS
    )
    cartography.intel.scaleway.iam.applications.load_applications(
        neo4j_session, data, TEST_ORG_ID, TEST_UPDATE_TAG
    )


@patch.object(
    cartography.intel.scaleway.iam.users,
    "get",
    return_value=tests.data.scaleway.iam.SCALEWAY_USERS,
)
def test_load_scaleway_users(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)

    # Act
    cartography.intel.scaleway.iam.users.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert Users exist
    expected_nodes = {
        (
            "998cbe72-913f-4f55-8620-4b0f7655d343",
            "mbsimpson@simpson.corp",
        ),
        (
            "b49932b2-2faa-4c56-905e-ffac52f063dc",
            "hjsimpson@simpson.corp",
        ),
    }
    assert check_nodes(neo4j_session, "ScalewayUser", ["id", "email"]) == expected_nodes

    # Assert users are linked to the organization
    expected_rels = {
        (
            "998cbe72-913f-4f55-8620-4b0f7655d343",
            TEST_ORG_ID,
        ),
        (
            "b49932b2-2faa-4c56-905e-ffac52f063dc",
            TEST_ORG_ID,
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayUser",
            "id",
            "ScalewayOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )


@patch.object(
    cartography.intel.scaleway.iam.applications,
    "get",
    return_value=tests.data.scaleway.iam.SCALEWAY_APPLICATIONS,
)
def test_load_scaleway_applications(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)

    # Act
    cartography.intel.scaleway.iam.applications.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert Applications exist
    expected_nodes = {
        (
            "98300a5a-438e-45dc-8b34-07b1adc7c409",
            "Mail Sender",
        ),
        (
            "c92d472f-f916-4071-b076-c8907c83e016",
            "Terraform",
        ),
    }
    assert (
        check_nodes(neo4j_session, "ScalewayApplication", ["id", "name"])
        == expected_nodes
    )

    # Assert Organization exists
    assert check_nodes(neo4j_session, "ScalewayOrganization", ["id"]) == {
        (TEST_ORG_ID,)
    }

    # Assert applications are linked to the organization
    expected_rels = {
        (
            "98300a5a-438e-45dc-8b34-07b1adc7c409",
            TEST_ORG_ID,
        ),
        (
            "c92d472f-f916-4071-b076-c8907c83e016",
            TEST_ORG_ID,
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayApplication",
            "id",
            "ScalewayOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )


@patch.object(
    cartography.intel.scaleway.iam.groups,
    "get",
    return_value=tests.data.scaleway.iam.SCALEWAY_GROUPS,
)
def test_load_scaleway_groups(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)
    _ensure_local_neo4j_has_test_applications(neo4j_session)

    # Act
    cartography.intel.scaleway.iam.groups.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert Groups exist
    expected_nodes = {
        (
            "1f767996-f6f6-4b0e-a7b1-6a255e809ed6",
            "Administrators",
        )
    }
    assert check_nodes(neo4j_session, "ScalewayGroup", ["id", "name"]) == expected_nodes

    # Assert groups are linked to the organization
    expected_rels = {
        (
            "1f767996-f6f6-4b0e-a7b1-6a255e809ed6",
            TEST_ORG_ID,
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayGroup",
            "id",
            "ScalewayOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert users are linked to the group
    expected_user_rels = {
        (
            "998cbe72-913f-4f55-8620-4b0f7655d343",
            "1f767996-f6f6-4b0e-a7b1-6a255e809ed6",
        )
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayUser",
            "id",
            "ScalewayGroup",
            "id",
            "MEMBER_OF",
            rel_direction_right=True,
        )
        == expected_user_rels
    )
    # Assert applications are linked to the group
    expected_application_rels = {
        ("c92d472f-f916-4071-b076-c8907c83e016", "1f767996-f6f6-4b0e-a7b1-6a255e809ed6")
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayApplication",
            "id",
            "ScalewayGroup",
            "id",
            "MEMBER_OF",
            rel_direction_right=True,
        )
        == expected_application_rels
    )


@patch.object(
    cartography.intel.scaleway.iam.apikeys,
    "get",
    return_value=tests.data.scaleway.iam.SCALEWAY_APIKEYS,
)
def test_load_scaleway_api_keys(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)
    _ensure_local_neo4j_has_test_applications(neo4j_session)

    # Act
    cartography.intel.scaleway.iam.apikeys.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert API Keys exist
    expected_nodes = {
        (
            "SCWXXX",
            "terraform",
        ),
        (
            "SCWYYY",
            None,
        ),
    }
    assert (
        check_nodes(neo4j_session, "ScalewayApiKey", ["id", "description"])
        == expected_nodes
    )

    # Assert API keys are linked to the organization
    expected_rels = {
        (
            "SCWXXX",
            TEST_ORG_ID,
        ),
        (
            "SCWYYY",
            TEST_ORG_ID,
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayApiKey",
            "id",
            "ScalewayOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert API keys are linked to the users
    expected_user_rels = {
        (
            "SCWYYY",
            "b49932b2-2faa-4c56-905e-ffac52f063dc",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayApiKey",
            "id",
            "ScalewayUser",
            "id",
            "HAS",
            rel_direction_right=False,
        )
        == expected_user_rels
    )
    # Assert API keys are linked to the applications
    expected_application_rels = {
        (
            "SCWXXX",
            "c92d472f-f916-4071-b076-c8907c83e016",
        )
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayApiKey",
            "id",
            "ScalewayApplication",
            "id",
            "HAS",
            rel_direction_right=False,
        )
        == expected_application_rels
    )


@patch.object(
    cartography.intel.scaleway.iam.permissionsets,
    "get",
    return_value=tests.data.scaleway.iam.SCALEWAY_PERMISSION_SETS,
)
def test_load_scaleway_permission_sets(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)

    # Act
    cartography.intel.scaleway.iam.permissionsets.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert PermissionSets exist
    expected_nodes = {
        (
            "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "InstancesFullAccess",
            "projects",
        ),
        (
            "b2c3d4e5-f6a7-8901-bcde-f12345678901",
            "ObjectStorageReadOnly",
            "projects",
        ),
    }
    assert (
        check_nodes(
            neo4j_session, "ScalewayPermissionSet", ["id", "name", "scope_type"]
        )
        == expected_nodes
    )

    # Assert permission sets are linked to the organization
    expected_rels = {
        (
            "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            TEST_ORG_ID,
        ),
        (
            "b2c3d4e5-f6a7-8901-bcde-f12345678901",
            TEST_ORG_ID,
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayPermissionSet",
            "id",
            "ScalewayOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )


def _ensure_local_neo4j_has_test_groups(neo4j_session):
    data = cartography.intel.scaleway.iam.groups.transform_groups(
        tests.data.scaleway.iam.SCALEWAY_GROUPS
    )
    cartography.intel.scaleway.iam.groups.load_groups(
        neo4j_session, data, TEST_ORG_ID, TEST_UPDATE_TAG
    )


def _ensure_local_neo4j_has_test_policies(neo4j_session):
    data = cartography.intel.scaleway.iam.policies.transform_policies(
        tests.data.scaleway.iam.SCALEWAY_POLICIES
    )
    cartography.intel.scaleway.iam.policies.load_policies(
        neo4j_session, data, TEST_ORG_ID, TEST_UPDATE_TAG
    )


@patch.object(
    cartography.intel.scaleway.iam.policies,
    "get_rules",
    side_effect=[
        tests.data.scaleway.iam.SCALEWAY_RULES_POLICY_1,
        tests.data.scaleway.iam.SCALEWAY_RULES_POLICY_2,
    ],
)
@patch.object(
    cartography.intel.scaleway.iam.policies,
    "get_policies",
    return_value=tests.data.scaleway.iam.SCALEWAY_POLICIES,
)
def test_load_scaleway_policies(_mock_get_policies, _mock_get_rules, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)
    _ensure_local_neo4j_has_test_groups(neo4j_session)

    # Act
    cartography.intel.scaleway.iam.policies.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert Policies exist
    expected_nodes = {
        (
            "pol-11111111-1111-1111-1111-111111111111",
            "Admin Policy",
        ),
        (
            "pol-22222222-2222-2222-2222-222222222222",
            "Group Policy",
        ),
    }
    assert (
        check_nodes(neo4j_session, "ScalewayPolicy", ["id", "name"]) == expected_nodes
    )

    # Assert policies are linked to the organization
    expected_org_rels = {
        (
            "pol-11111111-1111-1111-1111-111111111111",
            TEST_ORG_ID,
        ),
        (
            "pol-22222222-2222-2222-2222-222222222222",
            TEST_ORG_ID,
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayPolicy",
            "id",
            "ScalewayOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_org_rels
    )

    # Assert policy applies to user
    expected_user_rels = {
        (
            "pol-11111111-1111-1111-1111-111111111111",
            "998cbe72-913f-4f55-8620-4b0f7655d343",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayPolicy",
            "id",
            "ScalewayUser",
            "id",
            "APPLIES_TO",
            rel_direction_right=True,
        )
        == expected_user_rels
    )

    # Assert policy applies to group
    expected_group_rels = {
        (
            "pol-22222222-2222-2222-2222-222222222222",
            "1f767996-f6f6-4b0e-a7b1-6a255e809ed6",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayPolicy",
            "id",
            "ScalewayGroup",
            "id",
            "APPLIES_TO",
            rel_direction_right=True,
        )
        == expected_group_rels
    )

    # Assert Rules exist
    expected_rule_nodes = {
        (
            "rule-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "projects",
        ),
        (
            "rule-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "projects",
        ),
    }
    assert (
        check_nodes(neo4j_session, "ScalewayRule", ["id", "permission_sets_scope_type"])
        == expected_rule_nodes
    )

    # Assert rules are linked to the organization
    expected_rule_org_rels = {
        (
            "rule-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            TEST_ORG_ID,
        ),
        (
            "rule-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            TEST_ORG_ID,
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayRule",
            "id",
            "ScalewayOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rule_org_rels
    )

    # Assert rules are linked to their policies
    expected_rule_policy_rels = {
        (
            "rule-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "pol-11111111-1111-1111-1111-111111111111",
        ),
        (
            "rule-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "pol-22222222-2222-2222-2222-222222222222",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayRule",
            "id",
            "ScalewayPolicy",
            "id",
            "HAS",
            rel_direction_right=False,
        )
        == expected_rule_policy_rels
    )

    # Assert rules are scoped to projects
    expected_rule_project_rels = {
        (
            "rule-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        ),
        (
            "rule-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayRule",
            "id",
            "ScalewayProject",
            "id",
            "SCOPED_TO",
            rel_direction_right=True,
        )
        == expected_rule_project_rels
    )
