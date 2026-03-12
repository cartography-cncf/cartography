import cartography.intel.docker_scout.scanner
from cartography.intel.docker_scout.scanner import cleanup
from cartography.intel.docker_scout.scanner import sync_from_file
from tests.data.docker_scout.mock_data import MOCK_ECR_COMBINED_FILE_DATA
from tests.data.docker_scout.mock_data import MOCK_GITLAB_COMBINED_FILE_DATA
from tests.data.docker_scout.mock_data import TEST_ECR_IMAGE_DIGEST
from tests.data.docker_scout.mock_data import TEST_GITLAB_IMAGE_DIGEST
from tests.data.docker_scout.mock_data import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def _create_ecr_image(neo4j_session, image_digest, update_tag):
    neo4j_session.run(
        """
        MERGE (e:ECRImage{id: $digest})
        ON CREATE SET e.firstseen = timestamp()
        SET e.lastupdated = $update_tag
        """,
        digest=image_digest,
        update_tag=update_tag,
    )


def _create_gitlab_container_image(neo4j_session, image_id, update_tag):
    neo4j_session.run(
        """
        MERGE (g:GitLabContainerImage{id: $image_id})
        ON CREATE SET g.firstseen = timestamp()
        SET g.lastupdated = $update_tag
        """,
        image_id=image_id,
        update_tag=update_tag,
    )


