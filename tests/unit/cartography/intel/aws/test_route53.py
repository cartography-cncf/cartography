import pytest

from cartography.intel.aws.route53 import _normalize_alias_target
from cartography.intel.aws.route53 import _normalize_dns_target
from cartography.intel.aws.route53 import transform_record_set

LB_DNS_NAME = "myawesomeloadbalancer.us-east-1.elb.amazonaws.com"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (f"{LB_DNS_NAME}.", LB_DNS_NAME),
        # Route53 usually sends a trailing dot, but not always.
        (LB_DNS_NAME, LB_DNS_NAME),
        ("MyHost.Example.COM.", "myhost.example.com"),
        # A `dualstack.` prefix is only an alias-target artifact. On an ordinary CNAME the
        # value is zone data written by the operator, where it belongs to a genuinely
        # different hostname, so it must survive.
        ("dualstack.internal.example.com.", "dualstack.internal.example.com"),
    ],
)
def test_normalize_dns_target(value, expected):
    assert _normalize_dns_target(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # Route53 puts a `dualstack.` prefix on ELB alias targets; the ELB APIs do not.
        (f"dualstack.{LB_DNS_NAME}.", LB_DNS_NAME),
        (f"dualstack.{LB_DNS_NAME}", LB_DNS_NAME),
        (f"{LB_DNS_NAME}.", LB_DNS_NAME),
        # aws-cn and GovCloud ELBs carry the same prefix.
        (
            "dualstack.my-lb-1.cn-north-1.elb.amazonaws.com.cn.",
            "my-lb-1.cn-north-1.elb.amazonaws.com.cn",
        ),
        (
            "dualstack.my-lb-1.us-gov-west-1.elb.amazonaws.com.",
            "my-lb-1.us-gov-west-1.elb.amazonaws.com",
        ),
        # An alias may target another record in the same hosted zone rather than an ELB. There
        # a leading `dualstack.` is part of a genuinely different hostname, so it must survive.
        ("dualstack.internal.example.com.", "dualstack.internal.example.com"),
        # `.elb.` can appear anywhere in a customer zone, so only the AWS-owned suffix is
        # conclusive. This name is not an ELB and must be left alone.
        (
            "dualstack.app.elb.internal.example.com.",
            "dualstack.app.elb.internal.example.com",
        ),
        # Non-ELB alias targets never carry the prefix and must not be rewritten either.
        ("d111111abcdef8.cloudfront.net.", "d111111abcdef8.cloudfront.net"),
        # `dualstack` is only a prefix, never stripped from the middle of a name.
        (f"host.dualstack.{LB_DNS_NAME}.", f"host.dualstack.{LB_DNS_NAME}"),
    ],
)
def test_normalize_alias_target(value, expected):
    assert _normalize_alias_target(value) == expected


def test_transform_record_set_keeps_dualstack_on_ordinary_cname():
    record_set = {
        "Name": "app.example.com.",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "dualstack.internal.example.com."}],
    }

    transformed = transform_record_set(
        record_set, "/hostedzone/ZONE", "app.example.com"
    )

    assert transformed is not None
    assert transformed["value"] == "dualstack.internal.example.com"


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
