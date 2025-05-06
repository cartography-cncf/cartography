from unittest.mock import patch

import cartography.intel.github.users
from cartography.models.github.users import GitHubOrganizationUserSchema
from tests.data.github.users import GITHUB_ENTERPRISE_OWNER_DATA
from tests.data.github.users import GITHUB_ORG_DATA
from tests.data.github.users import GITHUB_USER_DATA
from tests.data.github.users import GITHUB_USER_DATA_AT_TIMESTAMP_2
from tests.integration.util import check_rels
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {"UPDATE_TAG": TEST_UPDATE_TAG}
TEST_GITHUB_URL = GITHUB_ORG_DATA["url"]
TEST_GITHUB_ORG = GITHUB_ORG_DATA["login"]
FAKE_API_KEY = "asdf"


def _ensure_local_neo4j_has_test_data(neo4j_session):
    """
    Not needed for this test file, but used to set up users for other tests that need them
    """
    processed_affiliated_user_data, _ = cartography.intel.github.users.transform_users(
        GITHUB_USER_DATA[0],
        GITHUB_ENTERPRISE_OWNER_DATA[0],
        GITHUB_ORG_DATA,
    )
    cartography.intel.github.users.load_users(
        neo4j_session,
        GitHubOrganizationUserSchema(),
        processed_affiliated_user_data,
        GITHUB_ORG_DATA,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.github.users,
    "get_users",
    return_value=GITHUB_USER_DATA,
)
@patch.object(
    cartography.intel.github.users,
    "get_enterprise_owners",
    return_value=GITHUB_ENTERPRISE_OWNER_DATA,
)
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
    expected_nodes = {
        ("https://example.com/hjsimpson",),
        ("https://example.com/lmsimpson",),
        ("https://example.com/mbsimpson",),
        ("https://example.com/kbroflovski",),
    }
    assert check_nodes(
        neo4j_session,
        "GitHubUser",
        ["id"],
    ) == expected_nodes
    # Ensure the human nodes are created
    expected_nodes = {
        ("hjsimpson@example.com", "hjsimpson@example.com"),
        ("kbroflovski@example.com", "kbroflovski@example.com"),
        ("lmsimpson@example.com", "lmsimpson@example.com"),
        ("mbsimpson@example.com", "mbsimpson@example.com"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "Human",
            ["id", "email"],
        )
        == expected_nodes
    )

    # Ensure users are connected to the expected organization
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "id",
        "GitHubOrganization",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        ("https://example.com/hjsimpson", "https://example.com/my_org"),
        ("https://example.com/lmsimpson", "https://example.com/my_org"),
        ("https://example.com/mbsimpson", "https://example.com/my_org"),
    }
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "id",
        "GitHubOrganization",
        "id",
        "ADMIN_OF",
        rel_direction_right=True,
    ) == {
        ("https://example.com/mbsimpson", "https://example.com/my_org"),
    }
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "id",
        "GitHubOrganization",
        "id",
        "UNAFFILIATED",
        rel_direction_right=True,
    ) == {
        ("https://example.com/kbroflovski", "https://example.com/my_org"),
    }

    # Ensure enterprise owners are identified
    assert check_nodes(
        neo4j_session,
        "GitHubUser",
        ["id", "is_enterprise_owner"],
    ) == {
        ("https://example.com/hjsimpson", False),
        ("https://example.com/lmsimpson", True),
        ("https://example.com/mbsimpson", True),
        ("https://example.com/kbroflovski", True),
    }

    # Ensure hasTwoFactorEnabled has not been improperly overwritten for enterprise owners
    assert check_nodes(
        neo4j_session,
        "GitHubUser",
        ["id", "has_2fa_enabled"],
    ) == {
        ("https://example.com/hjsimpson", None),
        ("https://example.com/lmsimpson", None),
        ("https://example.com/mbsimpson", True),
        ("https://example.com/kbroflovski", None),
    }

    # Ensure users are linked to the correct human nodes
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "id",
        "Human",
        "email",
        "IDENTITY_GITHUB",
        rel_direction_right=False,
    ) == {
        ("https://example.com/hjsimpson", "hjsimpson@example.com"),
        ("https://example.com/lmsimpson", "lmsimpson@example.com"),
        ("https://example.com/mbsimpson", "mbsimpson@example.com"),
        ("https://example.com/kbroflovski", "kbroflovski@example.com"),
    }


@patch.object(
    cartography.intel.github.users,
    "get_users",
    side_effect=[GITHUB_USER_DATA, GITHUB_USER_DATA_AT_TIMESTAMP_2],
)
@patch.object(
    cartography.intel.github.users,
    "get_enterprise_owners",
    return_value=GITHUB_ENTERPRISE_OWNER_DATA,
)
def test_sync_with_cleanups(mock_owners, mock_users, neo4j_session):
    # Act
    # Sync once
    cartography.intel.github.users.sync(
        neo4j_session,
        {"UPDATE_TAG": 100},
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_GITHUB_ORG,
    )
    # Assert that the only admin is marge
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "id",
        "GitHubOrganization",
        "id",
        "ADMIN_OF",
    ) == {
        ("https://example.com/mbsimpson", "https://example.com/my_org"),
    }

    # Act: Sync a second time
    cartography.intel.github.users.sync(
        neo4j_session,
        {"UPDATE_TAG": 200},
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_GITHUB_ORG,
    )
    # Assert that Marge is no longer an ADMIN of the GitHub org and the admin is now Homer
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "id",
        "GitHubOrganization",
        "id",
        "ADMIN_OF",
    ) == {
        ("https://example.com/hjsimpson", "https://example.com/my_org"),
    }
