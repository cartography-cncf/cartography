from contextlib import ExitStack
from typing import Any
from unittest.mock import patch

import pytest
import requests

import cartography.intel.render
import cartography.intel.render.blueprints
import cartography.intel.render.customdomains
import cartography.intel.render.disks
import cartography.intel.render.envgroups
import cartography.intel.render.environments
import cartography.intel.render.envvars
import cartography.intel.render.headerrules
import cartography.intel.render.keyvalue
import cartography.intel.render.logstream
import cartography.intel.render.postgres
import cartography.intel.render.projects
import cartography.intel.render.registrycredentials
import cartography.intel.render.routes
import cartography.intel.render.secretfiles
import cartography.intel.render.services
import cartography.intel.render.snapshots
import cartography.intel.render.tenants
import cartography.intel.render.workspacemembers
from cartography.config import Config
from tests.data.render.data import BLUEPRINTS_RESPONSE
from tests.data.render.data import CUSTOM_DOMAINS_RESPONSE
from tests.data.render.data import DISKS_RESPONSE
from tests.data.render.data import ENV_GROUPS_RESPONSE
from tests.data.render.data import ENV_VARS_RESPONSE
from tests.data.render.data import ENVIRONMENTS_RESPONSE
from tests.data.render.data import HEADER_RULES_RESPONSE
from tests.data.render.data import KEY_VALUE_RESPONSE
from tests.data.render.data import LATEST_DEPLOY_RESPONSE
from tests.data.render.data import LOG_STREAM_RESPONSE
from tests.data.render.data import OWNERS_RESPONSE
from tests.data.render.data import POSTGRES_RESPONSE
from tests.data.render.data import PROJECTS_RESPONSE
from tests.data.render.data import REGISTRY_CREDENTIALS_RESPONSE
from tests.data.render.data import ROUTES_RESPONSE
from tests.data.render.data import SECRET_FILES_RESPONSE
from tests.data.render.data import SERVICES_RESPONSE
from tests.data.render.data import SNAPSHOTS_RESPONSE
from tests.data.render.data import TEST_OWNER_ID
from tests.data.render.data import WORKSPACE_MEMBERS_RESPONSE
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
TEST_REGISTRY_CREDENTIAL_ID = "crd-test001"
TEST_WORKSPACE_MEMBER_USER_ID = "usr-test001"
TEST_WORKSPACE_MEMBER_ID = f"{TEST_OWNER_ID}:{TEST_WORKSPACE_MEMBER_USER_ID}"
TEST_ENV_VAR_ID = f"{TEST_SERVICE_ID}/DATABASE_URL"
TEST_HEADER_RULE_ID = "hdr-test001"
TEST_ROUTE_ID = "rte-test001"
TEST_SNAPSHOT_ID = f"{TEST_DISK_ID}/2026-01-03T00:00:00Z"
TEST_BLUEPRINT_ID = "bpr-test001"
TEST_SECOND_SERVICE_ID = "srv-test002"
TEST_SECOND_DISK_ID = "dsk-test002"
TEST_SECOND_ENV_VAR_ID = f"{TEST_SECOND_SERVICE_ID}/DATABASE_URL"
TEST_SECOND_SNAPSHOT_ID = f"{TEST_SECOND_DISK_ID}/2026-01-03T00:00:00Z"

