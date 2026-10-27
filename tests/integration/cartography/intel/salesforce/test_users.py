from copy import deepcopy
from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.salesforce.organization
import cartography.intel.salesforce.profiles
import cartography.intel.salesforce.userroles
import cartography.intel.salesforce.users
import tests.data.salesforce.data as test_data
from tests.integration.cartography.intel.salesforce.test_organization import (
    _ensure_local_neo4j_has_test_organization,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
HOMER, MARGE = test_data.SALESFORCE_USERS
SANDBOX_MARGE = {**MARGE, "Username": "mbsimpson@simpson.corp.dev"}


def _common_job_parameters():
    return {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": test_data.ORG_ID}


def _ensure_local_neo4j_has_prod_and_sandbox_orgs(neo4j_session):
    for org in (
        test_data.SALESFORCE_ORGANIZATION,
        test_data.SALESFORCE_SANDBOX_ORGANIZATION,
    ):
        cartography.intel.salesforce.organization.load_organization(
            neo4j_session,
            cartography.intel.salesforce.organization.transform(dict(org)),
            TEST_UPDATE_TAG,
        )


def _sync_users(neo4j_session, org_id, users, update_tag):
    with patch.object(
        cartography.intel.salesforce.users, "get", return_value=deepcopy(users)
    ):
        cartography.intel.salesforce.users.sync(
            neo4j_session, Mock(), {"UPDATE_TAG": update_tag, "ORG_ID": org_id}
        )


@patch.object(
    cartography.intel.salesforce.users,
    "get",
    return_value=deepcopy(test_data.SALESFORCE_USERS),
)
def test_sync_salesforce_users(mock_get, neo4j_session):
    # Arrange: org + the role/profile nodes the user links to must exist first
    _ensure_local_neo4j_has_test_organization(neo4j_session)
    cartography.intel.salesforce.profiles.load_profiles(
        neo4j_session,
        cartography.intel.salesforce.profiles.transform(
            deepcopy(test_data.SALESFORCE_PROFILES), test_data.ORG_ID
        ),
        test_data.ORG_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.salesforce.userroles.load_user_roles(
        neo4j_session,
        cartography.intel.salesforce.userroles.transform(
            deepcopy(test_data.SALESFORCE_USER_ROLES), test_data.ORG_ID
        ),
        test_data.ORG_ID,
        TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.salesforce.users.sync(
        neo4j_session, Mock(), _common_job_parameters()
    )

    # Assert users exist
    assert check_nodes(neo4j_session, "SalesforceUser", ["salesforce_id", "email"]) == {
        ("005000000000001AAA", "hjsimpson@simpson.corp"),
        ("005000000000002AAA", "mbsimpson@simpson.corp"),
    }

    # Users belong to the org
    assert check_rels(
        neo4j_session,
        "SalesforceUser",
        "salesforce_id",
        "SalesforceOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("005000000000001AAA", test_data.ORG_ID),
        ("005000000000002AAA", test_data.ORG_ID),
    }

    # Users have a profile (canonical HAS_ROLE ontology edge)
    assert check_rels(
        neo4j_session,
        "SalesforceUser",
        "salesforce_id",
        "SalesforceProfile",
        "salesforce_id",
        "HAS_ROLE",
        rel_direction_right=True,
    ) == {
        ("005000000000001AAA", "00e000000000001AAA"),
        ("005000000000002AAA", "00e000000000002AAA"),
    }

    # Users are members of a role
    assert check_rels(
        neo4j_session,
        "SalesforceUser",
        "salesforce_id",
        "SalesforceUserRole",
        "salesforce_id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        ("005000000000001AAA", "00E000000000001AAA"),
        ("005000000000002AAA", "00E000000000002AAA"),
    }


def test_sandbox_user_with_a_production_record_id_is_its_own_node(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _ensure_local_neo4j_has_prod_and_sandbox_orgs(neo4j_session)

    # Act
    _sync_users(neo4j_session, test_data.ORG_ID, [MARGE], TEST_UPDATE_TAG)
    _sync_users(
        neo4j_session, test_data.SANDBOX_ORG_ID, [SANDBOX_MARGE], TEST_UPDATE_TAG
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "SalesforceUser",
        "username",
        "SalesforceOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("mbsimpson@simpson.corp", test_data.ORG_ID),
        ("mbsimpson@simpson.corp.dev", test_data.SANDBOX_ORG_ID),
    }


def test_cleanup_of_one_org_keeps_a_failed_orgs_user_with_the_same_record_id(
    neo4j_session,
):
    # Arrange: last run loaded Marge in production and in its sandbox.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _ensure_local_neo4j_has_prod_and_sandbox_orgs(neo4j_session)
    _sync_users(neo4j_session, test_data.ORG_ID, [HOMER, MARGE], TEST_UPDATE_TAG)
    _sync_users(
        neo4j_session, test_data.SANDBOX_ORG_ID, [SANDBOX_MARGE], TEST_UPDATE_TAG
    )

    # Act: Marge left production; the sandbox fails before its users sync.
    _sync_users(neo4j_session, test_data.ORG_ID, [HOMER], TEST_UPDATE_TAG + 1)

    # Assert
    assert check_rels(
        neo4j_session,
        "SalesforceUser",
        "username",
        "SalesforceOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("hjsimpson@simpson.corp", test_data.ORG_ID),
        ("mbsimpson@simpson.corp.dev", test_data.SANDBOX_ORG_ID),
    }
