import cartography.intel.gcp.iam
import tests.data.gcp.iam
from cartography.intel.gcp.iam import ParentType
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


TEST_PROJECT_ID = 'project-123'
TEST_ORG_ID = 'organizations/123456789'
TEST_UPDATE_TAG = 123456789


def _create_test_project(neo4j_session):
    """Create Test GCP Project with associated organization_id."""
    neo4j_session.run(
        """
        MERGE (project:GCPProject {id: $project_id})
        ON CREATE SET project.firstseen = timestamp()
        SET project.lastupdated = $update_tag,
            project.organization_id = $org_id
        """,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
        org_id=TEST_ORG_ID,
    )


def _create_test_org(neo4j_session):
    """Create Test GCP Organization"""
    neo4j_session.run(
        """
        MERGE (org:GCPOrganization {id: $org_id})
        ON CREATE SET org.firstseen = timestamp()
        SET org.lastupdated = $update_tag
        """,
        org_id=TEST_ORG_ID,
        update_tag=TEST_UPDATE_TAG,
    )


def test_load_gcp_org_roles(neo4j_session):
    """Test loading organization-level roles and cleanup behavior"""
    # Arrange: create the organization node.
    _create_test_org(neo4j_session)

    # Act: load organization roles.
    data = tests.data.gcp.iam.LIST_ORG_ROLES_RESPONSE['roles']
    cartography.intel.gcp.iam.load_gcp_roles(
        neo4j_session,
        data,
        "123456789",  # Org id without prefix.
        ParentType.ORGANIZATION,
        TEST_UPDATE_TAG,
    )

    # Assert: ensure the expected organization-level roles are present.
    expected_nodes = {
        ("roles/viewer",),
        ("organizations/123456789/roles/customOrgRole",),
    }
    assert check_nodes(neo4j_session, 'GCPRole', ['id']) == expected_nodes
    expected_org_rels = {
        (TEST_ORG_ID, "roles/viewer"),
        (TEST_ORG_ID, "organizations/123456789/roles/customOrgRole"),
    }
    assert check_rels(neo4j_session, 'GCPOrganization', 'id', 'GCPRole', 'name', 'RESOURCE') == expected_org_rels

    # Now simulate a new sync run with an updated update tag—stale nodes should be cleaned up.
    common_job_parameters = {
        'UPDATE_TAG': TEST_UPDATE_TAG + 1,  # New sync run tag.
        'ORGANIZATION_ID': TEST_ORG_ID,
    }
    cartography.intel.gcp.iam.cleanup(neo4j_session, common_job_parameters, ParentType.ORGANIZATION)

    # Assert cleanup: No GCPRole nodes remain since the old ones are now stale.
    assert check_nodes(neo4j_session, 'GCPRole', ['id']) == set()


def test_load_gcp_project_roles(neo4j_session):
    """Test loading project-level roles and cleanup behavior"""
    # Arrange: create organization and project nodes.
    _create_test_org(neo4j_session)
    _create_test_project(neo4j_session)
    data = tests.data.gcp.iam.LIST_PROJECT_ROLES_RESPONSE['roles']

    # Act: load project roles using job_parameters that include the ORGANIZATION_ID.
    job_parameters = {"ORGANIZATION_ID": TEST_ORG_ID, "PROJECT_ID": TEST_PROJECT_ID}
    cartography.intel.gcp.iam.load_gcp_roles(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        ParentType.PROJECT,
        TEST_UPDATE_TAG,
        job_parameters,
    )

    # Assert: ensure that only project-specific roles are present.
    expected_nodes = {
        ("projects/project-123/roles/customRole1",),
        ("projects/project-123/roles/customRole2",),
    }
    assert check_nodes(neo4j_session, 'GCPRole', ['id']) == expected_nodes
    expected_org_rels = {
        (TEST_ORG_ID, "projects/project-123/roles/customRole1"),
        (TEST_ORG_ID, "projects/project-123/roles/customRole2"),
    }
    assert check_rels(neo4j_session, 'GCPOrganization', 'id', 'GCPRole', 'name', 'RESOURCE') == expected_org_rels
    expected_project_rels = {
        (TEST_PROJECT_ID, "projects/project-123/roles/customRole1"),
        (TEST_PROJECT_ID, "projects/project-123/roles/customRole2"),
    }
    assert check_rels(neo4j_session, 'GCPProject', 'id', 'GCPRole', 'name', 'RESOURCE') == expected_project_rels

    # Now simulate a new sync run to clean up stale project roles.
    common_job_parameters = {
        'UPDATE_TAG': TEST_UPDATE_TAG + 1,
        'PROJECT_ID': TEST_PROJECT_ID,
        'ORGANIZATION_ID': TEST_ORG_ID,
    }
    cartography.intel.gcp.iam.cleanup(neo4j_session, common_job_parameters, ParentType.PROJECT)

    # Assert cleanup: All GCPRole nodes should be removed since they are now considered stale.
    assert check_nodes(neo4j_session, 'GCPRole', ['id']) == set()


def test_load_gcp_service_accounts(neo4j_session):
    # Arrange
    _create_test_project(neo4j_session)
    data = tests.data.gcp.iam.LIST_SERVICE_ACCOUNTS_RESPONSE['accounts']

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
    assert check_nodes(neo4j_session, 'GCPServiceAccount', ['id']) == expected_nodes

    expected_rels = {
        (TEST_PROJECT_ID, "112233445566778899"),
        (TEST_PROJECT_ID, "998877665544332211"),
    }
    assert check_rels(neo4j_session, 'GCPProject', 'id', 'GCPServiceAccount', 'id', 'RESOURCE') == expected_rels
