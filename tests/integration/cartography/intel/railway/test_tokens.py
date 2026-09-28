from unittest.mock import Mock
from unittest.mock import patch

import pytest

import cartography.intel.railway.iam.tokens
import cartography.intel.railway.iam.users
import tests.data.railway.projects
import tests.data.railway.tokens
import tests.data.railway.workspaces
from cartography.intel.railway.utils import RailwayGraphQLError
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
WORKSPACE_TOKEN_ID = "a1a1a1a1-a1a1-a1a1-a1a1-a1a1a1a1a1a1"
PERSONAL_TOKEN_ID = "a2a2a2a2-a2a2-a2a2-a2a2-a2a2a2a2a2a2"
OTHER_WORKSPACE_TOKEN_ID = "a3a3a3a3-a3a3-a3a3-a3a3-a3a3a3a3a3a3"
PROJECT_TOKEN_ID = "b1b1b1b1-b1b1-b1b1-b1b1-b1b1b1b1b1b1"


def _arrange(neo4j_session):
    _ensure_local_neo4j_has_test_workspace_and_projects(neo4j_session)
    cartography.intel.railway.iam.users.sync(
        neo4j_session,
        _common_job_parameters(),
        tests.data.railway.workspaces.RAILWAY_WORKSPACE,
        tests.data.railway.projects.RAILWAY_PROJECTS,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.railway.iam.tokens,
    "get_project_tokens",
    side_effect=lambda _session, _url, project_id: (
        tests.data.railway.tokens.RAILWAY_PROJECT_TOKENS
        if project_id == TEST_PROJECT_ID
        else []
    ),
)
@patch.object(
    cartography.intel.railway.iam.tokens,
    "get_api_tokens",
    return_value=(
        [
            token
            for token in tests.data.railway.tokens.RAILWAY_API_TOKENS
            if token["id"] != OTHER_WORKSPACE_TOKEN_ID
        ],
        True,
    ),
)
def test_load_railway_tokens(mock_api_tokens, mock_project_tokens, neo4j_session):
    # Arrange
    _arrange(neo4j_session)

    # Act
    cartography.intel.railway.iam.tokens.sync(
        neo4j_session,
        Mock(),
        _common_job_parameters(),
        tests.data.railway.projects.RAILWAY_PROJECTS,
        ALICE_ID,
        TEST_UPDATE_TAG,
    )

    # Assert API tokens exist
    assert check_nodes(neo4j_session, "RailwayApiToken", ["id", "name"]) == {
        (WORKSPACE_TOKEN_ID, "ci-deploy"),
        (PERSONAL_TOKEN_ID, "laptop"),
    }

    # Assert API tokens attach to the workspace tenant
    assert check_rels(
        neo4j_session,
        "RailwayWorkspace",
        "id",
        "RailwayApiToken",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_WORKSPACE_ID, WORKSPACE_TOKEN_ID),
        (TEST_WORKSPACE_ID, PERSONAL_TOKEN_ID),
    }

    # Assert ownership. Railway has no owner field on ApiToken; apiTokens is account-scoped,
    # so the owner is the `me` principal.
    assert check_rels(
        neo4j_session,
        "RailwayApiToken",
        "id",
        "RailwayUser",
        "id",
        "OWNED_BY",
        rel_direction_right=True,
    ) == {
        (WORKSPACE_TOKEN_ID, ALICE_ID),
        (PERSONAL_TOKEN_ID, ALICE_ID),
    }

    # Assert project tokens exist and scope to their project, not the workspace
    assert check_nodes(
        neo4j_session,
        "RailwayProjectToken",
        ["id", "name", "environment_id"],
    ) == {
        (PROJECT_TOKEN_ID, "production-deploy", "44444444-4444-4444-4444-444444444444"),
    }
    assert check_rels(
        neo4j_session,
        "RailwayProject",
        "id",
        "RailwayProjectToken",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_PROJECT_ID, PROJECT_TOKEN_ID),
    }

    # Both token types carry the APIKey ontology label
    assert check_nodes(neo4j_session, "APIKey", ["id"]) == {
        (WORKSPACE_TOKEN_ID,),
        (PERSONAL_TOKEN_ID,),
        (PROJECT_TOKEN_ID,),
    }


def test_get_api_tokens_filters_other_workspaces():
    with patch(
        "cartography.intel.railway.iam.tokens.paginated_query",
        return_value=tests.data.railway.tokens.RAILWAY_API_TOKENS,
    ):
        tokens, readable = cartography.intel.railway.iam.tokens.get_api_tokens(
            Mock(),
            "https://backboard.railway.com/graphql/v2",
            TEST_WORKSPACE_ID,
        )

    # The token belonging to another workspace is dropped; the null-workspace personal token
    # is kept because it reaches every workspace.
    assert readable is True
    assert {token["id"] for token in tokens} == {
        WORKSPACE_TOKEN_ID,
        PERSONAL_TOKEN_ID,
    }


