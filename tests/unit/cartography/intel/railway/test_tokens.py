from unittest.mock import Mock
from unittest.mock import patch

import pytest

import cartography.intel.railway.iam.tokens
import tests.data.railway.tokens
from cartography.intel.railway.utils import RailwayGraphQLError

TEST_WORKSPACE_ID = "11111111-1111-1111-1111-111111111111"
WORKSPACE_TOKEN_ID = "a1a1a1a1-a1a1-a1a1-a1a1-a1a1a1a1a1a1"
PERSONAL_TOKEN_ID = "a2a2a2a2-a2a2-a2a2-a2a2-a2a2a2a2a2a2"


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
