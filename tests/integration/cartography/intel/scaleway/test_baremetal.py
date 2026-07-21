from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.baremetal.apple_silicon
import cartography.intel.scaleway.baremetal.dedibox
import cartography.intel.scaleway.baremetal.elastic_metal
import cartography.intel.scaleway.baremetal.flexible_ips
import tests.data.scaleway.baremetal
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"


@patch.object(
    cartography.intel.scaleway.baremetal.elastic_metal,
    "get",
    return_value=tests.data.scaleway.baremetal.SCALEWAY_ELASTIC_METAL_SERVERS,
)
def test_load_scaleway_elastic_metal(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": TEST_ORG_ID}
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)

    # Act
    cartography.intel.scaleway.baremetal.elastic_metal.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert
    assert check_nodes(neo4j_session, "ScalewayElasticMetalServer", ["id", "name"]) == {
        ("11111111-1111-1111-1111-111111111111", "em-demo"),
    }
    assert check_rels(
        neo4j_session,
        "ScalewayElasticMetalServer",
        "id",
        "ScalewayProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("11111111-1111-1111-1111-111111111111", TEST_PROJECT_ID),
    }


@patch.object(
    cartography.intel.scaleway.baremetal.apple_silicon,
    "get",
    return_value=tests.data.scaleway.baremetal.SCALEWAY_APPLE_SILICON_SERVERS,
)
def test_load_scaleway_apple_silicon(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": TEST_ORG_ID}
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)

    # Act
    cartography.intel.scaleway.baremetal.apple_silicon.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert
    assert check_nodes(neo4j_session, "ScalewayAppleSiliconServer", ["id", "name"]) == {
        ("22222222-2222-2222-2222-222222222222", "mac-demo"),
    }
    assert check_rels(
        neo4j_session,
        "ScalewayAppleSiliconServer",
        "id",
        "ScalewayProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("22222222-2222-2222-2222-222222222222", TEST_PROJECT_ID),
    }


@patch.object(
    cartography.intel.scaleway.baremetal.dedibox,
    "get",
    return_value=tests.data.scaleway.baremetal.SCALEWAY_DEDIBOX_SERVERS,
)
def test_load_scaleway_dedibox(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": TEST_ORG_ID}
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)

    # Act
    cartography.intel.scaleway.baremetal.dedibox.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert (id is stringified from the numeric Dedibox identifier)
    assert check_nodes(neo4j_session, "ScalewayDediboxServer", ["id", "hostname"]) == {
        ("12345", "dedibox-demo"),
    }
    # The raw Dedibox ServerStatus "ready" normalizes to the canonical _ont_state.
    assert check_nodes(
        neo4j_session, "ScalewayDediboxServer", ["id", "_ont_state"]
    ) == {
        ("12345", "running"),
    }
    assert check_rels(
        neo4j_session,
        "ScalewayDediboxServer",
        "id",
        "ScalewayProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("12345", TEST_PROJECT_ID),
    }


@patch.object(
    cartography.intel.scaleway.baremetal.elastic_metal,
    "get",
    return_value=tests.data.scaleway.baremetal.SCALEWAY_ELASTIC_METAL_SERVERS,
)
@patch.object(
    cartography.intel.scaleway.baremetal.flexible_ips,
    "get",
    return_value=tests.data.scaleway.baremetal.SCALEWAY_ELASTIC_METAL_FLEXIBLE_IPS,
)
def test_load_scaleway_elastic_metal_flexible_ips(
    _mock_fip_get, _mock_em_get, neo4j_session
):
    # Arrange
    client = Mock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": TEST_ORG_ID}
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    cartography.intel.scaleway.baremetal.elastic_metal.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.scaleway.baremetal.flexible_ips.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert node + project + IDENTIFIES edge to its Elastic Metal server
    assert check_nodes(
        neo4j_session, "ScalewayElasticMetalFlexibleIp", ["id", "ip_address"]
    ) == {
        ("fip00000-0000-0000-0000-000000000001", "51.15.9.9"),
    }
    assert check_rels(
        neo4j_session,
        "ScalewayElasticMetalFlexibleIp",
        "id",
        "ScalewayProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("fip00000-0000-0000-0000-000000000001", TEST_PROJECT_ID),
    }
    assert check_rels(
        neo4j_session,
        "ScalewayElasticMetalFlexibleIp",
        "id",
        "ScalewayElasticMetalServer",
        "id",
        "IDENTIFIES",
        rel_direction_right=True,
    ) == {
        (
            "fip00000-0000-0000-0000-000000000001",
            "11111111-1111-1111-1111-111111111111",
        ),
    }
