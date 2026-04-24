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
