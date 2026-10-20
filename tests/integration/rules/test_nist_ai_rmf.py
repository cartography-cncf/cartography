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


def test_ai_app_sensitive_scopes_flags_microsoft_365_consents(neo4j_session):
    # Arrange: scopes as Entra consent grants record them, from one user and from an
    # administrator on behalf of every user.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (tenant:AzureTenant {id: 'tenant-1'})
        CREATE (tenant)-[:RESOURCE]->(u1:EntraUser:UserAccount {id: 'user-1'})
        CREATE (tenant)-[:RESOURCE]->(:EntraUser:UserAccount {id: 'user-2'})
        CREATE (user_consented:EntraServicePrincipal:ThirdPartyApp {
            id: 'sp-user-consented', display_name: 'Example LLM Assistant',
            _ont_source: 'microsoft', _ont_client_id: 'app-1'
        })
        CREATE (u1)-[:AUTHORIZED {scopes: [
            'https://graph.microsoft.com/User.Read',
            'https://graph.microsoft.com/Mail.Read'
        ]}]->(user_consented)
        CREATE (admin_consented:EntraServicePrincipal:ThirdPartyApp {
            id: 'sp-admin-consented', display_name: 'Example GPT Connector',
            _ont_source: 'microsoft', _ont_client_id: 'app-2'
        })
        CREATE (tenant)-[:ADMIN_CONSENTED {scopes: [
            'https://graph.microsoft.com/User.Read',
            '00000003-0000-0ff1-ce00-000000000000/AllSites.Read'
        ]}]->(admin_consented)
        """
    )
    user_fact, admin_fact = ai_third_party_app_sensitive_scopes.facts

    # Act
    user_rows = neo4j_session.execute_read(
        read_list_of_dicts_tx, user_fact.cypher_query
    )
    admin_rows = neo4j_session.execute_read(
        read_list_of_dicts_tx, admin_fact.cypher_query
    )

    # Assert
    assert [
        (row["asset_node_id"], row["authorized_identity_count"], row["risky_scopes"])
        for row in user_rows
    ] == [("sp-user-consented", 1, ["https://graph.microsoft.com/Mail.Read"])]
    assert [
        (row["asset_node_id"], row["authorized_identity_count"], row["risky_scopes"])
        for row in admin_rows
    ] == [
        (
            "sp-admin-consented",
            2,
            ["00000003-0000-0ff1-ce00-000000000000/AllSites.Read"],
        )
    ]
