import cartography.intel.portkey
import tests.data.portkey
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "org-portkey"


def test_load_portkey_module(neo4j_session, mocker):
    mocker.patch.object(
        cartography.intel.portkey.users,
        "list_admin_users",
        return_value=tests.data.portkey.PORTKEY_USERS,
    )
    mocker.patch.object(
        cartography.intel.portkey.workspaces,
        "list_workspaces",
        return_value=tests.data.portkey.PORTKEY_WORKSPACES,
    )
    mocker.patch.object(
        cartography.intel.portkey.workspaces,
        "list_workspace_members",
        side_effect=lambda *_args: tests.data.portkey.PORTKEY_WORKSPACE_MEMBERS[
            "ws-eng"
        ],
    )
    mocker.patch.object(
        cartography.intel.portkey.resources.util,
        "list_user_invites",
        return_value=tests.data.portkey.PORTKEY_INVITES,
    )
    mocker.patch.object(
        cartography.intel.portkey.resources.util,
        "list_secret_references",
        return_value=tests.data.portkey.PORTKEY_SECRET_REFERENCES,
    )
    mocker.patch.object(
        cartography.intel.portkey.resources.util,
        "list_integrations",
        return_value=tests.data.portkey.PORTKEY_INTEGRATIONS,
    )
    mocker.patch.object(
        cartography.intel.portkey.resources.util,
        "list_mcp_integrations",
        return_value=tests.data.portkey.PORTKEY_MCP_INTEGRATIONS,
    )
    mocker.patch.object(
        cartography.intel.portkey.resources.util,
        "list_api_keys",
        return_value=tests.data.portkey.PORTKEY_API_KEYS,
    )
    mocker.patch.object(
        cartography.intel.portkey.resources.util,
        "retrieve_api_key",
        side_effect=lambda *_args: tests.data.portkey.PORTKEY_API_KEY_DETAILS["pk-1"],
    )
    mocker.patch.object(
        cartography.intel.portkey.resources.util,
        "list_virtual_keys",
        return_value=tests.data.portkey.PORTKEY_VIRTUAL_KEYS,
    )
    mocker.patch.object(
        cartography.intel.portkey.resources.util,
        "list_configs",
        return_value=tests.data.portkey.PORTKEY_CONFIGS,
    )
    mocker.patch.object(
        cartography.intel.portkey.resources.util,
        "list_providers",
        side_effect=lambda *_args: tests.data.portkey.PORTKEY_PROVIDERS["ws-eng"],
    )
    mocker.patch.object(
        cartography.intel.portkey.resources.util,
        "list_mcp_servers",
        side_effect=lambda *_args: tests.data.portkey.PORTKEY_MCP_SERVERS["ws-eng"],
    )
    mocker.patch.object(
        cartography.intel.portkey.resources.util,
        "list_guardrails",
        return_value=tests.data.portkey.PORTKEY_GUARDRAILS,
    )
    mocker.patch.object(
        cartography.intel.portkey.resources.util,
        "list_prompt_collections",
        side_effect=lambda *_args: tests.data.portkey.PORTKEY_PROMPT_COLLECTIONS[
            "ws-eng"
        ],
    )
    mocker.patch.object(
        cartography.intel.portkey.resources.util,
        "list_prompts",
        side_effect=lambda *_args: tests.data.portkey.PORTKEY_PROMPTS["ws-eng"],
    )

    class TestConfig:
        portkey_apikey = "pk_test"
        portkey_org_id = TEST_ORG_ID
        portkey_base_url = "https://api.portkey.ai/v1"
        update_tag = TEST_UPDATE_TAG

    cartography.intel.portkey.start_portkey_ingestion(neo4j_session, TestConfig())

    assert check_nodes(neo4j_session, "PortkeyOrganization", ["id"]) == {
        (TEST_ORG_ID,),
    }
    assert check_nodes(neo4j_session, "PortkeyUser", ["id", "email"]) == {
        ("user-1", "lisa@springfield.example"),
        ("user-2", "maggie@springfield.example"),
    }
    assert check_nodes(neo4j_session, "PortkeyWorkspace", ["id", "name"]) == {
        ("ws-eng", "Engineering"),
    }
    assert check_nodes(neo4j_session, "PortkeyInvite", ["id", "email"]) == {
        ("invite-1", "bart@springfield.example"),
    }
    assert check_nodes(neo4j_session, "PortkeyAPIKey", ["id", "name"]) == {
        ("pk-1", "Engineering API key"),
    }
    assert check_nodes(neo4j_session, "PortkeyIntegration", ["id", "name"]) == {
        ("int-openai", "OpenAI Production"),
    }
    assert check_nodes(neo4j_session, "PortkeyMCPIntegration", ["id", "name"]) == {
        ("mcp-int-1", "Atlassian MCP"),
    }
    assert check_nodes(neo4j_session, "PortkeyMCPServer", ["id", "name"]) == {
        ("mcp-server-1", "Atlassian Workspace Server"),
    }
    assert check_nodes(neo4j_session, "PortkeyProvider", ["id", "name"]) == {
        ("provider-openai", "OpenAI Workspace"),
    }
    assert check_nodes(neo4j_session, "PortkeyPrompt", ["id", "name"]) == {
        ("prompt-1", "Summarize"),
    }

    assert check_rels(
        neo4j_session,
        "PortkeyUser",
        "id",
        "PortkeyWorkspace",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        ("user-1", "ws-eng"),
        ("user-2", "ws-eng"),
    }
    assert check_rels(
        neo4j_session,
        "PortkeyMCPServer",
        "id",
        "PortkeyMCPIntegration",
        "id",
        "USES",
        rel_direction_right=True,
    ) == {
        ("mcp-server-1", "mcp-int-1"),
    }
    assert check_rels(
        neo4j_session,
        "PortkeyAPIKey",
        "id",
        "PortkeyWorkspace",
        "id",
        "AVAILABLE_IN",
        rel_direction_right=True,
    ) == {
        ("pk-1", "ws-eng"),
    }
    assert check_rels(
        neo4j_session,
        "PortkeyVirtualKey",
        "id",
        "PortkeyWorkspace",
        "id",
        "AVAILABLE_IN",
        rel_direction_right=True,
    ) == {
        ("vk-eng", "ws-eng"),
    }
    assert check_rels(
        neo4j_session,
        "PortkeyProvider",
        "id",
        "PortkeyWorkspace",
        "id",
        "AVAILABLE_IN",
        rel_direction_right=True,
    ) == {
        ("provider-openai", "ws-eng"),
    }
    assert check_rels(
        neo4j_session,
        "PortkeyProvider",
        "id",
        "PortkeyIntegration",
        "id",
        "USES",
        rel_direction_right=True,
    ) == {
        ("provider-openai", "int-openai"),
    }
    assert check_rels(
        neo4j_session,
        "PortkeyPrompt",
        "id",
        "PortkeyPromptCollection",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        ("prompt-1", "col-1"),
    }
