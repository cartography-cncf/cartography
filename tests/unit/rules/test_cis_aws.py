"""
Unit tests for CIS AWS Foundations Benchmark rules.

These tests verify that AWS CIS rule metadata stays aligned with the
current AWS CIS v6.0.0 requirement numbering used by Cartography.
"""

import pytest

from cartography.rules.data.rules.cis_aws_iam import aws_access_keys_not_rotated
from cartography.rules.data.rules.cis_aws_iam import aws_expired_ssl_tls_certificates
from cartography.rules.data.rules.cis_aws_iam import (
    aws_policies_with_full_administrative_privileges,
)
from cartography.rules.data.rules.cis_aws_iam import aws_root_user_access_keys
from cartography.rules.data.rules.cis_aws_iam import aws_root_user_mfa_disabled
from cartography.rules.data.rules.cis_aws_iam import aws_unused_credentials
from cartography.rules.data.rules.cis_aws_iam import (
    aws_users_with_direct_policy_attachments,
)
from cartography.rules.data.rules.cis_aws_iam import (
    aws_users_with_multiple_active_access_keys,
)
from cartography.rules.data.rules.cis_aws_logging import aws_cloudtrail_kms_encryption
from cartography.rules.data.rules.cis_aws_logging import (
    aws_cloudtrail_log_file_validation,
)
from cartography.rules.data.rules.cis_aws_logging import aws_cloudtrail_multi_region
from cartography.rules.data.rules.cis_aws_logging import (
    aws_cloudtrail_s3_bucket_access_logging,
)
from cartography.rules.data.rules.cis_aws_networking import (
    aws_cifs_access_restricted_to_trusted_networks,
)
from cartography.rules.data.rules.cis_aws_networking import (
    aws_default_security_group_restricts_traffic,
)
from cartography.rules.data.rules.cis_aws_networking import aws_ebs_volume_encryption
from cartography.rules.data.rules.cis_aws_networking import aws_ec2_instances_use_imdsv2
from cartography.rules.data.rules.cis_aws_networking import (
    aws_ipv4_remote_administration_ports_open_to_internet,
)
from cartography.rules.data.rules.cis_aws_networking import (
    aws_ipv6_remote_administration_ports_open_to_internet,
)
from cartography.rules.data.rules.cis_aws_storage import aws_rds_encryption_at_rest
from cartography.rules.data.rules.cis_aws_storage import aws_s3_block_public_access
from cartography.rules.data.rules.cis_aws_storage import aws_s3_bucket_mfa_delete
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module

ALL_CIS_AWS_RULES = [
    aws_root_user_access_keys,
    aws_root_user_mfa_disabled,
    aws_unused_credentials,
    aws_users_with_multiple_active_access_keys,
    aws_access_keys_not_rotated,
    aws_users_with_direct_policy_attachments,
    aws_policies_with_full_administrative_privileges,
    aws_expired_ssl_tls_certificates,
    aws_s3_bucket_mfa_delete,
    aws_s3_block_public_access,
    aws_rds_encryption_at_rest,
    aws_cloudtrail_multi_region,
    aws_cloudtrail_log_file_validation,
    aws_cloudtrail_s3_bucket_access_logging,
    aws_cloudtrail_kms_encryption,
    aws_ebs_volume_encryption,
    aws_cifs_access_restricted_to_trusted_networks,
    aws_ipv4_remote_administration_ports_open_to_internet,
    aws_ipv6_remote_administration_ports_open_to_internet,
    aws_default_security_group_restricts_traffic,
    aws_ec2_instances_use_imdsv2,
]


class TestCisAwsRuleStructure:
    """Test that all CIS AWS rules have expected structure."""

    @pytest.mark.parametrize("rule", ALL_CIS_AWS_RULES, ids=lambda r: r.id)
    def test_rule_has_unique_id(self, rule):
        assert rule.id
        assert rule.id.startswith("aws_")

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
        fw = next(
            fw for fw in rule.frameworks if fw.short_name == "cis" and fw.scope == "aws"
        )
        assert fw.short_name == "cis"
        assert fw.scope == "aws"
        assert fw.revision == "6.0.0"

    @pytest.mark.parametrize("rule", ALL_CIS_AWS_RULES, ids=lambda r: r.id)
    def test_rule_matches_cis_aws_filter(self, rule):
        assert rule.has_framework(short_name="CIS", scope="aws")
        assert rule.has_framework(short_name="CIS", scope="aws", revision="6.0.0")

    @pytest.mark.parametrize("rule", ALL_CIS_AWS_RULES, ids=lambda r: r.id)
    def test_rule_has_iso27001_framework(self, rule):
        assert rule.has_framework(short_name="ISO27001", revision="2022")


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

    def test_access_key_date_filters_parse_iso_datetime_strings(self):
        access_key_rules = (
            aws_unused_credentials,
            aws_access_keys_not_rotated,
        )

        for rule in access_key_rules:
            fact = rule.facts[0]
            query_text = f"{fact.cypher_query}\n{fact.cypher_visual_query}"
            assert "date(key.createdate_dt)" not in query_text
            assert "date(key.lastuseddate_dt)" not in query_text
            assert "date(datetime(key.createdate_dt))" in query_text

        unused_credentials_fact = aws_unused_credentials.facts[0]
        unused_credentials_query_text = (
            f"{unused_credentials_fact.cypher_query}\n"
            f"{unused_credentials_fact.cypher_visual_query}"
        )
        assert "date(datetime(key.lastuseddate_dt))" in unused_credentials_query_text


