from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.iam_role_external_account_trust import (
    iam_role_external_account_trust,
)


def _reset_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def _get_fact():
    return iam_role_external_account_trust.facts[0]


def test_flags_roles_trusting_unsynced_accounts(neo4j_session) -> None:
    """
    A role in a synced account (`inscope = true`) trusting a principal owned by an
    account that Cartography does not sync must be flagged. Trusts toward principals
    in another in-scope account, or with no owning account, must not.
    """
    _reset_graph(neo4j_session)
    neo4j_session.run(
        """
        CREATE (synced:AWSAccount {id: '111111111111', name: 'prod', inscope: true})
        CREATE (synced2:AWSAccount {id: '222222222222', name: 'staging', inscope: true})
        CREATE (external:AWSAccount {id: '999999999999'})

        CREATE (role_external:AWSRole {
            arn: 'arn:aws:iam::111111111111:role/trusts-external',
            name: 'trusts-external'
        })
        CREATE (role_internal:AWSRole {
            arn: 'arn:aws:iam::111111111111:role/trusts-internal',
            name: 'trusts-internal'
        })

        CREATE (ext_principal:AWSPrincipal {arn: 'arn:aws:iam::999999999999:root'})
        CREATE (int_principal:AWSPrincipal {arn: 'arn:aws:iam::222222222222:root'})

        MERGE (synced)-[:RESOURCE]->(role_external)
        MERGE (synced)-[:RESOURCE]->(role_internal)
        MERGE (external)-[:RESOURCE]->(ext_principal)
        MERGE (synced2)-[:RESOURCE]->(int_principal)
        MERGE (role_external)-[:TRUSTS_AWS_PRINCIPAL]->(ext_principal)
        MERGE (role_internal)-[:TRUSTS_AWS_PRINCIPAL]->(int_principal)
        """
    )

    findings = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        _get_fact().cypher_query,
    )

    assert findings == [
        {
            "role_arn": "arn:aws:iam::111111111111:role/trusts-external",
            "role_name": "trusts-external",
            "account_id": "111111111111",
            "external_account_id": "999999999999",
            "trusted_principal_arn": "arn:aws:iam::999999999999:root",
        }
    ]

    visual_rows = list(neo4j_session.run(_get_fact().cypher_visual_query))
    assert len(visual_rows) == 1
