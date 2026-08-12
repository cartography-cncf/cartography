from unittest.mock import patch

import cartography.intel.render
import cartography.intel.render.customdomains
import cartography.intel.render.dedicatedips
import cartography.intel.render.disks
import cartography.intel.render.envgroups
import cartography.intel.render.environments
import cartography.intel.render.keyvalue
import cartography.intel.render.postgres
import cartography.intel.render.projects
import cartography.intel.render.secretfiles
import cartography.intel.render.services
import cartography.intel.render.tenants
from cartography.config import Config
from tests.data.render.data import CUSTOM_DOMAINS_RESPONSE
from tests.data.render.data import DEDICATED_IPS_RESPONSE
from tests.data.render.data import DISKS_RESPONSE
from tests.data.render.data import ENV_GROUPS_RESPONSE
from tests.data.render.data import ENVIRONMENTS_RESPONSE
from tests.data.render.data import KEY_VALUE_RESPONSE
from tests.data.render.data import OWNERS_RESPONSE
from tests.data.render.data import POSTGRES_RESPONSE
from tests.data.render.data import PROJECTS_RESPONSE
from tests.data.render.data import SECRET_FILES_RESPONSE
from tests.data.render.data import SERVICES_RESPONSE
from tests.data.render.data import TEST_OWNER_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_2 = 223456789
TEST_PROJECT_ID = "prj-test001"
TEST_ENVIRONMENT_ID = "evn-test001"
TEST_SERVICE_ID = "srv-test001"
TEST_POSTGRES_ID = "dpg-test001"
TEST_DISK_ID = "dsk-test001"
TEST_CUSTOM_DOMAIN_ID = "cdm-test001"
TEST_SECRET_FILE_ID = f"{TEST_SERVICE_ID}/.env"
TEST_KEY_VALUE_ID = "red-test001"
TEST_ENV_GROUP_ID = "evg-test001"
TEST_DEDICATED_IP_ID = "dip-test001"