# (module, attr, default return value) for every Render resource's get() (+
# services.get_latest_deploy()). Used by _patch_all_resources() below so a test that
# only cares about one resource's failure behavior doesn't need to hand-mock every
# other resource, the way test_start_render_ingestion's stacked decorators do.
_ALL_GET_MOCKS = [
    (cartography.intel.render.tenants, "get", OWNERS_RESPONSE),
    (cartography.intel.render.projects, "get", PROJECTS_RESPONSE),
    (cartography.intel.render.environments, "get", ENVIRONMENTS_RESPONSE),
    (cartography.intel.render.services, "get", SERVICES_RESPONSE),
    (cartography.intel.render.services, "get_latest_deploy", LATEST_DEPLOY_RESPONSE),
    (cartography.intel.render.postgres, "get", POSTGRES_RESPONSE),
    (cartography.intel.render.keyvalue, "get", KEY_VALUE_RESPONSE),
    (cartography.intel.render.disks, "get", DISKS_RESPONSE),
    (cartography.intel.render.customdomains, "get", CUSTOM_DOMAINS_RESPONSE),
    (cartography.intel.render.secretfiles, "get", SECRET_FILES_RESPONSE),
    (cartography.intel.render.envgroups, "get", ENV_GROUPS_RESPONSE),
    (
        cartography.intel.render.registrycredentials,
        "get",
        REGISTRY_CREDENTIALS_RESPONSE,
    ),
    (cartography.intel.render.workspacemembers, "get", WORKSPACE_MEMBERS_RESPONSE),
    (cartography.intel.render.logstream, "get", LOG_STREAM_RESPONSE),
    (cartography.intel.render.snapshots, "get", SNAPSHOTS_RESPONSE),
    (cartography.intel.render.envvars, "get", ENV_VARS_RESPONSE),
    (cartography.intel.render.headerrules, "get", HEADER_RULES_RESPONSE),
    (cartography.intel.render.routes, "get", ROUTES_RESPONSE),
    (cartography.intel.render.blueprints, "get", BLUEPRINTS_RESPONSE),
]


def _patch_all_resources(stack: ExitStack, overrides: dict | None = None) -> None:
    """
    Patch every Render resource's get() (+ services.get_latest_deploy()) with its
    standard successful fixture response.

    :param overrides: {(module, attr): patch.object kwargs} - e.g.
        {(registrycredentials, "get"): {"side_effect": requests.exceptions.HTTPError()}}
        replaces that entry's default `return_value=...` patch with the given kwargs.
    """
    overrides = overrides or {}
    for module, attr, default_return in _ALL_GET_MOCKS:
        if (module, attr) in overrides:
            stack.enter_context(patch.object(module, attr, **overrides[(module, attr)]))
        else:
            stack.enter_context(patch.object(module, attr, return_value=default_return))


def _empty_resource_overrides() -> dict:
    return {
        (cartography.intel.render.projects, "get"): {"return_value": []},
        (cartography.intel.render.environments, "get"): {"return_value": []},
        (cartography.intel.render.services, "get"): {"return_value": []},
        (cartography.intel.render.services, "get_latest_deploy"): {
            "return_value": None
        },
        (cartography.intel.render.postgres, "get"): {"return_value": []},
        (cartography.intel.render.keyvalue, "get"): {"return_value": []},
        (cartography.intel.render.disks, "get"): {"return_value": []},
        (cartography.intel.render.customdomains, "get"): {"return_value": []},
        (cartography.intel.render.secretfiles, "get"): {"return_value": []},
        (cartography.intel.render.envgroups, "get"): {"return_value": []},
        (cartography.intel.render.registrycredentials, "get"): {"return_value": []},
        (cartography.intel.render.workspacemembers, "get"): {"return_value": []},
        (cartography.intel.render.logstream, "get"): {"return_value": None},
        (cartography.intel.render.snapshots, "get"): {"return_value": []},
        (cartography.intel.render.envvars, "get"): {"return_value": []},
        (cartography.intel.render.headerrules, "get"): {"return_value": []},
        (cartography.intel.render.routes, "get"): {"return_value": []},
        (cartography.intel.render.blueprints, "get"): {"return_value": []},
    }


