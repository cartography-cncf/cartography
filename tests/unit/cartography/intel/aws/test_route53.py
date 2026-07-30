import pytest

from cartography.intel.aws.route53 import _normalize_dns_target
from cartography.intel.aws.route53 import transform_record_set

LB_DNS_NAME = "myawesomeloadbalancer.us-east-1.elb.amazonaws.com"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # Route53 puts a `dualstack.` prefix on ELB alias targets; the ELB APIs do not.
        (f"dualstack.{LB_DNS_NAME}.", LB_DNS_NAME),
        (f"dualstack.{LB_DNS_NAME}", LB_DNS_NAME),
        (f"{LB_DNS_NAME}.", LB_DNS_NAME),
        # Route53 usually sends a trailing dot, but not always.
        (LB_DNS_NAME, LB_DNS_NAME),
        # `dualstack` is only a prefix, never stripped from the middle of a name.
        ("host.dualstack.example.com.", "host.dualstack.example.com"),
    ],
)
def test_normalize_dns_target(value, expected):
    assert _normalize_dns_target(value) == expected


@pytest.mark.parametrize(
    "record_type",
    ["A", "AAAA", "CNAME"],
)
def test_transform_record_set_strips_dualstack_from_alias_targets(record_type):
    record_set = {
        "Name": "app.example.com.",
        "Type": record_type,
        "AliasTarget": {
            "HostedZoneId": "HOSTED_ZONE_2",
            "DNSName": f"dualstack.{LB_DNS_NAME}.",
            "EvaluateTargetHealth": False,
        },
    }

    transformed = transform_record_set(
        record_set, "/hostedzone/ZONE", "app.example.com"
    )

    assert transformed is not None
    assert transformed["value"] == LB_DNS_NAME


def test_transform_record_set_leaves_ip_values_alone():
    record_set = {
        "Name": "app.example.com.",
        "Type": "A",
        "ResourceRecords": [{"Value": "1.2.3.4"}, {"Value": "5.6.7.8"}],
        "TTL": 300,
    }

    transformed = transform_record_set(
        record_set, "/hostedzone/ZONE", "app.example.com"
    )

    assert transformed is not None
    assert transformed["value"] == "1.2.3.4,5.6.7.8"
    assert transformed["ip_addresses"] == ["1.2.3.4", "5.6.7.8"]
