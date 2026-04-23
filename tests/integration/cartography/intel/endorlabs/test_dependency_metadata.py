from unittest.mock import patch

import cartography.intel.endorlabs.dependency_metadata
import tests.data.endorlabs.dependency_metadata
from cartography.client.core.tx import load
from cartography.intel.endorlabs.package_versions import load_package_versions
from cartography.intel.endorlabs.package_versions import (
    transform as transform_package_versions,
)
from cartography.intel.endorlabs.projects import load_projects
from cartography.intel.endorlabs.projects import transform as transform_projects
from cartography.models.endorlabs.namespace import EndorLabsNamespaceSchema
from tests.data.endorlabs.package_versions import PACKAGE_VERSIONS_RESPONSE
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
    cartography.intel.endorlabs.dependency_metadata,
    "get",
    return_value=tests.data.endorlabs.dependency_metadata.DEPENDENCY_METADATA_RESPONSE[
        "list"
    ]["objects"],
)
def test_sync_dependency_metadata(mock_api, neo4j_session):
    # Arrange: Load namespace, projects, and package versions first
    _load_namespace(neo4j_session)
    projects = transform_projects(PROJECTS_RESPONSE["list"]["objects"])
    load_projects(neo4j_session, projects, TEST_NAMESPACE, TEST_UPDATE_TAG)

    pvs = transform_package_versions(
        PACKAGE_VERSIONS_RESPONSE["list"]["objects"],
    )
    load_package_versions(neo4j_session, pvs, TEST_NAMESPACE, TEST_UPDATE_TAG)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "NAMESPACE_ID": TEST_NAMESPACE,
    }

    # Act
    cartography.intel.endorlabs.dependency_metadata.sync_dependency_metadata(
        neo4j_session,
        "fake-token",
        TEST_NAMESPACE,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert: Dependency metadata nodes exist
    expected_nodes = {
        ("dep-001", "npm://lodash@4.17.21", True),
        ("dep-002", "npm://qs@6.11.0", False),
    }
    assert (
        check_nodes(
            neo4j_session,
            "EndorLabsDependencyMetadata",
            ["id", "name", "direct"],
        )
        == expected_nodes
    )

    # Assert: Connected to importer package version (IMPORTED_BY)
    expected_importer_rels = {
        ("dep-001", "pkg-002"),
        ("dep-002", "pkg-002"),
    }
    assert (
        check_rels(
            neo4j_session,
            "EndorLabsDependencyMetadata",
            "id",
            "EndorLabsPackageVersion",
            "id",
            "IMPORTED_BY",
            rel_direction_right=True,
        )
        == expected_importer_rels
    )

    # Assert: dep-001 DEPENDS_ON pkg-001 (lodash)
    expected_depends_rels = {
        ("dep-001", "pkg-001"),
    }
    assert (
        check_rels(
            neo4j_session,
            "EndorLabsDependencyMetadata",
            "id",
            "EndorLabsPackageVersion",
            "id",
            "DEPENDS_ON",
            rel_direction_right=True,
        )
        == expected_depends_rels
    )