class TestCisAwsRuleRegistration:
    """Test that all CIS AWS rules are registered."""

    def test_all_rules_registered(self):
        from cartography.rules.data.rules import RULES

        for rule in ALL_CIS_AWS_RULES:
            assert rule.id in RULES, f"Rule {rule.id} not found in RULES registry"
            assert RULES[rule.id] is rule

    def test_rule_count(self):
        from cartography.rules.data.rules import RULES

        aws_rules = {
            k: v
            for k, v in RULES.items()
            if v.has_framework(short_name="cis", scope="aws", revision="6.0.0")
        }
        assert len(aws_rules) == len(ALL_CIS_AWS_RULES)


class TestCisAwsRuleIds:
    """Test that AWS CIS rule ids and framework requirements stay aligned."""

    EXPECTED_RULES = {
        "aws_root_user_access_keys": "2.3",
        "aws_root_user_mfa_disabled": "2.4",
        "aws_unused_credentials": "2.11",
        "aws_users_with_multiple_active_access_keys": "2.12",
        "aws_access_keys_not_rotated": "2.13",
        "aws_users_with_direct_policy_attachments": "2.14",
        "aws_policies_with_full_administrative_privileges": "2.15",
        "aws_expired_ssl_tls_certificates": "2.18",
        "aws_s3_bucket_mfa_delete": "3.1.2",
        "aws_s3_block_public_access": "3.1.4",
        "aws_rds_encryption_at_rest": "3.2.1",
        "aws_cloudtrail_multi_region": "4.1",
        "aws_cloudtrail_log_file_validation": "4.2",
        "aws_cloudtrail_s3_bucket_access_logging": "4.4",
        "aws_cloudtrail_kms_encryption": "4.5",
        "aws_ebs_volume_encryption": "6.1.1",
        "aws_cifs_access_restricted_to_trusted_networks": "6.1.2",
        "aws_ipv4_remote_administration_ports_open_to_internet": "6.3",
        "aws_ipv6_remote_administration_ports_open_to_internet": "6.4",
        "aws_default_security_group_restricts_traffic": "6.5",
        "aws_ec2_instances_use_imdsv2": "6.7",
    }

    def test_all_expected_rules_exist(self):
        rule_ids = {r.id for r in ALL_CIS_AWS_RULES}
        for expected_id in self.EXPECTED_RULES:
            assert expected_id in rule_ids, f"Expected rule {expected_id} not found"

    @pytest.mark.parametrize("rule", ALL_CIS_AWS_RULES, ids=lambda r: r.id)
    def test_rule_id_matches_framework_requirement(self, rule):
        expected_requirement = self.EXPECTED_RULES.get(rule.id)
        assert expected_requirement is not None, f"Unknown rule {rule.id}"
        fw = next(
            fw for fw in rule.frameworks if fw.short_name == "cis" and fw.scope == "aws"
        )
        assert fw.requirement == expected_requirement


class TestIso27001AwsMappings:
    """Test that batch 1 AWS rules have expected ISO 27001 Annex A mappings."""

    EXPECTED_REQUIREMENTS = {
        "aws_root_user_access_keys": {"8.2", "5.17"},
        "aws_root_user_mfa_disabled": {"8.5", "8.2"},
        "aws_unused_credentials": {"5.18"},
        "aws_users_with_multiple_active_access_keys": {"5.17"},
        "aws_access_keys_not_rotated": {"5.17"},
        "aws_users_with_direct_policy_attachments": {"5.18"},
        "aws_policies_with_full_administrative_privileges": {"8.2", "5.18"},
        "aws_expired_ssl_tls_certificates": {"8.24"},
        "aws_s3_bucket_mfa_delete": {"8.10"},
        "aws_s3_block_public_access": {"8.3"},
        "aws_rds_encryption_at_rest": {"8.24"},
        "aws_cloudtrail_multi_region": {"8.15", "8.16"},
        "aws_cloudtrail_log_file_validation": {"8.15"},
        "aws_cloudtrail_s3_bucket_access_logging": {"8.15"},
        "aws_cloudtrail_kms_encryption": {"8.24"},
        "aws_ebs_volume_encryption": {"8.24"},
        "aws_cifs_access_restricted_to_trusted_networks": {"8.20"},
        "aws_ipv4_remote_administration_ports_open_to_internet": {"8.20"},
        "aws_ipv6_remote_administration_ports_open_to_internet": {"8.20"},
        "aws_default_security_group_restricts_traffic": {"8.20", "8.22"},
        "aws_ec2_instances_use_imdsv2": {"8.9"},
    }

    @pytest.mark.parametrize("rule", ALL_CIS_AWS_RULES, ids=lambda r: r.id)
    def test_iso27001_requirements(self, rule):
        actual = {
            fw.requirement
            for fw in rule.frameworks
            if fw.short_name == "iso27001" and fw.revision == "2022"
        }
        assert actual == self.EXPECTED_REQUIREMENTS[rule.id]
