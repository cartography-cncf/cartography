from cartography.intel.ontology.deprecated_indexes import (
    drop_deprecated_ontology_indexes,
)

# Properties this test creates indexes on. The integration Neo4j is shared across test modules and
# only nodes (not indexes) are wiped between them, so we drop these before and after to stay
# hermetic and to avoid EquivalentSchemaRuleAlreadyExists on CREATE.
TEST_PROPERTIES = ("_ont_references", "_ont_description", "_ont_cve_id", "_ont_source")


def _index_names_on_property(neo4j_session, prop: str) -> set[str]:
    rows = neo4j_session.run(
        """
        SHOW INDEXES YIELD name, properties, entityType
        WHERE entityType = 'NODE' AND size(properties) = 1 AND properties[0] = $prop
        RETURN name
        """,
        prop=prop,
    )
    return {row["name"] for row in rows}


def _drop_all_indexes_on_properties(neo4j_session, properties) -> None:
    for prop in properties:
        for name in _index_names_on_property(neo4j_session, prop):
            neo4j_session.run(f"DROP INDEX `{name}` IF EXISTS")


def test_drop_deprecated_ontology_indexes(neo4j_session):
    """Deprecated _ont_ indexes are dropped; non-deprecated ones survive (#2845, remove in v1.0.0)."""
    _drop_all_indexes_on_properties(neo4j_session, TEST_PROPERTIES)
    try:
        # Deprecated indexes: RANGE indexes (cartography's default) on semantic labels for unbounded
        # fields that #2845 opted out.
        neo4j_session.run(
            "CREATE INDEX IF NOT EXISTS FOR (n:CVE) ON (n._ont_references)"
        )
        neo4j_session.run(
            "CREATE INDEX IF NOT EXISTS FOR (n:Risk) ON (n._ont_description)"
        )
        # Indexes that must be kept: still created by the data model.
        neo4j_session.run("CREATE INDEX IF NOT EXISTS FOR (n:CVE) ON (n._ont_cve_id)")
        neo4j_session.run("CREATE INDEX IF NOT EXISTS FOR (n:CVE) ON (n._ont_source)")
        # An operator-managed non-RANGE index on a deprecated property must survive: we only drop the
        # RANGE indexes cartography itself created, never TEXT/POINT/etc.
        neo4j_session.run(
            "CREATE TEXT INDEX op_text_ont_references IF NOT EXISTS "
            "FOR (n:CVE) ON (n._ont_references)"
        )

        assert _index_names_on_property(neo4j_session, "_ont_references")
        assert _index_names_on_property(neo4j_session, "_ont_description")

        drop_deprecated_ontology_indexes(neo4j_session)

        # Deprecated RANGE indexes are gone, but the operator-managed TEXT index survives.
        assert _index_names_on_property(neo4j_session, "_ont_references") == {
            "op_text_ont_references"
        }
        assert _index_names_on_property(neo4j_session, "_ont_description") == set()
        # Non-deprecated indexes survive.
        assert _index_names_on_property(neo4j_session, "_ont_cve_id")
        assert _index_names_on_property(neo4j_session, "_ont_source")

        # Idempotent: a second run with nothing left to drop is a no-op.
        drop_deprecated_ontology_indexes(neo4j_session)
        assert _index_names_on_property(neo4j_session, "_ont_cve_id")
        assert _index_names_on_property(neo4j_session, "_ont_references") == {
            "op_text_ont_references"
        }
    finally:
        # Don't leak schema into other test modules sharing this Neo4j instance.
        _drop_all_indexes_on_properties(neo4j_session, TEST_PROPERTIES)
