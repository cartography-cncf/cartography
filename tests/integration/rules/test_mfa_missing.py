from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.mfa_missing import missing_mfa_rule


def _reset_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def _get_fact(fact_id: str):
    return next(fact for fact in missing_mfa_rule.facts if fact.id == fact_id)


def test_ontology_mfa_fact_returns_users_with_explicit_false(neo4j_session) -> None:
    """
    The cross-cloud fact looks for `_ont_has_mfa = false` on UserAccount
    nodes. NULL means unknown, not missing, so users without the field
    must NOT appear in findings.
    """
    _reset_graph(neo4j_session)
    neo4j_session.run(
        """
        CREATE (no_mfa:UserAccount {
            id: 'cloudflare-no-mfa',
            _ont_email: 'no-mfa@example.com',
            _ont_has_mfa: false,
            _ont_active: true,
            _ont_source: 'cloudflare'
        })
        CREATE (yes_mfa:UserAccount {
            id: 'cloudflare-yes-mfa',
            _ont_email: 'yes-mfa@example.com',
            _ont_has_mfa: true,
            _ont_active: true,
            _ont_source: 'cloudflare'
        })
        CREATE (unknown_mfa:UserAccount {
            id: 'okta-unknown-mfa',
            _ont_email: 'unknown@example.com',
            _ont_active: true,
            _ont_source: 'okta'
        })
        CREATE (inactive:UserAccount {
            id: 'gh-inactive',
            _ont_email: 'inactive@example.com',
            _ont_has_mfa: false,
            _ont_active: false,
            _ont_source: 'github'
        })
        """
    )

    findings = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        _get_fact("missing-mfa-ontology").cypher_query,
    )

    assert [row["id"] for row in findings] == ["cloudflare-no-mfa"]