@patch.object(
    cartography.intel.render.envgroups,
    "get",
    return_value=ENV_GROUPS_RESPONSE,
)
@patch.object(
    cartography.intel.render.dedicatedips,
    "get",
    return_value=DEDICATED_IPS_RESPONSE,
)
@patch.object(
    cartography.intel.render.keyvalue,
    "get",
    return_value=KEY_VALUE_RESPONSE,
)
@patch.object(
    cartography.intel.render.secretfiles,
    "get",
    return_value=SECRET_FILES_RESPONSE,
)
@patch.object(
    cartography.intel.render.customdomains,
    "get",
    return_value=CUSTOM_DOMAINS_RESPONSE,
)
@patch.object(
    cartography.intel.render.disks,
    "get",
    return_value=DISKS_RESPONSE,
)
@patch.object(
    cartography.intel.render.postgres,
    "get",
    return_value=POSTGRES_RESPONSE,
)
@patch.object(
    cartography.intel.render.services,
    "get",
    return_value=SERVICES_RESPONSE,
)
@patch.object(
    cartography.intel.render.environments,
    "get",
    return_value=ENVIRONMENTS_RESPONSE,
)
@patch.object(
    cartography.intel.render.projects,
    "get",
    return_value=PROJECTS_RESPONSE,
)
@patch.object(
    cartography.intel.render.tenants,
    "get",
    return_value=OWNERS_RESPONSE,
)
def test_start_render_ingestion(
    mock_get_owners,
    mock_get_projects,
    mock_get_environments,
    mock_get_services,
    mock_get_postgres,
    mock_get_disks,
    mock_get_custom_domains,
    mock_get_secret_files,
    mock_get_key_value,
    mock_get_dedicated_ips,
    mock_get_env_groups,
    neo4j_session,
):
    # Arrange
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        render_api_key="test-api-key",
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.render.start_render_ingestion(neo4j_session, config)

    # Assert nodes
    assert check_nodes(neo4j_session, "RenderTenant", ["id", "name", "type"]) == {
        (TEST_OWNER_ID, "cartography-test-workspace", "team"),
    }
    assert check_nodes(neo4j_session, "Tenant", ["id", "_ont_name"]) == {
        (TEST_OWNER_ID, "cartography-test-workspace"),
    }
    assert check_nodes(neo4j_session, "RenderProject", ["id", "name"]) == {
        (TEST_PROJECT_ID, "cartography-test-project"),
    }
    assert check_nodes(
        neo4j_session,
        "RenderEnvironment",
        ["id", "name", "project_id"],
    ) == {
        (TEST_ENVIRONMENT_ID, "production", TEST_PROJECT_ID),
    }
    assert check_nodes(
        neo4j_session,
        "RenderService",
        ["id", "name", "environment_id"],
    ) == {
        (TEST_SERVICE_ID, "cartography-test-service", TEST_ENVIRONMENT_ID),
    }
    assert check_nodes(
        neo4j_session, "ComputeInstance", ["id", "_ont_name", "_ont_source"]
    ) == {
        (TEST_SERVICE_ID, "cartography-test-service", "render"),
    }
    assert check_nodes(
        neo4j_session,
        "RenderPostgres",
        ["id", "name", "database_name", "environment_id"],
    ) == {
        (
            TEST_POSTGRES_ID,
            "cartography-test-db",
            "cartography_test",
            TEST_ENVIRONMENT_ID,
        ),
    }
    assert check_nodes(
        neo4j_session,
        "RenderDisk",
        ["id", "name", "size_gb", "mount_path", "service_id"],
    ) == {
        (TEST_DISK_ID, "data", 1, "/data", TEST_SERVICE_ID),
    }
    assert check_nodes(
        neo4j_session,
        "BlockStorage",
        ["id", "_ont_name", "_ont_size_gb", "_ont_source"],
    ) == {
        (TEST_DISK_ID, "data", 1, "render"),
    }
    assert check_nodes(
        neo4j_session,
        "RenderCustomDomain",
        ["id", "name", "verification_status", "service_id"],
    ) == {
        (TEST_CUSTOM_DOMAIN_ID, "www.example.com", "verified", TEST_SERVICE_ID),
    }
    assert check_nodes(
        neo4j_session,
        "RenderSecretFile",
        ["id", "name", "service_id"],
    ) == {
        (TEST_SECRET_FILE_ID, ".env", TEST_SERVICE_ID),
    }
    assert check_nodes(neo4j_session, "Secret", ["id", "_ont_name", "_ont_source"]) == {
        (TEST_SECRET_FILE_ID, ".env", "render"),
    }
    # The secret file's plaintext content must never reach the graph.
    secret_file_props = neo4j_session.run(
        "MATCH (n:RenderSecretFile {id: $id}) RETURN properties(n) AS props",
        id=TEST_SECRET_FILE_ID,
    ).single()["props"]
    assert "content" not in secret_file_props
    assert check_nodes(
        neo4j_session,
        "RenderKeyValue",
        ["id", "name", "plan", "environment_id"],
    ) == {
        (TEST_KEY_VALUE_ID, "cartography-test-kv", "free", TEST_ENVIRONMENT_ID),
    }
    assert check_nodes(neo4j_session, "Database", ["id", "_ont_name", "_ont_type"]) == {
        (TEST_POSTGRES_ID, "cartography-test-db", "postgres"),
        (TEST_KEY_VALUE_ID, "cartography-test-kv", "redis"),
    }
    assert check_nodes(
        neo4j_session,
        "RenderEnvGroup",
        ["id", "name", "environment_id"],
    ) == {
        (TEST_ENV_GROUP_ID, "cartography-test-env-group", TEST_ENVIRONMENT_ID),
    }
    assert check_nodes(
        neo4j_session,
        "RenderDedicatedIP",
        ["id", "name", "region", "status"],
    ) == {
        (TEST_DEDICATED_IP_ID, "cartography-test-dedicated-ip", "oregon", "RUNNING"),
    }
    assert check_nodes(
        neo4j_session,
        "RenderIPAllowRule",
        ["id", "cidr_block", "resource_id", "resource_type"],
    ) == {
        (
            f"{TEST_ENVIRONMENT_ID}/0.0.0.0/0",
            "0.0.0.0/0",
            TEST_ENVIRONMENT_ID,
            "RenderEnvironment",
        ),
        (
            f"{TEST_SERVICE_ID}/203.0.113.0/24",
            "203.0.113.0/24",
            TEST_SERVICE_ID,
            "RenderService",
        ),
        (
            f"{TEST_POSTGRES_ID}/203.0.113.0/24",
            "203.0.113.0/24",
            TEST_POSTGRES_ID,
            "RenderPostgres",
        ),
        (
            f"{TEST_KEY_VALUE_ID}/0.0.0.0/0",
            "0.0.0.0/0",
            TEST_KEY_VALUE_ID,
            "RenderKeyValue",
        ),
    }

    # Assert relationships
    assert check_rels(
        neo4j_session,
        "RenderProject",
        "id",
        "RenderTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_PROJECT_ID, TEST_OWNER_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderEnvironment",
        "id",
        "RenderTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_ENVIRONMENT_ID, TEST_OWNER_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderEnvironment",
        "id",
        "RenderProject",
        "id",
        "CONTAINS",
        rel_direction_right=False,
    ) == {
        (TEST_ENVIRONMENT_ID, TEST_PROJECT_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderService",
        "id",
        "RenderTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_SERVICE_ID, TEST_OWNER_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderService",
        "id",
        "RenderEnvironment",
        "id",
        "CONTAINS",
        rel_direction_right=False,
    ) == {
        (TEST_SERVICE_ID, TEST_ENVIRONMENT_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderPostgres",
        "id",
        "RenderTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_POSTGRES_ID, TEST_OWNER_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderPostgres",
        "id",
        "RenderEnvironment",
        "id",
        "CONTAINS",
        rel_direction_right=False,
    ) == {
        (TEST_POSTGRES_ID, TEST_ENVIRONMENT_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderDisk",
        "id",
        "RenderTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_DISK_ID, TEST_OWNER_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderDisk",
        "id",
        "RenderService",
        "id",
        "MOUNTS",
        rel_direction_right=False,
    ) == {
        (TEST_DISK_ID, TEST_SERVICE_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderCustomDomain",
        "id",
        "RenderTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_CUSTOM_DOMAIN_ID, TEST_OWNER_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderCustomDomain",
        "id",
        "RenderService",
        "id",
        "HAS_DOMAIN",
        rel_direction_right=False,
    ) == {
        (TEST_CUSTOM_DOMAIN_ID, TEST_SERVICE_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderSecretFile",
        "id",
        "RenderTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_SECRET_FILE_ID, TEST_OWNER_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderSecretFile",
        "id",
        "RenderService",
        "id",
        "USES_SECRET",
        rel_direction_right=False,
    ) == {
        (TEST_SECRET_FILE_ID, TEST_SERVICE_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderKeyValue",
        "id",
        "RenderTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_KEY_VALUE_ID, TEST_OWNER_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderKeyValue",
        "id",
        "RenderEnvironment",
        "id",
        "CONTAINS",
        rel_direction_right=False,
    ) == {
        (TEST_KEY_VALUE_ID, TEST_ENVIRONMENT_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderEnvGroup",
        "id",
        "RenderTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_ENV_GROUP_ID, TEST_OWNER_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderEnvGroup",
        "id",
        "RenderEnvironment",
        "id",
        "CONTAINS",
        rel_direction_right=False,
    ) == {
        (TEST_ENV_GROUP_ID, TEST_ENVIRONMENT_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderEnvGroup",
        "id",
        "RenderService",
        "id",
        "LINKED_TO",
        rel_direction_right=True,
    ) == {
        (TEST_ENV_GROUP_ID, TEST_SERVICE_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderIPAllowRule",
        "id",
        "RenderTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (f"{TEST_ENVIRONMENT_ID}/0.0.0.0/0", TEST_OWNER_ID),
        (f"{TEST_SERVICE_ID}/203.0.113.0/24", TEST_OWNER_ID),
        (f"{TEST_POSTGRES_ID}/203.0.113.0/24", TEST_OWNER_ID),
        (f"{TEST_KEY_VALUE_ID}/0.0.0.0/0", TEST_OWNER_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderIPAllowRule",
        "id",
        "RenderEnvironment",
        "id",
        "GOVERNS",
        rel_direction_right=False,
    ) == {
        (f"{TEST_ENVIRONMENT_ID}/0.0.0.0/0", TEST_ENVIRONMENT_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderIPAllowRule",
        "id",
        "RenderService",
        "id",
        "GOVERNS",
        rel_direction_right=False,
    ) == {
        (f"{TEST_SERVICE_ID}/203.0.113.0/24", TEST_SERVICE_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderIPAllowRule",
        "id",
        "RenderPostgres",
        "id",
        "GOVERNS",
        rel_direction_right=False,
    ) == {
        (f"{TEST_POSTGRES_ID}/203.0.113.0/24", TEST_POSTGRES_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderIPAllowRule",
        "id",
        "RenderKeyValue",
        "id",
        "GOVERNS",
        rel_direction_right=False,
    ) == {
        (f"{TEST_KEY_VALUE_ID}/0.0.0.0/0", TEST_KEY_VALUE_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderDedicatedIP",
        "id",
        "RenderTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_DEDICATED_IP_ID, TEST_OWNER_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderDedicatedIP",
        "id",
        "RenderEnvironment",
        "id",
        "APPLIES_TO",
        rel_direction_right=True,
    ) == {
        (TEST_DEDICATED_IP_ID, TEST_ENVIRONMENT_ID),
    }


@patch.object(cartography.intel.render.envgroups, "get", return_value=[])
@patch.object(cartography.intel.render.dedicatedips, "get", return_value=[])
@patch.object(cartography.intel.render.keyvalue, "get", return_value=[])
@patch.object(cartography.intel.render.secretfiles, "get", return_value=[])
@patch.object(cartography.intel.render.customdomains, "get", return_value=[])
@patch.object(cartography.intel.render.disks, "get", return_value=[])
@patch.object(cartography.intel.render.postgres, "get", return_value=[])
@patch.object(cartography.intel.render.services, "get", return_value=[])
@patch.object(cartography.intel.render.environments, "get", return_value=[])
@patch.object(cartography.intel.render.projects, "get", return_value=[])
@patch.object(
    cartography.intel.render.tenants,
    "get",
    return_value=OWNERS_RESPONSE,
)
def test_render_cleanup_removes_stale_resources(
    mock_get_owners,
    mock_get_projects,
    mock_get_environments,
    mock_get_services,
    mock_get_postgres,
    mock_get_disks,
    mock_get_custom_domains,
    mock_get_secret_files,
    mock_get_key_value,
    mock_get_dedicated_ips,
    mock_get_env_groups,
    neo4j_session,
):
    """
    Resources present in one sync run must be removed by a later run that no longer sees
    them, so a decommissioned Render resource doesn't linger in the graph forever.
    """
    # Arrange: first sync loads a project, then a second run with an empty provider
    # response should clean it up.
    mock_get_projects.return_value = PROJECTS_RESPONSE
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        render_api_key="test-api-key",
        update_tag=TEST_UPDATE_TAG,
    )
    cartography.intel.render.start_render_ingestion(neo4j_session, config)
    assert check_nodes(neo4j_session, "RenderProject", ["id"]) == {(TEST_PROJECT_ID,)}

    # Act: second sync sees no projects for this workspace.
    mock_get_projects.return_value = []
    config.update_tag = TEST_UPDATE_TAG_2
    cartography.intel.render.start_render_ingestion(neo4j_session, config)

    # Assert
    assert check_nodes(neo4j_session, "RenderProject", ["id"]) == set()
    assert check_nodes(neo4j_session, "RenderTenant", ["id"]) == {(TEST_OWNER_ID,)}
