import cartography.intel.aws.rds
from tests.data.aws.rds import DESCRIBE_DBCLUSTERS_RESPONSE
from tests.data.aws.rds import DESCRIBE_DBINSTANCES_RESPONSE
from tests.data.aws.rds import DESCRIBE_DBSNAPSHOTS_RESPONSE

TEST_UPDATE_TAG = 123456789


def test_load_rds_clusters_basic(neo4j_session):
    """Test that we successfully load RDS cluster nodes to the graph"""
    cartography.intel.aws.rds.load_rds_clusters(
        neo4j_session,
        DESCRIBE_DBCLUSTERS_RESPONSE["DBClusters"],
        "us-east1",
        "1234",
        TEST_UPDATE_TAG,
    )
    query = """MATCH(rds:RDSCluster) RETURN rds.id, rds.arn, rds.storage_encrypted"""
    nodes = neo4j_session.run(query)

    actual_nodes = {
        (n["rds.id"], n["rds.arn"], n["rds.storage_encrypted"]) for n in nodes
    }
    expected_nodes = {
        (
            "arn:aws:rds:us-east-1:some-arn:cluster:some-prod-db-iad-0",
            "arn:aws:rds:us-east-1:some-arn:cluster:some-prod-db-iad-0",
            True,
        ),
    }
    assert actual_nodes == expected_nodes

    cartography.intel.aws.rds.load_rds_instances(
        neo4j_session,
        DESCRIBE_DBINSTANCES_RESPONSE["DBInstances"],
        "us-east1",
        "1234",
        TEST_UPDATE_TAG,
    )

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (r:RDSInstance)-[:IS_CLUSTER_MEMBER_OF]->(c:RDSCluster)
        RETURN r.db_cluster_identifier, c.db_cluster_identifier;
        """,
    )
    expected = {
        (
            "some-prod-db-iad",
            "some-prod-db-iad",
        ),
    }

    actual = {
        (r["r.db_cluster_identifier"], r["c.db_cluster_identifier"]) for r in result
    }

    assert actual == expected

    # Cleanup to not interfere with other rds tests
    result = neo4j_session.run(
        """
        MATCH (r:RDSInstance)
        DETACH DELETE r
        """,
    )


def test_load_rds_instances_basic(neo4j_session):
    """Test that we successfully load RDS instance nodes to the graph"""
    cartography.intel.aws.rds.load_rds_instances(
        neo4j_session,
        DESCRIBE_DBINSTANCES_RESPONSE["DBInstances"],
        "us-east1",
        "1234",
        TEST_UPDATE_TAG,
    )
    query = """MATCH(rds:RDSInstance) RETURN rds.id, rds.arn, rds.storage_encrypted"""
    nodes = neo4j_session.run(query)

    actual_nodes = {
        (n["rds.id"], n["rds.arn"], n["rds.storage_encrypted"]) for n in nodes
    }
    expected_nodes = {
        (
            "arn:aws:rds:us-east-1:some-arn:db:some-prod-db-iad-0",
            "arn:aws:rds:us-east-1:some-arn:db:some-prod-db-iad-0",
            True,
        ),
    }
    assert actual_nodes == expected_nodes


def test_load_rds_snapshots_basic(neo4j_session):
    """Test that we successfully load RDS snapshots to the graph"""
    cartography.intel.aws.rds.load_rds_instances(
        neo4j_session,
        DESCRIBE_DBINSTANCES_RESPONSE["DBInstances"],
        "us-east1",
        "1234",
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.rds.load_rds_snapshots(
        neo4j_session,
        DESCRIBE_DBSNAPSHOTS_RESPONSE["DBSnapshots"],
        "us-east1",
        "1234",
        TEST_UPDATE_TAG,
    )

    query = """MATCH(rds:RDSSnapshot) RETURN rds.id, rds.arn, rds.db_snapshot_identifier, rds.db_instance_identifier"""
    snapshots = neo4j_session.run(query)

    actual_snapshots = {
        (
            n["rds.id"],
            n["rds.arn"],
            n["rds.db_snapshot_identifier"],
            n["rds.db_instance_identifier"],
        )
        for n in snapshots
    }
    expected_snapshots = {
        (
            "arn:aws:rds:us-east-1:some-arn:snapshot:some-prod-db-iad-0",
            "arn:aws:rds:us-east-1:some-arn:snapshot:some-prod-db-iad-0",
            "some-db-snapshot-identifier",
            "some-prod-db-iad-0",
        ),
    }
    assert actual_snapshots == expected_snapshots

    query = """MATCH(rdsInstance:RDSInstance)-[:IS_SNAPSHOT_SOURCE]-(rdsSnapshot:RDSSnapshot)
               RETURN rdsInstance.id, rdsSnapshot.id"""
    results = neo4j_session.run(query)

    actual_results = {(n["rdsInstance.id"], n["rdsSnapshot.id"]) for n in results}
    expected_results = {
        (
            "arn:aws:rds:us-east-1:some-arn:db:some-prod-db-iad-0",
            "arn:aws:rds:us-east-1:some-arn:snapshot:some-prod-db-iad-0",
        ),
    }
    assert actual_results == expected_results
