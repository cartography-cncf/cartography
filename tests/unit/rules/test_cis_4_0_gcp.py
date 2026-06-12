from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.cis_4_0_gcp import DefaultNetworkExistsOutput
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
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module


def test_cis_rules_registered_and_fact_ids():
    expected_rules = {
        "gcp_default_network_exists": gcp_default_network_exists,
        "gcp_cloud_dns_dnssec_disabled": gcp_cloud_dns_dnssec_disabled,
        "gcp_cloud_dns_dnssec_key_signing_uses_rsasha1": gcp_cloud_dns_dnssec_key_signing_uses_rsasha1,
        "gcp_cloud_dns_dnssec_zone_signing_uses_rsasha1": gcp_cloud_dns_dnssec_zone_signing_uses_rsasha1,
        "gcp_subnets_without_compliant_vpc_flow_logs": gcp_subnets_without_compliant_vpc_flow_logs,
        "gcp_unrestricted_ssh_access": gcp_unrestricted_ssh_access,
        "gcp_unrestricted_rdp_access": gcp_unrestricted_rdp_access,
        "gcp_instances_using_default_service_account": gcp_instances_using_default_service_account,
        "gcp_default_service_account_full_cloud_api_scope": gcp_default_service_account_full_cloud_api_scope,
        "gcp_instances_not_blocking_project_wide_ssh_keys": gcp_instances_not_blocking_project_wide_ssh_keys,
        "gcp_projects_without_effective_os_login": gcp_projects_without_effective_os_login,
        "gcp_instances_with_serial_port_access": gcp_instances_with_serial_port_access,
        "gcp_instances_with_ip_forwarding": gcp_instances_with_ip_forwarding,
        "gcp_instances_without_shielded_vm_enabled": gcp_instances_without_shielded_vm_enabled,
        "gcp_compute_instance_public_ips": gcp_compute_instance_public_ips,
        "gcp_instances_without_confidential_computing_enabled": gcp_instances_without_confidential_computing_enabled,
        "gcp_bucket_uniform_access_disabled": gcp_bucket_uniform_access_disabled,
        "gcp_cloudsql_mysql_skip_show_database_not_on": gcp_cloudsql_mysql_skip_show_database_not_on,
        "gcp_cloudsql_mysql_local_infile_not_off": gcp_cloudsql_mysql_local_infile_not_off,
        "gcp_cloudsql_postgres_log_error_verbosity_too_permissive": gcp_cloudsql_postgres_log_error_verbosity_too_permissive,
        "gcp_cloudsql_postgres_log_connections_not_on": gcp_cloudsql_postgres_log_connections_not_on,
        "gcp_cloudsql_postgres_log_disconnections_not_on": gcp_cloudsql_postgres_log_disconnections_not_on,
        "gcp_cloudsql_postgres_log_min_messages_below_warning": gcp_cloudsql_postgres_log_min_messages_below_warning,
        "gcp_cloudsql_postgres_log_min_error_statement_below_error": gcp_cloudsql_postgres_log_min_error_statement_below_error,
        "gcp_cloudsql_postgres_log_min_duration_statement_not_disabled": gcp_cloudsql_postgres_log_min_duration_statement_not_disabled,
        "gcp_cloudsql_postgres_pgaudit_not_enabled": gcp_cloudsql_postgres_pgaudit_not_enabled,
        "gcp_cloudsql_sqlserver_external_scripts_enabled": gcp_cloudsql_sqlserver_external_scripts_enabled,
        "gcp_cloudsql_sqlserver_cross_db_ownership_chaining_enabled": gcp_cloudsql_sqlserver_cross_db_ownership_chaining_enabled,
        "gcp_cloudsql_sqlserver_user_connections_limiting": gcp_cloudsql_sqlserver_user_connections_limiting,
        "gcp_cloudsql_sqlserver_user_options_configured": gcp_cloudsql_sqlserver_user_options_configured,
        "gcp_cloudsql_sqlserver_remote_access_not_off": gcp_cloudsql_sqlserver_remote_access_not_off,
        "gcp_cloudsql_sqlserver_trace_flag_3625_not_on": gcp_cloudsql_sqlserver_trace_flag_3625_not_on,
        "gcp_cloudsql_sqlserver_contained_database_authentication_enabled": gcp_cloudsql_sqlserver_contained_database_authentication_enabled,
        "gcp_cloudsql_ssl_not_enforced": gcp_cloudsql_ssl_not_enforced,
        "gcp_cloudsql_authorized_networks_open_to_internet": gcp_cloudsql_authorized_networks_open_to_internet,
        "gcp_cloudsql_public_ips": gcp_cloudsql_public_ips,
        "gcp_cloudsql_automated_backups_disabled": gcp_cloudsql_automated_backups_disabled,
        "gcp_bigquery_datasets_publicly_accessible": gcp_bigquery_datasets_publicly_accessible,
        "gcp_bigquery_tables_without_cmek": gcp_bigquery_tables_without_cmek,
        "gcp_bigquery_datasets_without_default_cmek": gcp_bigquery_datasets_without_default_cmek,
    }

    for rule_id, rule_obj in expected_rules.items():
        assert rule_id in RULES
        assert RULES[rule_id] is rule_obj
        # Each rule has a single fact
        assert len(rule_obj.facts) == 1
        fact = rule_obj.facts[0]
        # Fact IDs now use gcp_ prefix (not cis_gcp_)
        assert fact.id.startswith("gcp_")


