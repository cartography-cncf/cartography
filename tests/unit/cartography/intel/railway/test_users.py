import cartography.intel.railway.iam.users
import tests.data.railway.projects
import tests.data.railway.workspaces

TEST_PROJECT_ID = "33333333-3333-3333-3333-333333333333"
ALICE_ID = "22222222-2222-2222-2222-222222222222"
BOB_ID = "23232323-2323-2323-2323-232323232323"
CAROL_ID = "24242424-2424-2424-2424-242424242424"


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
