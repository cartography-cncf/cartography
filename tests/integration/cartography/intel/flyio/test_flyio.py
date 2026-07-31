from unittest.mock import patch

from cartography.config import Config
import cartography.intel.flyio
import cartography.intel.flyio.apps
import cartography.intel.flyio.certificates
import cartography.intel.flyio.machines
import cartography.intel.flyio.secrets
import cartography.intel.flyio.volumes
from tests.data.flyio.apps import APPS_RESPONSE
from tests.data.flyio.certificates import CERTIFICATES_RESPONSE
from tests.data.flyio.machines import MACHINES_RESPONSE
from tests.data.flyio.secrets import SECRETS_RESPONSE
from tests.data.flyio.volumes import VOLUMES_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_SLUG = "jonathanfemi-example-com"
TEST_APP_ID = "jlyv9r258ew18xrg"
TEST_APP_NAME = "nhmhvxo3b9"
TEST_MACHINE_ID = "90802949c92987"
TEST_SERVICE_ID = f"{TEST_MACHINE_ID}/tcp/8000"


@patch.object(
    cartography.intel.flyio.certificates,
    "get",
    return_value=CERTIFICATES_RESPONSE,
)
@patch.object(
    cartography.intel.flyio.secrets,
    "get",
    return_value=SECRETS_RESPONSE,
)
@patch.object(
    cartography.intel.flyio.volumes,
    "get",
    return_value=VOLUMES_RESPONSE,
)
@patch.object(
    cartography.intel.flyio.machines,
    "get",
    return_value=MACHINES_RESPONSE,
)
@patch.object(
    cartography.intel.flyio.apps,
    "get",
    return_value=APPS_RESPONSE,
)
def test_start_flyio_ingestion(
    mock_apps,
    mock_machines,
    mock_volumes,
    mock_secrets,
    mock_certificates,
    neo4j_session,
):
    # Arrange
    neo4j_session.run(
        """
        MATCH (n)
        WHERE any(label IN labels(n) WHERE label STARTS WITH 'Fly')
        DETACH DELETE n
        """,
    )
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        flyio_token="test-token",
        flyio_org_slug=TEST_ORG_SLUG,
        flyio_base_url="https://api.machines.dev",
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.flyio.start_flyio_ingestion(neo4j_session, config)

    # Assert
    assert check_nodes(
        neo4j_session,
        "FlyOrganization",
        ["id", "name", "slug", "internal_numeric_id"],
    ) == {
        (TEST_ORG_SLUG, "jonathanfemi@example.com", TEST_ORG_SLUG, 977819),
    }
    assert check_nodes(
        neo4j_session,
        "FlyApp",
        ["id", "name", "status", "machine_count", "volume_count"],
    ) == {
        (TEST_APP_ID, TEST_APP_NAME, "deployed", 3, 1),
    }
    assert check_nodes(
        neo4j_session,
        "FlyMachine",
        ["id", "name", "state", "region", "image_repository", "memory_mb"],
    ) == {
        (TEST_MACHINE_ID, "dry-rain-8738", "started", "lhr", TEST_APP_NAME, 1024),
    }
    assert check_nodes(
        neo4j_session,
        "FlyVolume",
        ["id", "name", "encrypted", "attached_machine_id"],
    ) == {
        ("vol_vlykw0x679gyz5p4", "cartography_test_data", True, TEST_MACHINE_ID),
    }
    assert check_nodes(neo4j_session, "FlySecret", ["id", "name"]) == {
        (f"{TEST_APP_ID}/SECRET_KEY", "SECRET_KEY"),
        (f"{TEST_APP_ID}/FLY_API_TOKEN", "FLY_API_TOKEN"),
    }
    certificate = neo4j_session.run(
        """
        MATCH (c:FlyCertificate {id: $id})
        RETURN c.hostname AS hostname,
               c.status AS status,
               c.certificate_authorities AS certificate_authorities,
               c.sources AS sources
        """,
        id=f"{TEST_APP_ID}/www.example.com",
    ).single()
    assert certificate is not None
    assert certificate["hostname"] == "www.example.com"
    assert certificate["status"] == "active"
    assert certificate["certificate_authorities"] == ["lets_encrypt"]
    assert certificate["sources"] == ["fly"]
    assert check_nodes(neo4j_session, "Tenant", ["id", "_ont_name"]) == {
        (TEST_ORG_SLUG, "jonathanfemi@example.com"),
        (TEST_APP_ID, TEST_APP_NAME),
    }
    assert check_nodes(
        neo4j_session,
        "ComputeInstance",
        ["id", "_ont_name", "_ont_region", "_ont_state", "_ont_source"],
    ) == {
        (TEST_MACHINE_ID, "dry-rain-8738", "lhr", "started", "flyio"),
    }
    assert check_nodes(
        neo4j_session,
        "BlockStorage",
        ["id", "_ont_name", "_ont_size_gb", "_ont_encrypted", "_ont_source"],
    ) == {
        ("vol_vlykw0x679gyz5p4", "cartography_test_data", 1, True, "flyio"),
    }
    assert check_nodes(neo4j_session, "Secret", ["id", "_ont_name"]) == {
        (f"{TEST_APP_ID}/SECRET_KEY", "SECRET_KEY"),
        (f"{TEST_APP_ID}/FLY_API_TOKEN", "FLY_API_TOKEN"),
    }
    assert check_nodes(
        neo4j_session,
        "Certificate",
        ["id", "_ont_domain", "_ont_source"],
    ) == {
        (f"{TEST_APP_ID}/www.example.com", "www.example.com", "flyio"),
    }
    assert check_nodes(
        neo4j_session,
        "FlyMachineService",
        ["id", "protocol", "internal_port"],
    ) == {
        (TEST_SERVICE_ID, "tcp", 8000),
    }
    service_ports = neo4j_session.run(
        """
        MATCH (p:FlyMachineServicePort)
        RETURN p.id AS id,
               p.port AS port,
               p.handlers AS handlers,
               p.force_https AS force_https
        ORDER BY port
        """,
    )
    assert [dict(port) for port in service_ports] == [
        {
            "id": f"{TEST_SERVICE_ID}/80",
            "port": 80,
            "handlers": ["http"],
            "force_https": True,
        },
        {
            "id": f"{TEST_SERVICE_ID}/443",
            "port": 443,
            "handlers": ["http", "tls"],
            "force_https": None,
        },
    ]

    assert check_rels(
        neo4j_session,
        "FlyApp",
        "id",
        "FlyOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_APP_ID, TEST_ORG_SLUG),
    }
    assert check_rels(
        neo4j_session,
        "FlyMachine",
        "id",
        "FlyApp",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_MACHINE_ID, TEST_APP_ID),
    }
    assert check_rels(
        neo4j_session,
        "FlyVolume",
        "id",
        "FlyMachine",
        "id",
        "MOUNTS",
        rel_direction_right=False,
    ) == {
        ("vol_vlykw0x679gyz5p4", TEST_MACHINE_ID),
    }
    assert check_rels(
        neo4j_session,
        "FlyMachineService",
        "id",
        "FlyMachine",
        "id",
        "EXPOSE",
        rel_direction_right=False,
    ) == {
        (TEST_SERVICE_ID, TEST_MACHINE_ID),
    }
    assert check_rels(
        neo4j_session,
        "FlyMachineServicePort",
        "id",
        "FlyMachineService",
        "id",
        "EXPOSE",
        rel_direction_right=False,
    ) == {
        (f"{TEST_SERVICE_ID}/80", TEST_SERVICE_ID),
        (f"{TEST_SERVICE_ID}/443", TEST_SERVICE_ID),
    }