def test_cis_facts_are_gcp_and_stable():
    for rule in (
        gcp_default_network_exists,
        gcp_cloud_dns_dnssec_disabled,
        gcp_cloud_dns_dnssec_key_signing_uses_rsasha1,
        gcp_cloud_dns_dnssec_zone_signing_uses_rsasha1,
        gcp_subnets_without_compliant_vpc_flow_logs,
        gcp_unrestricted_ssh_access,
        gcp_unrestricted_rdp_access,
        gcp_instances_using_default_service_account,
        gcp_default_service_account_full_cloud_api_scope,
        gcp_instances_not_blocking_project_wide_ssh_keys,
        gcp_projects_without_effective_os_login,
        gcp_instances_with_serial_port_access,
        gcp_instances_with_ip_forwarding,
        gcp_instances_without_shielded_vm_enabled,
        gcp_compute_instance_public_ips,
        gcp_instances_without_confidential_computing_enabled,
        gcp_bucket_uniform_access_disabled,
        gcp_cloudsql_mysql_skip_show_database_not_on,
        gcp_cloudsql_mysql_local_infile_not_off,
        gcp_cloudsql_postgres_log_error_verbosity_too_permissive,
        gcp_cloudsql_postgres_log_connections_not_on,
        gcp_cloudsql_postgres_log_disconnections_not_on,
        gcp_cloudsql_postgres_log_min_messages_below_warning,
        gcp_cloudsql_postgres_log_min_error_statement_below_error,
        gcp_cloudsql_postgres_log_min_duration_statement_not_disabled,
        gcp_cloudsql_postgres_pgaudit_not_enabled,
        gcp_cloudsql_sqlserver_external_scripts_enabled,
        gcp_cloudsql_sqlserver_cross_db_ownership_chaining_enabled,
        gcp_cloudsql_sqlserver_user_connections_limiting,
        gcp_cloudsql_sqlserver_user_options_configured,
        gcp_cloudsql_sqlserver_remote_access_not_off,
        gcp_cloudsql_sqlserver_trace_flag_3625_not_on,
        gcp_cloudsql_sqlserver_contained_database_authentication_enabled,
        gcp_cloudsql_ssl_not_enforced,
        gcp_cloudsql_authorized_networks_open_to_internet,
        gcp_cloudsql_public_ips,
        gcp_cloudsql_automated_backups_disabled,
        gcp_bigquery_datasets_publicly_accessible,
        gcp_bigquery_tables_without_cmek,
        gcp_bigquery_datasets_without_default_cmek,
    ):
        for fact in rule.facts:
            assert fact.module == Module.GCP
            assert fact.maturity == Maturity.STABLE


def test_cis_parse_results_preserves_extra_fields():
    fact = gcp_default_network_exists.get_fact_by_id("gcp_default_network_exists")
    sample_results = [
        {
            "vpc_id": "projects/demo/global/networks/default",
            "vpc_name": "default",
            "project_id": "demo",
            "project_name": "Demo Project",
            "notes": "extra context",
        }
    ]

    findings = gcp_default_network_exists.parse_results(fact, sample_results)

    assert len(findings) == 1
    finding = findings[0]
    assert isinstance(finding, DefaultNetworkExistsOutput)
    assert finding.vpc_name == "default"
    assert finding.vpc_id == "projects/demo/global/networks/default"
    assert finding.project_id == "demo"
    assert finding.extra["notes"] == "extra context"
    assert finding.source == Module.GCP.value
