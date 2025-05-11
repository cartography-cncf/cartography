import cartography.intel.aws.elasticache
import tests.data.aws.elasticache

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def test_load_clusters(neo4j_session):
    neo4j_session.run("MERGE(a:AWSAccount{id:$account});", account=TEST_ACCOUNT_ID)
    elasticache_data = tests.data.aws.elasticache.DESCRIBE_CACHE_CLUSTERS
    clusters = elasticache_data["CacheClusters"]
    cartography.intel.aws.elasticache.load_elasticache_clusters(
        neo4j_session,
        clusters,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_cluster_arns = {cluster["ARN"] for cluster in clusters}
    nodes = neo4j_session.run(
        """
        MATCH (r:ElasticacheCluster) RETURN r.arn
        """,
    )
    actual_cluster_arns = {n["r.arn"] for n in nodes}
    assert actual_cluster_arns == expected_cluster_arns

    # Test the connection to the account
    expected_cluster_arns = {(cluster["ARN"], TEST_ACCOUNT_ID) for cluster in clusters}
    nodes = neo4j_session.run(
        """
        MATCH (r:ElasticacheCluster)<-[:RESOURCE]-(a:AWSAccount) RETURN r.arn, a.id
        """,
    )
    actual_cluster_arns = {(n["r.arn"], n["a.id"]) for n in nodes}
    assert actual_cluster_arns == expected_cluster_arns

    # Test undefined topic_arns
    topic_arns_in_test_data = {
        cluster.get("NotificationConfiguration", {}).get("TopicArn")
        for cluster in clusters
    }
    expected_topic_arns = {
        topic for topic in topic_arns_in_test_data if topic
    }  # Filter out Nones.
    nodes = neo4j_session.run(
        """
        MATCH (r:ElasticacheTopic) RETURN r.arn
        """,
    )
    actual_topic_arns = {n["r.arn"] for n in nodes}
    assert actual_topic_arns == expected_topic_arns
