from unittest.mock import patch

import cartography.intel.endorlabs.package_versions
import tests.data.endorlabs.package_versions
from cartography.client.core.tx import load
from cartography.intel.endorlabs.projects import load_projects
from cartography.intel.endorlabs.projects import transform as transform_projects
from cartography.models.endorlabs.namespace import EndorLabsNamespaceSchema
from tests.data.endorlabs.projects import PROJECTS_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_NAMESPACE = "acme-corp"


def _load_namespace(neo4j_session):
    load(
        neo4j_session,
        EndorLabsNamespaceSchema(),
        [{"id": TEST_NAMESPACE, "name": TEST_NAMESPACE}],
        lastupdated=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.endorlabs.package_versions,
    "get",
    return_value=tests.data.endorlabs.package_versions.PACKAGE_VERSIONS_RESPONSE[
        "list"
    ]["objects"],
)
def test_sync_package_versions(mock_api, neo4j_session):
    # Arrange: Load namespace and projects first
    _load_namespace(neo4j_session)
    projects = transform_projects(PROJECTS_RESPONSE["list"]["objects"])
    load_projects(neo4j_session, projects, TEST_NAMESPACE, TEST_UPDATE_TAG)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "NAMESPACE_ID": TEST_NAMESPACE,
    }

    # Act
    cartography.intel.endorlabs.package_versions.sync_package_versions(
        neo4j_session,
        "fake-token",
        TEST_NAMESPACE,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert: Package versions exist
    expected_nodes = {
        ("pkg-001", "npm://lodash@4.17.21", "ECOSYSTEM_NPM"),
        ("pkg-002", "npm://express@4.18.2", "ECOSYSTEM_NPM"),
        ("pkg-003", "pypi://requests@2.31.0", "ECOSYSTEM_PYPI"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "EndorLabsPackageVersion",
            ["id", "name", "ecosystem"],
        )
        == expected_nodes
    )

    # Assert: Also labeled as Dependency
    assert (
        check_nodes(
            neo4j_session,
            "Dependency",
            ["id", "name", "ecosystem"],
        )
        == expected_nodes
    )

    # Assert: Connected to projects via FOUND_IN
    expected_rels = {
        ("pkg-001", "proj-001"),
        ("pkg-002", "proj-001"),
        ("pkg-003", "proj-002"),
    }
    assert (
        check_rels(
            neo4j_session,
            "EndorLabsPackageVersion",
            "id",
            "EndorLabsProject",
            "id",
            "FOUND_IN",
            rel_direction_right=True,
        )
        == expected_rels
    )
