"""
Validation for the stable finding-identity contract.

``Fact.identity_fields`` is required (no default), and ``Fact.__post_init__``
fails construction (so the rule registry will not import) when it is empty or
when the Fact's ``cypher_query`` does not return each field (via a
``... AS <name>`` alias); the negative tests in ``test_model.py`` cover that
construction-time validation. What it cannot check is the owning Rule's output
model, so this module adds that every declared identity field exists on it.
"""

import pytest

from cartography.rules.data.rules import RULES
from cartography.rules.formatters import to_serializable
from cartography.rules.spec.result import FactResult

# (rule_id, fact_id, rule, fact) for every fact in the registry.
_ALL_FACTS = [
    pytest.param(rule.id, fact.id, rule, fact, id=f"{rule.id}::{fact.id}")
    for rule in RULES.values()
    for fact in rule.facts
]


@pytest.mark.parametrize("rule_id, fact_id, rule, fact", _ALL_FACTS)
def test_identity_fields_exist_on_output_model(rule_id, fact_id, rule, fact):
    """identity_fields must be real fields on the rule's output model."""
    model_fields = set(rule.output_model.model_fields)
    for field in fact.identity_fields:
        assert field in model_fields, (
            f"Rule '{rule_id}' fact '{fact_id}' lists identity field "
            f"'{field}' that is not on output model "
            f"'{rule.output_model.__name__}'."
        )


def test_identity_fields_surfaced_in_serialized_output():
    """
    identity_fields must reach the serialized (JSON) output so consumers that
    do not import the Python rule registry can read the identity contract.
    """
    result = FactResult(
        fact_id="aws_user_direct_policies",
        fact_name="Example",
        fact_description="Example",
        fact_provider="AWS",
        identity_fields=("user_arn", "policy_arn"),
    )
    serialized = to_serializable(result)
    assert serialized["identity_fields"] == ["user_arn", "policy_arn"]
