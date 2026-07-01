from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.grants
import cartography.intel.databricks.groups
import cartography.intel.databricks.service_principals
import cartography.intel.databricks.tables
import cartography.intel.databricks.users
from tests.data.databricks.grants import DATABRICKS_GRANTS
from tests.data.databricks.groups import DATABRICKS_GROUPS
from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID
from tests.data.databricks.service_principals import DATABRICKS_SERVICE_PRINCIPALS
from tests.data.databricks.tables import DATABRICKS_TABLES
from tests.data.databricks.users import DATABRICKS_USERS
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.integration.cartography.intel.databricks.test_catalogs import (
    _ensure_local_neo4j_has_test_catalogs,
)
from tests.integration.cartography.intel.databricks.test_metastores import (
    _ensure_local_neo4j_has_test_metastore,
)
from tests.integration.cartography.intel.databricks.test_schemas import (
    _ensure_local_neo4j_has_test_schemas,
)
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _uc_id(full_name):
    return f"{DATABRICKS_METASTORE_ID}/{full_name}"


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


def _seed_tables(neo4j_session):
    cartography.intel.databricks.tables.load_tables(
        neo4j_session,
        cartography.intel.databricks.tables.transform(DATABRICKS_TABLES),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.grants,
    "get",
    return_value=DATABRICKS_GRANTS,
)
def test_load_databricks_grants(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_metastore(neo4j_session)
    _ensure_local_neo4j_has_test_catalogs(neo4j_session)
    _ensure_local_neo4j_has_test_schemas(neo4j_session)
    _seed_tables(neo4j_session)
    _seed_principals(neo4j_session)

    cartography.intel.databricks.grants.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    # User -> Catalog HAS_PRIVILEGE
    assert check_rels(
        neo4j_session,
        "DatabricksUser",
        "user_name",
        "DatabricksCatalog",
        "id",
        "HAS_PRIVILEGE",
        rel_direction_right=True,
    ) == {("jeremy@subimage.io", _uc_id("prod"))}

    # Group -> Table HAS_PRIVILEGE
    assert check_rels(
        neo4j_session,
        "DatabricksGroup",
        "display_name",
        "DatabricksTable",
        "id",
        "HAS_PRIVILEGE",
        rel_direction_right=True,
    ) == {("admins", _uc_id("prod.finance.customers"))}

    # ServicePrincipal -> Schema HAS_PRIVILEGE
    assert check_rels(
        neo4j_session,
        "DatabricksServicePrincipal",
        "application_id",
        "DatabricksSchema",
        "id",
        "HAS_PRIVILEGE",
        rel_direction_right=True,
    ) == {("abcd1234-5678-90ab-cdef-1234567890ab", _uc_id("prod.finance"))}