def test_docker_scout_sync_from_file(neo4j_session):
    """Test file-based ingestion creates expected nodes and relationships."""
    # Arrange: create registry nodes with distinct digests
    _create_ecr_image(neo4j_session, TEST_ECR_IMAGE_DIGEST, TEST_UPDATE_TAG)
    _create_gitlab_container_image(
        neo4j_session, TEST_GITLAB_IMAGE_DIGEST, TEST_UPDATE_TAG
    )

    # Act: ingest both scan files
    cartography.intel.docker_scout.scanner.sync_from_file(
        neo4j_session,
        MOCK_ECR_COMBINED_FILE_DATA,
        "ecr-image.json",
        TEST_UPDATE_TAG,
    )
    cartography.intel.docker_scout.scanner.sync_from_file(
        neo4j_session,
        MOCK_GITLAB_COMBINED_FILE_DATA,
        "gitlab-image.json",
        TEST_UPDATE_TAG,
    )

    # Assert nodes
    assert check_nodes(
        neo4j_session,
        "DockerScoutPublicImage",
        ["id", "name", "tag"],
    ) == {
        ("python:3.12-slim", "python", "3.12-slim"),
    }

    assert check_nodes(
        neo4j_session,
        "DockerScoutPackage",
        ["id", "name", "version"],
    ) == {
        ("3.0.15-1~deb12u1|libssl3", "libssl3", "3.0.15-1~deb12u1"),
        ("7.88.1-10+deb12u8|curl", "curl", "7.88.1-10+deb12u8"),
    }

    assert check_nodes(
        neo4j_session,
        "DockerScoutFinding",
        ["id", "name", "severity"],
    ) == {
        ("DSF|CVE-2024-13176", "CVE-2024-13176", "MEDIUM"),
        ("DSF|CVE-2024-99999", "CVE-2024-99999", "HIGH"),
    }

    assert check_nodes(neo4j_session, "DockerScoutFix", ["id", "version"]) == {
        ("3.0.16-1~deb12u1|3.0.15-1~deb12u1|libssl3", "3.0.16-1~deb12u1"),
    }

    # Assert ECR relationships (only ECR digest, not GitLab)
    assert check_rels(
        neo4j_session,
        "ECRImage",
        "id",
        "DockerScoutPublicImage",
        "id",
        "BUILT_ON",
        rel_direction_right=True,
    ) == {
        (TEST_ECR_IMAGE_DIGEST, "python:3.12-slim"),
    }

    assert check_rels(
        neo4j_session,
        "DockerScoutPackage",
        "id",
        "ECRImage",
        "id",
        "DEPLOYED",
        rel_direction_right=True,
    ) == {
        ("3.0.15-1~deb12u1|libssl3", TEST_ECR_IMAGE_DIGEST),
        ("7.88.1-10+deb12u8|curl", TEST_ECR_IMAGE_DIGEST),
    }

    assert check_rels(
        neo4j_session,
        "DockerScoutFinding",
        "id",
        "ECRImage",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        ("DSF|CVE-2024-13176", TEST_ECR_IMAGE_DIGEST),
        ("DSF|CVE-2024-99999", TEST_ECR_IMAGE_DIGEST),
    }

    # Assert GitLab relationships (only GitLab digest, not ECR)
    assert check_rels(
        neo4j_session,
        "GitLabContainerImage",
        "id",
        "DockerScoutPublicImage",
        "id",
        "BUILT_ON",
        rel_direction_right=True,
    ) == {
        (TEST_GITLAB_IMAGE_DIGEST, "python:3.12-slim"),
    }

    assert check_rels(
        neo4j_session,
        "DockerScoutPackage",
        "id",
        "GitLabContainerImage",
        "id",
        "DEPLOYED",
        rel_direction_right=True,
    ) == {
        ("3.0.15-1~deb12u1|libssl3", TEST_GITLAB_IMAGE_DIGEST),
    }

    assert check_rels(
        neo4j_session,
        "DockerScoutFinding",
        "id",
        "GitLabContainerImage",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        ("DSF|CVE-2024-13176", TEST_GITLAB_IMAGE_DIGEST),
    }

    # Assert cross-node relationships
    assert check_rels(
        neo4j_session,
        "DockerScoutPackage",
        "id",
        "DockerScoutPublicImage",
        "id",
        "FROM_BASE",
        rel_direction_right=True,
    ) == {
        ("3.0.15-1~deb12u1|libssl3", "python:3.12-slim"),
        ("7.88.1-10+deb12u8|curl", "python:3.12-slim"),
    }

    assert check_rels(
        neo4j_session,
        "DockerScoutFinding",
        "id",
        "DockerScoutPackage",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        ("DSF|CVE-2024-13176", "3.0.15-1~deb12u1|libssl3"),
        ("DSF|CVE-2024-99999", "7.88.1-10+deb12u8|curl"),
    }

    assert check_rels(
        neo4j_session,
        "DockerScoutPackage",
        "id",
        "DockerScoutFix",
        "id",
        "SHOULD_UPDATE_TO",
        rel_direction_right=True,
    ) == {
        ("3.0.15-1~deb12u1|libssl3", "3.0.16-1~deb12u1|3.0.15-1~deb12u1|libssl3"),
    }

    assert check_rels(
        neo4j_session,
        "DockerScoutFix",
        "id",
        "DockerScoutFinding",
        "id",
        "APPLIES_TO",
        rel_direction_right=True,
    ) == {
        ("3.0.16-1~deb12u1|3.0.15-1~deb12u1|libssl3", "DSF|CVE-2024-13176"),
    }


def test_docker_scout_cleanup(neo4j_session):
    """Test that cleanup removes stale Docker Scout nodes."""
    # Ingest with tag 1
    _create_ecr_image(neo4j_session, TEST_ECR_IMAGE_DIGEST, TEST_UPDATE_TAG)
    sync_from_file(
        neo4j_session, MOCK_ECR_COMBINED_FILE_DATA, "test.json", TEST_UPDATE_TAG
    )

    # Run cleanup with tag 2 (simulating a new sync that didn't re-ingest)
    cleanup(neo4j_session, {"UPDATE_TAG": TEST_UPDATE_TAG + 1})

    # Assert stale nodes are removed
    assert check_nodes(neo4j_session, "DockerScoutPublicImage", ["id"]) == set()
    assert check_nodes(neo4j_session, "DockerScoutPackage", ["id"]) == set()
    assert check_nodes(neo4j_session, "DockerScoutFinding", ["id"]) == set()
    assert check_nodes(neo4j_session, "DockerScoutFix", ["id"]) == set()
