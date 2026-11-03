import copy
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.instances
import cartography.intel.aws.rds
import cartography.intel.aws.redshift
import cartography.intel.aws.resourcegroupstaggingapi as rgta
from cartography.client.core.tx import load
from cartography.intel.aws.ec2.instances import sync_ec2_instances
from cartography.intel.aws.ec2.load_balancers import load_load_balancers
from cartography.intel.aws.resourcegroupstaggingapi import sync
from cartography.models.aws.ec2.instances import EC2InstanceSchema
from tests.data.aws import govcloud
from tests.data.aws.ec2.instances import DESCRIBE_INSTANCES
from tests.data.aws.resourcegroupstaggingapi import GET_RESOURCES_RESPONSE
from tests.data.aws.resourcegroupstaggingapi import GET_RESOURCES_RESPONSE_LB_US_EAST_1
from tests.data.aws.resourcegroupstaggingapi import GET_RESOURCES_RESPONSE_LB_US_WEST_2
from tests.data.aws.resourcegroupstaggingapi import LOAD_BALANCERS_US_EAST_1
from tests.data.aws.resourcegroupstaggingapi import LOAD_BALANCERS_US_WEST_2
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "1234"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.ec2.instances,
    "get_ec2_instances",
    return_value=DESCRIBE_INSTANCES["Reservations"],
)
@patch.object(
    rgta,
    "get_tags",
    return_value=copy.deepcopy(GET_RESOURCES_RESPONSE),
)
def test_sync_tags(mock_get_tags, mock_get_instances, neo4j_session):
    """
    Verify that sync() creates AWSTag nodes and (Resource)-[:TAGGED]->(AWSTag) relationships.
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # First sync EC2 instances so we have resources to tag
    sync_ec2_instances(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Act - sync tags using the sync() function
    # Use a limited mapping to only test ec2:instance tags
    test_mapping = {
        "ec2:instance": rgta.TAG_RESOURCE_TYPE_MAPPINGS["ec2:instance"],
    }
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
        tag_resource_type_mappings=test_mapping,
    )

    # Assert - AWSTag nodes exist and carry the ontology _ont_source.
    assert check_nodes(
        neo4j_session, "AWSTag", ["id", "key", "value", "_ont_source"]
    ) == {
        ("TestKey:TestValue", "TestKey", "TestValue", "aws"),
    }

    # Assert - Relationships (AWSEC2Instance)-[TAGGED]->(AWSTag)
    assert check_rels(
        neo4j_session,
        "AWSEC2Instance",
        "id",
        "AWSTag",
        "id",
        "TAGGED",
        rel_direction_right=True,
    ) == {
        ("i-01", "TestKey:TestValue"),
    }

    # Assert - AWSTag nodes no longer carry a region property (#1094). The
    # property is meaningless on a shared Key:Value node and has been dropped.
    region_props = neo4j_session.run(
        "MATCH (n:AWSTag) RETURN keys(n) AS props",
    ).single()["props"]
    assert "region" not in region_props


def test_sync_tags_scopes_to_correct_region(neo4j_session):
    """
    Regression test for #1137: two load balancers with the same name in two
    different regions must each be tagged with only their own region's tags.
    The classic LB tag mapping is keyed by the non-unique `name`, so before the
    region predicate both LBs were cross-tagged.
    """
    # Arrange - account plus two same-named LBs in two regions
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    load_load_balancers(
        neo4j_session,
        LOAD_BALANCERS_US_EAST_1,
        "us-east-1",
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    load_load_balancers(
        neo4j_session,
        LOAD_BALANCERS_US_WEST_2,
        "us-west-2",
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Act - sync tags for both regions; each region returns its own tag data
    tag_data_by_region = {
        "us-east-1": GET_RESOURCES_RESPONSE_LB_US_EAST_1,
        "us-west-2": GET_RESOURCES_RESPONSE_LB_US_WEST_2,
    }

    def fake_get_tags(_boto3_session, _resource_types, region):
        return copy.deepcopy(tag_data_by_region[region])

    test_mapping = {
        "elasticloadbalancing:loadbalancer": rgta.TAG_RESOURCE_TYPE_MAPPINGS[
            "elasticloadbalancing:loadbalancer"
        ],
    }
    with patch.object(rgta, "get_tags", side_effect=fake_get_tags):
        sync(
            neo4j_session,
            boto3_session,
            ["us-east-1", "us-west-2"],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
            tag_resource_type_mappings=test_mapping,
        )

    # Assert - each LB is tagged only with its own region's tag, identified by
    # the region-specific `id`.
    assert check_rels(
        neo4j_session,
        "LoadBalancer",
        "id",
        "AWSTag",
        "id",
        "TAGGED",
        rel_direction_right=True,
    ) == {
        (LOAD_BALANCERS_US_EAST_1[0]["id"], "env:prod"),
        (LOAD_BALANCERS_US_WEST_2[0]["id"], "env:staging"),
    }


@patch.object(cartography.intel.aws.redshift, "get_redshift_cluster_data")
@patch.object(cartography.intel.aws.rds, "get_rds_event_subscription_data")
@patch.object(cartography.intel.aws.rds, "get_rds_snapshot_data", return_value=[])
@patch.object(cartography.intel.aws.rds, "get_rds_cluster_data", return_value=[])
@patch.object(cartography.intel.aws.rds, "get_rds_instance_data")
def test_sync_tags_govcloud_arn_ids(
    mock_get_rds_instances,
    mock_get_rds_clusters,
    mock_get_rds_snapshots,
    mock_get_rds_event_subscriptions,
    mock_get_redshift_clusters,
    neo4j_session,
):
    """
    RDS DB subnet groups and Redshift clusters use an ARN that Cartography builds as their
    node id. In AWS GovCloud (US), the tagging API returns "arn:aws-us-gov:" ARNs, so the
    built ids must use that partition for the tags to attach.
    """
    # Arrange
    neo4j_session.run(
        "MATCH (n) WHERE n:AWSTag OR n:AWSDBSubnetGroup OR n:AWSRedshiftCluster "
        "DETACH DELETE n",
    )
    mock_get_rds_instances.return_value = govcloud.DESCRIBE_DBINSTANCES_RESPONSE[
        "DBInstances"
    ]
    mock_get_rds_event_subscriptions.return_value = []
    mock_get_redshift_clusters.return_value = govcloud.REDSHIFT_CLUSTERS
    boto3_session = MagicMock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}
    for account_id in ("000000000000", "1111"):
        create_test_account(neo4j_session, account_id, TEST_UPDATE_TAG)
    common_job_parameters["AWS_ID"] = "000000000000"
    cartography.intel.aws.rds.sync(
        neo4j_session,
        boto3_session,
        [govcloud.GOV_REGION],
        "000000000000",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    common_job_parameters["AWS_ID"] = "1111"
    cartography.intel.aws.redshift.sync(
        neo4j_session,
        boto3_session,
        [govcloud.GOV_REGION],
        "1111",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    test_mapping = {
        resource_type: rgta.TAG_RESOURCE_TYPE_MAPPINGS[resource_type]
        for resource_type in ("rds:subgrp", "redshift:cluster")
    }

    # Act
    for account_id in ("000000000000", "1111"):
        with patch.object(
            rgta,
            "get_tags",
            return_value=copy.deepcopy(
                [
                    mapping
                    for mapping in govcloud.GET_RESOURCES_RESPONSE
                    if f":{account_id}:" in mapping["ResourceARN"]
                ],
            ),
        ):
            sync(
                neo4j_session,
                boto3_session,
                [govcloud.GOV_REGION],
                account_id,
                TEST_UPDATE_TAG,
                {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": account_id},
                tag_resource_type_mappings=test_mapping,
            )

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSDBSubnetGroup",
        "id",
        "AWSTag",
        "id",
        "TAGGED",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws-us-gov:rds:us-gov-west-1:000000000000:subgrp:subnet-group-1",
            "TestKey:TestValue",
        ),
    }
    assert check_rels(
        neo4j_session,
        "AWSRedshiftCluster",
        "id",
        "AWSTag",
        "id",
        "TAGGED",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws-us-gov:redshift:us-gov-west-1:1111:cluster:my-cluster",
            "TestKey:TestValue",
        ),
    }


ACCOUNT_A = "000000000000"
ACCOUNT_B = "000000000001"


def _load_instance(neo4j_session, instance_id, account_id, update_tag):
    load(
        neo4j_session,
        EC2InstanceSchema(),
        [{"InstanceId": instance_id}],
        Region=TEST_REGION,
        AWS_ID=account_id,
        lastupdated=update_tag,
    )


def _sync_instance_tags(neo4j_session, account_id, tagging_response, update_tag):
    with patch.object(rgta, "get_tags", return_value=copy.deepcopy(tagging_response)):
        sync(
            neo4j_session,
            MagicMock(),
            [TEST_REGION],
            account_id,
            update_tag,
            {"UPDATE_TAG": update_tag, "AWS_ID": account_id},
            tag_resource_type_mappings={
                "ec2:instance": rgta.TAG_RESOURCE_TYPE_MAPPINGS["ec2:instance"],
            },
        )


def _instance_tagging_response(account_id, instance_id, tags):
    return [
        {
            "ResourceARN": f"arn:aws:ec2:{TEST_REGION}:{account_id}:instance/{instance_id}",
            "Tags": [{"Key": key, "Value": value} for key, value in tags],
        },
    ]


def test_cleanup_keeps_tag_shared_with_another_account(neo4j_session):
    """
    AWSTag nodes are keyed by Key:Value and shared across accounts. When one
    account drops a tag that another account still uses, the first account's
    cleanup must remove only its own TAGGED relationship, not the shared node.
    """
    # Arrange - two accounts whose instances share the env:prod tag
    neo4j_session.run(
        "MATCH (n) WHERE n:AWSTag OR n:AWSEC2Instance DETACH DELETE n",
    )
    first_sync, second_sync = 1, 2
    for account_id, instance_id in ((ACCOUNT_A, "i-a"), (ACCOUNT_B, "i-b")):
        create_test_account(neo4j_session, account_id, first_sync)
        _load_instance(neo4j_session, instance_id, account_id, first_sync)
        _sync_instance_tags(
            neo4j_session,
            account_id,
            _instance_tagging_response(account_id, instance_id, [("env", "prod")]),
            first_sync,
        )

    # Act - account A syncs again, and its instance no longer has env:prod
    _load_instance(neo4j_session, "i-a", ACCOUNT_A, second_sync)
    _sync_instance_tags(
        neo4j_session,
        ACCOUNT_A,
        _instance_tagging_response(ACCOUNT_A, "i-a", [("team", "core")]),
        second_sync,
    )
    rgta.cleanup_orphan_tags(neo4j_session, {"UPDATE_TAG": second_sync})

    # Assert - the shared tag survives with B's relationship; A's is gone
    assert check_nodes(neo4j_session, "AWSTag", ["id"]) == {
        ("env:prod",),
        ("team:core",),
    }
    assert check_rels(
        neo4j_session,
        "AWSEC2Instance",
        "id",
        "AWSTag",
        "id",
        "TAGGED",
        rel_direction_right=True,
    ) == {
        ("i-a", "team:core"),
        ("i-b", "env:prod"),
    }


def test_cleanup_removes_tag_no_resource_uses(neo4j_session):
    """
    A tag node is deleted once the last resource that used it drops it. The
    per-account sync only removes the stale relationship; the node is removed by
    the end-of-run orphan sweep.
    """
    # Arrange
    neo4j_session.run(
        "MATCH (n) WHERE n:AWSTag OR n:AWSEC2Instance DETACH DELETE n",
    )
    create_test_account(neo4j_session, ACCOUNT_A, 1)
    _load_instance(neo4j_session, "i-a", ACCOUNT_A, 1)
    _sync_instance_tags(
        neo4j_session,
        ACCOUNT_A,
        _instance_tagging_response(ACCOUNT_A, "i-a", [("env", "prod")]),
        1,
    )

    # Act
    _load_instance(neo4j_session, "i-a", ACCOUNT_A, 2)
    _sync_instance_tags(neo4j_session, ACCOUNT_A, [], 2)
    rgta.cleanup_orphan_tags(neo4j_session, {"UPDATE_TAG": 2})

    # Assert
    assert check_nodes(neo4j_session, "AWSTag", ["id"]) == set()


def test_orphan_sweep_removes_tag_of_resource_missing_from_graph(neo4j_session):
    """
    The tagging API reports resources whose own sync did not load them. Their tags
    are loaded but never linked, and the end-of-run sweep removes them.
    """
    # Arrange
    neo4j_session.run(
        "MATCH (n) WHERE n:AWSTag OR n:AWSEC2Instance DETACH DELETE n",
    )
    create_test_account(neo4j_session, ACCOUNT_A, 1)
    _load_instance(neo4j_session, "i-a", ACCOUNT_A, 1)
    tagging_response = _instance_tagging_response(
        ACCOUNT_A, "i-a", [("env", "prod")]
    ) + _instance_tagging_response(ACCOUNT_A, "i-missing", [("team", "core")])

    # Act - the account sync loads both tags but links only the existing resource's
    _sync_instance_tags(neo4j_session, ACCOUNT_A, tagging_response, 1)

    # Assert
    assert check_nodes(neo4j_session, "AWSTag", ["id"]) == {
        ("env:prod",),
        ("team:core",),
    }
    assert check_rels(
        neo4j_session,
        "AWSEC2Instance",
        "id",
        "AWSTag",
        "id",
        "TAGGED",
        rel_direction_right=True,
    ) == {("i-a", "env:prod")}

    # Act - the end-of-run sweep
    rgta.cleanup_orphan_tags(neo4j_session, {"UPDATE_TAG": 1})

    # Assert - the unlinked tag is removed even though this sync wrote it
    assert check_nodes(neo4j_session, "AWSTag", ["id"]) == {("env:prod",)}


def test_orphan_sweep_keeps_linked_tags(neo4j_session):
    """
    The sweep must never delete a tag that a relationship uses, including one last
    written by an earlier sync.
    """
    # Arrange - account A was last synced at 1, account B syncs at 2
    neo4j_session.run(
        "MATCH (n) WHERE n:AWSTag OR n:AWSEC2Instance DETACH DELETE n",
    )
    for account_id, instance_id, update_tag, tags in (
        (ACCOUNT_A, "i-a", 1, [("env", "prod")]),
        (ACCOUNT_B, "i-b", 2, [("team", "core")]),
    ):
        create_test_account(neo4j_session, account_id, update_tag)
        _load_instance(neo4j_session, instance_id, account_id, update_tag)
        _sync_instance_tags(
            neo4j_session,
            account_id,
            _instance_tagging_response(account_id, instance_id, tags),
            update_tag,
        )

    # Act
    rgta.cleanup_orphan_tags(neo4j_session, {"UPDATE_TAG": 2})

    # Assert
    assert check_nodes(neo4j_session, "AWSTag", ["id", "lastupdated"]) == {
        ("env:prod", 1),
        ("team:core", 2),
    }
    assert check_rels(
        neo4j_session,
        "AWSEC2Instance",
        "id",
        "AWSTag",
        "id",
        "TAGGED",
        rel_direction_right=True,
    ) == {
        ("i-a", "env:prod"),
        ("i-b", "team:core"),
    }


def test_orphan_sweep_batches_and_keeps_tags_of_a_newer_sync(neo4j_session):
    """
    The sweep runs in batches of the configured size, and leaves unlinked tags
    stamped by a newer sync for that sync to link.
    """
    # Arrange - two orphans from this sync, one unlinked tag from a newer sync
    neo4j_session.run(
        "MATCH (n) WHERE n:AWSTag OR n:AWSEC2Instance DETACH DELETE n",
    )
    create_test_account(neo4j_session, ACCOUNT_A, 2)
    _sync_instance_tags(
        neo4j_session,
        ACCOUNT_A,
        _instance_tagging_response(
            ACCOUNT_A, "i-missing", [("env", "prod"), ("team", "core")]
        ),
        2,
    )
    _sync_instance_tags(
        neo4j_session,
        ACCOUNT_A,
        _instance_tagging_response(ACCOUNT_A, "i-later", [("owner", "ops")]),
        3,
    )

    # Act
    rgta.cleanup_orphan_tags(
        neo4j_session, {"UPDATE_TAG": 2, "aws_tagging_api_cleanup_batch": 1}
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSTag", ["id"]) == {("owner:ops",)}


def test_cleanup_removes_stale_relationships_written_before_matchlinks(
    neo4j_session,
):
    """
    TAGGED relationships written before AWSTag moved to the data model carry no
    _sub_resource_id. The account sync must still remove them once stale, which
    leaves the tag for the end-of-run sweep.
    """
    # Arrange - a pre-existing relationship without MatchLink scoping properties
    neo4j_session.run(
        "MATCH (n) WHERE n:AWSTag OR n:AWSEC2Instance DETACH DELETE n",
    )
    create_test_account(neo4j_session, ACCOUNT_A, 1)
    _load_instance(neo4j_session, "i-a", ACCOUNT_A, 1)
    neo4j_session.run(
        """
        MATCH (i:AWSEC2Instance{id: 'i-a'})
        MERGE (t:AWSTag:Tag{id: 'env:prod'})
        SET t.key = 'env', t.value = 'prod', t.lastupdated = 1
        MERGE (i)-[r:TAGGED]->(t)
        SET r.lastupdated = 1
        """,
    )

    # Act
    _load_instance(neo4j_session, "i-a", ACCOUNT_A, 2)
    _sync_instance_tags(neo4j_session, ACCOUNT_A, [], 2)

    # Assert
    assert (
        check_rels(
            neo4j_session,
            "AWSEC2Instance",
            "id",
            "AWSTag",
            "id",
            "TAGGED",
            rel_direction_right=True,
        )
        == set()
    )

    # Act
    rgta.cleanup_orphan_tags(neo4j_session, {"UPDATE_TAG": 2})

    # Assert
    assert check_nodes(neo4j_session, "AWSTag", ["id"]) == set()
