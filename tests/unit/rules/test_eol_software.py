from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.eol_software import eol_software
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module


def test_eol_software_rule_registered() -> None:
    assert RULES[eol_software.id] is eol_software


def test_eol_software_rule_shape() -> None:
    assert eol_software.name == "End-of-Life Software"
    assert len(eol_software.facts) == 2
    assert len(eol_software.references) >= 2


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
