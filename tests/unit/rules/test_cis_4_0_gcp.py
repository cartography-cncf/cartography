from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.cis_4_0_gcp import GCPCISFinding
from cartography.rules.data.rules.cis_4_0_gcp import (
    cis_gcp_3_1_default_network,
    cis_gcp_3_6_unrestricted_ssh,
    cis_gcp_3_7_unrestricted_rdp,
    cis_gcp_4_9_public_ip,
    cis_gcp_5_2_bucket_uniform_access,
)
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module


def test_cis_rules_registered_and_fact_ids():
    expected_rules = {
        "cis_gcp_3_1_default_network": cis_gcp_3_1_default_network,
        "cis_gcp_3_6_unrestricted_ssh": cis_gcp_3_6_unrestricted_ssh,
        "cis_gcp_3_7_unrestricted_rdp": cis_gcp_3_7_unrestricted_rdp,
        "cis_gcp_4_9_public_ip": cis_gcp_4_9_public_ip,
        "cis_gcp_5_2_bucket_uniform_access": cis_gcp_5_2_bucket_uniform_access,
    }

    for rule_id, rule_obj in expected_rules.items():
        assert rule_id in RULES
        assert RULES[rule_id] is rule_obj
        # Each rule is a single fact for now
        assert len(rule_obj.facts) == 1
        fact = rule_obj.facts[0]
        assert fact.id.startswith(rule_id)


def test_cis_facts_are_gcp_and_experimental():
    for rule in (
        cis_gcp_3_1_default_network,
        cis_gcp_3_6_unrestricted_ssh,
        cis_gcp_3_7_unrestricted_rdp,
        cis_gcp_4_9_public_ip,
        cis_gcp_5_2_bucket_uniform_access,
    ):
        for fact in rule.facts:
            assert fact.module == Module.GCP
            assert fact.maturity == Maturity.EXPERIMENTAL


def test_cis_parse_results_preserves_extra_fields():
    fact = cis_gcp_3_1_default_network.get_fact_by_id("cis_gcp_3_1_default_network")
    sample_results = [
        {
            "control_id": "3.1",
            "control_title": "Ensure That the Default Network Does Not Exist in a Project",
            "profile": "Level 2",
            "severity": "high",
            "resource_id": "projects/demo/global/networks/default",
            "resource_name": "default",
            "resource_type": "VPC Network",
            "project_id": "demo",
            "project_name": "Demo Project",
            "notes": "extra context",
        }
    ]

    findings = cis_gcp_3_1_default_network.parse_results(fact, sample_results)

    assert len(findings) == 1
    finding = findings[0]
    assert isinstance(finding, GCPCISFinding)
    assert finding.control_id == "3.1"
    assert finding.control_title.startswith("Ensure That the Default Network")
    assert finding.resource_name == "default"
    assert finding.extra["notes"] == "extra context"
    assert finding.source == Module.GCP.value
