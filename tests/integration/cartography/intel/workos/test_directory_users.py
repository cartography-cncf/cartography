from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.workos.directory_users
import tests.data.workos.directory_users
from tests.integration.cartography.intel.workos.test_directories import (
    _ensure_local_neo4j_has_test_directories,
)
from tests.integration.cartography.intel.workos.test_directory_groups import (
    _ensure_local_neo4j_has_test_directory_groups,
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


@patch.object(
    cartography.intel.workos.directory_users,
    "get",
    return_value=tests.data.workos.directory_users.WORKOS_DIRECTORY_USERS,
)
def test_load_workos_directory_users(mock_api, neo4j_session):
    """
    Ensure that directory users actually get loaded
    """
    # Arrange
    _ensure_local_neo4j_has_test_environment(neo4j_session)
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_directories(neo4j_session)
    _ensure_local_neo4j_has_test_directory_groups(neo4j_session)
    client = MagicMock()
    directory_ids = ["dir_01HXYZ1234567890ABCDEFGHIJ"]
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKOS_CLIENT_ID": TEST_CLIENT_ID,
    }

    # Act
    cartography.intel.workos.directory_users.sync(
        neo4j_session,
        client,
        directory_ids,
        common_job_parameters,
    )

    # Assert DirectoryUsers exist
    expected_nodes = {
        ("dirusr_01HXYZ1234567890ABCDEFGHIJ", "hjsimpson@springfield.com"),
        ("dirusr_02HXYZ0987654321ZYXWVUTSRQ", "mbsimpson@springfield.com"),
    }
    assert (
        check_nodes(neo4j_session, "WorkOSDirectoryUser", ["id", "email"])
        == expected_nodes
    )

    # Assert directory users are linked to the environment
    expected_rels = {
        ("dirusr_01HXYZ1234567890ABCDEFGHIJ", TEST_CLIENT_ID),
        ("dirusr_02HXYZ0987654321ZYXWVUTSRQ", TEST_CLIENT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSDirectoryUser",
            "id",
            "WorkOSEnvironment",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert directory users are linked to directories
    expected_rels = {
        ("dir_01HXYZ1234567890ABCDEFGHIJ", "dirusr_01HXYZ1234567890ABCDEFGHIJ"),
        ("dir_01HXYZ1234567890ABCDEFGHIJ", "dirusr_02HXYZ0987654321ZYXWVUTSRQ"),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSDirectory",
            "id",
            "WorkOSDirectoryUser",
            "id",
            "HAS",
            rel_direction_right=True,
        )
        == expected_rels
    )

    # Assert directory users are linked to organizations
    expected_rels = {
        ("dirusr_01HXYZ1234567890ABCDEFGHIJ", "org_01HXYZ1234567890ABCDEFGHIJ"),
        ("dirusr_02HXYZ0987654321ZYXWVUTSRQ", "org_01HXYZ1234567890ABCDEFGHIJ"),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSDirectoryUser",
            "id",
            "WorkOSOrganization",
            "id",
            "BELONGS_TO",
            rel_direction_right=True,
        )
        == expected_rels
    )

    # Assert directory users are linked to groups
    expected_rels = {
        ("dirusr_01HXYZ1234567890ABCDEFGHIJ", "dirgrp_01HXYZ1234567890ABCDEFGHIJ"),
        ("dirusr_02HXYZ0987654321ZYXWVUTSRQ", "dirgrp_02HXYZ0987654321ZYXWVUTSRQ"),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSDirectoryUser",
            "id",
            "WorkOSDirectoryGroup",
            "id",
            "MEMBER_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )
