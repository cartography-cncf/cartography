from unittest.mock import patch

import cartography.intel.ontology.users
import cartography.intel.pylon
import cartography.intel.pylon.organization
import cartography.intel.pylon.roles
import cartography.intel.pylon.teams
import cartography.intel.pylon.users
import tests.data.pylon.organization
import tests.data.pylon.roles
import tests.data.pylon.teams
import tests.data.pylon.users
from cartography.config import Config
from tests.data.pylon.organization import PYLON_ORG_ID
from tests.data.pylon.roles import ADMIN_ROLE_ID
from tests.data.pylon.roles import MEMBER_ROLE_ID
from tests.data.pylon.roles import SECURITY_ROLE_ID
from tests.data.pylon.teams import SECURITY_TEAM_ID
from tests.data.pylon.teams import SUPPORT_TEAM_ID
from tests.data.pylon.users import FRANK_ID
from tests.data.pylon.users import HOMER_ID
from tests.data.pylon.users import MARGE_ID
from tests.data.pylon.users import OLD_TOKEN_ID
from tests.data.pylon.users import TRIAGE_BOT_ID
from tests.data.pylon.users import ZAPIER_TOKEN_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TOKEN = "pylon_api_test-token"


def _config(update_tag: int) -> Config:
    return Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        pylon_api_token=TEST_TOKEN,
    )


@patch.object(
    cartography.intel.pylon.teams,
    "get",
    return_value=tests.data.pylon.teams.PYLON_TEAMS,
)
@patch.object(
    cartography.intel.pylon.users,
    "get",
    return_value=tests.data.pylon.users.PYLON_USERS,
)
@patch.object(
    cartography.intel.pylon.roles,
    "get",
    return_value=tests.data.pylon.roles.PYLON_ROLES,
)
@patch.object(
    cartography.intel.pylon.organization,
    "get",
    return_value=tests.data.pylon.organization.PYLON_ME,
)
def test_sync_pylon(mock_me, mock_roles, mock_users, mock_teams, neo4j_session):
    # Arrange
    neo4j_session.run(
        "MATCH (n) WHERE any(l IN labels(n) WHERE l STARTS WITH 'Pylon') DETACH DELETE n"
    )

    # Act
    cartography.intel.pylon.start_pylon_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "PylonOrganization",
        ["id", "name", "base_url"],
    ) == {(PYLON_ORG_ID, "Springfield Nuclear", "https://api.usepylon.com")}

    roles = {
        record["id"]: (
            record["slug"],
            record["permissions"],
            record["filtered_permissions"],
            record["field_restricted_permissions"],
            record["issue_access_rule_count"],
        )
        for record in neo4j_session.run(
            """
            MATCH (r:PylonRole)
            RETURN r.id AS id, r.slug AS slug, r.permissions AS permissions,
                r.filtered_permissions AS filtered_permissions,
                r.field_restricted_permissions AS field_restricted_permissions,
                r.issue_access_rule_count AS issue_access_rule_count
            """,
        )
    }
    assert roles == {
        ADMIN_ROLE_ID: (
            "admin",
            ["delete:issue", "manage:users", "read:issue", "write:issue"],
            [],
            [],
            0,
        ),
        MEMBER_ROLE_ID: ("member", ["read:issue", "write:issue"], [], [], 0),
        SECURITY_ROLE_ID: (
            "security",
            ["read:account", "read:issue", "write:contact"],
            ["read:account", "read:issue"],
            ["write:contact"],
            1,
        ),
    }

    assert check_nodes(
        neo4j_session,
        "PylonUser",
        ["id", "email", "is_deactivated", "_ont_active"],
    ) == {
        (MARGE_ID, "mbsimpson@simpson.corp", False, True),
        (HOMER_ID, "hjsimpson@simpson.corp", False, True),
        (FRANK_ID, "fgrimes@simpson.corp", True, False),
    }
    assert check_nodes(
        neo4j_session,
        "PylonServiceAccount",
        ["id", "name", "is_deactivated", "_ont_active"],
    ) == {
        (ZAPIER_TOKEN_ID, "Zapier - Write Back", False, True),
        (TRIAGE_BOT_ID, "Triage Bot", False, True),
        (OLD_TOKEN_ID, "Old Admin Token", True, False),
    }
    assert check_nodes(neo4j_session, "UserAccount", ["id"]) == {
        (MARGE_ID,),
        (HOMER_ID,),
        (FRANK_ID,),
    }
    assert check_nodes(neo4j_session, "ServiceAccount", ["id"]) == {
        (ZAPIER_TOKEN_ID,),
        (TRIAGE_BOT_ID,),
        (OLD_TOKEN_ID,),
    }

    assert check_nodes(
        neo4j_session,
        "PylonTeam",
        ["id", "name", "assignment_method"],
    ) == {
        (SUPPORT_TEAM_ID, "Support", "routing"),
        (SECURITY_TEAM_ID, "Security", "manual"),
    }

    for label in ("PylonRole", "PylonUser", "PylonServiceAccount", "PylonTeam"):
        assert check_rels(
            neo4j_session,
            "PylonOrganization",
            "id",
            label,
            "id",
            "RESOURCE",
        ) == {
            (PYLON_ORG_ID, node_id)
            for (node_id,) in check_nodes(neo4j_session, label, ["id"])
        }

    assert check_rels(
        neo4j_session,
        "PylonUser",
        "id",
        "PylonRole",
        "id",
        "HAS_ROLE",
    ) == {
        (MARGE_ID, ADMIN_ROLE_ID),
        (MARGE_ID, SECURITY_ROLE_ID),
        (HOMER_ID, MEMBER_ROLE_ID),
        (FRANK_ID, MEMBER_ROLE_ID),
    }
    assert check_rels(
        neo4j_session,
        "PylonServiceAccount",
        "id",
        "PylonRole",
        "id",
        "HAS_ROLE",
    ) == {
        (ZAPIER_TOKEN_ID, ADMIN_ROLE_ID),
        (TRIAGE_BOT_ID, MEMBER_ROLE_ID),
        (OLD_TOKEN_ID, ADMIN_ROLE_ID),
    }

    assert check_rels(
        neo4j_session,
        "PylonUser",
        "id",
        "PylonTeam",
        "id",
        "MEMBER_OF",
    ) == {
        (HOMER_ID, SUPPORT_TEAM_ID),
        (FRANK_ID, SUPPORT_TEAM_ID),
        (MARGE_ID, SECURITY_TEAM_ID),
    }
    assert check_rels(
        neo4j_session,
        "PylonServiceAccount",
        "id",
        "PylonTeam",
        "id",
        "MEMBER_OF",
    ) == {(TRIAGE_BOT_ID, SUPPORT_TEAM_ID)}


