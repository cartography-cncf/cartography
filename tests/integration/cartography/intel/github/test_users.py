import cartography.intel.github.users
from cartography.models.github.users import GitHubOrganizationUserSchema
from tests.data.github.users import GITHUB_ENTERPRISE_OWNER_DATA
from tests.data.github.users import GITHUB_ORG_DATA
from tests.data.github.users import GITHUB_SECOND_ORG_DATA
from tests.data.github.users import GITHUB_SECOND_ORG_USER_DATA
from tests.data.github.users import GITHUB_USER_DATA
from tests.data.github.users import GITHUB_USER_DATA_AT_TIMESTAMP_2
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {"UPDATE_TAG": TEST_UPDATE_TAG}


def _seed_organization(neo4j_session, org_data=GITHUB_ORG_DATA):
    """The GitHubOrganization node is written by the organization settings sync."""
    neo4j_session.run(
        "MERGE (org:GitHubOrganization {id: $url}) "
        "SET org.username = coalesce(org.username, $login)",
        url=org_data["url"],
        login=org_data["login"],
    )


def _node_organization_facts(neo4j_session, user_url):
    return neo4j_session.run(
        """
        MATCH (g:GitHubUser {id: $user_url})
        RETURN g{
            .has_2fa_enabled, ._ont_has_mfa, .is_enterprise_owner,
            .organization_verified_domain_emails, .normalized_emails
        } AS facts
        """,
        user_url=user_url,
    ).single()["facts"]


def _membership_organization_facts(neo4j_session, user_url):
    result = neo4j_session.run(
        """
        MATCH (:GitHubUser {id: $user_url})-[r:MEMBER_OF|UNAFFILIATED]->(org:GitHubOrganization)
        RETURN org.id AS org, r{
            .has_2fa_enabled, .is_enterprise_owner,
            .organization_verified_domain_emails, .normalized_emails
        } AS facts
        """,
        user_url=user_url,
    )
    return {row["org"]: row["facts"] for row in result}


def _ensure_local_neo4j_has_test_data(neo4j_session):
    """
    Not needed for this test file, but used to set up users for other tests that need them
    """
    _seed_organization(neo4j_session)
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


def test_sync(neo4j_session):
    # Arrange
    _seed_organization(neo4j_session)

    # Act
    cartography.intel.github.users.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        GITHUB_USER_DATA[0],
        GITHUB_ENTERPRISE_OWNER_DATA[0],
        GITHUB_ORG_DATA,
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
        "https://github.com/lmsimpson": [],
        "https://github.com/mbsimpson": ["mbsimpson@burns.corp"],
        "https://github.com/kbroflovski": [],
    }
    assert actual_emails == expected_emails


def test_sync_keeps_facts_that_another_organization_reports(neo4j_session):
    # Arrange
    _seed_organization(neo4j_session)
    _seed_organization(neo4j_session, GITHUB_SECOND_ORG_DATA)
    cartography.intel.github.users.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        GITHUB_USER_DATA[0],
        GITHUB_ENTERPRISE_OWNER_DATA[0],
        GITHUB_ORG_DATA,
    )

    # Act
    cartography.intel.github.users.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        GITHUB_SECOND_ORG_USER_DATA[0],
        [],
        GITHUB_SECOND_ORG_DATA,
    )

    # Assert
    assert _node_organization_facts(neo4j_session, "https://github.com/mbsimpson") == {
        "has_2fa_enabled": True,
        "_ont_has_mfa": True,
        "is_enterprise_owner": True,
        "organization_verified_domain_emails": ["mbsimpson@burns.corp"],
        "normalized_emails": ["mbsimpson@burns.corp", "mbsimpson@simpson.corp"],
    }
    assert _membership_organization_facts(
        neo4j_session, "https://github.com/mbsimpson"
    ) == {
        "https://github.com/simpsoncorp": {
            "has_2fa_enabled": True,
            "is_enterprise_owner": True,
            "organization_verified_domain_emails": ["mbsimpson@burns.corp"],
            "normalized_emails": ["mbsimpson@burns.corp", "mbsimpson@simpson.corp"],
        },
        "https://github.com/burnscorp": {
            "has_2fa_enabled": None,
            "is_enterprise_owner": False,
            "organization_verified_domain_emails": [],
            "normalized_emails": ["mbsimpson@simpson.corp"],
        },
    }


def test_sync_ignores_the_stale_relationship_of_a_user_who_changed_role(neo4j_session):
    # Arrange: Kyle is an unaffiliated enterprise owner.
    _seed_organization(neo4j_session)
    cartography.intel.github.users.sync(
        neo4j_session,
        {"UPDATE_TAG": 100},
        GITHUB_USER_DATA[0],
        GITHUB_ENTERPRISE_OWNER_DATA[0],
        GITHUB_ORG_DATA,
    )
    kyle = GITHUB_ENTERPRISE_OWNER_DATA[0][0]["node"]

    # Act: the next run lists Kyle as a plain member and no longer as an owner.
    cartography.intel.github.users.sync(
        neo4j_session,
        {"UPDATE_TAG": 200},
        [{"hasTwoFactorEnabled": None, "node": kyle, "role": "MEMBER"}],
        [],
        GITHUB_ORG_DATA,
    )

    # Assert
    facts = _node_organization_facts(neo4j_session, kyle["url"])
    assert facts["is_enterprise_owner"] is False


def test_cleanup_clears_facts_of_user_without_memberships(neo4j_session):
    # Arrange
    _seed_organization(neo4j_session)
    cartography.intel.github.users.sync(
        neo4j_session,
        {"UPDATE_TAG": 100},
        GITHUB_USER_DATA[0],
        GITHUB_ENTERPRISE_OWNER_DATA[0],
        GITHUB_ORG_DATA,
    )

    # Act: the next run finds no organization that still lists Marge.
    cartography.intel.github.users.cleanup(neo4j_session, {"UPDATE_TAG": 200})

    # Assert
    assert _node_organization_facts(neo4j_session, "https://github.com/mbsimpson") == {
        "has_2fa_enabled": None,
        "_ont_has_mfa": None,
        "is_enterprise_owner": None,
        "organization_verified_domain_emails": None,
        "normalized_emails": None,
    }


def test_sync_with_cleanups(neo4j_session):
    # Arrange
    _seed_organization(neo4j_session)

    # Act
    # Sync once
    cartography.intel.github.users.sync(
        neo4j_session,
        {"UPDATE_TAG": 100},
        GITHUB_USER_DATA[0],
        GITHUB_ENTERPRISE_OWNER_DATA[0],
        GITHUB_ORG_DATA,
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
        GITHUB_USER_DATA_AT_TIMESTAMP_2[0],
        GITHUB_ENTERPRISE_OWNER_DATA[0],
        GITHUB_ORG_DATA,
    )
    cartography.intel.github.users.cleanup(neo4j_session, {"UPDATE_TAG": 200})

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
