from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.eol_software import eol_software
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module


def test_eol_software_rule_registered() -> None:
    assert RULES[eol_software.id] is eol_software


def test_eol_software_rule_shape() -> None:
    assert eol_software.name == "End-of-Life Software"
    assert len(eol_software.facts) == 5
    assert len(eol_software.references) >= 5


def test_eol_software_fact_modules() -> None:
    modules = {fact.module for fact in eol_software.facts}
    assert modules == {Module.AWS, Module.AZURE, Module.GCP, Module.KUBERNETES}


def test_eol_software_facts_are_experimental() -> None:
    assert all(fact.maturity == Maturity.EXPERIMENTAL for fact in eol_software.facts)


def test_eks_fact_flags_kubernetes_1_29() -> None:
    """
    EKS no longer supports 1.29 (extended support covers 1.30 / 1.31 / 1.32).
    The fact's threshold must be at least 30 so 1.29 clusters are flagged.
    """
    fact = next(
        f for f in eol_software.facts if f.id == "eks_cluster_kubernetes_version_eol"
    )
    # The cypher hard-codes the threshold via the constant interpolation;
    # asserting the literal `< 30` keeps us aligned with the AWS EKS docs.
    assert "kubernetes_minor < 30" in fact.cypher_query


def test_aks_fact_flags_kubernetes_1_32_standard_support() -> None:
    """
    Microsoft's AKS standard-support window starts at 1.33 as of 2026-05;
    1.32 reached community EOL in March 2026. The fact's threshold must
    be at least 33 so 1.30 / 1.31 / 1.32 are surfaced.
    """
    fact = next(
        f for f in eol_software.facts if f.id == "aks_cluster_kubernetes_version_eol"
    )
    assert "kubernetes_minor < 33" in fact.cypher_query
