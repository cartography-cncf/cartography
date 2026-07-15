from cartography.intel.aws.label_migrations import AWS_LABEL_MIGRATIONS
from cartography.intel.aws.label_migrations import migrate_legacy_aws_labels

TEST_ACCOUNT_ID = "000000000000"
OTHER_ACCOUNT_ID = "111111111111"


def test_migrate_legacy_aws_labels_is_scoped_and_idempotent(neo4j_session):
    # Arrange
    neo4j_session.run(
        """
        CREATE (:AWSAccount{id: $account_id})
        CREATE (:AWSAccount{id: $other_account_id})
        """,
        account_id=TEST_ACCOUNT_ID,
        other_account_id=OTHER_ACCOUNT_ID,
    ).consume()
    original_element_ids = {}
    for index, migration in enumerate(AWS_LABEL_MIGRATIONS):
        resource_id = f"legacy-{index}"
        record = neo4j_session.run(
            f"""
            MATCH (account:AWSAccount{{id: $account_id}})
            CREATE (resource:{migration.old_label}{{id: $resource_id}})
            CREATE (account)-[:RESOURCE]->(resource)
            RETURN elementId(resource) AS element_id
            """,
            account_id=TEST_ACCOUNT_ID,
            resource_id=resource_id,
        ).single()
        original_element_ids[resource_id] = record["element_id"]

    neo4j_session.run(
        """
        MATCH (account:AWSAccount{id: $account_id})
        CREATE (resource:EC2Instance{id: 'other-account-instance'})
        CREATE (account)-[:RESOURCE]->(resource)
        """,
        account_id=OTHER_ACCOUNT_ID,
    ).consume()

    # Act
    migrate_legacy_aws_labels(neo4j_session, TEST_ACCOUNT_ID)
    migrate_legacy_aws_labels(neo4j_session, TEST_ACCOUNT_ID)

    # Assert
    records = neo4j_session.run(
        """
        MATCH (:AWSAccount{id: $account_id})-[:RESOURCE]->(resource)
        RETURN resource.id AS id,
               elementId(resource) AS element_id,
               labels(resource) AS labels
        """,
        account_id=TEST_ACCOUNT_ID,
    )
    migrated_resources = {record["id"]: record for record in records}
    assert len(migrated_resources) == len(AWS_LABEL_MIGRATIONS)

    for index, migration in enumerate(AWS_LABEL_MIGRATIONS):
        resource_id = f"legacy-{index}"
        record = migrated_resources[resource_id]
        assert record["element_id"] == original_element_ids[resource_id]
        assert migration.old_label in record["labels"]
        assert migration.new_label in record["labels"]

    other_account_record = neo4j_session.run(
        """
        MATCH (:AWSAccount{id: $account_id})-[:RESOURCE]->(resource:EC2Instance)
        RETURN resource:AWSEC2Instance AS migrated
        """,
        account_id=OTHER_ACCOUNT_ID,
    ).single()
    assert other_account_record["migrated"] is False
