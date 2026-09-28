from cartography.intel.deprecated_indexes import drop_deprecated_matchlink_rel_indexes

# Relationship types this test creates indexes on. The integration Neo4j is shared across test
# modules and only nodes (not indexes) are wiped between them, so we drop these before and after to
# stay hermetic and to avoid EquivalentSchemaRuleAlreadyExists on CREATE.
TEST_REL_TYPES = ("TEST_DEPRECATED_INDEX_A", "TEST_DEPRECATED_INDEX_B")


def _rel_indexes(neo4j_session, rel_type: str) -> set[tuple[str, tuple[str, ...]]]:
    rows = neo4j_session.run(
        """
        SHOW INDEXES YIELD name, labelsOrTypes, properties, entityType
        WHERE entityType = 'RELATIONSHIP' AND $rel_type IN labelsOrTypes
        RETURN name, properties
        """,
        rel_type=rel_type,
    )
    return {(row["name"], tuple(row["properties"])) for row in rows}


def _drop_all_rel_indexes(neo4j_session, rel_types) -> None:
    for rel_type in rel_types:
        for name, _ in _rel_indexes(neo4j_session, rel_type):
            neo4j_session.run(f"DROP INDEX `{name}` IF EXISTS")


def test_drop_deprecated_matchlink_rel_indexes(neo4j_session):
    """The old three-key MatchLink relationship index is dropped; every other one survives."""
    _drop_all_rel_indexes(neo4j_session, TEST_REL_TYPES)
    try:
        # Deprecated: the three-key shape cartography used to create, whose trailing `lastupdated`
        # made Neo4j rewrite every index entry on every sync.
        neo4j_session.run(
            "CREATE INDEX deprecated_three_key IF NOT EXISTS "
            "FOR ()-[r:TEST_DEPRECATED_INDEX_A]->() "
            "ON (r._sub_resource_label, r._sub_resource_id, r.lastupdated)"
        )
        # Must be kept: the two-key shape cartography creates today.
        neo4j_session.run(
            "CREATE INDEX current_two_key IF NOT EXISTS "
            "FOR ()-[r:TEST_DEPRECATED_INDEX_A]->() "
            "ON (r._sub_resource_label, r._sub_resource_id)"
        )
        # Must be kept: same properties in a different order is a different index shape, and is not
        # something cartography ever created.
        neo4j_session.run(
            "CREATE INDEX reordered_three_key IF NOT EXISTS "
            "FOR ()-[r:TEST_DEPRECATED_INDEX_B]->() "
            "ON (r.lastupdated, r._sub_resource_label, r._sub_resource_id)"
        )

        assert _rel_indexes(neo4j_session, "TEST_DEPRECATED_INDEX_A") == {
            (
                "deprecated_three_key",
                ("_sub_resource_label", "_sub_resource_id", "lastupdated"),
            ),
            ("current_two_key", ("_sub_resource_label", "_sub_resource_id")),
        }

        drop_deprecated_matchlink_rel_indexes(neo4j_session)

        # Only the three-key index in cartography's own key order is gone.
        assert _rel_indexes(neo4j_session, "TEST_DEPRECATED_INDEX_A") == {
            ("current_two_key", ("_sub_resource_label", "_sub_resource_id")),
        }
        assert _rel_indexes(neo4j_session, "TEST_DEPRECATED_INDEX_B") == {
            (
                "reordered_three_key",
                ("lastupdated", "_sub_resource_label", "_sub_resource_id"),
            ),
        }

        # Idempotent: a second run with nothing left to drop is a no-op.
        drop_deprecated_matchlink_rel_indexes(neo4j_session)
        assert _rel_indexes(neo4j_session, "TEST_DEPRECATED_INDEX_A") == {
            ("current_two_key", ("_sub_resource_label", "_sub_resource_id")),
        }
    finally:
        # Don't leak schema into other test modules sharing this Neo4j instance.
        _drop_all_rel_indexes(neo4j_session, TEST_REL_TYPES)
