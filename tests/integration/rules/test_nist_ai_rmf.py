from unittest.mock import patch

import cartography.intel.github.app_installations
import cartography.intel.openai
import cartography.intel.openai.adminapikeys
import cartography.intel.openai.apikeys
import cartography.intel.openai.projects
import cartography.intel.openai.serviceaccounts
import cartography.intel.openai.users
import tests.data.openai.adminapikeys
import tests.data.openai.apikeys
import tests.data.openai.projects
import tests.data.openai.serviceaccounts
import tests.data.openai.users
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.config import Config
from cartography.rules.data.rules.nist_ai_rmf import ai_provider_api_key_hygiene
from cartography.rules.data.rules.nist_ai_rmf import ai_third_party_app_inventory

TEST_UPDATE_TAG = 123456789
ORG_URLS = (
    "https://github.com/simpsoncorp",
    "https://github.com/burnsindustries",
)
LLM_APP_INSTALLATION = {
    "client_id": "Iv1.llmreviewer0001",
    "app_id": 4242,
    "app_slug": "example-llm-reviewer",
    "target_type": "Organization",
    "repository_selection": "all",
    "permissions": {"contents": "read", "metadata": "read"},
}


def test_ai_app_inventory_keys_each_installation_of_one_github_app(neo4j_session):
    # Arrange: one GitHub App installed in two orgs is two ThirdPartyApp nodes
    # that share the app's client id.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    for installation_id, org_url in enumerate(ORG_URLS, start=1):
        neo4j_session.run("MERGE (:GitHubOrganization {id: $org_url})", org_url=org_url)
        cartography.intel.github.app_installations.load_installations(
            neo4j_session,
            cartography.intel.github.app_installations.transform(
                [{**LLM_APP_INSTALLATION, "id": installation_id}],
                org_url,
            ),
            org_url,
            TEST_UPDATE_TAG,
        )
    fact = ai_third_party_app_inventory.facts[0]

    # Act
    rows = neo4j_session.execute_read(read_list_of_dicts_tx, fact.cypher_query)

    # Assert
    assert {row["asset_node_id"] for row in rows} == {
        f"{ORG_URLS[0]}/installations/1",
        f"{ORG_URLS[1]}/installations/2",
    }
    identities = [tuple(row[field] for field in fact.identity_fields) for row in rows]
    assert len(set(identities)) == len(identities)


def _sync_openai(neo4j_session, update_tag, projects, admin_api_keys):
    with (
        patch.object(
            cartography.intel.openai.users,
            "get",
            return_value=tests.data.openai.users.OPENAI_USERS,
        ),
        patch.object(cartography.intel.openai.projects, "get", return_value=projects),
        patch.object(
            cartography.intel.openai.projects,
            "get_project_users",
            return_value=tests.data.openai.projects.OPENAI_PROJECTS_MEMBERS,
        ),
        patch.object(
            cartography.intel.openai.serviceaccounts,
            "get",
            return_value=tests.data.openai.serviceaccounts.OPENAI_SERVICEACCOUNTS,
        ),
        patch.object(
            cartography.intel.openai.apikeys,
            "get",
            return_value=tests.data.openai.apikeys.OPENAI_APIKEYS,
        ),
        patch.object(
            cartography.intel.openai.adminapikeys,
            "get",
            return_value=admin_api_keys,
        ),
    ):
        cartography.intel.openai.start_openai_ingestion(
            neo4j_session,
            Config(
                neo4j_uri="bolt://unused",
                update_tag=update_tag,
                openai_apikey="test-key",
                openai_org_id="org-iwai3meew4phaeNgu8ae",
            ),
        )


def test_api_key_hygiene_reports_a_key_once_after_its_project_is_removed(
    neo4j_session,
):
    # Arrange: a key is synced under its project. Then the project leaves the
    # organization, and the admin keys endpoint returns the same key id, which
    # is how OpenAI reports a project key once its project is no longer listed.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync_openai(
        neo4j_session,
        TEST_UPDATE_TAG,
        projects=tests.data.openai.projects.OPENAI_PROJECTS,
        admin_api_keys=[],
    )
    _sync_openai(
        neo4j_session,
        TEST_UPDATE_TAG + 1,
        projects=[],
        admin_api_keys=tests.data.openai.adminapikeys.OPENAI_ADMINAPIKEYS,
    )
    fact = ai_provider_api_key_hygiene.get_fact_by_id(
        "openai_nist_ai_stale_or_unowned_api_keys",
    )

    # Act
    rows = neo4j_session.execute_read(read_list_of_dicts_tx, fact.cypher_query)

    # Assert: one row per key, and the removed project's key no longer has a
    # project scope.
    assert sorted(
        (row["api_key_id"], row["has_project_or_workspace_scope"]) for row in rows
    ) == [
        ("key_abc", False),
        ("key_iegheiWieG2jupheeYin", False),
    ]
