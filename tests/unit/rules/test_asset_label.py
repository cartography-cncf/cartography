"""
Validation for the ``Fact.asset_label`` half of the affected-node anchor.

``Fact.__post_init__`` already fails construction (so the registry will not
import) when ``asset_label`` is empty or when the fact's ``cypher_query`` never
matches the declared label. What it cannot check without importing
``cartography.models`` is whether the label is one the data model actually
writes, which is what this module adds: a fact anchored on a label no schema
produces can never be resolved by a consumer.
"""

import pytest

from cartography.rules.data.rules import RULES
from tests.utils import all_graph_labels

# Labels written by legacy handwritten Cypher rather than by a node schema, so
# `all_graph_labels()` cannot see them. Keep this list short: the fix for a new
# entry is normally to model the node, not to extend the allowlist.
_UNMODELED_LABELS: set[str] = set()

# Walking every model module is not cheap, so do it once for the whole module
# rather than per parametrized case.
_KNOWN_LABELS = all_graph_labels() | _UNMODELED_LABELS

# (rule_id, fact_id, fact) for every fact in the registry.
_ALL_FACTS = [
    pytest.param(rule.id, fact.id, fact, id=f"{rule.id}::{fact.id}")
    for rule in RULES.values()
    for fact in rule.facts
]


@pytest.mark.parametrize("rule_id, fact_id, fact", _ALL_FACTS)
def test_asset_label_is_written_by_the_data_model(rule_id, fact_id, fact):
    """asset_label must be a label some node schema writes.

    Consumers resolve the affected node with `MATCH (n:<asset_label> {id: ...})`,
    so a label that no schema ever sets makes the anchor permanently unresolvable.
    """
    assert fact.asset_label in _KNOWN_LABELS, (
        f"Rule '{rule_id}' fact '{fact_id}' declares asset_label "
        f"'{fact.asset_label}', which no CartographyNodeSchema writes as a "
        f"primary or extra label."
    )


@pytest.mark.parametrize("rule_id, fact_id, fact", _ALL_FACTS)
def test_asset_label_matched_by_query(rule_id, fact_id, fact):
    """The query must match the label the fact claims.

    Enforced at construction time too; kept here so the contract is visible
    alongside the other anchor tests and reported per fact.
    """
    assert f":{fact.asset_label}" in fact.cypher_query.replace(": ", ":"), (
        f"Rule '{rule_id}' fact '{fact_id}' declares asset_label "
        f"'{fact.asset_label}' but its cypher_query never matches that label."
    )
