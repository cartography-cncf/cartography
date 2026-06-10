from cartography.rules.data.rules import RULES

EXPECTED_ISO27001_REQUIREMENTS = {
    "gcp_default_network_exists": {"8.20", "8.22"},
    "gcp_cloud_dns_dnssec_disabled": {"8.20"},
    "gcp_cloud_dns_dnssec_key_signing_uses_rsasha1": {"8.24"},
    "gcp_cloud_dns_dnssec_zone_signing_uses_rsasha1": {"8.24"},
    "gcp_unrestricted_ssh_access": {"8.20"},
    "gcp_unrestricted_rdp_access": {"8.20"},
    "gcp_subnets_without_compliant_vpc_flow_logs": {"8.15", "8.16"},
    "gcp_instances_using_default_service_account": {"5.16"},
    "gcp_default_service_account_full_cloud_api_scope": {"5.18", "8.2"},
    "gcp_instances_not_blocking_project_wide_ssh_keys": {"8.5"},
    "gcp_projects_without_effective_os_login": {"8.5"},
    "gcp_instances_with_serial_port_access": {"8.3"},
    "gcp_instances_with_ip_forwarding": {"8.20"},
    "gcp_instances_without_shielded_vm_enabled": {"8.9"},
    "gcp_compute_instance_public_ips": {"8.20"},
    "gcp_instances_without_confidential_computing_enabled": {"8.24"},
    "gcp_bucket_uniform_access_disabled": {"8.3"},
    "gcp_cloudsql_mysql_skip_show_database_not_on": {"8.9"},
    "gcp_cloudsql_mysql_local_infile_not_off": {"8.9"},
    "gcp_cloudsql_postgres_log_error_verbosity_too_permissive": {"8.9"},
    "gcp_cloudsql_postgres_log_connections_not_on": {"8.9"},
    "gcp_cloudsql_postgres_log_disconnections_not_on": {"8.9"},
    "gcp_cloudsql_postgres_log_min_messages_below_warning": {"8.9"},
    "gcp_cloudsql_postgres_log_min_error_statement_below_error": {"8.9"},
    "gcp_cloudsql_postgres_log_min_duration_statement_not_disabled": {"8.9"},
    "gcp_cloudsql_postgres_pgaudit_not_enabled": {"8.9"},
    "gcp_cloudsql_sqlserver_external_scripts_enabled": {"8.9"},
    "gcp_cloudsql_sqlserver_cross_db_ownership_chaining_enabled": {"8.9"},
    "gcp_cloudsql_sqlserver_user_connections_limiting": {"8.9"},
    "gcp_cloudsql_sqlserver_user_options_configured": {"8.9"},
    "gcp_cloudsql_sqlserver_remote_access_not_off": {"8.9"},
    "gcp_cloudsql_sqlserver_trace_flag_3625_not_on": {"8.9"},
    "gcp_cloudsql_sqlserver_contained_database_authentication_enabled": {"8.9"},
    "gcp_cloudsql_ssl_not_enforced": {"8.24"},
    "gcp_cloudsql_authorized_networks_open_to_internet": {"8.20"},
    "gcp_cloudsql_public_ips": {"8.20"},
    "gcp_cloudsql_automated_backups_disabled": {"8.13"},
    "gcp_bigquery_datasets_publicly_accessible": {"8.3"},
    "gcp_bigquery_tables_without_cmek": {"8.24"},
    "gcp_bigquery_datasets_without_default_cmek": {"8.24"},
    "googleworkspace_too_few_super_admin_accounts": {"8.2"},
    "googleworkspace_too_many_super_admin_accounts": {"5.18", "8.2"},
    "googleworkspace_super_admin_accounts_used_for_daily_admin": {"8.2"},
    "googleworkspace_admins_without_enforced_2sv": {"8.5", "8.2"},
    "googleworkspace_users_without_enforced_2sv": {"8.5"},
    "cloud_security_product_deactivated": {"8.16"},
    "compute_instance_exposed": {"8.20"},
    "database_instance_exposed": {"8.20"},
    "delegation_boundary_modifiable": {"5.18", "8.2"},
    "device_security_posture_gaps": {"8.1", "8.8", "8.9"},
    "eol_software": {"8.8"},
    "identity_administration_privileges": {"5.18", "8.2"},
    "identity_mfa_gaps": {"8.5"},
    "inactive-user-active-accounts": {"5.18"},
    "malicious-npm-dependencies-shai-hulud": {"5.21", "8.8"},
    "mfa-missing": {"8.5"},
    "object_storage_public": {"8.3"},
    "policy_administration_privileges": {"5.18", "8.2"},
    "tailscale_tailnet_approval_disabled": {"5.15"},
    "tailscale_network_flow_logging_disabled": {"8.15"},
    "tailscale_device_auto_updates_disabled": {"8.8"},
    "tailscale_device_key_expiry_disabled": {"5.17"},
    "unmanaged-account": {"5.16", "5.18"},
    "unpinned-github-actions": {"8.28", "8.32"},
    "workload_identity_admin_capabilities": {"5.18", "8.2"},
    "kubernetes_cluster_admin_role_usage": {"5.18", "8.2"},
    "kubernetes_roles_grant_secret_access": {"8.3"},
    "kubernetes_wildcard_roles": {"5.18", "8.2"},
    "kubernetes_roles_grant_pod_creation": {"5.18"},
    "kubernetes_default_service_account_bindings": {"5.16", "5.18"},
    "kubernetes_service_account_tokens_mounted_in_pods": {"5.17"},
    "kubernetes_system_masters_group_usage": {"8.2"},
    "kubernetes_bind_impersonate_escalate_permissions": {"5.18", "8.2"},
    "kubernetes_roles_grant_persistent_volume_creation": {"5.18"},
    "kubernetes_node_proxy_subresource_access": {"8.2"},
    "kubernetes_csr_approval_subresource_access": {"8.5"},
    "kubernetes_webhook_configuration_access": {"8.9"},
    "kubernetes_service_account_token_creation_access": {"5.17"},
    "kubernetes_pods_sharing_host_pid_namespace": {"8.9"},
    "kubernetes_pods_sharing_host_ipc_namespace": {"8.9"},
    "kubernetes_pods_sharing_host_network_namespace": {"8.9", "8.20"},
    "kubernetes_containers_allowing_privilege_escalation": {"8.9"},
    "kubernetes_pods_using_hostpath_volumes": {"8.9"},
    "kubernetes_containers_using_hostports": {"8.9", "8.20"},
    "kubernetes_secrets_used_as_environment_variables": {"8.12"},
    "kubernetes_pods_missing_runtime_default_seccomp": {"8.9"},
    "ai_third_party_app_inventory": {"5.21", "5.23"},
    "ai_third_party_app_sensitive_scopes": {"5.15", "8.3"},
    "ai_admin_app_authorizations": {"5.18", "8.2"},
    "aibom_agent_inventory": {"5.9", "5.21"},
    "aibom_coverage_gaps": {"5.9", "5.21"},
    "ai_provider_api_key_hygiene": {"5.17", "5.18"},
}


def test_iso27001_mapped_rules_have_expected_requirements():
    for rule_id, expected_requirements in EXPECTED_ISO27001_REQUIREMENTS.items():
        rule = RULES[rule_id]
        actual_requirements = {
            fw.requirement
            for fw in rule.frameworks
            if fw.short_name == "iso" and fw.scope == "27001" and fw.revision == "2022"
        }
        assert actual_requirements == expected_requirements


def test_iso27001_mapped_rules_have_control_titles():
    expected_titles = {
        "5.18": "Access rights",
        "8.2": "Privileged access rights",
        "8.20": "Network security",
        "8.24": "Use of cryptography",
    }

    for rule_id in EXPECTED_ISO27001_REQUIREMENTS:
        rule = RULES[rule_id]
        for framework in rule.frameworks:
            if framework.short_name != "iso27001":
                continue

            assert framework.control_title is not None
            if framework.requirement in expected_titles:
                assert framework.control_title == expected_titles[framework.requirement]
