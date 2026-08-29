from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectTimeoutError

from cartography.intel.aws.ec2 import load_balancers


def _make_client_error(code: str, status_code: int, operation: str) -> ClientError:
    return ClientError(
        {
            "Error": {"Code": code, "Message": "temporary service issue"},
            "ResponseMetadata": {"HTTPStatusCode": status_code},
        },
        operation,
    )


def test_get_loadbalancer_data_raises_transient_region_failure_on_connect_timeout():
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    paginator = client.get_paginator.return_value
    paginator.paginate.side_effect = ConnectTimeoutError(
        endpoint_url="https://elasticloadbalancing.me-south-1.amazonaws.com/",
        error="timed out",
    )

    with pytest.raises(load_balancers.ELBTransientRegionFailure):
        load_balancers.get_loadbalancer_data(boto3_session, "me-south-1")


def test_sync_load_balancers_skips_cleanup_after_transient_region_failure(mocker):
    mocker.patch(
        "cartography.intel.aws.ec2.load_balancers._migrate_legacy_loadbalancer_labels"
    )
    mocker.patch(
        "cartography.intel.aws.ec2.load_balancers.get_loadbalancer_data",
        side_effect=load_balancers.ELBTransientRegionFailure("temporary failure"),
    )
    cleanup = mocker.patch(
        "cartography.intel.aws.ec2.load_balancers.cleanup_load_balancers"
    )

    load_balancers.sync_load_balancers(
        MagicMock(),
        MagicMock(),
        ["me-south-1"],
        "123456789012",
        1,
        {},
    )

    cleanup.assert_not_called()


def test_sync_load_balancers_skips_cleanup_after_retryable_client_error(mocker):
    mocker.patch(
        "cartography.intel.aws.ec2.load_balancers._migrate_legacy_loadbalancer_labels"
    )
    mocker.patch(
        "cartography.intel.aws.ec2.load_balancers.get_loadbalancer_data",
        side_effect=_make_client_error(
            "ServiceUnavailable",
            503,
            "DescribeLoadBalancers",
        ),
    )
    cleanup = mocker.patch(
        "cartography.intel.aws.ec2.load_balancers.cleanup_load_balancers"
    )

    load_balancers.sync_load_balancers(
        MagicMock(),
        MagicMock(),
        ["me-central-1"],
        "123456789012",
        1,
        {},
    )

    cleanup.assert_not_called()


def test_transform_load_balancer_data_lowercases_dnsname_but_not_id():
    raw_dns_name = "MyELB-1234567890.us-east-1.elb.amazonaws.com"
    data = [
        {
            "DNSName": raw_dns_name,
            "LoadBalancerName": "MyELB",
            "CreatedTime": "2024-01-01 00:00:00",
            "ListenerDescriptions": [
                {
                    "Listener": {
                        "LoadBalancerPort": 443,
                        "Protocol": "HTTPS",
                        "InstancePort": 8443,
                        "InstanceProtocol": "HTTPS",
                    },
                },
            ],
        },
    ]

    [transformed], [listener] = load_balancers.transform_load_balancer_data(data)

    # `id` is the join key for listeners, so it must stay byte-for-byte what AWS returned.
    assert transformed["id"] == raw_dns_name
    assert transformed["dnsname"] == raw_dns_name.lower()
    assert transformed["LISTENER_IDS"] == [listener["id"]]
    assert listener["id"].startswith(raw_dns_name)
