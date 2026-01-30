from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.rds
from cartography.intel.aws.rds import sync
from tests.data.aws.rds import DESCRIBE_DBCLUSTERS_RESPONSE
from tests.data.aws.rds import DESCRIBE_DBINSTANCES_RESPONSE
from tests.data.aws.rds import DESCRIBE_DBSNAPSHOTS_RESPONSE
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def _create_test_security_groups(neo4j_session):
    """
    Create the EC2 security groups that are referenced in the RDS test data
    """
    security_group_ids = ["sg-some-othersg", "sg-some-sg", "sg-secgroup"]
    for sg_id in security_group_ids:
        neo4j_session.run(
            """
            MERGE (sg:EC2SecurityGroup{id: $sg_id})
            ON CREATE SET sg.firstseen = timestamp()
            SET sg.lastupdated = $update_tag
            """,
            sg_id=sg_id,
            update_tag=TEST_UPDATE_TAG,
        )


def _create_test_subnets(neo4j_session):
    """
    Create the EC2 subnets that are referenced in the RDS test data
    """
    subnet_ids = ["subnet-abcd", "subnet-3421", "subnet-4567", "subnet-1234"]
    for subnet_id in subnet_ids:
        neo4j_session.run(
            """
            MERGE (subnet:EC2Subnet{subnetid: $subnet_id})
            ON CREATE SET subnet.firstseen = timestamp()
            SET subnet.lastupdated = $update_tag
            """,
            subnet_id=subnet_id,
            update_tag=TEST_UPDATE_TAG,
        )


