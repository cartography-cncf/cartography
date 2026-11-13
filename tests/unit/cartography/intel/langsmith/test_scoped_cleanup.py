from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.graph.cleanupbuilder import build_cleanup_queries
from cartography.intel.langsmith import util
from cartography.models.langsmith.apikey import LangSmithApiKeySchema
from cartography.models.langsmith.deployment import LangSmithDeploymentSchema
from cartography.models.langsmith.mcpserver import LangSmithMcpServerSchema
from cartography.models.langsmith.oauthclient import LangSmithOAuthClientSchema
from cartography.models.langsmith.resourcetag import LangSmithResourceTagSchema
from cartography.models.langsmith.secret import LangSmithSecretSchema
from cartography.models.langsmith.workspacemembership import (
    LangSmithWorkspaceMembershipSchema,
)

PARAMS = {"UPDATE_TAG": 1, "ORG_ID": "org-1"}

# Every schema whose cleanup is scoped to the workspaces that were read.
WORKSPACE_SCOPED_SCHEMAS = [
    LangSmithApiKeySchema(),
    LangSmithDeploymentSchema(),
    LangSmithMcpServerSchema(),
    LangSmithOAuthClientSchema(),
    LangSmithResourceTagSchema(),
    LangSmithSecretSchema(),
    LangSmithWorkspaceMembershipSchema(),
]


@pytest.mark.parametrize("schema", WORKSPACE_SCOPED_SCHEMAS, ids=lambda s: s.label)
def test_every_cleanup_statement_skips_unread_scopes(schema):
    # Act
    queries = [
        util.preserve_unread_in_cleanup_query(query, schema.label)
        for query in build_cleanup_queries(schema)
    ]

    # Assert
    # The filter must reach the stale-relationship statements as well as the node
    # delete, or a preserved node would lose its edges.
    assert len(queries) > 1
    for query in queries:
        lines = query.splitlines()
        assert lines[0].startswith(f"MATCH (n:{schema.label})")
        assert lines[1] == f"WITH n, s WHERE NOT ({util._PRESERVE_UNREAD})"
        assert lines[2] == "MATCH (n)"


def test_scoping_values_are_parameters_not_query_text():
    # Arrange
    query = build_cleanup_queries(LangSmithSecretSchema())[0]

    # Act
    narrowed = util.preserve_unread_in_cleanup_query(query, "LangSmithSecret")

    # Assert
    assert "$LANGSMITH_UNREAD_WORKSPACE_IDS" in narrowed
    assert "$LANGSMITH_UNREAD_KEY_TYPES" in narrowed


def test_an_unrecognized_query_is_refused_rather_than_scoped_wrongly():
    # Act and assert
    with pytest.raises(ValueError):
        util.preserve_unread_in_cleanup_query(
            "MATCH (x:LangSmithSecret) DETACH DELETE x", "LangSmithSecret"
        )


def test_nothing_unread_runs_the_standard_cleanup():
    # Arrange
    job = MagicMock()

    # Act
    with patch.object(util.GraphJob, "from_node_schema", return_value=job) as factory:
        util.cleanup_preserving_unread(
            MagicMock(), LangSmithSecretSchema(), PARAMS, set()
        )

    # Assert
    factory.assert_called_once()
    job.run.assert_called_once()


def test_unread_scopes_are_passed_as_parameters():
    # Arrange
    session = MagicMock()

    # Act
    with patch.object(util.GraphJob, "run", autospec=True) as run:
        util.cleanup_preserving_unread(
            session, LangSmithApiKeySchema(), PARAMS, {"ws-b", "ws-a"}, {"pat"}
        )

    # Assert
    job = run.call_args.args[0]
    assert job.statements
    for statement in job.statements:
        assert statement.parameters["LANGSMITH_UNREAD_WORKSPACE_IDS"] == [
            "ws-a",
            "ws-b",
        ]
        assert statement.parameters["LANGSMITH_UNREAD_KEY_TYPES"] == ["pat"]
        assert statement.parameters["ORG_ID"] == "org-1"
