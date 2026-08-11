"""The EXPOSE direction flip needs a migration, because generated cleanup cannot reach the
legacy edges: it only ever matches the new label and orientation, so an upgraded graph would
hold both directions at once and any traversal of EXPOSE would see contradictory results.
"""

from cartography.util import run_analysis_job

COMMON_JOB_PARAMETERS = {"UPDATE_TAG": 123456789}


def _legacy_and_current_edges(neo4j_session):
    return {
        (row["kind"], row["target"])
        for row in neo4j_session.run(
            """
            MATCH (a)-[r]->(b)
            WHERE type(r) IN ['EXPOSE', 'EXPOSES']
            RETURN type(r) + ':' + head(labels(a)) AS kind, head(labels(b)) AS target
            """,
        )
    }


def test_railway_expose_direction_migration_drops_only_the_legacy_edges(neo4j_session):
    # Arrange: a graph written before the flip, plus the edges the current loader writes.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (si:RailwayServiceInstance{id: 'si-1', lastupdated: $tag})
        CREATE (sd:RailwayServiceDomain{id: 'sd-1'})
        CREATE (cd:RailwayCustomDomain{id: 'cd-1'})
        CREATE (tp:RailwayTCPProxy{id: 'tp-1'})
        CREATE (si)-[:EXPOSE]->(sd)
        CREATE (si)-[:EXPOSE]->(cd)
        CREATE (si)-[:EXPOSE]->(tp)
        CREATE (sd)-[:EXPOSE]->(si)
        CREATE (cd)-[:EXPOSE]->(si)
        CREATE (tp)-[:EXPOSE]->(si)
        """,
        tag=COMMON_JOB_PARAMETERS["UPDATE_TAG"],
    )

    # Act
    run_analysis_job(
        "railway_expose_edge_direction_migration.json",
        neo4j_session,
        COMMON_JOB_PARAMETERS,
    )

    # Assert: only entrypoint -> instance survives, for all three entrypoint kinds.
    assert _legacy_and_current_edges(neo4j_session) == {
        ("EXPOSE:RailwayServiceDomain", "RailwayServiceInstance"),
        ("EXPOSE:RailwayCustomDomain", "RailwayServiceInstance"),
        ("EXPOSE:RailwayTCPProxy", "RailwayServiceInstance"),
    }


def test_modal_expose_rename_migration_drops_only_the_legacy_edges(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (sb:ModalSandbox{id: 'sb-1', lastupdated: $tag})
        CREATE (tn:ModalSandboxTunnel{id: 'sb-1/8000'})
        CREATE (sb)-[:EXPOSES]->(tn)
        CREATE (tn)-[:EXPOSE]->(sb)
        """,
        tag=COMMON_JOB_PARAMETERS["UPDATE_TAG"],
    )

    # Act
    run_analysis_job(
        "modal_expose_edge_rename_migration.json",
        neo4j_session,
        COMMON_JOB_PARAMETERS,
    )

    # Assert
    assert _legacy_and_current_edges(neo4j_session) == {
        ("EXPOSE:ModalSandboxTunnel", "ModalSandbox"),
    }


def test_expose_edge_migrations_are_idempotent(neo4j_session):
    """A second run must be a no-op: these jobs run on every sync until v1.0.0."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (si:RailwayServiceInstance{id: 'si-1'})
        CREATE (sd:RailwayServiceDomain{id: 'sd-1'})
        CREATE (sb:ModalSandbox{id: 'sb-1'})
        CREATE (tn:ModalSandboxTunnel{id: 'sb-1/8000'})
        CREATE (sd)-[:EXPOSE]->(si)
        CREATE (tn)-[:EXPOSE]->(sb)
        """
    )
    expected = _legacy_and_current_edges(neo4j_session)

    # Act
    for _ in range(2):
        for job in (
            "railway_expose_edge_direction_migration.json",
            "modal_expose_edge_rename_migration.json",
        ):
            run_analysis_job(job, neo4j_session, COMMON_JOB_PARAMETERS)

    # Assert: the current edges are untouched.
    assert _legacy_and_current_edges(neo4j_session) == expected


def test_expose_edge_migrations_spare_what_this_run_did_not_refresh(neo4j_session):
    """Both jobs run per workspace, and Modal also skips an environment whose fetch failed.

    A global delete would strip exposure edges off resources this run never loaded, so the
    queries are gated on the node carrying the current update tag.
    """
    # Arrange: one refreshed pair and one left over from an earlier run.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (fresh:RailwayServiceInstance{id: 'si-fresh', lastupdated: $tag})
        CREATE (stale:RailwayServiceInstance{id: 'si-stale', lastupdated: 1})
        CREATE (sd1:RailwayServiceDomain{id: 'sd-fresh'})
        CREATE (sd2:RailwayServiceDomain{id: 'sd-stale'})
        CREATE (fresh)-[:EXPOSE]->(sd1)
        CREATE (stale)-[:EXPOSE]->(sd2)

        CREATE (sb_fresh:ModalSandbox{id: 'sb-fresh', lastupdated: $tag})
        CREATE (sb_stale:ModalSandbox{id: 'sb-stale', lastupdated: 1})
        CREATE (tn1:ModalSandboxTunnel{id: 'sb-fresh/8000'})
        CREATE (tn2:ModalSandboxTunnel{id: 'sb-stale/8000'})
        CREATE (sb_fresh)-[:EXPOSES]->(tn1)
        CREATE (sb_stale)-[:EXPOSES]->(tn2)
        """,
        tag=COMMON_JOB_PARAMETERS["UPDATE_TAG"],
    )

    # Act
    for job in (
        "railway_expose_edge_direction_migration.json",
        "modal_expose_edge_rename_migration.json",
    ):
        run_analysis_job(job, neo4j_session, COMMON_JOB_PARAMETERS)

    # Assert: only the refreshed nodes lost their legacy edge.
    survivors = {
        (row["source"], row["kind"])
        for row in neo4j_session.run(
            """
            MATCH (a)-[r]->(b)
            WHERE type(r) IN ['EXPOSE', 'EXPOSES']
            RETURN a.id AS source, type(r) AS kind
            """,
        )
    }
    assert survivors == {("si-stale", "EXPOSE"), ("sb-stale", "EXPOSES")}
