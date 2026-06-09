from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.cis_aws_iam import cis_aws_2_3_root_access_key
from cartography.rules.data.rules.cis_aws_iam import cis_aws_2_4_root_mfa
from cartography.rules.data.rules.cis_aws_iam import cis_aws_2_11_unused_credentials
from cartography.rules.data.rules.cis_aws_iam import cis_aws_2_13_access_key_not_rotated
from cartography.rules.data.rules.cis_aws_iam import cis_aws_2_15_admin_policy


def _reset_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def _get_fact(rule):
    return rule.facts[0]


def test_access_key_rules_parse_iso_datetime_strings_with_z(neo4j_session) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    neo4j_session.run(
        """
        CREATE (a:AWSAccount {id: '111111111111', name: 'prod'})
        CREATE (rotated_user:AWSUser {
            arn: 'arn:aws:iam::111111111111:user/old-rotation',
            name: 'old-rotation'
        })
        CREATE (used_user:AWSUser {
            arn: 'arn:aws:iam::111111111111:user/old-last-used',
            name: 'old-last-used'
        })
        CREATE (never_used_user:AWSUser {
            arn: 'arn:aws:iam::111111111111:user/never-used',
            name: 'never-used'
        })
        CREATE (rotated_key:AccountAccessKey {
            accesskeyid: 'AKIAOLDROTATION',
            status: 'Active',
            createdate_dt: '2020-02-17T22:57:02Z',
            lastuseddate_dt: '2999-02-17T22:57:02Z'
        })
        CREATE (used_key:AccountAccessKey {
            accesskeyid: 'AKIAOLDLASTUSED',
            status: 'Active',
            createdate_dt: '2020-02-17T22:57:02Z',
            lastuseddate_dt: '2020-03-17T22:57:02Z'
        })
        CREATE (never_used_key:AccountAccessKey {
            accesskeyid: 'AKIANEVERUSED',
            status: 'Active',
            createdate_dt: '2020-04-17T22:57:02Z'
        })
        MERGE (a)-[:RESOURCE]->(rotated_user)
        MERGE (a)-[:RESOURCE]->(used_user)
        MERGE (a)-[:RESOURCE]->(never_used_user)
        MERGE (rotated_user)-[:AWS_ACCESS_KEY]->(rotated_key)
        MERGE (used_user)-[:AWS_ACCESS_KEY]->(used_key)
        MERGE (never_used_user)-[:AWS_ACCESS_KEY]->(never_used_key)
        """
    )

    rotation_fact = _get_fact(cis_aws_2_13_access_key_not_rotated)
    unused_fact = _get_fact(cis_aws_2_11_unused_credentials)

    # Act
    rotation_findings = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        rotation_fact.cypher_query,
    )
    unused_findings = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        unused_fact.cypher_query,
    )
    rotation_visual_rows = list(neo4j_session.run(rotation_fact.cypher_visual_query))
    unused_visual_rows = list(neo4j_session.run(unused_fact.cypher_visual_query))

    # Assert
    assert {row["access_key_id"] for row in rotation_findings} == {
        "AKIAOLDROTATION",
        "AKIAOLDLASTUSED",
        "AKIANEVERUSED",
    }
    assert all(row["days_since_rotation"] > 90 for row in rotation_findings)
    assert {row["access_key_id"] for row in unused_findings} == {
        "AKIAOLDLASTUSED",
        "AKIANEVERUSED",
    }
    assert len(rotation_visual_rows) == 3
    assert len(unused_visual_rows) == 2


def test_root_access_key_flags_accounts_with_root_keys(neo4j_session) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    neo4j_session.run(
        """
        CREATE (:AWSAccount {id: '111111111111', name: 'has-root-key', account_access_keys_present: 1})
        CREATE (:AWSAccount {id: '222222222222', name: 'no-root-key', account_access_keys_present: 0})
        CREATE (:AWSAccount {id: '333333333333', name: 'unknown'})
        """
    )
    fact = _get_fact(cis_aws_2_3_root_access_key)

    # Act
    findings = neo4j_session.execute_read(read_list_of_dicts_tx, fact.cypher_query)
    visual_rows = list(neo4j_session.run(fact.cypher_visual_query))
    count_rows = list(neo4j_session.run(fact.cypher_count_query))

    # Assert
    assert {row["account_id"] for row in findings} == {"111111111111"}
    assert len(visual_rows) == 1
    # The 'unknown' account has no IAM summary data, so it must not be counted
    # as an evaluated asset (otherwise it would be reported as passing).
    assert count_rows[0]["count"] == 2


def test_root_mfa_flags_accounts_without_root_mfa(neo4j_session) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    neo4j_session.run(
        """
        CREATE (:AWSAccount {id: '111111111111', name: 'mfa-off', account_mfa_enabled: 0})
        CREATE (:AWSAccount {id: '222222222222', name: 'mfa-on', account_mfa_enabled: 1})
        CREATE (:AWSAccount {id: '333333333333', name: 'unknown'})
        """
    )
    fact = _get_fact(cis_aws_2_4_root_mfa)

    # Act
    findings = neo4j_session.execute_read(read_list_of_dicts_tx, fact.cypher_query)
    visual_rows = list(neo4j_session.run(fact.cypher_visual_query))
    count_rows = list(neo4j_session.run(fact.cypher_count_query))

    # Assert
    assert {row["account_id"] for row in findings} == {"111111111111"}
    assert len(visual_rows) == 1
    # The 'unknown' account has no IAM summary data, so it must not be counted
    # as an evaluated asset (otherwise it would be reported as passing).
    assert count_rows[0]["count"] == 2


