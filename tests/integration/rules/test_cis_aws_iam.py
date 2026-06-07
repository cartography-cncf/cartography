from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.cis_aws_iam import cis_aws_2_11_unused_credentials
from cartography.rules.data.rules.cis_aws_iam import cis_aws_2_13_access_key_not_rotated


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
