from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.eol_software import eol_software
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module


def test_eol_software_rule_registered() -> None:
    assert RULES[eol_software.id] is eol_software


def test_eol_software_rule_shape() -> None:
    assert eol_software.name == "End-of-Life Software"
    assert len(eol_software.facts) == 3
    assert len(eol_software.references) >= 5


def test_eol_software_fact_modules() -> None:
    modules = {fact.module for fact in eol_software.facts}
    assert modules == {Module.AWS, Module.KUBERNETES}


def test_eol_software_facts_are_experimental() -> None:
    assert all(fact.maturity == Maturity.EXPERIMENTAL for fact in eol_software.facts)


def test_kubernetes_fact_dedupes_eks_backed_clusters() -> None:
    kubernetes_fact = next(
        fact
        for fact in eol_software.facts
        if fact.id == "kubernetes_cluster_kubernetes_version_eol"
    )
    assert "e.id = k.external_id" in kubernetes_fact.cypher_query
    assert "e.name = k.external_id" in kubernetes_fact.cypher_query
    assert "e.endpoint = k.api_server_url" in kubernetes_fact.cypher_query
    assert "WHERE NOT EXISTS" in kubernetes_fact.cypher_count_query


def test_eks_fact_uses_provider_support_window() -> None:
    eks_fact = next(
        fact
        for fact in eol_software.facts
        if fact.id == "eks_cluster_kubernetes_version_eol"
    )
    assert "kubernetes_minor < 29" in eks_fact.cypher_query
    assert "'provider' AS support_basis" in eks_fact.cypher_query


def test_kubernetes_fact_uses_upstream_support_window() -> None:
    kubernetes_fact = next(
        fact
        for fact in eol_software.facts
        if fact.id == "kubernetes_cluster_kubernetes_version_eol"
    )
    assert "kubernetes_minor < 33" in kubernetes_fact.cypher_query
    assert "'upstream' AS support_basis" in kubernetes_fact.cypher_query


def test_ec2_fact_uses_ssm_and_vendor_eol_date() -> None:
    ec2_fact = next(
        fact
        for fact in eol_software.facts
        if fact.id == "ec2_instance_amazon_linux_2_eol"
    )
    assert (
        "MATCH (ec2:EC2Instance)-[:HAS_INFORMATION]->(ssm:SSMInstanceInformation)"
        in ec2_fact.cypher_query
    )
    assert "ssm.platform_name" in ec2_fact.cypher_query
    assert "ssm.platform_version" in ec2_fact.cypher_query
    assert "date() > date('2026-06-30')" in ec2_fact.cypher_query
    assert "'vendor' AS support_basis" in ec2_fact.cypher_query
