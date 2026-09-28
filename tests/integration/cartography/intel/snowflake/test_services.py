from unittest.mock import patch

import cartography.intel.snowflake.services
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.image_repositories import SNOWFLAKE_MONORAIL_IMAGE_DIGEST
from tests.data.snowflake.services import SNOWFLAKE_CONTAINERS_BY_SERVICE
from tests.data.snowflake.services import SNOWFLAKE_ENDPOINTS_BY_SERVICE
from tests.data.snowflake.services import SNOWFLAKE_SERVICE_ROLES_BY_SERVICE
from tests.data.snowflake.services import SNOWFLAKE_SERVICES
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.cartography.intel.snowflake.test_compute_pools import (
    _ensure_local_neo4j_has_test_compute_pools,
)
from tests.integration.cartography.intel.snowflake.test_compute_pools import (
    MONORAIL_POOL_ID,
)
from tests.integration.cartography.intel.snowflake.test_external_access_integrations import (
    _ensure_local_neo4j_has_test_external_access_integrations,
)
from tests.integration.cartography.intel.snowflake.test_external_access_integrations import (
    DUFF_API_ACCESS_ID,
)
from tests.integration.cartography.intel.snowflake.test_image_repositories import (
    _ensure_local_neo4j_has_test_images,
)
from tests.integration.cartography.intel.snowflake.test_image_repositories import (
    MONORAIL_IMAGE_ID,
)
from tests.integration.cartography.intel.snowflake.test_schemas import (
    NUCLEAR_PLANT_SCHEMA_ID,
)
from tests.integration.cartography.intel.snowflake.test_schemas import TEST_SCHEMAS
from tests.integration.cartography.intel.snowflake.test_warehouses import (
    _ensure_local_neo4j_has_test_warehouses,
)
from tests.integration.cartography.intel.snowflake.test_warehouses import REACTOR_WH_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

MONORAIL_SERVICE_ID = (
    "SPRINGFIELD.NUCLEAR/service/SPRINGFIELD.NUCLEAR_PLANT.MONORAIL_TELEMETRY"
)
DONUT_JOB_ID = "SPRINGFIELD.NUCLEAR/service/SPRINGFIELD.NUCLEAR_PLANT.DONUT_BACKFILL"
TELEMETRY_CONTAINER_0_ID = (
    "SPRINGFIELD.NUCLEAR/service_container/"
    'SPRINGFIELD.NUCLEAR_PLANT.MONORAIL_TELEMETRY."telemetry"#0'
)
TELEMETRY_CONTAINER_1_ID = (
    "SPRINGFIELD.NUCLEAR/service_container/"
    'SPRINGFIELD.NUCLEAR_PLANT.MONORAIL_TELEMETRY."telemetry"#1'
)
DASHBOARD_ENDPOINT_ID = (
    "SPRINGFIELD.NUCLEAR/service_endpoint/"
    'SPRINGFIELD.NUCLEAR_PLANT.MONORAIL_TELEMETRY."dashboard"'
)
METRICS_ENDPOINT_ID = (
    "SPRINGFIELD.NUCLEAR/service_endpoint/"
    'SPRINGFIELD.NUCLEAR_PLANT.MONORAIL_TELEMETRY."metrics"'
)
DASHBOARD_VIEWER_ROLE_ID = (
    "SPRINGFIELD.NUCLEAR/service_role/"
    "SPRINGFIELD.NUCLEAR_PLANT.MONORAIL_TELEMETRY.DASHBOARD_VIEWER"
)

# The bundles the per-schema listing and the three sub-listings produce together.
TEST_SERVICE_BUNDLES = [
    {
        "database_name": service["database_name"],
        "schema_name": service["schema_name"],
        "service": service,
        "containers": SNOWFLAKE_CONTAINERS_BY_SERVICE[service["name"]],
        "endpoints": SNOWFLAKE_ENDPOINTS_BY_SERVICE[service["name"]],
        "roles": SNOWFLAKE_SERVICE_ROLES_BY_SERVICE[service["name"]],
    }
    for service in SNOWFLAKE_SERVICES
]


