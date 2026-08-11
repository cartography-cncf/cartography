from unittest.mock import patch

import cartography.intel.unikraft
import cartography.intel.unikraft.account
import cartography.intel.unikraft.certificates
import cartography.intel.unikraft.instances
import cartography.intel.unikraft.service_groups
import cartography.intel.unikraft.volumes
from cartography.config import Config
from cartography.intel.unikraft.util import METRO_BASE_URLS
from tests.data.unikraft.data import ACCOUNT_QUOTAS_RESPONSE
from tests.data.unikraft.data import CERTIFICATES_RESPONSE
from tests.data.unikraft.data import INSTANCES_RESPONSE
from tests.data.unikraft.data import INSTANCES_RESPONSE_BY_METRO
from tests.data.unikraft.data import SERVICE_GROUPS_RESPONSE
from tests.data.unikraft.data import VOLUMES_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_2 = 223456789
TEST_ACCOUNT_ID = "acct-0001"
TEST_INSTANCE_ID = "inst-0001"
TEST_VOLUME_ID = "vol-0001"
TEST_CERTIFICATE_ID = "cert-0001"
TEST_SERVICE_GROUP_ID = "svc-0001"
TEST_IMAGE_REF = "cartography-test:latest"
# METRO_BASE_URLS is iterated in insertion order and every metro is mocked
# with identical fixture data, so nodes converge and end up stamped with the
# last metro visited.
TEST_LAST_METRO = "sfo"


