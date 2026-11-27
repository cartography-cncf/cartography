"""Unit tests for ELBv2 listener rule routing (describe_rules transform).

The routing lists are index-aligned so a query can resolve the serving target
group for a request host+path without APOC. These tests pin the alignment, the
priority ordering (default last), and the condition-to-regex translation.
"""

import re
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ConnectTimeoutError

from cartography.intel.aws.ec2 import load_balancer_v2s

LISTENER_ARN = (
    "arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/my-alb/abc/def"
)
TG_BLUE = "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/blue/111"
TG_GREEN = "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/green/222"
TG_DEFAULT = (
    "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/default/333"
)


def _forward_action(tg_arn):
    return [{"Type": "forward", "TargetGroupArn": tg_arn}]


def _rule(priority, path=None, host=None, tg=TG_BLUE, is_default=False):
    """Build a describe_rules rule with the modern config shape."""
    conditions = []
    if path is not None:
        conditions.append(
            {
                "Field": "path-pattern",
                "PathPatternConfig": {"Values": path},
            }
        )
    if host is not None:
        conditions.append(
            {
                "Field": "host-header",
                "HostHeaderConfig": {"Values": host},
            }
        )
    rule = {
        "RuleArn": f"{LISTENER_ARN}/rule/{priority}",
        "Priority": "default" if is_default else str(priority),
        "Conditions": conditions,
        "Actions": _forward_action(tg),
        "IsDefault": is_default,
    }
    return rule


class TestWildcardToRegexBody:
    def test_star_matches_anything_including_slash(self):
        body = load_balancer_v2s._wildcard_to_regex_body("/api/*")
        assert re.match(f"^{body}$", "/api/orders/123")
        assert re.match(f"^{body}$", "/api/")

    def test_star_does_not_match_a_different_prefix(self):
        body = load_balancer_v2s._wildcard_to_regex_body("/api/*")
        assert not re.match(f"^{body}$", "/other/orders")

    def test_question_mark_matches_exactly_one_character(self):
        body = load_balancer_v2s._wildcard_to_regex_body("/v?/health")
        assert re.match(f"^{body}$", "/v1/health")
        assert not re.match(f"^{body}$", "/v12/health")

    def test_regex_metacharacters_are_escaped(self):
        # A dot in the pattern must be a literal dot, not "any character".
        body = load_balancer_v2s._wildcard_to_regex_body("/a.b")
        assert re.match(f"^{body}$", "/a.b")
        assert not re.match(f"^{body}$", "/axb")


class TestConditionValuesToRegex:
    def test_empty_values_means_match_anything(self):
        assert load_balancer_v2s._condition_values_to_regex([]) == ""

    def test_multiple_values_become_an_alternation(self):
        rx = load_balancer_v2s._condition_values_to_regex(["/api/*", "/v2/*"])
        assert re.match(rx, "/api/orders")
        assert re.match(rx, "/v2/orders")
        assert not re.match(rx, "/v3/orders")

    def test_unknown_path_is_rejected(self):
        rx = load_balancer_v2s._condition_values_to_regex(["/api/*", "/v2/*"])
        assert not re.match(rx, "/v3/orders")

    def test_lowercase_flag_lowercases_the_pattern(self):
        """The pattern is lowercased; consumers compare against a lowercased hostname.

        This is the documented contract on `rule_host_regexes` ("Compare against
        toLower(hostname)"), not a case-insensitive regex.
        """
        rx = load_balancer_v2s._condition_values_to_regex(
            ["Example.COM"], lowercase=True
        )
        # Matches once the hostname is lowercased, as the contract requires.
        assert re.match(rx, "example.com")
        # The stored pattern itself is lowercase, so an un-lowercased uppercase
        # hostname does not match - callers must apply toLower() first.
        assert not re.match(rx, "EXAMPLE.COM")

    def test_without_lowercase_flag_pattern_stays_case_sensitive(self):
        rx = load_balancer_v2s._condition_values_to_regex(["Example.COM"])
        assert re.match(rx, "Example.COM")
        assert not re.match(rx, "example.com")


