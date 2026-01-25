from unittest.mock import patch

import cartography.intel.github.users
from cartography.models.github.users import GitHubOrganizationUserSchema
from tests.data.github.users import GITHUB_ENTERPRISE_OWNER_DATA
from tests.data.github.users import GITHUB_ORG_DATA
from tests.data.github.users import GITHUB_USER_DATA
from tests.data.github.users import GITHUB_USER_DATA_AT_TIMESTAMP_2
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

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

    # Assert - Verify GitHubUser nodes exist
    assert check_nodes(neo4j_session, "GitHubUser", ["id"]) == {
        ("https://github.com/hjsimpson",),
        ("https://github.com/lmsimpson",),
        ("https://github.com/mbsimpson",),
        ("https://github.com/kbroflovski",),
    }

    # Assert - Verify MEMBER_OF relationships
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "id",
        "GitHubOrganization",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        ("https://github.com/hjsimpson", "https://github.com/simpsoncorp"),
        ("https://github.com/lmsimpson", "https://github.com/simpsoncorp"),
        ("https://github.com/mbsimpson", "https://github.com/simpsoncorp"),
    }

    # Assert - Verify ADMIN_OF relationships
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "id",
        "GitHubOrganization",
        "id",
        "ADMIN_OF",
        rel_direction_right=True,
    ) == {
        ("https://github.com/mbsimpson", "https://github.com/simpsoncorp"),
    }

    # Assert - Verify UNAFFILIATED relationships
    assert check_rels(
        neo4j_session,
        "GitHubUser",
        "id",
        "GitHubOrganization",
        "id",
        "UNAFFILIATED",
        rel_direction_right=True,
    ) == {
        ("https://github.com/kbroflovski", "https://github.com/simpsoncorp"),
    }

    # Assert - Verify enterprise owners are identified
    assert check_nodes(neo4j_session, "GitHubUser", ["id", "is_enterprise_owner"]) == {
        ("https://github.com/hjsimpson", False),
        ("https://github.com/lmsimpson", True),
        ("https://github.com/mbsimpson", True),
        ("https://github.com/kbroflovski", True),
    }

    # Assert - Verify hasTwoFactorEnabled has not been improperly overwritten
    assert check_nodes(neo4j_session, "GitHubUser", ["id", "has_2fa_enabled"]) == {
        ("https://github.com/hjsimpson", None),
        ("https://github.com/lmsimpson", None),
        ("https://github.com/mbsimpson", True),
        ("https://github.com/kbroflovski", None),
    }

    # Assert - Verify organization_verified_domain_emails
    # Note: check_nodes returns tuples with lists converted, so we need a raw query for list values
    nodes = neo4j_session.run(
        """
        MATCH (g:GitHubUser) RETURN g.id, g.organization_verified_domain_emails
        """,
    )
    actual_emails = {
        n["g.id"]: n["g.organization_verified_domain_emails"] for n in nodes
    }
    expected_emails = {
        "https://github.com/hjsimpson": ["hjsimpson@burns.corp"],
        "https://github.com/lmsimpson": None,
        "https://github.com/mbsimpson": None,
        "https://github.com/kbroflovski": None,
    }
    assert actual_emails == expected_emails


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
        ("https://github.com/mbsimpson", "https://github.com/simpsoncorp"),
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
        ("https://github.com/hjsimpson", "https://github.com/simpsoncorp"),
    }
