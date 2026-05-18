from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.mfa_missing import missing_mfa_rule


def _reset_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def _get_fact(fact_id: str):
    return next(fact for fact in missing_mfa_rule.facts if fact.id == fact_id)


def test_aws_mfa_fact_skips_users_with_a_device(neo4j_session) -> None:
    """
    The `:MFA_DEVICE` edge is modeled as `(AWSUser)-[:MFA_DEVICE]->(AWSMfaDevice)`
    (`AWSMfaDeviceToAWSUserRel` carries `LinkDirection.INWARD`). The fact
    must check that direction; an inverted predicate would flag every
    AWS user as missing MFA.
    """
    _reset_graph(neo4j_session)
    neo4j_session.run(
        """
        CREATE (a:AWSAccount {id: '111111111111', name: 'acme'})
        CREATE (u_with:AWSUser {
            arn: 'arn:aws:iam::111111111111:user/with-mfa',
            name: 'with-mfa'
        })
        CREATE (u_without:AWSUser {
            arn: 'arn:aws:iam::111111111111:user/without-mfa',
            name: 'without-mfa'
        })
        CREATE (mfa:AWSMfaDevice {
            id: 'arn:aws:iam::111111111111:mfa/with-mfa',
            serialnumber: 'arn:aws:iam::111111111111:mfa/with-mfa'
        })
        MERGE (a)-[:RESOURCE]->(u_with)
        MERGE (a)-[:RESOURCE]->(u_without)
        MERGE (u_with)-[:MFA_DEVICE]->(mfa)
        """
    )

    findings = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        _get_fact("missing-mfa-aws").cypher_query,
    )

    ids = [row["id"] for row in findings]
    assert ids == ["arn:aws:iam::111111111111:user/without-mfa"]


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
