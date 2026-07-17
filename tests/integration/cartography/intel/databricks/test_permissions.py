from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.clusters
import cartography.intel.databricks.groups
import cartography.intel.databricks.jobs
import cartography.intel.databricks.permissions
import cartography.intel.databricks.secret_scopes
import cartography.intel.databricks.service_principals
import cartography.intel.databricks.users
from tests.data.databricks.clusters import DATABRICKS_CLUSTERS
from tests.data.databricks.groups import DATABRICKS_GROUPS
from tests.data.databricks.jobs import DATABRICKS_JOBS
from tests.data.databricks.permissions import DATABRICKS_PERMISSIONS
from tests.data.databricks.secret_scopes import DATABRICKS_SECRET_SCOPES
from tests.data.databricks.service_principals import DATABRICKS_SERVICE_PRINCIPALS
from tests.data.databricks.users import DATABRICKS_USERS
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789

# The permissions API returns one ACL entry per principal (cluster + job);
# the secret scope ACL comes from the separate secrets endpoint.
_OBJECT_PERMISSIONS = [
    p for p in DATABRICKS_PERMISSIONS if p["object_type"] != "secret-scope"
]
_SECRET_SCOPE_ACLS = [
    p for p in DATABRICKS_PERMISSIONS if p["object_type"] == "secret-scope"
]


def _seed_principals(neo4j_session):
    cartography.intel.databricks.users.load_users(
        neo4j_session,
        cartography.intel.databricks.users.transform(
            DATABRICKS_USERS, DATABRICKS_WORKSPACE_ID
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.databricks.groups.load_groups(
        neo4j_session,
        cartography.intel.databricks.groups.transform(
            DATABRICKS_GROUPS, DATABRICKS_WORKSPACE_ID
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.databricks.service_principals.load_service_principals(
        neo4j_session,
        cartography.intel.databricks.service_principals.transform(
            DATABRICKS_SERVICE_PRINCIPALS, DATABRICKS_WORKSPACE_ID
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


def _seed_objects(neo4j_session):
    cartography.intel.databricks.clusters.load_clusters(
        neo4j_session,
        cartography.intel.databricks.clusters.transform(
            DATABRICKS_CLUSTERS, DATABRICKS_WORKSPACE_ID
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.databricks.jobs.load_jobs(
        neo4j_session,
        cartography.intel.databricks.jobs.transform_jobs(
            DATABRICKS_JOBS, DATABRICKS_WORKSPACE_ID, {}
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.databricks.secret_scopes.load_secret_scopes(
        neo4j_session,
        cartography.intel.databricks.secret_scopes.transform(
            DATABRICKS_SECRET_SCOPES, DATABRICKS_WORKSPACE_ID
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.permissions,
    "get_secret_scope_acls",
    return_value=(_SECRET_SCOPE_ACLS, True),
)
@patch.object(
    cartography.intel.databricks.permissions,
    "get",
    return_value=(_OBJECT_PERMISSIONS, True),
)
def test_load_databricks_permissions(mock_get, mock_scope_acls, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _seed_principals(neo4j_session)
    _seed_objects(neo4j_session)

    cartography.intel.databricks.permissions.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    # User -> Cluster HAS_PERMISSION
    assert check_rels(
        neo4j_session,
        "DatabricksUser",
        "user_name",
        "DatabricksCluster",
        "id",
        "HAS_PERMISSION",
        rel_direction_right=True,
    ) == {("jeremy@subimage.io", scoped("0202-cluster-aaaa"))}

    # Group -> Job HAS_PERMISSION
    assert check_rels(
        neo4j_session,
        "DatabricksGroup",
        "display_name",
        "DatabricksJob",
        "id",
        "HAS_PERMISSION",
        rel_direction_right=True,
    ) == {("admins", scoped("1011944831447606"))}

    # ServicePrincipal -> SecretScope HAS_PERMISSION (from the secrets ACL)
    assert check_rels(
        neo4j_session,
        "DatabricksServicePrincipal",
        "application_id",
        "DatabricksSecretScope",
        "id",
        "HAS_PERMISSION",
        rel_direction_right=True,
    ) == {("abcd1234-5678-90ab-cdef-1234567890ab", scoped("ci-cd"))}
