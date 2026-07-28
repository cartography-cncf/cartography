from unittest.mock import patch

import requests

import cartography.intel.supabase.branches
import tests.data.supabase.branches
from tests.integration.cartography.intel.supabase.test_organizations import (
    _ensure_local_neo4j_has_test_organizations,
)
from tests.integration.cartography.intel.supabase.test_projects import (
    _ensure_local_neo4j_has_test_projects,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_SLUG = "simpson-corp"
TEST_PROJECT_REF = "nuclearplantdbaaaaaa"
TEST_BASE_URL = "https://api.fake-supabase.com"
# A later tag, so cleanup removes the nodes loaded by earlier tests in this
# module: the integration suite shares one database per test module.
TEST_CLEANUP_UPDATE_TAG = TEST_UPDATE_TAG + 1


def _common_job_parameters():
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_SLUG": TEST_ORG_SLUG,
        "PROJECT_REF": TEST_PROJECT_REF,
    }


@patch.object(
    cartography.intel.supabase.branches,
    "get",
    return_value=tests.data.supabase.branches.SUPABASE_BRANCHES,
)
def test_load_supabase_branches(mock_get, neo4j_session):
    """
    Ensure preview branches are loaded with their Git linkage and attached to the
    project.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.branches.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert
    expected_nodes = {
        ("branch-main", "main", "master", None, True),
        ("branch-coolant-fix", "coolant-fix", "fix/coolant", 742, False),
    }
    assert (
        check_nodes(
            neo4j_session,
            "SupabaseBranch",
            ["id", "name", "git_branch", "pr_number", "is_default"],
        )
        == expected_nodes
    )

    assert check_rels(
        neo4j_session,
        "SupabaseBranch",
        "id",
        "SupabaseProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("branch-main", TEST_PROJECT_REF),
        ("branch-coolant-fix", TEST_PROJECT_REF),
    }


@patch.object(
    cartography.intel.supabase.branches,
    "get",
    return_value=tests.data.supabase.branches.SUPABASE_BRANCHES,
)
def test_supabase_branch_of_parent_project(mock_get, neo4j_session):
    """
    Ensure the BRANCH_OF edge resolves through parent_project_ref, so a preview
    branch is traceable back to the project it was cut from.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.branches.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "SupabaseBranch",
        "id",
        "SupabaseProject",
        "id",
        "BRANCH_OF",
        rel_direction_right=True,
    ) == {
        ("branch-main", TEST_PROJECT_REF),
        ("branch-coolant-fix", TEST_PROJECT_REF),
    }

    # The non-default branch lives in its own ephemeral project.
    record = neo4j_session.run(
        """
        MATCH (b:SupabaseBranch {id: 'branch-coolant-fix'})
        RETURN b.project_ref AS project_ref,
               b.persistent AS persistent,
               b.with_data AS with_data
        """,
    ).single()
    assert record["project_ref"] == "coolantfixdbdddddddd"
    assert record["persistent"] is False
    assert record["with_data"] is True


def test_supabase_branches_unavailable_keeps_existing_branches(neo4j_session):
    """
    A tolerated status must not delete the branches already in the graph.

    Branching is plan-gated, so this is the realistic regression: a subscription
    lapsing must not erase the branch inventory that was recorded while it was
    active.
    """
    # Arrange: a successful sync first, so there is real inventory to protect.
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)
    with patch.object(
        cartography.intel.supabase.branches,
        "get",
        return_value=tests.data.supabase.branches.SUPABASE_BRANCHES,
    ):
        cartography.intel.supabase.branches.sync(
            neo4j_session,
            api_session,
            _common_job_parameters(),
        )
    before = check_nodes(neo4j_session, "SupabaseBranch", ["id"])
    assert before, "arrange step should have loaded branches"

    # Act: the endpoint goes unavailable, on a later update tag so a cleanup would
    # consider every existing branch stale and delete it.
    with patch.object(cartography.intel.supabase.branches, "get", return_value=None):
        cartography.intel.supabase.branches.sync(
            neo4j_session,
            api_session,
            {**_common_job_parameters(), "UPDATE_TAG": TEST_CLEANUP_UPDATE_TAG},
        )

    # Assert: nothing was deleted.
    assert check_nodes(neo4j_session, "SupabaseBranch", ["id"]) == before
