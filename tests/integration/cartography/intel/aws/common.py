def create_test_account(neo4j_session, test_account_id, test_update_tag):
    # Create Test AWSAccount
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag, aws :Tenant
        """,
        aws_account_id=test_account_id,
        aws_update_tag=test_update_tag,
    )
