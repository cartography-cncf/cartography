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
