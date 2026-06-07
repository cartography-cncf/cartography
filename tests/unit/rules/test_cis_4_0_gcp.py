from cartography.rules.data.rules import RULES
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
from cartography.rules.data.rules.cis_4_0_gcp import DefaultNetworkExistsOutput
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module


def test_cis_rules_registered_and_fact_ids():
    expected_rules = {
        "cis_gcp_3_1_default_network": cis_gcp_3_1_default_network,
        "cis_gcp_3_3_dnssec_enabled": cis_gcp_3_3_dnssec_enabled,
        "cis_gcp_3_4_dnssec_no_rsasha1_ksk": cis_gcp_3_4_dnssec_no_rsasha1_ksk,
        "cis_gcp_3_5_dnssec_no_rsasha1_zsk": cis_gcp_3_5_dnssec_no_rsasha1_zsk,
        "cis_gcp_3_8_vpc_flow_logs": cis_gcp_3_8_vpc_flow_logs,
        "cis_gcp_3_6_unrestricted_ssh": cis_gcp_3_6_unrestricted_ssh,
        "cis_gcp_3_7_unrestricted_rdp": cis_gcp_3_7_unrestricted_rdp,
        "cis_gcp_4_1_default_service_account": cis_gcp_4_1_default_service_account,
        "cis_gcp_4_2_default_service_account_full_api": cis_gcp_4_2_default_service_account_full_api,
        "cis_gcp_4_3_block_project_wide_ssh_keys": cis_gcp_4_3_block_project_wide_ssh_keys,
        "cis_gcp_4_4_oslogin_enabled": cis_gcp_4_4_oslogin_enabled,
        "cis_gcp_4_5_serial_ports_disabled": cis_gcp_4_5_serial_ports_disabled,
        "cis_gcp_4_6_ip_forwarding": cis_gcp_4_6_ip_forwarding,
        "cis_gcp_4_8_shielded_vm": cis_gcp_4_8_shielded_vm,
        "cis_gcp_4_9_public_ip": cis_gcp_4_9_public_ip,
        "cis_gcp_4_11_confidential_compute": cis_gcp_4_11_confidential_compute,
        "cis_gcp_5_2_bucket_uniform_access": cis_gcp_5_2_bucket_uniform_access,
        "cis_gcp_6_1_2_cloudsql_mysql_skip_show_database": cis_gcp_6_1_2_cloudsql_mysql_skip_show_database,
        "cis_gcp_6_1_3_cloudsql_mysql_local_infile": cis_gcp_6_1_3_cloudsql_mysql_local_infile,
        "cis_gcp_6_2_1_cloudsql_postgres_log_error_verbosity": cis_gcp_6_2_1_cloudsql_postgres_log_error_verbosity,
        "cis_gcp_6_2_2_cloudsql_postgres_log_connections": cis_gcp_6_2_2_cloudsql_postgres_log_connections,
        "cis_gcp_6_2_3_cloudsql_postgres_log_disconnections": cis_gcp_6_2_3_cloudsql_postgres_log_disconnections,
        "cis_gcp_6_2_5_cloudsql_postgres_log_min_messages": cis_gcp_6_2_5_cloudsql_postgres_log_min_messages,
        "cis_gcp_6_2_6_cloudsql_postgres_log_min_error_statement": cis_gcp_6_2_6_cloudsql_postgres_log_min_error_statement,
        "cis_gcp_6_2_7_cloudsql_postgres_log_min_duration_statement": cis_gcp_6_2_7_cloudsql_postgres_log_min_duration_statement,
        "cis_gcp_6_2_8_cloudsql_postgres_enable_pgaudit": cis_gcp_6_2_8_cloudsql_postgres_enable_pgaudit,
        "cis_gcp_6_3_1_cloudsql_sqlserver_external_scripts": cis_gcp_6_3_1_cloudsql_sqlserver_external_scripts,
        "cis_gcp_6_3_2_cloudsql_sqlserver_cross_db_ownership": cis_gcp_6_3_2_cloudsql_sqlserver_cross_db_ownership,
        "cis_gcp_6_3_3_cloudsql_sqlserver_user_connections": cis_gcp_6_3_3_cloudsql_sqlserver_user_connections,
        "cis_gcp_6_3_4_cloudsql_sqlserver_user_options": cis_gcp_6_3_4_cloudsql_sqlserver_user_options,
        "cis_gcp_6_3_5_cloudsql_sqlserver_remote_access": cis_gcp_6_3_5_cloudsql_sqlserver_remote_access,
        "cis_gcp_6_3_6_cloudsql_sqlserver_trace_3625": cis_gcp_6_3_6_cloudsql_sqlserver_trace_3625,
        "cis_gcp_6_3_7_cloudsql_sqlserver_contained_auth": cis_gcp_6_3_7_cloudsql_sqlserver_contained_auth,
        "cis_gcp_6_4_cloudsql_ssl_required": cis_gcp_6_4_cloudsql_ssl_required,
        "cis_gcp_6_5_cloudsql_authorized_networks": cis_gcp_6_5_cloudsql_authorized_networks,
        "cis_gcp_6_6_cloudsql_public_ip": cis_gcp_6_6_cloudsql_public_ip,
        "cis_gcp_6_7_cloudsql_backups": cis_gcp_6_7_cloudsql_backups,
        "cis_gcp_7_1_bigquery_dataset_public": cis_gcp_7_1_bigquery_dataset_public,
        "cis_gcp_7_2_bigquery_table_cmek": cis_gcp_7_2_bigquery_table_cmek,
        "cis_gcp_7_3_bigquery_dataset_cmek": cis_gcp_7_3_bigquery_dataset_cmek,
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
        cis_gcp_3_1_default_network,
        cis_gcp_3_3_dnssec_enabled,
        cis_gcp_3_4_dnssec_no_rsasha1_ksk,
        cis_gcp_3_5_dnssec_no_rsasha1_zsk,
        cis_gcp_3_8_vpc_flow_logs,
        cis_gcp_3_6_unrestricted_ssh,
        cis_gcp_3_7_unrestricted_rdp,
        cis_gcp_4_1_default_service_account,
        cis_gcp_4_2_default_service_account_full_api,
        cis_gcp_4_3_block_project_wide_ssh_keys,
        cis_gcp_4_4_oslogin_enabled,
        cis_gcp_4_5_serial_ports_disabled,
        cis_gcp_4_6_ip_forwarding,
        cis_gcp_4_8_shielded_vm,
        cis_gcp_4_9_public_ip,
        cis_gcp_4_11_confidential_compute,
        cis_gcp_5_2_bucket_uniform_access,
        cis_gcp_6_1_2_cloudsql_mysql_skip_show_database,
        cis_gcp_6_1_3_cloudsql_mysql_local_infile,
        cis_gcp_6_2_1_cloudsql_postgres_log_error_verbosity,
        cis_gcp_6_2_2_cloudsql_postgres_log_connections,
        cis_gcp_6_2_3_cloudsql_postgres_log_disconnections,
        cis_gcp_6_2_5_cloudsql_postgres_log_min_messages,
        cis_gcp_6_2_6_cloudsql_postgres_log_min_error_statement,
        cis_gcp_6_2_7_cloudsql_postgres_log_min_duration_statement,
        cis_gcp_6_2_8_cloudsql_postgres_enable_pgaudit,
        cis_gcp_6_3_1_cloudsql_sqlserver_external_scripts,
        cis_gcp_6_3_2_cloudsql_sqlserver_cross_db_ownership,
        cis_gcp_6_3_3_cloudsql_sqlserver_user_connections,
        cis_gcp_6_3_4_cloudsql_sqlserver_user_options,
        cis_gcp_6_3_5_cloudsql_sqlserver_remote_access,
        cis_gcp_6_3_6_cloudsql_sqlserver_trace_3625,
        cis_gcp_6_3_7_cloudsql_sqlserver_contained_auth,
        cis_gcp_6_4_cloudsql_ssl_required,
        cis_gcp_6_5_cloudsql_authorized_networks,
        cis_gcp_6_6_cloudsql_public_ip,
        cis_gcp_6_7_cloudsql_backups,
        cis_gcp_7_1_bigquery_dataset_public,
        cis_gcp_7_2_bigquery_table_cmek,
        cis_gcp_7_3_bigquery_dataset_cmek,
    ):
        for fact in rule.facts:
            assert fact.module == Module.GCP
            assert fact.maturity == Maturity.STABLE


def test_cis_parse_results_preserves_extra_fields():
    fact = cis_gcp_3_1_default_network.get_fact_by_id("gcp_default_network_exists")
    sample_results = [
        {
            "vpc_id": "projects/demo/global/networks/default",
            "vpc_name": "default",
            "project_id": "demo",
            "project_name": "Demo Project",
            "notes": "extra context",
        }
    ]

    findings = cis_gcp_3_1_default_network.parse_results(fact, sample_results)

    assert len(findings) == 1
    finding = findings[0]
    assert isinstance(finding, DefaultNetworkExistsOutput)
    assert finding.vpc_name == "default"
    assert finding.vpc_id == "projects/demo/global/networks/default"
    assert finding.project_id == "demo"
    assert finding.extra["notes"] == "extra context"
    assert finding.source == Module.GCP.value
