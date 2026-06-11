"""
Validation for the stable finding-identity contract.

``Fact.identity_fields`` is required (no default), so a Fact that omits it fails
to construct and the rule registry will not import. On top of that hard failure,
every declared identity field must:
  * be non-empty,
  * exist on the owning Rule's output model, and
  * be returned by the Fact's ``cypher_query`` (via a ``... AS <name>`` alias).
"""

import re

import pytest

from cartography.rules.data.rules import RULES
from cartography.rules.formatters import to_serializable
from cartography.rules.spec.result import FactResult

# Matches the `RETURN expr AS alias` convention every fact query uses.
_RETURN_ALIAS_RE = re.compile(r"\bAS\s+(\w+)", re.IGNORECASE)


def _returned_aliases(cypher_query: str) -> set[str]:
    return set(_RETURN_ALIAS_RE.findall(cypher_query))


# (rule_id, fact_id, rule, fact) for every fact in the registry.
_ALL_FACTS = [
    pytest.param(rule.id, fact.id, rule, fact, id=f"{rule.id}::{fact.id}")
    for rule in RULES.values()
    for fact in rule.facts
]


@pytest.mark.parametrize("rule_id, fact_id, rule, fact", _ALL_FACTS)
def test_identity_fields_non_empty(rule_id, fact_id, rule, fact):
    """Every fact must declare at least one identity field."""
    assert fact.identity_fields, (
        f"Rule '{rule_id}' fact '{fact_id}' has empty identity_fields; "
        f"declare the field(s) forming the finding's stable logical identity."
    )


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


@pytest.mark.parametrize("rule_id, fact_id, rule, fact", _ALL_FACTS)
def test_identity_fields_returned_by_query(rule_id, fact_id, rule, fact):
    """identity_fields must be returned (AS <name>) by the fact's cypher_query."""
    aliases = _returned_aliases(fact.cypher_query)
    for field in fact.identity_fields:
        assert field in aliases, (
            f"Rule '{rule_id}' fact '{fact_id}' lists identity field "
            f"'{field}' that is not returned by its cypher_query."
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
