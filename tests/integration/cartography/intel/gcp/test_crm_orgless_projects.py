"""
Integration tests for GCP orgless projects (projects without parent org or folder).
"""

from unittest.mock import patch

import cartography.intel.gcp
import cartography.intel.gcp.crm.projects
from cartography.config import Config
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789

# Test data for orgless projects
ORGLESS_PROJECTS_DATA = [
    {
        "projectId": "no-parent-project",
        "projectNumber": "479667239352",
        "name": "No Parent Project",
        "lifecycleState": "ACTIVE",
    },
    {
        "projectId": "standalone-project",
        "projectNumber": "987654321098",
        "name": "Standalone Project",
        "lifecycleState": "ACTIVE",
    },
]


def test_sync_orgless_gcp_projects(neo4j_session):
    """
    Test that orgless GCP projects are properly synced.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Mock the get_orgless_gcp_projects to return test data
    with patch.object(
        cartography.intel.gcp.crm.projects,
        "get_orgless_gcp_projects",
        return_value=ORGLESS_PROJECTS_DATA,
    ):
        # Sync orgless projects
        projects = cartography.intel.gcp.crm.projects.sync_orgless_gcp_projects(
            neo4j_session,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG},
        )

    # Verify projects were returned
    assert len(projects) == 2

    # Verify nodes were created with GCPProject label
    nodes = check_nodes(neo4j_session, "GCPProject", ["id"])
    assert nodes == {
        ("no-parent-project",),
        ("standalone-project",),
    }

    # Verify properties
    nodes_with_props = neo4j_session.run(
        """
        MATCH (p:GCPProject)
        RETURN p.id as id, p.displayname as name, p.projectnumber as number
        ORDER BY p.id
        """
    ).data()

    assert nodes_with_props == [
        {
            "id": "no-parent-project",
            "name": "No Parent Project",
            "number": "479667239352",
        },
        {
            "id": "standalone-project",
            "name": "Standalone Project",
            "number": "987654321098",
        },
    ]


def test_orgless_projects_no_parent_relationships(neo4j_session):
    """
    Test that orgless projects don't have parent relationships to orgs or folders.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Create an org and folder that shouldn't be related
    neo4j_session.run(
        """
        CREATE (o:GCPOrganization {id: 'organizations/123456', lastupdated: $update_tag})
        CREATE (f:GCPFolder {id: 'folders/987654', lastupdated: $update_tag})
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    # Sync orgless projects
    with patch.object(
        cartography.intel.gcp.crm.projects,
        "get_orgless_gcp_projects",
        return_value=ORGLESS_PROJECTS_DATA,
    ):
        cartography.intel.gcp.crm.projects.sync_orgless_gcp_projects(
            neo4j_session,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG},
        )

    # Verify no PARENT relationships exist for orgless projects
    parent_rels = neo4j_session.run(
        """
        MATCH (p:GCPProject)-[:PARENT]->()
        RETURN count(p) as count
        """
    ).single()["count"]
    assert parent_rels == 0

    # Verify no RESOURCE relationships exist from orgs to orgless projects
    resource_rels = neo4j_session.run(
        """
        MATCH (o:GCPOrganization)-[:RESOURCE]->(p:GCPProject)
        RETURN count(p) as count
        """
    ).single()["count"]
    assert resource_rels == 0


def test_cleanup_orgless_projects(neo4j_session):
    """
    Test that the orgless projects sync cleans up ALL old GCP projects.
    Note: With unscoped cleanup, this removes all stale GCPProject nodes,
    not just orgless ones. This is a side effect of using the standard
    cleanup mechanism for nodes without relationships.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # First sync: two orgless projects
    with patch.object(
        cartography.intel.gcp.crm.projects,
        "get_orgless_gcp_projects",
        return_value=ORGLESS_PROJECTS_DATA,
    ):
        cartography.intel.gcp.crm.projects.sync_orgless_gcp_projects(
            neo4j_session,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG},
        )

    # Verify both projects exist
    assert len(check_nodes(neo4j_session, "GCPProject", ["id"])) == 2

    # Add an org-based project with old update tag (simulating orphaned project from an org)
    neo4j_session.run(
        """
        CREATE (p:GCPProject {
            id: 'orphaned-org-project',
            parent_org: 'organizations/999',
            lastupdated: $old_tag
        })
        """,
        old_tag=TEST_UPDATE_TAG,
    )

    # Verify we now have 3 projects
    assert len(check_nodes(neo4j_session, "GCPProject", ["id"])) == 3

    # Second sync: only one orgless project remains
    remaining_project = [ORGLESS_PROJECTS_DATA[0]]  # Only first project
    with patch.object(
        cartography.intel.gcp.crm.projects,
        "get_orgless_gcp_projects",
        return_value=remaining_project,
    ):
        cartography.intel.gcp.crm.projects.sync_orgless_gcp_projects(
            neo4j_session,
            TEST_UPDATE_TAG + 1,
            {"UPDATE_TAG": TEST_UPDATE_TAG + 1},
        )

    # Verify only the current orgless project remains
    # The unscoped cleanup removes ALL stale GCPProject nodes
    nodes = check_nodes(neo4j_session, "GCPProject", ["id"])
    assert nodes == {
        ("no-parent-project",)
    }, f"Should remove ALL stale GCPProject nodes. Found: {nodes}"


