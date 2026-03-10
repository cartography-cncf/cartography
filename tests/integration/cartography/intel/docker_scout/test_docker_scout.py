from cartography.intel.docker_scout.scanner import cleanup
from cartography.intel.docker_scout.scanner import load_findings
from cartography.intel.docker_scout.scanner import load_fixes
from cartography.intel.docker_scout.scanner import load_packages
from cartography.intel.docker_scout.scanner import load_public_image
from cartography.intel.docker_scout.scanner import transform_findings
from cartography.intel.docker_scout.scanner import transform_packages
from cartography.intel.docker_scout.scanner import transform_public_image
from tests.data.docker_scout.mock_data import MOCK_CVES_DATA
from tests.data.docker_scout.mock_data import MOCK_PUBLIC_SBOM_DATA
from tests.data.docker_scout.mock_data import MOCK_SBOM_DATA
from tests.data.docker_scout.mock_data import TEST_GITLAB_IMAGE_ID
from tests.data.docker_scout.mock_data import TEST_IMAGE_DIGEST
from tests.data.docker_scout.mock_data import TEST_PUBLIC_IMAGE_ID
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


def test_docker_scout_sync(neo4j_session):
    # Arrange: create external registry nodes that Docker Scout rels connect to
    _create_ecr_image(neo4j_session, TEST_IMAGE_DIGEST, TEST_UPDATE_TAG)
    _create_gitlab_container_image(neo4j_session, TEST_GITLAB_IMAGE_ID, TEST_UPDATE_TAG)

    # Transform
    public_image = transform_public_image(MOCK_SBOM_DATA, TEST_IMAGE_DIGEST)
    assert public_image is not None

    packages = transform_packages(
        MOCK_PUBLIC_SBOM_DATA, TEST_IMAGE_DIGEST, TEST_PUBLIC_IMAGE_ID
    )
    findings, fixes = transform_findings(MOCK_CVES_DATA, TEST_IMAGE_DIGEST)

    # Load
    load_public_image(neo4j_session, public_image, TEST_UPDATE_TAG)
    load_packages(neo4j_session, packages, TEST_UPDATE_TAG)
    load_findings(neo4j_session, findings, TEST_UPDATE_TAG)
    load_fixes(neo4j_session, fixes, TEST_UPDATE_TAG)

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
    cleanup(neo4j_session, {"UPDATE_TAG": TEST_UPDATE_TAG})
