from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.aws_admin_users_with_access_keys import (
    aws_admin_users_with_access_keys,
)

_FACT = aws_admin_users_with_access_keys.facts[0]

_POLICIES = """
CREATE (a:AWSAccount {id: '111111111111', name: 'prod'})
CREATE (admin:AWSPolicy {id: 'arn:aws:iam::aws:policy/AdministratorAccess', name: 'AdministratorAccess'})
CREATE (:AWSPolicyStatement {id: 'admin-stmt', effect: 'Allow', action: ['*'], resource: ['*']})<-[:STATEMENT]-(admin)
CREATE (service_admin:AWSPolicy {id: 'service-admin', name: 'ServiceAdmin'})
CREATE (:AWSPolicyStatement {id: 'service-admin-stmt', effect: 'Allow', action: ['*:*'], resource: ['*']})<-[:STATEMENT]-(service_admin)
CREATE (scoped:AWSPolicy {id: 'scoped', name: 'S3ReadOnly'})
CREATE (:AWSPolicyStatement {id: 'scoped-stmt', effect: 'Allow', action: ['s3:Get*'], resource: ['*']})<-[:STATEMENT]-(scoped)
CREATE (admins:AWSGroup:AWSPrincipal {arn: 'arn:aws:iam::111111111111:group/Administrators', name: 'Administrators'})-[:POLICY]->(admin)
CREATE (readers:AWSGroup:AWSPrincipal {arn: 'arn:aws:iam::111111111111:group/Readers', name: 'Readers'})-[:POLICY]->(scoped)
CREATE (user:AWSUser:AWSPrincipal {arn: 'arn:aws:iam::111111111111:user/alice', name: 'alice'})
MERGE (a)-[:RESOURCE]->(user)
"""


def _flagged(neo4j_session, grant: str, key_status: str = "Active") -> list[dict]:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        _POLICIES
        + grant
        + """
        CREATE (user)-[:AWS_ACCESS_KEY]->(:AWSAccountAccessKey {accesskeyid: 'AKIAALICE', status: $status})
        """,
        status=key_status,
    )
    return neo4j_session.execute_read(read_list_of_dicts_tx, _FACT.cypher_query)


def test_admin_via_group_with_active_key_is_flagged(neo4j_session) -> None:
    rows = _flagged(neo4j_session, "MERGE (user)-[:MEMBER_AWS_GROUP]->(admins)")

    assert [
        (r["access_key_id"], r["admin_policies"], r["admin_groups"]) for r in rows
    ] == [("AKIAALICE", ["AdministratorAccess"], ["Administrators"])]


def test_admin_via_direct_star_star_policy_is_flagged(neo4j_session) -> None:
    rows = _flagged(neo4j_session, "MERGE (user)-[:POLICY]->(service_admin)")

    assert [
        (r["access_key_id"], r["admin_policies"], r["admin_groups"]) for r in rows
    ] == [("AKIAALICE", ["ServiceAdmin"], [])]


def test_member_of_non_admin_group_is_not_flagged(neo4j_session) -> None:
    assert _flagged(neo4j_session, "MERGE (user)-[:MEMBER_AWS_GROUP]->(readers)") == []


def test_admin_with_inactive_key_is_not_flagged(neo4j_session) -> None:
    assert (
        _flagged(
            neo4j_session,
            "MERGE (user)-[:MEMBER_AWS_GROUP]->(admins)",
            key_status="Inactive",
        )
        == []
    )
