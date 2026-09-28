"""SOC 2 Trust Services Criteria mapping expectations.

``EXPECTED_SOC2_REQUIREMENTS`` is the independent source of truth for the
criteria each rule claims. It deliberately derives from no other framework's
table: SOC 2 and ISO 27001 each map straight onto rules, so editing one can never
silently change what the other asserts.
"""

import re
from pathlib import Path

from cartography.rules.data.frameworks import soc2 as soc2_module
from cartography.rules.data.frameworks.soc2 import SOC2_TSC_TITLES
from cartography.rules.data.rules import RULES

RULE_DATA_DIR = Path(__file__).parents[3] / "cartography" / "rules" / "data" / "rules"
SOC2_MODULE_PATH = Path(soc2_module.__file__)
COVERAGE_INDEX_LINE = re.compile(r"^#\s+(uncovered|partial): (.+)$", re.MULTILINE)

EXPECTED_SOC2_REQUIREMENTS = {
    "ai_admin_app_authorizations": {"CC6.3", "CC9.2"},
    "ai_provider_api_key_hygiene": {"CC6.1", "CC6.3"},
    "ai_third_party_app_inventory": {"CC9.2"},
    "ai_third_party_app_sensitive_scopes": {"CC6.1"},
    "aibom_agent_inventory": {"CC6.1"},
    "aibom_coverage_gaps": {"CC6.1"},
    "aws_access_keys_not_rotated": {"CC6.1"},
    "aws_cifs_access_restricted_to_trusted_networks": {"CC6.6"},
    "aws_cloudtrail_kms_encryption": {"CC6.1"},
    "aws_cloudtrail_log_file_validation": {"CC7.2"},
    "aws_cloudtrail_multi_region": {"CC7.2"},
    "aws_cloudtrail_s3_bucket_access_logging": {"CC7.2"},
    "aws_default_security_group_restricts_traffic": {"CC6.1", "CC6.6"},
    "aws_ebs_volume_encryption": {"CC6.1"},
    "aws_ec2_instances_use_imdsv2": {"CC7.1"},
    "aws_expired_ssl_tls_certificates": {"CC6.7"},
    "aws_ipv4_remote_administration_ports_open_to_internet": {"CC6.6"},
    "aws_ipv6_remote_administration_ports_open_to_internet": {"CC6.6"},
    "aws_policies_with_full_administrative_privileges": {"CC6.3"},
    "aws_rds_automated_backups_disabled": {"A1.2"},
    "aws_rds_encryption_at_rest": {"CC6.1"},
    "aws_root_user_access_keys": {"CC6.1", "CC6.3"},
    "aws_root_user_mfa_disabled": {"CC6.1"},
    "aws_s3_bucket_mfa_delete": {"CC7.1"},
    "aws_s3_block_public_access": {"CC6.1"},
    "aws_security_hub_configuration_gaps": {"CC7.1", "CC7.2"},
    "aws_users_with_direct_policy_attachments": {"CC6.3"},
    "aws_users_with_multiple_active_access_keys": {"CC6.1"},
    "azure_sql_minimum_tls_below_1_2": {"CC6.7"},
    "cloud_security_product_deactivated": {"CC7.2"},
    "compute_instance_exposed": {"CC6.6"},
    "database_instance_exposed": {"CC6.6"},
    "databricks_ip_access_list_allows_all": {"CC6.6"},
    "databricks_pat_never_expires": {"CC6.1"},
    "databricks_public_delta_sharing_recipient": {"CC6.1", "CC6.7"},
    "delegation_boundary_modifiable": {"CC6.3"},
    "device_malware_protection_gaps": {"CC6.8"},
    "device_management_gaps": {"CC6.1"},
    "device_security_posture_gaps": {"CC6.1"},
    "device_update_gaps": {"CC7.1"},
    "eol_software": {"CC7.1"},
    "gcp_bigquery_datasets_publicly_accessible": {"CC6.1"},
    "gcp_bigquery_datasets_without_default_cmek": {"CC6.1"},
    "gcp_bigquery_tables_without_cmek": {"CC6.1"},
    "gcp_bucket_uniform_access_disabled": {"CC6.1"},
    "gcp_cloud_dns_dnssec_disabled": {"CC6.6"},
    "gcp_cloud_dns_dnssec_key_signing_uses_rsasha1": {"CC6.6"},
    "gcp_cloud_dns_dnssec_zone_signing_uses_rsasha1": {"CC6.6"},
    "gcp_cloudsql_authorized_networks_open_to_internet": {"CC6.6"},
    "gcp_cloudsql_automated_backups_disabled": {"A1.2"},
    "gcp_cloudsql_mysql_local_infile_not_off": {"CC7.1"},
    "gcp_cloudsql_mysql_skip_show_database_not_on": {"CC7.1"},
    "gcp_cloudsql_postgres_log_connections_not_on": {"CC7.2"},
    "gcp_cloudsql_postgres_log_disconnections_not_on": {"CC7.2"},
    "gcp_cloudsql_postgres_log_error_verbosity_too_permissive": {"CC7.1"},
    "gcp_cloudsql_postgres_log_min_duration_statement_not_disabled": {"CC7.1"},
    "gcp_cloudsql_postgres_log_min_error_statement_below_error": {"CC7.1"},
    "gcp_cloudsql_postgres_log_min_messages_below_warning": {"CC7.1"},
    "gcp_cloudsql_postgres_pgaudit_not_enabled": {"CC7.2"},
    "gcp_cloudsql_public_ips": {"CC6.6"},
    "gcp_cloudsql_sqlserver_contained_database_authentication_enabled": {"CC7.1"},
    "gcp_cloudsql_sqlserver_cross_db_ownership_chaining_enabled": {"CC7.1"},
    "gcp_cloudsql_sqlserver_external_scripts_enabled": {"CC7.1"},
    "gcp_cloudsql_sqlserver_remote_access_not_off": {"CC7.1"},
    "gcp_cloudsql_sqlserver_trace_flag_3625_not_on": {"CC7.1"},
    "gcp_cloudsql_sqlserver_user_connections_limiting": {"CC7.1"},
    "gcp_cloudsql_sqlserver_user_options_configured": {"CC7.1"},
    "gcp_cloudsql_ssl_not_enforced": {"CC6.7"},
    "gcp_compute_instance_public_ips": {"CC6.6"},
    "gcp_default_network_exists": {"CC6.1", "CC6.6"},
    "gcp_default_service_account_full_cloud_api_scope": {"CC6.3"},
    "gcp_instances_not_blocking_project_wide_ssh_keys": {"CC6.1"},
    "gcp_instances_using_default_service_account": {"CC6.1"},
    "gcp_instances_with_ip_forwarding": {"CC6.6"},
    "gcp_instances_with_serial_port_access": {"CC6.1"},
    "gcp_instances_without_confidential_computing_enabled": {"CC6.1"},
    "gcp_instances_without_shielded_vm_enabled": {"CC7.1"},
    "gcp_kms_keys_without_rotation_policy": {"CC6.1"},
    "gcp_projects_without_effective_os_login": {"CC6.1"},
    "gcp_subnets_without_compliant_vpc_flow_logs": {"CC7.2"},
    "gcp_unrestricted_rdp_access": {"CC6.6"},
    "gcp_unrestricted_ssh_access": {"CC6.6"},
    "googleworkspace_admins_without_enforced_2sv": {"CC6.1"},
    "googleworkspace_super_admin_accounts_used_for_daily_admin": {"CC6.3"},
    "googleworkspace_too_many_super_admin_accounts": {"CC6.3"},
    "googleworkspace_users_without_enforced_2sv": {"CC6.1"},
    "guardduty_active_threat": {"CC7.2"},
    "iam_role_external_account_trust": {"CC6.3", "CC6.6"},
    "identity_administration_privileges": {"CC6.3"},
    "identity_mfa_gaps": {"CC6.1"},
    "inactive-user-active-accounts": {"CC6.2"},
    "kubernetes_bind_impersonate_escalate_permissions": {"CC6.3"},
    "kubernetes_cluster_admin_role_usage": {"CC6.3"},
    "kubernetes_containers_allowing_privilege_escalation": {"CC7.1"},
    "kubernetes_containers_using_hostports": {"CC6.6", "CC7.1"},
    "kubernetes_control_plane_exposed": {"CC6.6"},
    "kubernetes_csr_approval_subresource_access": {"CC6.1"},
    "kubernetes_default_service_account_bindings": {"CC6.3"},
    "kubernetes_node_proxy_subresource_access": {"CC6.3"},
    "kubernetes_pods_missing_runtime_default_seccomp": {"CC7.1"},
    "kubernetes_pods_sharing_host_ipc_namespace": {"CC7.1"},
    "kubernetes_pods_sharing_host_network_namespace": {"CC6.6", "CC7.1"},
    "kubernetes_pods_sharing_host_pid_namespace": {"CC7.1"},
    "kubernetes_pods_using_hostpath_volumes": {"CC7.1"},
    "kubernetes_roles_grant_persistent_volume_creation": {"CC6.3"},
    "kubernetes_roles_grant_pod_creation": {"CC6.3"},
    "kubernetes_roles_grant_secret_access": {"CC6.1"},
    "kubernetes_secrets_used_as_environment_variables": {"CC6.1"},
    "kubernetes_service_account_token_creation_access": {"CC6.1"},
    "kubernetes_service_account_tokens_mounted_in_pods": {"CC6.1"},
    "kubernetes_system_masters_group_usage": {"CC6.3"},
    "kubernetes_webhook_configuration_access": {"CC7.1"},
    "kubernetes_wildcard_roles": {"CC6.3"},
    "malicious-npm-dependencies-shai-hulud": {"CC6.8", "CC7.1"},
    "mfa-missing": {"CC6.1"},
    "object_storage_public": {"CC6.1", "CC6.6"},
    "policy_administration_privileges": {"CC6.3"},
    "public_snapshots": {"CC6.1", "CC6.6", "CC6.7"},
    "serverless_workload_exposed": {"CC6.6"},
    "tailscale_device_auto_updates_disabled": {"CC7.1"},
    "tailscale_device_key_expiry_disabled": {"CC6.1"},
    "tailscale_network_flow_logging_disabled": {"CC7.2"},
    "tailscale_tailnet_approval_disabled": {"CC6.1"},
    "unmanaged-account": {"CC6.2"},
    "unpinned-github-actions": {"CC6.8"},
    "workload_identity_admin_capabilities": {"CC6.3"},
}

