from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectTimeoutError

from cartography.intel.aws.ec2 import load_balancer_v2s


def _make_client_error(code: str, status_code: int, operation: str) -> ClientError:
    return ClientError(
        {
            "Error": {"Code": code, "Message": "temporary service issue"},
            "ResponseMetadata": {"HTTPStatusCode": status_code},
        },
        operation,
    )


def test_get_loadbalancer_v2_data_raises_transient_region_failure_on_connect_timeout():
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    paginator = client.get_paginator.return_value
    paginator.paginate.side_effect = ConnectTimeoutError(
        endpoint_url="https://elasticloadbalancing.me-central-1.amazonaws.com/",
        error="timed out",
    )

    with pytest.raises(load_balancer_v2s.ELBV2TransientRegionFailure):
        load_balancer_v2s.get_loadbalancer_v2_data(boto3_session, "me-central-1")


def test_sync_load_balancer_v2s_skips_cleanup_after_transient_region_failure(mocker):
    mocker.patch(
        "cartography.intel.aws.ec2.load_balancer_v2s._migrate_legacy_loadbalancerv2_labels"
    )
    mocker.patch(
        "cartography.intel.aws.ec2.load_balancer_v2s.get_loadbalancer_v2_data",
        side_effect=load_balancer_v2s.ELBV2TransientRegionFailure("temporary failure"),
    )
    cleanup = mocker.patch(
        "cartography.intel.aws.ec2.load_balancer_v2s.cleanup_load_balancer_v2s"
    )

    load_balancer_v2s.sync_load_balancer_v2s(
        MagicMock(),
        MagicMock(),
        ["me-central-1"],
        "123456789012",
        1,
        {"AWS_ID": "123456789012", "UPDATE_TAG": 1},
    )

    cleanup.assert_not_called()


def test_sync_load_balancer_v2s_skips_cleanup_after_retryable_client_error(mocker):
    mocker.patch(
        "cartography.intel.aws.ec2.load_balancer_v2s._migrate_legacy_loadbalancerv2_labels"
    )
    mocker.patch(
        "cartography.intel.aws.ec2.load_balancer_v2s.get_loadbalancer_v2_data",
        side_effect=_make_client_error(
            "ServiceUnavailable",
            503,
            "DescribeLoadBalancers",
        ),
    )
    cleanup = mocker.patch(
        "cartography.intel.aws.ec2.load_balancer_v2s.cleanup_load_balancer_v2s"
    )

    load_balancer_v2s.sync_load_balancer_v2s(
        MagicMock(),
        MagicMock(),
        ["me-central-1"],
        "123456789012",
        1,
        {"AWS_ID": "123456789012", "UPDATE_TAG": 1},
    )

    cleanup.assert_not_called()


def test_sync_load_balancer_v2_expose_skips_cleanup_after_transient_region_failure(
    mocker,
):
    mocker.patch(
        "cartography.intel.aws.ec2.load_balancer_v2s.get_loadbalancer_v2_data",
        side_effect=load_balancer_v2s.ELBV2TransientRegionFailure("temporary failure"),
    )
    cleanup = mocker.patch(
        "cartography.intel.aws.ec2.load_balancer_v2s.cleanup_load_balancer_v2_expose"
    )

    load_balancer_v2s.sync_load_balancer_v2_expose(
        MagicMock(),
        MagicMock(),
        ["me-central-1"],
        "123456789012",
        1,
        {"AWS_ID": "123456789012", "UPDATE_TAG": 1},
    )

    cleanup.assert_not_called()


def test_transform_load_balancer_v2_lowercases_dnsname_but_not_id():
    raw_dns_name = "My-ALB-1234567890.us-east-1.elb.amazonaws.com"
    data = [
        {
            "DNSName": raw_dns_name,
            "LoadBalancerName": "My-ALB",
            "CreatedTime": "2024-01-01 00:00:00",
            "Listeners": [
                {
                    "ListenerArn": "arn:aws:elasticloadbalancing:::listener/my-alb/1",
                    "Port": 443,
                    "Protocol": "HTTPS",
                },
            ],
            "TargetGroups": [
                {
                    "TargetGroupArn": "arn:aws:elasticloadbalancing:::targetgroup/tg/1",
                    "TargetGroupName": "tg",
                    "TargetType": "instance",
                    "Targets": ["i-01"],
                },
            ],
        },
    ]

    lb_data, listener_data, tg_data, target_data = (
        load_balancer_v2s._transform_load_balancer_v2_data(data)
    )

    # `DNSName` is the node id and the join key for listeners and target groups, so it
    # must stay byte-for-byte what AWS returned.
    assert lb_data[0]["DNSName"] == raw_dns_name
    assert lb_data[0]["DNSNameLower"] == raw_dns_name.lower()
    assert listener_data[0]["LoadBalancerId"] == raw_dns_name
    assert tg_data[0]["LoadBalancerId"] == [raw_dns_name]
    assert target_data[0]["LoadBalancerId"] == raw_dns_name