class TestRuleConditionValues:
    def test_reads_modern_config_shape(self):
        rule = _rule(1, path=["/api/*"])
        assert load_balancer_v2s._rule_condition_values(
            rule, "path-pattern", "PathPatternConfig"
        ) == ["/api/*"]

    def test_reads_legacy_shape_where_values_sit_on_the_condition(self):
        rule = {
            "Conditions": [{"Field": "path-pattern", "Values": ["/legacy/*"]}],
        }
        assert load_balancer_v2s._rule_condition_values(
            rule, "path-pattern", "PathPatternConfig"
        ) == ["/legacy/*"]

    def test_ignores_other_condition_fields(self):
        rule = _rule(1, path=["/api/*"], host=["example.com"])
        assert load_balancer_v2s._rule_condition_values(
            rule, "path-pattern", "PathPatternConfig"
        ) == ["/api/*"]

    def test_returns_empty_for_a_rule_with_no_conditions(self):
        assert (
            load_balancer_v2s._rule_condition_values(
                {"Conditions": []}, "path-pattern", "PathPatternConfig"
            )
            == []
        )


class TestRuleForwardTargetGroupArn:
    def test_reads_direct_target_group_arn(self):
        assert load_balancer_v2s._rule_forward_target_group_arn(_rule(1)) == TG_BLUE

    def test_reads_first_weighted_target(self):
        rule = {
            "Actions": [
                {
                    "Type": "forward",
                    "ForwardConfig": {
                        "TargetGroups": [
                            {"TargetGroupArn": TG_GREEN, "Weight": 90},
                            {"TargetGroupArn": TG_BLUE, "Weight": 10},
                        ]
                    },
                }
            ]
        }
        assert load_balancer_v2s._rule_forward_target_group_arn(rule) == TG_GREEN

    def test_ignores_non_forward_actions(self):
        rule = {
            "Actions": [
                {"Type": "redirect", "RedirectConfig": {"Host": "example.com"}},
                {"Type": "forward", "TargetGroupArn": TG_DEFAULT},
            ]
        }
        assert load_balancer_v2s._rule_forward_target_group_arn(rule) == TG_DEFAULT

    def test_returns_empty_when_no_forward_action(self):
        rule = {"Actions": [{"Type": "fixed-response"}]}
        assert load_balancer_v2s._rule_forward_target_group_arn(rule) == ""


