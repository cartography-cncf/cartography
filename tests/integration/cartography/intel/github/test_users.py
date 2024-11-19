from unittest.mock import patch

import cartography.intel.github.users
from tests.data.github.users import GITHUB_ENTERPRISE_OWNER_DATA
from tests.data.github.users import GITHUB_ORG_DATA
from tests.data.github.users import GITHUB_USER_DATA

TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {'UPDATE_TAG': TEST_UPDATE_TAG}
TEST_GITHUB_URL = GITHUB_ORG_DATA['url']
TEST_GITHUB_ORG = GITHUB_ORG_DATA['login']
FAKE_API_KEY = 'asdf'


@patch.object(cartography.intel.github.users, 'get_users', return_value=GITHUB_USER_DATA)
@patch.object(cartography.intel.github.users, 'get_enterprise_owners', return_value=GITHUB_ENTERPRISE_OWNER_DATA)
def test_sync(mock_owners, mock_users, neo4j_session):
    # Arrange
    # No need to 'arrange' data here.  The patched functions return all the data needed.

    # Act
    cartography.intel.github.users.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_GITHUB_ORG,
    )

    # Assert

    # Ensure users got loaded
    nodes = neo4j_session.run(
        """
        MATCH (g:GitHubUser) RETURN g.id, g.role;
        """,
    )
    expected_nodes = {
        ("https://example.com/hjsimpson", 'MEMBER'),
        ("https://example.com/lmsimpson", 'MEMBER'),
        ("https://example.com/mbsimpson", 'ADMIN'),
        ("https://example.com/kbroflovski", None),
    }
    actual_nodes = {
        (
            n['g.id'],
            n['g.role'],
        ) for n in nodes
    }
    assert actual_nodes == expected_nodes

    # Ensure users are connected to the expected organization
    nodes = neo4j_session.run(
        """
        MATCH(user:GitHubUser)-[r]->(org:GitHubOrganization)
        RETURN user.id, type(r), org.id
        """,
    )
    actual_nodes = {
        (
            n['user.id'],
            n['type(r)'],
            n['org.id'],
        ) for n in nodes
    }
    expected_nodes = {
        (
            'https://example.com/hjsimpson',
            'MEMBER_OF',
            'https://example.com/my_org',
        ), (
            'https://example.com/lmsimpson',
            'MEMBER_OF',
            'https://example.com/my_org',
        ), (
            'https://example.com/mbsimpson',
            'MEMBER_OF',
            'https://example.com/my_org',
        ), (
            'https://example.com/kbroflovski',
            'UNAFFILIATED',
            'https://example.com/my_org',
        ),
    }
    assert actual_nodes == expected_nodes

    # Ensure enterprise owners are identified
    nodes = neo4j_session.run(
        """
        MATCH (g:GitHubUser) RETURN g.id, g.is_enterprise_owner
        """,
    )
    expected_nodes = {
        ("https://example.com/hjsimpson", False),
        ("https://example.com/lmsimpson", True),
        ("https://example.com/mbsimpson", True),
        ("https://example.com/kbroflovski", True),
    }
    actual_nodes = {
        (
            n['g.id'],
            n['g.is_enterprise_owner'],
        ) for n in nodes
    }
    assert actual_nodes == expected_nodes

    # Ensure hasTwoFactorEnabled has not been improperly overwritten for enterprise owners
    nodes = neo4j_session.run(
        """
        MATCH (g:GitHubUser) RETURN g.id, g.has_2fa_enabled
        """,
    )
    expected_nodes = {
        ("https://example.com/hjsimpson", None),
        ("https://example.com/lmsimpson", None),
        ("https://example.com/mbsimpson", True),
        ("https://example.com/kbroflovski", None),
    }
    actual_nodes = {
        (
            n['g.id'],
            n['g.has_2fa_enabled'],
        ) for n in nodes
    }
    assert actual_nodes == expected_nodes
