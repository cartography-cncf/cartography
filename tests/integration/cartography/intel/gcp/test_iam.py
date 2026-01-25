from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.iam
import tests.data.gcp.iam
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_PROJECT_ID = "project-abc"
TEST_ORG_ID = "organizations/123456789012"
TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMS = {
    "PROJECT_ID": TEST_PROJECT_ID,
    "ORG_RESOURCE_NAME": TEST_ORG_ID,
    "UPDATE_TAG": TEST_UPDATE_TAG,
}


def _create_test_project(neo4j_session, project_id: str, update_tag: int):
    """Helper to create a GCPProject node for testing."""
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id:$ProjectId})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $gcp_update_tag
        """,
        ProjectId=project_id,
        gcp_update_tag=update_tag,
    )


def _create_test_organization(neo4j_session, org_id: str, update_tag: int):
    """Helper to create a GCPOrganization node for testing."""
    neo4j_session.run(
        """
        MERGE (o:GCPOrganization{id:$OrgId})
        ON CREATE SET o.firstseen = timestamp()
        SET o.lastupdated = $gcp_update_tag
        """,
        OrgId=org_id,
        gcp_update_tag=update_tag,
    )


@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_service_accounts",
    return_value=tests.data.gcp.iam.LIST_SERVICE_ACCOUNTS_RESPONSE["accounts"],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_project_custom_roles",
    return_value=tests.data.gcp.iam.LIST_PROJECT_CUSTOM_ROLES_RESPONSE["roles"],
)
def test_sync_gcp_iam_project_roles(
    _mock_get_project_roles, _mock_get_sa, neo4j_session
):
    """Test sync() loads GCP IAM project-level custom roles correctly."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    _create_test_organization(neo4j_session, TEST_ORG_ID, TEST_UPDATE_TAG)

    cartography.intel.gcp.iam.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify only project-level custom roles are created
    assert check_nodes(neo4j_session, "GCPRole", ["id"]) == {
        ("projects/project-abc/roles/customRole1",),
        ("projects/project-abc/roles/customRole2",),
    }


@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_service_accounts",
    return_value=tests.data.gcp.iam.LIST_SERVICE_ACCOUNTS_RESPONSE["accounts"],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_project_custom_roles",
    return_value=tests.data.gcp.iam.LIST_PROJECT_CUSTOM_ROLES_RESPONSE["roles"],
)
def test_sync_gcp_iam_service_accounts(
    _mock_get_project_roles, _mock_get_sa, neo4j_session
):
    """Test sync() loads GCP IAM service accounts correctly."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    _create_test_organization(neo4j_session, TEST_ORG_ID, TEST_UPDATE_TAG)

    cartography.intel.gcp.iam.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify service account nodes
    assert check_nodes(neo4j_session, "GCPServiceAccount", ["id"]) == {
        ("112233445566778899",),
        ("998877665544332211",),
    }


@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_service_accounts",
    return_value=tests.data.gcp.iam.LIST_SERVICE_ACCOUNTS_RESPONSE["accounts"],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_project_custom_roles",
    return_value=tests.data.gcp.iam.LIST_PROJECT_CUSTOM_ROLES_RESPONSE["roles"],
)
def test_sync_gcp_iam_project_role_relationships(
    _mock_get_project_roles, _mock_get_sa, neo4j_session
):
    """Test sync() creates correct relationships for project-level custom roles.

    Project-level custom roles are sub-resources of their project, not the organization.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    cartography.intel.gcp.iam.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify project -> role RESOURCE relationship (sub_resource)
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPRole",
        "name",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_PROJECT_ID, "projects/project-abc/roles/customRole1"),
        (TEST_PROJECT_ID, "projects/project-abc/roles/customRole2"),
    }

    # Verify no organization -> role relationship for project-level roles
    assert (
        check_rels(
            neo4j_session,
            "GCPOrganization",
            "id",
            "GCPRole",
            "name",
            "RESOURCE",
            rel_direction_right=True,
        )
        == set()
    )


