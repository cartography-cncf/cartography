from unittest.mock import patch

import requests

import cartography.intel.salesforce.organization
import cartography.intel.salesforce.permission_sets
import cartography.intel.salesforce.profiles
import cartography.intel.salesforce.users
import tests.data.salesforce.people
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_INSTANCE_URL = "https://simpson.my.salesforce.com"
TEST_ORG_ID = "00Dxx0000001gPLEAY"


@patch.object(
    cartography.intel.salesforce.users,
    "get_permission_set_assignments",
    return_value=tests.data.salesforce.people.SALESFORCE_PERMISSION_SET_ASSIGNMENTS,
)
@patch.object(
    cartography.intel.salesforce.users,
    "get",
    return_value=tests.data.salesforce.people.SALESFORCE_USERS,
)
@patch.object(
    cartography.intel.salesforce.permission_sets,
    "get",
    return_value=tests.data.salesforce.people.SALESFORCE_PERMISSION_SETS,
)
@patch.object(
    cartography.intel.salesforce.profiles,
    "get",
    return_value=tests.data.salesforce.people.SALESFORCE_PROFILES,
)
@patch.object(
    cartography.intel.salesforce.organization,
    "get",
    return_value=tests.data.salesforce.people.SALESFORCE_ORGANIZATION,
)
def test_sync_salesforce_people(
    _mock_org,
    _mock_profiles,
    _mock_permission_sets,
    _mock_users,
    _mock_assignments,
    neo4j_session,
):
    """Drive the full people-and-permissions sync and assert nodes + relationships."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "INSTANCE_URL": TEST_INSTANCE_URL,
    }

    # Act — mirror start_salesforce_ingestion's dispatch order.
    org_id = cartography.intel.salesforce.organization.sync(
        neo4j_session, api_session, common_job_parameters
    )
    common_job_parameters["ORG_ID"] = org_id
    cartography.intel.salesforce.profiles.sync(
        neo4j_session, api_session, common_job_parameters
    )
    cartography.intel.salesforce.permission_sets.sync(
        neo4j_session, api_session, common_job_parameters
    )
    cartography.intel.salesforce.users.sync(
        neo4j_session, api_session, common_job_parameters
    )

    # Assert — nodes
    assert org_id == TEST_ORG_ID
    assert check_nodes(neo4j_session, "SalesforceOrganization", ["id", "name"]) == {
        (TEST_ORG_ID, "Simpson Corp"),
    }
    assert check_nodes(neo4j_session, "SalesforceProfile", ["id", "name"]) == {
        ("00exx000000Admin", "System Administrator"),
        ("00exx000000Stand", "Standard User"),
    }
    assert check_nodes(neo4j_session, "SalesforcePermissionSet", ["id", "name"]) == {
        ("0PSxx00000Sales", "Sales_Access"),
        ("0PSxx00000Repor", "Report_Builder"),
    }
    assert check_nodes(neo4j_session, "SalesforceUser", ["id", "username"]) == {
        ("005xx0000Marge", "mbsimpson@simpson.corp"),
        ("005xx0000Homer", "hjsimpson@simpson.corp"),
    }

    # Assert — ontology extra labels were applied
    assert check_nodes(neo4j_session, "UserAccount", ["id"]) == {
        ("005xx0000Marge",),
        ("005xx0000Homer",),
    }
    assert check_nodes(neo4j_session, "PermissionRole", ["id"]) == {
        ("00exx000000Admin",),
        ("00exx000000Stand",),
        ("0PSxx00000Sales",),
        ("0PSxx00000Repor",),
    }

    # Assert — every node is scoped to the org via RESOURCE
    for label in (
        "SalesforceUser",
        "SalesforceProfile",
        "SalesforcePermissionSet",
    ):
        rels = check_rels(
            neo4j_session,
            "SalesforceOrganization",
            "id",
            label,
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        assert {org for org, _ in rels} == {TEST_ORG_ID}

    # Assert — User -[:HAS_PROFILE]-> Profile
    assert check_rels(
        neo4j_session,
        "SalesforceUser",
        "id",
        "SalesforceProfile",
        "id",
        "HAS_PROFILE",
        rel_direction_right=True,
    ) == {
        ("005xx0000Marge", "00exx000000Admin"),
        ("005xx0000Homer", "00exx000000Stand"),
    }

    # Assert — User -[:HAS_PERMISSION_SET]-> PermissionSet (many-to-many)
    assert check_rels(
        neo4j_session,
        "SalesforceUser",
        "id",
        "SalesforcePermissionSet",
        "id",
        "HAS_PERMISSION_SET",
        rel_direction_right=True,
    ) == {
        ("005xx0000Marge", "0PSxx00000Sales"),
        ("005xx0000Marge", "0PSxx00000Repor"),
        ("005xx0000Homer", "0PSxx00000Sales"),
    }
