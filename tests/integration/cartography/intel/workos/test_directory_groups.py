from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.workos.directory_groups
import tests.data.workos.directory_groups
from tests.integration.cartography.intel.workos.test_directories import (
    _ensure_local_neo4j_has_test_directories,
)
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


def _ensure_local_neo4j_has_test_directory_groups(neo4j_session):
    transformed_groups = cartography.intel.workos.directory_groups.transform(
        tests.data.workos.directory_groups.WORKOS_DIRECTORY_GROUPS
    )
    cartography.intel.workos.directory_groups.load_directory_groups(
        neo4j_session,
        transformed_groups,
        TEST_CLIENT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.workos.directory_groups,
    "get",
    return_value=tests.data.workos.directory_groups.WORKOS_DIRECTORY_GROUPS,
)
def test_load_workos_directory_groups(mock_api, neo4j_session):
    """
    Ensure that directory groups actually get loaded
    """
    # Arrange
    _ensure_local_neo4j_has_test_environment(neo4j_session)
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_directories(neo4j_session)
    client = MagicMock()
    directory_ids = ["dir_01HXYZ1234567890ABCDEFGHIJ"]
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKOS_CLIENT_ID": TEST_CLIENT_ID,
    }

    # Act
    cartography.intel.workos.directory_groups.sync(
        neo4j_session,
        client,
        directory_ids,
        common_job_parameters,
    )

    # Assert DirectoryGroups exist
    expected_nodes = {
        ("dirgrp_01HXYZ1234567890ABCDEFGHIJ", "Engineering"),
        ("dirgrp_02HXYZ0987654321ZYXWVUTSRQ", "Management"),
    }
    assert (
        check_nodes(neo4j_session, "WorkOSDirectoryGroup", ["id", "name"])
        == expected_nodes
    )

    # Assert directory groups are linked to the environment
    expected_rels = {
        ("dirgrp_01HXYZ1234567890ABCDEFGHIJ", TEST_CLIENT_ID),
        ("dirgrp_02HXYZ0987654321ZYXWVUTSRQ", TEST_CLIENT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSDirectoryGroup",
            "id",
            "WorkOSEnvironment",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert directory groups are linked to directories
    expected_rels = {
        ("dir_01HXYZ1234567890ABCDEFGHIJ", "dirgrp_01HXYZ1234567890ABCDEFGHIJ"),
        ("dir_01HXYZ1234567890ABCDEFGHIJ", "dirgrp_02HXYZ0987654321ZYXWVUTSRQ"),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSDirectory",
            "id",
            "WorkOSDirectoryGroup",
            "id",
            "HAS",
            rel_direction_right=True,
        )
        == expected_rels
    )

    # Assert directory groups are linked to organizations
    expected_rels = {
        ("dirgrp_01HXYZ1234567890ABCDEFGHIJ", "org_01HXYZ1234567890ABCDEFGHIJ"),
        ("dirgrp_02HXYZ0987654321ZYXWVUTSRQ", "org_01HXYZ1234567890ABCDEFGHIJ"),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSDirectoryGroup",
            "id",
            "WorkOSOrganization",
            "id",
            "BELONGS_TO",
            rel_direction_right=True,
        )
        == expected_rels
    )
