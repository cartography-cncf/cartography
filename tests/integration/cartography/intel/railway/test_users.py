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
CAROL_ID = "24242424-2424-2424-2424-242424242424"
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


def test_transform_users_splits_workspace_from_project_only_members():
    workspace_members, project_only = (
        cartography.intel.railway.iam.users.transform_users(
            tests.data.railway.workspaces.RAILWAY_WORKSPACE,
            tests.data.railway.projects.RAILWAY_PROJECTS,
        )
    )

    # Both fixture users are workspace members, so nothing is left over. A user present in
    # both sources belongs in the workspace group: only that payload carries 2FA and the
    # workspace role.
    by_id = {user["id"]: user for user in workspace_members}
    assert set(by_id) == {ALICE_ID, BOB_ID}
    assert project_only == []
    assert by_id[BOB_ID]["twoFactorAuthEnabled"] is True
    # The workspace role, not the project role (Bob is a project VIEWER).
    assert by_id[BOB_ID]["role"] == "MEMBER"


def test_transform_users_keeps_project_only_members_out_of_the_workspace_group():
    # Someone with access to a project but not to the workspace, which is possible on Team
    # plans. They must not be asserted to be a workspace member.
    workspace = {
        "members": [tests.data.railway.workspaces.RAILWAY_WORKSPACE["members"][0]]
    }
    projects = [
        {
            "id": TEST_PROJECT_ID,
            "members": [
                {
                    "id": CAROL_ID,
                    "email": "carol@example.com",
                    "name": "Carol Example",
                    "role": "VIEWER",
                },
            ],
        },
    ]

    workspace_members, project_only = (
        cartography.intel.railway.iam.users.transform_users(
            workspace,
            projects,
        )
    )

    assert [user["id"] for user in workspace_members] == [ALICE_ID]
    assert [user["id"] for user in project_only] == [CAROL_ID]
    # No 2FA key at all rather than a null one, so loading this row cannot blank a value
    # another workspace's sync established for the same person.
    assert "twoFactorAuthEnabled" not in project_only[0]


def test_project_only_member_is_not_a_workspace_member(neo4j_session):
    # Arrange. The neo4j fixture is module-scoped, so drop users an earlier test left behind.
    neo4j_session.run("MATCH (u:RailwayUser) DETACH DELETE u")
    _ensure_local_neo4j_has_test_workspace_and_projects(neo4j_session)
    workspace = {
        "members": [tests.data.railway.workspaces.RAILWAY_WORKSPACE["members"][0]]
    }
    projects = [
        {
            "id": TEST_PROJECT_ID,
            "members": [
                {
                    "id": CAROL_ID,
                    "email": "carol@example.com",
                    "name": "Carol Example",
                    "role": "VIEWER",
                },
            ],
        },
    ]

    # Act
    cartography.intel.railway.iam.users.sync(
        neo4j_session,
        _common_job_parameters(),
        workspace,
        projects,
        TEST_UPDATE_TAG,
    )

    # Assert Carol exists and is scoped to the workspace, but only Alice is a member of it.
    assert (CAROL_ID,) in check_nodes(neo4j_session, "RailwayUser", ["id"])
    assert check_rels(
        neo4j_session,
        "RailwayWorkspace",
        "id",
        "RailwayUser",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) >= {
        (TEST_WORKSPACE_ID, CAROL_ID),
    }
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
    }
    # She is a member of the project, though.
    assert check_rels(
        neo4j_session,
        "RailwayUser",
        "id",
        "RailwayProject",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        (CAROL_ID, TEST_PROJECT_ID),
    }


