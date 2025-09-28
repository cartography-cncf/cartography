import neo4j


def create_test_azure_subscription(
    neo4j_session: neo4j.Session, subscription_id: str, update_tag: int
) -> None:

    neo4j_session.run(
        """
        MERGE (sub:AzureSubscription{id: $subscription_id})
        ON CREATE SET sub.firstseen = timestamp()
        SET sub.lastupdated = $update_tag,
            sub.name = $display_name,
            sub.state = $state
        """,
        subscription_id=subscription_id,
        display_name="Test Subscription",
        state="Enabled",
        update_tag=update_tag,
    )
