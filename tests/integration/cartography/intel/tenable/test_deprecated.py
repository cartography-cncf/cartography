import neo4j
import pytest

import cartography.intel.tenable.deprecated as deprecated
from cartography.intel.tenable.deprecated import drop_legacy_cve_list_index
from cartography.intel.tenable.deprecated import remove_legacy_finding_cve_ontology

OPERATOR_TEXT_INDEX = "op_text_tenable_cve_list"


def _cve_list_index_names(neo4j_session) -> set[str]:
    rows = neo4j_session.run(
        """
        SHOW INDEXES YIELD name, labelsOrTypes, properties, entityType
        WHERE entityType = 'NODE'
          AND labelsOrTypes = ['TenableFinding'] AND properties = ['cve_list']
        RETURN name
        """
    )
    return {row["name"] for row in rows}


def _drop_cve_list_indexes(neo4j_session) -> None:
    # The integration Neo4j is shared across test modules and only nodes are wiped
    # between them, so indexes are dropped before and after to stay hermetic.
    for name in _cve_list_index_names(neo4j_session):
        neo4j_session.run(f"DROP INDEX `{name}` IF EXISTS")


def _create_legacy_cve_list_index(neo4j_session) -> None:
    """Create the RANGE index older versions declared, and wait until it is ONLINE.

    Index creation is asynchronous. A write that exceeds the key limit while the
    index is still POPULATING can fail at commit time and take the whole database
    down, instead of being rejected cleanly as it is against an ONLINE index - the
    state every real graph is in. Waiting keeps the tests deterministic and keeps a
    shared test database alive.
    """
    neo4j_session.run(
        "CREATE INDEX IF NOT EXISTS FOR (n:TenableFinding) ON (n.cve_list)"
    )
    neo4j_session.run("CALL db.awaitIndexes(60)")


def test_drop_legacy_cve_list_index(neo4j_session):
    """The legacy RANGE index is dropped; an operator-managed TEXT index survives."""
    _drop_cve_list_indexes(neo4j_session)
    try:
        # The RANGE index older versions created through extra_index=True.
        _create_legacy_cve_list_index(neo4j_session)
        # An index someone added by hand. Only cartography's own RANGE index goes.
        neo4j_session.run(
            f"CREATE TEXT INDEX {OPERATOR_TEXT_INDEX} IF NOT EXISTS "
            "FOR (n:TenableFinding) ON (n.cve_list)"
        )
        assert len(_cve_list_index_names(neo4j_session)) == 2

        drop_legacy_cve_list_index(neo4j_session)

        assert _cve_list_index_names(neo4j_session) == {OPERATOR_TEXT_INDEX}

        # Idempotent: a second run with nothing left to drop is a no-op.
        drop_legacy_cve_list_index(neo4j_session)
        assert _cve_list_index_names(neo4j_session) == {OPERATOR_TEXT_INDEX}
    finally:
        _drop_cve_list_indexes(neo4j_session)


def test_drop_legacy_cve_list_index_unblocks_large_cve_lists(neo4j_session):
    """The point of the drop: a CVE list over the index key limit becomes writable."""
    _drop_cve_list_indexes(neo4j_session)
    try:
        _create_legacy_cve_list_index(neo4j_session)
        # Roughly the size of a cumulative OS update plugin's CVE list.
        oversized = [f"CVE-2026-{n:05d}" for n in range(700)]
        write = "CREATE (:TenableFinding {id: 'large', cve_list: $cve_list})"

        with pytest.raises(neo4j.exceptions.Neo4jError, match="too large to index"):
            neo4j_session.run(write, cve_list=oversized).consume()

        drop_legacy_cve_list_index(neo4j_session)

        neo4j_session.run(write, cve_list=oversized).consume()
        stored = neo4j_session.run(
            "MATCH (f:TenableFinding {id: 'large'}) RETURN size(f.cve_list) AS n"
        ).single()["n"]
        assert stored == 700
    finally:
        neo4j_session.run("MATCH (f:TenableFinding {id: 'large'}) DETACH DELETE f")
        _drop_cve_list_indexes(neo4j_session)


def test_remove_legacy_finding_cve_ontology(neo4j_session, mocker):
    """Legacy :CVE state is stripped from findings, and nothing else is touched."""
    # A batch size of 1 makes the loop run once per node, so batching is exercised.
    mocker.patch.object(deprecated, "_LEGACY_ONTOLOGY_BATCH_SIZE", 1)
    neo4j_session.run(
        """
        // A finding with CVEs, as older versions left it: :CVE plus _ont_*.
        CREATE (:TenableFinding:CVE {
            id: 'legacy-with-cve', severity: 'high', cve_list: ['CVE-2022-21837'],
            _ont_source: 'tenable', _ont_cve_id: 'CVE-2022-21837',
            _ont_base_severity: 'high', _ont_vuln_status: 'open'
        })
        // A finding without CVEs. Older versions still wrote _ont_* on it, but no label.
        CREATE (:TenableFinding {
            id: 'legacy-no-cve', severity: 'info',
            _ont_source: 'tenable', _ont_base_severity: 'info', _ont_vuln_status: 'open'
        })
        CREATE (:TenableFinding:CVE {
            id: 'legacy-with-cve-2', _ont_source: 'tenable', _ont_cve_id: 'CVE-2022-21840'
        })
        // Nodes that legitimately carry :CVE today and must be left alone.
        CREATE (:TenableCve:CVE {
            id: 'TNB|CVE-2022-21837', cve_id: 'CVE-2022-21837',
            _ont_source: 'tenable', _ont_cve_id: 'CVE-2022-21837'
        })
        CREATE (:S1AppFinding:CVE {
            id: 's1-finding', _ont_source: 'sentinelone', _ont_cve_id: 'CVE-2022-21837'
        })
        """
    )

    remove_legacy_finding_cve_ontology(neo4j_session)

    legacy = neo4j_session.run(
        """
        MATCH (f:TenableFinding) WHERE f.id STARTS WITH 'legacy-'
        RETURN f.id AS id, f:CVE AS has_cve_label,
               [k IN keys(f) WHERE k STARTS WITH '_ont_'] AS ont_keys,
               f.severity AS severity, f.cve_list AS cve_list
        ORDER BY id
        """
    ).data()
    assert legacy == [
        {
            "id": "legacy-no-cve",
            "has_cve_label": False,
            "ont_keys": [],
            "severity": "info",
            "cve_list": None,
        },
        {
            "id": "legacy-with-cve",
            "has_cve_label": False,
            "ont_keys": [],
            "severity": "high",
            "cve_list": ["CVE-2022-21837"],
        },
        {
            "id": "legacy-with-cve-2",
            "has_cve_label": False,
            "ont_keys": [],
            "severity": None,
            "cve_list": None,
        },
    ]

    untouched = neo4j_session.run(
        """
        MATCH (n) WHERE n:TenableCve OR n:S1AppFinding
        RETURN n.id AS id, n:CVE AS has_cve_label, n._ont_source AS ont_source
        ORDER BY id
        """
    ).data()
    assert untouched == [
        {"id": "TNB|CVE-2022-21837", "has_cve_label": True, "ont_source": "tenable"},
        {"id": "s1-finding", "has_cve_label": True, "ont_source": "sentinelone"},
    ]

    # Idempotent: a second run finds nothing to change.
    remove_legacy_finding_cve_ontology(neo4j_session)
    remaining = neo4j_session.run(
        "MATCH (f:TenableFinding) WHERE f:CVE OR f._ont_source IS NOT NULL "
        "RETURN count(f) AS n"
    ).single()["n"]
    assert remaining == 0
