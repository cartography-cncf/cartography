from copy import deepcopy
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.instances
import cartography.intel.aws.iam
from cartography.intel.aws.ec2.instances import sync_ec2_instances
from tests.data.aws.ec2.instances import DESCRIBE_INSTANCES
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.ec2.instances,
    "get_ec2_instances",
    return_value=DESCRIBE_INSTANCES["Reservations"],
)
def test_sync_ec2_instances(mock_get_instances, neo4j_session):
    """
    Ensure that instances actually get loaded and have their key fields
    """
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    sync_ec2_instances(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert EC2 instances exist
    assert check_nodes(neo4j_session, "AWSEC2Instance", ["id", "instanceid"]) == {
        ("i-01", "i-01"),
        ("i-02", "i-02"),
        ("i-03", "i-03"),
        ("i-04", "i-04"),
    }

    assert check_nodes(
        neo4j_session,
        "AWSEC2FilesystemSnapshot",
        [
            "id",
            "instance_id",
            "volume_id",
            "kind",
            "region",
            "lastupdated",
            "_ont_kind",
            "_ont_source",
        ],
    ) == {
        (
            f"aws:ec2:{instance_id}:rootfs",
            instance_id,
            volume_id,
            "rootfs",
            TEST_REGION,
            TEST_UPDATE_TAG,
            "rootfs",
            "aws",
        )
        for instance_id, volume_id in (
            ("i-01", "vol-0df"),
            ("i-02", "vol-03"),
            ("i-03", "vol-09"),
            ("i-04", "vol-04"),
        )
    }
    assert check_rels(
        neo4j_session,
        "AWSEC2FilesystemSnapshot",
        "id",
        "AWSEBSVolume",
        "id",
        "SNAPSHOT_OF",
        rel_direction_right=True,
    ) == {
        ("aws:ec2:i-01:rootfs", "vol-0df"),
        ("aws:ec2:i-02:rootfs", "vol-03"),
        ("aws:ec2:i-03:rootfs", "vol-09"),
        ("aws:ec2:i-04:rootfs", "vol-04"),
    }
    assert check_rels(
        neo4j_session,
        "AWSEC2Instance",
        "id",
        "FilesystemSnapshot",
        "id",
        "SCANNED_AS",
        rel_direction_right=True,
    ) == {
        (instance_id, f"aws:ec2:{instance_id}:rootfs")
        for instance_id in ("i-01", "i-02", "i-03", "i-04")
    }
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "FilesystemSnapshot",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, f"aws:ec2:{instance_id}:rootfs")
        for instance_id in ("i-01", "i-02", "i-03", "i-04")
    }

    assert check_nodes(
        neo4j_session,
        "AWSEC2Instance",
        [
            "id",
            "metadatahttptokens",
            "imdsaccessmode",
            "imdsv1enabled",
            "imdsv2required",
            "metadatahttpendpoint",
            "metadatahttpprotocolipv6",
            "metadatainstancetags",
        ],
    ) == {
        (
            "i-01",
            "optional",
            "v1_or_v2",
            True,
            False,
            "enabled",
            "disabled",
            "disabled",
        ),
        ("i-02", None, None, None, None, None, None, None),
        ("i-03", None, None, None, None, None, None, None),
        ("i-04", "required", "v2_only", False, True, "enabled", "enabled", "enabled"),
    }

    # Assert that instances are connected to their expected reservations
    assert check_rels(
        neo4j_session,
        "AWSEC2Reservation",
        "reservationid",
        "AWSEC2Instance",
        "id",
        "MEMBER_OF_EC2_RESERVATION",
        rel_direction_right=False,
    ) == {
        ("r-01", "i-01"),
        ("r-02", "i-02"),
        ("r-03", "i-03"),
        ("r-03", "i-04"),
    }

    # Assert network interface to instances
    assert check_rels(
        neo4j_session,
        "AWSNetworkInterface",
        "id",
        "AWSEC2Instance",
        "id",
        "NETWORK_INTERFACE",
        rel_direction_right=False,
    ) == {
        ("eni-de", "i-01"),
        ("eni-87", "i-02"),
        ("eni-75", "i-03"),
        ("eni-76", "i-04"),
    }

    # Assert network interface to subnet
    assert check_rels(
        neo4j_session,
        "AWSNetworkInterface",
        "id",
        "AWSEC2Subnet",
        "id",
        "PART_OF_SUBNET",
        rel_direction_right=True,
    ) == {
        ("eni-75", "SOME_SUBNET_1"),
        ("eni-76", "SOME_SUBNET_1"),
        ("eni-87", "SOME_SUBNET_1"),
    }

    # #1316: Assert the fields of the subnet are as expected
    assert check_nodes(
        neo4j_session, "AWSEC2Subnet", ["id", "subnetid", "subnet_id"]
    ) == {
        ("SOME_SUBNET_1", "SOME_SUBNET_1", "SOME_SUBNET_1"),
    }

    # Assert network interface to security group
    assert check_rels(
        neo4j_session,
        "AWSNetworkInterface",
        "id",
        "AWSEC2SecurityGroup",
        "id",
        "MEMBER_OF_EC2_SECURITY_GROUP",
        rel_direction_right=True,
    ) == {
        ("eni-75", "SOME_GROUP_ID_2"),
        ("eni-75", "THIS_IS_A_SG_ID"),
        ("eni-76", "SOME_GROUP_ID_2"),
        ("eni-76", "THIS_IS_A_SG_ID"),
        ("eni-87", "SOME_GROUP_ID_2"),
        ("eni-87", "SOME_GROUP_ID_3"),
        ("eni-de", "SOME_GROUP_ID_2"),
        ("eni-de", "sg-GROUP-ID"),
    }

    # Assert network interface to AWS account
    assert check_rels(
        neo4j_session,
        "AWSNetworkInterface",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("eni-75", "000000000000"),
        ("eni-76", "000000000000"),
        ("eni-87", "000000000000"),
        ("eni-de", "000000000000"),
    }

    # Assert EC2 Key Pair to AWS account
    assert check_rels(
        neo4j_session,
        "AWSEC2KeyPair",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("arn:aws:ec2:us-east-1:000000000000:key-pair/boot", "000000000000"),
    }

    # Assert EC2 Key Pair to EC2 instance
    assert check_rels(
        neo4j_session,
        "AWSEC2KeyPair",
        "id",
        "AWSEC2Instance",
        "id",
        "SSH_LOGIN_TO",
        rel_direction_right=True,
    ) == {
        ("arn:aws:ec2:us-east-1:000000000000:key-pair/boot", "i-01"),
        ("arn:aws:ec2:us-east-1:000000000000:key-pair/boot", "i-02"),
        ("arn:aws:ec2:us-east-1:000000000000:key-pair/boot", "i-03"),
        ("arn:aws:ec2:us-east-1:000000000000:key-pair/boot", "i-04"),
    }

    # Assert EC2 Security Group to EC2 Instance
    assert check_rels(
        neo4j_session,
        "AWSEC2SecurityGroup",
        "id",
        "AWSEC2Instance",
        "id",
        "MEMBER_OF_EC2_SECURITY_GROUP",
        rel_direction_right=False,
    ) == {
        ("sg-GROUP-ID", "i-01"),
        ("SOME_GROUP_ID_2", "i-01"),
        ("SOME_GROUP_ID_2", "i-02"),
        ("SOME_GROUP_ID_2", "i-03"),
        ("SOME_GROUP_ID_2", "i-04"),
        ("SOME_GROUP_ID_3", "i-02"),
        ("THIS_IS_A_SG_ID", "i-03"),
        ("THIS_IS_A_SG_ID", "i-04"),
    }

    # Assert EC2 Security Group to AWS account
    assert check_rels(
        neo4j_session,
        "AWSEC2SecurityGroup",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("SOME_GROUP_ID_2", "000000000000"),
        ("SOME_GROUP_ID_3", "000000000000"),
        ("THIS_IS_A_SG_ID", "000000000000"),
        ("sg-GROUP-ID", "000000000000"),
    }

    # Assert EC2 Subnet to EC2 Instance
    assert check_rels(
        neo4j_session,
        "AWSEC2Subnet",
        "id",
        "AWSEC2Instance",
        "id",
        "PART_OF_SUBNET",
        rel_direction_right=False,
    ) == {
        ("SOME_SUBNET_1", "i-02"),
        ("SOME_SUBNET_1", "i-03"),
        ("SOME_SUBNET_1", "i-04"),
    }

    # Assert EC2 Subnet to AWS account
    assert check_rels(
        neo4j_session,
        "AWSEC2Subnet",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("SOME_SUBNET_1", "000000000000"),
    }

    # Assert EBS Volume to EC2 Instance
    assert check_rels(
        neo4j_session,
        "AWSEBSVolume",
        "id",
        "AWSEC2Instance",
        "id",
        "ATTACHED_TO",
        rel_direction_right=True,
    ) == {
        ("vol-0df", "i-01"),
        ("vol-03", "i-02"),
        ("vol-09", "i-03"),
        ("vol-04", "i-04"),
    }

    # Assert EBS Volume to AWS account
    assert check_rels(
        neo4j_session,
        "AWSEBSVolume",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("vol-03", "000000000000"),
        ("vol-04", "000000000000"),
        ("vol-09", "000000000000"),
        ("vol-0df", "000000000000"),
    }


