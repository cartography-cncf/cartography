import cartography.intel.github.app_installations
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.nist_ai_rmf import ai_third_party_app_inventory
from cartography.rules.data.rules.nist_ai_rmf import ai_third_party_app_sensitive_scopes

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


def test_ai_app_sensitive_scopes_flags_microsoft_365_mail_consent(neo4j_session):
    # Arrange: scopes as Entra consent grants record them.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (u:EntraUser:UserAccount {id: 'user-1'})
        CREATE (sp:EntraServicePrincipal:ThirdPartyApp {
            id: 'sp-vendor', app_id: 'vendor-app-id', display_name: 'Example LLM Assistant',
            _ont_source: 'microsoft', _ont_client_id: 'vendor-app-id'
        })
        CREATE (u)-[:AUTHORIZED {scopes: [
            'https://graph.microsoft.com/User.Read',
            'https://graph.microsoft.com/Mail.Read'
        ]}]->(sp)
        """
    )
    fact = ai_third_party_app_sensitive_scopes.facts[0]

    # Act
    rows = neo4j_session.execute_read(read_list_of_dicts_tx, fact.cypher_query)

    # Assert
    assert [(row["asset_node_id"], row["risky_scopes"]) for row in rows] == [
        ("sp-vendor", ["https://graph.microsoft.com/Mail.Read"]),
    ]
