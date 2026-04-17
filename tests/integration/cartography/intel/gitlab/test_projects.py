"""Integration tests for GitLab projects module."""

import json

from cartography.intel.gitlab.projects import load_projects
from tests.data.gitlab.projects import TEST_GITLAB_URL
from tests.data.gitlab.projects import TEST_ORG_ID
from tests.data.gitlab.projects import TRANSFORMED_PROJECTS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_URL = "https://gitlab.example.com/myorg"


def _create_test_organization(neo4j_session):
    """Create test GitLabOrganization node."""
    neo4j_session.run(
        """
        MERGE (org:GitLabOrganization{id: $org_id})
        ON CREATE SET org.firstseen = timestamp()
        SET org.lastupdated = $update_tag,
            org.name = 'myorg',
            org.web_url = $org_url,
            org.gitlab_url = $gitlab_url
        """,
        org_id=TEST_ORG_ID,
        org_url=TEST_ORG_URL,
        gitlab_url=TEST_GITLAB_URL,
        update_tag=TEST_UPDATE_TAG,
    )


def _create_test_groups(neo4j_session):
    """Create test GitLabGroup nodes for nested groups."""
    groups = [
        {
            "id": 20,
            "name": "Platform",
        },
        {
            "id": 30,
            "name": "Apps",
        },
    ]
    for group in groups:
        neo4j_session.run(
            """
            MERGE (g:GitLabGroup{id: $id})
            ON CREATE SET g.firstseen = timestamp()
            SET g.lastupdated = $update_tag,
                g.name = $name,
                g.gitlab_url = $gitlab_url
            """,
            id=group["id"],
            name=group["name"],
            gitlab_url=TEST_GITLAB_URL,
            update_tag=TEST_UPDATE_TAG,
        )


def test_load_gitlab_projects_nodes(neo4j_session):
    """Test that GitLab projects are loaded correctly into Neo4j."""
    # Arrange
    _create_test_organization(neo4j_session)

    # Act
    load_projects(
        neo4j_session,
        TRANSFORMED_PROJECTS,
        TEST_ORG_ID,
        TEST_GITLAB_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check that project nodes exist
    expected_nodes = {
        (123, "awesome-project"),
        (456, "backend-service"),
        (789, "frontend-app"),
    }
    assert check_nodes(neo4j_session, "GitLabProject", ["id", "name"]) == expected_nodes


def test_load_gitlab_projects_to_organization_relationships(neo4j_session):
    """Test that RESOURCE relationships to organization are created."""
    # Arrange
    _create_test_organization(neo4j_session)

    # Act
    load_projects(
        neo4j_session,
        TRANSFORMED_PROJECTS,
        TEST_ORG_ID,
        TEST_GITLAB_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check RESOURCE relationships from Organization to Project
    expected = {
        (TEST_ORG_ID, 123),
        (TEST_ORG_ID, 456),
        (TEST_ORG_ID, 789),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabOrganization",
            "id",
            "GitLabProject",
            "id",
            "RESOURCE",
        )
        == expected
    )


def test_load_gitlab_projects_to_group_relationships(neo4j_session):
    """Test that CAN_ACCESS relationships to nested groups are created."""
    # Arrange
    _create_test_organization(neo4j_session)
    _create_test_groups(neo4j_session)

    # Act
    load_projects(
        neo4j_session,
        TRANSFORMED_PROJECTS,
        TEST_ORG_ID,
        TEST_GITLAB_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check CAN_ACCESS relationships from Group to Project
    # Only projects in nested groups should have this relationship
    expected = {
        (20, 456),
        (30, 789),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabGroup",
            "id",
            "GitLabProject",
            "id",
            "CAN_ACCESS",
        )
        == expected
    )


def test_load_gitlab_projects_properties(neo4j_session):
    """Test that project properties are loaded correctly."""
    # Arrange
    _create_test_organization(neo4j_session)

    # Act
    load_projects(
        neo4j_session,
        TRANSFORMED_PROJECTS,
        TEST_ORG_ID,
        TEST_GITLAB_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check that all project properties are loaded correctly
    expected_nodes = {
        (
            123,
            "awesome-project",
            "private",
            "main",
            False,
        ),
        (
            456,
            "backend-service",
            "internal",
            "master",
            False,
        ),
        (
            789,
            "frontend-app",
            "public",
            "main",
            False,
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "GitLabProject",
            ["id", "name", "visibility", "default_branch", "archived"],
        )
        == expected_nodes
    )


def test_load_gitlab_projects_languages_property(neo4j_session):
    """Test that languages property is stored as JSON on projects."""
    # Arrange
    _create_test_organization(neo4j_session)

    # Act
    load_projects(
        neo4j_session,
        TRANSFORMED_PROJECTS,
        TEST_ORG_ID,
        TEST_GITLAB_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check that languages property is stored correctly
    result = neo4j_session.run(
        """
        MATCH (p:GitLabProject)
        WHERE p.id = 123
        RETURN p.languages as languages
        """,
    )
    record = result.single()
    languages = json.loads(record["languages"])
    assert languages == {"Python": 65.5, "JavaScript": 34.5}

    # Check another project
    result = neo4j_session.run(
        """
        MATCH (p:GitLabProject)
        WHERE p.id = 456
        RETURN p.languages as languages
        """,
    )
    record = result.single()
    languages = json.loads(record["languages"])
    assert languages == {"Go": 85.0, "Shell": 15.0}
