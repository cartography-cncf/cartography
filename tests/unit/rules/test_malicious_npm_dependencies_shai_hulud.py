import re

from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.malicious_npm_dependencies_shai_hulud import (
    malicious_npm_dependencies_shai_hulud,
)
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module

_AUG_2026_FACT_ID = "malicious-npm-dependencies-shai-hulud-aug-2026-github"
_AUG_2026_AT_RISK_FACT_ID = (
    "malicious-npm-dependencies-shai-hulud-aug-2026-at-risk-github"
)

# The ChainDrop entry points, the three highest-reach packages in the wave.
# flat-cache and file-entry-cache reach most repos transitively under ESLint.
_CHAINDROP_ENTRY_POINTS = (
    ("keyv", "6.0.0"),
    ("flat-cache", "6.1.24"),
    ("file-entry-cache", "11.1.6"),
)


def _fact(fact_id: str):
    return next(
        f for f in malicious_npm_dependencies_shai_hulud.facts if f.id == fact_id
    )


def _package_names(cypher: str) -> set[str]:
    return set(re.findall(r"name:\s*'([^']+)'", cypher))


def test_rule_registered() -> None:
    assert (
        RULES[malicious_npm_dependencies_shai_hulud.id]
        is malicious_npm_dependencies_shai_hulud
    )


def test_rule_shape() -> None:
    assert len(malicious_npm_dependencies_shai_hulud.facts) == 5
    assert malicious_npm_dependencies_shai_hulud.version == "0.3.0"
    assert len(malicious_npm_dependencies_shai_hulud.references) >= 10


def test_all_facts_are_github_and_experimental() -> None:
    for fact in malicious_npm_dependencies_shai_hulud.facts:
        assert fact.module == Module.GITHUB
        assert fact.maturity == Maturity.EXPERIMENTAL


def test_fact_ids_are_unique() -> None:
    fact_ids = [f.id for f in malicious_npm_dependencies_shai_hulud.facts]
    assert len(fact_ids) == len(set(fact_ids))


def test_aug_2026_wave_facts_registered() -> None:
    fact_ids = {f.id for f in malicious_npm_dependencies_shai_hulud.facts}
    assert _AUG_2026_FACT_ID in fact_ids
    assert _AUG_2026_AT_RISK_FACT_ID in fact_ids


def test_aug_2026_fact_covers_chaindrop_entry_points() -> None:
    fact = _fact(_AUG_2026_FACT_ID)
    for name, version in _CHAINDROP_ENTRY_POINTS:
        entry = f"{{ name: '{name}', version: '{version}' }}"
        assert entry in fact.cypher_query
        assert entry in fact.cypher_visual_query


def test_aug_2026_fact_covers_keyv_scoped_family() -> None:
    """The worm republished the whole @keyv/* scope at 6.0.0, not just `keyv`."""
    names = _package_names(_fact(_AUG_2026_FACT_ID).cypher_query)
    scoped = {name for name in names if name.startswith("@keyv/")}
    assert len(scoped) >= 14


def test_aug_2026_facts_cover_the_same_packages() -> None:
    """
    The pinned and at-risk Facts must not drift apart: a package added to one
    without the other would silently lose either exact-version or
    floating-range coverage.
    """
    pinned = _package_names(_fact(_AUG_2026_FACT_ID).cypher_query)
    at_risk = _package_names(_fact(_AUG_2026_AT_RISK_FACT_ID).cypher_query)
    assert pinned == at_risk


def test_aug_2026_queries_and_visual_queries_agree() -> None:
    for fact_id in (_AUG_2026_FACT_ID, _AUG_2026_AT_RISK_FACT_ID):
        fact = _fact(fact_id)
        assert _package_names(fact.cypher_query) == _package_names(
            fact.cypher_visual_query
        )


def test_at_risk_fact_only_matches_floating_ranges() -> None:
    """
    The at-risk Fact is scoped to ranges so it stays disjoint from the pinned
    Fact, which already reports exact malicious versions.
    """
    cypher = _fact(_AUG_2026_AT_RISK_FACT_ID).cypher_query
    assert "d.requirements CONTAINS '^'" in cypher
    assert "d.requirements CONTAINS '~'" in cypher
    assert "d.requirements CONTAINS '>'" in cypher


def test_at_risk_fact_normalizes_operator_prefixes() -> None:
    """
    GitHub's dependency graph emits `requirements` in several shapes
    (`= 4.2.0`, `18.2.0`, and operator-prefixed ranges), so the comparison
    strips operators and whitespace before reading the major version.
    """
    cypher = _fact(_AUG_2026_AT_RISK_FACT_ID).cypher_query
    assert "replace(d.requirements, '^', '')" in cypher
    for operator in ("'~'", "'>'", "'='"):
        assert f", {operator}, '')" in cypher
    assert "split(trim(" in cypher
    assert "[0] = a.major" in cypher


def test_at_risk_fact_reports_the_reachable_malicious_version() -> None:
    """
    `vulnerable_version` must be the malicious version the range can resolve
    to, so the finding satisfies the shared output model and identity fields.
    """
    fact = _fact(_AUG_2026_AT_RISK_FACT_ID)
    assert "a.version AS vulnerable_version" in fact.cypher_query
    for field in fact.identity_fields:
        assert field in fact.cypher_query


def test_aug_2026_facts_exclude_archived_and_disabled_repos() -> None:
    for fact_id in (_AUG_2026_FACT_ID, _AUG_2026_AT_RISK_FACT_ID):
        fact = _fact(fact_id)
        assert "coalesce(r.archived, false) = false" in fact.cypher_query
        assert "coalesce(r.disabled, false) = false" in fact.cypher_query


def test_aug_2026_facts_use_the_dependency_graph_manifest_label() -> None:
    for fact_id in (_AUG_2026_FACT_ID, _AUG_2026_AT_RISK_FACT_ID):
        fact = _fact(fact_id)
        assert "GitHubDependencyGraphManifest" in fact.cypher_query
        assert "GitHubDependencyGraphManifest" in fact.cypher_visual_query
