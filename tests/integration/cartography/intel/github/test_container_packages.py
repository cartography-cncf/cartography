import cartography.intel.github.container_packages
from tests.data.github.container_packages import GET_CONTAINER_PACKAGES, GET_PACKAGE_VERSIONS, IMAGE_MANIFEST, IMAGE_CONFIG
from unittest.mock import patch, MagicMock


@patch("cartography.intel.github.container_packages.util.fetch_all_rest_api_pages")
@patch("cartography.intel.github.container_packages._get_ghcr_token")
@patch("cartography.intel.github.container_packages._fetch_manifest")
@patch("cartography.intel.github.container_packages._fetch_config_blob")
def test_sync_container_packages(
    mock_config_blob, mock_manifest, mock_token, mock_fetch_all, neo4j_session
):
    """
    Test that sync_container_packages correctly creates Package, Tag, and Image nodes.
    """
    # Mock REST API for packages and versions
    mock_fetch_all.side_effect = [
        GET_CONTAINER_PACKAGES,  # get_container_packages
        GET_PACKAGE_VERSIONS,      # get_package_versions
    ]

    # Mock Token
    mock_token.return_value = "fake-jwt-token"

    # Mock Manifest Response
    mock_manifest_resp = MagicMock()
    mock_manifest_resp.status_code = 200
    mock_manifest_resp.json.return_value = IMAGE_MANIFEST
    mock_manifest_resp.headers = {"Docker-Content-Digest": "sha256:digest123"}
    mock_manifest.return_value = mock_manifest_resp

    # Mock Config Blob
    mock_config_blob.return_value = IMAGE_CONFIG

    # Run sync
    cartography.intel.github.container_packages.sync_container_packages(
        neo4j_session,
        "fake-token",
        "https://api.github.com",
        "test-org",
        "https://github.com/test-org",
        12345,
        {"UPDATE_TAG": 12345},
    )

    # Verify Package node
    res = neo4j_session.run("MATCH (p:GitHubContainerPackage) RETURN p.id as id, p.name as name")
    pkg = res.single()
    assert pkg["id"] == 123456
    assert pkg["name"] == "my-app"

    # Verify Image node
    res = neo4j_session.run("MATCH (i:GitHubContainerImage) RETURN i.digest as digest, i.architecture as arch, i.os as os")
    img = res.single()
    assert img["digest"] == "sha256:digest123"
    assert img["arch"] == "amd64"
    assert img["os"] == "linux"

    # Verify Tag nodes
    res = neo4j_session.run("MATCH (t:GitHubContainerPackageTag) RETURN count(t) as count")
    assert res.single()["count"] == 2

    # Verify Package -> Tag relationship
    res = neo4j_session.run("MATCH (p:GitHubContainerPackage)-[:HAS_TAG]->(t:GitHubContainerPackageTag) RETURN count(t) as count")
    assert res.single()["count"] == 2

    # Verify Tag -> Image relationship
    res = neo4j_session.run("MATCH (t:GitHubContainerPackageTag)-[:REFERENCES]->(i:GitHubContainerImage) RETURN count(i) as count")
    assert res.single()["count"] == 2


@patch("cartography.intel.github.container_packages.util.fetch_all_rest_api_pages")
@patch("cartography.intel.github.container_packages._get_ghcr_token")
@patch("cartography.intel.github.container_packages._fetch_manifest")
@patch("cartography.intel.github.container_packages._fetch_config_blob")
def test_cleanup_container_packages(
    mock_config_blob, mock_manifest, mock_token, mock_fetch_all, neo4j_session
):
    """
    Test that cleanup correctly removes stale nodes across all new schemas.
    """
    # Create stale nodes
    neo4j_session.run(
        "CREATE (:GitHubContainerPackage {id: 'stale-pkg', lastupdated: 1000})"
    )
    neo4j_session.run(
        "CREATE (:GitHubContainerImage {id: 'stale-img', digest: 'stale-img', lastupdated: 1000})"
    )
    neo4j_session.run(
        "CREATE (:GitHubContainerPackageTag {id: 'stale-tag', lastupdated: 1000})"
    )

    # Mock empty sync
    mock_fetch_all.return_value = []

    # Run sync with new update tag
    cartography.intel.github.container_packages.sync_container_packages(
        neo4j_session,
        "fake-token",
        "https://api.github.com",
        "test-org",
        "https://github.com/test-org",
        2000,
        {"UPDATE_TAG": 2000},
    )

    # Verify nodes are gone
    res = neo4j_session.run("MATCH (n:GitHubContainerPackage) RETURN count(n) as count")
    assert res.single()["count"] == 0
    res = neo4j_session.run("MATCH (n:GitHubContainerImage) RETURN count(n) as count")
    assert res.single()["count"] == 0
    res = neo4j_session.run("MATCH (n:GitHubContainerPackageTag) RETURN count(n) as count")
    assert res.single()["count"] == 0
