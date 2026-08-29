"""DEPRECATED: temporary backward-compatibility cleanup. Remove this whole module in v1.0.0.

Before #2845, cartography created a RANGE index on the `_ont_<field>` of every semantic label,
including unbounded text/list fields (`description`, `references`, `problem_types`) whose values can
exceed Neo4j's ~8 KB RANGE index value limit and crash the sync. #2845 added an `indexed=False`
opt-out so those indexes are no longer created, but graphs synced before that change still carry
them. This module drops those deprecated indexes if they exist.
"""

import logging

import neo4j

from cartography.models.ontology.mapping import get_deprecated_ontology_index_properties
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def drop_deprecated_ontology_indexes(neo4j_session: neo4j.Session) -> None:
    """DEPRECATED: drop RANGE indexes on `_ont_` fields that the `indexed=False` opt-out (#2845)
    no longer creates. Only needed for graphs synced before that change; remove in v1.0.0.
    """
    deprecated_props = get_deprecated_ontology_index_properties()
    if not deprecated_props:
        return
    # SHOW INDEXES is NOT an existence check we could skip with try/except: cartography creates these
    # indexes unnamed, so this is the only way to recover Neo4j's auto-generated names. `DROP INDEX`
    # accepts only a literal name (no `DROP INDEX FOR (n:Label) ON (n.prop)` form exists), so the two
    # queries are incompressible without re-introducing APOC.
    # type = 'RANGE' is required: cartography only ever created RANGE indexes on these properties,
    # and SHOW INDEXES also returns TEXT/POINT/etc. indexes. Without this filter we would drop an
    # operator-managed TEXT (or future non-RANGE) index on the same property.
    rows = neo4j_session.run(
        """
        SHOW INDEXES YIELD name, labelsOrTypes, properties, entityType, type
        WHERE entityType = 'NODE' AND type = 'RANGE'
          AND size(properties) = 1 AND properties[0] IN $props
        RETURN name
        """,
        props=list(deprecated_props),
    )
    names = [row["name"] for row in rows]
    for name in names:
        escaped = name.replace("`", "``")
        # IF EXISTS only tolerates an index vanishing between SHOW and DROP (race); it does not
        # replace the SHOW above.
        neo4j_session.run(f"DROP INDEX `{escaped}` IF EXISTS")
    if names:
        logger.info(
            "Dropped %d deprecated ontology _ont_ index(es): %s", len(names), names
        )