class TestTransformListenerRules:
    def test_lists_are_index_aligned_and_default_is_last(self):
        listener = {
            "ListenerArn": LISTENER_ARN,
            "Rules": [
                _rule(999, is_default=True, tg=TG_DEFAULT),
                _rule(20, path=["/api/*"], tg=TG_BLUE),
                _rule(10, path=["/static/*"], host=["cdn.example.com"], tg=TG_GREEN),
            ],
        }

        out = load_balancer_v2s._transform_listener_rules(listener)

        # Priority ascending (10, 20), default last.
        assert out["rule_priorities"] == ["10", "20", "default"]
        assert out["rule_is_default"] == [False, False, True]
        assert out["rule_path_patterns"] == ["/static/*", "/api/*", ""]
        assert out["rule_target_group_arns"] == [TG_GREEN, TG_BLUE, TG_DEFAULT]
        # Every aligned list has the same length.
        for key in (
            "rule_path_patterns",
            "rule_path_regexes",
            "rule_host_regexes",
            "rule_target_group_arns",
            "rule_priorities",
            "rule_is_default",
        ):
            assert len(out[key]) == 3, key

    def test_alignment_resolves_the_serving_target_group_for_host_and_path(self):
        """The point of the whole change: pick the target group for a request."""
        listener = {
            "ListenerArn": LISTENER_ARN,
            "Rules": [
                _rule(999, is_default=True, tg=TG_DEFAULT),
                _rule(10, path=["/api/*"], host=["api.example.com"], tg=TG_BLUE),
                _rule(20, path=["/api/v2/*"], tg=TG_GREEN),
            ],
        }

        out = load_balancer_v2s._transform_listener_rules(listener)

        def serving_tg(host, path):
            """Mirror how a Cypher consumer would walk the aligned lists."""
            for i, path_rx in enumerate(out["rule_path_regexes"]):
                host_rx = out["rule_host_regexes"][i]
                if path_rx and not re.match(path_rx, path):
                    continue
                if host_rx and not re.match(host_rx, host.lower()):
                    continue
                return out["rule_target_group_arns"][i]
            return None

        # Priority 10 is more specific than 20, so it wins for its host+path.
        assert serving_tg("api.example.com", "/api/orders") == TG_BLUE
        # Rule 10 requires api.example.com, so another host falls to rule 20.
        assert serving_tg("other.example.com", "/api/v2/orders") == TG_GREEN
        # Nothing matches a path outside both patterns -> default rule.
        assert serving_tg("other.example.com", "/unrelated") == TG_DEFAULT

    def test_rule_with_only_a_default_behavior_yields_aligned_single_entries(self):
        listener = {
            "ListenerArn": LISTENER_ARN,
            "Rules": [_rule(999, is_default=True, tg=TG_DEFAULT)],
        }
        out = load_balancer_v2s._transform_listener_rules(listener)
        assert out["rule_priorities"] == ["default"]
        assert out["rule_is_default"] == [True]
        assert out["rule_path_patterns"] == [""]
        assert out["rule_path_regexes"] == [""]
        assert out["rule_host_regexes"] == [""]
        assert out["rule_target_group_arns"] == [TG_DEFAULT]

    def test_no_rules_yields_none_not_empty_lists(self):
        """A listener with no rules yields no rule properties on the node.

        The transform returns None, which Cartography drops from the write, so the
        node simply has no `rule_*` keys. Asserted at the transform level here and
        end-to-end in the integration test, where the absence is observable via
        `keys()` / `IS NULL`.
        """
        out = load_balancer_v2s._transform_listener_rules(
            {"ListenerArn": LISTENER_ARN, "Rules": []}
        )
        assert out["rule_path_patterns"] is None
        assert out["rule_path_regexes"] is None
        assert out["rule_host_regexes"] is None
        assert out["rule_target_group_arns"] is None
        assert out["rule_priorities"] is None
        assert out["rule_is_default"] is None

    def test_host_regex_is_lowercased_for_comparison_with_lowercased_hostname(self):
        listener = {
            "ListenerArn": LISTENER_ARN,
            "Rules": [_rule(1, host=["API.Example.COM"])],
        }
        out = load_balancer_v2s._transform_listener_rules(listener)
        # The description tells consumers to compare against toLower(hostname).
        assert re.match(out["rule_host_regexes"][0], "api.example.com")

    def test_unparseable_priority_sorts_before_default_without_raising(self):
        listener = {
            "ListenerArn": LISTENER_ARN,
            "Rules": [
                _rule(999, is_default=True, tg=TG_DEFAULT),
                {"Priority": "not-a-number", "Conditions": [], "Actions": []},
            ],
        }
        out = load_balancer_v2s._transform_listener_rules(listener)
        # No exception, and the malformed rule still occupies an aligned slot.
        assert len(out["rule_priorities"]) == 2
        assert out["rule_priorities"][-1] == "default"


class TestTransformListenerIncludesRules:
    def test_transform_listener_merges_rule_lists_onto_the_listener(self):
        listener = {
            "ListenerArn": LISTENER_ARN,
            "Port": 443,
            "Protocol": "HTTPS",
            "Rules": [_rule(10, path=["/api/*"], tg=TG_BLUE)],
        }

        out = load_balancer_v2s._transform_listener(listener, "my-alb.example.com")

        # Existing listener fields survive.
        assert out["ListenerArn"] == LISTENER_ARN
        assert out["Port"] == 443
        assert out["Protocol"] == "HTTPS"
        # Routing lists are merged in.
        assert out["rule_path_patterns"] == ["/api/*"]
        assert out["rule_target_group_arns"] == [TG_BLUE]


class TestGetListenerRules:
    def test_paginates_all_rule_pages(self, mocker):
        client = MagicMock()
        paginator = client.get_paginator.return_value
        paginator.paginate.return_value = [
            {"Rules": [_rule(1)]},
            {"Rules": [_rule(2)]},
        ]

        rules = load_balancer_v2s.get_load_balancer_v2_listener_rules(
            client, LISTENER_ARN
        )

        assert len(rules) == 2
        paginator.paginate.assert_called_once_with(ListenerArn=LISTENER_ARN)

    def test_transient_timeout_is_wrapped_as_region_failure(self):
        client = MagicMock()
        paginator = client.get_paginator.return_value
        paginator.paginate.side_effect = ConnectTimeoutError(
            endpoint_url="https://elasticloadbalancing.us-east-1.amazonaws.com/",
            error="timed out",
        )

        with pytest.raises(load_balancer_v2s.ELBV2TransientRegionFailure):
            load_balancer_v2s.get_load_balancer_v2_listener_rules(client, LISTENER_ARN)
