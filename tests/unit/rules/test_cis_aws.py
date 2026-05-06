"""
Unit tests for CIS AWS Foundations Benchmark rules.

These tests verify that AWS CIS rule metadata stays aligned with the
current AWS CIS v6.0.0 requirement numbering used by Cartography.
"""

import pytest

from cartography.rules.data.rules.cis_aws_iam import cis_aws_2_11_unused_credentials
from cartography.rules.data.rules.cis_aws_iam import cis_aws_2_12_multiple_access_keys
from cartography.rules.data.rules.cis_aws_iam import cis_aws_2_13_access_key_not_rotated
from cartography.rules.data.rules.cis_aws_iam import cis_aws_2_14_user_direct_policies
from cartography.rules.data.rules.cis_aws_iam import cis_aws_2_18_expired_certificates
from cartography.rules.data.rules.cis_aws_logging import (
    cis_aws_4_1_cloudtrail_multi_region,
)
from cartography.rules.data.rules.cis_aws_logging import (
    cis_aws_4_2_cloudtrail_log_validation,
)
from cartography.rules.data.rules.cis_aws_logging import (
    cis_aws_4_4_cloudtrail_bucket_access_logging,
)
from cartography.rules.data.rules.cis_aws_logging import (
    cis_aws_4_5_cloudtrail_encryption,
)
from cartography.rules.data.rules.cis_aws_networking import cis_aws_6_1_1_ebs_encryption
from cartography.rules.data.rules.cis_aws_networking import (
    cis_aws_6_3_remote_admin_ipv4,
)
from cartography.rules.data.rules.cis_aws_networking import (
    cis_aws_6_4_remote_admin_ipv6,
)
from cartography.rules.data.rules.cis_aws_networking import (
    cis_aws_6_5_default_sg_traffic,
)
from cartography.rules.data.rules.cis_aws_networking import cis_aws_6_7_ec2_imdsv2
from cartography.rules.data.rules.cis_aws_storage import cis_aws_3_1_2_s3_mfa_delete
from cartography.rules.data.rules.cis_aws_storage import (
    cis_aws_3_1_4_s3_block_public_access,
)
from cartography.rules.data.rules.cis_aws_storage import cis_aws_3_2_1_rds_encryption
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module

ALL_CIS_AWS_RULES = [
    cis_aws_2_11_unused_credentials,
    cis_aws_2_12_multiple_access_keys,
    cis_aws_2_13_access_key_not_rotated,
    cis_aws_2_14_user_direct_policies,
    cis_aws_2_18_expired_certificates,
    cis_aws_3_1_2_s3_mfa_delete,
    cis_aws_3_1_4_s3_block_public_access,
    cis_aws_3_2_1_rds_encryption,
    cis_aws_4_1_cloudtrail_multi_region,
    cis_aws_4_2_cloudtrail_log_validation,
    cis_aws_4_4_cloudtrail_bucket_access_logging,
    cis_aws_4_5_cloudtrail_encryption,
    cis_aws_6_1_1_ebs_encryption,
    cis_aws_6_3_remote_admin_ipv4,
    cis_aws_6_4_remote_admin_ipv6,
    cis_aws_6_5_default_sg_traffic,
    cis_aws_6_7_ec2_imdsv2,
]


class TestCisAwsRuleStructure:
    """Test that all CIS AWS rules have expected structure."""

    @pytest.mark.parametrize("rule", ALL_CIS_AWS_RULES, ids=lambda r: r.id)
    def test_rule_has_unique_id(self, rule):
        assert rule.id
        assert rule.id.startswith("cis_aws_")

    @pytest.mark.parametrize("rule", ALL_CIS_AWS_RULES, ids=lambda r: r.id)
    def test_rule_has_name_and_description(self, rule):
        assert rule.name
        assert rule.description

    @pytest.mark.parametrize("rule", ALL_CIS_AWS_RULES, ids=lambda r: r.id)
    def test_rule_has_at_least_one_fact(self, rule):
        assert len(rule.facts) >= 1

    @pytest.mark.parametrize("rule", ALL_CIS_AWS_RULES, ids=lambda r: r.id)
    def test_rule_has_output_model_and_references(self, rule):
        assert rule.output_model is not None
        assert len(rule.references) >= 1


