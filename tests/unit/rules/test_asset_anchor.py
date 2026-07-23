"""
Validation for the affected-node anchor contract.

Every ``Fact`` must expose an indexable ``(asset_label, id)`` anchor on the node
it is about. ``Fact.__post_init__`` already fails construction (so the registry
will not import) when ``asset_label`` is empty, ``asset_id_field`` is unset, or
``asset_id_field`` is not returned by ``cypher_query``. On top of that hard
failure, every fact's ``asset_id_field`` must:
  * be a real field on the owning Rule's output model (the runner reads it via
    ``getattr(finding, asset_id_field)``), and
  * be returned by the fact's ``cypher_query`` (via a ``... AS <name>`` alias).
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
def test_asset_label_non_empty(rule_id, fact_id, rule, fact):
    """Every fact must declare the Neo4j label of the node it is about."""
    assert fact.asset_label, (
        f"Rule '{rule_id}' fact '{fact_id}' has empty asset_label; declare the "
        f"Neo4j node label the finding is about."
    )


@pytest.mark.parametrize("rule_id, fact_id, rule, fact", _ALL_FACTS)
def test_asset_id_field_set(rule_id, fact_id, rule, fact):
    """asset_label needs the id half of the anchor to be resolvable."""
    assert fact.asset_id_field, (
        f"Rule '{rule_id}' fact '{fact_id}' declares asset_label "
        f"'{fact.asset_label}' but no asset_id_field."
    )


@pytest.mark.parametrize("rule_id, fact_id, rule, fact", _ALL_FACTS)
def test_asset_id_field_exists_on_output_model(rule_id, fact_id, rule, fact):
    """asset_id_field must be a real field on the rule's output model.

    The runner reads the anchor id with ``getattr(finding, asset_id_field)``;
    if the field is not declared it lands in ``extra`` and the lookup fails.
    """
    model_fields = set(rule.output_model.model_fields)
    assert fact.asset_id_field in model_fields, (
        f"Rule '{rule_id}' fact '{fact_id}' asset_id_field "
        f"'{fact.asset_id_field}' is not on output model "
        f"'{rule.output_model.__name__}'."
    )


@pytest.mark.parametrize("rule_id, fact_id, rule, fact", _ALL_FACTS)
def test_asset_id_field_returned_by_query(rule_id, fact_id, rule, fact):
    """asset_id_field must be returned (AS <name>) by the fact's cypher_query."""
    aliases = _returned_aliases(fact.cypher_query)
    assert fact.asset_id_field in aliases, (
        f"Rule '{rule_id}' fact '{fact_id}' asset_id_field "
        f"'{fact.asset_id_field}' is not returned by its cypher_query."
    )


def test_asset_anchor_surfaced_in_serialized_output():
    """
    asset_label / asset_id_field must reach the serialized (JSON) output so
    consumers that do not import the Python rule registry can build the
    (label, id) anchor from the emitted findings.
    """
    result = FactResult(
        fact_id="aws_user_direct_policies",
        fact_name="Example",
        fact_description="Example",
        fact_provider="AWS",
        asset_label="AWSUser",
        asset_id_field="user_arn",
    )
    serialized = to_serializable(result)
    assert serialized["asset_label"] == "AWSUser"
    assert serialized["asset_id_field"] == "user_arn"