@patch.object(
    cartography.intel.unikraft.service_groups,
    "get",
    return_value=SERVICE_GROUPS_RESPONSE,
)
@patch.object(
    cartography.intel.unikraft.certificates,
    "get",
    return_value=CERTIFICATES_RESPONSE,
)
@patch.object(
    cartography.intel.unikraft.volumes,
    "get",
    return_value=VOLUMES_RESPONSE,
)
@patch.object(
    cartography.intel.unikraft.instances,
    "get",
    return_value=INSTANCES_RESPONSE,
)
@patch.object(
    cartography.intel.unikraft.account,
    "get_own_quotas",
    return_value=ACCOUNT_QUOTAS_RESPONSE,
)
def test_start_unikraft_ingestion(
    mock_get_quotas,
    mock_get_instances,
    mock_get_volumes,
    mock_get_certificates,
    mock_get_service_groups,
    neo4j_session,
):
    # Arrange
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        unikraft_token="test-token",
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.unikraft.start_unikraft_ingestion(neo4j_session, config)

    # Assert
    assert check_nodes(neo4j_session, "UnikraftAccount", ["id", "status"]) == {
        (TEST_ACCOUNT_ID, "success"),
    }
    assert check_nodes(neo4j_session, "Tenant", ["id", "_ont_name"]) == {
        (TEST_ACCOUNT_ID, TEST_ACCOUNT_ID),
    }
    assert check_nodes(
        neo4j_session, "ComputeInstance", ["id", "_ont_name", "_ont_source"]
    ) == {
        (TEST_INSTANCE_ID, "cartography-test-instance", "unikraft"),
    }
    assert check_nodes(
        neo4j_session,
        "BlockStorage",
        ["id", "_ont_name", "_ont_size_gb", "_ont_source"],
    ) == {
        (TEST_VOLUME_ID, "cartography-test-volume", 1, "unikraft"),
    }
    assert check_nodes(
        neo4j_session, "Certificate", ["id", "_ont_domain", "_ont_source"]
    ) == {
        (TEST_CERTIFICATE_ID, "www.example.com", "unikraft"),
    }
    assert check_nodes(
        neo4j_session, "LoadBalancer", ["id", "_ont_name", "_ont_source"]
    ) == {
        (TEST_SERVICE_GROUP_ID, "cartography-test-service", "unikraft"),
    }
    assert check_nodes(
        neo4j_session,
        "UnikraftInstance",
        ["id", "name", "state", "image", "metro"],
    ) == {
        (
            TEST_INSTANCE_ID,
            "cartography-test-instance",
            "running",
            TEST_IMAGE_REF,
            TEST_LAST_METRO,
        ),
    }
    assert check_nodes(
        neo4j_session,
        "UnikraftVolume",
        ["id", "name", "size_mb", "size_gb", "metro"],
    ) == {
        (TEST_VOLUME_ID, "cartography-test-volume", 1024, 1, TEST_LAST_METRO),
    }
    assert check_nodes(
        neo4j_session,
        "UnikraftCertificate",
        ["id", "common_name", "metro"],
    ) == {
        (TEST_CERTIFICATE_ID, "www.example.com", TEST_LAST_METRO),
    }
    assert check_nodes(
        neo4j_session,
        "UnikraftServiceGroup",
        ["id", "name", "metro", "primary_domain"],
    ) == {
        (
            TEST_SERVICE_GROUP_ID,
            "cartography-test-service",
            TEST_LAST_METRO,
            "www.example.com",
        ),
    }

    assert check_rels(
        neo4j_session,
        "UnikraftInstance",
        "id",
        "UnikraftAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_INSTANCE_ID, TEST_ACCOUNT_ID),
    }
    assert check_rels(
        neo4j_session,
        "UnikraftInstance",
        "id",
        "UnikraftVolume",
        "id",
        "MOUNTS",
    ) == {
        (TEST_INSTANCE_ID, TEST_VOLUME_ID),
    }
    assert check_rels(
        neo4j_session,
        "UnikraftServiceGroup",
        "id",
        "UnikraftInstance",
        "id",
        "EXPOSES",
    ) == {
        (TEST_SERVICE_GROUP_ID, TEST_INSTANCE_ID),
    }
    assert check_rels(
        neo4j_session,
        "UnikraftServiceGroup",
        "id",
        "UnikraftCertificate",
        "id",
        "SECURED_BY",
    ) == {
        (TEST_SERVICE_GROUP_ID, TEST_CERTIFICATE_ID),
    }

    # Act: re-sync with every resource removed upstream, under a new update tag.
    mock_get_instances.return_value = []
    mock_get_volumes.return_value = []
    mock_get_certificates.return_value = []
    mock_get_service_groups.return_value = []
    config.update_tag = TEST_UPDATE_TAG_2
    cartography.intel.unikraft.start_unikraft_ingestion(neo4j_session, config)

    # Assert: cleanup removed every stale child node and relationship, but the
    # account (still returned by the mocked quotas call) survives.
    assert check_nodes(neo4j_session, "UnikraftAccount", ["id"]) == {
        (TEST_ACCOUNT_ID,),
    }
    assert check_nodes(neo4j_session, "UnikraftInstance", ["id"]) == set()
    assert check_nodes(neo4j_session, "UnikraftVolume", ["id"]) == set()
    assert check_nodes(neo4j_session, "UnikraftCertificate", ["id"]) == set()
    assert check_nodes(neo4j_session, "UnikraftServiceGroup", ["id"]) == set()
    assert (
        check_rels(
            neo4j_session,
            "UnikraftInstance",
            "id",
            "UnikraftAccount",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == set()
    )


def test_unikraft_instances_distinct_per_metro(neo4j_session):
    """
    Two metros reporting different real instances (distinct UUIDs) must land
    as two separate nodes, not collapse into one the way
    test_start_unikraft_ingestion's identical-fixture-across-metros setup
    does. This assumes Unikraft UUIDs are globally unique across metros
    (standard UUIDv4 practice); if that assumption is ever wrong, this is
    the behavior that would silently merge two distinct real resources into
    one graph node.
    """
    # Arrange
    neo4j_session.run(
        "MATCH (n:UnikraftInstance) DETACH DELETE n",
    )

    def get_side_effect(session, base_url):
        for metro, metro_base_url in METRO_BASE_URLS.items():
            if base_url == metro_base_url:
                return INSTANCES_RESPONSE_BY_METRO.get(metro, [])
        return []

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": TEST_ACCOUNT_ID,
    }

    with patch.object(
        cartography.intel.unikraft.instances,
        "get",
        side_effect=get_side_effect,
    ):
        # Act
        cartography.intel.unikraft.instances.sync(
            neo4j_session,
            None,
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

    # Assert
    assert check_nodes(
        neo4j_session,
        "UnikraftInstance",
        ["id", "name", "metro"],
    ) == {
        ("inst-fra-0001", "cartography-test-instance-fra", "fra"),
        ("inst-dal-0001", "cartography-test-instance-dal", "dal"),
    }
