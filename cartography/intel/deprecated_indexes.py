"""DEPRECATED: temporary backward-compatibility cleanup. Remove this whole module in v1.0.0.

MatchLink relationship indexes used to be keyed on
`(_sub_resource_label, _sub_resource_id, lastupdated)`. Because `lastupdated` is rewritten on
every sync, every relationship's index entry was deleted and reinserted on every run, which
roughly halved warm write throughput on large MatchLink loads. The trailing key never helped
anyway: the only consumer is the MatchLink cleanup, whose `lastupdated <> $UPDATE_TAG` is not a
seekable predicate.

`build_create_index_queries_for_matchlink()` now creates the two-key index only, but
`CREATE INDEX IF NOT EXISTS` does not replace an index with a different property list, so graphs
synced before that change keep the churning three-key index alongside the new one. This module
drops those deprecated indexes if they exist.
"""

import logging

import neo4j

from cartography.util import timeit

logger = logging.getLogger(__name__)

_DEPRECATED_MATCHLINK_REL_INDEX_PROPERTIES = [
    "_sub_resource_label",
    "_sub_resource_id",
    "lastupdated",
]


@timeit
def drop_deprecated_matchlink_rel_indexes(neo4j_session: neo4j.Session) -> None:
    """DEPRECATED: drop the three-key MatchLink relationship indexes that
    `build_create_index_queries_for_matchlink()` no longer creates. Only needed for graphs synced
    before that change; remove in v1.0.0.
    """
    # SHOW INDEXES is NOT an existence check we could skip with try/except: cartography creates
    # these indexes unnamed, so this is the only way to recover Neo4j's auto-generated names.
    # `DROP INDEX` accepts only a literal name (no `DROP INDEX FOR ()-[r:X]->() ON (...)` form
    # exists), so the two queries are incompressible.
    # `properties = $props` is exact ordered-list equality, and SHOW INDEXES returns properties in
    # index-key order, so this can only ever match the old three-key shape and never the two-key
    # index we create today.
    # type = 'RANGE' is required: cartography only ever created RANGE indexes here, and
    # SHOW INDEXES also returns TEXT/POINT/etc. indexes. Without this filter we would drop an
    # operator-managed non-RANGE index on the same properties.
    rows = neo4j_session.run(
        """
        SHOW INDEXES YIELD name, properties, entityType, type
        WHERE entityType = 'RELATIONSHIP' AND type = 'RANGE'
          AND properties = $props
        RETURN name
        """,
        props=_DEPRECATED_MATCHLINK_REL_INDEX_PROPERTIES,
    )
    names = [row["name"] for row in rows]
    for name in names:
        escaped = name.replace("`", "``")
        # IF EXISTS only tolerates an index vanishing between SHOW and DROP (race); it does not
        # replace the SHOW above.
        neo4j_session.run(f"DROP INDEX `{escaped}` IF EXISTS")
    if names:
        logger.info(
            "Dropped %d deprecated MatchLink relationship index(es) keyed on lastupdated: %s",
            len(names),
            names,
        )
