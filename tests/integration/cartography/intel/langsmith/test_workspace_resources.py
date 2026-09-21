from unittest.mock import patch

import cartography.intel.langsmith.workspace_resources
import tests.data.langsmith.workspace_resources
from tests.data.langsmith.organizations import LANGSMITH_ORG_ID
from tests.data.langsmith.workspaces import LANGSMITH_WORKSPACES
from tests.data.langsmith.workspaces import WORKSPACE_DEV_ID
from tests.data.langsmith.workspaces import WORKSPACE_PROD_ID
from tests.integration.cartography.intel.langsmith.test_workspaces import (
    _ensure_local_neo4j_has_test_workspaces,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
DATA = tests.data.langsmith.workspace_resources


def _mock_get_secrets(client, org_id, workspace_id):
    return DATA.LANGSMITH_SECRETS[workspace_id]


def _mock_get_tags(client, org_id, workspace_id):
    tags = []
    for tag_key in DATA.LANGSMITH_TAG_KEYS[workspace_id]:
        for tag_value in DATA.LANGSMITH_TAG_VALUES.get(tag_key["id"], []):
            tags.append(
                {
                    "id": tag_value["id"],
                    "key": tag_key["key"],
                    "value": tag_value["value"],
                    "key_id": tag_key["id"],
                    "workspace_id": workspace_id,
                }
            )
    return tags


def _mock_get_oauth_clients(client, org_id, workspace_id):
    clients = [dict(c) for c in DATA.LANGSMITH_OAUTH_CLIENTS[workspace_id]["clients"]]
    for oauth_client in clients:
        oauth_client["workspace_id"] = workspace_id
    return clients


def _mock_get_mcp_servers(client, org_id, workspace_id):
    return [
        cartography.intel.langsmith.workspace_resources._transform_mcp_server(
            server, workspace_id, vendor=None
        )
        for server in DATA.LANGSMITH_MCP_SERVERS[workspace_id]
    ]


@patch.object(
    cartography.intel.langsmith.workspace_resources,
    "get_mcp_servers",
    side_effect=_mock_get_mcp_servers,
)
@patch.object(
    cartography.intel.langsmith.workspace_resources,
    "get_oauth_clients",
    side_effect=_mock_get_oauth_clients,
)
@patch.object(
    cartography.intel.langsmith.workspace_resources,
    "get_tags",
    side_effect=_mock_get_tags,
)
@patch.object(
    cartography.intel.langsmith.workspace_resources,
    "get_secrets",
    side_effect=_mock_get_secrets,
)
def test_sync_langsmith_workspace_resources(
    mock_secrets, mock_tags, mock_clients, mock_mcp, neo4j_session
):
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)

    cartography.intel.langsmith.workspace_resources.sync(
        neo4j_session,
        None,
        LANGSMITH_ORG_ID,
        LANGSMITH_WORKSPACES,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": LANGSMITH_ORG_ID},
    )

    # Secret key names only; the same key name in two workspaces stays two distinct nodes.
    assert check_nodes(neo4j_session, "LangSmithSecret", ["id", "name"]) == {
        (f"{WORKSPACE_PROD_ID}|OPENAI_API_KEY", "OPENAI_API_KEY"),
        (f"{WORKSPACE_PROD_ID}|SLACK_BOT_TOKEN", "SLACK_BOT_TOKEN"),
        (f"{WORKSPACE_DEV_ID}|OPENAI_API_KEY", "OPENAI_API_KEY"),
    }

    assert check_nodes(neo4j_session, "LangSmithResourceTag", ["key", "value"]) == {
        ("environment", "prod")
    }

    assert check_nodes(
        neo4j_session, "LangSmithOAuthClient", ["id", "name", "disabled"]
    ) == {("langsmith-mcp-client", "Internal MCP Client", False)}

    assert check_nodes(
        neo4j_session, "LangSmithMcpServer", ["slug", "auth_type", "tool_names"]
    ) == {("internal-docs", "oauth", ["search_docs", "get_doc"])}

    assert check_rels(
        neo4j_session,
        "LangSmithWorkspace",
        "id",
        "LangSmithSecret",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {
        (WORKSPACE_PROD_ID, f"{WORKSPACE_PROD_ID}|OPENAI_API_KEY"),
        (WORKSPACE_PROD_ID, f"{WORKSPACE_PROD_ID}|SLACK_BOT_TOKEN"),
        (WORKSPACE_DEV_ID, f"{WORKSPACE_DEV_ID}|OPENAI_API_KEY"),
    }