class TestCisAwsFrameworkMetadata:
    """Test that all CIS AWS rules target the expected AWS benchmark revision."""

    @pytest.mark.parametrize("rule", ALL_CIS_AWS_RULES, ids=lambda r: r.id)
    def test_rule_has_cis_aws_v6_framework(self, rule):
        assert len(rule.frameworks) == 1
        fw = rule.frameworks[0]
        assert fw.short_name == "cis"
        assert fw.scope == "aws"
        assert fw.revision == "6.0.0"

    @pytest.mark.parametrize("rule", ALL_CIS_AWS_RULES, ids=lambda r: r.id)
    def test_rule_matches_cis_aws_filter(self, rule):
        assert rule.has_framework(short_name="CIS", scope="aws")
        assert rule.has_framework(short_name="CIS", scope="aws", revision="6.0.0")


class TestCisAwsFactMetadata:
    """Test that all AWS facts have the expected metadata."""

    @pytest.mark.parametrize("rule", ALL_CIS_AWS_RULES, ids=lambda r: r.id)
    def test_all_facts_use_aws_module(self, rule):
        for fact in rule.facts:
            assert fact.module == Module.AWS

    @pytest.mark.parametrize("rule", ALL_CIS_AWS_RULES, ids=lambda r: r.id)
    def test_all_facts_are_stable(self, rule):
        for fact in rule.facts:
            assert fact.maturity == Maturity.STABLE

    @pytest.mark.parametrize("rule", ALL_CIS_AWS_RULES, ids=lambda r: r.id)
    def test_all_facts_have_queries(self, rule):
        for fact in rule.facts:
            assert fact.cypher_query.strip()
            assert fact.cypher_visual_query.strip()
            assert "COUNT" in fact.cypher_count_query
            assert "AS count" in fact.cypher_count_query


class TestCisAwsRuleRegistration:
    """Test that all CIS AWS rules are registered."""

    def test_all_rules_registered(self):
        from cartography.rules.data.rules import RULES

        for rule in ALL_CIS_AWS_RULES:
            assert rule.id in RULES, f"Rule {rule.id} not found in RULES registry"
            assert RULES[rule.id] is rule

    def test_rule_count(self):
        from cartography.rules.data.rules import RULES

        aws_rules = {k: v for k, v in RULES.items() if k.startswith("cis_aws_")}
        assert len(aws_rules) == len(ALL_CIS_AWS_RULES)


class TestCisAwsRuleIds:
    """Test that AWS CIS rule ids and framework requirements stay aligned."""

    EXPECTED_RULES = {
        "cis_aws_2_11_unused_credentials": "2.11",
        "cis_aws_2_12_multiple_access_keys": "2.12",
        "cis_aws_2_13_access_key_not_rotated": "2.13",
        "cis_aws_2_14_user_direct_policies": "2.14",
        "cis_aws_2_18_expired_certificates": "2.18",
        "cis_aws_3_1_2_s3_mfa_delete": "3.1.2",
        "cis_aws_3_1_4_s3_block_public_access": "3.1.4",
        "cis_aws_3_2_1_rds_encryption": "3.2.1",
        "cis_aws_4_1_cloudtrail_multi_region": "4.1",
        "cis_aws_4_2_cloudtrail_log_validation": "4.2",
        "cis_aws_4_4_cloudtrail_bucket_access_logging": "4.4",
        "cis_aws_4_5_cloudtrail_encryption": "4.5",
        "cis_aws_6_1_1_ebs_encryption": "6.1.1",
        "cis_aws_6_3_remote_admin_ipv4": "6.3",
        "cis_aws_6_4_remote_admin_ipv6": "6.4",
        "cis_aws_6_5_default_sg_traffic": "6.5",
        "cis_aws_6_7_ec2_imdsv2": "6.7",
    }

    def test_all_expected_rules_exist(self):
        rule_ids = {r.id for r in ALL_CIS_AWS_RULES}
        for expected_id in self.EXPECTED_RULES:
            assert expected_id in rule_ids, f"Expected rule {expected_id} not found"

    @pytest.mark.parametrize("rule", ALL_CIS_AWS_RULES, ids=lambda r: r.id)
    def test_rule_id_matches_framework_requirement(self, rule):
        expected_requirement = self.EXPECTED_RULES.get(rule.id)
        assert expected_requirement is not None, f"Unknown rule {rule.id}"
        fw = rule.frameworks[0]
        assert fw.requirement == expected_requirement
