import cartography.intel.gcp.iam
import tests.data.gcp.iam
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_PROJECT_ID = "project-123"
TEST_UPDATE_TAG = 123456789


def _create_test_project(neo4j_session):
    # Create Test GCP Project
    neo4j_session.run(
        """
        MERGE (project:GCPProject{id: $project_id})
        ON CREATE SET project.firstseen = timestamp()
        SET project.lastupdated = $update_tag
        """,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )


def test_load_gcp_roles(neo4j_session):
    # Arrange
    _create_test_project(neo4j_session)
    data = tests.data.gcp.iam.LIST_ROLES_RESPONSE["roles"]

    # Act
    cartography.intel.gcp.iam.load_gcp_roles(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected_nodes = {
        ("projects/project-123/roles/customRole1",),
        ("roles/editor",),
        ("projects/project-123/roles/customRole2",),
    }
    assert check_nodes(neo4j_session, "GCPRole", ["id"]) == expected_nodes

    # Check relationships
    expected_rels = {
        (TEST_PROJECT_ID, "projects/project-123/roles/customRole1"),
        (TEST_PROJECT_ID, "roles/editor"),
        (TEST_PROJECT_ID, "projects/project-123/roles/customRole2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "GCPProject",
            "id",
            "GCPRole",
            "name",
            "RESOURCE",
        )
        == expected_rels
    )


def test_load_gcp_service_accounts(neo4j_session):
    # Arrange
    _create_test_project(neo4j_session)
    data = tests.data.gcp.iam.LIST_SERVICE_ACCOUNTS_RESPONSE["accounts"]

    # Act
    cartography.intel.gcp.iam.load_gcp_service_accounts(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected_nodes = {
        ("112233445566778899",),
        ("998877665544332211",),
    }
    assert check_nodes(neo4j_session, "GCPServiceAccount", ["id"]) == expected_nodes

    # Check relationships
    expected_rels = {
        (TEST_PROJECT_ID, "112233445566778899"),
        (TEST_PROJECT_ID, "998877665544332211"),
    }
    assert (
        check_rels(
            neo4j_session,
            "GCPProject",
            "id",
            "GCPServiceAccount",
            "id",
            "RESOURCE",
        )
        == expected_rels
    )

def test_sync_gcp_iam(neo4j_session):
    """Integration test for sync() using static IAM test data."""
    
    _create_test_project(neo4j_session)

    def sa_execute():
        return tests.data.gcp.iam.LIST_SERVICE_ACCOUNTS_RESPONSE

    def custom_roles_execute():
        custom_roles = [
            role for role in tests.data.gcp.iam.LIST_ROLES_RESPONSE["roles"]
            if role["name"].startswith("projects/")
        ]
        return {"roles": custom_roles}

    def predefined_roles_execute():
        predefined_roles = [
            role for role in tests.data.gcp.iam.LIST_ROLES_RESPONSE["roles"]
            if role["name"].startswith("roles/")
        ]
        return {"roles": predefined_roles}

    def list_next(*args, **kwargs):
        return None

    # List methods that wrap the execute functions
    def sa_list(name):
        return type("Request", (), {"execute": sa_execute})()

    def custom_roles_list(parent):
        return type("Request", (), {"execute": custom_roles_execute})()

    def predefined_roles_list(view):
        return type("Request", (), {"execute": predefined_roles_execute})()

    # Builders for the API client
    def service_accounts():
        return type("ServiceAccounts", (), {
            "list": sa_list,
            "list_next": list_next,
        })()

    def project_roles():
        return type("ProjectRoles", (), {
            "list": custom_roles_list,
            "list_next": list_next,
        })()

    def projects():
        return type("Projects", (), {
            "serviceAccounts": service_accounts,
            "roles": project_roles,
        })()

    def roles():
        return type("Roles", (), {
            "list": predefined_roles_list,
            "list_next": list_next,
        })()

    iam_client = type("IAMClient", (), {
        "projects": projects,
        "roles": roles,
    })()

    common_job_parameters = {
        "PROJECT_ID": TEST_PROJECT_ID,
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    cartography.intel.gcp.iam.sync(
        neo4j_session,
        iam_client,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert: Roles
    expected_role_nodes = {
        ("projects/project-123/roles/customRole1",),
        ("roles/editor",),
        ("projects/project-123/roles/customRole2",),
    }
    assert check_nodes(neo4j_session, "GCPRole", ["id"]) == expected_role_nodes

    expected_role_rels = {
        (TEST_PROJECT_ID, "projects/project-123/roles/customRole1"),
        (TEST_PROJECT_ID, "roles/editor"),
        (TEST_PROJECT_ID, "projects/project-123/roles/customRole2"),
    }
    assert check_rels(
        neo4j_session,
        "GCPProject", "id",
        "GCPRole", "name",
        "RESOURCE",
    ) == expected_role_rels

    expected_sa_nodes = {
        ("112233445566778899",),
        ("998877665544332211",),
    }
    assert check_nodes(neo4j_session, "GCPServiceAccount", ["id"]) == expected_sa_nodes

    expected_sa_rels = {
        (TEST_PROJECT_ID, "112233445566778899"),
        (TEST_PROJECT_ID, "998877665544332211"),
    }
    assert check_rels(
        neo4j_session,
        "GCPProject", "id",
        "GCPServiceAccount", "id",
        "RESOURCE",
    ) == expected_sa_rels