def test_syncing_one_workspace_leaves_another_workspaces_edges_alone(neo4j_session):
    """
    A Railway user can belong to several workspaces, and workspaces are synced one after
    another. Two things must hold when the workspace being synced no longer lists a user:

      * the shared identity node survives, since deleting it would take every other
        workspace's edges - and any other module's edges - with it; and
      * the other workspace's edges survive even though they are stale, because that
        workspace has not been synced yet this run. Deleting them here would silently erase
        its memberships if its own sync then failed.
    """
    neo4j_session.run("MATCH (u:RailwayUser) DETACH DELETE u")
    other_workspace_id = "1a1a1a1a-1a1a-1a1a-1a1a-1a1a1a1a1a1a"
    # Deliberately stale: written by a previous run, and this run has not reached that
    # workspace yet.
    #
    # These edges carry the other workspace's _sub_resource_label / _sub_resource_id, exactly
    # as load_matchlinks would have written them. That is what makes this a real test: the
    # MatchLink cleanup matches on those two properties, so edges lacking them could never be
    # deleted and would survive even if workspace scoping were broken.
    neo4j_session.run(
        """
        MERGE (w:RailwayWorkspace {id: $other_workspace_id})
        SET w.lastupdated = $stale_tag
        MERGE (u:RailwayUser {id: $user_id})
        SET u.lastupdated = $stale_tag
        MERGE (w)-[r:RESOURCE]->(u)
        SET r.lastupdated = $stale_tag,
            r._sub_resource_label = 'RailwayWorkspace',
            r._sub_resource_id = $other_workspace_id
        MERGE (u)-[m:MEMBER_OF]->(w)
        SET m.lastupdated = $stale_tag, m.role = 'ADMIN',
            m._sub_resource_label = 'RailwayWorkspace',
            m._sub_resource_id = $other_workspace_id
        """,
        other_workspace_id=other_workspace_id,
        user_id=ALICE_ID,
        stale_tag=TEST_UPDATE_TAG,
    )
    _ensure_local_neo4j_has_test_workspace_and_projects(neo4j_session)

    # Act: the workspace under sync no longer lists Alice.
    cartography.intel.railway.iam.users.sync(
        neo4j_session,
        _common_job_parameters(TEST_UPDATE_TAG + 1),
        {"members": []},
        [],
        TEST_UPDATE_TAG + 1,
    )

    # Assert the node survives, and so do the other workspace's stale edges.
    assert (ALICE_ID,) in check_nodes(neo4j_session, "RailwayUser", ["id"])
    assert check_rels(
        neo4j_session,
        "RailwayWorkspace",
        "id",
        "RailwayUser",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (other_workspace_id, ALICE_ID),
    }
    assert check_rels(
        neo4j_session,
        "RailwayUser",
        "id",
        "RailwayWorkspace",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        (ALICE_ID, other_workspace_id),
    }


def test_stale_edges_of_the_synced_workspace_are_deleted(neo4j_session):
    """
    Positive control for the test above.

    On its own, "the other workspace's edge survived" would also hold if cleanup deleted
    nothing at all. This asserts the other half: an edge carrying *this* workspace's scope
    is deleted when it goes stale. Together the two prove the cleanup discriminates on
    _sub_resource_id rather than being a no-op.
    """
    neo4j_session.run("MATCH (u:RailwayUser) DETACH DELETE u")
    _ensure_local_neo4j_has_test_workspace_and_projects(neo4j_session)
    neo4j_session.run(
        """
        MERGE (w:RailwayWorkspace {id: $workspace_id})
        MERGE (u:RailwayUser {id: $user_id})
        SET u.lastupdated = $stale_tag
        MERGE (w)-[r:RESOURCE]->(u)
        SET r.lastupdated = $stale_tag,
            r._sub_resource_label = 'RailwayWorkspace',
            r._sub_resource_id = $workspace_id
        MERGE (u)-[m:MEMBER_OF]->(w)
        SET m.lastupdated = $stale_tag, m.role = 'ADMIN',
            m._sub_resource_label = 'RailwayWorkspace',
            m._sub_resource_id = $workspace_id
        """,
        workspace_id=TEST_WORKSPACE_ID,
        user_id=ALICE_ID,
        stale_tag=TEST_UPDATE_TAG,
    )

    # Act: this workspace no longer lists Alice.
    cartography.intel.railway.iam.users.sync(
        neo4j_session,
        _common_job_parameters(TEST_UPDATE_TAG + 1),
        {"members": []},
        [],
        TEST_UPDATE_TAG + 1,
    )

    # Assert both of this workspace's stale edges are gone, while the node remains.
    assert (ALICE_ID,) in check_nodes(neo4j_session, "RailwayUser", ["id"])
    assert (
        check_rels(
            neo4j_session,
            "RailwayWorkspace",
            "id",
            "RailwayUser",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "RailwayUser",
            "id",
            "RailwayWorkspace",
            "id",
            "MEMBER_OF",
            rel_direction_right=True,
        )
        == set()
    )
