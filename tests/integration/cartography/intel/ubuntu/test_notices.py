from unittest.mock import patch

import cartography.intel.ubuntu.cves
import cartography.intel.ubuntu.notices
import tests.data.ubuntu.cves
import tests.data.ubuntu.notices
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_API_URL = "https://fake-ubuntu-api.example.com"


def _load_cves_first(neo4j_session):
    """Load CVE nodes so that notice-to-CVE relationships can be created."""
    with patch.object(
        cartography.intel.ubuntu.cves,
        "get",
        return_value=tests.data.ubuntu.cves.UBUNTU_CVES_RESPONSE,
    ):
        cartography.intel.ubuntu.cves.sync(
            neo4j_session,
            TEST_API_URL,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG},
        )


@patch.object(
    cartography.intel.ubuntu.notices,
    "get",
    return_value=tests.data.ubuntu.notices.UBUNTU_NOTICES_RESPONSE,
)
def test_sync_ubuntu_notices(mock_api, neo4j_session):
    """
    Ensure that Ubuntu Security Notices are loaded correctly.
    """
    # Arrange: load CVEs first so relationships can be created
    _load_cves_first(neo4j_session)

    # Act
    cartography.intel.ubuntu.notices.sync(
        neo4j_session,
        TEST_API_URL,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert notice nodes exist
    expected_nodes = {
        ("USN-6600-1", "libfoo vulnerability"),
        ("USN-6700-1", "libbar vulnerability"),
    }
    assert check_nodes(neo4j_session, "UbuntuSecurityNotice", ["id", "title"]) == expected_nodes


@patch.object(
    cartography.intel.ubuntu.notices,
    "get",
    return_value=tests.data.ubuntu.notices.UBUNTU_NOTICES_RESPONSE,
)
def test_sync_ubuntu_notices_cve_relationships(mock_api, neo4j_session):
    """
    Ensure that Notice-to-CVE ADDRESSES relationships are created correctly.
    """
    # Arrange: load CVEs first
    _load_cves_first(neo4j_session)

    # Act
    cartography.intel.ubuntu.notices.sync(
        neo4j_session,
        TEST_API_URL,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert USN-6600-1 addresses CVE-2024-1234 and CVE-2024-5678
    expected_rels = {
        ("USN-6600-1", "CVE-2024-1234"),
        ("USN-6600-1", "CVE-2024-5678"),
        ("USN-6700-1", "CVE-2024-5678"),
    }
    assert (
        check_rels(
            neo4j_session,
            "UbuntuSecurityNotice",
            "id",
            "UbuntuCVE",
            "id",
            "ADDRESSES",
            rel_direction_right=True,
        )
        == expected_rels
    )


@patch.object(
    cartography.intel.ubuntu.notices,
    "get",
    return_value=tests.data.ubuntu.notices.UBUNTU_NOTICES_RESPONSE,
)
def test_sync_ubuntu_notices_cleanup(mock_api, neo4j_session):
    """
    Ensure that stale notice nodes are cleaned up on subsequent syncs.
    """
    # Arrange: load CVEs and notices
    _load_cves_first(neo4j_session)
    cartography.intel.ubuntu.notices.sync(
        neo4j_session,
        TEST_API_URL,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )
    assert len(check_nodes(neo4j_session, "UbuntuSecurityNotice", ["id"])) == 2

    # Act: second sync with only one notice
    new_update_tag = TEST_UPDATE_TAG + 1
    with patch.object(
        cartography.intel.ubuntu.notices,
        "get",
        return_value=[tests.data.ubuntu.notices.UBUNTU_NOTICES_RESPONSE[0]],
    ):
        cartography.intel.ubuntu.notices.sync(
            neo4j_session,
            TEST_API_URL,
            new_update_tag,
            {"UPDATE_TAG": new_update_tag},
        )

    # Assert only one notice remains
    expected_nodes = {("USN-6600-1",)}
    assert check_nodes(neo4j_session, "UbuntuSecurityNotice", ["id"]) == expected_nodes
