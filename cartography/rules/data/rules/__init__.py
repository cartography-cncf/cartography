from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_3_1_default_network
from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_3_3_dnssec_enabled
from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_3_4_dnssec_no_rsasha1_ksk
from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_3_5_dnssec_no_rsasha1_zsk
from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_3_6_unrestricted_ssh
from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_3_7_unrestricted_rdp
from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_3_8_vpc_flow_logs
from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_4_1_default_service_account
from cartography.rules.data.rules.cis_4_0_gcp import (
    cis_gcp_4_2_default_service_account_full_api,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    cis_gcp_4_3_block_project_wide_ssh_keys,
)
from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_4_4_oslogin_enabled
from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_4_5_serial_ports_disabled
from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_4_6_ip_forwarding
from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_4_8_shielded_vm
from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_4_9_public_ip
from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_4_11_confidential_compute
from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_5_2_bucket_uniform_access
from cartography.rules.data.rules.cis_4_0_gcp import (
    cis_gcp_6_1_2_cloudsql_mysql_skip_show_database,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    cis_gcp_6_1_3_cloudsql_mysql_local_infile,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    cis_gcp_6_2_1_cloudsql_postgres_log_error_verbosity,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    cis_gcp_6_2_2_cloudsql_postgres_log_connections,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    cis_gcp_6_2_3_cloudsql_postgres_log_disconnections,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    cis_gcp_6_2_5_cloudsql_postgres_log_min_messages,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    cis_gcp_6_2_6_cloudsql_postgres_log_min_error_statement,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    cis_gcp_6_2_7_cloudsql_postgres_log_min_duration_statement,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    cis_gcp_6_2_8_cloudsql_postgres_enable_pgaudit,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    cis_gcp_6_3_1_cloudsql_sqlserver_external_scripts,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    cis_gcp_6_3_2_cloudsql_sqlserver_cross_db_ownership,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    cis_gcp_6_3_3_cloudsql_sqlserver_user_connections,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    cis_gcp_6_3_4_cloudsql_sqlserver_user_options,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    cis_gcp_6_3_5_cloudsql_sqlserver_remote_access,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    cis_gcp_6_3_6_cloudsql_sqlserver_trace_3625,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    cis_gcp_6_3_7_cloudsql_sqlserver_contained_auth,
)
from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_6_4_cloudsql_ssl_required
from cartography.rules.data.rules.cis_4_0_gcp import (
    cis_gcp_6_5_cloudsql_authorized_networks,
)
from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_6_6_cloudsql_public_ip
from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_6_7_cloudsql_backups
from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_7_1_bigquery_dataset_public
from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_7_2_bigquery_table_cmek
from cartography.rules.data.rules.cis_4_0_gcp import cis_gcp_7_3_bigquery_dataset_cmek
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
from cartography.rules.data.rules.cis_google_workspace import (
    cis_gw_1_1_1_super_admin_count_too_low,
)
from cartography.rules.data.rules.cis_google_workspace import (
    cis_gw_1_1_2_super_admin_count_too_high,
)
from cartography.rules.data.rules.cis_google_workspace import (
    cis_gw_1_1_3_super_admin_used_for_daily_admin,
)
from cartography.rules.data.rules.cis_google_workspace import (
    cis_gw_4_1_1_1_admin_2sv_not_enforced,
)
from cartography.rules.data.rules.cis_google_workspace import (
    cis_gw_4_1_1_3_user_2sv_not_enforced,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_1_cluster_admin_usage,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import cis_k8s_5_1_2_secret_access
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_3_wildcard_roles,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_4_pod_create_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_5_default_sa_bindings,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_7_system_masters_group,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_8_escalation_permissions,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_9_pv_create_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_10_node_proxy_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_11_csr_approval_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_12_webhook_config_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_13_sa_token_creation,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    cis_k8s_5_1_6_sa_token_mounts,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import cis_k8s_5_2_3_host_pid
from cartography.rules.data.rules.cis_kubernetes_workloads import cis_k8s_5_2_4_host_ipc
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    cis_k8s_5_2_5_host_network,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    cis_k8s_5_2_6_allow_privilege_escalation,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    cis_k8s_5_2_11_host_path_volumes,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    cis_k8s_5_2_12_host_ports,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    cis_k8s_5_4_1_secrets_in_env_vars,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    cis_k8s_5_6_2_runtime_default_seccomp,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    cis_k8s_5_6_4_default_namespace,
)
from cartography.rules.data.rules.cloud_security_product_deactivated import (
    cloud_security_product_deactivated,
)
from cartography.rules.data.rules.compute_instance_exposed import (
    compute_instance_exposed,
)
from cartography.rules.data.rules.database_instance_exposed import (
    database_instance_exposed,
)
from cartography.rules.data.rules.delegation_boundary_modifiable import (
    delegation_boundary_modifiable,
)
from cartography.rules.data.rules.eol_software import eol_software
from cartography.rules.data.rules.identity_administration_privileges import (
    identity_administration_privileges,
)
from cartography.rules.data.rules.inactive_user_active_accounts import (
    inactive_user_active_accounts,
)
from cartography.rules.data.rules.malicious_npm_dependencies_shai_hulud import (
    malicious_npm_dependencies_shai_hulud,
)
from cartography.rules.data.rules.mfa_missing import missing_mfa_rule
from cartography.rules.data.rules.nist_ai_rmf import nist_ai_admin_ai_app_authorizations
from cartography.rules.data.rules.nist_ai_rmf import nist_ai_aibom_agent_inventory
from cartography.rules.data.rules.nist_ai_rmf import nist_ai_aibom_coverage_gaps
from cartography.rules.data.rules.nist_ai_rmf import nist_ai_provider_api_key_hygiene
from cartography.rules.data.rules.nist_ai_rmf import nist_ai_third_party_app_inventory
from cartography.rules.data.rules.nist_ai_rmf import (
    nist_ai_third_party_app_sensitive_scopes,
)
from cartography.rules.data.rules.object_storage_public import object_storage_public
from cartography.rules.data.rules.policy_administration_privileges import (
    policy_administration_privileges,
)
from cartography.rules.data.rules.serverless_workload_exposed import (
    serverless_workload_exposed,
)
from cartography.rules.data.rules.subimage_coverage import aws_account_not_synced
from cartography.rules.data.rules.subimage_coverage import container_image_not_found
from cartography.rules.data.rules.subimage_coverage import (
    repository_without_slsa_provenance,
)
from cartography.rules.data.rules.subimage_coverage import (
    subimage_framework_disabled_module_enabled,
)
from cartography.rules.data.rules.subimage_coverage import (
    subimage_module_not_configured,
)
from cartography.rules.data.rules.unmanaged_accounts import unmanaged_accounts
from cartography.rules.data.rules.unpinned_github_actions import unpinned_github_actions
from cartography.rules.data.rules.workload_identity_admin_capabilities import (
    workload_identity_admin_capabilities,
)

