import cartography.intel.aws.rds
from tests.data.aws.rds import DESCRIBE_DBCLUSTERS_RESPONSE
from tests.data.aws.rds import DESCRIBE_DBINSTANCES_RESPONSE
TEST_UPDATE_TAG = 123456789


def test_load_rds_clusters_basic(neo4j_session):
    """Test that we successfully load RDS cluster nodes to the graph"""
    cartography.intel.aws.rds.load_rds_clusters(
        neo4j_session,
        DESCRIBE_DBCLUSTERS_RESPONSE['DBClusters'],
        'us-east1',
        '1234',
        TEST_UPDATE_TAG,
    )
    query = """MATCH(rds:RDSCluster) RETURN rds.id, rds.arn, rds.storage_encrypted, rds.avalability_zones"""
    nodes = neo4j_session.run(query)

    actual_nodes = {(n['rds.id'], n['rds.arn'], n['rds.storage_encrypted'], n['AvailabilityZones']) for n in nodes}
    expected_nodes = {
        (
            'arn:aws:rds:us-east-1:some-arn:cluster:some-prod-db-iad-0',
            'arn:aws:rds:us-east-1:some-arn:cluster:some-prod-db-iad-0',
            True,
            ['us-east-1e'],
        ),
    }
    assert actual_nodes == expected_nodes

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (r:RDSInstance)-[:IS_CLUSTER_MEMBER_OF]->(c:RDSCluster)
        RETURN r.db_cluster_identifier, c.db_cluster_identifier;
        """,
    )
    expected = {
        (
            'some-prod-db-iad',
            'some-prod-db-iad',
        ),
    }

    actual = {
        (r['r.db_cluster_identifier'], r['n2.db_cluster_identifier']) for r in result
    }

    assert actual == expected


def test_load_rds_instances_basic(neo4j_session):
    """Test that we successfully load RDS instance nodes to the graph"""
    cartography.intel.aws.rds.load_rds_instances(
        neo4j_session,
        DESCRIBE_DBINSTANCES_RESPONSE['DBInstances'],
        'us-east1',
        '1234',
        TEST_UPDATE_TAG,
    )
    query = """MATCH(rds:RDSInstance) RETURN rds.id, rds.arn, rds.storage_encrypted"""
    nodes = neo4j_session.run(query)

    actual_nodes = {(n['rds.id'], n['rds.arn'], n['rds.storage_encrypted']) for n in nodes}
    expected_nodes = {
        (
            'arn:aws:rds:us-east-1:some-arn:db:some-prod-db-iad-0',
            'arn:aws:rds:us-east-1:some-arn:db:some-prod-db-iad-0',
            True,
        ),
    }
    assert actual_nodes == expected_nodes