@patch.object(cartography.intel.pylon.teams, "get")
@patch.object(cartography.intel.pylon.users, "get")
@patch.object(
    cartography.intel.pylon.roles,
    "get",
    return_value=tests.data.pylon.roles.PYLON_ROLES,
)
@patch.object(
    cartography.intel.pylon.organization,
    "get",
    return_value=tests.data.pylon.organization.PYLON_ME,
)
def test_sync_pylon_cleans_up_stale_data(
    mock_me,
    mock_roles,
    mock_users,
    mock_teams,
    neo4j_session,
):
    # Arrange
    neo4j_session.run(
        "MATCH (n) WHERE any(l IN labels(n) WHERE l STARTS WITH 'Pylon') DETACH DELETE n"
    )
    mock_users.return_value = tests.data.pylon.users.PYLON_USERS
    mock_teams.return_value = tests.data.pylon.teams.PYLON_TEAMS

    # Act
    cartography.intel.pylon.start_pylon_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )

    # Assert
    assert len(check_nodes(neo4j_session, "PylonUser", ["id"])) == 3
    assert len(check_nodes(neo4j_session, "PylonServiceAccount", ["id"])) == 3

    # Arrange: Frank leaves Pylon, Marge loses the Security role, two tokens are
    # deleted, and the Security team is deleted.
    marge = dict(tests.data.pylon.users.PYLON_USERS[0])
    marge["role_ids"] = [ADMIN_ROLE_ID]
    mock_users.return_value = [
        marge,
        tests.data.pylon.users.PYLON_USERS[1],
        tests.data.pylon.users.PYLON_USERS[3],
    ]
    support = dict(tests.data.pylon.teams.PYLON_TEAMS[0])
    support["users"] = [{"id": HOMER_ID, "email": "hjsimpson@simpson.corp"}]
    mock_teams.return_value = [support]

    # Act
    cartography.intel.pylon.start_pylon_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG + 1),
    )

    # Assert
    assert check_nodes(neo4j_session, "PylonUser", ["id"]) == {
        (MARGE_ID,),
        (HOMER_ID,),
    }
    assert check_nodes(neo4j_session, "PylonServiceAccount", ["id"]) == {
        (ZAPIER_TOKEN_ID,),
    }
    assert check_nodes(neo4j_session, "PylonTeam", ["id"]) == {
        (SUPPORT_TEAM_ID,),
    }
    assert check_rels(
        neo4j_session,
        "PylonUser",
        "id",
        "PylonRole",
        "id",
        "HAS_ROLE",
    ) == {
        (MARGE_ID, ADMIN_ROLE_ID),
        (HOMER_ID, MEMBER_ROLE_ID),
    }
    assert check_rels(
        neo4j_session,
        "PylonUser",
        "id",
        "PylonTeam",
        "id",
        "MEMBER_OF",
    ) == {(HOMER_ID, SUPPORT_TEAM_ID)}


@patch.object(
    cartography.intel.pylon.teams,
    "get",
    return_value=tests.data.pylon.teams.PYLON_TEAMS,
)
@patch.object(
    cartography.intel.pylon.users,
    "get",
    return_value=tests.data.pylon.users.PYLON_USERS,
)
@patch.object(
    cartography.intel.pylon.roles,
    "get",
    return_value=tests.data.pylon.roles.PYLON_ROLES,
)
@patch.object(
    cartography.intel.pylon.organization,
    "get",
    return_value=tests.data.pylon.organization.PYLON_ME,
)
def test_pylon_users_link_to_ontology_users(
    mock_me,
    mock_roles,
    mock_users,
    mock_teams,
    neo4j_session,
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    cartography.intel.pylon.start_pylon_ingestion(
        neo4j_session,
        _config(TEST_UPDATE_TAG),
    )

    # Act
    cartography.intel.ontology.users.sync(
        neo4j_session,
        ["pylon"],
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "User",
        "email",
        "PylonUser",
        "id",
        "HAS_ACCOUNT",
    ) == {
        ("mbsimpson@simpson.corp", MARGE_ID),
        ("hjsimpson@simpson.corp", HOMER_ID),
        ("fgrimes@simpson.corp", FRANK_ID),
    }
    assert check_nodes(neo4j_session, "PylonUser", ["id", "_ont_active"]) == {
        (MARGE_ID, True),
        (HOMER_ID, True),
        (FRANK_ID, False),
    }