# Rules whose absence from the table above is a decision, not an oversight.
# Justify every entry: an unlisted rule is indistinguishable from a forgotten one.
DELIBERATELY_UNMAPPED_RULES = {
    # Having too *few* super admins is an availability and operations concern.
    # No Trust Services criterion speaks to it.
    "googleworkspace_too_few_super_admin_accounts",
}

EXPECTED_SOC2_DATAMODEL_TODOS = {
    "A1.1",
    "A1.2",
    "A1.3",
    "C1.1",
    "C1.2",
    "CC6.5",
    "CC6.7",
    "CC6.8",
    "CC7.2",
    "CC7.3",
    "CC7.4",
    "CC7.5",
}


def _soc2_requirements(rule_id: str) -> set[str]:
    return {
        framework.requirement.upper()
        for framework in RULES[rule_id].frameworks
        if framework.short_name == "soc2"
    }


def test_soc2_mapped_rules_have_expected_requirements():
    for rule_id, expected_requirements in EXPECTED_SOC2_REQUIREMENTS.items():
        assert _soc2_requirements(rule_id) == expected_requirements, rule_id


def test_every_soc2_mapping_is_declared_in_the_table():
    """No rule may claim a criterion the table does not know about.

    Without this, a rule added later could carry any mapping at all and go
    unchecked, because the table only iterates the rules it already lists.
    """
    mapped_rule_ids = {
        rule_id for rule_id, rule in RULES.items() if _soc2_requirements(rule_id)
    }

    assert mapped_rule_ids == set(EXPECTED_SOC2_REQUIREMENTS)


