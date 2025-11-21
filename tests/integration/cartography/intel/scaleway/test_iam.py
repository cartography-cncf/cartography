from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.iam.apikeys
import cartography.intel.scaleway.iam.applications
import cartography.intel.scaleway.iam.groups
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
