from cartography.util import run_analysis_job

TEST_UPDATE_TAG = 123456789


def test_package_version_rename_migration(neo4j_session):
    neo4j_session.run(
        "MATCH (n) WHERE n:Package OR n:PackageVersion OR n:TrivyPackage DETACH DELETE n"
    )
    neo4j_session.run(
        """
        MERGE (p:Package:Ontology {id: 'npm|express|4.18.2'})
        SET p.name = 'express', p.version = '4.18.2', p.type = 'npm', p.lastupdated = $tag
        MERGE (tp:TrivyPackage {normalized_id: 'npm|express|4.18.2'})
        MERGE (p)-[r:DETECTED_AS]->(tp)
        SET r.lastupdated = $tag
        """,
        tag=TEST_UPDATE_TAG,
    )
    before = neo4j_session.run(
        "MATCH (n:Package {id: 'npm|express|4.18.2'}) RETURN elementId(n) AS eid"
    ).single()["eid"]

    run_analysis_job(
        "ontology_package_version_rename_migration.json",
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    row = neo4j_session.run(
        """
        MATCH (n:PackageVersion {id: 'npm|express|4.18.2'})-[:DETECTED_AS]->(:TrivyPackage)
        RETURN elementId(n) AS eid, labels(n) AS labels
        """
    ).single()
    assert row["eid"] == before, "node identity must be preserved"
    assert set(row["labels"]) == {"PackageVersion", "Ontology"}

    # A version-independent Package node must survive a re-run untouched.
    neo4j_session.run(
        "MERGE (p:Package:Ontology {id: 'npm|express'}) SET p.name = 'express', p.type = 'npm'"
    )
    run_analysis_job(
        "ontology_package_version_rename_migration.json",
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )
    assert (
        neo4j_session.run("MATCH (n:Package) RETURN count(n) AS c").single()["c"] == 1
    )
    assert (
        neo4j_session.run("MATCH (n:PackageVersion) RETURN count(n) AS c").single()["c"]
        == 1
    )
