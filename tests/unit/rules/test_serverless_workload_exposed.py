from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.serverless_workload_exposed import (
    serverless_workload_exposed,
)
from cartography.rules.data.rules.serverless_workload_exposed import (
    ServerlessWorkloadExposed,
)
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module


def test_serverless_workload_exposed_rule_registered() -> None:
    assert RULES[serverless_workload_exposed.id] is serverless_workload_exposed


def test_serverless_workload_exposed_rule_shape() -> None:
    assert serverless_workload_exposed.id == "serverless_workload_exposed"
    assert serverless_workload_exposed.output_model is ServerlessWorkloadExposed
    assert len(serverless_workload_exposed.facts) == 3


def test_serverless_workload_exposed_fact_modules() -> None:
    modules = {fact.module for fact in serverless_workload_exposed.facts}
    assert modules == {Module.AWS, Module.GCP}


def test_serverless_workload_exposed_facts_are_experimental() -> None:
    assert all(
        fact.maturity == Maturity.EXPERIMENTAL
        for fact in serverless_workload_exposed.facts
    )


def test_serverless_workload_exposed_fact_ids_are_unique() -> None:
    fact_ids = [fact.id for fact in serverless_workload_exposed.facts]
    assert len(fact_ids) == len(set(fact_ids))
