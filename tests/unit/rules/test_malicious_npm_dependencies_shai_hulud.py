import re

from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.malicious_npm_dependencies_shai_hulud import (
    malicious_npm_dependencies_shai_hulud,
)

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


def test_aug_2026_wave_facts_registered() -> None:
    """
    Fact ids are a stable identity that consumers key findings on across
    syncs; nothing generic checks that a specific id still exists.
    """
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
    """
    cypher_visual_query duplicates the IOC list for the web UI; nothing
    generic diffs it against cypher_query, so it can silently drift.
    """
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


def test_aug_2026_facts_exclude_archived_and_disabled_repos() -> None:
    for fact_id in (_AUG_2026_FACT_ID, _AUG_2026_AT_RISK_FACT_ID):
        fact = _fact(fact_id)
        assert "coalesce(r.archived, false) = false" in fact.cypher_query
        assert "coalesce(r.disabled, false) = false" in fact.cypher_query


def test_aug_2026_facts_use_explicit_relationship_labels() -> None:
    """
    Regression guard for a prior review comment: these Facts previously
    traversed with untyped `--`, which is ambiguous and cannot use the
    rel-type index. Both must use the explicit HAS_MANIFEST/HAS_DEP labels.
    """
    for fact_id in (_AUG_2026_FACT_ID, _AUG_2026_AT_RISK_FACT_ID):
        fact = _fact(fact_id)
        for cypher in (fact.cypher_query, fact.cypher_visual_query):
            assert (
                "-[:HAS_MANIFEST]->(manifest:GitHubDependencyGraphManifest)" in cypher
            )
            assert "-[:HAS_DEP]->(d:Dependency" in cypher
