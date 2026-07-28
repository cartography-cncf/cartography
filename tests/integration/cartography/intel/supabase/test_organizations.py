from unittest.mock import patch

import requests

import cartography.intel.supabase.organizations
import tests.data.supabase.organizations
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_SLUG = "simpson-corp"
TEST_BASE_URL = "https://api.fake-supabase.com"


def _ensure_local_neo4j_has_test_organizations(neo4j_session):
    cartography.intel.supabase.organizations.load_organizations(
        neo4j_session,
        cartography.intel.supabase.organizations.transform_organizations(
            tests.data.supabase.organizations.SUPABASE_ORGANIZATIONS,
            list(
                tests.data.supabase.organizations.SUPABASE_ORGANIZATION_DETAILS.values(),
            ),
        ),
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.supabase.organizations,
    "get_details",
    side_effect=lambda api_session, base_url, slug: (
        tests.data.supabase.organizations.SUPABASE_ORGANIZATION_DETAILS[slug]
    ),
)
@patch.object(
    cartography.intel.supabase.organizations,
    "get",
    return_value=tests.data.supabase.organizations.SUPABASE_ORGANIZATIONS,
)
def test_load_supabase_organizations(mock_get, mock_get_details, neo4j_session):
    """
    Ensure organizations are loaded with their plan details merged in.
    """
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
    }

    # Act
    organizations = cartography.intel.supabase.organizations.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert the sync returns the organizations for the caller to fan out over
    assert {o["slug"] for o in organizations} == {"simpson-corp", "burns-industries"}

    # Assert nodes are keyed by slug and carry the merged detail fields
    expected_nodes = {
        ("simpson-corp", "Simpson Corp", "pro"),
        ("burns-industries", "Burns Industries", "free"),
    }
    assert (
        check_nodes(neo4j_session, "SupabaseOrganization", ["id", "name", "plan"])
        == expected_nodes
    )


@patch.object(
    cartography.intel.supabase.organizations,
    "get_details",
    side_effect=lambda api_session, base_url, slug: (
        tests.data.supabase.organizations.SUPABASE_ORGANIZATION_DETAILS[slug]
    ),
)
@patch.object(
    cartography.intel.supabase.organizations,
    "get",
    return_value=tests.data.supabase.organizations.SUPABASE_ORGANIZATIONS,
)
def test_supabase_organizations_allowlist(mock_get, mock_get_details, neo4j_session):
    """
    Ensure --supabase-organizations restricts which organizations are synced.
    """
    # Arrange
    api_session = requests.Session()

    # Act
    organizations = cartography.intel.supabase.organizations.sync(
        neo4j_session,
        api_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "BASE_URL": TEST_BASE_URL},
        ["burns-industries"],
    )

    # Assert
    assert [o["slug"] for o in organizations] == ["burns-industries"]


@patch.object(
    cartography.intel.supabase.organizations,
    "get_members",
    return_value=tests.data.supabase.organizations.SUPABASE_ORGANIZATION_MEMBERS,
)
def test_load_supabase_organization_members(mock_get_members, neo4j_session):
    """
    Ensure members are loaded and attached to their organization.
    """
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_SLUG": TEST_ORG_SLUG,
    }
    _ensure_local_neo4j_has_test_organizations(neo4j_session)

    # Act
    cartography.intel.supabase.organizations.sync_members(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert members exist with their MFA state
    expected_nodes = {
        ("user-marge", "mbsimpson@simpson.corp", "Owner", True),
        ("user-homer", "hjsimpson@simpson.corp", "Developer", False),
    }
    assert (
        check_nodes(
            neo4j_session,
            "SupabaseOrganizationMember",
            ["id", "email", "role_name", "mfa_enabled"],
        )
        == expected_nodes
    )

    # Assert members are attached to the organization
    expected_rels = {
        ("user-marge", TEST_ORG_SLUG),
        ("user-homer", TEST_ORG_SLUG),
    }
    assert (
        check_rels(
            neo4j_session,
            "SupabaseOrganizationMember",
            "id",
            "SupabaseOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )


@patch.object(
    cartography.intel.supabase.organizations,
    "get_members",
    return_value=tests.data.supabase.organizations.SUPABASE_ORGANIZATION_MEMBERS,
)
def test_supabase_organization_member_ontology_labels(mock_get_members, neo4j_session):
    """
    Ensure the UserAccount semantic label and its _ont_* properties are applied.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)

    # Act
    cartography.intel.supabase.organizations.sync_members(
        neo4j_session,
        api_session,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "BASE_URL": TEST_BASE_URL,
            "ORG_SLUG": TEST_ORG_SLUG,
        },
    )

    # Assert
    record = neo4j_session.run(
        """
        MATCH (m:SupabaseOrganizationMember:UserAccount {id: 'user-marge'})
        RETURN m._ont_email AS email, m._ont_has_mfa AS has_mfa, m._ont_source AS source
        """,
    ).single()
    assert record["email"] == "mbsimpson@simpson.corp"
    assert record["has_mfa"] is True
    assert record["source"] == "supabase"
