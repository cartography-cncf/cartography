import cartography.intel.railway.iam.users
import tests.data.railway.projects
import tests.data.railway.workspaces
from tests.integration.cartography.intel.railway.test_projects import (
    _common_job_parameters,
)
from tests.integration.cartography.intel.railway.test_projects import (
    _ensure_local_neo4j_has_test_workspace_and_projects,
)
from tests.integration.cartography.intel.railway.test_projects import TEST_PROJECT_ID
from tests.integration.cartography.intel.railway.test_projects import TEST_UPDATE_TAG
from tests.integration.cartography.intel.railway.test_projects import TEST_WORKSPACE_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

ALICE_ID = "22222222-2222-2222-2222-222222222222"
BOB_ID = "23232323-2323-2323-2323-232323232323"


def test_load_railway_users(neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_workspace_and_projects(neo4j_session)

    # Act
    cartography.intel.railway.iam.users.sync(
        neo4j_session,
        _common_job_parameters(),
        tests.data.railway.workspaces.RAILWAY_WORKSPACE,
        tests.data.railway.projects.RAILWAY_PROJECTS,
        TEST_UPDATE_TAG,
    )

    # Assert users exist with their 2FA state
    assert check_nodes(
        neo4j_session,
        "RailwayUser",
        ["id", "email", "two_factor_auth_enabled"],
    ) == {
        (ALICE_ID, "alice@example.com", False),
        (BOB_ID, "bob@example.com", True),
    }

    # Assert users hang off the workspace tenant
    assert check_rels(
        neo4j_session,
        "RailwayWorkspace",
        "id",
        "RailwayUser",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_WORKSPACE_ID, ALICE_ID),
        (TEST_WORKSPACE_ID, BOB_ID),
    }

    # Assert workspace membership
    assert check_rels(
        neo4j_session,
        "RailwayUser",
        "id",
        "RailwayWorkspace",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        (ALICE_ID, TEST_WORKSPACE_ID),
        (BOB_ID, TEST_WORKSPACE_ID),
    }

    # Assert project membership, which is a MatchLink so the role can differ per project
    assert check_rels(
        neo4j_session,
        "RailwayUser",
        "id",
        "RailwayProject",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        (ALICE_ID, TEST_PROJECT_ID),
        (BOB_ID, TEST_PROJECT_ID),
    }

    # Bob is a workspace MEMBER but only a project VIEWER: the two roles must not collide.
    roles = neo4j_session.run(
        """
        MATCH (u:RailwayUser {id: $user_id})-[r:MEMBER_OF]->(t)
        RETURN labels(t) AS labels, r.role AS role
        """,
        user_id=BOB_ID,
    )
    assert {
        (
            next(label for label in record["labels"] if label.startswith("Railway")),
            record["role"],
        )
        for record in roles
    } == {
        ("RailwayWorkspace", "MEMBER"),
        ("RailwayProject", "VIEWER"),
    }

    # The UserAccount ontology label and the RailwayPrincipal umbrella are both applied
    assert check_nodes(neo4j_session, "UserAccount", ["id"]) >= {(ALICE_ID,), (BOB_ID,)}
    assert check_nodes(neo4j_session, "RailwayPrincipal", ["id"]) == {
        (ALICE_ID,),
        (BOB_ID,),
    }


def test_transform_users_prefers_workspace_records():
    # A project member payload has no twoFactorAuthEnabled; the workspace record does, and
    # must win when the same user appears in both.
    users = cartography.intel.railway.iam.users.transform_users(
        tests.data.railway.workspaces.RAILWAY_WORKSPACE,
        tests.data.railway.projects.RAILWAY_PROJECTS,
    )

    by_id = {user["id"]: user for user in users}
    assert by_id[BOB_ID]["twoFactorAuthEnabled"] is True
    # The workspace role, not the project role.
    assert by_id[BOB_ID]["role"] == "MEMBER"
