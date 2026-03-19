"""
Unit tests for CIS AWS Foundations Benchmark v5.0 rules.

These tests lock the implemented Cartography AWS CIS rules to the
actual v5 benchmark numbering and ensure non-CIS AWS best-practice
rules are not mislabeled as CIS.
"""

import pytest

from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.cis_aws_iam import cis_aws_1_11_unused_credentials
from cartography.rules.data.rules.cis_aws_iam import cis_aws_1_12_multiple_access_keys
from cartography.rules.data.rules.cis_aws_iam import cis_aws_1_13_access_key_not_rotated
from cartography.rules.data.rules.cis_aws_iam import cis_aws_1_14_user_direct_policies
from cartography.rules.data.rules.cis_aws_iam import cis_aws_1_18_expired_certificates
from cartography.rules.data.rules.cis_aws_logging import (
    aws_cloudtrail_cloudwatch_integration,
)
from cartography.rules.data.rules.cis_aws_logging import (
    cis_aws_3_1_cloudtrail_multi_region,
)
from cartography.rules.data.rules.cis_aws_logging import (
    cis_aws_3_2_cloudtrail_log_validation,
)
from cartography.rules.data.rules.cis_aws_logging import (
    cis_aws_3_5_cloudtrail_encryption,
)
from cartography.rules.data.rules.cis_aws_networking import (
    cis_aws_5_2_nacl_admin_ports_ipv4,
)
from cartography.rules.data.rules.cis_aws_networking import (
    cis_aws_5_3_security_group_admin_ports_ipv4,
)
from cartography.rules.data.rules.cis_aws_networking import (
    cis_aws_5_5_default_sg_traffic,
)
from cartography.rules.data.rules.cis_aws_networking import cis_aws_5_7_ec2_imdsv2
from cartography.rules.data.rules.cis_aws_storage import aws_ebs_volume_encryption
from cartography.rules.data.rules.cis_aws_storage import aws_s3_bucket_access_logging
from cartography.rules.data.rules.cis_aws_storage import aws_s3_bucket_versioning
from cartography.rules.data.rules.cis_aws_storage import aws_s3_default_encryption
from cartography.rules.data.rules.cis_aws_storage import cis_aws_2_1_2_s3_mfa_delete
from cartography.rules.data.rules.cis_aws_storage import (
    cis_aws_2_1_4_s3_block_public_access,
)
from cartography.rules.data.rules.cis_aws_storage import cis_aws_2_2_1_rds_encryption
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module

ALL_CIS_AWS_RULES = [
    cis_aws_1_11_unused_credentials,
    cis_aws_1_12_multiple_access_keys,
    cis_aws_1_13_access_key_not_rotated,
    cis_aws_1_14_user_direct_policies,
    cis_aws_1_18_expired_certificates,
    cis_aws_2_1_2_s3_mfa_delete,
    cis_aws_2_1_4_s3_block_public_access,
    cis_aws_2_2_1_rds_encryption,
    cis_aws_3_1_cloudtrail_multi_region,
    cis_aws_3_2_cloudtrail_log_validation,
    cis_aws_3_5_cloudtrail_encryption,
    cis_aws_5_2_nacl_admin_ports_ipv4,
    cis_aws_5_3_security_group_admin_ports_ipv4,
    cis_aws_5_5_default_sg_traffic,
    cis_aws_5_7_ec2_imdsv2,
]

AWS_BEST_PRACTICE_RULES = [
    aws_cloudtrail_cloudwatch_integration,
    aws_s3_bucket_versioning,
    aws_s3_bucket_access_logging,
    aws_s3_default_encryption,
    aws_ebs_volume_encryption,
]

EXPECTED_CIS_AWS_RULES = {
    "cis_aws_1_11_unused_credentials": "1.11",
    "cis_aws_1_12_multiple_access_keys": "1.12",
    "cis_aws_1_13_access_key_not_rotated": "1.13",
    "cis_aws_1_14_user_direct_policies": "1.14",
    "cis_aws_1_18_expired_certificates": "1.18",
    "cis_aws_2_1_2_s3_mfa_delete": "2.1.2",
    "cis_aws_2_1_4_s3_block_public_access": "2.1.4",
    "cis_aws_2_2_1_rds_encryption": "2.2.1",
    "cis_aws_3_1_cloudtrail_multi_region": "3.1",
    "cis_aws_3_2_cloudtrail_log_validation": "3.2",
    "cis_aws_3_5_cloudtrail_encryption": "3.5",
    "cis_aws_5_2_nacl_admin_ports_ipv4": "5.2",
    "cis_aws_5_3_security_group_admin_ports_ipv4": "5.3",
    "cis_aws_5_5_default_sg_traffic": "5.5",
    "cis_aws_5_7_ec2_imdsv2": "5.7",
}


class TestCisAwsFrameworkMetadata:
    @pytest.mark.parametrize("rule", ALL_CIS_AWS_RULES, ids=lambda r: r.id)
    def test_rule_has_cis_v5_framework(self, rule):
        assert len(rule.frameworks) == 1
        framework = rule.frameworks[0]
        assert framework.short_name == "cis"
        assert framework.scope == "aws"
        assert framework.revision == "5.0"

    @pytest.mark.parametrize("rule", ALL_CIS_AWS_RULES, ids=lambda r: r.id)
    def test_rule_matches_cis_aws_filter(self, rule):
        assert rule.has_framework(short_name="CIS", scope="aws", revision="5.0")

    @pytest.mark.parametrize("rule", ALL_CIS_AWS_RULES, ids=lambda r: r.id)
    def test_rule_id_matches_pdf_requirement(self, rule):
        assert rule.frameworks[0].requirement == EXPECTED_CIS_AWS_RULES[rule.id]


class TestCisAwsFactMetadata:
    @pytest.mark.parametrize("rule", ALL_CIS_AWS_RULES, ids=lambda r: r.id)
    def test_all_facts_use_aws_module(self, rule):
        for fact in rule.facts:
            assert fact.module == Module.AWS
            assert fact.maturity == Maturity.STABLE
            assert "MATCH" in fact.cypher_query
            assert "RETURN" in fact.cypher_query
            assert "COUNT" in fact.cypher_count_query


class TestCisAwsRuleRegistration:
    def test_only_expected_cis_aws_rules_are_registered(self):
        cis_aws_rule_ids = {
            rule_id for rule_id in RULES if rule_id.startswith("cis_aws_")
        }
        assert cis_aws_rule_ids == set(EXPECTED_CIS_AWS_RULES)

    def test_cis_rule_count(self):
        cis_aws_rule_ids = [
            rule_id for rule_id in RULES if rule_id.startswith("cis_aws_")
        ]
        assert len(cis_aws_rule_ids) == 15

    def test_all_expected_rules_registered(self):
        for rule in ALL_CIS_AWS_RULES:
            assert rule.id in RULES
            assert RULES[rule.id] is rule


class TestAwsBestPracticeRuleClassification:
    @pytest.mark.parametrize("rule", AWS_BEST_PRACTICE_RULES, ids=lambda r: r.id)
    def test_best_practice_rules_are_registered(self, rule):
        assert rule.id in RULES
        assert RULES[rule.id] is rule

    @pytest.mark.parametrize("rule", AWS_BEST_PRACTICE_RULES, ids=lambda r: r.id)
    def test_best_practice_rules_are_not_labeled_cis(self, rule):
        assert not rule.has_framework(short_name="CIS", scope="aws", revision="5.0")
        assert rule.frameworks == ()