@patch.object(
    cartography.intel.snowflake.services,
    "get",
    return_value=(TEST_SERVICE_BUNDLES, True),
)
def test_sync_snowflake_services(mock_get, neo4j_session):
    # Arrange: the pool that hosts the containers, the warehouse the code queries, the
    # egress allow-list it uses and the image it runs are all owned by other syncs.
    _ensure_local_neo4j_has_test_compute_pools(neo4j_session)
    _ensure_local_neo4j_has_test_warehouses(neo4j_session)
    _ensure_local_neo4j_has_test_external_access_integrations(neo4j_session)
    _ensure_local_neo4j_has_test_images(neo4j_session)

    # Act
    complete = cartography.intel.snowflake.services.sync(
        neo4j_session,
        build_test_client(),
        TEST_SCHEMAS,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert
    assert complete is True
    assert check_nodes(
        neo4j_session,
        "SnowflakeService",
        ["id", "name", "status", "compute_pool", "is_job", "query_warehouse"],
    ) == {
        (
            MONORAIL_SERVICE_ID,
            "MONORAIL_TELEMETRY",
            "RUNNING",
            "MONORAIL_POOL",
            False,
            "REACTOR_WH",
        ),
        (DONUT_JOB_ID, "DONUT_BACKFILL", "DONE", "MONORAIL_POOL", True, None),
    }
    assert check_nodes(neo4j_session, "ComputeService", ["id"]) >= {
        (MONORAIL_SERVICE_ID,),
        (DONUT_JOB_ID,),
    }

    # The instance id is part of the container key, so two instances of the same
    # container name are two nodes.
    assert check_nodes(
        neo4j_session,
        "SnowflakeServiceContainer",
        ["id", "name", "instance_id", "image_digest", "restart_count"],
    ) == {
        (
            TELEMETRY_CONTAINER_0_ID,
            "telemetry",
            "0",
            SNOWFLAKE_MONORAIL_IMAGE_DIGEST,
            0,
        ),
        (
            TELEMETRY_CONTAINER_1_ID,
            "telemetry",
            "1",
            SNOWFLAKE_MONORAIL_IMAGE_DIGEST,
            2,
        ),
    }
    assert check_nodes(neo4j_session, "Container", ["id"]) >= {
        (TELEMETRY_CONTAINER_0_ID,),
        (TELEMETRY_CONTAINER_1_ID,),
    }
    # A public endpoint is what makes a service reachable from the internet, so the
    # flag and the ingress URL both land on the node.
    assert check_nodes(
        neo4j_session,
        "SnowflakeServiceEndpoint",
        ["id", "name", "port", "is_public", "ingress_url"],
    ) == {
        (
            DASHBOARD_ENDPOINT_ID,
            "dashboard",
            8080,
            True,
            "monorail-dashboard-ab12345.snowflakecomputing.app",
        ),
        (METRICS_ENDPOINT_ID, "metrics", 9090, False, None),
    }
    assert check_nodes(neo4j_session, "SnowflakeServiceRole", ["id", "name"]) == {
        (DASHBOARD_VIEWER_ROLE_ID, "DASHBOARD_VIEWER")
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeService",
        "id",
        "SnowflakeSchema",
        "id",
        "CONTAINS",
        rel_direction_right=False,
    ) == {
        (MONORAIL_SERVICE_ID, NUCLEAR_PLANT_SCHEMA_ID),
        (DONUT_JOB_ID, NUCLEAR_PLANT_SCHEMA_ID),
    }
    # The canonical workload chain: container -> service -> compute pool.
    assert check_rels(
        neo4j_session,
        "SnowflakeServiceContainer",
        "id",
        "SnowflakeService",
        "id",
        "WORKLOAD_PARENT",
        rel_direction_right=True,
    ) == {
        (TELEMETRY_CONTAINER_0_ID, MONORAIL_SERVICE_ID),
        (TELEMETRY_CONTAINER_1_ID, MONORAIL_SERVICE_ID),
    }
    assert check_rels(
        neo4j_session,
        "SnowflakeService",
        "id",
        "SnowflakeComputePool",
        "id",
        "WORKLOAD_PARENT",
        rel_direction_right=True,
    ) == {
        (MONORAIL_SERVICE_ID, MONORAIL_POOL_ID),
        (DONUT_JOB_ID, MONORAIL_POOL_ID),
    }
    # The query warehouse is a data-plane dependency, distinct from the pool that
    # schedules the containers.
    assert check_rels(
        neo4j_session,
        "SnowflakeService",
        "id",
        "SnowflakeWarehouse",
        "id",
        "USES_WAREHOUSE",
        rel_direction_right=True,
    ) == {(MONORAIL_SERVICE_ID, REACTOR_WH_ID)}
    assert check_rels(
        neo4j_session,
        "SnowflakeService",
        "id",
        "SnowflakeExternalAccessIntegration",
        "id",
        "USES_INTEGRATION",
        rel_direction_right=True,
    ) == {(MONORAIL_SERVICE_ID, DUFF_API_ACCESS_ID)}
    # Matching on the untagged registry path *and* the digest ties running code to the
    # exact image it came from. The seeded repositories hold two copies of this digest,
    # one in PLANT_IMAGES and one promoted into SQUISHEE_IMAGES; a digest-only matcher
    # would attach both containers to both copies and double this set.
    assert check_rels(
        neo4j_session,
        "SnowflakeServiceContainer",
        "id",
        "SnowflakeImage",
        "id",
        "HAS_IMAGE",
        rel_direction_right=True,
    ) == {
        (TELEMETRY_CONTAINER_0_ID, MONORAIL_IMAGE_ID),
        (TELEMETRY_CONTAINER_1_ID, MONORAIL_IMAGE_ID),
    }
    assert check_rels(
        neo4j_session,
        "SnowflakeService",
        "id",
        "SnowflakeServiceEndpoint",
        "id",
        "HAS_ENDPOINT",
        rel_direction_right=True,
    ) == {
        (MONORAIL_SERVICE_ID, DASHBOARD_ENDPOINT_ID),
        (MONORAIL_SERVICE_ID, METRICS_ENDPOINT_ID),
    }
    assert check_rels(
        neo4j_session,
        "SnowflakeService",
        "id",
        "SnowflakeServiceRole",
        "id",
        "HAS_SERVICE_ROLE",
        rel_direction_right=True,
    ) == {(MONORAIL_SERVICE_ID, DASHBOARD_VIEWER_ROLE_ID)}