def test_admin_policy_flags_attached_full_admin_policies(neo4j_session) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    neo4j_session.run(
        """
        CREATE (a:AWSAccount {id: '111111111111', name: 'prod'})
        CREATE (admin_user:AWSUser:AWSPrincipal {
            arn: 'arn:aws:iam::111111111111:user/admin',
            name: 'admin'
        })
        CREATE (scoped_user:AWSUser:AWSPrincipal {
            arn: 'arn:aws:iam::111111111111:user/scoped',
            name: 'scoped'
        })
        CREATE (inline_role:AWSRole:AWSPrincipal {
            arn: 'arn:aws:iam::111111111111:role/inline-admin',
            name: 'inline-admin'
        })
        CREATE (admin_policy:AWSManagedPolicy:AWSPolicy {
            id: 'arn:aws:iam::aws:policy/AdministratorAccess',
            arn: 'arn:aws:iam::aws:policy/AdministratorAccess',
            name: 'AdministratorAccess'
        })
        CREATE (scoped_policy:AWSManagedPolicy:AWSPolicy {
            id: 'arn:aws:iam::111111111111:policy/ReadOnly',
            arn: 'arn:aws:iam::111111111111:policy/ReadOnly',
            name: 'ReadOnly'
        })
        // Inline policies are loaded with arn = null; policy.id is the only stable id.
        CREATE (inline_policy:AWSInlinePolicy:AWSPolicy {
            id: 'arn:aws:iam::111111111111:role/inline-admin/inline_policy/AdminInline',
            arn: null,
            name: 'AdminInline'
        })
        // Managed policy nodes are global and survive cleanup even when no longer
        // attached. An unattached admin policy must not be counted as evaluated.
        CREATE (orphan_policy:AWSManagedPolicy:AWSPolicy {
            id: 'arn:aws:iam::aws:policy/OrphanAdmin',
            arn: 'arn:aws:iam::aws:policy/OrphanAdmin',
            name: 'OrphanAdmin'
        })
        CREATE (orphan_stmt:AWSPolicyStatement {
            id: 'arn:aws:iam::aws:policy/OrphanAdmin/statement/1',
            effect: 'Allow',
            action: ['*'],
            resource: ['*'],
            sid: 'OrphanAll'
        })
        CREATE (admin_stmt:AWSPolicyStatement {
            id: 'arn:aws:iam::aws:policy/AdministratorAccess/statement/1',
            effect: 'Allow',
            action: ['*'],
            resource: ['*'],
            sid: 'AdminAll'
        })
        CREATE (scoped_stmt:AWSPolicyStatement {
            id: 'arn:aws:iam::111111111111:policy/ReadOnly/statement/1',
            effect: 'Allow',
            action: ['s3:GetObject'],
            resource: ['*']
        })
        CREATE (inline_stmt:AWSPolicyStatement {
            id: 'arn:aws:iam::111111111111:role/inline-admin/inline_policy/AdminInline/statement/1',
            effect: 'Allow',
            action: ['*:*'],
            resource: ['*'],
            sid: 'InlineAdmin'
        })
        MERGE (a)-[:RESOURCE]->(admin_user)
        MERGE (a)-[:RESOURCE]->(scoped_user)
        MERGE (a)-[:RESOURCE]->(inline_role)
        MERGE (admin_user)-[:POLICY]->(admin_policy)
        MERGE (scoped_user)-[:POLICY]->(scoped_policy)
        MERGE (inline_role)-[:POLICY]->(inline_policy)
        MERGE (admin_policy)-[:STATEMENT]->(admin_stmt)
        MERGE (scoped_policy)-[:STATEMENT]->(scoped_stmt)
        MERGE (inline_policy)-[:STATEMENT]->(inline_stmt)
        MERGE (orphan_policy)-[:STATEMENT]->(orphan_stmt)
        """
    )
    fact = _get_fact(cis_aws_2_15_admin_policy)

    # Act
    findings = neo4j_session.execute_read(read_list_of_dicts_tx, fact.cypher_query)
    visual_rows = list(neo4j_session.run(fact.cypher_visual_query))
    count_rows = list(neo4j_session.run(fact.cypher_count_query))

    # Assert: both the managed and the inline admin policy are flagged, each with
    # a stable, non-null policy_id (the inline policy has no arn).
    assert {row["policy_id"] for row in findings} == {
        "arn:aws:iam::aws:policy/AdministratorAccess",
        "arn:aws:iam::111111111111:role/inline-admin/inline_policy/AdminInline",
    }
    assert all(row["policy_id"] is not None for row in findings)
    inline_finding = next(
        row for row in findings if row["policy_id"].endswith("AdminInline")
    )
    assert inline_finding["policy_arn"] is None
    assert len(visual_rows) == 2
    # Only attached policies are evaluated assets: admin + scoped + inline = 3.
    # The unattached OrphanAdmin managed policy must be excluded.
    assert count_rows[0]["count"] == 3
