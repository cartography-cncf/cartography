"""DEPRECATED: temporary backward-compatibility cleanup. Remove this whole module in v1.0.0.

Before the TenableCve refactor, `TenableFinding.cve_list` was declared with `extra_index=True` and
`TenableFinding` itself carried the :CVE ontology label. Cartography only ever adds indexes, labels
and properties, so graphs synced before the refactor keep all of them:

- The RANGE index on `(:TenableFinding {cve_list})` stays live because `cve_list` is still written.
  Neo4j indexes a list under a single key and rejects values over ~8 KB, so a plugin naming
  hundreds of CVEs still aborts the whole sync.
- The :CVE label and its `_ont_*` properties stay on findings, so those findings keep showing up as
  CVE records next to the :TenableCve nodes that replaced them.

This module removes both. It is idempotent and does nothing on a graph that never had them.
"""

import logging

import neo4j

from cartography.util import timeit

logger = logging.getLogger(__name__)

# The `_ont_*` properties that the pre-refactor tenable ontology mapping wrote onto TenableFinding.
_LEGACY_FINDING_ONTOLOGY_PROPERTIES = (
    "_ont_source",
    "_ont_cve_id",
    "_ont_base_severity",
    "_ont_vuln_status",
)
# Matches cartography's default write batch size.
_LEGACY_ONTOLOGY_BATCH_SIZE = 10000


@timeit
def drop_legacy_cve_list_index(neo4j_session: neo4j.Session) -> None:
    """DEPRECATED: drop the RANGE index the old model created on `TenableFinding.cve_list`.
    Only needed for graphs synced before the TenableCve refactor; remove in v1.0.0.
    """
    # Same approach as cartography.intel.ontology.deprecated_indexes: cartography created the index
    # unnamed, so SHOW INDEXES is the only way to recover its generated name, and DROP INDEX accepts
    # only a literal name. type = 'RANGE' leaves an operator-managed TEXT index on the same property.
    rows = neo4j_session.run(
        """
        SHOW INDEXES YIELD name, labelsOrTypes, properties, entityType, type
        WHERE entityType = 'NODE' AND type = 'RANGE'
          AND labelsOrTypes = ['TenableFinding'] AND properties = ['cve_list']
        RETURN name
        """,
    )
    names = [row["name"] for row in rows]
    for name in names:
        escaped = name.replace("`", "``")
        # IF EXISTS only tolerates the index vanishing between SHOW and DROP.
        neo4j_session.run(f"DROP INDEX `{escaped}` IF EXISTS")
    if names:
        logger.info("Dropped legacy TenableFinding.cve_list index(es): %s", names)


@timeit
def remove_legacy_finding_cve_ontology(neo4j_session: neo4j.Session) -> None:
    """DEPRECATED: strip the :CVE label and `_ont_*` properties the old model put on
    TenableFinding. Only needed for graphs synced before the TenableCve refactor; remove in v1.0.0.
    """
    # Anchored on :TenableFinding, so the :TenableCve nodes that carry :CVE and
    # `_ont_source = 'tenable'` today are never touched. Each batch removes what the WHERE matches,
    # so the loop always makes progress and stops once nothing is left.
    remove_properties = ", ".join(
        f"f.{prop}" for prop in _LEGACY_FINDING_ONTOLOGY_PROPERTIES
    )
    query = f"""
        MATCH (f:TenableFinding)
        WHERE f:CVE OR f._ont_source = 'tenable'
        WITH f LIMIT $limit
        REMOVE f:CVE, {remove_properties}
        RETURN count(f) AS removed
    """
    total = 0
    while True:
        record = neo4j_session.run(query, limit=_LEGACY_ONTOLOGY_BATCH_SIZE).single()
        removed = record["removed"] if record else 0
        if not removed:
            break
        total += removed
    if total:
        logger.info(
            "Removed legacy :CVE ontology state from %d TenableFinding node(s)", total
        )
