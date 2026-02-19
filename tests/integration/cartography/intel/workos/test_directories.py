from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.workos.directories
import tests.data.workos.directories
from tests.integration.cartography.intel.workos.test_organizations import (
    _ensure_local_neo4j_has_test_environment,
)
from tests.integration.cartography.intel.workos.test_organizations import (
    _ensure_local_neo4j_has_test_organizations,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLIENT_ID = "client_1234567890abcdef"


def _ensure_local_neo4j_has_test_directories(neo4j_session):
    transformed_dirs = cartography.intel.workos.directories.transform(
        tests.data.workos.directories.WORKOS_DIRECTORIES
    )
    cartography.intel.workos.directories.load_directories(
        neo4j_session,
        transformed_dirs,
        TEST_CLIENT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.workos.directories,
    "get",
    return_value=tests.data.workos.directories.WORKOS_DIRECTORIES,
)
def test_load_workos_directories(mock_api, neo4j_session):
    """
    Ensure that directories actually get loaded
    """
    # Arrange
    _ensure_local_neo4j_has_test_environment(neo4j_session)
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    client = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKOS_CLIENT_ID": TEST_CLIENT_ID,
    }

    # Act
    cartography.intel.workos.directories.sync(
        neo4j_session,
        client,
        common_job_parameters,
    )

    # Assert Directories exist
    expected_nodes = {
        ("dir_01HXYZ1234567890ABCDEFGHIJ", "Springfield Azure AD"),
    }
    assert (
        check_nodes(neo4j_session, "WorkOSDirectory", ["id", "name"]) == expected_nodes
    )

    # Assert directories are linked to the environment
    expected_rels = {
        ("dir_01HXYZ1234567890ABCDEFGHIJ", TEST_CLIENT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSDirectory",
            "id",
            "WorkOSEnvironment",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert directories are linked to organizations
    expected_rels = {
        ("dir_01HXYZ1234567890ABCDEFGHIJ", "org_01HXYZ1234567890ABCDEFGHIJ"),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSDirectory",
            "id",
            "WorkOSOrganization",
            "id",
            "BELONGS_TO",
            rel_direction_right=True,
        )
        == expected_rels
    )
