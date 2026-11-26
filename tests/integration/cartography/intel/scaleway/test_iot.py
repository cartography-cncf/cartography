from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.iot.hubs
from tests.data.scaleway.iot import SCALEWAY_IOT_DEVICES
from tests.data.scaleway.iot import SCALEWAY_IOT_HUBS
from tests.data.scaleway.iot import TEST_DEVICE_ID
from tests.data.scaleway.iot import TEST_HUB_ID
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"


@patch.object(
    cartography.intel.scaleway.iot.hubs,
    "get",
    return_value=(SCALEWAY_IOT_HUBS, {TEST_HUB_ID: SCALEWAY_IOT_DEVICES}),
)
def test_load_scaleway_iot(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)

    # Act
    cartography.intel.scaleway.iot.hubs.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert nodes
    assert check_nodes(neo4j_session, "ScalewayIotHub", ["id", "name", "status"]) == {
        (TEST_HUB_ID, "demo-hub", "ready"),
    }
    assert check_nodes(
        neo4j_session, "ScalewayIotDevice", ["id", "name", "status"]
    ) == {
        (TEST_DEVICE_ID, "demo-device", "enabled"),
    }

    # Project ownership
    assert check_rels(
        neo4j_session,
        "ScalewayIotHub",
        "id",
        "ScalewayProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(TEST_HUB_ID, TEST_PROJECT_ID)}
    assert check_rels(
        neo4j_session,
        "ScalewayIotDevice",
        "id",
        "ScalewayProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(TEST_DEVICE_ID, TEST_PROJECT_ID)}

    # Hub -> Device
    assert check_rels(
        neo4j_session,
        "ScalewayIotHub",
        "id",
        "ScalewayIotDevice",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {(TEST_HUB_ID, TEST_DEVICE_ID)}


@patch.object(
    cartography.intel.scaleway.iot.hubs,
    "get",
    return_value=(SCALEWAY_IOT_HUBS, {TEST_HUB_ID: SCALEWAY_IOT_DEVICES}),
)
def test_scaleway_iot_cleanup_removes_stale_resources(mock_get, neo4j_session):
    # Arrange: one full sync, then everything upstream is gone.
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    cartography.intel.scaleway.iot.hubs.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    mock_get.return_value = ([], {})
    common_job_parameters["UPDATE_TAG"] = TEST_UPDATE_TAG + 1
    cartography.intel.scaleway.iot.hubs.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG + 1,
    )

    # Assert
    assert check_nodes(neo4j_session, "ScalewayIotHub", ["id"]) == set()
    assert check_nodes(neo4j_session, "ScalewayIotDevice", ["id"]) == set()