def test_sync_ec2_filesystem_snapshots_refresh_and_scoped_cleanup(
    neo4j_session, mocker
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    other_account_id = "111111111111"
    other_region = "us-west-2"
    for account_id in (TEST_ACCOUNT_ID, other_account_id):
        create_test_account(neo4j_session, account_id, TEST_UPDATE_TAG)
    other_reservations = [
        {
            "ReservationId": "r-other",
            "OwnerId": other_account_id,
            "Instances": [
                {
                    "InstanceId": "i-other",
                    "State": {"Name": "running"},
                    "Architecture": "x86_64",
                    "RootDeviceType": "ebs",
                    "RootDeviceName": "/dev/sda1",
                    "BlockDeviceMappings": [
                        {
                            "DeviceName": "/dev/sda1",
                            "Ebs": {
                                "VolumeId": "vol-other",
                                "DeleteOnTermination": True,
                            },
                        },
                    ],
                    "NetworkInterfaces": [],
                },
            ],
        },
    ]
    get_instances = mocker.patch.object(
        cartography.intel.aws.ec2.instances,
        "get_ec2_instances",
        return_value=other_reservations,
    )
    boto3_session = MagicMock()
    sync_ec2_instances(
        neo4j_session,
        boto3_session,
        [other_region],
        other_account_id,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": other_account_id},
    )
    reservations = deepcopy(DESCRIBE_INSTANCES["Reservations"])
    # Put a data disk first to ensure only the root device becomes the scan source.
    reservations[2]["Instances"][0]["BlockDeviceMappings"].insert(
        0,
        {
            "DeviceName": "/dev/sdf",
            "Ebs": {"VolumeId": "vol-data", "DeleteOnTermination": False},
        },
    )
    get_instances.return_value = reservations

    # Act
    sync_ec2_instances(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, "FilesystemSnapshot", ["id"]) == {
        (f"aws:ec2:{instance_id}:rootfs",)
        for instance_id in ("i-01", "i-02", "i-03", "i-04", "i-other")
    }
    assert check_rels(
        neo4j_session,
        "FilesystemSnapshot",
        "id",
        "BlockStorage",
        "id",
        "SNAPSHOT_OF",
        rel_direction_right=True,
    ) == {
        ("aws:ec2:i-01:rootfs", "vol-0df"),
        ("aws:ec2:i-02:rootfs", "vol-03"),
        ("aws:ec2:i-03:rootfs", "vol-09"),
        ("aws:ec2:i-04:rootfs", "vol-04"),
        ("aws:ec2:i-other:rootfs", "vol-other"),
    }

    # Arrange
    reservations[0]["Instances"][0]["State"]["Name"] = "stopped"
    reservations[1]["Instances"] = []
    reservations[2]["Instances"][0]["BlockDeviceMappings"][1]["Ebs"][
        "VolumeId"
    ] = "vol-replaced-root"
    next_update_tag = TEST_UPDATE_TAG + 1

    # Act
    sync_ec2_instances(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        next_update_tag,
        {"UPDATE_TAG": next_update_tag, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "FilesystemSnapshot",
        ["id", "volume_id", "region", "lastupdated"],
    ) == {
        ("aws:ec2:i-03:rootfs", "vol-replaced-root", TEST_REGION, next_update_tag),
        ("aws:ec2:i-04:rootfs", "vol-04", TEST_REGION, next_update_tag),
        ("aws:ec2:i-other:rootfs", "vol-other", other_region, TEST_UPDATE_TAG),
    }
    assert check_rels(
        neo4j_session,
        "FilesystemSnapshot",
        "id",
        "BlockStorage",
        "id",
        "SNAPSHOT_OF",
        rel_direction_right=True,
    ) == {
        ("aws:ec2:i-03:rootfs", "vol-replaced-root"),
        ("aws:ec2:i-04:rootfs", "vol-04"),
        ("aws:ec2:i-other:rootfs", "vol-other"),
    }
    # The old volume still exists, so the stale edge was removed by target cleanup.
    assert ("vol-09",) in check_nodes(neo4j_session, "AWSEBSVolume", ["id"])
    assert check_rels(
        neo4j_session,
        "AWSEC2Instance",
        "id",
        "FilesystemSnapshot",
        "id",
        "SCANNED_AS",
        rel_direction_right=True,
    ) == {
        (instance_id, f"aws:ec2:{instance_id}:rootfs")
        for instance_id in ("i-03", "i-04", "i-other")
    }
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "FilesystemSnapshot",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "aws:ec2:i-03:rootfs"),
        (TEST_ACCOUNT_ID, "aws:ec2:i-04:rootfs"),
        (other_account_id, "aws:ec2:i-other:rootfs"),
    }
