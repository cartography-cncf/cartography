from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_bigquery_datasets_publicly_accessible,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_bigquery_datasets_without_default_cmek,
)
from cartography.rules.data.rules.cis_4_0_gcp import gcp_bigquery_tables_without_cmek
from cartography.rules.data.rules.cis_4_0_gcp import gcp_bucket_uniform_access_disabled
from cartography.rules.data.rules.cis_4_0_gcp import gcp_cloud_dns_dnssec_disabled
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_cloud_dns_dnssec_key_signing_uses_rsasha1,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_cloud_dns_dnssec_zone_signing_uses_rsasha1,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_cloudsql_authorized_networks_open_to_internet,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_cloudsql_automated_backups_disabled,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_cloudsql_mysql_local_infile_not_off,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_cloudsql_mysql_skip_show_database_not_on,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_cloudsql_postgres_log_connections_not_on,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_cloudsql_postgres_log_disconnections_not_on,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_cloudsql_postgres_log_error_verbosity_too_permissive,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_cloudsql_postgres_log_min_duration_statement_not_disabled,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_cloudsql_postgres_log_min_error_statement_below_error,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_cloudsql_postgres_log_min_messages_below_warning,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_cloudsql_postgres_pgaudit_not_enabled,
)
from cartography.rules.data.rules.cis_4_0_gcp import gcp_cloudsql_public_ips
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_cloudsql_sqlserver_contained_database_authentication_enabled,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_cloudsql_sqlserver_cross_db_ownership_chaining_enabled,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_cloudsql_sqlserver_external_scripts_enabled,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_cloudsql_sqlserver_remote_access_not_off,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_cloudsql_sqlserver_trace_flag_3625_not_on,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_cloudsql_sqlserver_user_connections_limiting,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_cloudsql_sqlserver_user_options_configured,
)
from cartography.rules.data.rules.cis_4_0_gcp import gcp_cloudsql_ssl_not_enforced
from cartography.rules.data.rules.cis_4_0_gcp import gcp_compute_instance_public_ips
from cartography.rules.data.rules.cis_4_0_gcp import gcp_default_network_exists
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_default_service_account_full_cloud_api_scope,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_instances_not_blocking_project_wide_ssh_keys,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_instances_using_default_service_account,
)
from cartography.rules.data.rules.cis_4_0_gcp import gcp_instances_with_ip_forwarding
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_instances_with_serial_port_access,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_instances_without_confidential_computing_enabled,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_instances_without_shielded_vm_enabled,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_projects_without_effective_os_login,
)
from cartography.rules.data.rules.cis_4_0_gcp import (
    gcp_subnets_without_compliant_vpc_flow_logs,
)
from cartography.rules.data.rules.cis_4_0_gcp import gcp_unrestricted_rdp_access
from cartography.rules.data.rules.cis_4_0_gcp import gcp_unrestricted_ssh_access
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
from cartography.rules.data.rules.cis_google_workspace import (
    googleworkspace_admins_without_enforced_2sv,
)
from cartography.rules.data.rules.cis_google_workspace import (
    googleworkspace_super_admin_accounts_used_for_daily_admin,
)
from cartography.rules.data.rules.cis_google_workspace import (
    googleworkspace_too_few_super_admin_accounts,
)
from cartography.rules.data.rules.cis_google_workspace import (
    googleworkspace_too_many_super_admin_accounts,
)
from cartography.rules.data.rules.cis_google_workspace import (
    googleworkspace_users_without_enforced_2sv,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_bind_impersonate_escalate_permissions,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_cluster_admin_role_usage,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_csr_approval_subresource_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_default_service_account_bindings,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_node_proxy_subresource_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_roles_grant_persistent_volume_creation,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_roles_grant_pod_creation,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_roles_grant_secret_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_service_account_token_creation_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_system_masters_group_usage,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_webhook_configuration_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import kubernetes_wildcard_roles
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_containers_allowing_privilege_escalation,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_containers_using_hostports,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_pods_missing_runtime_default_seccomp,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_pods_running_in_default_namespace,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_pods_sharing_host_ipc_namespace,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_pods_sharing_host_network_namespace,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_pods_sharing_host_pid_namespace,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_pods_using_hostpath_volumes,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_secrets_used_as_environment_variables,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_service_account_tokens_mounted_in_pods,
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
from cartography.rules.data.rules.databricks_security import (
    databricks_ip_access_list_allows_all,
)
from cartography.rules.data.rules.databricks_security import (
    databricks_pat_never_expires,
)
from cartography.rules.data.rules.databricks_security import (
    databricks_public_delta_sharing_recipient,
)
from cartography.rules.data.rules.delegation_boundary_modifiable import (
    delegation_boundary_modifiable,
)
from cartography.rules.data.rules.device_security_posture_gaps import (
    device_security_posture_gaps,
)
from cartography.rules.data.rules.eol_software import eol_software
from cartography.rules.data.rules.guardduty_active_threat import guardduty_active_threat
from cartography.rules.data.rules.iam_role_external_account_trust import (
    iam_role_external_account_trust,
)
from cartography.rules.data.rules.identity_administration_privileges import (
    identity_administration_privileges,
)
from cartography.rules.data.rules.identity_mfa_gaps import identity_mfa_gaps
from cartography.rules.data.rules.inactive_user_active_accounts import (
    inactive_user_active_accounts,
)
from cartography.rules.data.rules.kubernetes_control_plane_exposed import (
    kubernetes_control_plane_exposed,
)
from cartography.rules.data.rules.malicious_npm_dependencies_shai_hulud import (
    malicious_npm_dependencies_shai_hulud,
)
from cartography.rules.data.rules.mfa_missing import missing_mfa_rule
from cartography.rules.data.rules.nist_ai_rmf import ai_admin_app_authorizations
from cartography.rules.data.rules.nist_ai_rmf import ai_provider_api_key_hygiene
from cartography.rules.data.rules.nist_ai_rmf import ai_third_party_app_inventory
from cartography.rules.data.rules.nist_ai_rmf import ai_third_party_app_sensitive_scopes
from cartography.rules.data.rules.nist_ai_rmf import aibom_agent_inventory
from cartography.rules.data.rules.nist_ai_rmf import aibom_coverage_gaps
from cartography.rules.data.rules.object_storage_public import object_storage_public
from cartography.rules.data.rules.policy_administration_privileges import (
    policy_administration_privileges,
)
from cartography.rules.data.rules.public_snapshots import public_snapshots
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
from cartography.rules.data.rules.tailscale_security_configuration_gaps import (
    tailscale_device_auto_updates_disabled,
)
from cartography.rules.data.rules.tailscale_security_configuration_gaps import (
    tailscale_device_key_expiry_disabled,
)
from cartography.rules.data.rules.tailscale_security_configuration_gaps import (
    tailscale_network_flow_logging_disabled,
)
from cartography.rules.data.rules.tailscale_security_configuration_gaps import (
    tailscale_tailnet_approval_disabled,
)
from cartography.rules.data.rules.unmanaged_accounts import unmanaged_accounts
from cartography.rules.data.rules.unpinned_github_actions import unpinned_github_actions
from cartography.rules.data.rules.workload_identity_admin_capabilities import (
    workload_identity_admin_capabilities,
)

# Rule registry - all available rules
RULES = {
    # Databricks Rules
    databricks_pat_never_expires.id: databricks_pat_never_expires,
    databricks_ip_access_list_allows_all.id: databricks_ip_access_list_allows_all,
    databricks_public_delta_sharing_recipient.id: databricks_public_delta_sharing_recipient,
    # CIS AWS IAM Rules (Section 2)
    aws_root_user_access_keys.id: aws_root_user_access_keys,
    aws_root_user_mfa_disabled.id: aws_root_user_mfa_disabled,
    aws_unused_credentials.id: aws_unused_credentials,
    aws_users_with_multiple_active_access_keys.id: aws_users_with_multiple_active_access_keys,
    aws_access_keys_not_rotated.id: aws_access_keys_not_rotated,
    aws_users_with_direct_policy_attachments.id: aws_users_with_direct_policy_attachments,
    aws_policies_with_full_administrative_privileges.id: aws_policies_with_full_administrative_privileges,
    aws_expired_ssl_tls_certificates.id: aws_expired_ssl_tls_certificates,
    # CIS AWS Storage Rules (Section 3)
    aws_s3_bucket_mfa_delete.id: aws_s3_bucket_mfa_delete,
    aws_s3_block_public_access.id: aws_s3_block_public_access,
    aws_rds_encryption_at_rest.id: aws_rds_encryption_at_rest,
    # CIS AWS Logging Rules (Section 4)
    aws_cloudtrail_multi_region.id: aws_cloudtrail_multi_region,
    aws_cloudtrail_log_file_validation.id: aws_cloudtrail_log_file_validation,
    aws_cloudtrail_s3_bucket_access_logging.id: aws_cloudtrail_s3_bucket_access_logging,
    aws_cloudtrail_kms_encryption.id: aws_cloudtrail_kms_encryption,
    # CIS AWS Networking Rules (Section 6)
    aws_ebs_volume_encryption.id: aws_ebs_volume_encryption,
    aws_cifs_access_restricted_to_trusted_networks.id: aws_cifs_access_restricted_to_trusted_networks,
    aws_ipv4_remote_administration_ports_open_to_internet.id: aws_ipv4_remote_administration_ports_open_to_internet,
    aws_ipv6_remote_administration_ports_open_to_internet.id: aws_ipv6_remote_administration_ports_open_to_internet,
    aws_default_security_group_restricts_traffic.id: aws_default_security_group_restricts_traffic,
    aws_ec2_instances_use_imdsv2.id: aws_ec2_instances_use_imdsv2,
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
    device_security_posture_gaps.id: device_security_posture_gaps,
    eol_software.id: eol_software,
    iam_role_external_account_trust.id: iam_role_external_account_trust,
    identity_administration_privileges.id: identity_administration_privileges,
    identity_mfa_gaps.id: identity_mfa_gaps,
    inactive_user_active_accounts.id: inactive_user_active_accounts,
    kubernetes_control_plane_exposed.id: kubernetes_control_plane_exposed,
    missing_mfa_rule.id: missing_mfa_rule,
    object_storage_public.id: object_storage_public,
    policy_administration_privileges.id: policy_administration_privileges,
    public_snapshots.id: public_snapshots,
    tailscale_tailnet_approval_disabled.id: tailscale_tailnet_approval_disabled,
    tailscale_network_flow_logging_disabled.id: tailscale_network_flow_logging_disabled,
    tailscale_device_auto_updates_disabled.id: tailscale_device_auto_updates_disabled,
    tailscale_device_key_expiry_disabled.id: tailscale_device_key_expiry_disabled,
    serverless_workload_exposed.id: serverless_workload_exposed,
    unmanaged_accounts.id: unmanaged_accounts,
    workload_identity_admin_capabilities.id: workload_identity_admin_capabilities,
    cloud_security_product_deactivated.id: cloud_security_product_deactivated,
    guardduty_active_threat.id: guardduty_active_threat,
    malicious_npm_dependencies_shai_hulud.id: malicious_npm_dependencies_shai_hulud,
    unpinned_github_actions.id: unpinned_github_actions,
    # NIST AI RMF Rules
    ai_third_party_app_inventory.id: ai_third_party_app_inventory,
    ai_third_party_app_sensitive_scopes.id: ai_third_party_app_sensitive_scopes,
    ai_admin_app_authorizations.id: ai_admin_app_authorizations,
    aibom_agent_inventory.id: aibom_agent_inventory,
    aibom_coverage_gaps.id: aibom_coverage_gaps,
    ai_provider_api_key_hygiene.id: ai_provider_api_key_hygiene,
    # CIS GCP 4.0 Rules
    gcp_default_network_exists.id: gcp_default_network_exists,
    gcp_cloud_dns_dnssec_disabled.id: gcp_cloud_dns_dnssec_disabled,
    gcp_cloud_dns_dnssec_key_signing_uses_rsasha1.id: gcp_cloud_dns_dnssec_key_signing_uses_rsasha1,
    gcp_cloud_dns_dnssec_zone_signing_uses_rsasha1.id: gcp_cloud_dns_dnssec_zone_signing_uses_rsasha1,
    gcp_subnets_without_compliant_vpc_flow_logs.id: gcp_subnets_without_compliant_vpc_flow_logs,
    gcp_unrestricted_ssh_access.id: gcp_unrestricted_ssh_access,
    gcp_unrestricted_rdp_access.id: gcp_unrestricted_rdp_access,
    gcp_instances_using_default_service_account.id: gcp_instances_using_default_service_account,
    gcp_default_service_account_full_cloud_api_scope.id: gcp_default_service_account_full_cloud_api_scope,
    gcp_instances_not_blocking_project_wide_ssh_keys.id: gcp_instances_not_blocking_project_wide_ssh_keys,
    gcp_projects_without_effective_os_login.id: gcp_projects_without_effective_os_login,
    gcp_instances_with_serial_port_access.id: gcp_instances_with_serial_port_access,
    gcp_instances_with_ip_forwarding.id: gcp_instances_with_ip_forwarding,
    gcp_instances_without_shielded_vm_enabled.id: gcp_instances_without_shielded_vm_enabled,
    gcp_compute_instance_public_ips.id: gcp_compute_instance_public_ips,
    gcp_instances_without_confidential_computing_enabled.id: gcp_instances_without_confidential_computing_enabled,
    gcp_bucket_uniform_access_disabled.id: gcp_bucket_uniform_access_disabled,
    gcp_cloudsql_mysql_skip_show_database_not_on.id: gcp_cloudsql_mysql_skip_show_database_not_on,
    gcp_cloudsql_mysql_local_infile_not_off.id: gcp_cloudsql_mysql_local_infile_not_off,
    gcp_cloudsql_postgres_log_error_verbosity_too_permissive.id: gcp_cloudsql_postgres_log_error_verbosity_too_permissive,
    gcp_cloudsql_postgres_log_connections_not_on.id: gcp_cloudsql_postgres_log_connections_not_on,
    gcp_cloudsql_postgres_log_disconnections_not_on.id: gcp_cloudsql_postgres_log_disconnections_not_on,
    gcp_cloudsql_postgres_log_min_messages_below_warning.id: gcp_cloudsql_postgres_log_min_messages_below_warning,
    gcp_cloudsql_postgres_log_min_error_statement_below_error.id: gcp_cloudsql_postgres_log_min_error_statement_below_error,
    gcp_cloudsql_postgres_log_min_duration_statement_not_disabled.id: gcp_cloudsql_postgres_log_min_duration_statement_not_disabled,
    gcp_cloudsql_postgres_pgaudit_not_enabled.id: gcp_cloudsql_postgres_pgaudit_not_enabled,
    gcp_cloudsql_sqlserver_external_scripts_enabled.id: gcp_cloudsql_sqlserver_external_scripts_enabled,
    gcp_cloudsql_sqlserver_cross_db_ownership_chaining_enabled.id: gcp_cloudsql_sqlserver_cross_db_ownership_chaining_enabled,
    gcp_cloudsql_sqlserver_user_connections_limiting.id: gcp_cloudsql_sqlserver_user_connections_limiting,
    gcp_cloudsql_sqlserver_user_options_configured.id: gcp_cloudsql_sqlserver_user_options_configured,
    gcp_cloudsql_sqlserver_remote_access_not_off.id: gcp_cloudsql_sqlserver_remote_access_not_off,
    gcp_cloudsql_sqlserver_trace_flag_3625_not_on.id: gcp_cloudsql_sqlserver_trace_flag_3625_not_on,
    gcp_cloudsql_sqlserver_contained_database_authentication_enabled.id: gcp_cloudsql_sqlserver_contained_database_authentication_enabled,
    gcp_cloudsql_ssl_not_enforced.id: gcp_cloudsql_ssl_not_enforced,
    gcp_cloudsql_authorized_networks_open_to_internet.id: gcp_cloudsql_authorized_networks_open_to_internet,
    gcp_cloudsql_public_ips.id: gcp_cloudsql_public_ips,
    gcp_cloudsql_automated_backups_disabled.id: gcp_cloudsql_automated_backups_disabled,
    gcp_bigquery_datasets_publicly_accessible.id: gcp_bigquery_datasets_publicly_accessible,
    gcp_bigquery_tables_without_cmek.id: gcp_bigquery_tables_without_cmek,
    gcp_bigquery_datasets_without_default_cmek.id: gcp_bigquery_datasets_without_default_cmek,
    # CIS Google Workspace Rules
    googleworkspace_too_few_super_admin_accounts.id: googleworkspace_too_few_super_admin_accounts,
    googleworkspace_too_many_super_admin_accounts.id: googleworkspace_too_many_super_admin_accounts,
    googleworkspace_super_admin_accounts_used_for_daily_admin.id: googleworkspace_super_admin_accounts_used_for_daily_admin,
    googleworkspace_users_without_enforced_2sv.id: googleworkspace_users_without_enforced_2sv,
    googleworkspace_admins_without_enforced_2sv.id: googleworkspace_admins_without_enforced_2sv,
    # CIS Kubernetes Benchmark v1.12 Rules
    kubernetes_cluster_admin_role_usage.id: kubernetes_cluster_admin_role_usage,
    kubernetes_roles_grant_secret_access.id: kubernetes_roles_grant_secret_access,
    kubernetes_wildcard_roles.id: kubernetes_wildcard_roles,
    kubernetes_roles_grant_pod_creation.id: kubernetes_roles_grant_pod_creation,
    kubernetes_default_service_account_bindings.id: kubernetes_default_service_account_bindings,
    kubernetes_system_masters_group_usage.id: kubernetes_system_masters_group_usage,
    kubernetes_bind_impersonate_escalate_permissions.id: kubernetes_bind_impersonate_escalate_permissions,
    kubernetes_roles_grant_persistent_volume_creation.id: kubernetes_roles_grant_persistent_volume_creation,
    kubernetes_node_proxy_subresource_access.id: kubernetes_node_proxy_subresource_access,
    kubernetes_csr_approval_subresource_access.id: kubernetes_csr_approval_subresource_access,
    kubernetes_webhook_configuration_access.id: kubernetes_webhook_configuration_access,
    kubernetes_service_account_token_creation_access.id: kubernetes_service_account_token_creation_access,
    kubernetes_service_account_tokens_mounted_in_pods.id: kubernetes_service_account_tokens_mounted_in_pods,
    kubernetes_pods_sharing_host_pid_namespace.id: kubernetes_pods_sharing_host_pid_namespace,
    kubernetes_pods_sharing_host_ipc_namespace.id: kubernetes_pods_sharing_host_ipc_namespace,
    kubernetes_pods_sharing_host_network_namespace.id: kubernetes_pods_sharing_host_network_namespace,
    kubernetes_containers_allowing_privilege_escalation.id: kubernetes_containers_allowing_privilege_escalation,
    kubernetes_pods_using_hostpath_volumes.id: kubernetes_pods_using_hostpath_volumes,
    kubernetes_containers_using_hostports.id: kubernetes_containers_using_hostports,
    kubernetes_pods_missing_runtime_default_seccomp.id: kubernetes_pods_missing_runtime_default_seccomp,
    kubernetes_secrets_used_as_environment_variables.id: kubernetes_secrets_used_as_environment_variables,
    kubernetes_pods_running_in_default_namespace.id: kubernetes_pods_running_in_default_namespace,
}