def test_get_api_tokens_skips_when_not_authorized(caplog):
    # A workspace-scoped token cannot read apiTokens. That must degrade to a warning rather
    # than abort the whole workspace sync.
    with patch(
        "cartography.intel.railway.iam.tokens.paginated_query",
        side_effect=RailwayGraphQLError([{"message": "Not Authorized"}]),
    ):
        tokens, readable = cartography.intel.railway.iam.tokens.get_api_tokens(
            Mock(),
            "https://backboard.railway.com/graphql/v2",
            TEST_WORKSPACE_ID,
        )

    # Crucially `readable` is False, not just an empty list: the caller must be able to tell
    # "cannot read" apart from "there are none".
    assert tokens == []
    assert readable is False
    assert "not authorized to read apiTokens" in caplog.text


@patch.object(
    cartography.intel.railway.iam.tokens,
    "get_project_tokens",
    return_value=[],
)
def test_unreadable_api_tokens_are_not_deleted(mock_project_tokens, neo4j_session):
    # Arrange: a first sync with an account token ingests the API tokens. The neo4j fixture
    # is module-scoped, so clear any tokens an earlier test in this file left behind.
    neo4j_session.run("MATCH (t:RailwayApiToken) DETACH DELETE t")
    _arrange(neo4j_session)
    with patch.object(
        cartography.intel.railway.iam.tokens,
        "get_api_tokens",
        return_value=([tests.data.railway.tokens.RAILWAY_API_TOKENS[0]], True),
    ):
        cartography.intel.railway.iam.tokens.sync(
            neo4j_session,
            Mock(),
            _common_job_parameters(),
            tests.data.railway.projects.RAILWAY_PROJECTS,
            ALICE_ID,
            TEST_UPDATE_TAG,
        )
    assert check_nodes(neo4j_session, "RailwayApiToken", ["id"]) == {
        (WORKSPACE_TOKEN_ID,),
    }

    # Act: re-sync with a workspace-scoped token that cannot read the inventory.
    with patch.object(
        cartography.intel.railway.iam.tokens,
        "get_api_tokens",
        return_value=([], False),
    ):
        cartography.intel.railway.iam.tokens.sync(
            neo4j_session,
            Mock(),
            _common_job_parameters(TEST_UPDATE_TAG + 1),
            tests.data.railway.projects.RAILWAY_PROJECTS,
            ALICE_ID,
            TEST_UPDATE_TAG + 1,
        )

    # Assert the previously ingested token survives: an unreadable inventory is not an empty
    # one, so cleanup must not treat it as stale.
    assert check_nodes(neo4j_session, "RailwayApiToken", ["id"]) == {
        (WORKSPACE_TOKEN_ID,),
    }


@patch.object(
    cartography.intel.railway.iam.tokens,
    "get_project_tokens",
    return_value=[],
)
def test_readable_api_tokens_are_still_cleaned_up(mock_project_tokens, neo4j_session):
    # The completeness guard must not disable cleanup when the inventory *was* readable.
    neo4j_session.run("MATCH (t:RailwayApiToken) DETACH DELETE t")
    _arrange(neo4j_session)
    with patch.object(
        cartography.intel.railway.iam.tokens,
        "get_api_tokens",
        return_value=([tests.data.railway.tokens.RAILWAY_API_TOKENS[0]], True),
    ):
        cartography.intel.railway.iam.tokens.sync(
            neo4j_session,
            Mock(),
            _common_job_parameters(),
            tests.data.railway.projects.RAILWAY_PROJECTS,
            ALICE_ID,
            TEST_UPDATE_TAG,
        )

    # Act: the token is revoked upstream and the inventory legitimately comes back empty.
    with patch.object(
        cartography.intel.railway.iam.tokens,
        "get_api_tokens",
        return_value=([], True),
    ):
        cartography.intel.railway.iam.tokens.sync(
            neo4j_session,
            Mock(),
            _common_job_parameters(TEST_UPDATE_TAG + 1),
            tests.data.railway.projects.RAILWAY_PROJECTS,
            ALICE_ID,
            TEST_UPDATE_TAG + 1,
        )

    assert check_nodes(neo4j_session, "RailwayApiToken", ["id"]) == set()


def test_get_api_tokens_reraises_other_errors():
    with patch(
        "cartography.intel.railway.iam.tokens.paginated_query",
        side_effect=RailwayGraphQLError([{"message": "Problem processing request"}]),
    ):
        with pytest.raises(RailwayGraphQLError):
            cartography.intel.railway.iam.tokens.get_api_tokens(
                Mock(),
                "https://backboard.railway.com/graphql/v2",
                TEST_WORKSPACE_ID,
            )