def test_load_rds_clusters_basic(neo4j_session):
    """Test that we successfully load RDS cluster nodes to the graph"""
    # Transform the data first
    transformed_data = cartography.intel.aws.rds.transform_rds_clusters(
        DESCRIBE_DBCLUSTERS_RESPONSE["DBClusters"]
    )
    cartography.intel.aws.rds.load_rds_clusters(
        neo4j_session,
        transformed_data,
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

    # Transform the data first
    transformed_data = cartography.intel.aws.rds.transform_rds_instances(
        DESCRIBE_DBINSTANCES_RESPONSE["DBInstances"], "us-east1", "1234"
    )
    cartography.intel.aws.rds.load_rds_instances(
        neo4j_session,
        transformed_data,
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
    # Transform the data first
    transformed_data = cartography.intel.aws.rds.transform_rds_instances(
        DESCRIBE_DBINSTANCES_RESPONSE["DBInstances"], "us-east1", "1234"
    )
    cartography.intel.aws.rds.load_rds_instances(
        neo4j_session,
        transformed_data,
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
    # Transform the data first
    transformed_data = cartography.intel.aws.rds.transform_rds_instances(
        DESCRIBE_DBINSTANCES_RESPONSE["DBInstances"], "us-east1", "1234"
    )
    cartography.intel.aws.rds.load_rds_instances(
        neo4j_session,
        transformed_data,
        "us-east1",
        "1234",
        TEST_UPDATE_TAG,
    )
    # Transform snapshot data first
    transformed_snapshot_data = cartography.intel.aws.rds.transform_rds_snapshots(
        DESCRIBE_DBSNAPSHOTS_RESPONSE["DBSnapshots"]
    )
    cartography.intel.aws.rds.load_rds_snapshots(
        neo4j_session,
        transformed_snapshot_data,
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


@patch.object(
    cartography.intel.aws.rds,
    "get_rds_snapshot_data",
    return_value=DESCRIBE_DBSNAPSHOTS_RESPONSE["DBSnapshots"],
)
@patch.object(
    cartography.intel.aws.rds,
    "get_rds_instance_data",
    return_value=DESCRIBE_DBINSTANCES_RESPONSE["DBInstances"],
)
@patch.object(
    cartography.intel.aws.rds,
    "get_rds_cluster_data",
    return_value=DESCRIBE_DBCLUSTERS_RESPONSE["DBClusters"],
)
def test_sync_rds_comprehensive(
    mock_get_clusters, mock_get_instances, mock_get_snapshots, neo4j_session
):
    """
    Test the comprehensive RDS sync function that loads clusters, instances, and snapshots
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _create_test_security_groups(neo4j_session)
    _create_test_subnets(neo4j_session)

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(
        neo4j_session, "RDSCluster", ["id", "db_cluster_identifier"]
    ) == {
        (
            "arn:aws:rds:us-east-1:some-arn:cluster:some-prod-db-iad-0",
            "some-prod-db-iad",
        ),
    }, "RDS clusters don't exist"

    assert check_nodes(
        neo4j_session, "RDSInstance", ["id", "db_instance_identifier"]
    ) == {
        ("arn:aws:rds:us-east-1:some-arn:db:some-prod-db-iad-0", "some-prod-db-iad-0"),
    }, "RDS instances don't exist"

    assert check_nodes(
        neo4j_session, "RDSSnapshot", ["id", "db_snapshot_identifier"]
    ) == {
        (
            "arn:aws:rds:us-east-1:some-arn:snapshot:some-prod-db-iad-0",
            "some-db-snapshot-identifier",
        ),
    }, "RDS snapshots don't exist"

    assert check_nodes(neo4j_session, "DBSubnetGroup", ["id", "name"]) == {
        ("arn:aws:rds:us-east-1:000000000000:subgrp:subnet-group-1", "subnet-group-1"),
    }, "DB subnet groups don't exist"

    assert check_rels(
        neo4j_session,
        "RDSCluster",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("arn:aws:rds:us-east-1:some-arn:cluster:some-prod-db-iad-0", "000000000000"),
    }, "RDS clusters are not connected to AWS account"

    assert check_rels(
        neo4j_session,
        "RDSInstance",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("arn:aws:rds:us-east-1:some-arn:db:some-prod-db-iad-0", "000000000000"),
    }, "RDS instances are not connected to AWS account"

    assert check_rels(
        neo4j_session,
        "RDSSnapshot",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("arn:aws:rds:us-east-1:some-arn:snapshot:some-prod-db-iad-0", "000000000000"),
    }, "RDS snapshots are not connected to AWS account"

    assert check_rels(
        neo4j_session,
        "DBSubnetGroup",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("arn:aws:rds:us-east-1:000000000000:subgrp:subnet-group-1", "000000000000"),
    }, "DB subnet groups are not connected to AWS account"

    assert check_rels(
        neo4j_session,
        "RDSInstance",
        "id",
        "DBSubnetGroup",
        "id",
        "MEMBER_OF_DB_SUBNET_GROUP",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:rds:us-east-1:some-arn:db:some-prod-db-iad-0",
            "arn:aws:rds:us-east-1:000000000000:subgrp:subnet-group-1",
        ),
    }, "RDS instances are not connected to DB subnet groups"

    assert check_rels(
        neo4j_session,
        "RDSInstance",
        "id",
        "EC2SecurityGroup",
        "id",
        "MEMBER_OF_EC2_SECURITY_GROUP",
        rel_direction_right=True,
    ) == {
        ("arn:aws:rds:us-east-1:some-arn:db:some-prod-db-iad-0", "sg-some-othersg"),
        ("arn:aws:rds:us-east-1:some-arn:db:some-prod-db-iad-0", "sg-some-sg"),
        ("arn:aws:rds:us-east-1:some-arn:db:some-prod-db-iad-0", "sg-secgroup"),
    }, "RDS instances are not connected to EC2 security groups"

    assert check_rels(
        neo4j_session,
        "RDSInstance",
        "id",
        "RDSCluster",
        "id",
        "IS_CLUSTER_MEMBER_OF",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:rds:us-east-1:some-arn:db:some-prod-db-iad-0",
            "arn:aws:rds:us-east-1:some-arn:cluster:some-prod-db-iad-0",
        ),
    }, "RDS instances are not connected to RDS clusters"

    assert check_rels(
        neo4j_session,
        "DBSubnetGroup",
        "id",
        "EC2Subnet",
        "subnetid",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("arn:aws:rds:us-east-1:000000000000:subgrp:subnet-group-1", "subnet-abcd"),
        ("arn:aws:rds:us-east-1:000000000000:subgrp:subnet-group-1", "subnet-3421"),
        ("arn:aws:rds:us-east-1:000000000000:subgrp:subnet-group-1", "subnet-4567"),
        ("arn:aws:rds:us-east-1:000000000000:subgrp:subnet-group-1", "subnet-1234"),
    }, "DB subnet groups are not connected to EC2 subnets"
