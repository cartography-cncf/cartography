from cartography.util import run_analysis_job

TEST_UPDATE_TAG = 123456789


def test_image_source_backfill_fills_images_enriched_before_the_mapping(
    neo4j_session,
):
    neo4j_session.run(
        "MATCH (n) WHERE n:AWSECRImage OR n:GitHubContainerImage DETACH DELETE n"
    )
    # Images enriched by an older version: native source fields, no ontology copy.
    neo4j_session.run(
        """
        CREATE (:AWSECRImage {id: 'sha256:ecr', source_uri: 'https://github.com/example/api', source_revision: 'abc123'})
        CREATE (:GitHubContainerImage {id: 'sha256:ghcr', source_uri: 'https://github.com/example/web'})
        CREATE (:AWSECRImage {id: 'sha256:nosource'})
        CREATE (:AWSECRImage {id: 'sha256:current', source_uri: 'https://github.com/example/new', source_revision: 'def456',
                              _ont_source_uri: 'https://github.com/example/new', _ont_source_revision: 'def456'})
        """
    )

    run_analysis_job(
        "ontology_image_source_backfill.json",
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    rows = neo4j_session.run(
        """
        MATCH (n) WHERE n:AWSECRImage OR n:GitHubContainerImage
        RETURN n.id AS id, n._ont_source_uri AS uri, n._ont_source_revision AS revision
        """
    )
    assert {(r["id"], r["uri"], r["revision"]) for r in rows} == {
        ("sha256:ecr", "https://github.com/example/api", "abc123"),
        ("sha256:ghcr", "https://github.com/example/web", None),
        ("sha256:nosource", None, None),
        ("sha256:current", "https://github.com/example/new", "def456"),
    }
