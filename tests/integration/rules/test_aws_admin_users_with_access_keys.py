from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.aws_admin_users_with_access_keys import (
    aws_admin_users_with_access_keys,
)


def test_admin_users_with_access_keys(neo4j_session) -> None:
    # Admin via a group, admin via a direct policy, a scoped user, an admin whose
    # only key is inactive, and an admin with no keys. Only active keys owned by
    # admins are flagged.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (a:AWSAccount {id: '111111111111', name: 'prod'})
        CREATE (admin_policy:AWSPolicy {id: 'arn:aws:iam::aws:policy/AdministratorAccess', name: 'AdministratorAccess'})
        CREATE (admin_stmt:AWSPolicyStatement {id: 'admin-stmt', effect: 'Allow', action: ['*'], resource: ['*']})
        CREATE (scoped_policy:AWSPolicy {id: 'scoped-policy', name: 'S3ReadOnly'})
        CREATE (scoped_stmt:AWSPolicyStatement {id: 'scoped-stmt', effect: 'Allow', action: ['s3:Get*'], resource: ['*']})
        MERGE (admin_policy)-[:STATEMENT]->(admin_stmt)
        MERGE (scoped_policy)-[:STATEMENT]->(scoped_stmt)

        CREATE (admins:AWSGroup:AWSPrincipal {arn: 'arn:aws:iam::111111111111:group/Administrators', name: 'Administrators'})
        MERGE (admins)-[:POLICY]->(admin_policy)

        CREATE (group_admin:AWSUser:AWSPrincipal {arn: 'arn:aws:iam::111111111111:user/group-admin', name: 'group-admin'})
        CREATE (direct_admin:AWSUser:AWSPrincipal {arn: 'arn:aws:iam::111111111111:user/direct-admin', name: 'direct-admin'})
        CREATE (scoped_user:AWSUser:AWSPrincipal {arn: 'arn:aws:iam::111111111111:user/scoped', name: 'scoped'})
        CREATE (inactive_admin:AWSUser:AWSPrincipal {arn: 'arn:aws:iam::111111111111:user/inactive-admin', name: 'inactive-admin'})
        CREATE (keyless_admin:AWSUser:AWSPrincipal {arn: 'arn:aws:iam::111111111111:user/keyless-admin', name: 'keyless-admin'})
        MERGE (group_admin)-[:MEMBER_AWS_GROUP]->(admins)
        MERGE (direct_admin)-[:POLICY]->(admin_policy)
        MERGE (scoped_user)-[:POLICY]->(scoped_policy)
        MERGE (inactive_admin)-[:MEMBER_AWS_GROUP]->(admins)
        MERGE (keyless_admin)-[:MEMBER_AWS_GROUP]->(admins)

        CREATE (k1:AWSAccountAccessKey {accesskeyid: 'AKIAGROUPADMIN', status: 'Active'})
        CREATE (k2:AWSAccountAccessKey {accesskeyid: 'AKIAGROUPADMIN2', status: 'Active'})
        CREATE (k3:AWSAccountAccessKey {accesskeyid: 'AKIADIRECTADMIN', status: 'Active'})
        CREATE (k4:AWSAccountAccessKey {accesskeyid: 'AKIASCOPED', status: 'Active'})
        CREATE (k5:AWSAccountAccessKey {accesskeyid: 'AKIAINACTIVE', status: 'Inactive'})
        MERGE (group_admin)-[:AWS_ACCESS_KEY]->(k1)
        MERGE (group_admin)-[:AWS_ACCESS_KEY]->(k2)
        MERGE (direct_admin)-[:AWS_ACCESS_KEY]->(k3)
        MERGE (scoped_user)-[:AWS_ACCESS_KEY]->(k4)
        MERGE (inactive_admin)-[:AWS_ACCESS_KEY]->(k5)

        MERGE (a)-[:RESOURCE]->(admins)
        MERGE (a)-[:RESOURCE]->(group_admin)
        MERGE (a)-[:RESOURCE]->(direct_admin)
        MERGE (a)-[:RESOURCE]->(scoped_user)
        MERGE (a)-[:RESOURCE]->(inactive_admin)
        MERGE (a)-[:RESOURCE]->(keyless_admin)
        """
    )
    fact = aws_admin_users_with_access_keys.facts[0]

    findings = neo4j_session.execute_read(read_list_of_dicts_tx, fact.cypher_query)
    visual_rows = list(neo4j_session.run(fact.cypher_visual_query))
    count_rows = list(neo4j_session.run(fact.cypher_count_query))

    assert {
        (
            row["access_key_id"],
            row["user_name"],
            tuple(row["admin_policies"]),
            tuple(row["admin_groups"]),
        )
        for row in findings
    } == {
        (
            "AKIAGROUPADMIN",
            "group-admin",
            ("AdministratorAccess",),
            ("Administrators",),
        ),
        (
            "AKIAGROUPADMIN2",
            "group-admin",
            ("AdministratorAccess",),
            ("Administrators",),
        ),
        ("AKIADIRECTADMIN", "direct-admin", ("AdministratorAccess",), ()),
    }
    assert len(visual_rows) == 3
    # Denominator is every active key, admin or not.
    assert count_rows[0]["count"] == 4
