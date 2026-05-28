from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.kubernetes_control_plane_exposed import (
    kubernetes_control_plane_exposed,
)
from cartography.rules.data.rules.kubernetes_control_plane_exposed import (
    KubernetesControlPlaneExposed,
)
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module


def test_kubernetes_control_plane_exposed_rule_registered() -> None:
    assert (
        RULES[kubernetes_control_plane_exposed.id] is kubernetes_control_plane_exposed
    )


def test_kubernetes_control_plane_exposed_rule_shape() -> None:
    assert kubernetes_control_plane_exposed.id == "kubernetes_control_plane_exposed"
    assert (
        kubernetes_control_plane_exposed.output_model is KubernetesControlPlaneExposed
    )
    assert len(kubernetes_control_plane_exposed.facts) == 3


def test_kubernetes_control_plane_exposed_fact_modules() -> None:
    modules = {fact.module for fact in kubernetes_control_plane_exposed.facts}
    assert modules == {Module.AWS, Module.AZURE, Module.GCP}


def test_kubernetes_control_plane_exposed_facts_are_experimental() -> None:
    assert all(
        fact.maturity == Maturity.EXPERIMENTAL
        for fact in kubernetes_control_plane_exposed.facts
    )


def test_kubernetes_control_plane_exposed_fact_ids_are_unique() -> None:
    fact_ids = [fact.id for fact in kubernetes_control_plane_exposed.facts]
    assert len(fact_ids) == len(set(fact_ids))
