"""Integration tests for ELBv2 listener rule routing properties.

Verifies the rule-routing lists are persisted onto AWSELBV2Listener nodes and
stay index-aligned after a real sync through the schema, not just in the
transform's return value.

`check_nodes()` cannot return list-valued properties (it would raise
`TypeError: unhashable type: 'list'`), so these assertions read the node
directly, which tests/AGENTS.md permits for shapes check_nodes/check_rels
cannot express.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.aws.ec2.load_balancer_v2s import sync_load_balancer_v2s
from tests.integration.cartography.intel.aws.common import create_test_account

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789

TEST_LISTENER_ARN = (
    "arn:aws:elasticloadbalancing:us-east-1:000000000000:"
    "listener/app/test-alb/abc123/def456"
)
TG_BLUE = "arn:aws:elasticloadbalancing:us-east-1:000000000000:targetgroup/blue/111"
TG_GREEN = "arn:aws:elasticloadbalancing:us-east-1:000000000000:targetgroup/green/222"
TG_DEFAULT = (
    "arn:aws:elasticloadbalancing:us-east-1:000000000000:targetgroup/default/333"
)

LB_DATA = [
    {
        "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:"
        "loadbalancer/app/test-alb/abc123",
        "DNSName": "test-alb-1234567890.us-east-1.elb.amazonaws.com",
        "LoadBalancerName": "test-alb",
        "Type": "application",
        "Scheme": "internet-facing",
        "CreatedTime": "2024-01-01 00:00:00",
        "AvailabilityZones": [],
        "SecurityGroups": [],
        "Listeners": [
            {
                "ListenerArn": TEST_LISTENER_ARN,
                "Port": 443,
                "Protocol": "HTTPS",
                "Rules": [
                    {
                        "RuleArn": f"{TEST_LISTENER_ARN}/rule/default",
                        "Priority": "default",
                        "IsDefault": True,
                        "Conditions": [],
                        "Actions": [
                            {"Type": "forward", "TargetGroupArn": TG_DEFAULT},
                        ],
                    },
                    {
                        "RuleArn": f"{TEST_LISTENER_ARN}/rule/20",
                        "Priority": "20",
                        "IsDefault": False,
                        "Conditions": [
                            {
                                "Field": "path-pattern",
                                "PathPatternConfig": {"Values": ["/api/*"]},
                            },
                        ],
                        "Actions": [
                            {"Type": "forward", "TargetGroupArn": TG_BLUE},
                        ],
                    },
                    {
                        "RuleArn": f"{TEST_LISTENER_ARN}/rule/10",
                        "Priority": "10",
                        "IsDefault": False,
                        "Conditions": [
                            {
                                "Field": "path-pattern",
                                "PathPatternConfig": {"Values": ["/static/*"]},
                            },
                            {
                                "Field": "host-header",
                                "HostHeaderConfig": {"Values": ["CDN.Example.COM"]},
                            },
                        ],
                        "Actions": [
                            {"Type": "forward", "TargetGroupArn": TG_GREEN},
                        ],
                    },
                ],
            },
        ],
        "TargetGroups": [],
    },
]


def _sync(neo4j_session):
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    with patch(
        "cartography.intel.aws.ec2.load_balancer_v2s.get_loadbalancer_v2_data",
        return_value=LB_DATA,
    ):
        sync_load_balancer_v2s(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
        )


def _read_listener(neo4j_session):
    result = neo4j_session.run(
        """
        MATCH (l:AWSELBV2Listener {id: $arn})
        RETURN l.rule_path_patterns AS path_patterns,
               l.rule_path_regexes AS path_regexes,
               l.rule_host_regexes AS host_regexes,
               l.rule_target_group_arns AS tg_arns,
               l.rule_priorities AS priorities,
               l.rule_is_default AS is_default
        """,
        arn=TEST_LISTENER_ARN,
    ).single()
    assert result is not None, "listener node was not created"
    return result


def test_listener_rule_routing_is_persisted(neo4j_session):
    """The six routing lists reach the node, aligned and in priority order."""
    _sync(neo4j_session)
    node = _read_listener(neo4j_session)

    # Priority ascending, default last.
    assert node["priorities"] == ["10", "20", "default"]
    assert node["is_default"] == [False, False, True]
    assert node["path_patterns"] == ["/static/*", "/api/*", ""]
    assert node["tg_arns"] == [TG_GREEN, TG_BLUE, TG_DEFAULT]

    # All aligned lists are the same length - the invariant a Cypher consumer
    # relies on when joining by index.
    lengths = {
        len(node[key])
        for key in (
            "path_patterns",
            "path_regexes",
            "host_regexes",
            "tg_arns",
            "priorities",
            "is_default",
        )
    }
    assert lengths == {3}


def test_listener_rule_host_regex_is_lowercased(neo4j_session):
    """host-header values are lowercased so consumers can compare toLower(hostname)."""
    _sync(neo4j_session)
    node = _read_listener(neo4j_session)

    # Rule at index 0 is priority 10, which carries the host condition.
    import re

    host_regex = node["host_regexes"][0]
    assert re.match(host_regex, "cdn.example.com")
    assert not re.match(host_regex, "CDN.Example.COM")


def test_listener_without_rules_has_no_rule_properties(neo4j_session):
    """A listener with no rules has no `rule_*` keys at all on the node.

    Neo4j does not store a property whose value is None, and Cartography drops
    None values from the write, so the absence is observable via keys().
    """
    data = [
        {
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:"
            "loadbalancer/app/test-alb/abc123",
            "DNSName": "test-alb-1234567890.us-east-1.elb.amazonaws.com",
            "LoadBalancerName": "test-alb",
            "Type": "application",
            "Scheme": "internet-facing",
            "CreatedTime": "2024-01-01 00:00:00",
            "AvailabilityZones": [],
            "SecurityGroups": [],
            "Listeners": [
                {
                    "ListenerArn": TEST_LISTENER_ARN,
                    "Port": 443,
                    "Protocol": "HTTPS",
                    "Rules": [],
                },
            ],
            "TargetGroups": [],
        },
    ]
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    with patch(
        "cartography.intel.aws.ec2.load_balancer_v2s.get_loadbalancer_v2_data",
        return_value=data,
    ):
        sync_load_balancer_v2s(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
        )

    node = _read_listener(neo4j_session)
    assert node["path_patterns"] is None
    assert node["tg_arns"] is None

    # Absence is verifiable directly: no rule_* key exists on the node.
    keys = neo4j_session.run(
        """
        MATCH (l:AWSELBV2Listener {id: $arn})
        RETURN [k IN keys(l) WHERE k STARTS WITH 'rule_'] AS rule_keys
        """,
        arn=TEST_LISTENER_ARN,
    ).single()["rule_keys"]
    assert keys == []