# Rule registry - all available rules
RULES = {
    # CIS AWS IAM Rules (Section 2)
    cis_aws_2_11_unused_credentials.id: cis_aws_2_11_unused_credentials,
    cis_aws_2_12_multiple_access_keys.id: cis_aws_2_12_multiple_access_keys,
    cis_aws_2_13_access_key_not_rotated.id: cis_aws_2_13_access_key_not_rotated,
    cis_aws_2_14_user_direct_policies.id: cis_aws_2_14_user_direct_policies,
    cis_aws_2_18_expired_certificates.id: cis_aws_2_18_expired_certificates,
    # CIS AWS Storage Rules (Section 3)
    cis_aws_3_1_2_s3_mfa_delete.id: cis_aws_3_1_2_s3_mfa_delete,
    cis_aws_3_1_4_s3_block_public_access.id: cis_aws_3_1_4_s3_block_public_access,
    cis_aws_3_2_1_rds_encryption.id: cis_aws_3_2_1_rds_encryption,
    # CIS AWS Logging Rules (Section 4)
    cis_aws_4_1_cloudtrail_multi_region.id: cis_aws_4_1_cloudtrail_multi_region,
    cis_aws_4_2_cloudtrail_log_validation.id: cis_aws_4_2_cloudtrail_log_validation,
    cis_aws_4_4_cloudtrail_bucket_access_logging.id: cis_aws_4_4_cloudtrail_bucket_access_logging,
    cis_aws_4_5_cloudtrail_encryption.id: cis_aws_4_5_cloudtrail_encryption,
    # CIS AWS Networking Rules (Section 6)
    cis_aws_6_1_1_ebs_encryption.id: cis_aws_6_1_1_ebs_encryption,
    cis_aws_6_3_remote_admin_ipv4.id: cis_aws_6_3_remote_admin_ipv4,
    cis_aws_6_4_remote_admin_ipv6.id: cis_aws_6_4_remote_admin_ipv6,
    cis_aws_6_5_default_sg_traffic.id: cis_aws_6_5_default_sg_traffic,
    cis_aws_6_7_ec2_imdsv2.id: cis_aws_6_7_ec2_imdsv2,
    # SubImage Coverage Rules
    subimage_module_not_configured.id: subimage_module_not_configured,
    subimage_framework_disabled_module_enabled.id: subimage_framework_disabled_module_enabled,
    container_image_not_found.id: container_image_not_found,
    repository_without_slsa_provenance.id: repository_without_slsa_provenance,
    aws_account_not_synced.id: aws_account_not_synced,
    # Security Rules
    compute_instance_exposed.id: compute_instance_exposed,
    database_instance_exposed.id: database_instance_exposed,
    delegation_boundary_modifiable.id: delegation_boundary_modifiable,
    eol_software.id: eol_software,
    identity_administration_privileges.id: identity_administration_privileges,
    inactive_user_active_accounts.id: inactive_user_active_accounts,
    missing_mfa_rule.id: missing_mfa_rule,
    object_storage_public.id: object_storage_public,
    policy_administration_privileges.id: policy_administration_privileges,
    serverless_workload_exposed.id: serverless_workload_exposed,
    unmanaged_accounts.id: unmanaged_accounts,
    workload_identity_admin_capabilities.id: workload_identity_admin_capabilities,
    cloud_security_product_deactivated.id: cloud_security_product_deactivated,
    malicious_npm_dependencies_shai_hulud.id: malicious_npm_dependencies_shai_hulud,
    unpinned_github_actions.id: unpinned_github_actions,
    # NIST AI RMF Rules
    nist_ai_third_party_app_inventory.id: nist_ai_third_party_app_inventory,
    nist_ai_third_party_app_sensitive_scopes.id: nist_ai_third_party_app_sensitive_scopes,
    nist_ai_admin_ai_app_authorizations.id: nist_ai_admin_ai_app_authorizations,
    nist_ai_aibom_agent_inventory.id: nist_ai_aibom_agent_inventory,
    nist_ai_aibom_coverage_gaps.id: nist_ai_aibom_coverage_gaps,
    nist_ai_provider_api_key_hygiene.id: nist_ai_provider_api_key_hygiene,
    # CIS GCP 4.0 Rules
    cis_gcp_3_1_default_network.id: cis_gcp_3_1_default_network,
    cis_gcp_3_3_dnssec_enabled.id: cis_gcp_3_3_dnssec_enabled,
    cis_gcp_3_4_dnssec_no_rsasha1_ksk.id: cis_gcp_3_4_dnssec_no_rsasha1_ksk,
    cis_gcp_3_5_dnssec_no_rsasha1_zsk.id: cis_gcp_3_5_dnssec_no_rsasha1_zsk,
    cis_gcp_3_8_vpc_flow_logs.id: cis_gcp_3_8_vpc_flow_logs,
    cis_gcp_3_6_unrestricted_ssh.id: cis_gcp_3_6_unrestricted_ssh,
    cis_gcp_3_7_unrestricted_rdp.id: cis_gcp_3_7_unrestricted_rdp,
    cis_gcp_4_1_default_service_account.id: cis_gcp_4_1_default_service_account,
    cis_gcp_4_2_default_service_account_full_api.id: cis_gcp_4_2_default_service_account_full_api,
    cis_gcp_4_3_block_project_wide_ssh_keys.id: cis_gcp_4_3_block_project_wide_ssh_keys,
    cis_gcp_4_4_oslogin_enabled.id: cis_gcp_4_4_oslogin_enabled,
    cis_gcp_4_5_serial_ports_disabled.id: cis_gcp_4_5_serial_ports_disabled,
    cis_gcp_4_6_ip_forwarding.id: cis_gcp_4_6_ip_forwarding,
    cis_gcp_4_8_shielded_vm.id: cis_gcp_4_8_shielded_vm,
    cis_gcp_4_9_public_ip.id: cis_gcp_4_9_public_ip,
    cis_gcp_4_11_confidential_compute.id: cis_gcp_4_11_confidential_compute,
    cis_gcp_5_2_bucket_uniform_access.id: cis_gcp_5_2_bucket_uniform_access,
    cis_gcp_6_1_2_cloudsql_mysql_skip_show_database.id: cis_gcp_6_1_2_cloudsql_mysql_skip_show_database,
    cis_gcp_6_1_3_cloudsql_mysql_local_infile.id: cis_gcp_6_1_3_cloudsql_mysql_local_infile,
    cis_gcp_6_2_1_cloudsql_postgres_log_error_verbosity.id: cis_gcp_6_2_1_cloudsql_postgres_log_error_verbosity,
    cis_gcp_6_2_2_cloudsql_postgres_log_connections.id: cis_gcp_6_2_2_cloudsql_postgres_log_connections,
    cis_gcp_6_2_3_cloudsql_postgres_log_disconnections.id: cis_gcp_6_2_3_cloudsql_postgres_log_disconnections,
    cis_gcp_6_2_5_cloudsql_postgres_log_min_messages.id: cis_gcp_6_2_5_cloudsql_postgres_log_min_messages,
    cis_gcp_6_2_6_cloudsql_postgres_log_min_error_statement.id: cis_gcp_6_2_6_cloudsql_postgres_log_min_error_statement,
    cis_gcp_6_2_7_cloudsql_postgres_log_min_duration_statement.id: cis_gcp_6_2_7_cloudsql_postgres_log_min_duration_statement,
    cis_gcp_6_2_8_cloudsql_postgres_enable_pgaudit.id: cis_gcp_6_2_8_cloudsql_postgres_enable_pgaudit,
    cis_gcp_6_3_1_cloudsql_sqlserver_external_scripts.id: cis_gcp_6_3_1_cloudsql_sqlserver_external_scripts,
    cis_gcp_6_3_2_cloudsql_sqlserver_cross_db_ownership.id: cis_gcp_6_3_2_cloudsql_sqlserver_cross_db_ownership,
    cis_gcp_6_3_3_cloudsql_sqlserver_user_connections.id: cis_gcp_6_3_3_cloudsql_sqlserver_user_connections,
    cis_gcp_6_3_4_cloudsql_sqlserver_user_options.id: cis_gcp_6_3_4_cloudsql_sqlserver_user_options,
    cis_gcp_6_3_5_cloudsql_sqlserver_remote_access.id: cis_gcp_6_3_5_cloudsql_sqlserver_remote_access,
    cis_gcp_6_3_6_cloudsql_sqlserver_trace_3625.id: cis_gcp_6_3_6_cloudsql_sqlserver_trace_3625,
    cis_gcp_6_3_7_cloudsql_sqlserver_contained_auth.id: cis_gcp_6_3_7_cloudsql_sqlserver_contained_auth,
    cis_gcp_6_4_cloudsql_ssl_required.id: cis_gcp_6_4_cloudsql_ssl_required,
    cis_gcp_6_5_cloudsql_authorized_networks.id: cis_gcp_6_5_cloudsql_authorized_networks,
    cis_gcp_6_6_cloudsql_public_ip.id: cis_gcp_6_6_cloudsql_public_ip,
    cis_gcp_6_7_cloudsql_backups.id: cis_gcp_6_7_cloudsql_backups,
    cis_gcp_7_1_bigquery_dataset_public.id: cis_gcp_7_1_bigquery_dataset_public,
    cis_gcp_7_2_bigquery_table_cmek.id: cis_gcp_7_2_bigquery_table_cmek,
    cis_gcp_7_3_bigquery_dataset_cmek.id: cis_gcp_7_3_bigquery_dataset_cmek,
    # CIS Google Workspace Rules
    cis_gw_1_1_1_super_admin_count_too_low.id: cis_gw_1_1_1_super_admin_count_too_low,
    cis_gw_1_1_2_super_admin_count_too_high.id: cis_gw_1_1_2_super_admin_count_too_high,
    cis_gw_1_1_3_super_admin_used_for_daily_admin.id: cis_gw_1_1_3_super_admin_used_for_daily_admin,
    cis_gw_4_1_1_3_user_2sv_not_enforced.id: cis_gw_4_1_1_3_user_2sv_not_enforced,
    cis_gw_4_1_1_1_admin_2sv_not_enforced.id: cis_gw_4_1_1_1_admin_2sv_not_enforced,
    # CIS Kubernetes Benchmark v1.12 Rules
    cis_k8s_5_1_1_cluster_admin_usage.id: cis_k8s_5_1_1_cluster_admin_usage,
    cis_k8s_5_1_2_secret_access.id: cis_k8s_5_1_2_secret_access,
    cis_k8s_5_1_3_wildcard_roles.id: cis_k8s_5_1_3_wildcard_roles,
    cis_k8s_5_1_4_pod_create_access.id: cis_k8s_5_1_4_pod_create_access,
    cis_k8s_5_1_5_default_sa_bindings.id: cis_k8s_5_1_5_default_sa_bindings,
    cis_k8s_5_1_7_system_masters_group.id: cis_k8s_5_1_7_system_masters_group,
    cis_k8s_5_1_8_escalation_permissions.id: cis_k8s_5_1_8_escalation_permissions,
    cis_k8s_5_1_9_pv_create_access.id: cis_k8s_5_1_9_pv_create_access,
    cis_k8s_5_1_10_node_proxy_access.id: cis_k8s_5_1_10_node_proxy_access,
    cis_k8s_5_1_11_csr_approval_access.id: cis_k8s_5_1_11_csr_approval_access,
    cis_k8s_5_1_12_webhook_config_access.id: cis_k8s_5_1_12_webhook_config_access,
    cis_k8s_5_1_13_sa_token_creation.id: cis_k8s_5_1_13_sa_token_creation,
    cis_k8s_5_1_6_sa_token_mounts.id: cis_k8s_5_1_6_sa_token_mounts,
    cis_k8s_5_2_3_host_pid.id: cis_k8s_5_2_3_host_pid,
    cis_k8s_5_2_4_host_ipc.id: cis_k8s_5_2_4_host_ipc,
    cis_k8s_5_2_5_host_network.id: cis_k8s_5_2_5_host_network,
    cis_k8s_5_2_6_allow_privilege_escalation.id: cis_k8s_5_2_6_allow_privilege_escalation,
    cis_k8s_5_2_11_host_path_volumes.id: cis_k8s_5_2_11_host_path_volumes,
    cis_k8s_5_2_12_host_ports.id: cis_k8s_5_2_12_host_ports,
    cis_k8s_5_6_2_runtime_default_seccomp.id: cis_k8s_5_6_2_runtime_default_seccomp,
    cis_k8s_5_4_1_secrets_in_env_vars.id: cis_k8s_5_4_1_secrets_in_env_vars,
    cis_k8s_5_6_4_default_namespace.id: cis_k8s_5_6_4_default_namespace,
}
