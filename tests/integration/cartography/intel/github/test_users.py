from unittest.mock import patch

import cartography.intel.github.users
from cartography.models.github.users import GitHubOrganizationUserSchema
from tests.data.github.users import GITHUB_ENTERPRISE_OWNER_DATA
from tests.data.github.users import GITHUB_ORG_DATA
from tests.data.github.users import GITHUB_USER_DATA
from tests.data.github.users import GITHUB_USER_DATA_AT_TIMESTAMP_2
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {'UPDATE_TAG': TEST_UPDATE_TAG}
TEST_GITHUB_URL = GITHUB_ORG_DATA['url']
TEST_GITHUB_ORG = GITHUB_ORG_DATA['login']
FAKE_API_KEY = 'asdf'


def _ensure_local_neo4j_has_test_data(neo4j_session):
    """
    Not needed for this test file, but used to set up users for other tests that need them
    """
    processed_affiliated_user_data, _ = (
        cartography.intel.github.users.transform_users(
            GITHUB_USER_DATA[0], GITHUB_ENTERPRISE_OWNER_DATA[0], GITHUB_ORG_DATA,
        )
    )
    cartography.intel.github.users.load_users(
        neo4j_session,
        GitHubOrganizationUserSchema(),
        processed_affiliated_user_data,
        GITHUB_ORG_DATA,
        TEST_UPDATE_TAG,
    )


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

    # Ensure the expected users are there
    nodes = neo4j_session.run(
        """
        MATCH (g:GitHubUser) RETURN g.id;
        """,
    )
    expected_nodes = {
        ("https://example.com/hjsimpson",),
        ("https://example.com/lmsimpson",),
        ("https://example.com/mbsimpson",),
        ("https://example.com/kbroflovski",),
    }
    actual_nodes = {
        (
            n['g.id'],
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
            'https://example.com/mbsimpson',
            'ADMIN_OF',
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


@patch.object(
    cartography.intel.github.users,
    'get_users',
    side_effect=[GITHUB_USER_DATA, GITHUB_USER_DATA_AT_TIMESTAMP_2],
)
@patch.object(cartography.intel.github.users, 'get_enterprise_owners', return_value=GITHUB_ENTERPRISE_OWNER_DATA)
def test_sync_with_cleanups(mock_owners, mock_users, neo4j_session):
    # Act
    # Sync once
    cartography.intel.github.users.sync(
        neo4j_session,
        {'UPDATE_TAG': 100},
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_GITHUB_ORG,
    )
    # Assert that the only admin is marge
    assert check_rels(neo4j_session, 'GitHubUser', 'id', 'GitHubOrganization', 'id', 'ADMIN_OF') == {
        ('https://example.com/mbsimpson', 'https://example.com/my_org'),
    }

    # Act: Sync a second time
    cartography.intel.github.users.sync(
        neo4j_session,
        {'UPDATE_TAG': 200},
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_GITHUB_ORG,
    )
    # Assert that Marge is no longer an ADMIN of the GitHub org and the admin is now Homer
    assert check_rels(neo4j_session, 'GitHubUser', 'id', 'GitHubOrganization', 'id', 'ADMIN_OF') == {
        ('https://example.com/hjsimpson', 'https://example.com/my_org'),
    }
