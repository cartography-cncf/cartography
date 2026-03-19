import cartography.intel.docker_scout.scanner
from cartography.intel.docker_scout.scanner import cleanup
from cartography.intel.docker_scout.scanner import sync_from_file
from tests.data.docker_scout.mock_data import MOCK_ECR_RECOMMENDATION_RAW
from tests.data.docker_scout.mock_data import MOCK_GITLAB_RECOMMENDATION_RAW
from tests.data.docker_scout.mock_data import TEST_ECR_IMAGE_DIGEST
from tests.data.docker_scout.mock_data import TEST_GITLAB_IMAGE_DIGEST
from tests.data.docker_scout.mock_data import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def _create_ontology_image(neo4j_session, ont_digest, update_tag):
    neo4j_session.run(
        """
        MERGE (i:Image{id: $image_id})
        ON CREATE SET i.firstseen = timestamp()
        SET i._ont_digest = $ont_digest, i.lastupdated = $update_tag
        """,
        image_id=f"image-for-{ont_digest[:18]}",
        ont_digest=ont_digest,
        update_tag=update_tag,
    )


def test_docker_scout_sync_from_file(neo4j_session):
    _create_ontology_image(neo4j_session, TEST_ECR_IMAGE_DIGEST, TEST_UPDATE_TAG)
    _create_ontology_image(neo4j_session, TEST_GITLAB_IMAGE_DIGEST, TEST_UPDATE_TAG)

    cartography.intel.docker_scout.scanner.sync_from_file(
        neo4j_session,
        MOCK_ECR_RECOMMENDATION_RAW,
        "ecr-image.txt",
        TEST_UPDATE_TAG,
    )
    cartography.intel.docker_scout.scanner.sync_from_file(
        neo4j_session,
        MOCK_GITLAB_RECOMMENDATION_RAW,
        "gitlab-image.txt",
        TEST_UPDATE_TAG,
    )

    assert check_nodes(
        neo4j_session,
        "DockerScoutPublicImage",
        ["id", "name", "tag"],
    ) == {
        ("node:25-alpine", "node", "25-alpine"),
    }

    public_image_details = {
        (record["id"], record["tag"]): record["alternative_tags"]
        for record in neo4j_session.run(
            """
            MATCH (p:DockerScoutPublicImage)
            RETURN p.id AS id, p.tag AS tag, p.alternative_tags AS alternative_tags
            """,
        )
    }
    assert public_image_details[("node:25-alpine", "25-alpine")] == [
        "25-alpine3.23",
        "alpine",
        "alpine3.23",
        "current-alpine",
        "current-alpine3.23",
    ]

    assert check_nodes(
        neo4j_session,
        "DockerScoutPublicImageTag",
        ["id", "name", "tag"],
    ) == {
        ("node:25-alpine", "node", "25-alpine"),
        ("node:current-alpine", "node", "current-alpine"),
        ("node:current-alpine3.23", "node", "current-alpine3.23"),
        ("node:slim", "node", "slim"),
    }

    base_image_details = {
        (record["id"], record["tag"]): record["alternative_tags"]
        for record in neo4j_session.run(
            """
            MATCH (b:DockerScoutPublicImageTag)
            RETURN b.id AS id, b.tag AS tag, b.alternative_tags AS alternative_tags
            """,
        )
    }
    assert base_image_details[("node:25-alpine", "25-alpine")] == [
        "25-alpine3.23",
        "alpine",
        "alpine3.23",
        "current-alpine",
        "current-alpine3.23",
        "25.8.1-alpine",
        "25.8.1-alpine3.23",
        "25.8-alpine",
        "25.8-alpine3.23",
    ]
    assert base_image_details[("node:slim", "slim")] == [
        "25.8.1-slim",
        "25.8-slim",
        "current-slim",
        "25-slim",
        "bookworm-slim",
        "25-bookworm-slim",
        "25.8-bookworm-slim",
        "25.8.1-bookworm-slim",
        "current-bookworm-slim",
    ]

    tags_with_digest = neo4j_session.run(
        """
        MATCH (b:DockerScoutPublicImageTag)
        WHERE b.digest IS NOT NULL
        RETURN count(b) AS count
        """,
    ).single()["count"]
    assert tags_with_digest == 0

    assert check_rels(
        neo4j_session,
        "Image",
        "id",
        "DockerScoutPublicImage",
        "id",
        "BUILT_ON",
        rel_direction_right=True,
    ) == {
        (f"image-for-{TEST_ECR_IMAGE_DIGEST[:18]}", "node:25-alpine"),
        (f"image-for-{TEST_GITLAB_IMAGE_DIGEST[:18]}", "node:25-alpine"),
    }

    assert check_rels(
        neo4j_session,
        "DockerScoutPublicImage",
        "id",
        "DockerScoutPublicImageTag",
        "id",
        "BUILT_FROM",
        rel_direction_right=True,
    ) == {
        ("node:25-alpine", "node:25-alpine"),
    }

    assert check_rels(
        neo4j_session,
        "DockerScoutPublicImage",
        "id",
        "DockerScoutPublicImageTag",
        "id",
        "SHOULD_UPDATE_TO",
        rel_direction_right=True,
    ) == {
        ("node:25-alpine", "node:25-alpine"),
        ("node:25-alpine", "node:current-alpine"),
        ("node:25-alpine", "node:current-alpine3.23"),
        ("node:25-alpine", "node:slim"),
    }

    should_update_rels = neo4j_session.run(
        """
        MATCH (p:DockerScoutPublicImage)-[r:SHOULD_UPDATE_TO]->(b:DockerScoutPublicImageTag)
        RETURN
            p.id AS public_image_id,
            b.id AS base_image_id,
            r.benefits AS benefits,
            r.fix_critical AS fix_critical,
            r.fix_high AS fix_high,
            r.fix_medium AS fix_medium,
            r.fix_low AS fix_low
        """,
    )
    rel_props = {
        (record["public_image_id"], record["base_image_id"]): (
            record["benefits"],
            record["fix_critical"],
            record["fix_high"],
            record["fix_medium"],
            record["fix_low"],
        )
        for record in should_update_rels
    }
    assert rel_props[("node:25-alpine", "node:25-alpine")] == (
        [
            "Same OS detected",
            "Minor runtime version update",
            "Newer image for same tag",
            "Image contains 9 fewer packages",
            "Tag was pushed more recently",
            "Image has similar size",
            "Image introduces no new vulnerability but removes 2",
        ],
        None,
        2,
        None,
        None,
    )
    assert rel_props[("node:25-alpine", "node:slim")] == (
        [
            "Tag is preferred tag",
            "Tag was pushed more recently",
            "Tag is using slim variant",
            "slim was pulled 17K times last month",
        ],
        None,
        2,
        1,
        None,
    )


def test_docker_scout_cleanup(neo4j_session):
    _create_ontology_image(neo4j_session, TEST_ECR_IMAGE_DIGEST, TEST_UPDATE_TAG)
    sync_from_file(
        neo4j_session,
        MOCK_ECR_RECOMMENDATION_RAW,
        "test.txt",
        TEST_UPDATE_TAG,
    )

    cleanup(neo4j_session, {"UPDATE_TAG": TEST_UPDATE_TAG + 1})

    assert check_nodes(neo4j_session, "DockerScoutPublicImage", ["id"]) == set()
    assert check_nodes(neo4j_session, "DockerScoutPublicImageTag", ["id"]) == set()
