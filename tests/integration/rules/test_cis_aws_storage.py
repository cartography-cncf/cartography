from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.cis_aws_storage import aws_s3_block_public_access


def _reset_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def _get_fact(rule):
    return rule.facts[0]


def test_block_public_access_respects_account_level_bpa(neo4j_session) -> None:
    # Arrange: three accounts, each owning a bucket with NULL bucket-level BPA.
    #  - covered:   account-level BPA fully enforced -> bucket must NOT be flagged
    #  - partial:   account-level BPA only partially enforced -> bucket flagged
    #  - uncovered: no account-level BPA node at all -> bucket flagged
    # Plus a bucket with its own full bucket-level BPA, which is never flagged.
    _reset_graph(neo4j_session)
    neo4j_session.run(
        """
        CREATE (covered:AWSAccount {id: '111111111111', name: 'covered'})
        CREATE (partial:AWSAccount {id: '222222222222', name: 'partial'})
        CREATE (uncovered:AWSAccount {id: '333333333333', name: 'uncovered'})

        CREATE (covered_bucket:S3Bucket {id: 'covered-bucket', name: 'covered-bucket', region: 'us-east-1'})
        CREATE (partial_bucket:S3Bucket {id: 'partial-bucket', name: 'partial-bucket', region: 'us-east-1'})
        CREATE (uncovered_bucket:S3Bucket {id: 'uncovered-bucket', name: 'uncovered-bucket', region: 'us-east-1'})
        CREATE (self_blocked_bucket:S3Bucket {
            id: 'self-blocked-bucket',
            name: 'self-blocked-bucket',
            region: 'us-east-1',
            block_public_acls: true,
            ignore_public_acls: true,
            block_public_policy: true,
            restrict_public_buckets: true
        })
        // Explicit partially-disabling bucket-level config under the fully-enforced
        // account: the bucket does NOT purely inherit account BPA, so it must still
        // be flagged (account-level enforcement must not mask an explicit override).
        CREATE (override_bucket:S3Bucket {
            id: 'override-bucket',
            name: 'override-bucket',
            region: 'us-east-1',
            block_public_acls: false
        })

        // Account-level BPA is account-global but stored one node per region; a
        // region with no config (us-west-2) must not defeat the us-east-1 enforcement.
        CREATE (covered_pab_east:S3AccountPublicAccessBlock {
            id: '111111111111:us-east-1',
            block_public_acls: true,
            ignore_public_acls: true,
            block_public_policy: true,
            restrict_public_buckets: true
        })
        CREATE (partial_pab:S3AccountPublicAccessBlock {
            id: '222222222222:us-east-1',
            block_public_acls: true,
            ignore_public_acls: true,
            block_public_policy: false,
            restrict_public_buckets: false
        })

        MERGE (covered)-[:RESOURCE]->(covered_bucket)
        MERGE (partial)-[:RESOURCE]->(partial_bucket)
        MERGE (uncovered)-[:RESOURCE]->(uncovered_bucket)
        MERGE (covered)-[:RESOURCE]->(self_blocked_bucket)
        MERGE (covered)-[:RESOURCE]->(override_bucket)
        MERGE (covered)-[:RESOURCE]->(covered_pab_east)
        MERGE (partial)-[:RESOURCE]->(partial_pab)
        """
    )
    fact = _get_fact(aws_s3_block_public_access)

    # Act
    findings = neo4j_session.execute_read(read_list_of_dicts_tx, fact.cypher_query)
    visual_rows = list(neo4j_session.run(fact.cypher_visual_query))
    count_rows = list(neo4j_session.run(fact.cypher_count_query))

    # Assert: partial + uncovered buckets are flagged, and so is the override bucket
    # (explicit bucket-level config means it does not purely inherit account BPA).
    # The covered bucket (all-NULL under enforced account) and the self-blocked bucket
    # are not flagged.
    assert {row["bucket_id"] for row in findings} == {
        "partial-bucket",
        "uncovered-bucket",
        "override-bucket",
    }
    assert len(visual_rows) == 3
    # The count (denominator) still covers every evaluated bucket.
    assert count_rows[0]["count"] == 5