@patch.object(
    cartography.intel.gcp,
    "_sync_project_resources",
    return_value=None,  # Skip resource sync for this test
)
def test_full_ingestion_with_orgless_projects(mock_sync_resources, neo4j_session):
    """
    Test that orgless projects are properly ingested alongside org-based projects
    in the full GCP ingestion flow.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Test data
    org_data = [
        {
            "name": "organizations/123456",
            "displayName": "Test Org",
            "lifecycleState": "ACTIVE",
        },
    ]
    org_project_data = [
        {
            "projectId": "org-project",
            "projectNumber": "111111",
            "name": "Org Project",
            "lifecycleState": "ACTIVE",
            "parent": "organizations/123456",
        },
    ]

    # Mock the various fetch functions
    with (
        patch.object(
            cartography.intel.gcp.crm.orgs,
            "get_gcp_organizations",
            return_value=org_data,
        ),
        patch.object(
            cartography.intel.gcp.crm.folders,
            "get_gcp_folders",
            return_value=[],
        ),
        patch.object(
            cartography.intel.gcp.crm.projects,
            "get_gcp_projects",
            return_value=org_project_data,
        ),
        patch.object(
            cartography.intel.gcp.crm.projects,
            "get_orgless_gcp_projects",
            return_value=ORGLESS_PROJECTS_DATA,
        ),
    ):
        config = Config(
            neo4j_uri="bolt://localhost:7687",
            update_tag=TEST_UPDATE_TAG,
        )
        cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

    # Verify all projects exist
    all_projects = check_nodes(neo4j_session, "GCPProject", ["id"])
    assert all_projects == {
        ("no-parent-project",),
        ("standalone-project",),
        ("org-project",),
    }

    # Verify org project has parent relationship
    org_project_parents = neo4j_session.run(
        """
        MATCH (p:GCPProject {id: 'org-project'})-[:PARENT]->(o:GCPOrganization)
        RETURN o.id as org_id
        """
    ).data()
    assert len(org_project_parents) == 1
    assert org_project_parents[0]["org_id"] == "organizations/123456"

    # Verify orgless projects have no parent relationships
    orgless_parents = neo4j_session.run(
        """
        MATCH (p:GCPProject)-[:PARENT]->()
        WHERE p.id IN ['no-parent-project', 'standalone-project']
        RETURN count(p) as count
        """
    ).single()["count"]
    assert orgless_parents == 0