@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_service_accounts",
    return_value=tests.data.gcp.iam.LIST_SERVICE_ACCOUNTS_RESPONSE["accounts"],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_project_custom_roles",
    return_value=[],
)
def test_sync_gcp_iam_service_account_relationships(
    _mock_get_project_roles, _mock_get_sa, neo4j_session
):
    """Test sync() creates correct relationships for GCP IAM service accounts."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    _create_test_organization(neo4j_session, TEST_ORG_ID, TEST_UPDATE_TAG)

    cartography.intel.gcp.iam.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify project -> service account RESOURCE relationship
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPServiceAccount",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_PROJECT_ID, "112233445566778899"),
        (TEST_PROJECT_ID, "998877665544332211"),
    }


@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_predefined_roles",
    return_value=tests.data.gcp.iam.LIST_PREDEFINED_ROLES_RESPONSE["roles"],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_org_roles",
    return_value=tests.data.gcp.iam.LIST_ORG_ROLES_RESPONSE["roles"],
)
def test_sync_org_iam_roles(_mock_get_org_roles, _mock_get_predefined, neo4j_session):
    """Test sync_org_iam() loads organization-level IAM roles correctly."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_organization(neo4j_session, TEST_ORG_ID, TEST_UPDATE_TAG)

    cartography.intel.gcp.iam.sync_org_iam(
        neo4j_session,
        MagicMock(),
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify all org-level roles are created (predefined + custom org roles)
    assert check_nodes(neo4j_session, "GCPRole", ["id"]) == {
        # Basic/predefined roles
        ("roles/owner",),
        ("roles/editor",),
        ("roles/viewer",),
        ("roles/iam.securityAdmin",),
        # Custom org roles
        ("organizations/123456789012/roles/customOrgRole1",),
        ("organizations/123456789012/roles/customOrgRole2",),
    }


@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_predefined_roles",
    return_value=tests.data.gcp.iam.LIST_PREDEFINED_ROLES_RESPONSE["roles"],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_org_roles",
    return_value=tests.data.gcp.iam.LIST_ORG_ROLES_RESPONSE["roles"],
)
def test_sync_org_iam_role_relationships(
    _mock_get_org_roles, _mock_get_predefined, neo4j_session
):
    """Test sync_org_iam() creates correct relationships for org-level roles."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_organization(neo4j_session, TEST_ORG_ID, TEST_UPDATE_TAG)

    cartography.intel.gcp.iam.sync_org_iam(
        neo4j_session,
        MagicMock(),
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify organization -> role RESOURCE relationship
    assert check_rels(
        neo4j_session,
        "GCPOrganization",
        "id",
        "GCPRole",
        "name",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ORG_ID, "roles/owner"),
        (TEST_ORG_ID, "roles/editor"),
        (TEST_ORG_ID, "roles/viewer"),
        (TEST_ORG_ID, "roles/iam.securityAdmin"),
        (TEST_ORG_ID, "organizations/123456789012/roles/customOrgRole1"),
        (TEST_ORG_ID, "organizations/123456789012/roles/customOrgRole2"),
    }


@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_predefined_roles",
    return_value=tests.data.gcp.iam.LIST_PREDEFINED_ROLES_RESPONSE["roles"],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_org_roles",
    return_value=tests.data.gcp.iam.LIST_ORG_ROLES_RESPONSE["roles"],
)
def test_sync_org_iam_role_scope_property(
    _mock_get_org_roles, _mock_get_predefined, neo4j_session
):
    """Test sync_org_iam() sets the scope property correctly on roles."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_organization(neo4j_session, TEST_ORG_ID, TEST_UPDATE_TAG)

    cartography.intel.gcp.iam.sync_org_iam(
        neo4j_session,
        MagicMock(),
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify scope property is set correctly
    result = neo4j_session.run(
        """
        MATCH (r:GCPRole)
        RETURN r.name as name, r.scope as scope, r.role_type as role_type
        ORDER BY r.name
        """
    )
    roles = {
        record["name"]: (record["scope"], record["role_type"]) for record in result
    }

    # Basic roles should have GLOBAL scope and BASIC type
    assert roles["roles/owner"] == ("GLOBAL", "BASIC")
    assert roles["roles/editor"] == ("GLOBAL", "BASIC")
    assert roles["roles/viewer"] == ("GLOBAL", "BASIC")

    # Predefined roles should have GLOBAL scope and PREDEFINED type
    assert roles["roles/iam.securityAdmin"] == ("GLOBAL", "PREDEFINED")

    # Custom org roles should have ORGANIZATION scope and CUSTOM type
    assert roles["organizations/123456789012/roles/customOrgRole1"] == (
        "ORGANIZATION",
        "CUSTOM",
    )
    assert roles["organizations/123456789012/roles/customOrgRole2"] == (
        "ORGANIZATION",
        "CUSTOM",
    )


@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_service_accounts",
    return_value=[],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_project_custom_roles",
    return_value=tests.data.gcp.iam.LIST_PROJECT_CUSTOM_ROLES_RESPONSE["roles"],
)
def test_sync_project_role_scope_property(
    _mock_get_project_roles, _mock_get_sa, neo4j_session
):
    """Test sync() sets the scope property correctly on project custom roles."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    _create_test_organization(neo4j_session, TEST_ORG_ID, TEST_UPDATE_TAG)

    cartography.intel.gcp.iam.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify scope property is set correctly
    result = neo4j_session.run(
        """
        MATCH (r:GCPRole)
        RETURN r.name as name, r.scope as scope, r.role_type as role_type
        ORDER BY r.name
        """
    )
    roles = {
        record["name"]: (record["scope"], record["role_type"]) for record in result
    }

    # Custom project roles should have PROJECT scope and CUSTOM type
    assert roles["projects/project-abc/roles/customRole1"] == ("PROJECT", "CUSTOM")
    assert roles["projects/project-abc/roles/customRole2"] == ("PROJECT", "CUSTOM")
