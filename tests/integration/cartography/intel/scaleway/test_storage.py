from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.storage.snapshots
import cartography.intel.scaleway.storage.volumes
import tests.data.scaleway.storages
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"


def _ensure_local_neo4j_has_test_volumes(neo4j_session):
    data = cartography.intel.scaleway.storage.volumes.transform_volumes(
        tests.data.scaleway.storages.SCALEWAY_VOLUMES
    )
    cartography.intel.scaleway.storage.volumes.load_volumes(
        neo4j_session, data, TEST_UPDATE_TAG
    )


@patch.object(
    cartography.intel.scaleway.storage.volumes,
    "get",
    return_value=tests.data.scaleway.storages.SCALEWAY_VOLUMES,
)
def test_load_scaleway_volumes(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)

    # Act
    cartography.intel.scaleway.storage.volumes.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert Volumes exist
    expected_nodes = {
        (
            "7c37b328-247c-4668-8ee1-701a3a3cc2e4",
            "Ubuntu 24.04 Noble Numbat",
        )
    }
    assert (
        check_nodes(neo4j_session, "ScalewayVolume", ["id", "name"]) == expected_nodes
    )

    # Assert Project exists
    assert check_nodes(neo4j_session, "ScalewayProject", ["id"]) == {(TEST_PROJECT_ID,)}

    # Assert volumes are linked to the project
    expected_rels = {
        (
            "7c37b328-247c-4668-8ee1-701a3a3cc2e4",
            TEST_PROJECT_ID,
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayVolume",
            "id",
            "ScalewayProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )


@patch.object(
    cartography.intel.scaleway.storage.snapshots,
    "get",
    return_value=tests.data.scaleway.storages.SCALEWAY_SNAPSHOTS,
)
def test_load_scaleway_snapshots(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    _ensure_local_neo4j_has_test_volumes(neo4j_session)

    # Act
    cartography.intel.scaleway.storage.snapshots.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert Snapshots exist
    expected_nodes = {
        (
            "7c689d68-94a7-4498-9a87-d83077859519",
            "image-gateway_snap_0",
        )
    }
    assert (
        check_nodes(neo4j_session, "ScalewayVolumeSnapshot", ["id", "name"])
        == expected_nodes
    )

    # Assert Project exists
    assert check_nodes(neo4j_session, "ScalewayProject", ["id"]) == {(TEST_PROJECT_ID,)}

    # Assert snapshots are linked to the project
    expected_rels = {
        (
            "7c689d68-94a7-4498-9a87-d83077859519",
            TEST_PROJECT_ID,
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayVolumeSnapshot",
            "id",
            "ScalewayProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert snapshots are linked to volumes
    expected_volume_rels = {
        (
            "7c689d68-94a7-4498-9a87-d83077859519",
            "7c37b328-247c-4668-8ee1-701a3a3cc2e4",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayVolumeSnapshot",
            "id",
            "ScalewayVolume",
            "id",
            "HAS",
            rel_direction_right=False,
        )
        == expected_volume_rels
    )