def test_deliberately_unmapped_rules_carry_no_soc2_mapping():
    for rule_id in DELIBERATELY_UNMAPPED_RULES:
        assert not _soc2_requirements(rule_id), rule_id


def test_soc2_mappings_use_the_tsc_scope():
    for rule in RULES.values():
        for framework in rule.frameworks:
            if framework.short_name != "soc2":
                continue

            assert framework.scope == "tsc", (rule.id, framework)
            assert framework.revision == "2022", (rule.id, framework)


def test_soc2_declared_titles_are_all_mapped():
    """A criterion with no rule behind it must not be declared.

    Titles exist to render mappings. Declaring one that no rule covers makes the
    framework look broader than it is; the gap belongs in a
    ``# TODO: SOC 2 <criterion>:`` comment instead.
    """
    mapped_requirements = {
        framework.requirement
        for rule in RULES.values()
        for framework in rule.frameworks
        if framework.short_name == "soc2"
    }

    assert set(SOC2_TSC_TITLES) == mapped_requirements


def test_soc2_mappings_have_control_titles():
    for rule in RULES.values():
        for framework in rule.frameworks:
            if framework.short_name == "soc2":
                assert framework.control_title is not None, (rule.id, framework)


def _documented_gap_requirements() -> set[str]:
    rule_source = "\n".join(
        path.read_text() for path in sorted(RULE_DATA_DIR.glob("*.py"))
    )
    return set(re.findall(r"# TODO: SOC 2 ([A-Z]+\d+\.\d+):", rule_source))


def _coverage_index() -> dict[str, set[str]]:
    """Parse the coverage-gap index comment in the SOC 2 framework module."""
    return {
        kind: {criterion.strip() for criterion in criteria.split(",")}
        for kind, criteria in COVERAGE_INDEX_LINE.findall(SOC2_MODULE_PATH.read_text())
    }


def test_soc2_datamodel_gaps_are_documented():
    assert _documented_gap_requirements() == EXPECTED_SOC2_DATAMODEL_TODOS


def test_soc2_coverage_index_matches_the_documented_gaps():
    """The index in soc2.py must not drift from the TODO blocks it points at."""
    index = _coverage_index()

    assert index["uncovered"] | index["partial"] == _documented_gap_requirements()


def test_soc2_coverage_index_tells_the_truth_about_coverage():
    """A criterion filed as uncovered must have no rule, and partial must have one."""
    index = _coverage_index()
    mapped_requirements = {
        framework.requirement.upper()
        for rule in RULES.values()
        for framework in rule.frameworks
        if framework.short_name == "soc2"
    }

    assert not index["uncovered"] & mapped_requirements
    assert index["partial"] <= mapped_requirements