def _two_services_response() -> list[dict[str, Any]]:
    first: dict[str, Any] = SERVICES_RESPONSE[0]
    service_details: dict[str, Any] = dict(first["serviceDetails"])
    disk: dict[str, Any] = dict(service_details["disk"])
    disk["id"] = TEST_SECOND_DISK_ID
    service_details["disk"] = disk
    second: dict[str, Any] = {
        **first,
        "id": TEST_SECOND_SERVICE_ID,
        "name": "cartography-test-service-2",
        "slug": "cartography-test-service-2",
        "dashboardUrl": "https://dashboard.render.com/web/srv-test002",
        "serviceDetails": service_details,
    }
    return [first, second]


def _two_disks_response() -> list[dict[str, Any]]:
    first: dict[str, Any] = DISKS_RESPONSE[0]
    second: dict[str, Any] = {
        **first,
        "id": TEST_SECOND_DISK_ID,
        "name": "data-2",
        "serviceId": TEST_SECOND_SERVICE_ID,
    }
    return [first, second]


@patch.object(
    cartography.intel.render.blueprints,
    "get",
    return_value=BLUEPRINTS_RESPONSE,
)
@patch.object(
    cartography.intel.render.routes,
    "get",
    return_value=ROUTES_RESPONSE,
)
@patch.object(
    cartography.intel.render.headerrules,
    "get",
    return_value=HEADER_RULES_RESPONSE,
)
@patch.object(
    cartography.intel.render.envvars,
    "get",
    return_value=ENV_VARS_RESPONSE,
)
@patch.object(
    cartography.intel.render.snapshots,
    "get",
    return_value=SNAPSHOTS_RESPONSE,
)
@patch.object(
    cartography.intel.render.logstream,
    "get",
    return_value=LOG_STREAM_RESPONSE,
)
@patch.object(
    cartography.intel.render.workspacemembers,
    "get",
    return_value=WORKSPACE_MEMBERS_RESPONSE,
)
@patch.object(
    cartography.intel.render.registrycredentials,
    "get",
    return_value=REGISTRY_CREDENTIALS_RESPONSE,
)
@patch.object(
    cartography.intel.render.envgroups,
    "get",
    return_value=ENV_GROUPS_RESPONSE,
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
    "get_latest_deploy",
    return_value=LATEST_DEPLOY_RESPONSE,
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
    mock_get_latest_deploy,
    mock_get_postgres,
    mock_get_disks,
    mock_get_custom_domains,
    mock_get_secret_files,
    mock_get_key_value,
    mock_get_env_groups,
    mock_get_registry_credentials,
    mock_get_workspace_members,
    mock_get_log_stream,
    mock_get_snapshots,
    mock_get_env_vars,
    mock_get_header_rules,
    mock_get_routes,
    mock_get_blueprints,
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
        (TEST_ENV_VAR_ID, "DATABASE_URL", "render"),
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
    assert check_nodes(
        neo4j_session,
        "RenderRegistryCredential",
        ["id", "name", "registry"],
    ) == {
        (TEST_REGISTRY_CREDENTIAL_ID, "cartography-test-registry-credential", "DOCKER"),
    }
    assert check_nodes(
        neo4j_session,
        "RenderWorkspaceMember",
        ["id", "user_id", "email", "role"],
    ) == {
        (
            TEST_WORKSPACE_MEMBER_ID,
            TEST_WORKSPACE_MEMBER_USER_ID,
            "test-user@example.com",
            "ADMIN",
        ),
    }
    assert check_nodes(
        neo4j_session, "UserAccount", ["id", "_ont_email", "_ont_source"]
    ) == {
        (TEST_WORKSPACE_MEMBER_ID, "test-user@example.com", "render"),
    }
    assert check_nodes(
        neo4j_session,
        "RenderLogStream",
        ["id", "endpoint", "preview"],
    ) == {
        (TEST_OWNER_ID, "https://logs.example.com/ingest", "drop"),
    }
    assert check_nodes(
        neo4j_session,
        "RenderEnvVar",
        ["id", "key", "service_id"],
    ) == {
        (TEST_ENV_VAR_ID, "DATABASE_URL", TEST_SERVICE_ID),
    }
    # The env var's plaintext value must never reach the graph.
    env_var_props = neo4j_session.run(
        "MATCH (n:RenderEnvVar {id: $id}) RETURN properties(n) AS props",
        id=TEST_ENV_VAR_ID,
    ).single()["props"]
    assert "value" not in env_var_props
    assert check_nodes(
        neo4j_session,
        "RenderHeaderRule",
        ["id", "name", "value", "service_id"],
    ) == {
        (TEST_HEADER_RULE_ID, "X-Frame-Options", "DENY", TEST_SERVICE_ID),
    }
    assert check_nodes(
        neo4j_session,
        "RenderRoute",
        ["id", "type", "source", "destination", "service_id"],
    ) == {
        (TEST_ROUTE_ID, "rewrite", "/old-path", "/new-path", TEST_SERVICE_ID),
    }
    assert check_nodes(
        neo4j_session,
        "RenderSnapshot",
        ["id", "disk_id", "instance_id"],
    ) == {
        (TEST_SNAPSHOT_ID, TEST_DISK_ID, TEST_SERVICE_ID),
    }
    assert check_nodes(
        neo4j_session, "Snapshot", ["id", "_ont_name", "_ont_source"]
    ) == {
        (TEST_SNAPSHOT_ID, TEST_SNAPSHOT_ID, "render"),
    }
    assert check_nodes(
        neo4j_session,
        "RenderBlueprint",
        ["id", "name", "status", "auto_sync"],
    ) == {
        (TEST_BLUEPRINT_ID, "cartography-test-blueprint", "created", True),
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
        "RenderRegistryCredential",
        "id",
        "RenderTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_REGISTRY_CREDENTIAL_ID, TEST_OWNER_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderService",
        "id",
        "RenderRegistryCredential",
        "id",
        "USES_CREDENTIAL",
        rel_direction_right=True,
    ) == {
        (TEST_SERVICE_ID, TEST_REGISTRY_CREDENTIAL_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderWorkspaceMember",
        "id",
        "RenderTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_WORKSPACE_MEMBER_ID, TEST_OWNER_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderLogStream",
        "id",
        "RenderTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_OWNER_ID, TEST_OWNER_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderEnvVar",
        "id",
        "RenderTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_ENV_VAR_ID, TEST_OWNER_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderEnvVar",
        "id",
        "RenderService",
        "id",
        "USES_SECRET",
        rel_direction_right=False,
    ) == {
        (TEST_ENV_VAR_ID, TEST_SERVICE_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderHeaderRule",
        "id",
        "RenderTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_HEADER_RULE_ID, TEST_OWNER_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderHeaderRule",
        "id",
        "RenderService",
        "id",
        "HAS_HEADER_RULE",
        rel_direction_right=False,
    ) == {
        (TEST_HEADER_RULE_ID, TEST_SERVICE_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderRoute",
        "id",
        "RenderTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_ROUTE_ID, TEST_OWNER_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderRoute",
        "id",
        "RenderService",
        "id",
        "HAS_ROUTE",
        rel_direction_right=False,
    ) == {
        (TEST_ROUTE_ID, TEST_SERVICE_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderSnapshot",
        "id",
        "RenderTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_SNAPSHOT_ID, TEST_OWNER_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderSnapshot",
        "id",
        "RenderDisk",
        "id",
        "HAS_SNAPSHOT",
        rel_direction_right=False,
    ) == {
        (TEST_SNAPSHOT_ID, TEST_DISK_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderBlueprint",
        "id",
        "RenderTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_BLUEPRINT_ID, TEST_OWNER_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderBlueprint",
        "id",
        "RenderService",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {
        (TEST_BLUEPRINT_ID, TEST_SERVICE_ID),
    }


@patch.object(cartography.intel.render.blueprints, "get", return_value=[])
@patch.object(cartography.intel.render.routes, "get", return_value=[])
@patch.object(cartography.intel.render.headerrules, "get", return_value=[])
@patch.object(cartography.intel.render.envvars, "get", return_value=[])
@patch.object(cartography.intel.render.snapshots, "get", return_value=[])
@patch.object(cartography.intel.render.logstream, "get", return_value=None)
@patch.object(cartography.intel.render.workspacemembers, "get", return_value=[])
@patch.object(cartography.intel.render.registrycredentials, "get", return_value=[])
@patch.object(cartography.intel.render.envgroups, "get", return_value=[])
@patch.object(cartography.intel.render.keyvalue, "get", return_value=[])
@patch.object(cartography.intel.render.secretfiles, "get", return_value=[])
@patch.object(cartography.intel.render.customdomains, "get", return_value=[])
@patch.object(cartography.intel.render.disks, "get", return_value=[])
@patch.object(cartography.intel.render.postgres, "get", return_value=[])
@patch.object(cartography.intel.render.services, "get_latest_deploy", return_value=None)
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
    mock_get_latest_deploy,
    mock_get_postgres,
    mock_get_disks,
    mock_get_custom_domains,
    mock_get_secret_files,
    mock_get_key_value,
    mock_get_env_groups,
    mock_get_registry_credentials,
    mock_get_workspace_members,
    mock_get_log_stream,
    mock_get_snapshots,
    mock_get_env_vars,
    mock_get_header_rules,
    mock_get_routes,
    mock_get_blueprints,
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


def test_render_cleanup_removes_stale_resources_across_resource_types(neo4j_session):
    """
    The Render module owns many cleanup jobs, not just RenderProject. A successful run
    that later sees empty inventories should clean stale nodes for each resource type.
    """
    with ExitStack() as stack:
        _patch_all_resources(stack)
        cartography.intel.render.start_render_ingestion(neo4j_session, _config())

    stale_labels = [
        "RenderProject",
        "RenderEnvironment",
        "RenderService",
        "RenderPostgres",
        "RenderKeyValue",
        "RenderDisk",
        "RenderSnapshot",
        "RenderCustomDomain",
        "RenderSecretFile",
        "RenderEnvGroup",
        "RenderRegistryCredential",
        "RenderWorkspaceMember",
        "RenderLogStream",
        "RenderEnvVar",
        "RenderHeaderRule",
        "RenderRoute",
        "RenderBlueprint",
        "RenderIPAllowRule",
    ]
    for label in stale_labels:
        assert check_nodes(neo4j_session, label, ["id"])

    with ExitStack() as stack:
        _patch_all_resources(stack, overrides=_empty_resource_overrides())
        cartography.intel.render.start_render_ingestion(
            neo4j_session, _config(TEST_UPDATE_TAG_2)
        )

    for label in stale_labels:
        assert check_nodes(neo4j_session, label, ["id"]) == set()
    assert check_nodes(neo4j_session, "RenderTenant", ["id"]) == {(TEST_OWNER_ID,)}


def _config(update_tag: int = TEST_UPDATE_TAG) -> Config:
    return Config(
        neo4j_uri="bolt://localhost:7687",
        render_api_key="test-api-key",
        update_tag=update_tag,
    )


def test_enrichment_resource_failure_does_not_abort_the_workspace_sync(neo4j_session):
    """
    Registry credentials are enrichment, not core (see cartography/intel/render/
    __init__.py's classification). A failure fetching them must not prevent core
    resources (project, service, ...) from syncing.
    """
    with ExitStack() as stack:
        _patch_all_resources(
            stack,
            overrides={
                (cartography.intel.render.registrycredentials, "get"): {
                    "side_effect": requests.exceptions.HTTPError("boom"),
                },
            },
        )
        cartography.intel.render.start_render_ingestion(neo4j_session, _config())

    assert check_nodes(neo4j_session, "RenderProject", ["id"]) == {(TEST_PROJECT_ID,)}
    assert check_nodes(neo4j_session, "RenderService", ["id"]) == {(TEST_SERVICE_ID,)}
    assert check_nodes(neo4j_session, "RenderRegistryCredential", ["id"]) == set()


def test_enrichment_cleanup_is_skipped_when_its_fetch_fails(neo4j_session):
    """
    A resource type's own sync() only reaches load()/cleanup() if get() succeeds. If
    an enrichment resource's fetch fails on a later run, the node it loaded on an
    earlier successful run must survive - safe_sync() containing the exception must
    not be mistaken for "this resource type has zero items now".
    """
    with ExitStack() as stack:
        _patch_all_resources(stack)
        cartography.intel.render.start_render_ingestion(neo4j_session, _config())
    assert check_nodes(neo4j_session, "RenderRegistryCredential", ["id"]) == {
        (TEST_REGISTRY_CREDENTIAL_ID,)
    }

    with ExitStack() as stack:
        _patch_all_resources(
            stack,
            overrides={
                (cartography.intel.render.registrycredentials, "get"): {
                    "side_effect": requests.exceptions.HTTPError("boom"),
                },
            },
        )
        cartography.intel.render.start_render_ingestion(
            neo4j_session, _config(TEST_UPDATE_TAG_2)
        )

    assert check_nodes(neo4j_session, "RenderRegistryCredential", ["id"]) == {
        (TEST_REGISTRY_CREDENTIAL_ID,)
    }


def test_core_resource_failure_aborts_the_workspace_sync(neo4j_session):
    """
    Services are core (see __init__.py's classification): unlike an enrichment
    resource, a failure here is not caught by safe_sync() and must propagate.
    """
    with ExitStack() as stack:
        _patch_all_resources(
            stack,
            overrides={
                (cartography.intel.render.services, "get"): {
                    "side_effect": requests.exceptions.HTTPError("boom"),
                },
            },
        )
        with pytest.raises(requests.exceptions.HTTPError):
            cartography.intel.render.start_render_ingestion(neo4j_session, _config())


def test_latest_deploy_failure_does_not_abort_service_sync(neo4j_session):
    """
    Latest deploy details are service enrichment, not the service inventory itself. If
    that per-service metadata fetch fails after the service list succeeded, keep the
    service node and omit only the latest-deploy fields for this run.
    """
    with ExitStack() as stack:
        _patch_all_resources(
            stack,
            overrides={
                (cartography.intel.render.services, "get_latest_deploy"): {
                    "side_effect": requests.exceptions.HTTPError("boom"),
                },
            },
        )
        cartography.intel.render.start_render_ingestion(neo4j_session, _config())

    assert check_nodes(
        neo4j_session,
        "RenderService",
        ["id", "name", "latest_deploy_id"],
    ) == {
        (TEST_SERVICE_ID, "cartography-test-service", None),
    }


def test_service_child_cleanup_is_skipped_when_its_fetch_fails_halfway(neo4j_session):
    """
    Env vars are fetched per-service-id; a failure partway through that loop must not
    delete an env var node loaded on an earlier successful run.
    """
    with ExitStack() as stack:
        _patch_all_resources(
            stack,
            overrides={
                (cartography.intel.render.services, "get"): {
                    "return_value": _two_services_response(),
                },
            },
        )
        cartography.intel.render.start_render_ingestion(neo4j_session, _config())
    assert check_nodes(neo4j_session, "RenderEnvVar", ["id"]) == {
        (TEST_ENV_VAR_ID,),
        (TEST_SECOND_ENV_VAR_ID,),
    }

    with ExitStack() as stack:
        _patch_all_resources(
            stack,
            overrides={
                (cartography.intel.render.services, "get"): {
                    "return_value": _two_services_response(),
                },
                (cartography.intel.render.envvars, "get"): {
                    "side_effect": [
                        ENV_VARS_RESPONSE,
                        requests.exceptions.HTTPError("boom"),
                    ],
                },
            },
        )
        service_cleanup = stack.enter_context(
            patch.object(cartography.intel.render.services, "cleanup")
        )
        cartography.intel.render.start_render_ingestion(
            neo4j_session, _config(TEST_UPDATE_TAG_2)
        )

    service_cleanup.assert_not_called()
    assert check_nodes(neo4j_session, "RenderEnvVar", ["id"]) == {
        (TEST_ENV_VAR_ID,),
        (TEST_SECOND_ENV_VAR_ID,),
    }


def test_snapshot_cleanup_is_skipped_when_its_fetch_fails_halfway(neo4j_session):
    """
    Snapshots are fetched per-disk-id; a failure partway through that loop must not
    delete a snapshot node loaded on an earlier successful run.
    """
    with ExitStack() as stack:
        _patch_all_resources(
            stack,
            overrides={
                (cartography.intel.render.disks, "get"): {
                    "return_value": _two_disks_response(),
                },
            },
        )
        cartography.intel.render.start_render_ingestion(neo4j_session, _config())
    assert check_nodes(neo4j_session, "RenderSnapshot", ["id"]) == {
        (TEST_SNAPSHOT_ID,),
        (TEST_SECOND_SNAPSHOT_ID,),
    }

    with ExitStack() as stack:
        _patch_all_resources(
            stack,
            overrides={
                (cartography.intel.render.disks, "get"): {
                    "return_value": _two_disks_response(),
                },
                (cartography.intel.render.snapshots, "get"): {
                    "side_effect": [
                        SNAPSHOTS_RESPONSE,
                        requests.exceptions.HTTPError("boom"),
                    ],
                },
            },
        )
        disk_cleanup = stack.enter_context(
            patch.object(cartography.intel.render.disks, "cleanup")
        )
        cartography.intel.render.start_render_ingestion(
            neo4j_session, _config(TEST_UPDATE_TAG_2)
        )

    disk_cleanup.assert_not_called()
    assert check_nodes(neo4j_session, "RenderSnapshot", ["id"]) == {
        (TEST_SNAPSHOT_ID,),
        (TEST_SECOND_SNAPSHOT_ID,),
    }


def test_disks_cleanup_runs_after_snapshots_cleanup(neo4j_session):
    order: list[str] = []

    def _record(name: str):
        def _side_effect(*args, **kwargs):
            order.append(name)

        return _side_effect

    with ExitStack() as stack:
        _patch_all_resources(stack)
        stack.enter_context(
            patch.object(
                cartography.intel.render.disks, "cleanup", side_effect=_record("disks")
            )
        )
        stack.enter_context(
            patch.object(
                cartography.intel.render.snapshots,
                "cleanup",
                side_effect=_record("snapshots"),
            )
        )
        cartography.intel.render.start_render_ingestion(neo4j_session, _config())

    assert order.index("snapshots") < order.index("disks")


def test_services_cleanup_runs_after_service_child_cleanups(neo4j_session):
    order: list[str] = []

    def _record(name: str):
        def _side_effect(*args, **kwargs):
            order.append(name)

        return _side_effect

    service_children = [
        (cartography.intel.render.customdomains, "customdomains"),
        (cartography.intel.render.secretfiles, "secretfiles"),
        (cartography.intel.render.envvars, "envvars"),
        (cartography.intel.render.headerrules, "headerrules"),
        (cartography.intel.render.routes, "routes"),
    ]
    with ExitStack() as stack:
        _patch_all_resources(stack)
        stack.enter_context(
            patch.object(
                cartography.intel.render.services,
                "cleanup",
                side_effect=_record("services"),
            )
        )
        for module, name in service_children:
            stack.enter_context(
                patch.object(module, "cleanup", side_effect=_record(name))
            )
        cartography.intel.render.start_render_ingestion(neo4j_session, _config())

    services_index = order.index("services")
    for _, name in service_children:
        assert order.index(name) < services_index
