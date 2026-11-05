"""
Synthesized ARNs must use the partition of the region they are built for, so they
match the ARNs that AWS returns in AWS GovCloud (US) as well as in commercial regions.
"""

from unittest.mock import MagicMock

import pytest

from cartography.intel.aws.bedrock.agents import transform_agents
from cartography.intel.aws.ec2.instances import transform_ec2_instances
from cartography.intel.aws.ec2.internet_gateways import transform_internet_gateways
from cartography.intel.aws.ec2.key_pairs import transform_ec2_key_pairs
from cartography.intel.aws.ec2.network_acls import transform_network_acl_data
from cartography.intel.aws.ec2.volumes import transform_volumes
from cartography.intel.aws.rds import _get_db_subnet_group_arn
from cartography.intel.aws.redshift import _make_redshift_cluster_arn
from cartography.intel.aws.ses import get_ses_email_identities
from cartography.intel.aws.util.arns import get_account_partition
from cartography.intel.aws.util.arns import get_partition

ACCOUNT_ID = "111122223333"


@pytest.mark.parametrize(
    "region, partition",
    [
        ("us-east-1", "aws"),
        ("eu-west-1", "aws"),
        ("us-gov-west-1", "aws-us-gov"),
        ("us-gov-east-1", "aws-us-gov"),
        ("cn-north-1", "aws-cn"),
        # botocore sends a FIPS pseudo-region to its base region's partition.
        ("fips-us-gov-west-1", "aws-us-gov"),
        ("us-gov-east-1-fips", "aws-us-gov"),
        ("fips-us-east-1", "aws"),
        ("not-a-region", "aws"),
    ],
)
def test_get_partition(region, partition):
    assert get_partition(region) == partition


@pytest.mark.parametrize(
    "regions, session_region, partition",
    [
        (["us-gov-west-1"], "us-east-1", "aws-us-gov"),
        # Region discovery found nothing: use the session's region, then "aws".
        ([], "us-gov-west-1", "aws-us-gov"),
        ([], None, "aws"),
    ],
)
def test_get_account_partition(regions, session_region, partition):
    assert get_account_partition(regions, session_region) == partition


@pytest.mark.parametrize(
    "region, partition",
    [("us-east-1", "aws"), ("us-gov-west-1", "aws-us-gov")],
)
def test_ec2_instance_and_key_pair_arns(region, partition):
    # Arrange
    reservations = [
        {
            "ReservationId": "r-1",
            "OwnerId": ACCOUNT_ID,
            "Instances": [
                {
                    "InstanceId": "i-0123456789abcdef0",
                    "KeyName": "example-key",
                    "NetworkInterfaces": [],
                    "BlockDeviceMappings": [],
                },
            ],
        },
    ]
    key_pairs = [{"KeyName": "example-key", "KeyFingerprint": "1f:51:ae"}]

    # Act
    data = transform_ec2_instances(reservations, region, ACCOUNT_ID)
    described_key_pairs = transform_ec2_key_pairs(key_pairs, region, ACCOUNT_ID)

    # Assert
    assert (
        data.instance_list[0]["Arn"]
        == f"arn:{partition}:ec2:{region}:{ACCOUNT_ID}:instance/i-0123456789abcdef0"
    )
    key_pair_arn = f"arn:{partition}:ec2:{region}:{ACCOUNT_ID}:key-pair/example-key"
    # Both key pair producers must build the same id, or the node splits in two.
    assert data.keypair_list[0]["KeyPairArn"] == key_pair_arn
    assert described_key_pairs[0]["KeyPairArn"] == key_pair_arn


@pytest.mark.parametrize(
    "region, partition",
    [("us-east-1", "aws"), ("us-gov-west-1", "aws-us-gov")],
)
def test_ec2_network_arns(region, partition):
    # Act
    igws = transform_internet_gateways(
        [{"InternetGatewayId": "igw-0abc", "OwnerId": ACCOUNT_ID, "Attachments": []}],
        region,
        ACCOUNT_ID,
    )
    nacls = transform_network_acl_data(
        [
            {
                "NetworkAclId": "acl-0abc",
                "IsDefault": True,
                "VpcId": "vpc-0abc",
                "OwnerId": ACCOUNT_ID,
            },
        ],
        region,
        ACCOUNT_ID,
    )
    volumes = transform_volumes([{"VolumeId": "vol-0abc"}], region, ACCOUNT_ID)

    # Assert
    assert (
        igws[0]["Arn"]
        == f"arn:{partition}:ec2:{region}:{ACCOUNT_ID}:internet-gateway/igw-0abc"
    )
    assert (
        nacls.network_acls[0]["Arn"]
        == f"arn:{partition}:ec2:{region}:{ACCOUNT_ID}:network-acl/acl-0abc"
    )
    assert (
        volumes[0]["Arn"]
        == f"arn:{partition}:ec2:{region}:{ACCOUNT_ID}:volume/vol-0abc"
    )


@pytest.mark.parametrize(
    "region, partition",
    [("us-east-1", "aws"), ("us-gov-west-1", "aws-us-gov")],
)
def test_rds_and_redshift_arns(region, partition):
    assert (
        _get_db_subnet_group_arn(region, ACCOUNT_ID, "example-subnet-group")
        == f"arn:{partition}:rds:{region}:{ACCOUNT_ID}:subgrp:example-subnet-group"
    )
    assert (
        _make_redshift_cluster_arn(region, ACCOUNT_ID, "example-cluster")
        == f"arn:{partition}:redshift:{region}:{ACCOUNT_ID}:cluster:example-cluster"
    )


@pytest.mark.parametrize(
    "region, partition",
    [("us-east-1", "aws"), ("us-gov-west-1", "aws-us-gov")],
)
def test_bedrock_agent_arns(region, partition):
    # Arrange
    agents = [
        {
            "foundationModel": "anthropic.claude-v2",
            "knowledgeBaseSummaries": [{"knowledgeBaseId": "KB12345678"}],
            "guardrailConfiguration": {"guardrailIdentifier": "gr1234567890"},
        },
    ]

    # Act
    transformed = transform_agents(agents, region, ACCOUNT_ID)

    # Assert
    agent = transformed[0]
    assert (
        agent["foundation_model_arn"]
        == f"arn:{partition}:bedrock:{region}::foundation-model/anthropic.claude-v2"
    )
    assert agent["knowledge_base_arns"] == [
        f"arn:{partition}:bedrock:{region}:{ACCOUNT_ID}:knowledge-base/KB12345678",
    ]
    assert (
        agent["guardrail_arn"]
        == f"arn:{partition}:bedrock:{region}:{ACCOUNT_ID}:guardrail/gr1234567890"
    )


@pytest.mark.parametrize(
    "region, partition",
    [("us-east-1", "aws"), ("us-gov-west-1", "aws-us-gov")],
)
def test_ses_email_identity_arn(region, partition):
    # Arrange
    client = MagicMock()
    client.get_paginator.return_value.paginate.return_value = [
        {
            "EmailIdentities": [
                {"IdentityName": "example.com", "IdentityType": "DOMAIN"},
            ],
        },
    ]
    client.get_email_identity.return_value = {"VerificationStatus": "SUCCESS"}
    boto3_session = MagicMock()
    boto3_session.client.return_value = client

    # Act
    identities = get_ses_email_identities(boto3_session, region, ACCOUNT_ID)

    # Assert
    assert identities[0]["Arn"] == (
        f"arn:{partition}:ses:{region}:{ACCOUNT_ID}:identity/example.com"
    )
