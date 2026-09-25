from cartography.analysis.kubernetes.analysis import K8S_SERVICE_ASSET_EXPOSURE
from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.kubernetes_service_exposed import (
    kubernetes_service_exposed,
)
from cartography.rules.data.rules.kubernetes_service_exposed import (
    KubernetesServiceExposed,
)
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module


def test_kubernetes_service_exposed_rule_registered() -> None:
    assert RULES[kubernetes_service_exposed.id] is kubernetes_service_exposed


def test_kubernetes_service_exposed_rule_shape() -> None:
    assert kubernetes_service_exposed.id == "kubernetes_service_exposed"
    assert kubernetes_service_exposed.output_model is KubernetesServiceExposed
    assert len(kubernetes_service_exposed.facts) == 2


def test_kubernetes_service_exposed_facts_are_kubernetes_module() -> None:
    modules = {fact.module for fact in kubernetes_service_exposed.facts}
    assert modules == {Module.KUBERNETES}


def test_kubernetes_service_exposed_facts_are_experimental() -> None:
    assert all(
        fact.maturity == Maturity.EXPERIMENTAL
        for fact in kubernetes_service_exposed.facts
    )


def test_kubernetes_service_exposed_fact_ids_are_unique() -> None:
    fact_ids = [fact.id for fact in kubernetes_service_exposed.facts]
    assert len(fact_ids) == len(set(fact_ids))


def test_kubernetes_service_exposed_facts_anchor_on_the_service() -> None:
    """Both entry paths must report the backend service, not the load balancer."""
    for fact in kubernetes_service_exposed.facts:
        assert fact.asset_label == "KubernetesService"
        assert fact.asset_id_field == "id"
        assert fact.identity_fields == ("id",)


def test_kubernetes_service_exposed_covers_both_entry_paths() -> None:
    """One fact per route into the cluster: a direct load balancer and an ingress."""
    exposure_types = {
        "direct_load_balancer": "USES_LOAD_BALANCER",
        "ingress_load_balancer": "KubernetesIngress",
    }

    for fact in kubernetes_service_exposed.facts:
        matched = [
            evidence
            for exposure_type, evidence in exposure_types.items()
            if f"'{exposure_type}' AS exposure_type" in fact.cypher_query
        ]
        assert len(matched) == 1, fact.id
        assert matched[0] in fact.cypher_query


def _collapse_whitespace(query: str) -> str:
    return " ".join(query.split())


def test_kubernetes_service_exposed_facts_agree_with_the_analysis_job() -> None:
    """
    Every query must use the same internet-facing test as the analysis job.

    The facts re-derive KubernetesService.exposed_internet rather than reading it,
    so a predicate that drifts from K8S_SERVICE_ASSET_EXPOSURE would make the rule
    and the flag disagree about the same service.
    """
    predicate = (
        "lb.exposed_internet = true "
        "OR (lb.scheme = 'internet-facing' AND lb.type = 'network')"
    )

    # The job is the source of this predicate: assert it still says what the facts
    # copied, so a change there fails here rather than silently splitting the two.
    assert all(
        predicate in _collapse_whitespace(statement.match or "")
        for statement in K8S_SERVICE_ASSET_EXPOSURE.statements
    )

    for fact in kubernetes_service_exposed.facts:
        assert predicate in _collapse_whitespace(fact.cypher_query), fact.id
        assert predicate in _collapse_whitespace(fact.cypher_visual_query), fact.id
