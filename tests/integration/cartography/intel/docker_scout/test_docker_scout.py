from unittest.mock import patch

import cartography.intel.docker_scout.scanner
from tests.data.docker_scout.mock_data import MOCK_CVES_DATA
from tests.data.docker_scout.mock_data import MOCK_PUBLIC_SBOM_DATA
from tests.data.docker_scout.mock_data import MOCK_SBOM_DATA
from tests.data.docker_scout.mock_data import TEST_GITLAB_IMAGE_ID
from tests.data.docker_scout.mock_data import TEST_IMAGE
from tests.data.docker_scout.mock_data import TEST_IMAGE_DIGEST
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


@patch.object(
    cartography.intel.docker_scout.scanner,
    "get_cves",
    return_value=MOCK_CVES_DATA,
)
@patch.object(
    cartography.intel.docker_scout.scanner,
    "get_sbom",
    side_effect=[MOCK_SBOM_DATA, MOCK_PUBLIC_SBOM_DATA],
)
def test_docker_scout_sync(mock_get_sbom, mock_get_cves, neo4j_session):
    # Arrange: create external registry nodes that Docker Scout rels connect to
    _create_ecr_image(neo4j_session, TEST_IMAGE_DIGEST, TEST_UPDATE_TAG)
    _create_gitlab_container_image(neo4j_session, TEST_GITLAB_IMAGE_ID, TEST_UPDATE_TAG)

    # Act: run the full sync orchestration
    cartography.intel.docker_scout.scanner.sync(
        neo4j_session,
        TEST_IMAGE,
        TEST_UPDATE_TAG,
    )

    # Verify get_sbom was called twice (scanned image, then public image)
    assert mock_get_sbom.call_count == 2
    assert mock_get_sbom.call_args_list[0].args[0] == TEST_IMAGE
    assert mock_get_sbom.call_args_list[1].args[0] == "python:3.12-slim"
    mock_get_cves.assert_called_once_with(TEST_IMAGE)

    # --- Assert nodes ---

    # DockerScoutPublicImage
    assert check_nodes(
        neo4j_session, "DockerScoutPublicImage", ["id", "name", "tag"]
    ) == {
        ("python:3.12-slim", "python", "3.12-slim"),
    }

    # DockerScoutPackage
    assert check_nodes(
        neo4j_session, "DockerScoutPackage", ["id", "name", "version"]
    ) == {
        ("3.0.15-1~deb12u1|libssl3", "libssl3", "3.0.15-1~deb12u1"),
        ("7.88.1-10+deb12u8|curl", "curl", "7.88.1-10+deb12u8"),
        ("5.2.15-2+b2|bash", "bash", "5.2.15-2+b2"),
    }

    # DockerScoutFinding (name is mapped from source_id)
    assert check_nodes(
        neo4j_session, "DockerScoutFinding", ["id", "name", "severity"]
    ) == {
        ("DSF|CVE-2024-13176", "CVE-2024-13176", "MEDIUM"),
        ("DSF|CVE-2024-99999", "CVE-2024-99999", "HIGH"),
    }

    # DockerScoutFix (version is mapped from fixed_by)
    assert check_nodes(neo4j_session, "DockerScoutFix", ["id", "version"]) == {
        ("3.0.16-1~deb12u1|3.0.15-1~deb12u1|libssl3", "3.0.16-1~deb12u1"),
    }

    # Extra labels
    assert check_nodes(neo4j_session, "CVE", ["id"]) == {
        ("DSF|CVE-2024-13176",),
        ("DSF|CVE-2024-99999",),
    }
    assert check_nodes(neo4j_session, "Risk", ["id"]) == {
        ("DSF|CVE-2024-13176",),
        ("DSF|CVE-2024-99999",),
    }
    assert check_nodes(neo4j_session, "Fix", ["id"]) == {
        ("3.0.16-1~deb12u1|3.0.15-1~deb12u1|libssl3",),
    }

    # --- Assert relationships ---

    # ECRImage -[:BUILT_ON]-> DockerScoutPublicImage
    assert check_rels(
        neo4j_session,
        "ECRImage",
        "id",
        "DockerScoutPublicImage",
        "id",
        "BUILT_ON",
        rel_direction_right=True,
    ) == {
        (TEST_IMAGE_DIGEST, "python:3.12-slim"),
    }

    # GitLabContainerImage -[:BUILT_ON]-> DockerScoutPublicImage
    assert check_rels(
        neo4j_session,
        "GitLabContainerImage",
        "id",
        "DockerScoutPublicImage",
        "id",
        "BUILT_ON",
        rel_direction_right=True,
    ) == {
        (TEST_GITLAB_IMAGE_ID, "python:3.12-slim"),
    }

    # DockerScoutPackage -[:DEPLOYED]-> ECRImage
    assert check_rels(
        neo4j_session,
        "DockerScoutPackage",
        "id",
        "ECRImage",
        "id",
        "DEPLOYED",
        rel_direction_right=True,
    ) == {
        ("3.0.15-1~deb12u1|libssl3", TEST_IMAGE_DIGEST),
        ("7.88.1-10+deb12u8|curl", TEST_IMAGE_DIGEST),
        ("5.2.15-2+b2|bash", TEST_IMAGE_DIGEST),
    }

    # DockerScoutPackage -[:DEPLOYED]-> GitLabContainerImage
    assert check_rels(
        neo4j_session,
        "DockerScoutPackage",
        "id",
        "GitLabContainerImage",
        "id",
        "DEPLOYED",
        rel_direction_right=True,
    ) == {
        ("3.0.15-1~deb12u1|libssl3", TEST_GITLAB_IMAGE_ID),
        ("7.88.1-10+deb12u8|curl", TEST_GITLAB_IMAGE_ID),
        ("5.2.15-2+b2|bash", TEST_GITLAB_IMAGE_ID),
    }

    # DockerScoutPackage -[:FROM_BASE]-> DockerScoutPublicImage
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
        ("5.2.15-2+b2|bash", "python:3.12-slim"),
    }

    # DockerScoutFinding -[:AFFECTS]-> ECRImage
    assert check_rels(
        neo4j_session,
        "DockerScoutFinding",
        "id",
        "ECRImage",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        ("DSF|CVE-2024-13176", TEST_IMAGE_DIGEST),
        ("DSF|CVE-2024-99999", TEST_IMAGE_DIGEST),
    }

    # DockerScoutFinding -[:AFFECTS]-> GitLabContainerImage
    assert check_rels(
        neo4j_session,
        "DockerScoutFinding",
        "id",
        "GitLabContainerImage",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        ("DSF|CVE-2024-13176", TEST_GITLAB_IMAGE_ID),
        ("DSF|CVE-2024-99999", TEST_GITLAB_IMAGE_ID),
    }

    # DockerScoutFinding -[:AFFECTS]-> DockerScoutPackage
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

    # DockerScoutPackage -[:SHOULD_UPDATE_TO]-> DockerScoutFix
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

    # DockerScoutFix -[:APPLIES_TO]-> DockerScoutFinding
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

    # --- Cleanup test ---
    cartography.intel.docker_scout.scanner.cleanup(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )
